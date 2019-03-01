#!/usr/bin/env python
# -*- coding: utf-8 -*-

# #########################################################################
# Copyright (c) 2016, UChicago Argonne, LLC. All rights reserved.         #
#                                                                         #
# Copyright 2016. UChicago Argonne, LLC. This software was produced       #
# under U.S. Government contract DE-AC02-06CH11357 for Argonne National   #
# Laboratory (ANL), which is operated by UChicago Argonne, LLC for the    #
# U.S. Department of Energy. The U.S. Government has rights to use,       #
# reproduce, and distribute this software.  NEITHER THE GOVERNMENT NOR    #
# UChicago Argonne, LLC MAKES ANY WARRANTY, EXPRESS OR IMPLIED, OR        #
# ASSUMES ANY LIABILITY FOR THE USE OF THIS SOFTWARE.  If software is     #
# modified to produce derivative works, such modified software should     #
# be clearly marked, so as not to confuse it with the version available   #
# from ANL.                                                               #
#                                                                         #
# Additionally, redistribution and use in source and binary forms, with   #
# or without modification, are permitted provided that the following      #
# conditions are met:                                                     #
#                                                                         #
#     * Redistributions of source code must retain the above copyright    #
#       notice, this list of conditions and the following disclaimer.     #
#                                                                         #
#     * Redistributions in binary form must reproduce the above copyright #
#       notice, this list of conditions and the following disclaimer in   #
#       the documentation and/or other materials provided with the        #
#       distribution.                                                     #
#                                                                         #
#     * Neither the name of UChicago Argonne, LLC, Argonne National       #
#       Laboratory, ANL, the U.S. Government, nor the names of its        #
#       contributors may be used to endorse or promote products derived   #
#       from this software without specific prior written permission.     #
#                                                                         #
# THIS SOFTWARE IS PROVIDED BY UChicago Argonne, LLC AND CONTRIBUTORS     #
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT       #
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS       #
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL UChicago     #
# Argonne, LLC OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,        #
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,    #
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;        #
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER        #
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT      #
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN       #
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE         #
# POSSIBILITY OF SUCH DAMAGE.                                             #
# #########################################################################

"""
Please make sure the installation :ref:`pre-requisite-reference-label` are met.

This module feeds the data coming from detector.
"""

import controller.utilities.utils as ut
import json
import time
import pvaccess


__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['start_feed',
           'stop_feed'
           'on_change']


class Feed(object):
    """
    This class reads frames in a real time, and delivers to consumers.
    """

    def __init__(self, config, app):
        """
        Constructor
        """
        # for communication with pvaccess - receiving data
        self.app = app
        self.pva_name = config['pva_name']
        self.detector = config['detector']
        with open(config['pvs']) as file:
            self.pvs = json.loads(file.read())
        self.chan = None


    def deliver_data(self, data):
        # process data in the same thread as the callback
        self.app.process_data(data)


    def on_change(self, v):
        uniqueId = v['uniqueId']
        print('uniqueId: ', uniqueId)

        img = v['value'][0]['ushortValue']
        slice = img.reshape(self.dims)

        #acq_time = v["attribute"][self.ack_time]["value"][0]["value"]
        pv_pairs = {}
        for pv in self.pvs:
            pv_pairs[pv] = (self.pvs[pv], v["attribute"][self.pvs[pv]]["value"][0]["value"])

        data = ut.Data(slice, pv_pairs)
        #data = ut.Data(slice, ack_time=acq_time)

        self.deliver_data(data)



    def stop_feed(self):
        # stop getting data
        self.chan.stopMonitor()
        self.chan.unsubscribe('update')


    def feed_data(self):
        self.chan = pvaccess.Channel(self.pva_name)

        x, y = self.chan.get('field()')['dimension']
        self.dims = (y['size'], x['size'])
        print(self.dims)

        labels = [item['name'] for item in self.chan.get('field()')['attribute']]
        self.ack_time = labels.index("AckTime")

        self.chan.subscribe('update', self.on_change)
        self.chan.startMonitor("value,attribute,uniqueId")

        # start the infinit loop so the feed does not stop after this init
        if True:
            time.sleep(10)


