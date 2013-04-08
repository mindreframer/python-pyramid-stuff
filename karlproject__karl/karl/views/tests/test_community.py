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

import mock
import unittest

from pyramid import testing

from karl import testing as karltesting

class RedirectCommunityViewTests(unittest.TestCase):
    def setUp(self):
        testing.cleanUp()

    def tearDown(self):
        testing.cleanUp()

    def _callFUT(self, context, request):
        from karl.views.community import redirect_community_view
        return redirect_community_view(context, request)

    def test_it(self):
        from karl.models.interfaces import ICommunity
        from zope.interface import directlyProvides
        context = testing.DummyModel()
        directlyProvides(context, ICommunity)
        context.default_tool = 'murg'
        request = testing.DummyRequest()
        response = self._callFUT(context, request)
        self.assertEqual(response.location, 'http://example.com/murg')

    def test_it_with_query(self):
        from karl.models.interfaces import ICommunity
        from zope.interface import directlyProvides
        context = testing.DummyModel()
        directlyProvides(context, ICommunity)
        context.default_tool = 'murg'
        request = testing.DummyRequest(GET={'status': 'married'})
        response = self._callFUT(context, request)
        self.assertEqual(response.location,
                         'http://example.com/murg?status=married')

    def test_it_notool(self):
        from karl.models.interfaces import ICommunity
        from zope.interface import directlyProvides
        context = testing.DummyModel()
        directlyProvides(context, ICommunity)
        request = testing.DummyRequest()
        response = self._callFUT(context, request)
        self.assertEqual(response.location, 'http://example.com/view.html')

class ShowCommunityViewTests(unittest.TestCase):
    def setUp(self):
        testing.cleanUp()

    def tearDown(self):
        testing.cleanUp()

    def _register(self):
        from zope.interface import Interface
        from karl.models.interfaces import ITagQuery
        from karl.models.interfaces import ICommunityInfo
        from karl.models.interfaces import ICatalogSearch
        from karl.models.interfaces import IGridEntryInfo
        from karl.models.adapters import CatalogSearch
        karltesting.registerAdapter(DummyTagQuery, (Interface, Interface),
                                    ITagQuery)
        karltesting.registerAdapter(DummyGridEntryAdapter,
                                    (Interface, Interface),
                                    IGridEntryInfo)
        karltesting.registerAdapter(DummyAdapter, (Interface, Interface),
                                    ICommunityInfo)
        karltesting.registerAdapter(CatalogSearch, (Interface), ICatalogSearch)

    def _callFUT(self, context, request):
        from karl.views.community import show_community_view
        return show_community_view(context, request)

    def _makeCommunity(self):
        from zope.interface import directlyProvides
        from karl.models.interfaces import ICommunity
        community = testing.DummyModel(title='thetitle')
        community.member_names = community.moderator_names = set()
        directlyProvides(community, ICommunity)
        foo = testing.DummyModel(__name__='foo')
        catalog = karltesting.DummyCatalog({1:'/foo'})
        karltesting.registerModels({'/foo':foo})
        community.catalog = catalog
        return community

    def test_not_a_member(self):
        from pyramid.url import resource_url
        self._register()
        context = self._makeCommunity()
        request = testing.DummyRequest()
        request.layout_manager = mock.Mock()
        layout = request.layout_manager.layout
        layout.head_data = dict(panel_data={})
        info = self._callFUT(context, request)
        self.assertEqual(info['actions'],
                         [('Edit', 'edit.html'),
                          ('Join', 'join.html'),
                          ('Delete', 'delete.html'),
                          ('Advanced', 'advanced.html'),
                         ])
        self.assertEqual(info['feed_url'],
                         resource_url(context, request, "atom.xml"))
        self.assertEqual(len(info['recent_items']), 1)
        self.assertEqual(info['recent_items'][0].context.__name__, 'foo')

    def test_already_member(self):
        self._register()
        context = self._makeCommunity()
        context.member_names = set(('userid',))
        context['profiles'] = testing.DummyModel()
        request = testing.DummyRequest()
        request.layout_manager = mock.Mock()
        layout = request.layout_manager.layout
        layout.head_data = dict(panel_data={})
        karltesting.registerDummySecurityPolicy('userid')
        info = self._callFUT(context, request)
        self.assertEqual(info['actions'],
                         [('Edit', 'edit.html'),
                          ('Delete', 'delete.html'),
                          ('Advanced', 'advanced.html'),
                         ])


class CommunityRecentItemsAjaxViewTests(unittest.TestCase):
    def setUp(self):
        testing.cleanUp()

    def tearDown(self):
        testing.cleanUp()

    def _register(self):
        from zope.interface import Interface
        from karl.models.interfaces import ICatalogSearch
        from karl.models.interfaces import IGridEntryInfo
        from karl.models.adapters import CatalogSearch
        karltesting.registerAdapter(
            DummyGridEntryAdapter, (Interface, Interface),
            IGridEntryInfo)
        karltesting.registerAdapter(CatalogSearch, (Interface), ICatalogSearch)

    def _callFUT(self, context, request):
        from karl.views.community import community_recent_items_ajax_view
        return community_recent_items_ajax_view(context, request)

    def _makeCommunity(self):
        from zope.interface import directlyProvides
        from karl.models.interfaces import ICommunity
        community = testing.DummyModel(title='thetitle')
        directlyProvides(community, ICommunity)
        foo = testing.DummyModel(__name__='foo')
        catalog = karltesting.DummyCatalog({1:'/foo'})
        karltesting.registerModels({'/foo':foo})
        community.catalog = catalog
        return community

    def test_simple(self):
        self._register()
        context = self._makeCommunity()
        request = testing.DummyRequest()
        info = self._callFUT(context, request)
        self.assertEqual(len(info['items']), 1)
        self.assertEqual(info['items'][0].context.__name__, 'foo')

class CommunityMembersAjaxViewTests(unittest.TestCase):
    def setUp(self):
        testing.cleanUp()

    def tearDown(self):
        testing.cleanUp()

    def _register(self):
        from zope.interface import Interface
        from karl.models.interfaces import ICatalogSearch
        from karl.models.interfaces import IGridEntryInfo
        from karl.models.adapters import CatalogSearch
        karltesting.registerAdapter(
            DummyGridEntryAdapter, (Interface, Interface),
            IGridEntryInfo)
        karltesting.registerAdapter(CatalogSearch, (Interface), ICatalogSearch)

    def _callFUT(self, context, request):
        from karl.views.community import community_members_ajax_view
        return community_members_ajax_view(context, request)

    def _makeCommunity(self):
        from zope.interface import directlyProvides
        from karl.models.interfaces import ICommunity
        community = testing.DummyModel(title='thetitle')
        catalog = karltesting.DummyCatalog({1: '/profiles/phred',
                                            2: '/profiles/bharney',
                                            3: '/profiles/wylma',
                                           })
        phred = testing.DummyModel(__name__='phred')
        bharney = testing.DummyModel(__name__='bharney')
        wylma = testing.DummyModel(__name__='wylma')
        karltesting.registerModels({'/profiles/phred':phred,
                                    '/profiles/bharney':bharney,
                                    '/profiles/wylma':wylma,
                                    })
        community.catalog = catalog
        community.member_names = set(['phred', 'bharney', 'wylma'])
        community.moderator_names = set(['bharney'])
        directlyProvides(community, ICommunity)
        return community

    def test_simple(self):
        self._register()
        context = self._makeCommunity()
        request = testing.DummyRequest()
        info = self._callFUT(context, request)
        self.assertEqual(len(info['items']), 3)
        self.assertEqual(info['items'][0].context.__name__, 'bharney')
        self.assertEqual(info['items'][1].context.__name__, 'phred')
        self.assertEqual(info['items'][2].context.__name__, 'wylma')

class RelatedCommunitiesAjaxViewTests(unittest.TestCase):
    def setUp(self):
        testing.cleanUp()

    def tearDown(self):
        testing.cleanUp()

    def _callFUT(self, context, request):
        from karl.views.community import related_communities_ajax_view
        return related_communities_ajax_view(context, request)

    def _register(self):
        from zope.interface import Interface
        from karl.models.interfaces import ICatalogSearch
        from karl.models.interfaces import IGridEntryInfo
        from karl.models.adapters import CatalogSearch
        karltesting.registerAdapter(
            DummyGridEntryAdapter, (Interface, Interface),
            IGridEntryInfo)
        karltesting.registerAdapter(CatalogSearch, (Interface), ICatalogSearch)

    def _makeCommunity(self, results=None):
        from zope.interface import directlyProvides
        from karl.models.interfaces import ICommunity
        if results is None:
            results = [{}]
        community = testing.DummyModel(title='Interests Align')
        catalog = karltesting.DummyCatalog(*results)
        community.catalog = catalog
        directlyProvides(community, ICommunity)
        return community

    def test_it_no_matches(self):
        from karl.models.interfaces import ICommunity
        self._register()
        context = self._makeCommunity()
        request = testing.DummyRequest()
        info = self._callFUT(context, request)
        self.assertEqual(info['items'], [])
        self.assertEqual(context.catalog.queries,
                         [{'interfaces': [ICommunity],
                           'limit': 5,
                           'reverse': True,
                           'sort_index': 'modified_date',
                           'texts': 'interests OR align',
                           'allowed': {'query': [], 'operator': 'or'}
                          }])

class FormControllerTestBase(unittest.TestCase):
    def setUp(self):
        testing.cleanUp()

    def tearDown(self):
        testing.cleanUp()

    def _registerDummyWorkflow(self):
        from repoze.workflow.testing import registerDummyWorkflow
        wf = DummyWorkflow(
            [{'transitions':['private'],'name': 'public', 'title':'Public'},
             {'transitions':['public'], 'name': 'private', 'title':'Private'}])
        workflow = registerDummyWorkflow('security', wf)
        return workflow

    def _register(self):
        from zope.interface import Interface
        from karl.models.interfaces import ITagQuery
        from pyramid_formish import IFormishRenderer
        karltesting.registerAdapter(DummyTagQuery, (Interface, Interface),
                                    ITagQuery)
        def renderer(template, args):
            return ''
        karltesting.registerUtility(renderer, IFormishRenderer)

    def _registerAddables(self, addables):
        from karl.views.interfaces import IToolAddables
        from zope.interface import Interface
        def tool_adapter(context, request):
            def adapter():
                return addables
            return adapter
        karltesting.registerAdapter(tool_adapter, (Interface, Interface),
                                    IToolAddables)

class AddCommunityFormControllerTests(FormControllerTestBase):
    def _makeOne(self, context, request):
        from karl.views.community import AddCommunityFormController
        return AddCommunityFormController(context, request)

    def test_form_defaults(self):
        workflow = self._registerDummyWorkflow()
        context = testing.DummyModel()
        request = testing.DummyRequest()
        controller = self._makeOne(context, request)
        defaults = controller.form_defaults()
        self.assertEqual(defaults['title'], '')
        self.assertEqual(defaults['tags'], [])
        self.assertEqual(defaults['description'], '')
        self.assertEqual(defaults['text'], '')
        self.assertEqual(defaults['tools'], [])
        self.assertEqual(defaults['security_state'], workflow.initial_state)

    def test_form_fields(self):
        self._registerDummyWorkflow()
        context = testing.DummyModel()
        request = testing.DummyRequest()
        controller = self._makeOne(context, request)
        fields = dict(controller.form_fields())
        self.failUnless('tags' in fields)
        self.failUnless('security_state' in fields)
        self.failUnless('default_tool' in fields)

    def test_form_widgets(self):
        self._registerDummyWorkflow()
        context = testing.DummyModel()
        request = testing.DummyRequest()
        controller = self._makeOne(context, request)
        widgets = controller.form_widgets([('security_state', True)])
        self.failUnless('tags' in widgets)
        self.failUnless('security_state' in widgets)
        self.failUnless('default_tool' in widgets)

    def test___call__(self):
        context = testing.DummyModel()
        request = testing.DummyRequest(layout_manager=mock.Mock())
        controller = self._makeOne(context, request)
        response = controller()
        self.failUnless('api' in response)
        self.assertEqual(response['api'].page_title, 'Add Community')
        self.assertEqual(
            request.layout_manager.layout.page_title, 'Add Community')

    def test_handle_cancel(self):
        context = testing.DummyModel()
        request = testing.DummyRequest()
        controller = self._makeOne(context, request)
        response = controller.handle_cancel()
        self.assertEqual(response.location, 'http://example.com/')

    def test_handle_submit_success(self):
        self._register()
        from zope.interface import directlyProvides
        from karl.models.interfaces import ISite
        from karl.models.interfaces import ICommunity
        from repoze.lemonade.interfaces import IContentFactory
        context = testing.DummyModel()
        directlyProvides(context, ISite)
        tags = context.tags = testing.DummyModel()
        _tagged = []
        def _update(item, user, tags):
            _tagged.append((item, user, tags))
        tags.update = _update
        karltesting.registerDummySecurityPolicy('userid')
        workflow = self._registerDummyWorkflow()
        karltesting.registerAdapter(lambda *arg: DummyCommunity,
                                    (ICommunity,),
                                    IContentFactory)
        dummy_tool_factory = DummyToolFactory()
        self._registerAddables([{'name':'blog', 'title':'blog',
                                 'component':dummy_tool_factory}])
        context.users = karltesting.DummyUsers({})
        context.catalog = karltesting.DummyCatalog({1:'/foo'})
        request = testing.DummyRequest()
        controller = self._makeOne(context, request)
        converted = {'title':'Thetitle yo',
                     'description':'thedescription',
                     'text':'thetext',
                     'tools': ['blog'],
                     'security_state': 'private',
                     'tags': ['foo'],
                     'default_tool': 'blog',
                     }
        result = controller.handle_submit(converted)
        rl = 'http://example.com/thetitle-yo/members/add_existing.html'
        self.failUnless(result.location.startswith(rl))
        community = context['thetitle-yo']
        self.assertEqual(community.title, 'Thetitle yo')
        self.assertEqual(community.description, 'thedescription')
        self.assertEqual(community.text, 'thetext')
        self.assertEqual(community.default_tool, 'blog')
        self.assertEqual(community.creator, 'userid')
        self.assertEqual(community.modified_by, 'userid')
        self.assertEqual(
            context.users.added_groups,
            [('userid', 'moderators'), ('userid', 'members') ]
        )
        self.assertEqual(dummy_tool_factory.added, True)
        self.assertEqual(len(_tagged), 1)
        self.assertEqual(_tagged[0][0], None)
        self.assertEqual(_tagged[0][1], 'userid')
        self.assertEqual(_tagged[0][2], ['foo'])
        self.assertEqual(workflow.transitioned[0]['to_state'], 'private')

        # try again w/ an invalid default_tool
        converted['title'] = 'Another title yo'
        converted['default_tool'] = 'wiki'
        result = controller.handle_submit(converted)
        community = context['another-title-yo']
        self.failUnless(community.default_tool is None)

class EditCommunityFormControllerTests(FormControllerTestBase):
    def _makeOne(self, context, request):
        from karl.views.community import EditCommunityFormController
        return EditCommunityFormController(context, request)

    def test_ctor(self):
        context = testing.DummyModel()
        request = testing.DummyRequest()
        controller = self._makeOne(context, request)
        self.assertEqual(controller.selected_tools, [])

    def test_form_defaults(self):
        self._registerDummyWorkflow()
        dummy_tool_factory = DummyToolFactory()
        dummy_tool_factory = DummyToolFactory(present=True)
        self._registerAddables([{'name':'blog', 'title':'blog',
                                 'component':dummy_tool_factory}])
        context = testing.DummyModel(
            title='title', description='description', text='text',
            default_tool='blog')
        request = testing.DummyRequest()
        controller = self._makeOne(context, request)
        defaults = controller.form_defaults()
        self.assertEqual(defaults['title'], context.title)
        self.assertEqual(defaults['tags'], [])
        self.assertEqual(defaults['description'], context.description)
        self.assertEqual(defaults['text'], context.text)
        self.assertEqual(defaults['default_tool'], 'blog')
        self.assertEqual(defaults['tools'], ['blog'])
        self.assertEqual(defaults['security_state'], None)

    def test_form_fields(self):
        self._registerDummyWorkflow()
        context = testing.DummyModel()
        request = testing.DummyRequest()
        controller = self._makeOne(context, request)
        fields = controller.form_fields()
        self.failUnless('tags' in dict(fields))
        self.failUnless('security_state' in dict(fields))

    def test_form_widgets(self):
        self._register()
        self._registerDummyWorkflow()
        context = testing.DummyModel()
        request = testing.DummyRequest()
        controller = self._makeOne(context, request)
        widgets = controller.form_widgets([('security_state', True)])
        self.failUnless('tags' in widgets)
        self.failUnless('default_tool' in widgets)
        self.failUnless('security_state' in widgets)

    def test___call__(self):
        context = testing.DummyModel(title='title')
        request = testing.DummyRequest()
        controller = self._makeOne(context, request)
        response = controller()
        self.failUnless('api' in response)
        self.assertEqual(response['api'].page_title, 'Edit title')

    def test_handle_submit_events(self):
        from zope.interface import Interface
        from karl.models.interfaces import IObjectModifiedEvent
        from karl.models.interfaces import IObjectWillBeModifiedEvent
        context = testing.DummyModel(
            title='oldtitle', description='oldescription',
            default_tool='overview')
        request = testing.DummyRequest()
        L = karltesting.registerEventListener((Interface, IObjectModifiedEvent))
        L2 = karltesting.registerEventListener((Interface,
                                                IObjectWillBeModifiedEvent))
        self._register()
        view = self._makeOne(context, request)
        converted = {'title':u'Thetitle yo',
                     'description':'thedescription',
                     'text':'thetext',
                     'security_state':'public',
                     'default_tool': 'files',
                     'tags': 'thetesttag',
                     'tools':[],
                      }
        view.handle_submit(converted)
        self.assertEqual(len(L), 2)
        self.assertEqual(len(L2), 2)

    def test_handle_submit_propchanges(self):
        karltesting.registerDummySecurityPolicy('user2')
        context = testing.DummyModel(
            title='oldtitle', description='oldescription',
            default_tool='overview', modified_by = 'user1')
        request = testing.DummyRequest()
        self._register()
        view = self._makeOne(context, request)
        converted = {'title':u'Thetitle yo',
                     'description':'thedescription',
                     'text':'thetext',
                     'security_state':'public',
                     'default_tool': 'files',
                     'tags': 'thetesttag',
                     'tools':[],
                      }
        view.handle_submit(converted)
        self.assertEqual(context.title, 'Thetitle yo')
        self.assertEqual(context.description, 'thedescription')
        self.assertEqual(context.text, 'thetext')
        self.assertEqual(context.modified_by, 'user2')

    def test_handle_submit_responselocation(self):
        context = testing.DummyModel(
            title='oldtitle', description='oldescription',
            default_tool='overview')
        request = testing.DummyRequest()
        self._register()
        view = self._makeOne(context, request)
        converted = {'title':u'Thetitle yo',
                     'description':'thedescription',
                     'text':'thetext',
                     'security_state':'public',
                     'default_tool': 'files',
                     'tags': 'thetesttag',
                     'tools':[],
                      }
        response = view.handle_submit(converted)
        self.assertEqual(response.location, 'http://example.com/')

    def test_handle_submit_sharingchange(self):
        from karl.testing import DummyCatalog
        karltesting.registerDummySecurityPolicy('userid')
        context = testing.DummyModel(
            title='oldtitle', description='oldescription',
            default_tool='overview')
        context.__acl__ = ['a']
        context.staff_acl = ['1']
        context.catalog = DummyCatalog()
        request = testing.DummyRequest()
        self._register()
        workflow = self._registerDummyWorkflow()
        view = self._makeOne(context, request)
        converted = {'title':u'Thetitle yo',
                     'description':'thedescription',
                     'text':'thetext',
                     'security_state':'public',
                     'default_tool': 'files',
                     'tags': 'thetesttag',
                     'tools':[],
                      }
        view.handle_submit(converted)
        self.assertEqual(workflow.transitioned[0]['to_state'], 'public')

    def test_handle_submit_nosharingchange(self):
        context = testing.DummyModel(
            title='oldtitle', description='oldescription',
            default_tool='overview')
        context.__acl__ = ['a']
        context.staff_acl = ['1']
        request = testing.DummyRequest()
        self._register()
        workflow = self._registerDummyWorkflow()
        view = self._makeOne(context, request)
        converted = {'title':u'Thetitle yo',
                     'description':'thedescription',
                     'text':'thetext',
                     'security_state':'private',
                     'default_tool': 'files',
                     'tools':[],
                     }
        view.handle_submit(converted)
        self.assertEqual(workflow.transitioned[0]['to_state'], 'private')

    def test_handle_submit_changetools(self):
        context = testing.DummyModel(title='oldtitle', default_tool='overview')
        request = testing.DummyRequest()
        blog_tool_factory = DummyToolFactory(present=True)
        calendar_tool_factory = DummyToolFactory(present=False)
        self._registerAddables([
            {'name':'blog', 'title':'blog', 'component':blog_tool_factory},
            {'name':'calendar', 'title':'calendar',
             'component':calendar_tool_factory}])
        self._register()
        view = self._makeOne(context, request)
        converted = {'title':u'Thetitle yo',
                     'description':'thedescription',
                     'text':'thetext',
                     'security_state':'public',
                     'calendar':'calendar',
                     'default_tool': 'overview',
                     'tools':['calendar'],
                     }
        view.handle_submit(converted)
        self.assertEqual(blog_tool_factory.removed, True)
        self.assertEqual(calendar_tool_factory.added, True)

class JoinCommunityViewTests(unittest.TestCase):
    def setUp(self):
        testing.cleanUp()

    def tearDown(self):
        testing.cleanUp()

    def _callFUT(self, context, request):
        from karl.views.community import join_community_view
        return join_community_view(context, request)

    def test_show_form(self):
        c = karltesting.DummyCommunity()
        site = c.__parent__.__parent__
        profiles = site["profiles"] = testing.DummyModel()
        profiles["user"] = karltesting.DummyProfile()
        karltesting.registerDummySecurityPolicy("user")
        request = testing.DummyRequest()
        response = self._callFUT(c, request)
        self.assertEqual(response['profile'], profiles["user"])
        self.assertEqual(response['community'], c)
        self.assertEqual(
            response['post_url'],
            "http://example.com/communities/community/join.html"
        )

    def test_submit_form(self):
        from repoze.sendmail.interfaces import IMailDelivery
        karltesting.registerDummyRenderer("templates/join_community.pt")

        c = karltesting.DummyCommunity()
        c.moderator_names = set(["moderator1", "moderator2"])
        site = c.__parent__.__parent__
        profiles = site["profiles"] = testing.DummyModel()
        profiles["user"] = karltesting.DummyProfile()
        profiles["moderator1"] = karltesting.DummyProfile()
        profiles["moderator2"] = karltesting.DummyProfile()

        mailer = karltesting.DummyMailer()
        karltesting.registerUtility(mailer, IMailDelivery)

        karltesting.registerDummySecurityPolicy("user")
        request = testing.DummyRequest({
            "form.submitted": "1",
            "message": "Message text.",
        })
        karltesting.registerDummyRenderer(
            'karl.views:templates/email_join_community.pt')
        response = self._callFUT(c, request)

        self.assertEqual(response.location,
                         "http://example.com/communities/community/"
                         "?status_message=Your+request+has+been+sent+"
                         "to+the+moderators.")
        self.assertEqual(len(mailer), 1)
        msg = mailer.pop()
        self.assertEqual(msg.mto, ["moderator1@x.org",
                                   "moderator2@x.org"])


class DeleteCommunityViewTests(unittest.TestCase):
    def setUp(self):
        testing.cleanUp()

    def tearDown(self):
        testing.cleanUp()

    def _callFUT(self, context, request):
        from karl.views.community import delete_community_view
        return delete_community_view(context, request)

    def _register(self):
        from zope.interface import Interface
        from karl.models.interfaces import ICommunityInfo
        from karl.models.interfaces import ICatalogSearch
        from karl.models.adapters import CatalogSearch
        karltesting.registerAdapter(DummyAdapter, (Interface, Interface),
                                    ICommunityInfo)
        karltesting.registerAdapter(CatalogSearch, (Interface), ICatalogSearch)

    def test_not_confirmed(self):
        from karl.testing import registerLayoutProvider
        registerLayoutProvider()

        request = testing.DummyRequest()
        context = testing.DummyModel(title='oldtitle')
        context.__name__  = 'thename'
        context.catalog = karltesting.DummyCatalog({})
        context.users = karltesting.DummyUsers({})
        karltesting.registerDummyRenderer('templates/delete_resource.pt')
        self._register()
        response = self._callFUT(context, request)
        self.assertTrue(isinstance(response, dict))

    def test_confirmed(self):
        request = testing.DummyRequest({'confirm':'1'})
        context = testing.DummyModel(title='oldtitle')
        parent = DummyParent()
        parent['thename'] = context
        parent.catalog = karltesting.DummyCatalog({})
        parent.users = karltesting.DummyUsers({})
        parent['profiles'] = testing.DummyModel()
        karltesting.registerDummyRenderer('templates/delete_resource.pt')
        self._register()
        karltesting.registerDummySecurityPolicy('userid')
        response = self._callFUT(context, request)
        self.assertEqual(parent.deleted, 'thename')
        self.assertEqual(response.location, 'http://example.com/')

class DummyToolFactory:
    def __init__(self, present=False):
        self.present = present

    def add(self, context, request):
        self.added = True

    def remove(self, context, request):
        self.removed = True

    def is_present(self, context, request):
        return self.present

class DummyParent(testing.DummyModel):
    def __delitem__(self, name):
        self.deleted = name

class DummyAdapter:
    def __init__(self, context, request):
        self.context = context
        self.request = request

class DummyTagQuery(DummyAdapter):
    tagswithcounts = []
    docid = 'ABCDEF01'

class DummyGridEntryAdapter(object):
    def __init__(self, context, request):
        self.context = context
        self.request = request

class DummyWorkflow:
    state_attr = 'security_state'
    initial_state = 'initial'
    def __init__(self, state_info=[
        {'name':'public', 'transitions':['private']},
        {'name':'private', 'transitions':['public']},
        ]):
        self.transitioned = []
        self._state_info = state_info

    def state_info(self, context, request):
        return self._state_info

    def transition_to_state(self, content, request, to_state, context=None,
                            guards=(), skip_same=True):
        self.transitioned.append({'to_state':to_state, 'content':content,
                                  'request':request, 'guards':guards,
                                  'context':context, 'skip_same':skip_same})

    def state_of(self, content):
        return getattr(content, self.state_attr, None)


class DummyForm:
    def __init__(self):
        self.widgets = {}
        self.allfields = []

    def validate(self, request, render, succeed):
        pass

    def __call__(self):
        pass

    def set_widget(self, name, field):
        self.widgets[name] = field
        self.allfields.append(field)

class DummySchema:
    def __init__(self, **kw):
        self.__dict__.update(kw)

class DummyCommunity:
    def __init__(self, title, description, text, creator):
        self.title = title
        self.description = description
        self.text = text
        self.creator = self.modified_by = creator
        self.members_group_name = 'members'
        self.moderators_group_name = 'moderators'
