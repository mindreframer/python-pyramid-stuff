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

from pyramid import testing

import karl.testing

class TestSiteView(unittest.TestCase):
    def setUp(self):
        testing.cleanUp()

    def tearDown(self):
        testing.cleanUp()
        
    def _callFUT(self, context, request):
        from karl.views.site import site_view
        return site_view(context, request)

    def test_no_communities(self):
        from karl.testing import DummyCommunity
        from karl.testing import DummyUsers
        karl.testing.registerDummySecurityPolicy("userid")
        c = DummyCommunity()
        context = c.__parent__.__parent__
        users = context.users = DummyUsers()
        users.add("userid", "userid", "password", [])
        request = testing.DummyRequest()
        response = self._callFUT(context, request)
        self.assertEqual(response.location, 'http://example.com/communities/')

    def test_one_community(self):
        from karl.testing import DummyCommunity
        from karl.testing import DummyUsers
        karl.testing.registerDummySecurityPolicy("userid")
        c = DummyCommunity()
        context = c.__parent__.__parent__
        users = context.users = DummyUsers()
        users.add("userid", "userid", "password",
                  ["group.community:community:members",])
        request = testing.DummyRequest()
        response = self._callFUT(context, request)
        self.assertEqual(response.location, 
                         'http://example.com/communities/community/')
        
    def test_multiple_communities(self):
        from karl.testing import DummyCommunity
        from karl.testing import DummyUsers
        karl.testing.registerDummySecurityPolicy("userid")
        c = DummyCommunity()
        context = c.__parent__.__parent__
        users = context.users = DummyUsers()
        users.add("userid", "userid", "password",
                  ["group.community:community:members",
                   "group.community:community2:members"])
        request = testing.DummyRequest()
        response = self._callFUT(context, request)
        self.assertEqual(response.location, 
                         'http://example.com/communities/')
        
    def test_user_home_path(self):
        from zope.interface.interfaces import IInterface
        from zope.interface import directlyProvides
        from pyramid.interfaces import ITraverserFactory
        from karl.testing import DummyCommunity
        from karl.testing import DummyProfile
        karl.testing.registerDummySecurityPolicy("userid")
        c = DummyCommunity()
        site = c.__parent__.__parent__
        directlyProvides(site, IInterface)
        c["foo"] = foo = testing.DummyModel()
        site["profiles"] = profiles = testing.DummyModel()
        profiles["userid"] = profile = DummyProfile()
        profile.home_path = "/communities/community/foo"
        karl.testing.registerAdapter(
            dummy_traverser_factory(foo), IInterface, ITraverserFactory
        )
        request = testing.DummyRequest()
        response = self._callFUT(site, request)
        self.assertEqual(response.location, 
                         "http://example.com/communities/community/foo/")
        
    def test_user_home_path_w_view(self):
        from zope.interface.interfaces import IInterface
        from zope.interface import directlyProvides
        from pyramid.interfaces import ITraverserFactory
        from karl.testing import DummyCommunity
        from karl.testing import DummyProfile
        karl.testing.registerDummySecurityPolicy("userid")
        c = DummyCommunity()
        site = c.__parent__.__parent__
        directlyProvides(site, IInterface)
        c["foo"] = foo = testing.DummyModel()
        site["profiles"] = profiles = testing.DummyModel()
        profiles["userid"] = profile = DummyProfile()
        profile.home_path = "/communities/community/foo/some_view.html"
        karl.testing.registerAdapter(
            dummy_traverser_factory(foo, "some_view.html",), 
            IInterface, ITraverserFactory
        )
        request = testing.DummyRequest()
        response = self._callFUT(site, request)
        self.assertEqual(response.location,
            "http://example.com/communities/community/foo/some_view.html")


# XXX these tests would break now, but actually we no longer
# use the component being tested here.
class TestVersioningStaticView(unittest.TestCase):
    def _callFUT(self, context, request):
        from karl.views.site import versioning_static_view
        return versioning_static_view(context, request)

    def test_with_version(self):
        request = testing.DummyRequest()
        request.subpath = ('r1234567890', 'abcdef', 'test.css')
        request.copy = lambda: request
        request.get_response = lambda app: None
        context = testing.DummyModel()
        self._callFUT(context, request)
        self.assertEqual(request.subpath, ('abcdef', 'test.css',))

    def test_without_version(self):
        request = testing.DummyRequest()
        request.subpath = ('abcdef', 'test.css')
        request.copy = lambda: request
        request.get_response = lambda app: None
        context = testing.DummyModel()
        self._callFUT(context, request)
        self.assertEqual(request.subpath, ('abcdef', 'test.css',))

class DummyMatch(testing.DummyModel):
    title = "somematch"

def dummy_traverser_factory(ob, name=''):
    def factory(root):
        def traverser(environ):
            return {'context':ob, 'view_name':name, 'subpath':[]}
        return traverser
    return factory
