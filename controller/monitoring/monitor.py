#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Monitor receives data from Feed, run suite of checks and if any event is discovered, notifies responder.
"""

import json
from controller.utilities.utils import Observable
import controller.monitoring.checks as checks


class Monitor(Observable):
    def __init__(self, config):
        """
        constructor
        """
        with open(config['bounds']) as file:
            self.bounds = json.loads(file.read())
        with open(config['checks']) as file:
            self.checks = json.loads(file.read())


    def process_data(self, data):
        """
        This function runs applicable checks.
        All events returned by the checks are passed with notify function to the observer.
        """
        events = checks.run_quality_checks(data, self.checks, self.bounds)
        print ('events',events)
        if events is not None:
            # if event is detected, call notify
            self.notify(events)
