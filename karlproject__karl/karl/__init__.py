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

__import__('pkg_resources').declare_namespace(__name__)

# shim to atone for usage of zope.testing.cleanUp in the test suite;
# this doesn't belong here at all and must go away when the use of
# zope.testing.cleanup.cleanUp is exorcised from the codebase

try:
    import zope.testing.cleanup
    from pyramid.testing import setUp
    zope.testing.cleanup.addCleanUp(setUp)
except ImportError:
    pass

# for pickles that referred to bfg; conditionalized because buildout
# imports our __init__ during pkg_resource scanning, causing a race
try:
    import pyramid.security
    import pyramid.interfaces
    import sys
    sys.modules['repoze.bfg.security'] = pyramid.security
    sys.modules['repoze.bfg.interfaces'] = pyramid.interfaces
except ImportError:
    pass

# formish 0.8.5.2 needs to import UnicodeMultiDict from webob; webob 1.0+
# moved it; pyramid doesn't work with any webob < 1.0; conditionalized because
# buildout imports our __init__ during resource scanning causing a race
try:
    from webob.multidict import UnicodeMultiDict
    import webob
    webob.UnicodeMultiDict = UnicodeMultiDict
except ImportError:
    pass

