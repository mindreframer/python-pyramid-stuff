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


class Test_redirect_up_view(unittest.TestCase):
    def _callFUT(self, context, request):
        from karl.views.redirects import redirect_up_view
        return redirect_up_view(context, request)

    def test_it(self):
        grand_parent = testing.DummyModel()
        parent = grand_parent["foo"] = testing.DummyModel()
        context = parent["bar"] = testing.DummyModel()
        response = self._callFUT(context, testing.DummyRequest())
        self.assertEqual(response.location, "http://example.com/foo/")


class Test_redirect_favicon_view(unittest.TestCase):
    def setUp(self):
        testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _callFUT(self, context, request):
        from karl.views.redirects import redirect_favicon
        return redirect_favicon(context, request)

    def test_it(self):
        context = testing.DummyModel()
        request = testing.DummyRequest()
        request.registry.settings['static_rev'] = 'rev'
        response = self._callFUT(context, request)
        self.assertEqual(response.location,
                         "http://example.com/static/rev/images/favicon.ico")


class Test_redirect_rss_view_xml(unittest.TestCase):
    def _callFUT(self, context, request):
        from karl.views.redirects import redirect_rss_view_xml
        return redirect_rss_view_xml(context, request)

    def test_it(self):
        context = testing.DummyModel()
        response = self._callFUT(context, testing.DummyRequest())
        self.assertEqual(response.location, "http://example.com/atom.xml")


class TestRedirectExpiredStatic(unittest.TestCase):
    def _callFUT(self, context, request):
        from karl.views.site import expired_static
        return expired_static(context, request)

    def test_it(self):
        context = testing.DummyModel()
        request = testing.DummyRequest()
        request.matchdict = dict(path=('r1234567', 'ux2', 'foo', 'bar.png'))
        request.registry.settings['static_rev'] = 'r1234'
        response = self._callFUT(context, request)
        self.assertEqual(response.location, "http://example.com/static/r1234/ux2/foo/bar.png")

    def test_norevision(self):
        # It also works if the revision is just omitted.
        context = testing.DummyModel()
        request = testing.DummyRequest()
        request.matchdict = dict(path=('ux2', 'foo', 'bar.png'))
        request.registry.settings['static_rev'] = 'r1234'
        response = self._callFUT(context, request)
        self.assertEqual(response.location, "http://example.com/static/r1234/ux2/foo/bar.png")

        context = testing.DummyModel()
        request = testing.DummyRequest()
        request.matchdict = dict(path=('r1234notarev', 'foo', 'bar.png'))
        request.registry.settings['static_rev'] = 'r1234'
        response = self._callFUT(context, request)
        self.assertEqual(response.location, "http://example.com/static/r1234/r1234notarev/foo/bar.png")

