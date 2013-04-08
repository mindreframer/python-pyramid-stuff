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

import calendar 
import datetime  
import time
from karl.content.calendar.presenters.base import BasePresenter
from karl.content.calendar.presenters.base import BaseEvent
from karl.content.calendar.utils import next_month
from karl.content.calendar.utils import prior_month


class DayEventHorizon(BasePresenter):
    @property
    def first_moment(self):
        return datetime.datetime(self.focus_datetime.year, 
                                 self.focus_datetime.month, 
                                 self.focus_datetime.day, 
                                 0, 0, 0)
    
    @property
    def last_moment(self):
        return datetime.datetime(self.focus_datetime.year, 
                                 self.focus_datetime.month, 
                                 self.focus_datetime.day, 
                                 23, 59, 59)


class DayViewPresenter(DayEventHorizon):
    name = 'day'
    
    def _initialize(self):
        self._init_title()
        self.feed_url = self.url_for('atom.xml')  

        self._init_prev_datetime()
        self._init_next_datetime()
        self._init_navigation()
        
        self._init_hour_labels()
        self._init_time_slots()
        self._init_add_event_url()

    def _init_title(self):
        day_num = calendar.weekday(self.focus_datetime.year,
                                   self.focus_datetime.month,
                                   self.focus_datetime.day)
        day_name = calendar.day_name[day_num]                                   

        self.title = "%d/%d/%d" % ( self.focus_datetime.month,
                                   self.focus_datetime.day,
                                   self.focus_datetime.year)

        self.title_year = self.focus_datetime.year

    def _init_prev_datetime(self):
        minus_one  = self.focus_datetime.day - 1
        
        if (minus_one < 1):
            year, month = prior_month(self.focus_datetime.year,
                                      self.focus_datetime.month) 
            day = calendar.monthrange(year, month)[1]                                       
        else:
            year  = self.focus_datetime.year
            month = self.focus_datetime.month
            day   = minus_one

        self.prev_datetime = datetime.datetime(year, month, day)
 
    def _init_next_datetime(self):
        last_day = calendar.monthrange(self.focus_datetime.year,
                                       self.focus_datetime.month)[1]

        plus_one = self.focus_datetime.day + 1
        
        if (plus_one > last_day):
            year, month = next_month(self.focus_datetime.year,
                                     self.focus_datetime.month)
            day = 1
        else:
            year  = self.focus_datetime.year
            month = self.focus_datetime.month
            day   = plus_one

        self.next_datetime = datetime.datetime(year, month, day)            

    def _init_hour_labels(self):
        self.hour_labels = []
        for hour in range(0, 24):
            if hour == 0:
                label = '12 AM'
            elif hour == 12:
                label = '12 PM'
            elif hour < 12:
                label = '%d AM' % hour
            else:
                label = '%d PM' % (hour - 12)
            self.hour_labels.append(label)

    def _init_time_slots(self):
        self.half_hour_slots = []

        for i in range(0, 48):
           is_shaded    = (i < 16) or (i > 35)
           is_half_hour = (i % 2) != 0

           minutes_ahead  = datetime.timedelta(minutes=(i*30))
           start_datetime = self.first_moment + minutes_ahead

           # url to add an event to this time slot           
           starts = time.mktime(start_datetime.timetuple())
           add_event_url = self.url_for('add_calendarevent.html',
                            query={'starts':int(starts)})
           
           slot = TimeSlot(shaded_row=is_shaded, 
                           is_half_hour=is_half_hour,
                           start_datetime=start_datetime,
                           add_event_url=add_event_url)
           self.half_hour_slots.append(slot)

    def _init_add_event_url(self):
        day_at_9am = self.first_moment + datetime.timedelta(hours=9)
        starts = time.mktime(day_at_9am.timetuple())
        self.add_event_url = self.url_for('add_calendarevent.html',
                                query={'starts':int(starts)}) 

    def paint_events(self, events):
        all_day_events, events = self._separate_all_day_events(events)
        
        # all-day events
        self.all_day_events = []
        for catalog_event in all_day_events:
            event = EventOnDayView(self, catalog_event,
                show_url=self.url_for(context=catalog_event))            
            self.all_day_events.append(event)

        # [ [event], [event,event], ... ]
        mapping = self._map_catalog_events_to_slot_indices(events)

        for slot_index, catalog_events in enumerate(mapping):

            # We only take the first event in one slot into consideration:
            # the rest will thus start displaying in the next slot.
            # It may happen so, that there are too many events for one slot
            # consequently some events will not display at all.
            if catalog_events:

                catalog_event = catalog_events[0]

                bubble = Bubble()
                
                bubble.event = EventOnDayView(self, catalog_event,
                    show_url=self.url_for(context=catalog_event))
                
                for i in range(slot_index, len(mapping)):
                    next_in_map = mapping[i]
                    if catalog_event in next_in_map:
                         next_in_map.remove(catalog_event)
                         bubble.length += 1
                    else:
                        break

                self.half_hour_slots[slot_index].bubbles.append(bubble)        
            

    def _separate_all_day_events(self, events):
        all_day_events, other_events = [], []
        
        for event in events:
            lbound = (event.startDate <= self.first_moment)
            ubound = (event.endDate   >= self.last_moment)
            
            if lbound and ubound:
                all_day_events.append(event)
            else:
                other_events.append(event) 
        
        return (all_day_events, other_events)

    def _map_catalog_events_to_slot_indices(self, events):
        mapping = [ [] for slot in self.half_hour_slots ]

        num_slots = len(self.half_hour_slots)

        for event in events:
            index = self._find_first_slot_index_for_event(event)
            if index is None:
                continue
            
            for i in range(index, num_slots):
                mapping[i].append(event)

                if (i != num_slots-1):
                    next_slot = self.half_hour_slots[i+1]                                           
                    if event.endDate <= next_slot.start_datetime:
                        break

        return mapping

    def _find_first_slot_index_for_event(self, catalog_event):
        if catalog_event.endDate < self.first_moment:
            return None

        event_start_datetime = catalog_event.startDate
        if event_start_datetime < self.first_moment:
            event_start_datetime = self.first_moment
        
        slot_index = None
        
        for i, slot in enumerate(self.half_hour_slots):
            if slot.start_datetime > event_start_datetime:
                break
            slot_index = i
        
        return slot_index

    @property
    def auto_scroll_class(self):
        same_year  = (self.now_datetime.year  == self.focus_datetime.year)
        same_month = (self.now_datetime.month == self.focus_datetime.month)
        same_day   = (self.now_datetime.day   == self.focus_datetime.day)

        if same_year and same_month and same_day:
            css_class = 'today'
        else:
            css_class = ''

        return css_class

    @property
    def template_filename(self):
        return 'karl.content.views:templates/calendar_day.pt'


class TimeSlot(object):
    def __init__(self, shaded_row=False, is_half_hour=False,
                       start_datetime=0, add_event_url='#'):
        self.shaded_row     = shaded_row
        self.is_half_hour   = is_half_hour
        self.start_datetime = start_datetime             
        self.add_event_url  = add_event_url

        self.bubbles        = []
    
    @property
    def bubble(self):
        if self.bubbles:
            return self.bubbles[0]
        return None


class Bubble(object):
    def __init__(self, event=None):    
        self.event  = event
        self.length = 0 # half hour slots
    
    @property
    def length_px(self):
        return self.length * 25 + (self.length - 1 - 2) # 25 + (borders - padding)


class EventOnDayView(BaseEvent):
    def __init__(self, day, catalog_event, 
                 show_url='#', edit_url='#', delete_url='#'): 

        BaseEvent.__init__(self, day, catalog_event, 
                       show_url, edit_url, delete_url)         

    @property        
    def time_of_first_moment(self):
        return self.first_moment.strftime('%l:%M %p')
        

