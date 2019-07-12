# #########################################################################
# Copyright (c) , UChicago Argonne, LLC. All rights reserved.             #
#                                                                         #
# See LICENSE file.                                                       #
# #########################################################################
import os
from configobj import ConfigObj
import controller.response.responder as resp
import controller.monitoring.monitor as mon
import controller.feeds.pv_feed as pvf
#import controller.feeds.pva_feed as pvaf


__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c), UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['control']

def control(conf):
    """
    This function starts monitoring and controlling experiment as a loop back.

    It initiates the responder as observer, and auditor as observable, and feed that will deliver data.
    The auditor monitors experiment outcome, and if defined parameter reaches a threshold, it will
    notify the observer.
    The responder observer will take an action when it is notified. The action will be typically
    changing process variable, and will be executed in a separate thread.

    Parameters
    ----------
    conf : str
        name of the configuration file

    Returns
    -------
    nothing
    """
    if os.path.isfile(conf):
        config = ConfigObj(conf)
        try:
            assert 'bounds' in config
            assert 'checks' in config
            assert 'pvs' in config
            assert 'feed' in config
            assert 'detector' in config
        except:
            print("configuration file must have defined following parameters: 'bounds','checks','pvs','feed','detector'")
            return
    else:
        print ('configuration file ' + conf + ' not found')
        return

    cntl = resp.Responder(config)
    # monitor will start feed
    monitor = mon.Monitor(config)
    monitor.register(cntl)

    if config['feed'] == 'pv':
        feed = pvf.Feed(config, monitor)
    elif config['feed'] == 'pva':
        feed = pvaf.Feed(config, monitor)

    feed.feed_data()

control('config/cntl_conf')