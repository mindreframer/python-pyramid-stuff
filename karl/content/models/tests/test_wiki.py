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

class WikiTests(unittest.TestCase):

    def setUp(self):
        testing.cleanUp()

    def tearDown(self):
        testing.cleanUp()

    def _getTargetClass(self):
        from karl.content.models.wiki import Wiki
        return Wiki

    def _makeOne(self):
        from repoze.lemonade.interfaces import IContentFactory
        karl.testing.registerAdapter(lambda *arg, **kw: DummyContent, (None,),
                                     IContentFactory)
        return self._getTargetClass()('creator')

    def test_class_conforms_to_IWiki(self):
        from zope.interface.verify import verifyClass
        from karl.content.interfaces import IWiki
        verifyClass(IWiki, self._getTargetClass())

    def test_instance_conforms_to_IWiki(self):
        from zope.interface.verify import verifyObject
        from karl.content.interfaces import IWiki
        verifyObject(IWiki, self._makeOne())

    def test_frontpage_made(self):
        wiki = self._makeOne()
        self.failUnless(isinstance(wiki['front_page'], DummyContent))

    def test_delete_frontpage_makes_new_frontpage(self):
        wiki = self._makeOne()
        del wiki['front_page']
        self.failUnless(isinstance(wiki['front_page'], DummyContent))


class WikiContainerVersionTests(unittest.TestCase):

    def _getTargetClass(self):
        from karl.content.models.wiki import WikiContainerVersion
        return WikiContainerVersion

    def _makeOne(self, context):
        return self._getTargetClass()(context)

    def test_container_version(self):
        root = testing.DummyModel()
        wiki = root['wiki'] = testing.DummyModel(docid=5)
        wiki['one'] = testing.DummyModel(docid=6)
        wiki['two'] = testing.DummyModel(docid=7)
        wiki['front_page'] = testing.DummyModel(docid=8)
        container = self._makeOne(wiki)
        self.assertEqual(container.container_id, 5)
        self.assertEqual(container.path, '/wiki')
        self.assertEqual(container.map, {
            'one': 6,
            'two': 7,
            'front_page': 8
        })
        self.assertEqual(container.ns_map, {})


class WikiPageTests(unittest.TestCase):

    def _getTargetClass(self):
        from karl.content.models.wiki import WikiPage
        return WikiPage

    def _makeOne(self, title=u'title', text=u'', description=u'',
                 creator=u'admin'):
        return self._getTargetClass()(
            title, text, description, creator)

    def test_class_conforms_to_IWikiPage(self):
        from zope.interface.verify import verifyClass
        from karl.content.interfaces import IWikiPage
        verifyClass(IWikiPage, self._getTargetClass())

    def test_instance_conforms_to_IWikiPage(self):
        from zope.interface.verify import verifyObject
        from karl.content.interfaces import IWikiPage
        verifyObject(IWikiPage, self._makeOne())

    def test_instance_construct_with_none(self):
        instance = self._makeOne(text=None)
        self.assertEqual(instance.text, u'')

    def test_instance_construct_description_is_none(self):
        instance = self._makeOne(description=None)
        self.assertEqual(instance.description, u'')

    def test_cook_empty(self):
        wp = self._makeOne()
        request = testing.DummyRequest()
        self.assertEqual(wp.cook(request), u'')

    def test_cook_no_wiki_markup(self):
        TEXT = (u'Now is the time for all good men '
                 'to come to the aid of the Party')
        wp = self._makeOne(text=TEXT)
        request = testing.DummyRequest()
        self.assertEqual(wp.cook(request), TEXT)

    def test_cook_w_wiki_markup_no_match(self):
        TEXT = (u'Now is the time for ((all good men)) '
                 'to come to the aid of the Party')
        EXPECTED = (u'Now is the time for '
                     '<span class="wicked_unresolved">all good men</span> '
                     '<a href="../add_wikipage.html'
                     '?title=all%20good%20men">+</a> '
                     'to come to the aid of the Party')
        wp = self._makeOne(text=TEXT)
        parent = testing.DummyModel()
        wp.__parent__ = parent
        wp.__name__ = 'wikipage'
        request = testing.DummyRequest()
        self.assertEqual(wp.cook(request), EXPECTED)

    def test_cook_w_wiki_markup_no_match_unicode(self):
        TEXT = (u'Now is the time for ((\xe0ll good men)) '
                 'to come to the aid of the Party')
        EXPECTED = (u'Now is the time for '
                    u'<span class="wicked_unresolved">\xe0ll good men</span> '
                     '<a href="../add_wikipage.html'
                     '?title=%C3%A0ll%20good%20men">+</a> '
                     'to come to the aid of the Party')
        wp = self._makeOne(text=TEXT)
        parent = testing.DummyModel()
        wp.__parent__ = parent
        wp.__name__ = 'wikipage'
        request = testing.DummyRequest()
        self.assertEqual(wp.cook(request), EXPECTED)

    def test_cook_w_wiki_markup_and_html_no_match(self):
        TEXT = (u'Now is the time for ((<b>all good men</b>)) '
                 'to come to the aid of the Party')
        EXPECTED = (u'Now is the time for '
                     '<span class="wicked_unresolved"><b>all good men</b></span> '
                     '<a href="../add_wikipage.html'
                     '?title=all%20good%20men">+</a> '
                     'to come to the aid of the Party')
        wp = self._makeOne(text=TEXT)
        parent = testing.DummyModel()
        wp.__parent__ = parent
        wp.__name__ = 'wikipage'
        request = testing.DummyRequest()
        self.assertEqual(wp.cook(request), EXPECTED)

    def test_cook_w_wiki_markup_w_match(self):
        TEXT = (u'Now is the time for ((all good men)) '
                 'to come to the aid of the Party')
        EXPECTED = (u'Now is the time for '
                     '<a href="http://example.com/whatever/">'
                     '<span class="wicked_resolved">all good men</span></a> '
                     'to come to the aid of the Party')
        parent = testing.DummyModel()
        parent['whatever'] = testing.DummyModel(title='all good men')
        wp = self._makeOne(text=TEXT)
        wp.__parent__ = parent
        wp.__name__ = 'wikipage'
        request = testing.DummyRequest()
        self.assertEqual(wp.cook(request), EXPECTED)

    def test_cook_w_wiki_markup_and_entities_w_match(self):
        TEXT = (u'Now is the time for ((L&#225;)) '
                 'to come to the aid of the Party')
        EXPECTED = (u'Now is the time for '
                     '<a href="http://example.com/whatever/">'
                     '<span class="wicked_resolved">L&#225;</span></a> '
                     'to come to the aid of the Party')
        parent = testing.DummyModel()
        parent['whatever'] = testing.DummyModel(title=u'L\u00e1;')
        wp = self._makeOne(text=TEXT)
        wp.__parent__ = parent
        wp.__name__ = 'wikipage'
        request = testing.DummyRequest()
        self.assertEqual(wp.cook(request), EXPECTED)

    def test_cook_w_wiki_markup_and_html_w_match(self):
        TEXT = (u'Now is the time for ((<b>all good men</b>)) '
                 'to come to the aid of the Party')
        EXPECTED = (u'Now is the time for '
                     '<a href="http://example.com/whatever/">'
                     '<span class="wicked_resolved"><b>all good men</b></span></a> '
                     'to come to the aid of the Party')
        parent = testing.DummyModel()
        parent['whatever'] = testing.DummyModel(title='all good men')
        wp = self._makeOne(text=TEXT)
        wp.__parent__ = parent
        wp.__name__ = 'wikipage'
        request = testing.DummyRequest()
        self.assertEqual(wp.cook(request), EXPECTED)

    def test_instance_has_valid_construction(self):
        instance = self._makeOne()
        self.assertEqual(instance.title, u'title')
        self.assertEqual(instance.text, u'')
        self.assertEqual(instance.creator, u'admin')
        self.assertEqual(instance.modified_by, u'admin')

    def test_change_title_badtitle(self):
        page = self._makeOne()
        self.assertRaises(ValueError, page.change_title, '')

    def test_change_title_duptitle(self):
        page = self._makeOne()
        wiki = testing.DummyModel()
        exists = testing.DummyModel()
        exists.title = 'exists'
        exists.text = ''
        wiki['page'] = page
        wiki['exists'] = exists
        self.assertRaises(ValueError, page.change_title, 'exists')

    def test_change_title(self):
        page = self._makeOne(title='replace')
        wiki = testing.DummyModel()
        one = testing.DummyModel()
        one.title = 'one'
        one.text = 'hi ((dontreplace)) bye ((replace))'
        two = testing.DummyModel()
        two.title = 'two'
        two.text = 'bye ((replace)) hi ((dontreplace))'
        wiki['one'] = one
        wiki['two'] = two
        page.__parent__ = wiki
        page.change_title('target')
        self.assertEqual(page.title, 'target')
        self.assertEqual(one.text, 'hi ((dontreplace)) bye ((target))')
        self.assertEqual(two.text, 'bye ((target)) hi ((dontreplace))')

    def test_fix_links_no_changes(self):
        wiki = testing.DummyModel()
        wiki['one'] = self._makeOne('one', 'text of one')
        wiki['two'] = self._makeOne('two', 'I link to ((one))')
        changes = wiki['two'].fix_links()
        self.assertEqual(changes, [])
        self.assertEqual(wiki['two'].text, 'I link to ((one))')

    def test_fix_links_case(self):
        wiki = testing.DummyModel()
        wiki['One Page'] = self._makeOne('One Page', 'text of one')
        wiki['two'] = self._makeOne('two', 'I link to ((one page))')
        changes = wiki['two'].fix_links()
        self.assertEqual(changes, [('one page', 'One Page')])
        self.assertEqual(wiki['two'].text, 'I link to ((One Page))')

    def test_fix_links_strip(self):
        wiki = testing.DummyModel()
        wiki['one'] = self._makeOne('one', 'text of one')
        wiki['two'] = self._makeOne('two', 'I link to (( one ))')
        changes = wiki['two'].fix_links()
        self.assertEqual(changes, [(' one ', 'one')])
        self.assertEqual(wiki['two'].text, 'I link to ((one))')

    def test_fix_links_skip_nonexistent(self):
        wiki = testing.DummyModel()
        wiki['one'] = self._makeOne('one', 'text of one')
        wiki['two'] = self._makeOne('two', 'I link to ((one missing page))')
        changes = wiki['two'].fix_links()
        self.assertEqual(changes, [])
        self.assertEqual(wiki['two'].text, 'I link to ((one missing page))')

    def test_get_attachements(self):
        page = self._makeOne()
        self.assertEqual(page.get_attachments(), page)

    def test_revert(self):
        class Version:
            docid = 5l
            created = 'created'
            title = 'the title'
            description = 'description'
            modified = 'modified'
            user = 'modified_by'
            attrs = {
                'text': 'wiki text',
                'creator': 'creator'
            }

        page = self._makeOne()
        page.revert(Version)
        self.assertEqual(page.docid, 5)
        self.failUnless(type(page.docid), int)
        self.assertEqual(page.created, 'created')
        self.assertEqual(page.title, 'the title')
        self.assertEqual(page.description, 'description')
        self.assertEqual(page.modified, 'modified')
        self.assertEqual(page.modified_by, 'modified_by')
        self.assertEqual(page.text, 'wiki text')
        self.assertEqual(page.creator, 'creator')


class WikiPageVersionTests(unittest.TestCase):

    def _getTargetClass(self):
        from karl.content.models.wiki import WikiPageVersion
        return WikiPageVersion

    def _makeOne(self, context):
        return self._getTargetClass()(context)

    def test_version_w_modified_by(self):
        class Dummy(testing.DummyModel):
            pass
        root = testing.DummyModel()
        wiki = root['wiki'] = testing.DummyModel()
        page = wiki['page'] = Dummy(title='the title',
                                    description='description',
                                    created='created',
                                    modified='modified',
                                    docid=5,
                                    text='wiki text',
                                    creator='creator',
                                    modified_by='modified_by',
                                   )
        version = self._makeOne(page)
        self.assertEqual(version.title, 'the title')
        self.assertEqual(version.description, 'description')
        self.assertEqual(version.created, 'created')
        self.assertEqual(version.modified, 'modified')
        self.assertEqual(version.docid, 5)
        self.assertEqual(version.path, '/wiki/page')
        self.assertEqual(version.attrs['text'], 'wiki text')
        self.assertEqual(version.attrs['creator'], 'creator')
        self.assertEqual(version.attachments, None)
        self.failUnless(version.klass is Dummy)
        self.assertEqual(version.user, 'modified_by')
        self.assertEqual(version.comment, None)

    def test_version_no_modified_by(self):
        class Dummy(testing.DummyModel):
            pass
        root = testing.DummyModel()
        wiki = root['wiki'] = testing.DummyModel()
        page = wiki['page'] = Dummy(title='the title',
                                    description='description',
                                    created='created',
                                    modified='modified',
                                    docid=5,
                                    text='wiki text',
                                    creator='creator',
                                    modified_by=None,
                                   )
        version = self._makeOne(page)
        self.assertEqual(version.title, 'the title')
        self.assertEqual(version.description, 'description')
        self.assertEqual(version.created, 'created')
        self.assertEqual(version.modified, 'modified')
        self.assertEqual(version.docid, 5)
        self.assertEqual(version.path, '/wiki/page')
        self.assertEqual(version.attrs['text'], 'wiki text')
        self.assertEqual(version.attrs['creator'], 'creator')
        self.assertEqual(version.attachments, None)
        self.failUnless(version.klass is Dummy)
        self.assertEqual(version.user, 'creator')
        self.assertEqual(version.comment, None)


class WikiPageContainerVersionTests(unittest.TestCase):

    def _getTargetClass(self):
        from karl.content.models.wiki import WikiPageContainerVersion
        return WikiPageContainerVersion

    def _makeOne(self, context):
        return self._getTargetClass()(context)

    def test_container_version(self):
        root = testing.DummyModel()
        page = root['page'] = testing.DummyModel(docid=5)
        page['one'] = testing.DummyModel(docid=6)
        page['two'] = testing.DummyModel(docid=7)
        container = self._makeOne(page)
        self.assertEqual(container.container_id, 5)
        self.assertEqual(container.path, '/page')
        self.assertEqual(container.map, {'one': 6, 'two': 7})
        self.assertEqual(container.ns_map, {})


class TestWikiToolFactory(unittest.TestCase):
    def setUp(self):
        testing.cleanUp()

    def tearDown(self):
        testing.cleanUp()

    def _makeOne(self):
        from karl.content.models.wiki import wiki_tool_factory
        return wiki_tool_factory

    def test_factory(self):
        from repoze.lemonade.interfaces import IContentFactory
        karl.testing.registerAdapter(lambda *arg, **kw: DummyContent, (None,),
                                     IContentFactory)
        context = testing.DummyModel()
        request = testing.DummyRequest()
        factory = self._makeOne()
        factory.add(context, request)
        self.failUnless(context['wiki'])
        self.failUnless(factory.is_present(context, request))
        factory.remove(context, request)
        self.failIf(factory.is_present(context, request))

class DummyContent(object):
    def __init__(self, *arg, **kw):
        pass

