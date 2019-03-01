#!/usr/bin/env python
# -*- coding: utf-8 -*-


from multiprocessing import Queue, Process
import numpy as np
import zmq
import time
import sys
import json

__author__ = "Barbara Frosik"
__copyright__ = "Copyright (c) 2016, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['zmq_rec.zmq_rec',
           'zmq_rec.destroy',
           'init',
           'receive_zmq_send']


class zmq_rec():
    """
    This class represents ZeroMQ connection.
    """
    def __init__(self, host=None, port=None):
        """
        Constructor
        This constructor creates zmq Context and socket for the zmq.PAIR.
        It initiate connect to the server given by host and port.
        Parameters
        ----------
        host : str
            server host name
        port : str
            serving port
        """
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PAIR)
        self.socket.connect("tcp://" + host +":%s" % port)


    def destroy(self):
        """
        Destroys Context. This also closes socket associated with the context.
        """
        self.context.destroy()


def init(config):
    """
    This function initializes variables according to configuration.
    It gets values from the configuration file, evaluates and processes the values. If mandatory parameter is missing,
    the script logs an error and exits.
    Parameters
    ----------
    config : str
        configuration file name, including path
    Returns
    -------
    logger : Logger
        logger instance
    bounds.json : dictionary
        a dictionary containing limit values read from the configured 'limit' file
    quality_checks : dict
        a dictionary containing quality check functions ids
    feedback : list
        a list of strings defining real time feedback of quality checks errors. Currently supporting 'PV', 'log', and
        'console'
    report_type : int
        report type; currently supporting 'none', 'error', and 'full'
    consumers : dict
        a dictionary parsed from json file representing consumers
    zmq_host : str
        ZeroMQ server host name
    zmq_rcv_port : str
        ZeroMQ port
    detector : str
        detector name, only needed if feedback contains pv
    """

    conf = utils.get_config(config)
    if conf is None:
        print ('configuration file is missing')
        exit(-1)

    logger = utils.get_logger(__name__, conf)

    limitsfile = utils.get_file(conf, 'bounds.json', logger)
    if limitsfile is None:
        sys.exit(-1)

    with open(limitsfile) as limits_file:
        limits = json.loads(limits_file.read())

    qcfile = utils.get_file(conf, 'quality_checks', logger)
    if qcfile is None:
        sys.exit(-1)

    with open(qcfile) as qc_file:
        dict = json.loads(qc_file.read())
    #quality_checks = utils.get_quality_checks(dict)
    quality_checks = dict

    try:
        feedback = conf['feedback_type']
    except KeyError:
        feedback = None

    try:
        report_type = conf['report_type']
    except KeyError:
        report_type = const.REPORT_FULL

    try:
        zmq_host = conf['zmq_host']
    except:
        zmq_host = 'localhost'

    try:
        zmq_rcv_port = conf['zmq_rcv_port']
    except:
        zmq_rcv_port = None
        print ('configuration error: zmq_rcv_port not configured')

    try:
        detector = conf['detector']
    except KeyError:
        print ('configuration error: detector parameter not configured.')
        return None

    try:
        consumers = conf['zmq_snd_port']
    except KeyError:
        consumers = None

    return logger, limits, quality_checks, feedback, report_type, consumers, zmq_host, zmq_rcv_port, detector


def receive_zmq_send(dataq, zmq_host, zmq_rcv_port):
    """
    This function receives data from socket and enqueues it into a queue until the end is detected.
    Parameters
    ----------
    dataq : Queue
        a queue passing data received from ZeroMQ server to another process
    zmq_host : str
        ZeroMQ server host name
    zmq_rcv_port : str
        ZeroMQ port
    Returns
    -------
    none
    """

    conn = zmq_rec(zmq_host, zmq_rcv_port)
    socket = conn.socket
    interrupted = False
    while not interrupted:
        msg = socket.recv_json()
        key = msg.get("key")
        if key == "end":
            data = containers.Data(const.DATA_STATUS_END)
            dataq.put(data)
            interrupted = True
            conn.destroy()
        elif key == "image":
            msg["receiving_timestamp"] = time.time()
            dtype = msg["dtype"]
            shape = msg["shape"]
            image_number = msg['image_number']
            #image_timestamp = msg['image_timestamp']
            theta = msg['rotation']

            image = np.frombuffer(socket.recv(), dtype=dtype).reshape(shape)

            data = containers.Data(const.DATA_STATUS_DATA, image, 'data')
            data.theta = theta
            data.image_number = image_number
            dataq.put(data)


def verify(config):
    """
    This function starts real time verification process according to the given configuration.
    This function reads configuration and initiates variables accordingly.
    It starts the handler process that verifies data and starts a process receiving the data from ZeroMQ server.
    Parameters
    ----------
    conf : str
        configuration file name, including path
    Returns
    -------
    none
    """
    logger, limits, quality_checks, feedback, report_type, consumers, zmq_host, zmq_rcv_port, detector = init(config)

    feedback_obj = fb.Feedback(feedback)
    if const.FEEDBACK_LOG in feedback:
        feedback_obj.set_logger(logger)

    if const.FEEDBACK_PV in feedback:
        feedback_pvs = utils.get_feedback_pvs(quality_checks)
        feedback_obj.set_feedback_pv(feedback_pvs, detector)

    dataq = Queue()
    p = Process(target=handler.handle_data, args=(dataq, limits, None, quality_checks, None, consumers, feedback_obj))
    p.start()

    receive_zmq_send(dataq, zmq_host, zmq_rcv_port)