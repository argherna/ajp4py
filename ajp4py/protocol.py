'''
protocol.py
===========

Manages communications between the servlet container and this
library.

This is a low-level module and should be used by the other
modules in this library. However, to have more explicit control
over interactions, it can be used by clients.
'''

import socket

from hexdump import hexdump

from . import PROTOCOL_LOGGER
from .models import AjpResponse


def connect(host_name, port):
    '''
    Returns a socket for communicating to a servlet container.

    :param host_name: name of the host to connect to.
    :param port: port to connect to.
    '''
    skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    skt.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    skt.connect((host_name, port))
    PROTOCOL_LOGGER.debug('Connection established:%s', skt)
    return skt


def disconnect(skt):
    '''
    Closes the connection on the given socket.

    :param skt: socket to close connection on.
    '''
    PROTOCOL_LOGGER.debug('Closing %s', skt)
    skt.close()


def send_and_receive(skt, ajp_request):
    '''
    Performs the data exchange with the servlet container.

    :param skt: socket connection to the servlet container.
    :param ajp_request: request to send to the servlet container.

    :return: the AjpResponse object
    '''
    buffer = skt.makefile('rb')
    request_packet = ajp_request.serialize_to_packet()
    PROTOCOL_LOGGER.debug(
        'request_packet sent:\n%s', hexdump(
            request_packet, result='return'))
    skt.sendall(request_packet)
    ajp_resp = AjpResponse.parse(buffer, ajp_request)
    buffer.close()
    return ajp_resp
