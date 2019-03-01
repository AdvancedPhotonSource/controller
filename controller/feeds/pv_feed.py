#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
Please make sure the installation :ref:`pre-requisite-reference-label` are met.

This module feeds the data coming from detector to a process using queue.
"""

from epics import caget, PV
from epics.ca import CAThread
import numpy as np
import json
import sys
import time
import controller.utilities.utils as ut


if sys.version[0] == '2':
    import Queue as tqueue
else:
    import queue as tqueue

__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['handle_event',
           'on_change',
           'start_processes',
           'get_pvs',
           'feed_data']


class Feed(object):
    """
    This class reads frames in a real time using pyepics, and delivers to consuming process.
    """

    def __init__(self, config, app):
        """
        Constructor
        """
        self.app = app
        self.eventq = tqueue.Queue()
        self.detector = config['detector']
        with open(config['pvs']) as file:
            self.pvs = json.loads(file.read())
        self.sizex = 0
        self.sizey = 0
        self.index = 0
        self.current_counter = None


    def event(self, event_str):
        # we will find out later how to handle the events
        pass


    def deliver_data(self, data):
        # process data in the same thread as the callback
        self.app.process_data(data)


    def handle_event(self):
        """
        This function receives data, processes it, and delivers to consuming process.

        This function is invoked at the beginning of the feed as a distinct thread. It reads data from a thread_dataq
        inside a loop that delivers current counter value on change.
        If the counter is not a consecutive number to the previous reading a 'missing' string is enqueued into
        process_dataq in place of the data to mark the missing frames.
        For every received frame data, it reads a data type from PV, and the two elements are delivered to a consuming
        process via process_dataq as Data instance. If a sequence is defined, then the data type for this frame
        determined from sequence is compared with the data type read from PV. If they are different, a warning log is
        recorded.
        On the loop exit an 'all_data' string is enqueud into the inter-process queue, and 'exit' string is enqueued
        into the inter-thread queue, to notify the main thread of the exit event.

        Parameters
        ----------
        data_pv : str
            a PV string for the area detector data

        frame_type_pv : str
            a PV string for the area detector data type

        logger : Logger
            a Logger instance, typically synchronized with the consuming process logger

        Returns
        -------
        None
        """
        self.done = False
        while not self.done:
            try:
                callback_item = self.eventq.get(timeout=1)
                if callback_item == 'finish':
                    self.done = True
                else:
                    current_ctr = callback_item
                    if current_ctr > self.current_counter + 1:
                        self.event('missing frames')
                    self.current_counter = current_ctr + 1

                    try:
                        pv_pairs = {}
                        slice = np.array(caget(self.get_data_pv_name()))
                        # read other pvs
                        for pv in self.pvs:
                            pv_pairs[pv] = (self.pvs[pv], caget(self.pvs[pv]))
                        if slice is None:
                            done = True
                            self.event('reading image times out, possibly the detector exposure time is too small')
                        else:
                            slice.resize(self.sizex, self.sizey)
                            data = ut.Data(slice, pv_pairs)
                            # deliver data to monitor
                            self.deliver_data(data)
                    except:
                        self.done = True
                        self.event('reading image raises exception, possibly the detector exposure time is too small')
            except tqueue.Empty:
                continue

        self.finish()


    def acq_done(self, pvname=None, **kws):
        """
        A callback method that activates when pv acquire switches to off.

        If the value is 0, the function enqueues key word 'finish' into event queue that will be dequeued by the
        'handle_event' function.

        Parameters
        ----------
        pvname : str
            a PV string for acquire

        Returns
        -------
        None
        """
        if kws['value'] == 0:
            self.eventq.put('finish')


    def on_change(self, pvname=None, **kws):
        """
        A callback method that activates when a frame counter of area detector changes.

        This method reads the counter value and enqueues it into event queue that will be dequeued by the
        'handle_event' function.
        If it is a first read, the function adjusts counter data in the self object.

        Parameters
        ----------
        pvname : str
            a PV string for the area detector frame counter

        Returns
        -------
        None
        """

        current_ctr = kws['value']
        # init on first read
        if self.current_counter is None:
            self.current_counter = current_ctr - 1 # the self.current_counter holds previous
        self.eventq.put(current_ctr)


    def start_processes(self):
        """
        This function starts processes and callbacks.

        This is a main thread that starts thread reacting to the callback, starts the consuming process, and sets a
        callback on the frame counter PV change. The function then awaits for the data in the exit queue that indicates
        that all frames have been processed. The functin cancells the callback on exit.

        Parameters
        ----------
        none

        Returns
        -------
        nothing
        """
        data_thread = CAThread(target=self.handle_event, args=())
        data_thread.start()

        self.counter_pv = PV(self.get_counter_pv_name())
        self.counter_pv.add_callback(self.on_change, index=1)

        self.acq_pv = PV(self.get_acquire_pv_name())
        self.acq_pv.add_callback(self.acq_done, index=2)


    def get_acquire_pv_name(self):
        return self.detector + ':cam1:Acquire'


    def get_counter_pv_name(self):
        return self.detector + ':cam1:ArrayCounter_RBV'


    def get_data_pv_name(self):
        return self.detector + ':image1:ArrayData'


    def feed_data(self):
        """
        This function is called by a client to start the process.

        After all initial settings are completed, the method awaits for the area detector to start acquireing by polling
        the PV. When the area detective is active it starts processing.

        Parameters
        ----------
        none

        Returns
        -------
        nothing
        """
        test = True

        sizex_pv = self.detector + ':image1:ArraySize0_RBV'
        sizey_pv = self.detector + ':image1:ArraySize1_RBV'
        acquire_pv_name = self.get_acquire_pv_name()
        while test:
            self.sizex = caget(sizex_pv)
            self.sizey = caget(sizey_pv)
            ack = caget(acquire_pv_name)
            if ack == 1:
                test = False
                self.start_processes()
            else:
                time.sleep(.005)

        return caget(acquire_pv_name)


    def finish(self):
        try:
            self.counter_pv.disconnect()
        except:
            pass
        try:
            self.acq_pv.disconnect()
        except:
            pass


