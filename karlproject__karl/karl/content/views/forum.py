# Copyright (C) 2008-2009 Open Society Institute
#               Thomas Moroz: tmoroz@sorosny.org
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License Version 2 as published
# by the Free Software Foundation.  You may not use, modify or distribute
# this program under any other version of the GNU General Public License.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

import datetime

import formish
import schemaish
from schemaish.type import File as SchemaFile
from validatish import validator

from pyramid.httpexceptions import HTTPFound

from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.component.event import objectEventNotify

from pyramid.renderers import render_to_response

from pyramid_formish import Form
from pyramid_formish.zcml import FormAction
from pyramid.url import resource_url
from pyramid.traversal import resource_path
from pyramid.security import authenticated_userid
from pyramid.security import effective_principals
from pyramid.security import has_permission
from repoze.workflow import get_workflow

from repoze.lemonade.content import create_content

from karl.content.interfaces import IForum
from karl.content.interfaces import IForumTopic

from karl.events import ObjectModifiedEvent
from karl.events import ObjectWillBeModifiedEvent

from karl.models.interfaces import IComment
from karl.models.interfaces import ICatalogSearch

from karl.security.workflow import get_security_states

from karl.utils import get_layout_provider
from karl.utils import find_interface
from karl.utils import find_profiles
from karl.utils import find_intranet
from karl.utils import support_attachments
from karl.utilities.image import thumb_url
from karl.utilities.interfaces import IKarlDates
from karl.utilities.image import relocate_temp_images

from karl.views.api import TemplateAPI

from karl.views.forms import widgets as karlwidgets
from karl.views.forms.filestore import get_filestore
from karl.views.people import PROFILE_THUMB_SIZE
from karl.views.utils import convert_to_script
from karl.views.utils import make_unique_name
from karl.views.tags import set_tags
from karl.views.batch import get_catalog_batch_grid
from karl.views.tags import get_tags_client_data

from karl.content.views.commenting import AddCommentFormController
from karl.content.views.utils import extract_description
from karl.content.views.interfaces import IBylineInfo
from karl.content.views.utils import upload_attachments
from karl.content.views.utils import fetch_attachments

def titlesort(one, two):
    return cmp(one.title, two.title)

class ShowForumsView(object):
    _admin_actions = [
        ('Add Forum', 'add_forum.html'),
        ]

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        context = self.context
        request = self.request

        page_title = context.title
        api = TemplateAPI(context, request, page_title)
        karldates = getUtility(IKarlDates)

        actions = []
        if has_permission('create', context, request):
            actions = [(title, request.resource_url(context, view))
                       for title, view in self._admin_actions]

        forums = list(context.values())
        forums.sort(titlesort)

        forum_data = []

        for forum in forums:
            D = {}
            D['title'] = forum.title
            D['url'] = resource_url(forum, request)
            D['number_of_topics'] = number_of_topics(forum)
            D['number_of_comments'] = number_of_comments(forum, request)

            latest = latest_object(forum, request)

            _NOW = datetime.datetime.now()

            if latest:
                D['latest_activity_url'] = resource_url(latest, request)
                D['latest_activity_link'] = getattr(latest, 'title', None)
                D['latest_activity_by'] = getattr(latest, 'creator', None)
                modified = getattr(latest, 'modified_date', _NOW)
                modified_str = karldates(modified, 'longform')
                D['latest_activity_at'] = modified_str
            else:
                D['latest_activity_url'] = None
                D['latest_activity_link'] = None
                D['latest_activity_by'] = None
                D['latest_activity_at'] = None

            forum_data.append(D)

        client_json_data = dict(
            tagbox = get_tags_client_data(context, request),
            )

        layout = self.request.layout_manager.layout
        layout.section_style = "none"
        intranet = find_intranet(context)
        intranet_title = getattr(intranet, 'title', '')
        layout.page_title = '%s Forums' % intranet_title
        layout.head_data['panel_data']['tagbox'] = client_json_data['tagbox']
        layout.add_portlet('tagbox')
        return render_to_response(
            'templates/show_forums.pt',
            dict(api=api,
                 actions=actions,
                 forum_data = forum_data),
            request=request,
            )

def show_forums_view(context, request):
    return ShowForumsView(context, request)()

def show_forum_view(context, request):

    page_title = context.title
    api = TemplateAPI(context, request, page_title)

    actions = []
    if has_permission('create', context, request):
        actions.append(('Add Forum Topic', 'add_forum_topic.html'))
    if has_permission('edit', context, request):
        actions.append(('Edit', 'edit.html'))
    if has_permission('delete', context, request):
        actions.append(('Delete', 'delete.html'))

    profiles = find_profiles(context)
    karldates = getUtility(IKarlDates)

    topic_batch = get_topic_batch(context, request)
    topic_entries = topic_batch['entries']

    topics = []
    for topic in topic_entries:
        D = {}
        profile = profiles.get(topic.creator)
        posted_by = getattr(profile, 'title', None)
        date = karldates(topic.created, 'longform')
        D['url'] = resource_url(topic, request)
        D['title'] = topic.title
        D['posted_by'] = posted_by
        D['date'] = date
        D['number_of_comments'] = len(topic['comments'])
        topics.append(D)

    # In the intranet side, the backlinks should go to the show_forums
    # view (the default)
    forums = context.__parent__
    backto = {
        'href': resource_url(forums, request),
        'title': forums.title,
        }

    # Get a layout
    layout_provider = get_layout_provider(context, request)
    layout = layout_provider('generic')

    ux2_layout = request.layout_manager.layout
    ux2_layout.section_style = "none"

    return render_to_response(
        'templates/show_forum.pt',
        dict(api = api,
             actions = actions,
             title = context.title,
             topics = topics,
             batch_info = topic_batch,
             backto=backto,
             old_layout=layout),
        request=request,
        )

tags_field = schemaish.Sequence(schemaish.String())
text_field = schemaish.String()
security_field = schemaish.String(
    description=('Items marked as private can only be seen by '
                 'members of this community.'))
attachments_field = schemaish.Sequence(schemaish.File(),
    title='Attachments',
    )

title_field = schemaish.String(
    validator=validator.All(
        validator.Length(max=100),
        validator.Required(),
        )
    )
description_field = schemaish.String(
    validator=validator.Length(max=500),
    description=("This description will appear in search "
                 "results and on the community listing page. Please "
                 "limit your description to 100 words or less.")
    )

class AddForumFormController(object):
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.workflow = get_workflow(IForum, 'security', self.context)

    def _get_security_states(self):
        return get_security_states(self.workflow, None, self.request)

    def form_defaults(self):
        defaults = {
            'title':'',
            'description':''}

        if self.workflow is not None:
            defaults['security_state'] = self.workflow.initial_state
        return defaults

    def form_fields(self):
        fields = []
        fields.append(('title', title_field))
        fields.append(('description', description_field))
        security_states = self._get_security_states()
        if security_states:
            fields.append(('security_state', security_field))
        return fields

    def form_widgets(self, fields):
        widgets = {
            'title':formish.Input(empty=''),
            'description':formish.TextArea(cols=60, rows=10, empty=''),
            }
        security_states = self._get_security_states()
        schema = dict(fields)
        if 'security_state' in schema:
            security_states = self._get_security_states()
            widgets['security_state'] = formish.RadioChoice(
                options=[ (s['name'], s['title']) for s in security_states],
                none_option=None)
        return widgets

    def __call__(self):
        layout = self.request.layout_manager.layout
        layout.section_style = "none"
        layout.page_title = 'Add Forum'
        api = TemplateAPI(self.context, self.request, layout.page_title)
        return {'api':api, 'actions':()}

    def handle_cancel(self):
        return HTTPFound(location=resource_url(self.context, self.request))

    def handle_submit(self, converted):
        request = self.request
        context = self.context
        workflow = self.workflow

        forum = create_content(IForum,
            converted['title'],
            converted['description'],
            authenticated_userid(request),
            )

        name = make_unique_name(context, converted['title'])
        context[name] = forum

        # Set up workflow
        if workflow is not None:
            workflow.initialize(forum)
            if 'security_state' in converted:
                workflow.transition_to_state(forum, request,
                                             converted['security_state'])

        location = resource_url(forum, request)
        return HTTPFound(location=location)

class EditForumFormController(object):
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.workflow = get_workflow(IForum, 'security', context)

    def _get_security_states(self):
        return get_security_states(self.workflow, self.context, self.request)

    def form_defaults(self):
        defaults = {
            'title':self.context.title,
            'description':self.context.description}

        if self.workflow is not None:
            defaults['security_state'] = self.workflow.state_of(self.context)
        return defaults

    def form_fields(self):
        fields = []
        fields.append(('title', title_field))
        fields.append(('description', description_field))
        security_states = self._get_security_states()
        if security_states:
            fields.append(('security_state', security_field))
        return fields

    def form_widgets(self, fields):
        widgets = {
            'title':formish.Input(empty=''),
            'description':formish.TextArea(cols=60, rows=10, empty=''),
            }
        security_states = self._get_security_states()
        schema = dict(fields)
        if 'security_state' in schema:
            security_states = self._get_security_states()
            widgets['security_state'] = formish.RadioChoice(
                options=[ (s['name'], s['title']) for s in security_states],
                none_option=None)
        return widgets

    def __call__(self):
        page_title = 'Edit %s' % self.context.title
        layout = self.request.layout_manager.layout
        layout.section_style = "none"
        layout.page_title = page_title
        page_title = 'Edit %s' % self.context.title
        api = TemplateAPI(self.context, self.request, page_title)
        return {'api':api, 'actions':()}

    def handle_cancel(self):
        return HTTPFound(location=resource_url(self.context, self.request))

    def handle_submit(self, converted):
        context = self.context
        request = self.request
        workflow = self.workflow
        # *will be* modified event
        objectEventNotify(ObjectWillBeModifiedEvent(context))
        if workflow is not None:
            if 'security_state' in converted:
                workflow.transition_to_state(context, request,
                                             converted['security_state'])

        context.title = converted['title']
        context.description = converted['description']

        # Modified
        context.modified_by = authenticated_userid(request)
        objectEventNotify(ObjectModifiedEvent(context))

        location = resource_url(context, request,
                             query={'status_message':'Forum Edited'})
        return HTTPFound(location=location)

def show_forum_topic_view(context, request):
    post_url = resource_url(context, request, "comments", "add_comment.html")
    karldates = getUtility(IKarlDates)
    profiles = find_profiles(context)

    # Convert comments into a digestable form for the template
    comments = []

    page_title = context.title

    actions = []
    if has_permission('edit', context, request):
        actions.append(('Edit', 'edit.html'))
    if has_permission('delete', context, request):
        actions.append(('Delete', 'delete.html'))
    if has_permission('administer', context, request):
        actions.append(('Advanced', 'advanced.html'))

    api = TemplateAPI(context, request, page_title)

    for comment in context['comments'].values():
        profile = profiles.get(comment.creator)
        author_name = profile.title
        author_url = resource_url(profile, request)

        newc = {}
        newc['id'] = comment.__name__
        if has_permission('edit', comment, request):
            newc['edit_url'] = resource_url(comment, request, 'edit.html')
        else:
            newc['edit_url'] = None

        if has_permission('delete', comment, request):
            newc['delete_url'] = resource_url(comment, request, 'delete.html')
        else:
            newc['delete_url'] = None

        if has_permission('administer', comment, request):
            newc['advanced_url'] = resource_url(comment, request, 'advanced.html')
        else:
            newc['advanced_url'] = None

        # Display portrait
        photo = profile.get('photo')
        photo_url = {}
        if photo is not None:
            photo_url = thumb_url(photo, request, PROFILE_THUMB_SIZE)
        else:
            photo_url = api.static_url + "/images/defaultUser.gif"
        newc["portrait_url"] = photo_url

        newc['author_url'] = author_url
        newc['author_name'] = author_name

        newc['date'] = karldates(comment.created, 'longform')
        newc['timestamp'] = comment.created
        newc['text'] = comment.text

        # Fetch the attachments info
        newc['attachments'] = fetch_attachments(comment, request)
        comments.append(newc)
    comments.sort(key=lambda x: x['timestamp'])

    byline_info = getMultiAdapter((context, request), IBylineInfo)
    forum = find_interface(context, IForum)
    backto = {
        'href': resource_url(forum, request),
        'title': forum.title,
        }

    # provide client data for rendering current tags in the tagbox
    client_json_data = dict(
        tagbox = get_tags_client_data(context, request),
        )

    # Get a layout
    layout_provider = get_layout_provider(context, request)
    old_layout = layout_provider('community')

    if support_attachments(context):
        attachments = fetch_attachments(context['attachments'], request)
    else:
        attachments = ()

    # manually construct formish comment form
    controller = AddCommentFormController(context['comments'], request)
    form_schema = schemaish.Structure()
    form_fields = controller.form_fields()
    for fieldname, field in form_fields:
        form_schema.add(fieldname, field)
    form_action_url = '%sadd_comment.html' % resource_url(context['comments'],
                                                       request)
    comment_form = Form(form_schema, add_default_action=False, name='save',
                        action_url=form_action_url)
    form_defaults = controller.form_defaults()
    comment_form.defaults = form_defaults
    request.form_defaults = form_defaults

    form_actions = [FormAction('submit', 'submit'),
                    FormAction('cancel', 'cancel', validate=False)]
    for action in form_actions:
        comment_form.add_action(action.name, action.title)

    widgets = controller.form_widgets(form_fields)
    for name, widget in widgets.items():
        comment_form[name].widget = widget

    # enable imagedrawer for adding forum replies (comments)
    api.karl_client_data['text'] = dict(
            enable_imagedrawer_upload = True,
            )
    # ux2
    layout = request.layout_manager.layout
    layout.section_style = "none"
    layout.head_data['panel_data']['tinymce'] = api.karl_client_data['text']
    layout.head_data['panel_data']['tagbox'] = client_json_data['tagbox']
    layout.add_portlet('tagbox')

    return render_to_response(
        'templates/show_forum_topic.pt',
        dict(api=api,
             actions=actions,
             comments=comments,
             attachments=attachments,
             formfields=api.formfields,
             post_url=post_url,
             byline_info=byline_info,
             head_data=convert_to_script(client_json_data),
             backto=backto,
             old_layout=old_layout,
             comment_form=comment_form),
        request=request,
        )


class AddForumTopicFormController(object):
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.workflow = get_workflow(IForumTopic, 'security', context)
        self.filestore = get_filestore(context, request, 'add-forumtopic')

    def _get_security_states(self):
        return get_security_states(self.workflow, None, self.request)

    def form_defaults(self):
        defaults = {
            'title':'',
            'tags':[],
            'text':'',
            'attachments':[],
            }

        if self.workflow is not None:
            defaults['security_state'] = self.workflow.initial_state
        return defaults

    def form_fields(self):
        fields = []
        title_field = schemaish.String(
            validator=validator.All(
                validator.Length(max=100),
                validator.Required(),
                )
            )
        fields.append(('title', title_field))
        fields.append(('tags', tags_field))
        fields.append(('text', text_field))
        fields.append(('attachments', attachments_field))
        security_states = self._get_security_states()
        if security_states:
            fields.append(('security_state', security_field))
        return fields

    def form_widgets(self, fields):
        widgets = {
            'title':formish.Input(empty=''),
            'tags':karlwidgets.TagsAddWidget(),
            'text':karlwidgets.RichTextWidget(empty=''),
            'attachments': karlwidgets.AttachmentsSequence(sortable=False,
                                                           min_start_fields=0),
            'attachments.*':karlwidgets.FileUpload2(filestore=self.filestore),
            }
        security_states = self._get_security_states()
        schema = dict(fields)
        if 'security_state' in schema:
            security_states = self._get_security_states()
            widgets['security_state'] = formish.RadioChoice(
                options=[ (s['name'], s['title']) for s in security_states],
                none_option=None)
        return widgets

    def __call__(self):
        layout_provider = get_layout_provider(self.context, self.request)
        old_layout = layout_provider('community')
        api = TemplateAPI(self.context, self.request, 'Add Forum Topic')
        # ux1
        api.karl_client_data['text'] = dict(
                enable_imagedrawer_upload = True,
                )
        # ux2
        layout = self.request.layout_manager.layout
        layout.section_style = "none"
        layout.head_data['panel_data']['tinymce'] = api.karl_client_data['text']
        return {
            'api': api,             # deprecated UX1
            'old_layout': old_layout,   # deprecated UX1
            'actions': []}          # deprecated UX1

    def handle_cancel(self):
        return HTTPFound(location=resource_url(self.context, self.request))

    def handle_submit(self, converted):
        context = self.context
        request = self.request
        workflow = self.workflow

        name = make_unique_name(context, converted['title'])
        creator = authenticated_userid(request)

        topic = create_content(IForumTopic,
            converted['title'],
            converted['text'],
            creator,
            )

        topic.description = extract_description(converted['text'])
        context[name] = topic

        # Set up workflow
        if workflow is not None:
            workflow.initialize(topic)
            if 'security_state' in converted:
                workflow.transition_to_state(topic, request,
                                             converted['security_state'])

        # send the temp images to their final place
        relocate_temp_images(topic, request)

        # Tags and attachments
        set_tags(topic, request, converted['tags'])
        if support_attachments(topic):
            upload_attachments(converted['attachments'], topic['attachments'],
                               creator, request)

        location = resource_url(topic, request)
        return HTTPFound(location=location)

class EditForumTopicFormController(object):
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.workflow = get_workflow(IForumTopic, 'security', context)
        self.filestore = get_filestore(context, request, 'edit-forumtopic')

    def _get_security_states(self):
        return get_security_states(self.workflow, self.context, self.request)

    def form_defaults(self):
        attachments = [SchemaFile(None, x.__name__, x.mimetype)
                       for x in self.context['attachments'].values()]
        defaults = {
            'title':self.context.title,
            'tags':[], # initial values supplied by widget
            'text':self.context.text,
            'attachments':attachments,
            }

        if self.workflow is not None:
            defaults['security_state'] = self.workflow.state_of(self.context)
        return defaults

    def form_fields(self):
        fields = []
        title_field = schemaish.String(
            validator=validator.All(
                validator.Length(max=100),
                validator.Required(),
                )
            )
        fields.append(('title', title_field))
        fields.append(('tags', tags_field))
        fields.append(('text', text_field))
        fields.append(('attachments', attachments_field))
        security_states = self._get_security_states()
        if security_states:
            fields.append(('security_state', security_field))
        return fields

    def form_widgets(self, fields):
        tagdata = get_tags_client_data(self.context, self.request)
        widgets = {
            'title':formish.Input(empty=''),
            'tags':karlwidgets.TagsEditWidget(tagdata=tagdata),
            'text':karlwidgets.RichTextWidget(empty=''),
            'attachments': karlwidgets.AttachmentsSequence(sortable=False,
                                                           min_start_fields=0),
            'attachments.*':karlwidgets.FileUpload2(filestore=self.filestore),
            }
        security_states = self._get_security_states()
        schema = dict(fields)
        if 'security_state' in schema:
            security_states = self._get_security_states()
            widgets['security_state'] = formish.RadioChoice(
                options=[ (s['name'], s['title']) for s in security_states],
                none_option=None)
        return widgets

    def __call__(self):
        layout_provider = get_layout_provider(self.context, self.request)
        old_layout = layout_provider('community')
        page_title = 'Edit %s' % self.context.title
        api = TemplateAPI(self.context, self.request, page_title)
        # ux1
        api.karl_client_data['text'] = dict(
                enable_imagedrawer_upload = True,
                )
        # ux2
        layout = self.request.layout_manager.layout
        layout.section_style = "none"
        layout.head_data['panel_data']['tinymce'] = api.karl_client_data['text']
        return {
            'api': api,             # deprecated UX1
            'old_layout': old_layout,   # deprecated UX1
            'actions': []}          # deprecated UX1

    def handle_cancel(self):
        return HTTPFound(location=resource_url(self.context, self.request))

    def handle_submit(self, converted):
        context = self.context
        request = self.request
        workflow = self.workflow

        # *will be* modified event
        objectEventNotify(ObjectWillBeModifiedEvent(context))
        if workflow is not None:
            if 'security_state' in converted:
                workflow.transition_to_state(context, request,
                                             converted['security_state'])

        context.title = converted['title']
        context.text = converted['text']
        context.description = extract_description(converted['text'])

        # Save the tags on it
        set_tags(context, request, converted['tags'])

        # Save new attachments
        creator = authenticated_userid(request)
        if support_attachments(context):
            upload_attachments(converted['attachments'], context['attachments'],
                               creator, request)

        # Modified
        context.modified_by = authenticated_userid(request)
        objectEventNotify(ObjectModifiedEvent(context))

        location = resource_url(context, request,
                             query={'status_message':'Forum Topic Edited'})
        return HTTPFound(location=location)

def number_of_topics(forum):
    return len(forum)

def number_of_comments(forum, request):
    searcher = ICatalogSearch(forum)
    total, docids, resolver = searcher(
        interfaces=[IComment],
        path={'query': resource_path(forum)},
        allowed={'query': effective_principals(request), 'operator': 'or'},
        )
    return total

def latest_object(forum, request):
    searcher = ICatalogSearch(forum)
    total, docids, resolver = searcher(
        sort_index='modified_date',
        interfaces={'query': [IForumTopic, IComment], 'operator':'or'},
        path={'query': resource_path(forum)},
        allowed={'query': effective_principals(request), 'operator': 'or'},
        reverse=True)

    docids = list(docids)
    if docids:
        return resolver(docids[0])
    else:
        return None

def get_topic_batch(forum, request):
    return get_catalog_batch_grid(
        forum, request, interfaces=[IForumTopic], reverse=True,
        path={'query': resource_path(forum)},
        allowed={'query': effective_principals(request), 'operator': 'or'},
        )

