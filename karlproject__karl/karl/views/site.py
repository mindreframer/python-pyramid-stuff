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

"""Publish static resources under /static/"""

import os
import re

from pyramid.httpexceptions import HTTPFound

from pyramid.url import resource_url
from pyramid.static import static_view

from karl.views.utils import get_user_home
from karl.views.utils import get_static_url

here = os.path.abspath(os.path.dirname(__file__))

# five year expires time
static_view = static_view('static', cache_max_age=157680000, use_subpath=True)

version_match = re.compile(r'^r-?\d+$').match
# version number is "r" plus an integer (possibly negative)

def versioning_static_view(context, request):
    # if the first element in the subpath is the version number, strip
    # it out of the subpath (see views/api.py static_url)
    subpath = request.subpath
    if subpath and version_match(subpath[0]):
        request.subpath = subpath[1:]
    return static_view(context, request)

def site_view(context, request):
    home, extra_path = get_user_home(context, request)
    return HTTPFound(location=resource_url(home, request, *extra_path))

class StaticRootFactory(object):
    def __init__(self, environ):
        pass


def expired_static(context, request):
    """Redirect static urls that use an expired revision segment
    to the currently active one. This has the following advantages:
    
    - prevent static links from saved content causing a 404
      (instead they will give a 303 and go to the current version)
    
    - make it easier to find the QUnit tests from a browser.

    """
    path = request.matchdict['path']
    path0 = path[0]
    # Is the first segment a r1234455667 format?
    first_segment = False
    if path0.startswith('r'):
        try:
            int(path0[1:])
        except ValueError:
            pass
        else:
            first_segment = True
    # Let's be smart here and except old or missing revision segments alike:
    # /static/{r1234oldrev}/foo/bar   --> /static/{r5678newrev}/foo/bar
    # /static/foo/bar                 --> /static/{r5678newrev}/foo/bar
    if first_segment:
        path = path[1:]
    # Do the redirect
    url = get_static_url(request) + '/' + '/'.join(path);
    return HTTPFound(location=url)

