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

class IntranetsFolderTests(unittest.TestCase):
    def _getTargetClass(self):
        from karl.content.models.intranets import IntranetsFolder
        return IntranetsFolder

    def _makeOne(self):
        return self._getTargetClass()()

    def test_class_conforms_to_IIntranetsTool(self):
        from zope.interface.verify import verifyClass
        from karl.content.interfaces import IIntranetsTool
        verifyClass(IIntranetsTool, self._getTargetClass())

    def test_instance_conforms_to_IIntranetsTool(self):
        from zope.interface.verify import verifyObject
        from karl.content.interfaces import IIntranetsTool
        verifyObject(IIntranetsTool, self._makeOne())
    

class TestIntranetsToolFactory(unittest.TestCase):
    def setUp(self):
        testing.cleanUp()

    def tearDown(self):
        testing.cleanUp()

    def _makeOne(self):
        from karl.content.models.intranets import intranets_tool_factory
        return intranets_tool_factory

    def test_it(self):
        from repoze.lemonade.interfaces import IContentFactory
        karl.testing.registerAdapter(lambda *arg, **kw: DummyContent, (None,),
                                     IContentFactory)
        context = testing.DummyModel()
        request = testing.DummyRequest
        factory = self._makeOne()
        factory.add(context, request)
        self.failUnless(context['intranets'])
        feature = getattr(context, 'feature', None)
        self.assertEqual(feature, u'')
        self.failUnless(factory.is_present(context, request))
        factory.remove(context, request)
        self.failIf(factory.is_present(context, request))
        

class DummyContent:
    pass
