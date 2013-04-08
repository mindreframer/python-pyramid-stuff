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
"""Views registered to multiple content types.
"""

from pyramid.url import resource_url
from pyramid.httpexceptions import HTTPFound

from karl.utils import find_community
from karl.utils import find_intranet
from karl.utils import get_layout_provider
from karl.views.api import TemplateAPI

def delete_resource_view(context, request, num_children=0):

    page_title = 'Delete ' + context.title
    api = TemplateAPI(context, request, page_title)

    confirm = request.params.get('confirm')
    if confirm:
        location = resource_url(
            context.__parent__, request,
            query=dict(status_message= 'Deleted %s' % context.title)
            )
        del context.__parent__[context.__name__]
        return HTTPFound(location=location)

    # Get a layout
    layout_provider = get_layout_provider(context, request)
    layout_name = 'generic'
    if find_intranet(context):
        layout_name = 'intranet'
    elif find_community(context):
        layout_name = 'community'
    layout = layout_provider(layout_name)

    return {'api': api,             # deprecated UX2
            'old_layout': layout,   # deprecated UX2
            'num_children': num_children,
           }

