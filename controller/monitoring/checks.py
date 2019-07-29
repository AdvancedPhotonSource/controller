#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This file is a suite of verification functions for scientific data.
"""
import controller.utilities.utils as ut

__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['check_limit',
           'intensity_rate',
           'Npix_oversat_cnt_rate',
           'Npix_undersat_cnt_rate',
           'run_quality_checks']


E_IN_LIMITS = 0
E_IN_THRESHOLDS = 0
E_LOW_TH = 1
E_HIGH_TH = 2
E_LOW_LM = 3
E_HIGH_LM = 4


def check_limit(res, limits):
    """
    This evaluates given result value against limits.

    Parameters
    ----------
    res : float
        calculated result

    limits : dictionary
        a dictionary containing limit values
    Returns
    -------
    result : int
        evaluation result
    """
    try:
        ll = limits['low_limit']
        if res < ll:
            return E_LOW_LM
    except KeyError:
        pass

    try:
        hl = limits['high_limit']
        if res > hl:
            return E_HIGH_LM
    except KeyError:
        pass

    return E_IN_LIMITS


def check_threshold(res, thresholds):
    """
    This evaluates given result value against thresholds.

    Parameters
    ----------
    res : float
        calculated result

    thresholds : dictionary
        a dictionary containing threshold values
    Returns
    -------
    result : int
        evaluation result
    """
    try:
        lt = thresholds['low_threshold']
        if res < lt:
            return E_LOW_TH
    except KeyError:
        pass

    try:
        ht = thresholds['high_threshold']
        if res > ht:
            return E_HIGH_TH
    except KeyError:
        pass

    return E_IN_THRESHOLDS


def intensity_rate(**kws):
    """
    This function validates rate of intensity in the frame.

    It sums the pixels intensity in the given frame and divides the sum by acquire time. The result is compared
    with threshold values. If the result exceeds limits or thresholds, an Event instance is created and returned.

    Parameters
    ----------
    data : Data
        data instance that includes slice 2D data
    bounds : dictionary
        a dictionary containing threshold values for the check
    Returns
    -------
    eval : int
        result of evaluation
    args : Event
        Event instance contains result value, and tuple with acquire time pv name and value
    """
    bounds = kws['bounds']
    data = kws['data']
    acq_time_pair = data.acq_time
    acq_time = acq_time_pair[1]

    this_bounds = bounds['intensity_rate']
    res = data.slice.sum()/acq_time
    eval = check_limit(res, this_bounds)
    # if the result did not exceeded limit, check if it over threshold
    if eval == E_IN_LIMITS:
        eval = check_threshold(res, this_bounds)
        if eval == E_IN_THRESHOLDS:
            return eval, None

    args = {}
    args['result'] = res
    args['ack_time'] = acq_time_pair
    return eval, args


def Npix_oversat_cnt_rate(**kws):
    """
    This method validates over-saturation rate in a frame.

    It calculates the saturation rate in the given frame for all pixels. All pixels for which the saturation rate
    exceeds limit are summed. The nuber of pixels is compared with limit and threshold values.
    If the result exceeds limits or thresholds, an Event instance is created and returned.

    Parameters
    ----------
    data : Data
        data instance that includes slice 2D data
    bounds : dictionary
        a dictionary containing threshold values for the check
    Returns
    -------
    eval : int
        result of evaluation
    args : Event
        Event instance contains result value, and tuple with acquire time pv name and value
    """
    bounds = kws['bounds']
    data = kws['data']

    this_bounds = bounds['Npix_oversat_cnt_rate']
    sub_bounds = bounds['pix_sat_cnt_rate']
    acq_time_pair = data.acq_time
    acq_time = acq_time_pair[1]

    rate = data.slice/acq_time

    points_over_hlimit = (rate > sub_bounds['high_limit']).sum()
    # find if number of pixels with saturation rate (intensity divided by acquire time) over limit exceeds the
    # number point saturation rate limit
    eval = check_limit(points_over_hlimit, this_bounds)
    # if the result do not exceed limit, check the threshold
    args = None
    if eval == E_IN_LIMITS:
        points_over_threshold = (rate > sub_bounds['target']).sum()
        print ('point over thr', points_over_threshold)
        eval = check_threshold(points_over_threshold, this_bounds)
        if eval != E_IN_THRESHOLDS:
            args = {}
            args['points_over_threshold'] = points_over_threshold
            args['ack_time'] = acq_time_pair

    return eval, args


def Npix_undersat_cnt_rate(**kws):
    """
    This method validates under-saturation rate in a frame.

    It calculates the saturation rate in the given frame for all pixels. All pixels for which the saturation rate
    is below limit are summed. The nuber of pixels is compared with limit and threshold values.
    If the result exceeds limits or thresholds, an Event instance is created and returned.

    Parameters
    ----------
    data : Data
        data instance that includes slice 2D data
    bounds : dictionary
        a dictionary containing threshold values for the check
    Returns
    -------
    eval : int
        result of evaluation
    args : Event
        Event instance contains result value, and tuple with acquire time pv name and value
    """

    bounds = kws['bounds']
    data = kws['data']

    this_bounds = bounds['Npix_undersat_cnt_rate']
    sub_bounds = bounds['pix_sat_cnt_rate']
    acq_time_pair = data.acq_time
    acq_time = acq_time_pair[1]

    rate = data.slice/acq_time

    points_over_llimit = (rate > sub_bounds['low_limit']).sum()

    # find if number of pixels with saturation rate (intensity divided by acquire time) over low limit is not enough
    eval = check_limit(points_over_llimit, this_bounds)
    # if the result do not exceed limit, check the threshold
    args = None
    if eval == E_IN_LIMITS:
        points_over_threshold = (rate > sub_bounds['target']).sum()
        eval = check_threshold(points_over_threshold, this_bounds)
        if eval != E_IN_THRESHOLDS:
            args = {}
            args['points_over_threshold'] = points_over_threshold
            args['ack_time'] = acq_time_pair

    return eval, args


# maps the quality check ID to the function object
function_mapper = {
                   'intensity_rate': intensity_rate,
                   'Npix_oversat_cnt_rate': Npix_oversat_cnt_rate,
                   'Npix_undersat_cnt_rate': Npix_undersat_cnt_rate,
                  }

def run_quality_checks(data, checks, bounds):
    """
    This function runs evaluation methods.

    This function calls the checks that are included in argument 'check' list. If the check returns event, it is added
    to event dictionary. Each event is an Event instance that contains fields applicable to the adjuster function that
    corresponds to the check.

    Parameters
    ----------
    data : Data
        data instance that includes slice 2D data
    checks : list
        a list of quality checks to apply
    bounds : dictionary
        a dictionary containing threshold values for the checks
    Returns
    -------
    events_dict : dict
        dictionary with check id key and Event as value. The Event is container encapsulating check specific
        fields that are passed to corresponding adjuster function

    """

    events_dict = {}
    for ck in checks:
        print ('check', ck)
        function = function_mapper[ck]
        eval, args = function(data=data, bounds=bounds)
        if eval != E_IN_THRESHOLDS:
            print ('event, args', args)
            events_dict[ck] = ut.Event(args)

    if len(events_dict) > 0:
        return events_dict
    else:
        return None