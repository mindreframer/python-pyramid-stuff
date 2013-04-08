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

"""Community membership views, both for browsing and managing.

Includes invitations, per-user preferences on alerts, etc.
"""

import schemaish
import formish
from validatish import validator
from karl.views.forms import widgets as karlwidgets
from karl.views.forms import validators as karlvalidators
from karl.views.forms.filestore import get_filestore
from karl.views.utils import Invalid
from karl.consts import countries
from karl.consts import cultures

import transaction

from email.Message import Message
from pyramid.response import Response
from simplejson import JSONEncoder

from pyramid.httpexceptions import HTTPFound
from zope.component import getUtility
from zope.component import queryMultiAdapter
from zope.index.text.parsetree import ParseError

from pyramid.renderers import get_renderer
from pyramid.security import has_permission
from pyramid.security import effective_principals
from pyramid.security import remember
from pyramid.traversal import resource_path
from pyramid.traversal import find_interface
from pyramid.url import resource_url

from pyramid_formish import ValidationError

from repoze.workflow import get_workflow

from repoze.lemonade.content import create_content
from repoze.sendmail.interfaces import IMailDelivery

from karl.views.api import TemplateAPI
from karl.views.batch import get_catalog_batch

from karl.models.interfaces import ICommunity
from karl.models.interfaces import IProfile
from karl.models.interfaces import ICatalogSearch
from karl.models.interfaces import IInvitation

from karl.utilities.image import thumb_url
from karl.utilities.interfaces import IRandomId

from karl.utils import find_profiles
from karl.utils import find_site
from karl.utils import find_users
from karl.utils import get_setting

from karl.views.peopledirectory import profile_photo_rows
from karl.views.forms.widgets import ManageMembersWidget
from karl.views.interfaces import IInvitationBoilerplate
from karl.views.utils import handle_photo_upload
from karl.views.utils import photo_from_filestore_view

PROFILE_THUMB_SIZE = (75, 100)

def _get_manage_actions(community, request):

    # Filter the actions based on permission in the **community**
    actions = []
    if has_permission('moderate', community, request):
        actions.append(('Manage Members', 'manage.html'))
        actions.append(('Add Existing', 'add_existing.html'))
        actions.append(('Invite New', 'invite_new.html'))

    return actions

def _get_actions_menu(context, request, actions):
    """
    Convert UX1 actions to UX2 menu.
    """
    return {'actions': [
        {'title': title, 'url': request.resource_url(context, view)}
        for title, view in actions]}

def _get_common_email_info(community, community_href):
    info = {}
    info['system_name'] = get_setting(community, 'system_name', 'KARL')
    info['system_email_domain'] = get_setting(community,
                                              'system_email_domain')
    info['from_name'] = '%s invitation' % info['system_name']
    info['from_email'] = 'invitation@%s' % info['system_email_domain']
    info['c_title'] = community.title
    info['c_description'] = community.description
    info['c_href'] = community_href
    info['mfrom'] = '%s <%s>' % (info['from_name'], info['from_email'])

    return info

def _member_profile_batch(context, request):
    community = find_interface(context, ICommunity)
    member_names = community.member_names
    profiles_path = resource_path(find_profiles(context))
    batch = get_catalog_batch(
        context, request,
        batch_size = 12,
        interfaces = [IProfile],
        path={'query': profiles_path, 'depth': 1},
        allowed={'query': effective_principals(request), 'operator': 'or'},
        name = list(member_names),
        sort_index='lastfirst',
        )
    return batch

def show_members_view(context, request):
    """Default view of community members (with/without pictures)."""

    layout = request.layout_manager.layout
    layout.page_title = 'Community Members'
    api = TemplateAPI(context, request, layout.page_title)

    # Filter the actions based on permission in the **community**
    community = find_interface(context, ICommunity)
    actions = _get_manage_actions(community, request)
    actions_menu = _get_actions_menu(context, request, actions)

    # Did we get the "show pictures" flag?
    list_view = request.view_name == 'list_view.html'
    pictures_href = request.resource_url(context)
    list_href = request.resource_url(context, 'list_view.html')
    submenu = [  # deprecated in ux2
        {'label': 'Show Pictures',
         'href': pictures_href, 'make_link': list_view},
        {'label': 'Hide Pictures',
         'href': list_href, 'make_link': not(list_view)},
        ]

    formats = [   # ux2
        {'name': 'tabular',
         'selected': list_view,
         'bs-icon': 'icon-th-list',
         'url': list_href,
         'title': 'Tabular View',
         'description': 'Show table'},
        {'name': 'picture',
         'selected': not list_view,
         'bs-icon': 'icon-th',
         'url': pictures_href,
         'title': 'Picture View',
         'description': 'Show pictures'}
    ]

    profiles = find_profiles(context)
    member_batch = _member_profile_batch(context, request)
    member_entries = member_batch['entries']
    moderator_names = community.moderator_names

    member_info = []
    for i in range(len(member_entries)):
        derived = {}
        entry = member_entries[i]
        derived['title'] = entry.title
        derived['href'] = resource_url(entry, request)
        derived['position'] = entry.position
        derived['organization'] = entry.organization
        derived['phone'] = entry.phone
        derived['department'] = entry.department
        derived['email'] = entry.email
        derived['city'] = entry.location

        photo = entry.get('photo')
        if photo is not None:
            derived['photo_url'] = thumb_url(photo, request,
                                             PROFILE_THUMB_SIZE)
        else:
            derived['photo_url'] = api.static_url + "/images/defaultUser.gif"

        derived['is_moderator'] = entry.__name__ in moderator_names
        # Chameleon's tal:repeat and repeat variable support for
        # things like index is pretty iffy.  Fix the entry info to
        # supply the CSS class information.
        derived['css_class'] = 'photoProfile'
        if derived['is_moderator']:
            derived['css_class'] += ' moderator'
        member_info.append(derived)

    moderator_info = []
    profiles = find_profiles(context)
    for moderator_name in moderator_names:
        if moderator_name in profiles:
            derived = {}
            profile = profiles[moderator_name]
            if not has_permission('view', profile, request):
                continue
            derived['title'] = profile.title
            derived['href'] = resource_url(profile, request)
            moderator_info.append(derived)

    renderer_data = dict(
        api=api,  # deprecated in ux2
        actions=actions,  # deprecated in ux2
        actions_menu=actions_menu,
        submenu=submenu,  # deprecated in ux2
        formats=formats,
        moderators=moderator_info,  # deprecated in ux2
        members=member_info,  # deprecated in ux2
        batch=member_batch,
        batch_info=member_batch,  # deprecated in ux2
        hide_pictures=list_view)  # deprecated in ux2

    if not list_view:
        renderer_data['rows'] = profile_photo_rows(
            member_batch['entries'], request, api)

    return renderer_data


def _send_moderators_changed_email(community,
                                   community_href,
                                   new_moderators,
                                   old_moderators,
                                   cur_moderators,
                                   prev_moderators):
    info = _get_common_email_info(community, community_href)
    subject_fmt = 'Change in moderators for %s'
    subject = subject_fmt % info['c_title']
    body_template = get_renderer(
        'templates/email_moderators_changed.pt').implementation()

    profiles = find_profiles(community)
    all_moderators = cur_moderators | prev_moderators
    to_profiles = [profiles[name] for name in all_moderators]
    to_addrs = ["%s <%s>" % (p.title, p.email) for p in to_profiles]

    mailer = getUtility(IMailDelivery)
    msg = Message()
    msg['From'] = info['mfrom']
    msg['To'] = ",".join(to_addrs)
    msg['Subject'] = subject
    body = body_template(
        system_name=info['system_name'],
        community_href=info['c_href'],
        community_name=info['c_title'],
        new_moderators=[profiles[name].title for name in new_moderators],
        old_moderators=[profiles[name].title for name in old_moderators],
        cur_moderators=[profiles[name].title for name in cur_moderators],
        prev_moderators=[profiles[name].title for name in prev_moderators]
        )

    if isinstance(body, unicode):
        body = body.encode("UTF-8")

    msg.set_payload(body, "UTF-8")
    msg.set_type('text/html')
    mailer.send(to_addrs, msg)

class ManageMembersFormController(object):
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.community = find_interface(context, ICommunity)
        self.profiles = find_profiles(self.community)

    def _getInvitations(self):
        L = []
        for invitation in self.context.values():
            if IInvitation.providedBy(invitation):
                L.append(invitation)
        return L

    def form_defaults(self):
        records = []
        community = self.community
        profiles = self.profiles
        member_names = community.member_names
        moderator_names = community.moderator_names
        for mod_name in moderator_names:
            profile = profiles[mod_name]
            sortkey = (0, '%s, %s' % (profile.lastname, profile.firstname))
            record = {
                'sortkey':sortkey,
                'name':mod_name,
                'title':profile.title,
                'moderator':True,
                'member':True,
                'resend':False,
                'remove':False,
                'invite':False,
                }
            records.append(record)
        for mem_name in member_names:
            if mem_name in moderator_names:
                continue
            profile = profiles[mem_name]
            sortkey = (1, '%s, %s' % (profile.lastname, profile.firstname))
            record = {
                'sortkey':sortkey,
                'name':mem_name,
                'title':profile.title,
                'member':True,
                'moderator':False,
                'resend':False,
                'remove':False,
                'invite':False,
                }
            records.append(record)
        for invitation in self._getInvitations():
            sortkey = (2, invitation.email)
            record = {
                'sortkey':sortkey,
                'title':invitation.email,
                'name':invitation.__name__,
                'member':False,
                'moderator':False,
                'resend':False,
                'remove':False,
                'invite':True,
                }
            records.append(record)
        records.sort(key=lambda x: x['sortkey'])
        return {'members':records}

    def form_fields(self):
        class Member(schemaish.Structure):
            name = schemaish.String()
            title = schemaish.String()
            moderator = schemaish.Boolean()
            member = schemaish.String()
            resend = schemaish.Boolean()
            remove = schemaish.Boolean()
        members = schemaish.Sequence(Member())
        members.title = ''
        num_moderators = len(self.community.moderator_names)
        members.num_moderators = num_moderators
        return [('members', members)]

    def form_widgets(self, fields):
        return {
            'members':ManageMembersWidget(),
            'members.*.name':formish.widgets.Hidden(),
            'members.*.title':formish.widgets.Input(readonly=True),
            'members.*.moderator':formish.widgets.Checkbox(),
            'members.*.member':formish.widgets.Hidden(),
            'members.*.resend':formish.widgets.Checkbox(),
            'members.*.remove':formish.widgets.Checkbox(),
            }

    def __call__(self):
        community = self.community
        context = self.context
        request = self.request
        layout = request.layout_manager.layout

        layout.page_title = u'Manage Community Members'
        api = TemplateAPI(context, request, layout.page_title)
        actions = _get_manage_actions(community, request)
        actions_menu = _get_actions_menu(context, request, actions)
        desc = ('Use the form below to remove members or to resend invites '
                'to people who have not accepted your invitation to join '
                'this community.')
        return {'api': api,  # deprecated in ux2
                'actions': actions,  # deprecated in ux2
                'page_title': layout.page_title,  # deprecated in ux2
                'actions_menu': actions_menu,
                'page_description': desc}

    def handle_cancel(self):
        return HTTPFound(location=resource_url(self.context, self.request))

    def handle_submit(self, converted):
        results = []
        community = self.community
        community_href = resource_url(community, self.request)
        context = self.context
        request = self.request
        moderators = community.moderator_names # property
        members = community.member_names # property
        invitation_names = [ x.__name__ for x in self._getInvitations() ]

        members_group_name = community.members_group_name
        moderators_group_name = community.moderators_group_name

        users = find_users(context)

        results = []

        for record in converted['members']:
            name = record['name']
            if record['remove']:
                if name in members:
                    users.remove_group(name, members_group_name)
                    results.append('Removed member %s' % record['title'])
                if name in moderators:
                    users.remove_group(name, moderators_group_name)
                    results.append('Removed moderator %s' %
                                   record['title'])
                if name in invitation_names:
                    del context[name]
                    results.append('Removed invitation %s' %
                                   record['title'])
            else:
                if record['resend']:
                    invitation = context.get(name)
                    _send_invitation_email(request, community, community_href,
                                           invitation)
                    results.append('Resent invitation to %s'%
                                   record['title'])
                else:
                    if (name in moderators) and (not record['moderator']):
                        users.remove_group(name, moderators_group_name)
                        results.append('%s is no longer a moderator'%
                                       record['title'])
                    if (not name in moderators) and record['moderator']:
                        users.add_group(name, moderators_group_name)
                        results.append('%s is now a moderator' %
                                       record['title'])

        # Invariant: Don't allow removal of the last moderator.
        if not community.moderator_names:
            transaction.abort()
            raise ValidationError(
                members="Must leave at least one moderator for community.")

        cur_moderators = community.moderator_names
        new_moderators = cur_moderators - moderators
        old_moderators = moderators - cur_moderators
        if new_moderators or old_moderators:
            _send_moderators_changed_email(community, community_href,
                                           new_moderators, old_moderators,
                                           cur_moderators, moderators)
        joined_result = ', '.join(results)
        status_message = 'Membership information changed: %s' % joined_result
        location = resource_url(context, request, "manage.html",
                             query={"status_message": status_message})
        return HTTPFound(location=location)


def _send_aeu_emails(community, community_href, profiles, text):
    # To make reading the add_existing_user_view easier, move the mail
    # delivery part here.

    info = _get_common_email_info(community, community_href)
    subject_fmt = 'You have been added to the %s community'
    subject = subject_fmt % info['c_title']
    body_template = get_renderer(
        'templates/email_add_existing.pt').implementation()
    html_body = text

    mailer = getUtility(IMailDelivery)
    for profile in profiles:
        to_email = profile.email

        msg = Message()
        msg['From'] = info['mfrom']
        msg['To'] = to_email
        msg['Subject'] = subject
        body = body_template(
            system_name=info['system_name'],
            community_href=info['c_href'],
            community_name=info['c_title'],
            community_description=info['c_description'],
            personal_message=html_body,
            )

        if isinstance(body, unicode):
            body = body.encode("UTF-8")

        msg.set_payload(body, "UTF-8")
        msg.set_type('text/html')
        mailer.send([to_email,], msg)


class AddExistingUserFormController(object):
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.community = find_interface(context, ICommunity)
        self.profiles = find_profiles(context)

    def form_fields(self):
        return [
            ('users', schemaish.Sequence(schemaish.String(
                validator=validator.Required()
                ))
             ),
            ('text', schemaish.String()
             ),
            ]

    def form_widgets(self, fields):
        return {
            'users':karlwidgets.UserProfileLookupWidget(),
            'text': karlwidgets.RichTextWidget(),
            }

    def __call__(self):
        community = self.community
        context = self.context
        request = self.request
        profiles = self.profiles
        layout = request.layout_manager.layout

        # Handle userid passed in via GET request
        # Moderator would get here by clicking a link in an email to grant a
        # user's request to join this community.
        add_user_id = request.params.get("user_id", None)
        if add_user_id is not None:
            profile = profiles.get(add_user_id, None)
            if profile is not None:
                return _add_existing_users(context, community, [profile,],
                                           "", request)

        system_name = get_setting(context, 'system_name', 'KARL')

        layout.page_title = u'Add Existing %s Users' % system_name
        api = TemplateAPI(context, request, layout.page_title)
        actions = _get_manage_actions(community, request)
        actions_menu = _get_actions_menu(context, request, actions)
        desc = ('Type the first few letters of the name of the person you '
                'would like to add to this community, select their name, '
                'and press submit. The short message below is included '
                'along with the text of your invite.')
        return {'api': api,   # deprecated in ux2
                'actions': actions,# deprecated in ux2
                'page_title': layout.page_title,# deprecated in ux2
                'actions_menu': actions_menu,
                'page_description': desc}

    def handle_submit(self, converted):
        request = self.request
        context = self.context
        community = self.community
        profiles = self.profiles
        usernames = converted['users']
        users = []
        for username in usernames:
            if username not in profiles:
                raise ValidationError(users='%s is not a valid profile' %
                                      username)
            users.append(profiles[username])
        return _add_existing_users(context, community, users,
                                   converted['text'], request)

    def handle_cancel(self):
        return HTTPFound(location=resource_url(self.context, self.request))

def _add_existing_users(context, community, profiles, text, request):
    users = find_users(community)
    for profile in profiles:
        group_name = community.members_group_name
        user_name = profile.__name__
        users.add_group(user_name, group_name)

    # Generate HTML and text mail messages and send a mail for
    # each user added to the community.
    community_href = resource_url(community, request)
    _send_aeu_emails(community, community_href, profiles, text)

    # We delivered invitation messages to each user.  Redirect to
    # Manage Members with a status message.
    n = len(profiles)
    if n == 1:
        msg = 'One member added and email sent.'
    else:
        fmt = '%s members added and emails sent.'
        msg = fmt % len(profiles)
    location = resource_url(context, request, 'manage.html',
                         query={'status_message': msg})
    return HTTPFound(location=location)

def accept_invitation_photo_view(context, request):
    return photo_from_filestore_view(context, request, 'accept-invitation')

class AcceptInvitationFormController(object):
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.community = find_interface(context, ICommunity)
        self.profiles = find_profiles(context)
        self.api = TemplateAPI(context, request)
        self.filestore = get_filestore(context, request, 'accept-invitation')

    def form_fields(self):
        required = validator.Required()
        min_pw_length = int(get_setting(self.context, 'min_pw_length', 6))
        pwlen = validator.Length(min_pw_length)
        username = karlvalidators.RegularExpression(
            r'^[\w-]+$',
            'Username must contain only letters, numbers, and dashes')
        fields = [
            ('username', schemaish.String(validator=validator.All(required,
                                                                  username))),
            ('password', schemaish.String(
                validator=validator.All(required, pwlen))),
            ('password_confirm', schemaish.String(
                validator=validator.All(required, pwlen))),
            ('firstname', schemaish.String(validator=required)),
            ('lastname', schemaish.String(validator=required)),
            ('phone', schemaish.String()),
            ('extension', schemaish.String()),
            ('organization', schemaish.String()),
            ('country', schemaish.String(
                validator=validator.All(
                            validator.OneOf(countries.as_dict.keys()),
                            validator.Required()),
                ),
            ),
            ('location', schemaish.String()),
            ('department', schemaish.String()),
            ('position', schemaish.String()),
            ('websites', schemaish.Sequence(
                schemaish.String(validator=validator.URL()))),
            ('languages', schemaish.String()),
            ('biography', schemaish.String()),
            ('photo', schemaish.File()),
            ('date_format', schemaish.String(
                validator=validator.OneOf(cultures.as_dict.keys()))),
            ]

        r = queryMultiAdapter((self.context, self.request),
                              IInvitationBoilerplate)
        if r is None:
            r = DefaultInvitationBoilerplate(self.context)
        if r.terms_and_conditions:
            fields.append(
                ('terms_and_conditions',
                 schemaish.Boolean(validator=validator.Equal(True)))
            )
        if r.privacy_statement:
            fields.append(
                ('accept_privacy_policy',
                 schemaish.Boolean(validator=validator.Equal(True)))
            )
        return fields

    def form_widgets(self, fields):
        default_icon = self.api.static_url + '/images/defaultUser.gif'
        system_name = get_setting(self.context, 'system_name', 'KARL')
        widgets = {
            'biography': karlwidgets.RichTextWidget(),
            'password':formish.Password(),
            'password_confirm':formish.Password(),
            'country':formish.SelectChoice(countries),
            'photo':karlwidgets.PhotoImageWidget(
                filestore=self.filestore,
                url_base=resource_url(self.context, self.request, 'photo'),
                image_thumbnail_default=default_icon),
            'date_format':formish.SelectChoice(cultures),
            'websites': formish.TextArea(
                rows=3,
                converter_options={'delimiter':'\n'}),
            }

        r = queryMultiAdapter((self.context, self.request),
                              IInvitationBoilerplate)
        if r is None:
            r = DefaultInvitationBoilerplate(self.context)
        terms_text = r.terms_and_conditions
        if terms_text:
            widgets['terms_and_conditions'] = (
                karlwidgets.AcceptFieldWidget(
                    terms_text, 'the %s Terms and Conditions' % system_name
                ))
        privacy_text = r.privacy_statement
        if privacy_text:
            widgets['accept_privacy_policy'] = (
                karlwidgets.AcceptFieldWidget(
                    privacy_text, 'the %s Privacy Policy' % system_name
                ))
        return widgets

    def handle_cancel(self):
        return HTTPFound(location=resource_url(self.context, self.request))

    def handle_submit(self, converted):
        context = self.context
        community = self.community
        request = self.request
        users = find_users(context)
        profiles = self.profiles

        password = converted['password']
        password_confirm = converted['password_confirm']

        if password != password_confirm:
            msg = 'Mismatched password and confirm'
            raise ValidationError(password_confirm=msg, password=msg)

        username = converted['username']
        if username in profiles:
            raise ValidationError(username='Username already taken')

        community_href = resource_url(community, request)
        groups = [ community.members_group_name ]
        users.add(username, username, password, groups)
        remember_headers = remember(request, username)
        profile = create_content(
            IProfile,
            firstname=converted['firstname'],
            lastname=converted['lastname'],
            email=context.email,
            phone=converted['phone'],
            extension=converted['extension'],
            department=converted['department'],
            position=converted['position'],
            organization=converted['organization'],
            location=converted['location'],
            country=converted['country'],
            websites=converted['websites'],
            date_format=converted['date_format'],
            biography=converted['biography'],
            languages=converted['languages']
            )
        profiles[username] = profile
        workflow = get_workflow(IProfile, 'security')
        if workflow is not None:
            workflow.initialize(profile)
        try:
            handle_photo_upload(profile, converted)
        except Invalid, e:
            raise ValidationError(**e.error_dict)

        del context.__parent__[context.__name__]
        url = resource_url(community, request,
                        query={'status_message':'Welcome!'})
        _send_ai_email(community, community_href, username, profile)
        self.filestore.clear()
        return HTTPFound(headers=remember_headers, location=url)

    def __call__(self):
        community_name = self.community.title
        context = self.context

        system_name = get_setting(context, 'system_name', 'KARL')

        desc = ('You have been invited to join the "%s" in %s.  Please begin '
                'by creating a %s login with profile information.' %
                (community_name, system_name, system_name))
        return {'api':self.api,
                'page_title':'Accept %s Invitation' % system_name,
                'page_description':desc}


def _send_ai_email(community, community_href, username, profile):
    """Send email to user who has accepted a community invitation.
    """
    info = _get_common_email_info(community, community_href)
    subject_fmt = 'Thank you for joining the %s community'
    subject = subject_fmt % info['c_title']
    body_template = get_renderer(
        'templates/email_accept_invitation.pt').implementation()

    mailer = getUtility(IMailDelivery)
    msg = Message()
    msg['From'] = info['mfrom']
    msg['To'] = profile.email
    msg['Subject'] = subject
    body = body_template(
        community_href=info['c_href'],
        community_name=info['c_title'],
        community_description=info['c_description'],
        username=username,
        )

    if isinstance(body, unicode):
        body = body.encode("UTF-8")

    msg.set_payload(body, "UTF-8")
    msg.set_type('text/html')
    mailer.send([profile.email,], msg)

class InviteNewUsersFormController(object):
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.community = find_interface(context, ICommunity)

    def form_fields(self):
        email = schemaish.String(validator=validator.Email())
        return [
            ('email_addresses',
             schemaish.Sequence(email, validator=validator.Required())),
            ('text',
             schemaish.String()),
            ]

    def form_widgets(self, fields):
        return {
            'email_addresses':formish.TextArea(
                converter_options={'delimiter':'\n'}),
            'text':karlwidgets.RichTextWidget(),
            }

    def __call__(self):
        community = self.community
        context = self.context
        request = self.request
        layout = request.layout_manager.layout
        system_name = get_setting(context, 'system_name', 'KARL')

        layout.page_title = u'Invite New %s Users' % system_name
        api = TemplateAPI(context, request, layout.page_title)
        actions = _get_manage_actions(community, request)
        actions_menu = _get_actions_menu(context, request, actions)
        desc = ('Type email addresses (one per line) of people you would '
                'like to add to your community. The short message below is '
                'included along with the text of your invite.')
        return {'api': api,    # deprecated in ux2
                'actions': actions,    # deprecated in ux2
                'page_title': layout.page_title,    # deprecated in ux2
                'actions_menu': actions_menu,
                'page_description': desc}

    def handle_cancel(self):
        return HTTPFound(location=resource_url(self.context, self.request))

    def handle_submit(self, converted):
        context = self.context
        request = self.request
        community = self.community
        random_id = getUtility(IRandomId)
        members = community.member_names | community.moderator_names
        community_href = resource_url(community, request)

        search = ICatalogSearch(context)

        addresses = converted['email_addresses']
        html_body = converted['text']

        ninvited = nadded = nignored = 0

        for email_address in addresses:
            # Check for existing members
            total, docids, resolver = search(email=email_address.lower(),
                                             interfaces=[IProfile,])

            if total:
                # User is already a member of Karl
                profile = resolver(docids[0])

                if profile.__name__ in members:
                    # User is a member of this community, do nothing
                    nignored += 1

                else:
                    # User is in Karl but not in this community.  If user is
                    # active, just add them to the community as though we had
                    # used the add existing user form.
                    if profile.security_state == 'active':
                        _add_existing_users(context, community, [profile,],
                                            html_body, request)
                        nadded += 1
                    else:
                        msg = ('Address, %s, belongs to a user which has '
                               'previously been deactivated.  This user must '
                               'be reactivated by a system administrator '
                               'before they can be added to this community.' %
                               email_address)
                        raise ValidationError(email_addresses=msg)

            else:
                # Invite new user to Karl
                invitation = create_content(
                    IInvitation,
                    email_address,
                    html_body
                )
                while 1:
                    name = random_id()
                    if name not in context:
                        context[name] = invitation
                        break

                _send_invitation_email(request, community, community_href,
                                       invitation)
                ninvited += 1

        status = ''

        if ninvited:
            if ninvited == 1:
                status = 'One user invited.  '
            else:
                status = '%d users invited.  ' % ninvited

        if nadded:
            if nadded == 1:
                status += 'One existing Karl user added to community.  '
            else:
                status += ('%d existing Karl users added to community.  '
                           % nadded)
        if nignored:
            if nignored == 1:
                status += 'One user already member.'
            else:
                status += '%d users already members.' % nignored

        location = resource_url(context, request, 'manage.html',
                             query={'status_message': status})

        return HTTPFound(location=location)

def _send_invitation_email(request, community, community_href, invitation):
    mailer = getUtility(IMailDelivery)
    info = _get_common_email_info(community, community_href)
    subject_fmt = 'Please join the %s community at %s'
    info['subject'] = subject_fmt % (info['c_title'],
                                     info['system_name'])
    body_template = get_renderer(
        'templates/email_invite_new.pt').implementation()

    msg = Message()
    msg['From'] = info['mfrom']
    msg['To'] = invitation.email
    msg['Subject'] = info['subject']
    body = body_template(
        system_name=info['system_name'],
        community_href=info['c_href'],
        community_name=info['c_title'],
        community_description=info['c_description'],
        personal_message=invitation.message,
        invitation_url=resource_url(invitation.__parent__, request,
                                 invitation.__name__)
        )

    if isinstance(body, unicode):
        body = body.encode("UTF-8")

    msg.set_payload(body, "UTF-8")
    msg.set_type('text/html')
    mailer.send([invitation.email,], msg)


# This view is in function in KARL3 (UX1)
def jquery_member_search_view(context, request):
    prefix = request.params['val'].lower()
    community = find_interface(context, ICommunity)
    member_names = community.member_names
    moderator_names = community.moderator_names
    community_member_names = member_names.union(moderator_names)
    query = dict(
        member_name='%s*' % prefix,
        sort_index='title',
        limit=20,
        )
    searcher = ICatalogSearch(context)
    try:
        total, docids, resolver = searcher(**query)
        profiles = filter(None, map(resolver, docids))
        records = [dict(
                    id = profile.__name__,
                    text = profile.title,
                    )
                   for profile in profiles
                   if profile.__name__ not in community_member_names
                   and profile.security_state != 'inactive']
    except ParseError:
        records = []
    result = JSONEncoder().encode(records)
    return Response(result, content_type="application/x-json")


# This view is made for KARL UX2.
# We follow the payload format that the new client requires
#
# From autocomplete documentation:
#
# - The data from local data, a url or a callback can come in two variants:
#
#   An Array of Strings:
#   [ "Choice1", "Choice2" ]
#   An Array of Objects with label and value properties:
#   [ { label: "Choice1", value: "value1" }, ... ]
#
def member_search_json_view(context, request):
    try:
        # Query parameter shall be 'term'.
        prefix = request.params['term']
    except UnicodeDecodeError:
        # not utf8, just return empty list since tags can't have these chars
        result = JSONEncoder().encode([])
        return Response(result, content_type="application/x-json")
    # case insensitive
    prefix = prefix.lower()
    community = find_interface(context, ICommunity)
    member_names = community.member_names
    moderator_names = community.moderator_names
    community_member_names = member_names.union(moderator_names)
    query = dict(
        member_name='%s*' % prefix,
        sort_index='title',
        limit=20,
        )
    searcher = ICatalogSearch(context)
    try:
        total, docids, resolver = searcher(**query)
        profiles = filter(None, map(resolver, docids))
        records = [dict(
                    value = profile.__name__,
                    label = profile.title,
                    )
                   for profile in profiles
                   if profile.__name__ not in community_member_names
                   and profile.security_state != 'inactive']
    except ParseError:
        records = []
    result = JSONEncoder().encode(records)
    return Response(result, content_type="application/x-json")





class DefaultInvitationBoilerplate(object):
    terms_and_conditions = ''
    privacy_statement = ''

    def __init__(self, context):
        site = find_site(context)
        legal = site.get('legal')
        if legal is not None:
            self.terms_and_conditions = legal.text
        privacy = site.get('privacy')
        if privacy is not None:
            self.privacy_statement = privacy.text
