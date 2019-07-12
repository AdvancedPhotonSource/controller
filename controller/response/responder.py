#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
responder receives event in update function, and runs corresponding adjusters.
"""

import json
import time
from controller.utilities.utils import Observer
import controller.response.adjusters as aj


class Responder(Observer):
    def __init__(self, config):
        """
        constructor
        """
        with open(config['bounds']) as file:
            self.bounds = json.loads(file.read())
        self.adjust_time = float(config['adjust_time'])
        # adjusted dictionary holds events that happend no longer than adjust_time
        # during the adjustment time the events are ignored to allow the control loop delay
        # the dictionary values are the time the delay will expire expire
        self.adjusted = {}


    def include_delay(self, events):
        """
        This function checks previous events that were added to self.adjusted with the delay time
        if the delay expired. All events for which the delay expired are removed from adjusted.
        Then the new events are checked against the self.adjusted dictionary. If the event already
        is there, it is ignore (because the delay time did not pass yet from the previous event).
        If it is a new event, it is added to the self.adjusted and to the new_events dictionary that
        will be returned
        Parameters
        ----------
        events : dict
            dictionary with the key of check function name, and value of tuple containing event and result
        Returns
        -------
        new_events : dict
            events with removed ones found in the self.adjusted dict
        """

        now = time.time()
        for ev in self.adjusted:
            if self.adjusted[ev] < now:
                self.adjusted.pop(ev)
        new_events = {}
        for ev in events:
            print ('ev', ev, type(ev))
            if not ev in self.adjusted:
                self.adjusted[ev] = now + self.adjust_time
                new_events[ev] = events[ev]

        return new_events


    def update(self, *args, **kwargs):
        """
        This function runs adjusters corresponding to events.
        """
        events = args[0][0]
        print ('events1',events)
        print(events, type(events))
        events = self.include_delay(events)
        aj.adjust(events, self.bounds)



