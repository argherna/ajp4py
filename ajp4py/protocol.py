'''
protocol.py
===========

Manages communications between the servlet container and this
library.

'''

import socket
from io import BytesIO

from . import PROTOCOL_LOGGER
from .ajp_types import (AjpPacketHeadersFromContainer, AjpSendHeaders,
                        header_case, lookup_status_by_code)
from .models import ATTRIBUTE, AjpAttribute, AjpResponse
from .utils import unpack_as_string, unpack_as_string_length, unpack_bytes

# pylint: disable=R0914


class AjpConnection:
    r'''Encapsulates a connection to a servlet container.

    Use the `with` construct to use an instance of AjpConnection. This
    will guarantee connections are closed at the end.

    ..code-block :: Python

        with AjpConnection('localhost', 8009) as ajp_conn:
            ajp_response = ajp_conn.send_and_receive(ajp_request)

    '''

    # Receive buffer length
    RECEIVE_BUFFER_LENGTH = 8192

    # Response header length
    RESPONSE_HEADER_LENGTH = 5

    def __init__(self, host_name, port):
        self._host_name = host_name
        self._port = port
        self._socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)

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
        # Add this socket's local port as a request attribute.
        attrs = ajp_request.request_attributes
        attrs.append(ATTRIBUTE(AjpAttribute.REQ_ATTRIBUTE,
                               ('AJP_REMOTE_PORT',
                                str(self._socket.getsockname()[1]))))
        PROTOCOL_LOGGER.debug('Request attributes: %s',
                              ajp_request.request_attributes)

        # Serialize the non-data part of the request.
        request_packet = ajp_request.serialize_to_packet()
        self._socket.sendall(request_packet)

        # Serialize the data (if any).
        _prefix_code = AjpPacketHeadersFromContainer.GET_BODY_CHUNK
        _resp_buffer = None
        for packet in ajp_request.serialize_data_to_packet():
            # As each data packet is sent, make sure the servlet container
            # responds with a GET_BODY_CHUNK header and send more if there
            # is any.
            if _prefix_code == AjpPacketHeadersFromContainer.GET_BODY_CHUNK:
                self._socket.sendall(packet)
                _data = self._socket.recv(self.RESPONSE_HEADER_LENGTH)
                _resp_buffer = BytesIO(_data)
                _, _data_len, _prefix_code = unpack_bytes('>HHb', _resp_buffer)
                _resp_buffer = BytesIO(self._socket.recv(_data_len - 1))

        ajp_resp = AjpResponse()
        _resp_content = b''

        # Data has been sent. Now parse the reply making sure to 'offset'
        # anything read from the socket already by sending the BytesIO
        # object if there is one.
        while _prefix_code != AjpPacketHeadersFromContainer.END_RESPONSE:

            if not _resp_buffer:
                _data = self._socket.recv(self.RESPONSE_HEADER_LENGTH)
                _magic, _data_len, _prefix_code = unpack_bytes(
                    '>HHb', BytesIO(_data))
                _resp_buffer = BytesIO(self._socket.recv(_data_len - 1))

            if _prefix_code == AjpPacketHeadersFromContainer.SEND_HEADERS:

                status_code, = unpack_bytes('>H', _resp_buffer)
                _, = unpack_as_string(_resp_buffer)
                setattr(ajp_resp, '_response_headers',
                        self._read_response_headers(_resp_buffer))
                setattr(ajp_resp, '_status_code', status_code)
                setattr(
                    ajp_resp,
                    '_status_msg',
                    lookup_status_by_code(status_code).description)

            elif _prefix_code == AjpPacketHeadersFromContainer.SEND_BODY_CHUNK:

                _data_len, = unpack_bytes('>H', _resp_buffer)
                _resp_content += _resp_buffer.read(_data_len + 1)

            elif _prefix_code == AjpPacketHeadersFromContainer.END_RESPONSE:

                _, = unpack_bytes('b', _resp_buffer)

            else:

                PROTOCOL_LOGGER.error(
                    'Unknown value for _prefix_code:%d', _prefix_code)
                raise NotImplementedError

            # Clear the response buffer for the next iteration.
            _resp_buffer = None

        setattr(ajp_resp, '_ajp_request', ajp_request)
        setattr(ajp_resp, '_content', _resp_content)
        return ajp_resp

    @staticmethod
    def _read_response_headers(resp_buffer):
        '''
        Read response headers from the response, parse, and return them.

        :param resp_buffer: BytesIO object containing the header data.
        :return: dict containing the response headers.
        '''
        response_headers = {}
        headers_sz, = unpack_bytes('>H', resp_buffer)
        for _ in range(headers_sz):
            header_name_len, = unpack_bytes('>H', resp_buffer)
            if header_name_len < AjpSendHeaders.CONTENT_TYPE.value:
                header_n, = unpack_as_string_length(
                    resp_buffer, header_name_len)
                header_v, = unpack_as_string(resp_buffer)
            else:
                header_n = header_case(
                    AjpSendHeaders(header_name_len).name)
                header_v, = unpack_as_string(resp_buffer)
            response_headers[header_n] = header_v

        return response_headers
