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
from zope.interface import Interface

from karl import testing as karltesting

class TestDeprecatedCatalogSearch(unittest.TestCase):

    def setUp(self):
        testing.cleanUp()

    def tearDown(self):
        testing.cleanUp()

    def _getTargetClass(self):
        from karl.models.adapters import CatalogSearch
        return CatalogSearch

    def _makeOne(self, context, request):
        global __warningregistry__
        import warnings
        old_filters = warnings.filters[:]
        warnings.filterwarnings('ignore', category=DeprecationWarning)
        try:
            adapter = self._getTargetClass()(context, request)
        finally:
            warnings.filters[:] = old_filters
        assert __warningregistry__
        del __warningregistry__
        return adapter

    def test_it(self):
        context = testing.DummyModel()
        context.catalog = karltesting.DummyCatalog({})
        request = testing.DummyRequest()
        adapter = self._makeOne(context, request)
        num, docids, resolver = adapter()
        self.assertEqual(num, 0)
        self.assertEqual(list(docids), [])

    def test_unfound_model(self):
        from pyramid.interfaces import IDebugLogger
        class DummyLogger:
            def warn(self, msg):
                self.msg = msg
        logger = DummyLogger()
        karltesting.registerUtility(logger, IDebugLogger)
        a = testing.DummyModel()
        b = testing.DummyModel()
        karltesting.registerModels({'/a':a})
        context = testing.DummyModel()
        context.catalog = karltesting.DummyCatalog({1:'/a', 2:'/b'})
        request = testing.DummyRequest()
        adapter = self._makeOne(context, request)
        num, docids, resolver = adapter()
        self.assertEqual(num, 2)
        self.assertEqual(list(docids), [1, 2])
        results = filter(None, map(resolver, docids))
        self.assertEqual(results, [a])
        self.assertEqual(logger.msg, 'Model missing: /b')

    def test_unfound_docid(self):
        context = testing.DummyModel()
        context.catalog = karltesting.DummyCatalog({})
        request = testing.DummyRequest()
        adapter = self._makeOne(context, request)
        num, docids, resolver = adapter()
        self.assertEqual(resolver(123), None)


class TestCatalogSearch(unittest.TestCase):

    def setUp(self):
        testing.cleanUp()

    def tearDown(self):
        testing.cleanUp()

    def _getTargetClass(self):
        from karl.models.adapters import CatalogSearch
        return CatalogSearch

    def _makeOne(self, context):
        adapter = self._getTargetClass()(context)
        return adapter

    def test_it(self):
        context = testing.DummyModel()
        context.catalog = karltesting.DummyCatalog({})
        adapter = self._makeOne(context)
        num, docids, resolver = adapter()
        self.assertEqual(num, 0)
        self.assertEqual(list(docids), [])

    def test_unfound_model(self):
        from pyramid.interfaces import IDebugLogger
        class DummyLogger:
            def warn(self, msg):
                self.msg = msg
        logger = DummyLogger()
        karltesting.registerUtility(logger, IDebugLogger)
        a = testing.DummyModel()
        b = testing.DummyModel()
        karltesting.registerModels({'/a':a})
        context = testing.DummyModel()
        context.catalog = karltesting.DummyCatalog({1:'/a', 2:'/b'})
        adapter = self._makeOne(context)
        num, docids, resolver = adapter()
        self.assertEqual(num, 2)
        self.assertEqual(list(docids), [1, 2])
        results = filter(None, map(resolver, docids))
        self.assertEqual(results, [a])
        self.assertEqual(logger.msg, 'Model missing: /b')

    def test_unfound_docid(self):
        context = testing.DummyModel()
        context.catalog = karltesting.DummyCatalog({})
        adapter = self._makeOne(context)
        num, docids, resolver = adapter()
        self.assertEqual(resolver(123), None)


class TestPeopleDirectoryCatalogSearch(unittest.TestCase):

    def setUp(self):
        testing.cleanUp()

    def tearDown(self):
        testing.cleanUp()

    def _getTargetClass(self):
        from karl.models.adapters import PeopleDirectoryCatalogSearch
        return PeopleDirectoryCatalogSearch

    def _makeOne(self, context):
        adapter = self._getTargetClass()(context)
        return adapter

    def test_it(self):
        from zope.interface import directlyProvides
        from karl.models.interfaces import ISite
        site = testing.DummyModel()
        directlyProvides(site, ISite)
        peopledir = testing.DummyModel()
        site['people'] = peopledir
        site['people'].catalog = karltesting.DummyCatalog({})
        context = testing.DummyModel()
        site['obj'] = context
        adapter = self._makeOne(context)
        num, docids, resolver = adapter()
        self.assertEqual(num, 0)
        self.assertEqual(list(docids), [])


class TestGridEntryInfo(unittest.TestCase):

    def _getTargetClass(self):
        from karl.models.adapters import GridEntryInfo
        return GridEntryInfo

    def _makeOne(self, context, request):
        return self._getTargetClass()(context, request)

    def test_class_conforms_to_IGridEntryInfo(self):
        from zope.interface.verify import verifyClass
        from karl.models.interfaces import IGridEntryInfo
        verifyClass(IGridEntryInfo, self._getTargetClass())

    # instance wont conform due to properties

    def test_title(self):
        request = testing.DummyRequest()
        context = testing.DummyModel()
        context.title = 'title'
        adapter = self._makeOne(context, request)
        self.assertEqual(adapter.title, 'title')

    def test_url(self):
        request = testing.DummyRequest()
        context = testing.DummyModel()
        adapter = self._makeOne(context, request)
        self.assertEqual(adapter.url, 'http://example.com/')

    def test_comment_url(self):
        request = testing.DummyRequest()
        context = testing.DummyModel()
        commentfolder = testing.DummyModel()
        grandparent = testing.DummyModel()
        grandparent['commentfolder'] = commentfolder
        commentfolder['0123'] = context
        from zope.interface import directlyProvides
        from karl.models.interfaces import IComment
        directlyProvides(context, IComment)
        adapter = self._makeOne(context, request)
        self.assertEqual(adapter.url, 'http://example.com/#comment-0123')

    def test_type(self):
        from zope.interface import Interface
        from zope.interface import taggedValue
        from zope.interface import directlyProvides
        from repoze.lemonade.testing import registerContentFactory
        request = testing.DummyRequest()
        context = testing.DummyModel()
        class Dummy:
            pass
        class IDummy(Interface):
            taggedValue('name', 'yo')
        registerContentFactory(Dummy, IDummy)
        directlyProvides(context, IDummy)
        adapter = self._makeOne(context, request)
        self.assertEqual(adapter.type, 'yo')

    def test_modified(self):
        import datetime
        request = testing.DummyRequest()
        context = testing.DummyModel()
        now = datetime.datetime.now()
        context.modified = now
        adapter = self._makeOne(context, request)
        self.assertEqual(adapter.modified,now.strftime("%m/%d/%Y"))

    def test_created(self):
        import datetime
        request = testing.DummyRequest()
        context = testing.DummyModel()
        now = datetime.datetime.now()
        context.created = now
        adapter = self._makeOne(context, request)
        self.assertEqual(adapter.created,now.strftime("%m/%d/%Y"))

    def test_creator_title(self):
        request = testing.DummyRequest()
        context = testing.DummyModel()
        from karl.models.interfaces import ISite
        from zope.interface import directlyProvides
        directlyProvides(context, ISite)
        creator = testing.DummyModel(title='Dummy creator')
        context['profiles'] = profiles = testing.DummyModel()
        profiles['creator'] = creator
        context.creator = 'creator'
        adapter = self._makeOne(context, request)
        self.assertEqual(adapter.creator_title,
                         'Dummy creator')

    def test_creator_without_title(self):
        request = testing.DummyRequest()
        context = testing.DummyModel()
        from karl.models.interfaces import ISite
        from zope.interface import directlyProvides
        directlyProvides(context, ISite)
        creator = testing.DummyModel()
        context['profiles'] = profiles = testing.DummyModel()
        profiles['creator'] = creator
        context.creator = 'creator'
        adapter = self._makeOne(context, request)
        self.assertEqual(adapter.creator_title,
                         'no profile title')

    def test_creator_url(self):
        request = testing.DummyRequest()
        context = testing.DummyModel()
        from karl.models.interfaces import ISite
        from zope.interface import directlyProvides
        directlyProvides(context, ISite)
        creator = testing.DummyModel(title='Dummy creator')
        context['profiles'] = profiles = testing.DummyModel()
        profiles['creator'] = creator
        context.creator = 'creator'
        adapter = self._makeOne(context, request)
        self.assertEqual(adapter.creator_url,
                         'http://example.com/profiles/creator/')

    def test_modified_by_title_falls_back_to_creator(self):
        request = testing.DummyRequest()
        context = testing.DummyModel()
        from karl.models.interfaces import ISite
        from zope.interface import directlyProvides
        directlyProvides(context, ISite)
        profile = testing.DummyModel(title='Test User')
        context['profiles'] = profiles = testing.DummyModel()
        profiles['testuser'] = profile
        context.creator = 'testuser'
        adapter = self._makeOne(context, request)
        self.assertEqual(adapter.modified_by_title, 'Test User')

    def test_modified_by_title(self):
        request = testing.DummyRequest()
        context = testing.DummyModel()
        from karl.models.interfaces import ISite
        from zope.interface import directlyProvides
        directlyProvides(context, ISite)
        profile = testing.DummyModel(title='Test User')
        context['profiles'] = profiles = testing.DummyModel()
        profiles['testuser'] = profile
        context.modified_by = 'testuser'
        adapter = self._makeOne(context, request)
        self.assertEqual(adapter.modified_by_title, 'Test User')

    def test_modified_by_without_title(self):
        request = testing.DummyRequest()
        context = testing.DummyModel()
        from karl.models.interfaces import ISite
        from zope.interface import directlyProvides
        directlyProvides(context, ISite)
        profile = testing.DummyModel()
        context['profiles'] = profiles = testing.DummyModel()
        profiles['testuser'] = profile
        context.modified_by = 'testuser'
        adapter = self._makeOne(context, request)
        self.assertEqual(adapter.modified_by_title, 'no profile title')

    def test_modified_by_without_profile(self):
        request = testing.DummyRequest()
        context = testing.DummyModel()
        from karl.models.interfaces import ISite
        from zope.interface import directlyProvides
        directlyProvides(context, ISite)
        profile = testing.DummyModel()
        context['profiles'] = profiles = testing.DummyModel()
        context.modified_by = 'testuser'
        adapter = self._makeOne(context, request)
        self.assertEqual(adapter.modified_by_title, 'no profile title')

    def test_modified_by_url(self):
        request = testing.DummyRequest()
        context = testing.DummyModel()
        from karl.models.interfaces import ISite
        from zope.interface import directlyProvides
        directlyProvides(context, ISite)
        profile = testing.DummyModel(title='Test User')
        context['profiles'] = profiles = testing.DummyModel()
        profiles['testuser'] = profile
        context.modified_by = 'testuser'
        adapter = self._makeOne(context, request)
        self.assertEqual(adapter.modified_by_url,
                         'http://example.com/profiles/testuser/')


class TestTagQuery(unittest.TestCase):

    def setUp(self):
        testing.cleanUp()

    def tearDown(self):
        testing.cleanUp()

    def _getTargetClass(self):
        from karl.models.adapters import TagQuery
        return TagQuery

    def _makeOne(self, context, request):
        manager = self._getTargetClass()(context, request)
        manager.iface = DummyInterface
        return manager

    def test_tags_with_counts(self):
        from zope.interface import directlyProvides
        from karl import testing as karltesting
        context = testing.DummyModel()
        request = testing.DummyRequest()
        context.catalog = karltesting.DummyCatalog()

        def dummy_getTagObjects(*args, **kw):
            self.assertEqual(kw['items'], (123,))
            return [testing.DummyModel(name='tag1', user='nyc1'),
                    testing.DummyModel(name='tag1', user='admin'),
                    testing.DummyModel(name='tag2', user='nyc1'),
                   ]
        dummy_tags = testing.DummyModel()
        dummy_tags.getTagObjects = dummy_getTagObjects
        context.tags = dummy_tags
        directlyProvides(context, DummyInterface)
        adapter = self._makeOne(context, request)
        adapter._docid = 123
        adapter.username = u'admin'

        alltaginfo = adapter.tagswithcounts

        self.assertEqual(len(alltaginfo), 2, alltaginfo)
        self.assertEqual(alltaginfo[0]['count'], 2)
        self.assertEqual(alltaginfo[0]['tag'], u'tag1')
        self.assertEqual(alltaginfo[0]['snippet'], '')
        self.assertEqual(alltaginfo[1]['count'], 1)
        self.assertEqual(alltaginfo[1]['tag'], u'tag2')
        self.assertEqual(alltaginfo[1]['snippet'], 'nondeleteable')

    def test_tagusers(self):
        context = testing.DummyModel()
        tags = context.tags = testing.DummyModel()
        def _getTags(*args, **kw):
            self.assertEqual(kw['users'], ('dummy',))
            self.assertEqual(kw['items'], (1,))
            return ['1', '2']
        tags.getTags = _getTags
        request = testing.DummyRequest()
        adapter = self._makeOne(context, request)
        adapter._docid = 1
        adapter.username = u'dummy'
        self.assertEqual(adapter.tagusers, '1 2')

    def test_docid(self):
        from karl import testing as karltesting
        request = testing.DummyRequest()
        context = testing.DummyModel()
        context.catalog = karltesting.DummyCatalog()
        adapter = self._makeOne(context, request)
        self.assertEqual(adapter.docid, None)

    def test_tags_with_prefix(self):
        request = testing.DummyRequest()
        context = testing.DummyModel()
        tags = testing.DummyModel()
        tags.getTagsWithPrefix = lambda x: x
        context.tags = tags
        adapter = self._makeOne(context, request)
        generator = adapter.tags_with_prefix('1')
        self.assertEqual(list(generator), ['1'])


class TestCommunityInfo(unittest.TestCase):

    def _getTargetClass(self):
        from karl.models.adapters import CommunityInfo
        return CommunityInfo

    def _makeOne(self, context, request):
        return self._getTargetClass()(context, request)

    def _makeCommunity(self, **kw):
        community = testing.DummyModel(title='title', description='description')
        return community

    def test_class_conforms_to_ICommunityInfo(self):
        from zope.interface.verify import verifyClass
        from karl.models.interfaces import ICommunityInfo
        verifyClass(ICommunityInfo, self._getTargetClass())

    # instance wont conform due to properties

    def test_number_of_members(self):
        context = self._makeCommunity()
        request = testing.DummyRequest()
        context.number_of_members = 3
        adapter = self._makeOne(context, request)
        self.assertEqual(adapter.number_of_members, 3)

    def test_tabs_requestcontext_iscommunity(self):
        from karl.models.interfaces import ICommunity
        from karl.models.interfaces import IToolFactory
        from repoze.lemonade.testing import registerListItem
        from zope.interface import directlyProvides
        tool_factory = DummyToolFactory()
        registerListItem(IToolFactory, tool_factory, 'one', title='One')
        context = self._makeCommunity()
        directlyProvides(context, ICommunity)
        request = testing.DummyRequest()
        request.context = context
        adapter = self._makeOne(context, request)
        tabs = adapter.tabs
        self.assertEqual(len(tabs), 2)
        self.assertEqual(tabs[0],
                         {'url': 'http://example.com/view.html',
                          'css_class': 'curr', 'name': 'OVERVIEW',
                          'selected': 'selected', 'title': 'Overview'}
                         )
        self.assertEqual(tabs[1],
                         {'url': 'http://example.com/tab',
                          'css_class': '', 'name': 'ONE',
                          'selected': None, 'title': 'One'}
                         )

    def test_tabs_requestcontext_is_not_community(self):
        from karl.models.interfaces import IToolFactory
        from repoze.lemonade.testing import registerListItem
        tool_factory = DummyToolFactory()
        registerListItem(IToolFactory, tool_factory, 'one', title='One')
        context = self._makeCommunity()
        request = testing.DummyRequest()
        request.context = context
        adapter = self._makeOne(context, request)
        tabs = adapter.tabs
        self.assertEqual(len(tabs), 2)
        self.assertEqual(tabs[0],
                         {'url': 'http://example.com/view.html',
                          'css_class': '', 'name': 'OVERVIEW',
                          'selected': None, 'title': 'Overview'}
                         )
        self.assertEqual(tabs[1],
                         {'url': 'http://example.com/tab',
                          'css_class': 'curr', 'name': 'ONE',
                          'selected': 'selected', 'title': 'One'}
                         )

    def test_description(self):
        context = self._makeCommunity()
        context.description = 'description'
        request = testing.DummyRequest()
        adapter = self._makeOne(context, request)
        self.assertEqual(adapter.description, 'description')

    def test_title(self):
        context = self._makeCommunity()
        context.title = 'title'
        request = testing.DummyRequest()
        adapter = self._makeOne(context, request)
        self.assertEqual(adapter.title, 'title')

    def test_name(self):
        context = self._makeCommunity()
        context.__name__ = 'name'
        request = testing.DummyRequest()
        adapter = self._makeOne(context, request)
        self.assertEqual(adapter.name, 'name')

    def test_last_activity_date(self):
        context = self._makeCommunity()
        import datetime
        now = datetime.datetime.now()
        context.content_modified = now
        request = testing.DummyRequest()
        adapter = self._makeOne(context, request)
        self.assertEqual(adapter.last_activity_date, now.strftime("%m/%d/%Y"))

    def test_url(self):
        context = self._makeCommunity()
        request = testing.DummyRequest()
        adapter = self._makeOne(context, request)
        self.assertEqual(adapter.url, 'http://example.com/')

    def test_community_tags_no_tags_tool(self):
        context = self._makeCommunity()
        request = testing.DummyRequest()
        adapter = self._makeOne(context, request)
        self.assertEqual(len(adapter.community_tags), 0)

    def test_community_tags_wo_tags_tool_less_than_five(self):
        context = self._makeCommunity()
        context.__name__ = 'dummy'
        tool = context.tags = DummyTags([('foo', 3), ('bar', 6)])
        request = testing.DummyRequest()
        adapter = self._makeOne(context, request)

        tags = adapter.community_tags

        self.assertEqual(len(tags), 2)
        self.assertEqual(tags[0], {'tag': 'bar', 'count': 6})
        self.assertEqual(tags[1], {'tag': 'foo', 'count': 3})
        self.assertEqual(tool._called_with, 'dummy')

    def test_community_tags_wo_tags_tool_more_than_five(self):
        context = self._makeCommunity()
        context.tags = DummyTags([('foo', 3),
                                  ('bar', 6),
                                  ('baz', 14),
                                  ('qux', 1),
                                  ('quxxy', 4),
                                  ('spam', 2),
                                 ])
        request = testing.DummyRequest()
        adapter = self._makeOne(context, request)

        tags = adapter.community_tags

        self.assertEqual(len(tags), 5)
        self.assertEqual(tags[0], {'tag': 'baz', 'count': 14})
        self.assertEqual(tags[1], {'tag': 'bar', 'count': 6})
        self.assertEqual(tags[2], {'tag': 'quxxy', 'count': 4})
        self.assertEqual(tags[3], {'tag': 'foo', 'count': 3})
        self.assertEqual(tags[4], {'tag': 'spam', 'count': 2})

    def test_is_member_direct(self):
        context = self._makeCommunity()
        context.member_names = ['dummy', 'foo']
        request = testing.DummyRequest()
        karltesting.registerDummySecurityPolicy('dummy')
        adapter = self._makeOne(context, request)

        self.assertEqual(adapter.member, True)

    def test_is_member_via_group(self):
        context = self._makeCommunity()
        context.member_names = ['a_group', 'foo']
        request = testing.DummyRequest()
        karltesting.registerDummySecurityPolicy('dummy', ['a_group'])
        adapter = self._makeOne(context, request)

        self.assertEqual(adapter.member, True)

    def test_is_not_member(self):
        context = self._makeCommunity()
        context.member_names = ['foo', 'bar']
        request = testing.DummyRequest()
        karltesting.registerDummySecurityPolicy('dummy')
        adapter = self._makeOne(context, request)

        self.assertEqual(adapter.member, False)

    def test_is_moderator(self):
        context = self._makeCommunity()
        context.moderator_names = ['dummy', 'foo']
        request = testing.DummyRequest()
        karltesting.registerDummySecurityPolicy('dummy')
        adapter = self._makeOne(context, request)

        self.assertEqual(adapter.moderator, True)

    def test_is_not_moderator(self):
        context = self._makeCommunity()
        context.moderator_names = ['foo', 'bar']
        request = testing.DummyRequest()
        karltesting.registerDummySecurityPolicy('dummy')
        adapter = self._makeOne(context, request)

        self.assertEqual(adapter.moderator, False)


class TestLetterManager(unittest.TestCase):
    def setUp(self):
        testing.cleanUp()

    def tearDown(self):
        testing.cleanUp()

    def _getTargetClass(self):
        from karl.models.adapters import LetterManager
        return LetterManager

    def _makeOne(self, context):
        manager = self._getTargetClass()(context)
        manager.iface = DummyInterface
        return manager

    def test_delta_title_none(self):
        context = testing.DummyModel()
        adapter = self._makeOne(context)
        result = adapter.delta(-1)
        self.assertEqual(result, False)

    def test_delta_storage_none(self):
        context = testing.DummyModel()
        context.title = 'title'
        adapter = self._makeOne(context)
        result = adapter.delta(-1)
        self.assertEqual(result, False)

    def test_delta_storage_not_none_noalpha(self):
        context = testing.DummyModel()
        context.title = 'title'
        from zope.interface import directlyProvides
        directlyProvides(context, DummyInterface)
        adapter = self._makeOne(context)
        result = adapter.delta(1)
        self.assertEqual(result, 1)
        self.assertEqual(context.alpha['T'], 1)

    def test_delta_storage_existing_alpha(self):
        context = testing.DummyModel()
        context.title = 'title'
        context.alpha = {'T':1}
        from zope.interface import directlyProvides
        directlyProvides(context, DummyInterface)
        adapter = self._makeOne(context)
        result = adapter.delta(1)
        self.assertEqual(result, 2)
        self.assertEqual(context.alpha['T'], 2)

    def test_delta_lessthan_zero(self):
        context = testing.DummyModel()
        context.title = 'title'
        context.alpha = {'T':1}
        from zope.interface import directlyProvides
        directlyProvides(context, DummyInterface)
        adapter = self._makeOne(context)
        result = adapter.delta(-100)
        self.assertEqual(result, 0)
        self.assertEqual(context.alpha['T'], 0)

    def test_get_info_noalpha(self):
        request = testing.DummyRequest()
        context = testing.DummyModel()
        from zope.interface import directlyProvides
        directlyProvides(context, DummyInterface)
        adapter = self._makeOne(context)
        letters = adapter.get_info(request)
        self.assertEqual(len(letters), 27)
        self.assertEqual(letters[0]['name'], 'A')
        self.assertEqual(letters[0]['css_class'], 'notcurrent')
        self.assertEqual(letters[0]['href'], None)
        self.assertEqual(letters[0]['is_current'], False)
        self.assertEqual(letters[26]['name'], 'Any')
        self.assertEqual(letters[26]['css_class'], 'current')
        self.assertEqual(letters[26]['href'], None)
        self.assertEqual(letters[26]['is_current'], True)

    def test_get_info_alpha(self):
        request = testing.DummyRequest()
        context = testing.DummyModel()
        context.alpha = {'A':1}
        from zope.interface import directlyProvides
        directlyProvides(context, DummyInterface)
        adapter = self._makeOne(context)
        letters = adapter.get_info(request)
        self.assertEqual(len(letters), 27)
        self.assertEqual(letters[0]['name'], 'A')
        self.assertEqual(letters[0]['css_class'], 'notcurrent')
        self.assertEqual(letters[0]['href'],
                         'http://example.com?titlestartswith=A')
        self.assertEqual(letters[0]['is_current'], False)
        self.assertEqual(letters[1]['name'], 'B')
        self.assertEqual(letters[1]['css_class'], 'notcurrent')
        self.assertEqual(letters[1]['href'], None)
        self.assertEqual(letters[1]['is_current'], False)
        self.assertEqual(letters[26]['name'], 'Any')
        self.assertEqual(letters[26]['css_class'], 'current')
        self.assertEqual(letters[26]['href'], None)
        self.assertEqual(letters[26]['is_current'], True)

    def test_titlestartswith(self):
        request = testing.DummyRequest(dict(titlestartswith='A'))
        context = testing.DummyModel()
        context.alpha = {'A':1}
        from zope.interface import directlyProvides
        directlyProvides(context, DummyInterface)
        adapter = self._makeOne(context)
        letters = adapter.get_info(request)
        self.assertEqual(len(letters), 27)
        self.assertEqual(letters[0]['name'], 'A')
        self.assertEqual(letters[0]['css_class'], 'current')
        self.assertEqual(letters[0]['href'],
                         'http://example.com?titlestartswith=A')
        self.assertEqual(letters[0]['is_current'], True)
        self.assertEqual(letters[26]['name'], 'Any')
        self.assertEqual(letters[26]['css_class'], 'notcurrent')
        self.assertEqual(letters[26]['href'], 'http://example.com')
        self.assertEqual(letters[26]['is_current'], False)


class TestPeopleReportLetterManager(unittest.TestCase):
    def setUp(self):
        testing.cleanUp()

    def tearDown(self):
        testing.cleanUp()

    def _getTargetClass(self):
        from karl.models.adapters import PeopleReportLetterManager
        return PeopleReportLetterManager

    def _makeOne(self, context):
        return self._getTargetClass()(context)

    def test_get_info(self):
        obj = self._makeOne(None)

        # stub the get_active_letters method
        def get_active_letters():
            return set(['A', 'B'])
        obj.get_active_letters = get_active_letters

        request = testing.DummyRequest({'lastnamestartswith': 'B'})
        letters = obj.get_info(request)
        self.assertEqual(len(letters), 27)
        self.assertEqual(letters[0]['name'], 'A')
        self.assertEqual(letters[0]['css_class'], 'notcurrent')
        self.assertEqual(letters[0]['href'],
                        'http://example.com?lastnamestartswith=A')
        self.assertEqual(letters[0]['is_current'], False)
        self.assertEqual(letters[1]['name'], 'B')
        self.assertEqual(letters[1]['css_class'], 'current')
        self.assertEqual(letters[1]['href'],
                        'http://example.com?lastnamestartswith=B')
        self.assertEqual(letters[1]['is_current'], True)
        self.assertEqual(letters[2]['name'], 'C')
        self.assertEqual(letters[2]['css_class'], 'notcurrent')
        self.assertEqual(letters[2]['href'], None)
        self.assertEqual(letters[2]['is_current'], False)
        self.assertEqual(letters[26]['name'], 'Any')
        self.assertEqual(letters[26]['css_class'], 'notcurrent')
        self.assertEqual(letters[26]['href'], 'http://example.com')
        self.assertEqual(letters[26]['is_current'], False)

    def test_no_filters(self):
        site = testing.DummyModel()
        from karl.models.interfaces import ISite
        from zope.interface import directlyProvides
        directlyProvides(site, ISite)
        site['people'] = testing.DummyModel()
        site['people'].catalog = karltesting.DummyCatalog()
        index = DummyFieldIndex({'A': None, 'M': None})
        site['people'].catalog['lastnamestartswith'] = index

        report = testing.DummyModel()
        site['report'] = report
        obj = self._makeOne(report)
        active = obj.get_active_letters()
        self.assertEqual(active, set(['A', 'M']))

    def test_with_category_filter(self):
        from BTrees import family32
        from zope.interface import directlyProvides
        from karl.models.interfaces import IPeopleReportCategoryFilter
        from karl.models.interfaces import ISite
        site = testing.DummyModel()
        directlyProvides(site, ISite)
        site['people'] = testing.DummyModel()
        site['people'].catalog = karltesting.DummyCatalog({2: None, 3: None})
        index = DummyFieldIndex({
            'A': family32.IF.TreeSet([1]),
            'B': family32.IF.TreeSet([2, 5]),
            'C': family32.IF.TreeSet([3]),
            'D': family32.IF.TreeSet([4, 6]),
            })
        index.family = family32
        site['people'].catalog['lastnamestartswith'] = index

        report = testing.DummyModel()
        nyc = report['office'] = testing.DummyModel(values=['nyc'])
        directlyProvides(nyc, IPeopleReportCategoryFilter)
        site['report'] = report
        obj = self._makeOne(report)
        active = obj.get_active_letters()
        self.assertEqual(active, set(['B', 'C']))
        self.assertEqual(site['people'].catalog.queries, [{
            'category_office': {'operator': 'or', 'query': ['nyc']},
            }])

    def test_with_group_filter(self):
        from BTrees import family32
        from zope.interface import directlyProvides
        from karl.models.interfaces import IPeopleReportGroupFilter
        from karl.models.interfaces import ISite
        site = testing.DummyModel()
        directlyProvides(site, ISite)
        site['people'] = testing.DummyModel()
        site['people'].catalog = karltesting.DummyCatalog({2: None, 3: None})
        index = DummyFieldIndex({
            'A': family32.IF.TreeSet([1]),
            'B': family32.IF.TreeSet([2, 5]),
            'C': family32.IF.TreeSet([3]),
            'D': family32.IF.TreeSet([4, 6]),
            })
        index.family = family32
        site['people'].catalog['lastnamestartswith'] = index

        report = testing.DummyModel()
        staff = report['office'] = testing.DummyModel(values=['staff'])
        directlyProvides(staff, IPeopleReportGroupFilter)
        site['report'] = report
        obj = self._makeOne(report)
        active = obj.get_active_letters()
        self.assertEqual(active, set(['B', 'C']))
        self.assertEqual(site['people'].catalog.queries, [{
            'groups': {'operator': 'or', 'query': ['staff']},
            }])


class TestPeopleReportMailinHandler(unittest.TestCase):
    def setUp(self):
        testing.cleanUp()

    def tearDown(self):
        testing.cleanUp()

    def _getTargetClass(self):
        from karl.models.adapters import PeopleReportMailinHandler
        return PeopleReportMailinHandler

    def _makeOne(self, context=None):
        if context is None:
            context = testing.DummyModel()
        return self._getTargetClass()(context)

    def _registerMailDelivery(self):
        from repoze.sendmail.interfaces import IMailDelivery
        class DummyMailDelivery:
            def __init__(self):
                self._sent = []
            def send(self, to, message):
                self._sent.append((to, message))
        md = DummyMailDelivery()
        karltesting.registerUtility(md, IMailDelivery)
        return md

    def _registerCatalogSearch(self, docids):
        from zope.interface import Interface
        from karl.models.interfaces import ICatalogSearch
        class DummyProfile:
            def __init__(self, docid):
                self.email = 'profile_%d@example.com' % docid
        def _find_profile(docid):
            return DummyProfile(docid)
        _called_with = []
        def _search(context):
            def _inner(**kw):
                _called_with.append(kw)
                return len(docids), docids, _find_profile
            return _inner
        karltesting.registerAdapter(_search, Interface, ICatalogSearch)
        return _called_with

    def _makeMessage(self, frm='sender@example.com',
                           to='recpiient@example.com', msgid='MSGID'):
        from email.message import Message
        message = Message()
        message['From'] = frm
        message['To'] = to
        message['Message-ID'] = msgid
        return message

    def test_class_conforms_to_IMailinHandler(self):
        from zope.interface.verify import verifyClass
        from karl.adapters.interfaces import IMailinHandler
        verifyClass(IMailinHandler, self._getTargetClass())

    def test_instance_conforms_to_IMailinHandler(self):
        from zope.interface.verify import verifyObject
        from karl.adapters.interfaces import IMailinHandler
        verifyObject(IMailinHandler, self._makeOne())

    def test_handle_no_mailinglist(self):
        md = self._registerMailDelivery()
        message = self._makeMessage()
        adapter = self._makeOne()
        adapter.handle(message, {'report': 'section+report'}, 'text', ())
        self.assertEqual(len(md._sent), 0)

    def test_handle_w_mailinglist_wo_subdomain(self):
        karltesting.registerSettings()
        md = self._registerMailDelivery()
        _called_with = self._registerCatalogSearch([0, 1])
        message = self._makeMessage()
        root = testing.DummyModel()
        people = root['people'] = testing.DummyModel()
        section = people['section'] = testing.DummyModel()
        report = section['report'] = testing.DummyModel()
        report['mailinglist'] = testing.DummyModel(short_address='alias')
        report.getQuery = lambda: {'testing': True}
        adapter = self._makeOne(report)

        adapter.handle(message, {'report': 'section+report'}, 'text', ())

        self.assertEqual(len(md._sent), 2)
        for index, (to, sentmessage) in enumerate(md._sent):
            self.assertEqual(to, ['profile_%d@example.com' % index])
            self.failIf('Message-Id' in sentmessage)
            self.assertEqual(sentmessage['Reply-To'],
                            'alias@karl3.example.com')
        self.assertEqual(_called_with, [{'testing': True}])

    def test_handle_w_mailinglist_w_subdomain(self):
        karltesting.registerSettings(
                system_list_subdomain='lists.example.com')
        md = self._registerMailDelivery()
        _called_with = self._registerCatalogSearch([0, 1])
        message = self._makeMessage()
        root = testing.DummyModel()
        people = root['people'] = testing.DummyModel()
        section = people['section'] = testing.DummyModel()
        report = section['report'] = testing.DummyModel()
        report['mailinglist'] = testing.DummyModel(short_address='alias')
        report.getQuery = lambda: {'testing': True}
        adapter = self._makeOne(report)

        adapter.handle(message, {'report': 'section+report'}, 'text', ())

        self.assertEqual(len(md._sent), 2)
        for index, (to, sentmessage) in enumerate(md._sent):
            self.assertEqual(to, ['profile_%d@example.com' % index])
            self.failIf('Message-Id' in sentmessage)
            self.assertEqual(sentmessage['Reply-To'],
                            'alias@lists.example.com')
        self.assertEqual(_called_with, [{'testing': True}])


class TestPGTextIndexContextualSummarizer(unittest.TestCase):

    def test_it(self):
        from karl.models.adapters import PGTextIndexContextualSummarizer as cut
        class DummyIndex(object):
            def get_contextual_summary(myself, raw_text, query, **options):
                self.assertEqual(raw_text, 'raw text')
                self.assertEqual(query, 'query')
                self.assertEqual(options, {'MaxFragments': 3})
                return 'summary'
        document = testing.DummyModel(text='raw text')
        instance = cut(DummyIndex())
        def dummy_text_repr(self, doc, default):
            return (doc.text,)
        cut.get_textrepr = dummy_text_repr
        summary = instance(document, 'query')
        self.assertEqual(summary, '... summary ...')


class TestZopeTextIndexContextualSummarizer(unittest.TestCase):

    def test_it(self):
        from karl.models.adapters import ZopeTextIndexContextualSummarizer
        instance = ZopeTextIndexContextualSummarizer(None)
        document = testing.DummyModel(description='description')
        self.assertEqual(instance(document, None), 'description')
        self.assertEqual(instance(object, None), '')


class DummyTags:
    _called_with = None

    def __init__(self, tags=()):
        self._tags = tags

    def getFrequency(self, tags=None, community=None):
        assert tags is None
        self._called_with = community
        return self._tags


class DummyToolFactory:
    def is_present(self, context, request):
        return True

    def tab_url(self, context, request):
        return 'http://example.com/tab'

    def is_current(self, context, request):
        return True


class DummyInterface(Interface):
    pass


class DummyFieldIndex:
    def __init__(self, data={}):
        self._fwd_index = data
