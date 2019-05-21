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
    return skt


def disconnect(socket):
    '''
    Closes the connection on the given socket.

    :param socket: socket to close connection on.
    '''
    socket.close()


def send_and_receive(socket, ajp_request, stream):
    '''
    Performs the data exchange with the servlet container.

    :param socket: socket connection to the servlet container.
    :param ajp_request: request to send to the servlet container.
    :param stream: bytes object used to receive data.

    :return: the AjpResponse object
    '''
    socket.sendall(ajp_request.serialize_to_packet())
    return AjpResponse.parse(stream, ajp_request)
