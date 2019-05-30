'''
protocol.py
===========

Manages communications between the servlet container and this
library.

'''

import socket

from . import PROTOCOL_LOGGER
from .models import ATTRIBUTE, AjpAttribute, AjpResponse


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
        self._socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
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
        PROTOCOL_LOGGER.info('Connected %s', self.__repr__())

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
        # Add this socket's local port and address as request attributes.
        attrs = ajp_request.request_attributes
        attrs.append(ATTRIBUTE(AjpAttribute.REQ_ATTRIBUTE,
                               ('AJP_REMOTE_PORT',
                                str(self._socket.getsockname()[1]))))
        attrs.append(ATTRIBUTE(AjpAttribute.REQ_ATTRIBUTE,
                               ('AJP_LOCAL_ADDR',
                                self._socket.getsockname()[0])))
        # Serialize the non-data part of the request.
        request_packet = ajp_request.serialize_to_packet()
        self._socket.sendall(request_packet)

        # Serialize the data (if any).
        for packet in ajp_request.serialize_data_to_packet():
            if len(packet) == 4:
                break
            self._socket.sendall(packet)

        ajp_resp = AjpResponse.parse(buffer, ajp_request)
        buffer.close()
        return ajp_resp
