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

class ExtractDescriptionTests(unittest.TestCase):

    def _callFUT(self, htmlstring):
        from karl.content.views.utils import extract_description
        return extract_description(htmlstring)

    def test_plain_bytes(self):
        summary = self._callFUT("I am text")
        self.assertEqual(summary, "I am text")

    def test_plain_unicode(self):
        summary = self._callFUT(u"I am text")
        self.assertEqual(summary, u"I am text")

    def test_html_body(self):
        summary = self._callFUT("<html><body>I am text</body></html>")
        self.assertEqual(summary, "I am text")

    def test_html_elements(self):
        summary = self._callFUT("<div>I</div> <span>am</span> <b>text</b>")
        self.assertEqual(summary, "I am text")

    def test_bad_html(self):
        summary = self._callFUT("<b>I <i>am</i> <u>broken text")
        self.assertEqual(summary, "I am broken text")

    def test_newline(self):
        summary = self._callFUT("I am \r\n divided text")
        self.assertEqual(summary, "I am divided text")

    def test_wiki_markup(self):
        summary = self._callFUT("I am ((wiki linked)) text")
        self.assertEqual(summary, "I am wiki linked text")

    def test_limit(self):
        summary = self._callFUT("I am quite long text. " * 50)
        self.assertEqual(len(summary), 222)
        self.assertTrue(summary.endswith('...'))

    def test_link_text(self):
        # See https://bugs.launchpad.net/karl3/+bug/663399
        HTML = ('<p>Hi All,</p>\r\n<p>I just came across this post '
                'via the Council on Foundations\' Twitter Feed.&#160; '
                'Apparently the '
                '<a href="http://craigslistfoundation.org/">Craigslist '
                'Foundation</a> is going to build a knowledge sharing '
                'tool/community/platform - it\'s a bit unclear at this '
                'point.&#160;')
        WORDS = ('Hi All, I just came across this post '
                 'via the Council on Foundations\' Twitter Feed. '
                 'Apparently the Craigslist Foundation '
                 'is going to build a knowledge sharing '
                 'tool/community/platform - it\'s a bit unclear '
                 'at this point.'
                )
        summary = self._callFUT(HTML)
        self.assertEqual(summary, WORDS)

class Test_get_show_sendalert(unittest.TestCase):
    def setUp(self):
        testing.cleanUp()

    def tearDown(self):
        testing.cleanUp()

    def _call_fut(self, context, request):
        from karl.content.views.utils import get_show_sendalert
        return get_show_sendalert(context, request)

    def test_not_intranet(self):
        context = testing.DummyModel()
        self.failUnless(self._call_fut(context, None))

    def test_in_intranet(self):
        from karl.content.interfaces import IIntranets
        from zope.interface import directlyProvides
        intranet = testing.DummyModel()
        directlyProvides(intranet, IIntranets)
        intranet['foo'] = context = testing.DummyModel()
        self.failIf(self._call_fut(context, None))

    def test_override_adapter(self):
        class DummyAdapter(object):
            show_sendalert = 'foo'
            def __init__(self, context, request):
                pass

        from zope.interface import Interface
        from karl.content.views.interfaces import IShowSendalert
        karl.testing.registerAdapter(
            DummyAdapter, (Interface, Interface), IShowSendalert
        )

        context = testing.DummyModel()
        request = testing.DummyRequest()
        self.assertEqual(self._call_fut(context, request), 'foo')

class TestGetUploadMimetype(unittest.TestCase):
    def _callFUT(self, fieldstorage):
        from karl.content.views.utils import get_upload_mimetype
        return get_upload_mimetype(fieldstorage)

    def test_good_upload(self):
        fieldstorage = DummyFieldStorage()
        mimetype = self._callFUT(fieldstorage)
        self.assertEqual(mimetype, "x/foo")

    def test_fix_broken_upload(self):
        fieldstorage = DummyFieldStorage()
        fieldstorage.type = 'application/x-download'
        fieldstorage.filename = 'file.pdf'
        mimetype = self._callFUT(fieldstorage)
        self.assertEqual(mimetype, "application/pdf")

    def test_cant_fix_broken_upload(self):
        fieldstorage = DummyFieldStorage()
        fieldstorage.type = 'application/x-download'
        fieldstorage.filename = 'somefile'
        mimetype = self._callFUT(fieldstorage)
        self.assertEqual(mimetype, "application/x-download")

    def test_fix_bad_ie_jpeg_mimetype(self):
        fieldstorage = DummyFieldStorage()
        fieldstorage.type = None
        fieldstorage.mimetype = 'image/pjpeg'
        fieldstorage.filename = 'file.jpg'
        mimetype = self._callFUT(fieldstorage)
        self.assertEqual(mimetype, "image/jpeg")

    def test_fix_bad_ie_png_mimetype(self):
        fieldstorage = DummyFieldStorage()
        fieldstorage.type = 'image/x-png'
        fieldstorage.filename = 'file.png'
        mimetype = self._callFUT(fieldstorage)
        self.assertEqual(mimetype, "image/png")


class DummyFieldStorage:
    file = 'abc'
    filename = 'filename'
    type = 'x/foo'
