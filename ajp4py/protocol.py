'''
protocol.py
===========

Manages communications between the servlet container and this
library.

'''

import socket

from hexdump import hexdump

from . import PROTOCOL_LOGGER
from .models import AjpResponse


class AjpConnection:
    r'''Encapsulates a connection to a servlet container.

    Use the `with` construct to use an instance of AjpConnection. This 
    will guarantee connections are closed at the end.

    ..code-block :: Python

        with AjpConnection('localhost', 8009) as ajp_conn:
            ajp_response = ajp_conn.send_and_receive(ajp_request)

    '''

    def __init__(self, host_name, port):
        self._host_name = host_name
        self._port = port
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.disconnect()

    def __repr__(self):
        return '<AjpConnection: {0}:{1}>'.format(self._host_name, self._port)

    def connect(self):
        'Connect to this AjpConnection\'s host on the given port.'
        self._socket.connect((self._host_name, self._port))
        PROTOCOL_LOGGER.info('Connected {}'.format(self.__repr__()))

    def disconnect(self):
        'Disconnect from the host'
        PROTOCOL_LOGGER.debug('Closing connection...')
        self._socket.close()

    def send_and_receive(self, ajp_request):
        '''Send the request and receive the response.

        :type ajp_request: AjpForwardRequest with all request data.
        :return: :class:`AjpResponse <AjpResponse>` object
        :rtype: ajp4py.AjpResponse
        '''
        buffer = self._socket.makefile('rb')
        request_packet = ajp_request.serialize_to_packet()
        PROTOCOL_LOGGER.debug(
            'request_packet sent:\n%s', hexdump(
                request_packet, result='return'))
        self._socket.sendall(request_packet)
        ajp_resp = AjpResponse.parse(buffer, ajp_request)
        buffer.close()
        return ajp_resp
