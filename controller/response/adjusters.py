#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This file is a suite of control functions.
"""

from epics import caput
import math


__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = [
           'intensity_rate_adj',
           'Npix_oversat_cnt_rate_adj',
           'Npix_undersat_cnt_rate_adj',
           'adjust']


def intensity_rate_adj(**kws):
    """
    This method adjusts pv that affects intensity od data.

    Parameters
    ----------
    event : Event
        Event instance containing result value, and tuple with acquire time pv name and value
    bounds : dict
        dictionary of bounds, including target value

    Returns
    -------
    nothing
    """
    bounds = kws['bounds']
    target = bounds['target']
    # Event instance for this adjuster contains result and a tuple with acquire time pv name and value
    event = kws['event']
    res = event.result
    acq_time_pair = event.acq_time

    # the rate (intensity sum/acq_time) should be adjusted towards target by changing acq_time
    new_ack_time = res / target * acq_time_pair[1]
    caput(acq_time_pair[0], new_ack_time)


def Npix_oversat_cnt_rate_adj(**kws):
    """
    This method adjusts pv that affects saturation count rate.

    Parameters
    ----------
    event : Event
        Event instance containing rate value, and tuple with acquire time pv name and value
    bounds : dict
        dictionary of bounds, including target
    Returns
    -------
    nothing
    """
    bounds = kws['bounds']
    target = bounds['target']
    event = kws['event']
    points_over_threshold = event.points_over_threshold
    acq_time_pair = event.acq_time

    # Too many points over saturation threshold
    adjust = math.log(points_over_threshold/target)

    new_ack_time = acq_time_pair[1] / adjust
    print ('old acq_time, new_acq_time', acq_time_pair[1], new_ack_time)
    caput(acq_time_pair[0], new_ack_time)


def Npix_undersat_cnt_rate_adj(**kws):
    """
    This method adjusts pv that affects saturation count rate.

    Parameters
    ----------
    event : Event
        Event instance containing rate value, and tuple with acquire time pv name and value
    bounds : dict
        dictionary of bounds, including target
    Returns
    -------
    nothing
    """
    bounds = kws['bounds']
    target = bounds['target']
    event = kws['event']
    points_over_threshold = event.points_over_threshold
    acq_time_pair = event.acq_time

    # Too little points over saturation threshold
    adjust = math.log(target/points_over_threshold)

    new_ack_time = acq_time_pair[1] / adjust
    print ('old acq_time, new_acq_time', acq_time_pair[1], new_ack_time)
    caput(acq_time_pair[0], new_ack_time)



# maps the adjuster ID to the function object
function_mapper = {
                   'intensity_rate': intensity_rate_adj,
                   'Npix_oversat_cnt_rate': Npix_oversat_cnt_rate_adj,
                   'Npix_undersat_cnt_rate': Npix_undersat_cnt_rate_adj,
                  }

def adjust(events, bounds):
    """
    This function runs validation methods applicable to the frame data type and enqueues results.
    This function calls all the quality checks and creates Results object that holds results of each quality check, and
    attributes, such data type, index, and status. This object is then enqueued into the "resultsq" queue.
    Parameters
    ----------
    events : dict
        dictionary with the key of check function name, and value of tuple containing event and result
    bounds : dictionary
        a dictionary containing target values for the checks
    Returns
    -------
    events : dict

    """

    for ev in events:
        function = function_mapper[ev]
        function(event=events[ev], bounds=bounds)
