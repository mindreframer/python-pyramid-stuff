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

import unittest

from zope.interface import Interface

from pyramid.testing import DummyModel
from pyramid.testing import DummyRequest
from pyramid.testing import cleanUp

from karl.testing import DummyCatalog
from karl.testing import DummyLayoutProvider
from karl.testing import DummySearchAdapter
from karl.testing import DummyTagQuery
from karl.testing import DummyFolderAddables
from karl.testing import DummyUsers

import karl.testing

class TestShowNetworkEventsView(unittest.TestCase):
    def setUp(self):
        cleanUp()

        self.parent = DummyModel(title='dummyparent')
        self.context = DummyModel(title='dummytitle', text='dummytext')
        self.context['attachments'] = DummyModel()
        self.parent['child'] = self.context
        self.parent.catalog = DummyCatalog()
        self.parent["profiles"] = DummyModel()
        users = self.parent.users = DummyUsers()
        users.add("userid", "userid", "password", [])

    def tearDown(self):
        cleanUp()

    def _callFUT(self, context, request):
        from karl.content.views.custom_folderviews import NetworkEventsView
        return NetworkEventsView(context, request)()

    def _registerAddables(self):
        from karl.views.interfaces import IFolderAddables
        karl.testing.registerAdapter(
            DummyFolderAddables, (Interface, Interface),
            IFolderAddables)

    def _registerTagbox(self):
        from karl.models.interfaces import ITagQuery
        karl.testing.registerAdapter(DummyTagQuery, (Interface, Interface),
                                     ITagQuery)

    def _registerKarlDates(self):
        d1 = 'Wednesday, January 28, 2009 08:32 AM'
        def dummy(date, flavor):
            return d1
        from karl.utilities.interfaces import IKarlDates
        karl.testing.registerUtility(dummy, IKarlDates)

    def _registerCatalogSearch(self):
        from karl.models.interfaces import ICatalogSearch
        karl.testing.registerAdapter(
            DummySearchAdapter, (Interface), ICatalogSearch)

    def _registerLayoutProvider(self):
        from karl.views.interfaces import ILayoutProvider

        ad = karl.testing.registerAdapter(DummyLayoutProvider,
                                          (Interface, Interface),
                                          ILayoutProvider)

    def _registerSecurityPolicy(self, permissions):
        if permissions is None:
            karl.testing.registerDummySecurityPolicy("userid")
        else:
            from pyramid.interfaces import IAuthenticationPolicy
            from pyramid.interfaces import IAuthorizationPolicy
            policy = DummySecurityPolicy("userid", permissions=permissions)
            karl.testing.registerUtility(policy, IAuthenticationPolicy)
            karl.testing.registerUtility(policy, IAuthorizationPolicy)

    def _register(self, permissions=None):
        self._registerAddables()
        self._registerKarlDates()
        self._registerCatalogSearch()
        self._registerTagbox()
        self._registerLayoutProvider()
        self._registerSecurityPolicy(permissions)

    def test_first_request(self):
        self._register()

        context = self.context
        request = DummyRequest()

        response = self._callFUT(context, request)
        self.assertEqual(len(response['actions']), 5)
        self.assertEqual(response['backto'],
                         {'href': 'http://example.com/',
                          'title': 'Home'})
        self.assertEqual(response['entries'], [])
        self.assertEqual(response['fb_years'][:3], ['2007', '2008', '2009'])
        self.assertEqual(len(response['fb_months']), 12)
        self.assertEqual(response['searchterm'], None)
        self.assertEqual(response['selected_year'], None)
        self.assertEqual(response['selected_month'], None)
        self.assertEqual(response['past_events_url'],
                         "http://example.com/child/?past_events=True")

    def test_with_searchterm(self):
        self._register()

        context = self.context
        request = DummyRequest({'searchterm':'someword'})

        response = self._callFUT(context, request)

        self.assertEqual(response['searchterm'], 'someword')
        self.assertEqual(response['selected_year'], None)
        self.assertEqual(response['selected_month'], None)

    def test_with_unparseable_searchterm(self):
        self._register()

        context = self.context
        request = DummyRequest({'searchterm':'the'})

        response = self._callFUT(context, request)

        self.assertEqual(response['searchterm'], 'the')
        self.assertEqual(response['selected_year'], None)
        self.assertEqual(response['selected_month'], None)

    def test_with_year_and_month(self):
        self._register()

        context = self.context
        request = DummyRequest({
                'year':'2007',
                'month':'3',
                })

        response = self._callFUT(context, request)

        self.assertEqual(response['searchterm'], None)
        self.assertEqual(response['selected_year'], '2007')
        self.assertEqual(response['selected_month'], '3')

    def test_past_events(self):
        self._register()

        context = self.context
        request = DummyRequest({
            'past_events': 'True',
        })

        response = self._callFUT(context, request)

        self.assertEqual(response['future_events_url'],
                         "http://example.com/child/?past_events=False")
        self.assertEqual(response['past_events_url'], None)

    def test_future_events(self):
        self._register()

        context = self.context
        request = DummyRequest({
            'past_events': 'False',
        })

        response = self._callFUT(context, request)

        self.assertEqual(response['past_events_url'],
                         "http://example.com/child/?past_events=True")
        self.assertEqual(response['future_events_url'], None)

    def test_read_only(self):
        self._register({self.context: ('view',),})
        request = DummyRequest()
        response = self._callFUT(self.context, request)
        self.assertEqual(response['actions'], [])

    def test_editable(self):
        self._register({self.context: ('view', 'edit'),})
        request = DummyRequest()
        response = self._callFUT(self.context, request)
        self.assertEqual(response['actions'], [('Edit', 'edit.html')])

    def test_deletable(self):
        self._register({self.context.__parent__: ('view', 'delete'),})
        request = DummyRequest()
        response = self._callFUT(self.context, request)
        self.assertEqual(response['actions'], [('Delete', 'delete.html')])

    def test_delete_is_for_children_not_container(self):
        self._register({self.context: ('view', 'delete'),})
        request = DummyRequest()
        response = self._callFUT(self.context, request)
        self.assertEqual(response['actions'], [])

    def test_creatable(self):
        self._register({self.context: ('view', 'create'),})
        request = DummyRequest()
        response = self._callFUT(self.context, request)
        self.assertEqual(response['actions'], [
            ('Add Folder', 'add_folder.html'), ('Add File', 'add_file.html')])

class TestShowNetworkNewsView(unittest.TestCase):
    def setUp(self):
        cleanUp()

        self.template_fn = 'templates/custom_folder.pt'

        self.parent = DummyModel(title='dummyparent')
        self.context = DummyModel(title='dummytitle', text='dummytext')
        self.context['attachments'] = DummyModel()
        self.parent['child'] = self.context
        self.parent.catalog = DummyCatalog()
        self.parent["profiles"] = DummyModel()
        users = self.parent.users = DummyUsers()
        users.add("userid", "userid", "password", [])

    def tearDown(self):
        cleanUp()

    def _callFUT(self, context, request):
        from karl.content.views.custom_folderviews import NetworkNewsView
        return NetworkNewsView(context, request)()

    def _registerAddables(self):
        from karl.views.interfaces import IFolderAddables
        karl.testing.registerAdapter(
            DummyFolderAddables, (Interface, Interface),
            IFolderAddables)

    def _registerTagbox(self):
        from karl.models.interfaces import ITagQuery
        karl.testing.registerAdapter(DummyTagQuery, (Interface, Interface),
                                     ITagQuery)

    def _registerKarlDates(self):
        d1 = 'Wednesday, January 28, 2009 08:32 AM'
        def dummy(date, flavor):
            return d1
        from karl.utilities.interfaces import IKarlDates
        karl.testing.registerUtility(dummy, IKarlDates)

    def _registerCatalogSearch(self):
        from karl.models.interfaces import ICatalogSearch
        karl.testing.registerAdapter(DummySearchAdapter,
                                     (Interface), ICatalogSearch)

    def _registerLayoutProvider(self):
        from karl.views.interfaces import ILayoutProvider

        ad = karl.testing.registerAdapter(
            DummyLayoutProvider,
            (Interface, Interface),
            ILayoutProvider)

    def _registerSecurityPolicy(self):
        karl.testing.registerDummySecurityPolicy("userid")

    def _register(self):
        self._registerAddables()
        self._registerKarlDates()
        self._registerCatalogSearch()
        self._registerTagbox()
        self._registerLayoutProvider()
        self._registerSecurityPolicy()

    def test_first_request(self):
        self._register()

        context = self.context
        request = DummyRequest()

        response = self._callFUT(context, request)
        self.assertEqual(len(response['actions']), 5)
        self.assertEqual(response['backto'],
                         {'href': 'http://example.com/',
                          'title': 'Home'})
        self.assertEqual(response['entries'], [])
        self.assertEqual(response['fb_years'][:3], ['2007', '2008', '2009'])
        self.assertEqual(len(response['fb_months']), 12)
        self.assertEqual(response['searchterm'], None)
        self.assertEqual(response['selected_year'], None)
        self.assertEqual(response['selected_month'], None)
        self.assertEqual(response['past_events_url'], None)

    def test_with_searchterm(self):
        self._register()

        context = self.context
        request = DummyRequest({'searchterm':'someword'})

        response = self._callFUT(context, request)

        self.assertEqual(response['searchterm'], 'someword')
        self.assertEqual(response['selected_year'], None)
        self.assertEqual(response['selected_month'], None)

    def test_with_year_and_month(self):
        self._register()

        context = self.context
        request = DummyRequest({
                'year':'2007',
                'month':'3',
                })

        response = self._callFUT(context, request)

        self.assertEqual(response['searchterm'], None)

from pyramid.security import Authenticated
from pyramid.security import Everyone

class DummySecurityPolicy:
    """ A standin for both an IAuthentication and IAuthorization policy """
    def __init__(self, userid=None, groupids=(), permissions=None):
        self.userid = userid
        self.groupids = groupids
        self.permissions = permissions or {}

    def authenticated_userid(self, request):
        return self.userid

    def effective_principals(self, request):
        effective_principals = [Everyone]
        if self.userid:
            effective_principals.append(Authenticated)
            effective_principals.append(self.userid)
            effective_principals.extend(self.groupids)
        return effective_principals

    def remember(self, request, principal, **kw):
        return []

    def forget(self, request):
        return []

    def permits(self, context, principals, permission):
        if context in self.permissions:
            permissions = self.permissions[context]
            return permission in permissions
        return False

    def principals_allowed_by_permission(self, context, permission):
        return self.effective_principals(None)
