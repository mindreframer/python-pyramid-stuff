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

from karl.content.calendar.tests.presenters.test_base import dummy_url_for
from karl.content.calendar.tests.presenters.test_base import DummyCatalogEvent


class MonthViewPresenterTests(unittest.TestCase):
    def setUp(self):
        calendar.setfirstweekday(calendar.SUNDAY)
        testing.setUp()
        karl.testing.registerDummyRenderer(
            'karl.content.views:templates/calendar_navigation.pt')

    def tearDown(self):
        testing.tearDown()

    def test_has_a_name_of_month(self):
        focus_at = datetime.datetime(2009, 8, 26)
        now_at   = datetime.datetime.now() 

        presenter = self._makeOne(focus_at, now_at, dummy_url_for)
        self.assertEqual(presenter.name, 'month') 

    def test_title_is_month_name_and_year(self):
        focus_at = datetime.datetime(2009, 8, 26)
        now_at   = datetime.datetime.now()

        presenter = self._makeOne(focus_at, now_at, dummy_url_for)
        self.assertEqual(presenter.title, 'August 2009')

    def test_has_feed_url(self):
        focus_at = datetime.datetime(2009, 8, 26)
        now_at   = datetime.datetime.now()

        presenter = self._makeOne(focus_at, now_at, dummy_url_for)
        self.assertTrue(presenter.feed_url.endswith('atom.xml'))

    # first & last moment

    def test_computes_first_moment_into_prior_month(self):
        focus_at = datetime.datetime(2009, 8, 26)
        now_at   = datetime.datetime.now()

        presenter = self._makeOne(focus_at, now_at, dummy_url_for)

        expected = datetime.datetime(2009, 07, 26)
        self.assertEqual(presenter.first_moment, expected)

    def test_computes_last_moment_into_next_month(self):
        focus_at = datetime.datetime(2009, 8, 26)
        now_at   = datetime.datetime.now()

        presenter = self._makeOne(focus_at, now_at, dummy_url_for)

        expected = datetime.datetime(2009, 9, 5, 23, 59, 59)
        self.assertEqual(presenter.last_moment, expected)

    # prev_datetime & next_datetime 
    
    def test_computes_prev_datetime_preserving_day_if_in_range(self):
        focus_at = datetime.datetime(2009, 8, 31)
        now_at   = datetime.datetime.now()

        presenter = self._makeOne(focus_at, now_at, dummy_url_for)

        self.assertEqual(presenter.prev_datetime.year, 2009)
        self.assertEqual(presenter.prev_datetime.month, 7)
        self.assertEqual(presenter.prev_datetime.day, 31)
        
    def test_computes_prev_datetime_adjusting_out_of_range_day(self):
        focus_at = datetime.datetime(2009, 7, 31) # 31 not in june
        now_at   = datetime.datetime.now()

        presenter = self._makeOne(focus_at, now_at, dummy_url_for)

        self.assertEqual(presenter.prev_datetime.year, 2009)
        self.assertEqual(presenter.prev_datetime.month, 6)
        self.assertEqual(presenter.prev_datetime.day, 30) # adjusted

    def test_computes_next_datetime_preserving_day_if_in_range(self):
        focus_at = datetime.datetime(2009, 7, 31) 
        now_at   = datetime.datetime.now()

        presenter = self._makeOne(focus_at, now_at, dummy_url_for)

        self.assertEqual(presenter.next_datetime.year, 2009)
        self.assertEqual(presenter.next_datetime.month, 8)
        self.assertEqual(presenter.next_datetime.day, 31) 

    def test_computes_next_datetime_adjusting_out_of_range_day(self):
        focus_at = datetime.datetime(2009, 8, 31) # 31 not in september
        now_at   = datetime.datetime.now()

        presenter = self._makeOne(focus_at, now_at, dummy_url_for)

        self.assertEqual(presenter.next_datetime.year, 2009)
        self.assertEqual(presenter.next_datetime.month, 9)
        self.assertEqual(presenter.next_datetime.day, 30) # adjusted

    # left navigation
    
    def test_sets_navigation_today_url(self):
        focus_at = datetime.datetime(2009, 11, 1) 
        now_at   = datetime.datetime(2009, 8, 26)

        presenter = self._makeOne(focus_at, now_at, dummy_url_for)

        self.assertTrue(presenter.navigation.today_url.endswith(
            'month.html?year=2009&month=8&day=26'
        ))

    def test_sets_navigation_prev_url(self):
        focus_at = datetime.datetime(2009, 8, 1) 
        now_at   = datetime.datetime(2009, 8, 26)

        presenter = self._makeOne(focus_at, now_at, dummy_url_for)

        self.assertTrue(presenter.navigation.prev_url.endswith(
            'month.html?year=2009&month=7&day=1'
        ))

    def test_sets_navigation_next_url(self):
        focus_at = datetime.datetime(2009, 8, 1) 
        now_at   = datetime.datetime(2009, 8, 26)

        presenter = self._makeOne(focus_at, now_at, dummy_url_for)

        self.assertTrue(presenter.navigation.next_url.endswith(
            'month.html?year=2009&month=9&day=1'
        ))

    # canvas

    def test_sets_day_headings_for_template_to_show_above_calendar(self):
        focus_at = datetime.datetime(2009, 8, 26)
        now_at   = datetime.datetime.now()

        presenter = self._makeOne(focus_at, now_at, dummy_url_for)
        self.assertEqual(len(presenter.day_headings), 7)
        
        sunday = calendar.day_name[ calendar.firstweekday() ]
        self.assertEqual(presenter.day_headings[0], sunday)

    def test_has_weeks_where_each_week_is_a_list_of_days(self):
        focus_at = datetime.datetime(2009, 8, 1) 
        now_at   = datetime.datetime(2009, 8, 26)

        presenter = self._makeOne(focus_at, now_at, dummy_url_for)
        
        weeks = presenter.weeks
        self.assertEqual(weeks[0][0].month,  7)  # sun jul 26
        self.assertEqual(weeks[0][0].day,   26)
        self.assertEqual(weeks[5][6].month,  9)  # sat sep 5
        self.assertEqual(weeks[5][6].day,    5)
    
    def test_each_day_of_the_week_is_initialized_to_no_events(self):
        focus_at = datetime.datetime(2009, 8, 1) 
        now_at   = datetime.datetime(2009, 8, 26)

        presenter = self._makeOne(focus_at, now_at, dummy_url_for)
        
        for week in presenter.weeks:
            for day in week:
                self.assertEqual(day.events, [])

    def test_each_day_of_week_is_given_an_add_event_url(self):
        focus_at = datetime.datetime(2009, 8, 1) 
        now_at   = datetime.datetime(2009, 8, 26)

        presenter = self._makeOne(focus_at, now_at, dummy_url_for)

        for week in presenter.weeks:
            for day in week:
                dt = datetime.datetime(day.year, day.month, day.day)
                day_at_9am = dt + datetime.timedelta(hours=9)
                starts = time.mktime(day_at_9am.timetuple())
                expected_url = presenter.url_for('add_calendarevent.html',
                                                query={'starts':int(starts)})
                self.assertEqual(day.add_event_url, expected_url)

    def test_each_day_of_week_is_given_a_show_day_url(self):
        focus_at = datetime.datetime(2009, 8, 1) 
        now_at   = datetime.datetime(2009, 8, 26)

        presenter = self._makeOne(focus_at, now_at, dummy_url_for)

        for week in presenter.weeks:
            for day in week:
                format = '%s?year=%d&month=%d&day=%d'
                url = format % (presenter.url_for('day.html'),
                                day.year, day.month, day.day)   
                self.assertEqual(day.show_day_url, url)

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

        # find day of Feb 15 when dummy event starts
        week_of_feb_14 = presenter.weeks[2] 
        feb_15         = week_of_feb_14[1]    

        # presenters.month.EventOnMonthView
        painted_event  = feb_15.event_slots[0]
        self.assertEqual(painted_event.title, "Meeting")
        self.assertFalse(painted_event.bubbled)

    def test_paints_event_of_three_full_days(self):
        focus_at = datetime.datetime(2010, 2, 15)
        now_at   = datetime.datetime.now()
        
        presenter = self._makeOne(focus_at, now_at, dummy_url_for)
        event = DummyCatalogEvent(
                    title="Vacation",
                    startDate=datetime.datetime(2010, 2, 15,  0,  0,  0),
                    endDate  =datetime.datetime(2010, 2, 18,  0,  0,  0)
                )        
        presenter.paint_events([event])

        # find days of Feb 15, 16, 17 
        week_of_feb_14 = presenter.weeks[2] 
        feb_15         = week_of_feb_14[1] # dummy event on feb 15  
        feb_16         = week_of_feb_14[2] #   continues through feb 16    
        feb_17         = week_of_feb_14[3] #   and through feb 17    

        # presenters.month.EventOnMonthView
        painted_event = feb_15.event_slots[0]
        self.assertEqual(painted_event.title, "Vacation")
        self.assertTrue(painted_event.bubbled)
        self.assertEqual(painted_event.rounding_class, "left")

        painted_event = feb_16.event_slots[0]
        self.assertEqual(painted_event.title, "Vacation")
        self.assertTrue(painted_event.bubbled)
        self.assertEqual(painted_event.rounding_class, "center")

        painted_event = feb_17.event_slots[0]
        self.assertEqual(painted_event.title, "Vacation")
        self.assertTrue(painted_event.bubbled)
        self.assertEqual(painted_event.rounding_class, "right")

    def test_paints_event_of_three_days_with_partial_days_on_ends(self):
        focus_at = datetime.datetime(2010, 2, 15)
        now_at   = datetime.datetime.now()
        
        presenter = self._makeOne(focus_at, now_at, dummy_url_for)
        event = DummyCatalogEvent(
                    title="Travel",
                    startDate=datetime.datetime(2010, 2, 15, 13,  0,  0),
                    endDate  =datetime.datetime(2010, 2, 17, 16,  0,  0)
                )        
        presenter.paint_events([event])

        # find days of Feb 15, 16, 17 
        week_of_feb_14 = presenter.weeks[2] 
        feb_15         = week_of_feb_14[1] # dummy event on feb 15 @ 1pm 
        feb_16         = week_of_feb_14[2] #   continues through feb 16    
        feb_17         = week_of_feb_14[3] #   and until feb 17  @ 4pm  

        # presenters.month.EventOnMonthView
        painted_event = feb_15.event_slots[0]
        self.assertEqual(painted_event.title, "Travel")
        self.assertTrue(painted_event.bubbled)
        self.assertEqual(painted_event.rounding_class, "left")

        painted_event = feb_16.event_slots[0]
        self.assertEqual(painted_event.title, "Travel")
        self.assertTrue(painted_event.bubbled)
        self.assertEqual(painted_event.rounding_class, "center")

        painted_event = feb_17.event_slots[0]
        self.assertEqual(painted_event.title, "Travel")
        self.assertTrue(painted_event.bubbled)
        self.assertEqual(painted_event.rounding_class, "right")

    def test_paints_a_complex_combination_of_events_correctly(self):
       focus_at = datetime.datetime(2010, 2, 15)
       now_at   = datetime.datetime.now()
       
       presenter = self._makeOne(focus_at, now_at, dummy_url_for)
       single_day_16 = DummyCatalogEvent(
                   title="Single Day on 16",
                   startDate=datetime.datetime(2010, 2, 16, 13,  0,  0),
                   endDate  =datetime.datetime(2010, 2, 16, 13, 30,  0)
               )        
       all_day_15_16 = DummyCatalogEvent(
                   title="All-Day on 15 & 16",
                   startDate=datetime.datetime(2010, 2, 15, 0,  0,  0),
                   endDate  =datetime.datetime(2010, 2, 17, 0,  0,  0)
               )        
       multi_day_17_19 = DummyCatalogEvent(
                   title="Multi-Day",
                   startDate=datetime.datetime(2010, 2, 17, 15, 15,  0),
                   endDate  =datetime.datetime(2010, 2, 19, 16, 15,  0)
               )        
       all_day_16_17 = DummyCatalogEvent(
                   title="All-Day on 16 & 17",
                   startDate=datetime.datetime(2010, 2, 16, 0,  0,  0),
                   endDate  =datetime.datetime(2010, 2, 18, 0,  0,  0)
               )        
       presenter.paint_events(
           [single_day_16, all_day_15_16, multi_day_17_19, all_day_16_17]
       )

       week_of_feb_14 = presenter.weeks[2] 
       feb_15         = week_of_feb_14[1] 
       feb_16         = week_of_feb_14[2] 
       feb_17         = week_of_feb_14[3] 
       feb_18         = week_of_feb_14[4] 
       feb_19         = week_of_feb_14[5]

       # all-day event on 15 and 16
       for day in (feb_15, feb_16):
           painted_event = day.event_slots[0]
           self.assertEqual(painted_event.title, all_day_15_16.title)
           self.assertTrue(painted_event.bubbled)

       # all-day event on 16 and 17
       for day in (feb_16, feb_17):
           painted_event = day.event_slots[1]
           self.assertEqual(painted_event.title, all_day_16_17.title)
           self.assertTrue(painted_event.bubbled)

       # single day event on feb 16
       painted_event = feb_16.event_slots[2]
       self.assertEqual(painted_event.title, single_day_16.title)
       self.assertFalse(painted_event.bubbled)
       
       # event spanning feb 17-19, starts middle of 17 and ends middle of 19
       for day in (feb_17, feb_18, feb_18):
           painted_event = day.event_slots[0]
           self.assertEqual(painted_event.title, multi_day_17_19.title)
           self.assertTrue(painted_event.bubbled)

    def test_painting_an_event_out_of_range_ignores_the_event(self):
        focus_at = datetime.datetime(2008, 1, 3)
        now_at   = datetime.datetime.now()
        
        presenter = self._makeOne(focus_at, now_at, dummy_url_for)
        out_of_range_event = DummyCatalogEvent(
                    title="Out of Range of Calendar",
                    startDate=datetime.datetime(2010, 1, 5, 11, 15,  0),
                    endDate  =datetime.datetime(2010, 1, 6, 12, 15,  0)
                )        
        presenter.paint_events([out_of_range_event])
        
        for week in presenter.weeks:
            for day in week:
                for slot in day.event_slots:
                    self.assert_(slot is None) 

    # helpers

    def _makeOne(self, *args, **kargs):
        from karl.content.calendar.presenters.month import MonthViewPresenter
        return MonthViewPresenter(*args, **kargs)


class DayOnMonthViewTests(unittest.TestCase):

    # year, month, day

    def test_assigns_year_month_day(self):
        day = self._makeOne(2009, 9, 5)
        self.assertEqual(day.year,  2009)
        self.assertEqual(day.month, 9)
        self.assertEqual(day.day,   5)

    # current_month

    def test_current_month_defaults_to_True(self):
        day = self._makeOne(2009, 9, 5)
        self.assertTrue(day.current_month)

    def test_assigns_current_month(self):
        day = self._makeOne(2009, 9, 5, current_month=True)
        self.assertTrue(day.current_month)

    # current_day

    def test_current_day_defaults_to_True(self):
        day = self._makeOne(2009, 9, 5)
        self.assertFalse(day.current_day)

    def test_assigns_current_day(self):
        day = self._makeOne(2009, 9, 5, current_day=True)
        self.assertTrue(day.current_month)

    # add_event_url

    def test_add_event_url_defaults_to_pound(self):
        day = self._makeOne(2009, 9, 5)
        self.assertEqual(day.add_event_url, '#')

    def test_assigns_add_event_url(self):
        url = 'http://somewhere'
        day = self._makeOne(2009, 9, 5, add_event_url=url)
        self.assertEqual(day.add_event_url, url)

    # show_day_url

    def test_show_day_url_defaults_to_pound(self):
        day = self._makeOne(2009, 9, 5)
        self.assertEqual(day.show_day_url, '#')

    def test_assigns_show_day_url_url(self):
        url = 'http://somewhere'
        day = self._makeOne(2009, 9, 5, show_day_url=url)
        self.assertEqual(day.show_day_url, url)

    # events

    def test_assigns_events(self):
        dummy_event = self

        day = self._makeOne(2009, 9, 5)
        day.event_slots[0] = dummy_event
        day.event_slots[1] = dummy_event

        events = [dummy_event, dummy_event]
        self.assertEqual(day.events, events)

    # first and last moment
    
    def test_first_moment_is_beginning_of_day(self):
        day = self._makeOne(2009, 9, 5)         
        expected = datetime.datetime(2009, 9, 5, 0, 0, 0)
        self.assertEqual(day.first_moment, expected)

    def test_first_moment_is_ending_of_day(self):
        day = self._makeOne(2009, 9, 5)         
        expected = datetime.datetime(2009, 9, 5, 23, 59, 59)
        self.assertEqual(day.last_moment, expected)

    # helpers

    def _makeOne(self, *args, **kargs):
        from karl.content.calendar.presenters.month import DayOnMonthView
        return DayOnMonthView(*args, **kargs)
