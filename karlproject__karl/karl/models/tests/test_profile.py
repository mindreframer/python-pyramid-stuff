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

class ProfileTests(unittest.TestCase):

    def setUp(self):
        from zope.testing.cleanup import cleanUp
        cleanUp()

    def tearDown(self):
        from zope.testing.cleanup import cleanUp
        cleanUp()

    def _getTargetClass(self):
        from karl.models.profile import Profile
        return Profile

    def _makeOne(self, **kw):
        return self._getTargetClass()(**kw)

    def test_verifyImplements(self):
        from zope.interface.verify import verifyClass
        from karl.models.interfaces import IProfile
        verifyClass(IProfile, self._getTargetClass())

    def test_verifyProvides(self):
        from zope.interface.verify import verifyObject
        from karl.models.interfaces import IProfile
        verifyObject(IProfile, self._makeOne())

    def test_ctor(self):
        inst = self._makeOne(firstname='fred')
        self.assertEqual(inst.firstname, 'fred')

    def test_creator_is___name__(self):
        from pyramid.testing import DummyModel
        profiles = DummyModel()
        inst = profiles['flinty'] = self._makeOne(firstname='fred',
                                                  lastname='flintstone ')

        self.assertEqual(inst.creator, 'flinty')

    def test_title(self):
        inst = self._makeOne(firstname='fred', lastname='flintstone ')
        self.assertEqual(inst.title, 'fred flintstone')

    def test_title_inactive(self):
        inst = self._makeOne(firstname='fred', lastname='flintstone ')
        inst.security_state = 'inactive'
        self.assertEqual(inst.title, 'fred flintstone (Inactive)')

    def test_folderish(self):
        from repoze.folder import Folder
        from repoze.folder.interfaces import IFolder
        cls = self._getTargetClass()
        self.failUnless(IFolder.implementedBy(cls))
        o = self._makeOne()
        self.failUnless(IFolder.providedBy(o))
        self.failUnless(isinstance(o, Folder))
        self.failUnless(hasattr(o, "data"))

    def test_alert_prefs(self):
        from karl.models.interfaces import IProfile
        inst = self._makeOne()
        self.assertEqual(IProfile.ALERT_IMMEDIATELY,
                         inst.get_alerts_preference("foo"))
        inst.set_alerts_preference("foo", IProfile.ALERT_DIGEST)
        self.assertEqual(IProfile.ALERT_DIGEST,
                         inst.get_alerts_preference("foo"))
        inst.set_alerts_preference("foo", IProfile.ALERT_NEVER)
        self.assertEqual(IProfile.ALERT_NEVER,
                         inst.get_alerts_preference("foo"))

        self.assertRaises(ValueError, inst.set_alerts_preference, "foo", 13)

    def test_verify_alert_prefs_persistent(self):
        from persistent.mapping import PersistentMapping
        inst = self._makeOne()
        self.failUnless(isinstance(inst._alert_prefs, PersistentMapping))

    def test_pending_alerts(self):
        inst = self._makeOne()
        self.assertEqual(0, len(inst._pending_alerts))
        inst._pending_alerts.append( "FOO" )
        self.assertEqual(1, len(inst._pending_alerts))
        self.assertEqual("FOO", inst._pending_alerts.pop(0))
        self.assertEqual(0, len(inst._pending_alerts))

    def test_pending_alerts_persistent(self):
        from persistent.list import PersistentList
        inst = self._makeOne()
        self.failUnless(isinstance(inst._pending_alerts, PersistentList))

    def test_empty_country(self):
        inst = self._makeOne()
        self.assertEqual(inst.country, 'XX')

    def test_invalid_country(self):
        inst = self._makeOne(country='XY')
        self.assertEqual(inst.country, 'XX')

    def test_empty_date_format(self):
        inst = self._makeOne()
        self.assertEqual(inst.date_format, None)

    def test_invalid_date_format(self):
        inst = self._makeOne(date_format='XY')
        self.assertEqual(inst.date_format, None)

    def test_valid_date_format(self):
        inst = self._makeOne(date_format='en-US')
        self.assertEqual(inst.date_format, 'en-US')

    def test_valid_country(self):
        inst = self._makeOne(country='HT')
        self.assertEqual(inst.country, 'HT')

    def test_website_websites_new_instance(self):
        inst = self._makeOne()
        self.assertEqual(inst.website, '')
        self.assertEqual(list(inst.websites), [])

    def test_websites_as_empty_list(self):
        inst = self._makeOne(websites=[])
        self.assertEqual(inst.website, '')
        self.assertEqual(inst.websites, [])

    def test_website_not_settable(self):
        inst = self._makeOne()
        try:
            inst.website = 'http://example.com/'
        except AttributeError:
            pass
        else:
            raise AssertionError('website should not be settable.')

    def test_old_website_gets_included_in_websites(self):
        inst = self._makeOne()
        inst.__dict__['website'] = 'http://example.com/'
        self.assertEqual(list(inst.websites), ['http://example.com/'])

    def test_seting_websites_clears_old_website(self):
        inst = self._makeOne()
        inst.__dict__['website'] = 'http://example.com/'
        inst.websites = ['http://another.example.com/',
                         'http://yetanother.example.com/']
        self.failIf('website' in inst.__dict__)

class ProfilesFolderTests(unittest.TestCase):

    def setUp(self):
        from zope.testing.cleanup import cleanUp
        cleanUp()

    def tearDown(self):
        from zope.testing.cleanup import cleanUp
        cleanUp()

    def _getTargetClass(self):
        from karl.models.profile import ProfilesFolder
        return ProfilesFolder

    def _makeOne(self, **kw):
        return self._getTargetClass()(**kw)

    def test_verifyImplements(self):
        from zope.interface.verify import verifyClass
        from karl.models.interfaces import IProfiles
        verifyClass(IProfiles, self._getTargetClass())

    def test_verifyProvides(self):
        from zope.interface.verify import verifyObject
        from karl.models.interfaces import IProfiles
        verifyObject(IProfiles, self._makeOne())

    def test___init___defaults(self):
        pf = self._makeOne()
        self.assertEqual(len(pf.email_to_name), 0)
        self.assertEqual(pf.email_to_name.get('nonesuch'), None)

    def test_getProfileByEmail_miss(self):
        pf = self._makeOne()
        self.assertEqual(pf.getProfileByEmail('nonesuch@example.com'), None)

    def test_getProfileByEmail_hit(self):
        from pyramid.testing import DummyModel
        pf = self._makeOne()
        profile = pf['extant'] = DummyModel()
        pf.email_to_name['extant@example.com'] = 'extant'
        self.failUnless(pf.getProfileByEmail('extant@example.com') is profile)

    def test_getProfileByEmail_mixedcase(self):
        from pyramid.testing import DummyModel
        pf = self._makeOne()
        profile = pf['extant'] = DummyModel()
        pf.email_to_name['eXtant@example.com'] = 'extant'
        self.failUnless(pf.getProfileByEmail('Extant@example.com') is profile)


class Test_profile_textindexdata(unittest.TestCase):

    def _callFUT(self, profile):
        from karl.models.profile import profile_textindexdata
        return profile_textindexdata(profile)

    def test_no_attrs(self):
        from pyramid.testing import DummyModel
        callable = self._callFUT(DummyModel(title='title'))
        self.assertEqual(callable(), ('title', ''))

    def test_w_all_attrs(self):
        from pyramid.testing import DummyModel
        ATTR_NAMES = [
            '__name__',
            'firstname',
            'lastname',
            'email',
            'phone',
            'extension',
            'department',
            'position',
            'organization',
            'location',
            'country',
            'website',
            'languages',
            'office',
            'room_no',
            'biography',
        ]
        ATTR_VALUES = [x.upper() for x in ATTR_NAMES]
        mapping = dict(zip(ATTR_NAMES, ATTR_VALUES))
        mapping['title'] = 'TITLE'
        profile = DummyModel(**mapping)
        callable = self._callFUT(profile)
        self.assertEqual(callable(), ('TITLE', '\n'.join(ATTR_VALUES)))

    def test_w_extra_attrs(self):
        from pyramid.testing import DummyModel
        profile = DummyModel(title='Phred Phlyntstone',
                             firstname='Phred',
                             lastname='Phlyntstone',
                             town='Bedrock',
                            )
        callable = self._callFUT(profile)
        self.assertEqual(callable(),
                         ('Phred Phlyntstone', 'Phred\nPhlyntstone'))

    def test_w_UTF8_attrs(self):
        from pyramid.testing import DummyModel
        FIRSTNAME = u'Phr\xE9d'
        profile = DummyModel(title='title', firstname=FIRSTNAME.encode('UTF8'))
        callable = self._callFUT(profile)
        self.assertEqual(callable(), ('title', FIRSTNAME))

    def test_w_latin1_attrs(self):
        from pyramid.testing import DummyModel
        FIRSTNAME = u'Phr\xE9d'
        profile = DummyModel(title='title',
                             firstname=FIRSTNAME.encode('latin1'))
        callable = self._callFUT(profile)
        self.assertEqual(callable(), ('title', FIRSTNAME))
