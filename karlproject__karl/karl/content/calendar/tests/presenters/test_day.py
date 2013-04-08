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
import datetime
import time
import calendar

from pyramid import testing

import karl.testing

from karl.content.calendar.tests.presenters.test_base import DummyCatalogEvent
from karl.content.calendar.tests.presenters.test_base import dummy_url_for


class DayViewPresenterTests(unittest.TestCase):
    def setUp(self):
        calendar.setfirstweekday(calendar.SUNDAY)
        testing.setUp()
        karl.testing.registerDummyRenderer(
            'karl.content.views:templates/calendar_navigation.pt')

    def tearDown(self):
        testing.tearDown()

    def test_title_is_day_name_with_numeric_month_and_day(self):
        focus_at = datetime.datetime(2009, 8, 1) 
        now_at   = datetime.datetime.now()

        presenter = self._makeOne(focus_at, now_at, dummy_url_for)

        self.assertEqual(presenter.title, '8/1/2009')

    def test_has_a_feed_url(self):
        focus_at = datetime.datetime(2009, 8, 1) 
        now_at   = datetime.datetime.now()

        presenter = self._makeOne(focus_at, now_at, dummy_url_for)

        self.assert_(presenter.feed_url.startswith('http'))

    # first & last moment

    def test_computes_first_moment_as_beginning_of_same_day(self):
        focus_at = datetime.datetime(2009, 8, 26)
        now_at   = datetime.datetime.now()

        presenter = self._makeOne(focus_at, now_at, dummy_url_for)

        expected = datetime.datetime(2009, 8, 26)
        self.assertEqual(presenter.first_moment, expected)

    def test_computes_last_moment_as_ending_of_same_day(self):
        focus_at = datetime.datetime(2009, 8, 26)
        now_at   = datetime.datetime.now()

        presenter = self._makeOne(focus_at, now_at, dummy_url_for)

        expected = datetime.datetime(2009, 8, 26, 23, 59, 59)
        self.assertEqual(presenter.last_moment, expected)

    # add_event_url

    def test_sets_add_event_url_to_focus_day_at_9am(self):
        focus_at = datetime.datetime(2009, 8, 26)
        now_at   = datetime.datetime.now()

        presenter = self._makeOne(focus_at, now_at, dummy_url_for)

        day_at_9am = focus_at + datetime.timedelta(hours=9)
        starts = time.mktime(day_at_9am.timetuple())
        expected_url = presenter.url_for('add_calendarevent.html',
                                        query={'starts':int(starts)})
        self.assertEqual(presenter.add_event_url, expected_url)

    # css auto_scroll_class used to trigger javascript scroll effect
    
    def test_auto_scroll_class_is_today_when_now_is_in_focus(self):
        focus_at = datetime.datetime(2009, 11, 2, 0, 0, 0)
        now_at   = datetime.datetime(2009, 11, 2, 1, 2, 3)

        presenter = self._makeOne(focus_at, now_at, dummy_url_for)

        self.assertEqual(presenter.auto_scroll_class, 'today')
        
    def test_auto_scroll_class_is_empty_when_now_is_not_in_focus(self):
        focus_at = datetime.datetime(2009, 11, 2)
        now_at   = datetime.datetime(2009, 11, 3)

        presenter = self._makeOne(focus_at, now_at, dummy_url_for)

        self.assertEqual(presenter.auto_scroll_class, '')

    # prev_datetime & next_datetime
    
    def test_computes_next_datetime_within_the_same_month(self):
        focus_at = datetime.datetime(2009, 8, 30) 
        now_at   = datetime.datetime.now()

        presenter = self._makeOne(focus_at, now_at, dummy_url_for)

        self.assertEqual(presenter.next_datetime.year,  2009)
        self.assertEqual(presenter.next_datetime.month, 8)
        self.assertEqual(presenter.next_datetime.day,   31)

    def test_computes_next_datetime_into_the_next_month(self):
        focus_at = datetime.datetime(2009, 8, 31) 
        now_at   = datetime.datetime.now()

        presenter = self._makeOne(focus_at, now_at, dummy_url_for)

        self.assertEqual(presenter.next_datetime.year,  2009)
        self.assertEqual(presenter.next_datetime.month, 9)
        self.assertEqual(presenter.next_datetime.day,   1)

    def test_computes_prev_datetime_within_the_same_month(self):
        focus_at = datetime.datetime(2009, 8, 2) 
        now_at   = datetime.datetime.now()

        presenter = self._makeOne(focus_at, now_at, dummy_url_for)

        self.assertEqual(presenter.prev_datetime.year,  2009)
        self.assertEqual(presenter.prev_datetime.month, 8)
        self.assertEqual(presenter.prev_datetime.day,   1)

    def test_computes_prev_datetime_into_the_prior_month(self):
        focus_at = datetime.datetime(2009, 8, 1) 
        now_at   = datetime.datetime.now()

        presenter = self._makeOne(focus_at, now_at, dummy_url_for)

        self.assertEqual(presenter.prev_datetime.year,  2009)
        self.assertEqual(presenter.prev_datetime.month, 7)
        self.assertEqual(presenter.prev_datetime.day,   31)

    # left navigation
    
    def test_sets_navigation_today_url(self):
        focus_at = datetime.datetime(2009, 11, 1) 
        now_at   = datetime.datetime(2009, 8, 26)

        presenter = self._makeOne(focus_at, now_at, dummy_url_for)

        self.assertTrue(presenter.navigation.today_url.endswith(
            'day.html?year=2009&month=8&day=26'
        ))

    def test_sets_navigation_prev_url(self):
        focus_at = datetime.datetime(2009, 8, 1) 
        now_at   = datetime.datetime(2009, 8, 26)

        presenter = self._makeOne(focus_at, now_at, dummy_url_for)

        self.assertTrue(presenter.navigation.prev_url.endswith(
            'day.html?year=2009&month=7&day=31'
        ))

    def test_sets_navigation_next_url(self):
        focus_at = datetime.datetime(2009, 8, 1) 
        now_at   = datetime.datetime(2009, 8, 26)

        presenter = self._makeOne(focus_at, now_at, dummy_url_for)

        self.assertTrue(presenter.navigation.next_url.endswith(
            'day.html?year=2009&month=8&day=2'
        ))

    # paint_events

    def test_paints_event_of_one_hour(self):
        focus_at = datetime.datetime(2010, 2, 15)
        now_at   = datetime.datetime.now()
        
        presenter = self._makeOne(focus_at, now_at, dummy_url_for)
        event = DummyCatalogEvent(
                    title="Meeting",
                    startDate=datetime.datetime(2010, 2, 15,  13,  0,  0),
                    endDate  =datetime.datetime(2010, 2, 15,  14,  0,  0)
                )        
        presenter.paint_events([event])
        
        # search for 1pm time slot (dummy event starts at 1pm)
        for time_slot in presenter.half_hour_slots:
            if time_slot.start_datetime == event.startDate:
                break
        
        # presenters.day.TimeSlot  
        bubble_containing_event = time_slot.bubbles[0]
        self.assertEqual(bubble_containing_event.length, 2) # 2 half hours

        # presenters.day.EventOnDayView
        painted_event = bubble_containing_event.event
        self.assertEqual(painted_event.title, "Meeting")

    def test_paints_event_of_three_full_days_on_its_first_day(self):
        focus_at = datetime.datetime(2010, 2, 15)
        now_at   = datetime.datetime.now()
        
        presenter = self._makeOne(focus_at, now_at, dummy_url_for)
        event = DummyCatalogEvent(
                    title="Vacation",
                    startDate=datetime.datetime(2010, 2, 15,  0,  0,  0),
                    endDate  =datetime.datetime(2010, 2, 18,  0,  0,  0)
                )        
        presenter.paint_events([event])

        # presenters.day.EventOnDayView
        painted_event = presenter.all_day_events[0]
        self.assertEqual(painted_event.title, "Vacation")

    def test_paints_event_of_three_full_days_on_its_second_day(self):
        focus_at = datetime.datetime(2010, 2, 16)
        now_at   = datetime.datetime.now()
        
        presenter = self._makeOne(focus_at, now_at, dummy_url_for)
        event = DummyCatalogEvent(
                    title="Vacation",
                    startDate=datetime.datetime(2010, 2, 15,  0,  0,  0),
                    endDate  =datetime.datetime(2010, 2, 18,  0,  0,  0)
                )        
        presenter.paint_events([event])

        # presenters.day.EventOnDayView
        painted_event = presenter.all_day_events[0]
        self.assertEqual(painted_event.title, "Vacation")

    def test_paints_event_of_three_full_days_on_its_last_day(self):
        focus_at = datetime.datetime(2010, 2, 17)
        now_at   = datetime.datetime.now()
        
        presenter = self._makeOne(focus_at, now_at, dummy_url_for)
        event = DummyCatalogEvent(
                    title="Vacation",
                    startDate=datetime.datetime(2010, 2, 15,  0,  0,  0),
                    endDate  =datetime.datetime(2010, 2, 18,  0,  0,  0)
                )        
        presenter.paint_events([event])

        # presenters.day.EventOnDayView
        painted_event = presenter.all_day_events[0]
        self.assertEqual(painted_event.title, "Vacation")

    def test_paints_event_of_three_full_days_stays_within_bounds(self):
        focus_at = datetime.datetime(2010, 2, 18) # out of bounds
        now_at   = datetime.datetime.now()
        
        presenter = self._makeOne(focus_at, now_at, dummy_url_for)
        event = DummyCatalogEvent(
                    title="Vacation",
                    startDate=datetime.datetime(2010, 2, 15,  0,  0,  0),
                    endDate  =datetime.datetime(2010, 2, 18,  0,  0,  0)
                )        
        presenter.paint_events([event])

        self.assertEqual(len(presenter.all_day_events), 0)

    def test_paints_event_of_three_days_with_partial_days_first_day(self):
        focus_at = datetime.datetime(2010, 2, 15)
        now_at   = datetime.datetime.now()
        
        presenter = self._makeOne(focus_at, now_at, dummy_url_for)
        event = DummyCatalogEvent(
                    title="Travel",
                    startDate=datetime.datetime(2010, 2, 15, 13,  0,  0),
                    endDate  =datetime.datetime(2010, 2, 17, 16,  0,  0)
                )        
        presenter.paint_events([event])

        self.assertEqual(len(presenter.all_day_events), 0)

        # search for 1pm time slot (dummy event starts at 1pm)
        for time_slot in presenter.half_hour_slots:
            if time_slot.start_datetime == event.startDate:
                break

        # presenters.day.TimeSlot  
        bubble_containing_event = time_slot.bubbles[0]
        self.assertEqual(bubble_containing_event.length, 22) # 22 half hours

        # presenters.day.EventOnDayView
        painted_event = bubble_containing_event.event
        self.assertEqual(painted_event.title, "Travel")

    def test_paints_event_of_three_days_with_partial_days_second_day(self):
        focus_at = datetime.datetime(2010, 2, 16)
        now_at   = datetime.datetime.now()
        
        presenter = self._makeOne(focus_at, now_at, dummy_url_for)
        event = DummyCatalogEvent(
                    title="Travel",
                    startDate=datetime.datetime(2010, 2, 15, 13,  0,  0),
                    endDate  =datetime.datetime(2010, 2, 17, 16,  0,  0)
                )        
        presenter.paint_events([event])

        # presenters.day.EventOnDayView
        painted_event = presenter.all_day_events[0]
        self.assertEqual(painted_event.title, "Travel")

    def test_paints_event_of_three_days_with_partial_days_last_day(self):
        focus_at = datetime.datetime(2010, 2, 17)
        now_at   = datetime.datetime.now()
        
        presenter = self._makeOne(focus_at, now_at, dummy_url_for)
        event = DummyCatalogEvent(
                    title="Travel",
                    startDate=datetime.datetime(2010, 2, 15, 13,  0,  0),
                    endDate  =datetime.datetime(2010, 2, 17, 16,  0,  0)
                )        
        presenter.paint_events([event])

        self.assertEqual(len(presenter.all_day_events), 0)

        # time slot is 12am (dummy event on this day is 12am-4pm)
        time_slot = presenter.half_hour_slots[0]

        # presenters.day.TimeSlot  
        bubble_containing_event = time_slot.bubbles[0]
        self.assertEqual(bubble_containing_event.length, 32) # 32 half hours

        # presenters.day.EventOnDayView
        painted_event = bubble_containing_event.event
        self.assertEqual(painted_event.title, "Travel")
    
    def test_paint_events_separates_all_day_events_from_others(self):
        focus_at = datetime.datetime(2009, 9, 14) 
        now_at   = datetime.datetime(2009, 8, 26)

        presenter = self._makeOne(focus_at, now_at, dummy_url_for)

        all_day_catalog_event = DummyCatalogEvent(
                    startDate=datetime.datetime(2009, 9, 14,  0,  0,  0),
                    endDate  =datetime.datetime(2009, 9, 15,  0,  0,  0),
                    title    ='all-day-event'
                )
        other_catalog_event = DummyCatalogEvent(
                    startDate=datetime.datetime(2009, 9, 14,  1,  0,  0),
                    endDate  =datetime.datetime(2009, 9, 14,  2,  0,  0),
                    title    ='other-event'
                )
        presenter.paint_events([all_day_catalog_event, other_catalog_event])

        self.assertEqual(len(presenter.all_day_events), 1)
        self.assertEqual(presenter.all_day_events[0].title, 'all-day-event')

    def test_paint_events_wraps_all_day_event_and_assigns_show_url(self):
        focus_at = datetime.datetime(2009, 9, 14) 
        now_at   = datetime.datetime(2009, 8, 26)

        presenter = self._makeOne(focus_at, now_at, dummy_url_for)

        all_day_catalog_event = DummyCatalogEvent(
                    startDate=datetime.datetime(2009, 9, 14,  0,  0,  0),
                    endDate  =datetime.datetime(2009, 9, 15,  0,  0,  0),
                    title    ='all-day-event'
                )
        presenter.paint_events([all_day_catalog_event])

        self.assertEqual(len(presenter.all_day_events), 1)
        self.assert_(presenter.all_day_events[0].show_url.startswith('http'))

    def test_painting_an_all_day_event_does_not_bleed_into_prior_day(self):
        focus_at = datetime.datetime(2010, 2, 13) # prior day
        now_at   = datetime.datetime.now()

        presenter = self._makeOne(focus_at, now_at, dummy_url_for)

        all_day_catalog_event = DummyCatalogEvent(
                    startDate=datetime.datetime(2009, 9, 14,  0,  0,  0),
                    endDate  =datetime.datetime(2009, 9, 15,  0,  0,  0),
                    title    ='all-day-event'
                )
        presenter.paint_events([all_day_catalog_event])

        self.assertEqual(len(presenter.all_day_events), 0)
        self.assertEqual(len(presenter.half_hour_slots[47].bubbles), 0)

    def test_painting_an_all_day_event_does_not_bleed_into_next_day(self):
        focus_at = datetime.datetime(2010, 2, 15) # next day
        now_at   = datetime.datetime.now()

        presenter = self._makeOne(focus_at, now_at, dummy_url_for)

        all_day_catalog_event = DummyCatalogEvent(
                    startDate=datetime.datetime(2009, 9, 14,  0,  0,  0),
                    endDate  =datetime.datetime(2009, 9, 15,  0,  0,  0),
                    title    ='all-day-event'
                )
        presenter.paint_events([all_day_catalog_event])

        self.assertEqual(len(presenter.all_day_events), 0)
        self.assertEqual(len(presenter.half_hour_slots[0].bubbles), 0)

    # time slots

    def test_builds_48_half_hour_slots(self):
        focus_at = datetime.datetime(2009, 8, 1) 
        now_at   = datetime.datetime(2009, 8, 26)

        presenter = self._makeOne(focus_at, now_at, dummy_url_for)

        self.assertEqual(48, len(presenter.half_hour_slots))

    def test_assigns_start_datetime_to_each_half_hour_slot(self):
        focus_at = datetime.datetime(2009, 8, 1) 
        now_at   = datetime.datetime(2009, 8, 26)

        presenter = self._makeOne(focus_at, now_at, dummy_url_for)
        
        half_hour_slots = presenter.half_hour_slots

        self.assertEqual(half_hour_slots[0].start_datetime, 
                         datetime.datetime(2009, 8, 1, 0, 0, 0))   # 12:00am
        
        self.assertEqual(half_hour_slots[-1].start_datetime,
                         datetime.datetime(2009, 8, 1, 23, 30, 0)) # 11:30pm

    def test_assigns_add_event_url_to_each_half_hour_slot(self):
        focus_at = datetime.datetime(2009, 11, 17) 
        now_at   = datetime.datetime(2009, 11, 17)

        presenter = self._makeOne(focus_at, now_at, dummy_url_for)
        
        half_hour_slot = presenter.half_hour_slots[0]
        
        starts = time.mktime(half_hour_slot.start_datetime.timetuple())
        expected_url = presenter.url_for('add_calendarevent.html',
                                            query={'starts':int(starts)})

        self.assertEqual(half_hour_slot.add_event_url, expected_url)

    # _find_starting_slot_for_event
    
    def test_find_starting_slot_index_finds_first_slot(self):
        focus_at = datetime.datetime(2009, 8, 1) 
        now_at   = datetime.datetime(2009, 8, 26)

        presenter = self._makeOne(focus_at, now_at, dummy_url_for)
                   
        event = DummyCatalogEvent(
                    startDate=datetime.datetime(2009, 8, 1, 0,  0, 0),
                    endDate  =datetime.datetime(2009, 8, 1, 0, 10, 0)
                )

        index = presenter._find_first_slot_index_for_event(event)
        self.assertEqual(index, 0)

    def test_find_starting_slot_index_finds_last_slot(self):
        focus_at = datetime.datetime(2009, 8, 1) 
        now_at   = datetime.datetime(2009, 8, 26)

        presenter = self._makeOne(focus_at, now_at, dummy_url_for)
                   
        event = DummyCatalogEvent(
                    startDate=datetime.datetime(2009, 8, 1, 23, 30, 0),
                    endDate  =datetime.datetime(2009, 8, 1, 23, 31, 0)
                )

        index = presenter._find_first_slot_index_for_event(event)
        self.assertEqual(index, 47)

    def test_find_starting_slot_index_aligns_down_to_nearest_half_hour(self):
        focus_at = datetime.datetime(2009, 8, 1) 
        now_at   = datetime.datetime(2009, 8, 26)

        presenter = self._makeOne(focus_at, now_at, dummy_url_for)
                   
        event = DummyCatalogEvent(
                    startDate=datetime.datetime(2009, 8, 1, 1, 13, 0),
                    endDate  =datetime.datetime(2009, 8, 1, 1, 14, 0)
                )
        
        index = presenter._find_first_slot_index_for_event(event)
        self.assertEqual(index, 2)
    
    def test_find_starting_slot_index_does_not_exceed_event_start_time(self):
        focus_at = datetime.datetime(2009, 8, 1) 
        now_at   = datetime.datetime(2009, 8, 26)

        presenter = self._makeOne(focus_at, now_at, dummy_url_for)
                   
        event = DummyCatalogEvent(
                    startDate=datetime.datetime(2009, 8, 1, 0, 57, 0),
                    endDate  =datetime.datetime(2009, 8, 1, 0, 58, 0)
                )
        
        index = presenter._find_first_slot_index_for_event(event)
        self.assertEqual(index, 1)

    def test_find_starting_slot_index_coeres_start_date_too_early(self):
        focus_at = datetime.datetime(2009, 8, 1) 
        now_at   = datetime.datetime(2009, 8, 26)

        presenter = self._makeOne(focus_at, now_at, dummy_url_for)
                   
        event = DummyCatalogEvent(
                    startDate=datetime.datetime(2009, 7, 25, 0, 0, 0),
                    endDate  =datetime.datetime(2009, 8, 1, 10, 0, 0)
                )
        index = presenter._find_first_slot_index_for_event(event)
        self.assertEqual(index, 0)
        
    def test_find_starting_slot_index_None_if_event_ends_before_day(self):
        focus_at = datetime.datetime(2009, 8, 1) 
        now_at   = datetime.datetime(2009, 8, 26)

        presenter = self._makeOne(focus_at, now_at, dummy_url_for)
                   
        event = DummyCatalogEvent(
                    startDate=datetime.datetime(2009, 7, 25,  0, 0, 0),
                    endDate  =datetime.datetime(2009, 7, 25, 10, 0, 0)
                )
        index = presenter._find_first_slot_index_for_event(event)
        self.assert_(index is None)

    # _map_catalog_events_to_slot_indices
    
    def test_map_catalog_events_to_slot_indices_spans_slots(self):
        focus_at = datetime.datetime(2009, 8, 1) 
        now_at   = datetime.datetime(2009, 8, 26)

        presenter = self._makeOne(focus_at, now_at, dummy_url_for)
        
        event = DummyCatalogEvent(
                    startDate=datetime.datetime(2009, 8, 1, 0, 0,  0),
                    endDate  =datetime.datetime(2009, 8, 1, 0, 35, 0) 
                )
        events = [ event ]
                                                                      
        mapping = presenter._map_catalog_events_to_slot_indices(events)                                                                      
        self.assertEqual(mapping[0], [event])
        self.assertEqual(mapping[1], [event])
        self.assertEqual(mapping[2], [])

    def test_map_catalog_events_to_slot_stacks_events_in_a_slot(self):
        focus_at = datetime.datetime(2009, 8, 1) 
        now_at   = datetime.datetime(2009, 8, 26)

        presenter = self._makeOne(focus_at, now_at, dummy_url_for)
        
        event_1 = DummyCatalogEvent(
                    startDate=datetime.datetime(2009, 8, 1, 0, 0,  0),
                    endDate  =datetime.datetime(2009, 8, 1, 0, 35, 0) 
                  )
        event_2 = DummyCatalogEvent(
                    startDate=datetime.datetime(2009, 8, 1, 0, 0,  0),
                    endDate  =datetime.datetime(2009, 8, 1, 0, 35, 0) 
                  )
        events = [ event_1, event_2 ]
                                                                      
        mapping = presenter._map_catalog_events_to_slot_indices(events)                                                                      
        self.assert_(event_1 in mapping[0])
        self.assert_(event_2 in mapping[0])
        self.assert_(event_1 in mapping[1])
        self.assert_(event_2 in mapping[1])
        self.assertEqual(mapping[2], [])

    def test_map_catalog_events_maps_into_last_slot(self):
        focus_at = datetime.datetime(2009, 8, 1) 
        now_at   = datetime.datetime(2009, 8, 26)

        presenter = self._makeOne(focus_at, now_at, dummy_url_for)
        
        event = DummyCatalogEvent(
                    startDate=datetime.datetime(2009, 8, 1, 23,  0,  0),
                    endDate  =datetime.datetime(2009, 8, 1, 23, 45, 0) 
                )
        events = [ event ]
                                                                      
        mapping = presenter._map_catalog_events_to_slot_indices(events)                                                                      
        self.assertEqual(mapping[46], [event])
        self.assertEqual(mapping[47], [event])

    # helpers

    def _makeOne(self, *args, **kargs):
        from karl.content.calendar.presenters.day import DayViewPresenter
        return DayViewPresenter(*args, **kargs)


class TimeSlotTests(unittest.TestCase):
    # add_event_url
    
    def test_add_event_url_defaults_to_pound(self):
        time_slot = self._makeOne()
        self.assertEqual(time_slot.add_event_url, '#')
    
    def test_add_event_url_can_be_set(self):
        time_slot = self._makeOne(add_event_url='http://foo')
        self.assertEqual(time_slot.add_event_url, 'http://foo')

    # helpers

    def _makeOne(self, *args, **kargs):
        from karl.content.calendar.presenters.day import TimeSlot
        return TimeSlot(*args, **kargs)
