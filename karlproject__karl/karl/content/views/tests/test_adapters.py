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
import mock
from pyramid import testing
from karl import testing as karltesting
from datetime import datetime

from pyramid.testing import cleanUp


class TestFileInfo(unittest.TestCase):
    def setUp(self):
        config = cleanUp()
        config.add_static_view('static', 'karl.views:static')

    def tearDown(self):
        cleanUp()

    def _getTargetClass(self):
        from karl.content.views.adapters import FileInfo
        return FileInfo

    def _makeOne(self, context, request):
        return self._getTargetClass()(context, request)

    def test_class_conforms_to_IFileInfo(self):
        from zope.interface.verify import verifyClass
        from karl.content.views.interfaces import IFileInfo
        verifyClass(IFileInfo, self._getTargetClass())

    def test_title(self):
        context = testing.DummyModel(title='the title')
        request = testing.DummyRequest()
        adapter = self._makeOne(context, request)
        self.assertEqual(adapter.title, 'the title')

    def test_modified(self):
        now = datetime.now()
        context = testing.DummyModel(modified=now)
        request = testing.DummyRequest()
        adapter = self._makeOne(context, request)
        self.assertEqual(adapter.modified, now.strftime("%m/%d/%Y"))

    def test_url(self):
        context = testing.DummyModel()
        request = testing.DummyRequest()
        adapter = self._makeOne(context, request)
        self.assertEqual(adapter.url, 'http://example.com/')

    def test_mimeinfo_no_mimetype(self):
        context = testing.DummyModel()
        request = testing.DummyRequest()
        adapter = self._makeOne(context, request)
        self.assertEqual(adapter.mimeinfo, {
            'small_icon_name': 'files_folder_small.png',
            'small_icon_url':
                'http://example.com/static/images/files_folder_small.png',
            'title': 'Folder'})

    def test_mimeinfo_with_mimetype(self):
        mimeinfo = {'small_icon_name': 'iddybiddy.png'}
        def m(mimetype):
            return mimeinfo
        from karl.utilities.interfaces import IMimeInfo
        karltesting.registerUtility(m, IMimeInfo)
        context = testing.DummyModel(mimetype='abc')
        request = testing.DummyRequest()
        adapter = self._makeOne(context, request)
        self.assertEqual(adapter.mimeinfo, mimeinfo)

    def test_size(self):
        request = testing.DummyRequest()
        context = testing.DummyModel()

        context.size = 0
        adapter = self._makeOne(context, request)
        self.assertEqual(adapter.size, "0 bytes")

        context.size = 345
        adapter = self._makeOne(context, request)
        self.assertEqual(adapter.size, "345 bytes")

        context.size = 345000
        adapter = self._makeOne(context, request)
        self.assertEqual(adapter.size, "345.0 KB")

        context.size = 34500000
        adapter = self._makeOne(context, request)
        self.assertEqual(adapter.size, "34.5 MB")

    def test_modified_by_title(self):
        request = testing.DummyRequest()
        context = testing.DummyModel()
        root = karltesting.DummyRoot()
        root['foo'] = context
        context.modified_by = 'dummy1'

        adapter = self._makeOne(context, request)
        self.assertEqual(adapter.modified_by_title, "Dummy One")

    def test_modified_by_url(self):
        request = testing.DummyRequest()
        context = testing.DummyModel()
        root = karltesting.DummyRoot()
        root['foo'] = context
        context.modified_by = 'dummy1'

        adapter = self._makeOne(context, request)
        self.assertEqual(adapter.modified_by_url,
                         "http://example.com/profiles/dummy1/")


class TestBylineInfo(unittest.TestCase):
    def setUp(self):
        cleanUp()

    def tearDown(self):
        cleanUp()

    def _getTargetClass(self):
        from karl.content.views.adapters import BylineInfo
        return BylineInfo

    def _makeOne(self, context, request):
        return self._getTargetClass()(context, request)

    def test_class_conforms_to_IBylineInfo(self):
        from zope.interface.verify import verifyClass
        from karl.content.views.interfaces import IBylineInfo
        verifyClass(IBylineInfo, self._getTargetClass())

    def test_author_name(self):
        context = DummyContext()
        request = testing.DummyRequest()
        adapter = self._makeOne(context, request)
        self.assertEqual(adapter.author_name, 'Dummy Profile')

    def test_author_url(self):
        context = DummyContext()
        request = testing.DummyRequest()
        adapter = self._makeOne(context, request)
        self.assertEqual(adapter.author_url,
                         'http://example.com/profiles/dummy/')

    def test_posted_date(self):
        from karl.utilities.interfaces import IKarlDates
        context = DummyContext()
        request = testing.DummyRequest()
        dummy = mock.Mock(return_value = mock.sentinel.SOMEDATE)
        karltesting.registerUtility(dummy, IKarlDates)
        adapter = self._makeOne(context, request)
        self.assertEqual(adapter.posted_date, mock.sentinel.SOMEDATE)
        dummy.assert_called_once_with(
            datetime(2009, 1, 28, 13, 32, 0, 928857),
            'longform',
            )

    def test_posted_date_compact(self):
        from karl.utilities.interfaces import IKarlDates
        context = DummyContext()
        request = testing.DummyRequest()
        dummy = mock.Mock(return_value = mock.sentinel.SOMEDATE)
        karltesting.registerUtility(dummy, IKarlDates)
        adapter = self._makeOne(context, request)
        self.assertEqual(adapter.posted_date_compact, mock.sentinel.SOMEDATE)
        dummy.assert_called_once_with(
            datetime(2009, 1, 28, 13, 32, 0, 928857),
            'compact',
            )


class TestBlogEntryAlert(unittest.TestCase):

    def setUp(self):
        from zope.interface import directlyProvides
        from karl.content.interfaces import IBlogEntry

        config = cleanUp()
        config.setup_registry() # this is not a unit test

        karltesting.registerSettings()

        # Create dummy site skel
        self.community = community = karltesting.DummyCommunity()
        site = community.__parent__.__parent__

        profiles = testing.DummyModel()
        site["profiles"] = profiles
        self.profile = profiles["member"] = karltesting.DummyProfile()
        profiles["creator"] = karltesting.DummyProfile()

        community["blog"] = testing.DummyModel()

        blogentry = testing.DummyModel(text="This is a test")
        community["blog"]["blogentry"] = blogentry
        blogentry["attachments"] = testing.DummyModel()
        blogentry.title = "Blog Entry"
        blogentry.docid = 0
        directlyProvides(blogentry, IBlogEntry)
        self.blogentry = blogentry
        blogentry.creator = "creator"

    def tearDown(self):
        cleanUp()

    def _getTargetClass(self):
        from karl.content.views.adapters import BlogEntryAlert
        return BlogEntryAlert

    def _makeOne(self, context, profile, request):
        return self._getTargetClass()(context, profile, request)

    def test_class_conforms_to_IAlert(self):
        from zope.interface.verify import verifyClass
        from karl.utilities.interfaces import IAlert
        verifyClass(IAlert, self._getTargetClass())

    def test_alert(self):
        from repoze.postoffice.message import Message
        request = testing.DummyRequest()
        alert = self._makeOne(self.blogentry, self.profile, request)
        self.assertEqual(1, len(alert.mto))
        self.assertEqual("member@x.org", alert.mto[0])

        self.failUnless(isinstance(alert.message, Message))
        self.assertEqual(alert.message["reply-to"],
                         u'"Dummy Communit\xe0" <community+blog-7FFFFFFF'
                          '@karl3.example.com>'
                        )
        self.assertEqual(alert.message['Precedence'], 'bulk')

    def test_digest(self):
        from repoze.postoffice.message import Message
        request = testing.DummyRequest()
        alert = self._makeOne(self.blogentry, self.profile, request)
        alert.digest = True
        self.assertEqual(1, len(alert.mto))
        self.assertEqual("member@x.org", alert.mto[0])

        self.failUnless(isinstance(alert.message, Message))
        self.assertEqual( alert.message["reply-to"],
                         u'"Dummy Communit\xe0" <community+blog-7FFFFFFF'
                          '@karl3.example.com>'
                        )

    def test_digest_malformed_text(self):
        from repoze.postoffice.message import Message
        self.blogentry.text = malformed_text
        request = testing.DummyRequest()
        alert = self._makeOne(self.blogentry, self.profile, request)
        alert.digest = True
        self.assertEqual(1, len(alert.mto))
        self.assertEqual("member@x.org", alert.mto[0])

        self.failUnless(isinstance(alert.message, Message))
        self.assertEqual(alert.message["reply-to"],
                         u'"Dummy Communit\xe0" <community+blog-7FFFFFFF'
                          '@karl3.example.com>'
                        )


class TestBlogCommentAlert(unittest.TestCase):

    def setUp(self):
        import datetime
        from zope.interface import directlyProvides
        from karl.content.interfaces import IBlogEntry

        cleanUp()
        karltesting.registerSettings()

        # Create dummy site skel
        community = karltesting.DummyCommunity()
        site = community.__parent__.__parent__

        profiles = testing.DummyModel()
        site["profiles"] = profiles
        self.profile = profiles["member"] = karltesting.DummyProfile()
        profiles["creator"] = karltesting.DummyProfile()

        community["blog"] = testing.DummyModel()

        blogentry = testing.DummyModel(text="This is a test")
        blogentry.created = datetime.datetime(2010, 5, 12, 2, 42)
        blogentry.creator = 'member'
        community["blog"]["blogentry"] = blogentry
        blogentry["attachments"] = testing.DummyModel()
        blogentry.title = "Blog Entry"
        blogentry.docid = 0
        directlyProvides(blogentry, IBlogEntry)
        self.blogentry = blogentry

        blogentry["comments"] = testing.DummyModel()
        self.comment = self._add_comment(blogentry)

    def tearDown(self):
        cleanUp()

    def _add_comment(self, blogentry,
                     name="comment",
                     text="This is a test.",
                     creator="creator"):
        from zope.interface import directlyProvides
        from karl.models.interfaces import IComment
        comments = blogentry["comments"]
        comments[name] = comment = testing.DummyModel()
        directlyProvides(comment, IComment)
        comment.text = text
        comment.creator = creator
        comment.created = len(comments)
        return comment

    def _getTargetClass(self):
        from karl.content.views.adapters import BlogCommentAlert
        return BlogCommentAlert

    def _makeOne(self, context, profile, request):
        return self._getTargetClass()(context, profile, request)

    def test_class_conforms_to_IAlert(self):
        from zope.interface.verify import verifyClass
        from karl.utilities.interfaces import IAlert
        verifyClass(IAlert, self._getTargetClass())

    def test_ctor_with_forum_comment(self):
        # LP #615370:  comment alerts need to work against forum topics, too.
        from zope.interface import directlyProvides
        from karl.content.interfaces import IForumTopic
        topic = testing.DummyModel(text="This is a test")
        community = self.blogentry.__parent__.__parent__
        community["forum"] = testing.DummyModel()
        community["forum"]["topic"] = topic
        topic["attachments"] = testing.DummyModel()
        topic["comments"] = testing.DummyModel()
        topic.title = "Forum Post"
        topic.docid = 0
        directlyProvides(topic, IForumTopic)
        comment = self._add_comment(topic)
        request = testing.DummyRequest()
        alert = self._makeOne(comment, self.profile, request)
        self.failUnless(alert._blogentry is topic)

    def test_alert(self):
        from repoze.postoffice.message import Message
        renderer = karltesting.registerDummyRenderer(
            'templates/email_blog_comment_alert.pt')
        request = testing.DummyRequest()
        alert = self._makeOne(self.comment, self.profile, request)
        self.assertEqual(1, len(alert.mto))
        self.assertEqual("member@x.org", alert.mto[0])

        self.failUnless(isinstance(alert.message, Message))
        self.assertEqual(alert.message["reply-to"],
                         u'"Dummy Communit\xe0" <community+blog-7FFFFFFF'
                          '@karl3.example.com>'
                        )
        self.assertEqual(alert.message['Precedence'], 'bulk')

        messages, n = renderer.history
        self.assertEqual(n, 1)
        self.assertEqual(messages[0], self.blogentry)

    def test_alert_template(self):
        from repoze.postoffice.message import Message
        request = testing.DummyRequest()
        alert = self._makeOne(self.comment, self.profile, request)
        self.failUnless(isinstance(alert.message, Message))

    def test_digest(self):
        from repoze.postoffice.message import Message
        renderer = karltesting.registerDummyRenderer(
            'templates/email_blog_comment_alert.pt')
        renderer.string_response = "<body>Dummy message body.</body>"

        request = testing.DummyRequest()
        alert = self._makeOne(self.comment, self.profile, request)
        alert.digest = True
        self.assertEqual(1, len(alert.mto))
        self.assertEqual("member@x.org", alert.mto[0])

        self.failUnless(isinstance(alert.message, Message))
        self.assertEqual(alert.message["reply-to"],
                         u'"Dummy Communit\xe0" <community+blog-7FFFFFFF'
                          '@karl3.example.com>'
                        )
        self.assertEqual(renderer.history, ([], 0))

    def test_long_history(self):
        from repoze.postoffice.message import Message
        comments = []
        for i in xrange(6):
            comments.append(
                self._add_comment(self.blogentry, "comment%d" % i))

        renderer = karltesting.registerDummyRenderer(
            'templates/email_blog_comment_alert.pt')
        request = testing.DummyRequest()
        alert = self._makeOne(self.comment, self.profile, request)
        self.assertEqual(1, len(alert.mto))
        self.assertEqual("member@x.org", alert.mto[0])

        self.failUnless(isinstance(alert.message, Message))
        self.assertEqual(alert.message["reply-to"],
                         u'"Dummy Communit\xe0" <community+blog-7FFFFFFF'
                          '@karl3.example.com>'
                        )

        messages, n = renderer.history
        self.assertEqual(n, 7)
        self.assertEqual(len(messages), 7)
        self.assertEqual(messages[0], self.blogentry)
        self.assertEqual(messages[1], comments[0])
        self.assertEqual(messages[2], comments[1])
        self.assertEqual(messages[3], comments[2])
        self.assertEqual(messages[4], comments[3])
        self.assertEqual(messages[5], comments[4])
        self.assertEqual(messages[6], comments[5])


class TestCalendarEventAlert(unittest.TestCase):

    def setUp(self):
        from zope.interface import directlyProvides
        from karl.content.interfaces import ICalendarEvent

        config = cleanUp()
        config.setup_registry() # this is not a unit test

        karltesting.registerSettings()
        karltesting.registerKarlDates()

        # Create dummy site skel
        community = karltesting.DummyCommunity()
        site = community.__parent__.__parent__

        profiles = testing.DummyModel()
        site["profiles"] = profiles
        self.profile = profiles["member"] = karltesting.DummyProfile()
        profiles["creator"] = karltesting.DummyProfile()

        community["calendar"] = testing.DummyModel()

        event = testing.DummyModel(
            text="This is a test",
            description="Some description",
            startDate=datetime(2009, 8, 5, 10, 0),
            endDate=datetime(2009, 8, 5, 11, 0),
            attendees=['alice', 'bob'],
            location='NYC',
            contact_name='Alice W',
            contact_email='alice@wonderland.org',
            )
        community["calendar"]["event"] = event
        event.title = "An Exciting Event!"
        event.docid = 0
        directlyProvides(event, ICalendarEvent)
        self.event = event
        event.creator = "creator"

    def tearDown(self):
        cleanUp()

    def _getTargetClass(self):
        from karl.content.views.adapters import CalendarEventAlert
        return CalendarEventAlert

    def _makeOne(self, context, profile, request):
        return self._getTargetClass()(context, profile, request)

    def test_class_conforms_to_IAlert(self):
        from zope.interface.verify import verifyClass
        from karl.utilities.interfaces import IAlert
        verifyClass(IAlert, self._getTargetClass())

    def test_alert(self):
        from repoze.postoffice.message import Message

        request = testing.DummyRequest()
        alert = self._makeOne(self.event, self.profile, request)
        self.assertEqual(1, len(alert.mto))
        self.assertEqual("member@x.org", alert.mto[0])

        self.failUnless(isinstance(alert.message, Message))
        self.assertEqual(alert.message["to"],
                         u'"Dummy Communit\xe0" <member@x.org>')
        self.assertEqual(alert.message["subject"],
                         u'[Dummy Communit\xe0] An Exciting Event!')
        self.assertEqual(alert.message["from"],
                         u'"title | karl3test" <alerts@karl3.example.com>')
        self.assertEqual(
            alert.startDate, 'Wednesday, January 28, 2009 08:32 AM')
        self.assertEqual(
            alert.endDate, 'Wednesday, January 28, 2009 08:32 AM')
        self.assertEqual(alert.attendees, 'alice; bob')
        self.assertEqual(alert.message['Precedence'], 'bulk')

    def test_digest(self):
        from repoze.postoffice.message import Message

        request = testing.DummyRequest()
        alert = self._makeOne(self.event, self.profile, request)
        alert.digest = True
        self.assertEqual(1, len(alert.mto))
        self.assertEqual("member@x.org", alert.mto[0])

        self.failUnless(isinstance(alert.message, Message))
        self.assertEqual(alert.message["to"],
                         u'"Dummy Communit\xe0" <member@x.org>')
        self.assertEqual(alert.message["subject"],
                         u'[Dummy Communit\xe0] An Exciting Event!')
        self.assertEqual(alert.message["from"],
                         u'"title | karl3test" <alerts@karl3.example.com>')


class TestCommunityFileAlert(unittest.TestCase):

    def setUp(self):
        from zope.interface import directlyProvides
        from karl.content.interfaces import ICommunityFile

        config = cleanUp()
        config.setup_registry() # this is not a unit test

        karltesting.registerSettings()

        # Create dummy site skel
        community = karltesting.DummyCommunity()
        site = community.__parent__.__parent__

        profiles = testing.DummyModel()
        site["profiles"] = profiles
        self.profile = profiles["member"] = karltesting.DummyProfile()
        profiles["creator"] = karltesting.DummyProfile()

        community["files"] = testing.DummyModel()

        f = testing.DummyModel(
            text="This is a test", description="Some description")
        community["files"]["file"] = f
        f.title = "An interesting file"
        f.docid = 0
        directlyProvides(f, ICommunityFile)
        self.f = f
        f.creator = "creator"

    def tearDown(self):
        cleanUp()

    def _getTargetClass(self):
        from karl.content.views.adapters import CommunityFileAlert
        return CommunityFileAlert

    def _makeOne(self, context, profile, request):
        return self._getTargetClass()(context, profile, request)

    def test_class_conforms_to_IAlert(self):
        from zope.interface.verify import verifyClass
        from karl.utilities.interfaces import IAlert
        verifyClass(IAlert, self._getTargetClass())

    def test_alert(self):
        from repoze.postoffice.message import Message
        request = testing.DummyRequest()
        alert = self._makeOne(self.f, self.profile, request)
        alert.digest = True
        self.assertEqual(1, len(alert.mto))
        self.assertEqual("member@x.org", alert.mto[0])

        self.failUnless(isinstance(alert.message, Message))
        self.assertEqual(alert.message["to"],
                         u'"Dummy Communit\xe0" <member@x.org>')
        self.assertEqual(alert.message["subject"],
                         u'[Dummy Communit\xe0] An interesting file')
        self.assertEqual(alert.message["from"],
                         u'"title | karl3test" <alerts@karl3.example.com>')
        self.assertEqual(alert.message['Precedence'], 'bulk')


class TestForumPortlet(unittest.TestCase):
    def setUp(self):
        cleanUp()

    def tearDown(self):
        cleanUp()

    def _register(self):
        from karl.models.interfaces import ICatalogSearch
        from zope.interface import Interface
        karltesting.registerAdapter(
            DummySearchAdapter, Interface, ICatalogSearch)

    def _getTargetClass(self):
        from karl.content.views.adapters import ForumPortlet
        return ForumPortlet

    def _makeOne(self, context, request):
        return self._getTargetClass()(context, request)

    def test_class_conforms_to_IIntranetPortlet(self):
        from zope.interface.verify import verifyClass
        from karl.views.interfaces import IIntranetPortlet
        verifyClass(IIntranetPortlet, self._getTargetClass())

    def test_title(self):
        context = testing.DummyModel(title='the title')
        request = testing.DummyRequest()
        adapter = self._makeOne(context, request)
        self.assertEqual(adapter.title, 'the title')

    def test_href(self):
        context = testing.DummyModel(title='the title')
        request = testing.DummyRequest()
        adapter = self._makeOne(context, request)
        self.assertEqual(adapter.href, 'http://example.com/')

    def test_entries(self):
        self._register()
        context = testing.DummyModel(title='the title')
        request = testing.DummyRequest()
        adapter = self._makeOne(context, request)
        self.assertEqual(adapter.entries, None)

    def test_asHTML(self):
        self._register()
        context = testing.DummyModel(title='the title')
        request = testing.DummyRequest()
        adapter = self._makeOne(context, request)
        self.assert_(adapter.asHTML.startswith('<div'))


class TestDefaultShowSendalert(unittest.TestCase):
    def setUp(self):
        cleanUp()

    def tearDown(self):
        cleanUp()

    def _getTargetClass(self):
        from karl.content.views.adapters import DefaultShowSendalert
        return DefaultShowSendalert

    def test_class_conforms_to_interface(self):
        from zope.interface.verify import verifyClass
        from karl.content.views.interfaces import IShowSendalert
        verifyClass(IShowSendalert, self._getTargetClass())

    def _call_fut(self, context, request):
        adapter = self._getTargetClass()(context, request)
        return adapter.show_sendalert

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


class DummySearchAdapter:
    def __init__(self, context):
        self.context = context

    def __call__(self, **kw):
        return 0, [], None


class DummyContext(testing.DummyModel):
    creator=u'dummy'
    created_timestamp = 1233149520.9288571
    posted_date = 'Wednesday, January 28, 2009 08:32 AM'

    def __init__(self):
        testing.DummyModel.__init__(self)
        parent = self.__parent__ = testing.DummyModel()
        profile = testing.DummyModel()
        profile.title = 'Dummy Profile'
        parent['profiles'] = profiles = testing.DummyModel()
        profiles[u'dummy'] = profile
        self.created = datetime.utcfromtimestamp(self.created_timestamp)

malformed_text = """<p>In oil-rich Nigeria, Africa's most populous nation,
where watchdog
groups say efforts to combat corruption are backsliding
<a href="http://www.hrw.org/en/news/2009/06/07/nigeria-abusers-reign-midterm">
http://www.hrw.org/en/news/2009/06/07/nigeria-abusers-reign-midterm</a> ,
Nuhu Ribadu,
<http://www.pbs.org/frontlineworld/stories/bribe/2009/05/lowell-bergman.
html> who built a well-trained staff of investigators at the Economic
and Financial Crimes Commission, said he fled his homeland into
self-imposed exile in England in December. Officials had sent Mr. Ribadu
away to a training course a year earlier, soon after his agency charged
a wealthy, politically connected former governor with trying to bribe
officials on his staff with huge sacks stuffed with $15 million in $100
bills. Mr. Ribadu, who was dismissed from the police force last year,
said he had received death threats and was fired upon in September by
assailants.</p>"""
