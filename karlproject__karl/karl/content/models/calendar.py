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

from persistent import Persistent
from repoze.lemonade.content import create_content

from repoze.folder import Folder
from pyramid.traversal import resource_path

from zope.interface import implements

from karl.content.interfaces import ICalendar
from karl.content.interfaces import ICalendarLayer
from karl.content.interfaces import ICalendarCategory
from karl.content.interfaces import ICalendarEvent

from karl.content.models.attachments import AttachmentsFolder

from karl.models.tool import ToolFactory
from karl.models.interfaces import IToolFactory

class Calendar(Folder):
    implements(ICalendar)
    title = u'Calendar'

class CalendarCategory(Persistent):
    implements(ICalendarCategory)

    def __init__(self, title):
        self.title = title

class CalendarLayer(Persistent):
    implements(ICalendarLayer)

    def __init__(self, title, color, paths=()):
        self.title = title
        self.color = color
        self.paths = paths

class CalendarEvent(Folder):
    implements(ICalendarEvent)
    modified_by = None
    calendar_category = u''

    def __init__(self, title, startDate, endDate, creator,
                 text=u'', location=u'', attendees=[],
                 contact_name = u'', contact_email = u'',
                 calendar_category=u''):
        Folder.__init__(self)
        self.title = unicode(title)
        self.startDate = startDate
        self.endDate = endDate
        self.location = location
        self.attendees = attendees
        self.contact_name = contact_name
        self.contact_email = contact_email
        self.creator = unicode(creator)
        self.modified_by = self.creator
        if text is None:
            self.text = u''
        else:
            self.text = unicode(text)
        self.calendar_category = calendar_category
        self['attachments'] = AttachmentsFolder()


class CalendarToolFactory(ToolFactory):
    implements(IToolFactory)
    name = 'calendar'
    interfaces = (ICalendar, ICalendarEvent)
    def add(self, context, request):
        default_category_name = ICalendarCategory.getTaggedValue('default_name')
        default_layer_name = ICalendarLayer.getTaggedValue('default_name')

        calendar = create_content(ICalendar)
        context['calendar'] = calendar
        calendar = context['calendar']
        default_category = create_content(ICalendarCategory, 'Default')
        calendar[default_category_name] = default_category
        local_layer = create_content(ICalendarLayer,
                                     "This Calendar's Events Only",' blue',
                                     [resource_path(default_category)])
        calendar[default_layer_name] = local_layer

    def remove(self, context, request):
        del context['calendar']

calendar_tool_factory = CalendarToolFactory()
