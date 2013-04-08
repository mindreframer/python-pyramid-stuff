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

class TestUtilFunctions(unittest.TestCase):
    def test_find_users(self):
        from karl.utils import find_users
        context = testing.DummyModel()
        self.assertEqual(find_users(context), None)
        context.users = '1'
        self.assertEqual(find_users(context), '1')

    def test_find_catalog(self):
        from karl.utils import find_catalog
        context = testing.DummyModel()
        self.assertEqual(find_catalog(context), None)
        context.catalog = '1'
        self.assertEqual(find_catalog(context), '1')

    def test_find_tags(self):
        from karl.utils import find_tags
        context = testing.DummyModel()
        self.assertEqual(find_tags(context), None)
        context.tags = '1'
        self.assertEqual(find_tags(context), '1')

    def test_find_profiles(self):
        from karl.utils import find_profiles
        context = testing.DummyModel()
        self.assertEqual(find_profiles(context), None)
        pf = context['profiles'] = testing.DummyModel()
        self.failUnless(find_profiles(context) is pf)

    def test_find_communities(self):
        from karl.utils import find_communities
        context = testing.DummyModel()
        self.assertEqual(find_communities(context), None)
        cf = context['communities'] = testing.DummyModel()
        self.failUnless(find_communities(context) is cf)

    def test_find_peopledirectory(self):
        from karl.utils import find_peopledirectory
        pd = testing.DummyModel()
        from zope.interface import directlyProvides
        from karl.models.interfaces import IPeopleDirectory
        directlyProvides(pd, IPeopleDirectory)
        site = testing.DummyModel()
        site['people'] = pd
        context = testing.DummyModel()
        pd['obj'] = context
        self.assertEqual(find_peopledirectory(context), pd)

    def test_find_peopledirectory_catalog(self):
        from karl.utils import find_peopledirectory_catalog
        context = testing.DummyModel()
        self.assertEqual(find_peopledirectory_catalog(context), None)
        people = context['people'] = testing.DummyModel()
        people.catalog = testing.DummyModel()
        self.failUnless(
            find_peopledirectory_catalog(context) is people.catalog)

    def test_get_session(self):
        from karl.utils import get_session
        context = testing.DummyModel()
        session = testing.DummyModel()
        sessions = testing.DummyModel()
        sessions['abc'] = session
        context.sessions = sessions
        request = testing.DummyRequest()
        request.environ['repoze.browserid'] = 'abc'
        result = get_session(context, request)
        self.assertEqual(result, session)

    def test_docid_to_hex(self):
        from karl.utils import docid_to_hex
        from karl.utils import _MAX_32BIT_INT
        self.assertEqual(docid_to_hex(0), '7FFFFFFF')
        self.assertEqual(docid_to_hex(_MAX_32BIT_INT), 'FFFFFFFE')
        self.assertEqual(docid_to_hex(-_MAX_32BIT_INT), '00000000')

    def test_hex_to_docid(self):
        from karl.utils import hex_to_docid
        from karl.utils import _MAX_32BIT_INT
        self.assertEqual(hex_to_docid('7FFFFFFF'), 0)
        self.assertEqual(hex_to_docid('FFFFFFFE'), _MAX_32BIT_INT)
        self.assertEqual(hex_to_docid('00000000'), -_MAX_32BIT_INT)

    def test_coarse_datetime_repr(self):
        import datetime
        from karl.utils import coarse_datetime_repr
        self.assertEqual(coarse_datetime_repr(
            datetime.datetime(2009, 2, 13, 23, 31, 30)), 12345678)
        self.assertEqual(coarse_datetime_repr(
            datetime.datetime(2009, 2, 13, 23, 31, 31)), 12345678)
        self.assertEqual(coarse_datetime_repr(
            datetime.datetime(2009, 2, 13, 23, 31, 40)), 12345679)

    def test_find_tempfolder_exists(self):
        from karl.utils import find_tempfolder
        root = testing.DummyModel()
        root['TEMP'] = tempfolder = testing.DummyModel()
        self.assertEqual(find_tempfolder(root), tempfolder)

    def test_find_tempfolder_create(self):
        from karl.models.tempfolder import TempFolder
        from karl.utils import find_tempfolder
        root = testing.DummyModel()
        tempfolder = find_tempfolder(root)
        self.failUnless(isinstance(tempfolder, TempFolder))
        self.assertEqual(root['TEMP'], tempfolder)

    def test_find_repo(self):
        from karl.utils import find_repo
        context = testing.DummyModel()
        self.assertEqual(find_repo(context), None)
        context.repo = '1'
        self.assertEqual(find_repo(context), '1')

class TestDebugSearch(unittest.TestCase):
    def setUp(self):
        from zope.testing.cleanup import cleanUp
        cleanUp()

    def tearDown(self):
        from zope.testing.cleanup import cleanUp
        cleanUp()

    def _callFUT(self, context, **kw):
        from karl.utils import debugsearch
        return debugsearch(context, **kw)

    def test_it(self):
        from karl.models.interfaces import ICatalogSearch
        def searcher(context):
            def search(**kw):
                return 1, [1], lambda *arg: None
            return search
        karl.testing.registerAdapter(searcher, provides=ICatalogSearch)
        context = testing.DummyModel()
        result = self._callFUT(context)
        self.assertEqual(result, (1, [None]))

class TestGetContentTypeNameAndIcon(unittest.TestCase):
    def setUp(self):
        from zope.testing.cleanup import cleanUp
        cleanUp()

    def tearDown(self):
        from zope.testing.cleanup import cleanUp
        cleanUp()

    def _callFUT(self, context):
        from karl.utils import get_content_type_name_and_icon as fut
        return fut(context)

    def test_blog_entry(self):
        from karl.content.interfaces import IBlogEntry as ctype
        from zope.interface import directlyProvides
        from repoze.lemonade.testing import registerContentFactory
        registerContentFactory(testing.DummyModel, ctype)
        context = testing.DummyModel()
        directlyProvides(context, ctype)
        self.assertEqual(self._callFUT(context), ('Blog Entry', 'blog.png'))

    def test_calendar_event(self):
        from karl.content.interfaces import ICalendarEvent as ctype
        from zope.interface import directlyProvides
        from repoze.lemonade.testing import registerContentFactory
        registerContentFactory(testing.DummyModel, ctype)
        context = testing.DummyModel()
        directlyProvides(context, ctype)
        self.assertEqual(self._callFUT(context),
                         ('Event', 'calendar-select.png'))

    def test_news_item(self):
        from karl.content.interfaces import INewsItem as ctype
        from zope.interface import directlyProvides
        from repoze.lemonade.testing import registerContentFactory
        registerContentFactory(testing.DummyModel, ctype)
        context = testing.DummyModel()
        directlyProvides(context, ctype)
        self.assertEqual(self._callFUT(context),
                         ('News Item', 'newspaper.png'))

    def test_wiki_page(self):
        from karl.content.interfaces import IWikiPage as ctype
        from zope.interface import directlyProvides
        from repoze.lemonade.testing import registerContentFactory
        registerContentFactory(testing.DummyModel, ctype)
        context = testing.DummyModel()
        directlyProvides(context, ctype)
        self.assertEqual(self._callFUT(context),
                         ('Wiki Page', 'wiki.png'))

    def test_file(self):
        from karl.content.interfaces import ICommunityFile as ctype
        from zope.interface import directlyProvides
        from repoze.lemonade.testing import registerContentFactory
        registerContentFactory(testing.DummyModel, ctype)
        context = testing.DummyModel()
        directlyProvides(context, ctype)
        self.assertEqual(self._callFUT(context),
                         ('File', 'blue-document-text.png'))

    def test_comment(self):
        from karl.models.interfaces import IComment as ctype
        from zope.interface import directlyProvides
        from repoze.lemonade.testing import registerContentFactory
        registerContentFactory(testing.DummyModel, ctype)
        context = testing.DummyModel()
        directlyProvides(context, ctype)
        self.assertEqual(self._callFUT(context),
                         ('Comment', 'quill.png'))

    def test_community(self):
        from karl.models.interfaces import ICommunity as ctype
        from zope.interface import directlyProvides
        from repoze.lemonade.testing import registerContentFactory
        registerContentFactory(testing.DummyModel, ctype)
        context = testing.DummyModel()
        directlyProvides(context, ctype)
        self.assertEqual(self._callFUT(context),
                         ('Community', 'building.png'))

class TestGetSession(unittest.TestCase):
    def _callFUT(self, context, request):
        from karl.utils import get_session
        return get_session(context, request)

    def test_it(self):
        request = testing.DummyRequest()
        context = testing.DummyModel()
        context.sessions = testing.DummyModel()
        foo = testing.DummyModel()
        context.sessions['foo'] = foo
        request.environ = {'repoze.browserid':'foo'}
        result = self._callFUT(context, request)
        self.assertEqual(result, foo)

class TestPersistentBBB(unittest.TestCase):
    def _makeOne(self, *arg):
        from karl.utils import PersistentBBB
        return PersistentBBB(*arg)

    def test_it(self):
        from persistent import Persistent
        class Dummy(Persistent):
            attr = self._makeOne('attr', [])
        d = Dummy()
        self.assertEqual(d.__dict__, {})
        self.assertEqual(d.attr, [])
        self.assertEqual(d.__dict__, {'attr':[]})

    def test_default_copied(self):
        from persistent import Persistent
        L = []
        class Dummy(Persistent):
            attr = self._makeOne('attr', L)
        d = Dummy()
        self.assertEqual(d.__dict__, {})
        L2 = d.attr
        self.failIf(L is L2)
