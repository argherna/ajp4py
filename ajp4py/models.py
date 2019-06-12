'''
models.py
=========

Basic objects used for communication bodies with a servlet container.
'''
import logging
import struct
from io import BytesIO
from collections import namedtuple

from . import AJP4PY_LOGGER
from .ajp_types import (AjpAttribute, AjpHeader, AjpPacketHeadersFromContainer,
                        AjpPacketHeadersToContainer, AjpRequestDirection,
                        AjpSendHeaders, header_case, lookup_status_by_code)

# Used by AjpForwardRequest to avoid magic numbers.
DEFAULT_REQUEST_SERVER_PORT = 80

# AjpForwardRequest uses this namedtuple for building a list of request
# attributes.
ATTRIBUTE = namedtuple('Attribute', 'ajp_attr, value')


def pack_as_string(string):
    'Returns the bytes object after packing the string'
    if not string:
        return struct.pack('>h', -1)

    string_len = len(string)
    return struct.pack(
        '>H%dsb' % string_len, string_len, string.encode('utf8'), 0)


def unpack_bytes(fmt, buffer):
    '''Unpacks bytes from the buffer using the given fmt.

    fmt is the same as struct.

    :param fmt: format string for unpacking the bytes.
    :param buffer: buffer containing the bytes to unpack.
    :return: tuple containing the values unpacked according to the
    fmt string.

    See https://docs.python.org/3/library/struct.html#format-strings
    '''
    size = struct.calcsize(fmt)
    chunk = buffer.read(size)
    return struct.unpack(fmt, chunk)


def unpack_as_string_length(buffer, length):
    'Unpacks the buffer for the given length as string.'
    resp_str = unpack_bytes('%ds' % length, buffer)

    # Skip over null-terminator
    buffer.read(1)
    return resp_str


def unpack_as_string(buffer):
    'Unpacks the given buffer as a string and returns it.'
    str_len = unpack_bytes('>h', buffer)
    if not str_len:
        return None

    return unpack_as_string_length(buffer, str_len)


class AjpForwardRequest:
    '''
    Represents a request to the servlet container.

    See https://tomcat.apache.org/connectors-doc/ajp/ajpv13a.html

    :param direction: AjpRequestDirection for this request.
    :param method: AjpCommand for the method to use.
    :param protocol: (optional) protocol to set. This is only sent as
        part of the request and is metadata from what I can tell. 
    :param req_url: (optional) request uri, which is the path of the
        url sent to the servlet container.
    :param remote_addr: IP address of the host sending the request.
    :param remote_host: name of the host sending the request.
    :param server_name: name of the server to receive the request.
    :param server_port: (optional) target port on the server. This is
        only sent as part of the request and is metadata from what I
        can tell.
    :param is_ssl: (optional) boolean flag indicating that the request
        is SSL (default is False).
    :param request_headers: dictionary of HTTP request headers.
    :param attributes: list of ATTRIBUTE named tuples that are AJP
        attributes sent to the request.
    :param data_stream: (optional) File-like object containing the 
        request data (e.g. json, form data, or binary data).
    '''

    # AJP's maximum buffer size for sending data.
    MAX_REQUEST_LENGTH = 8186

    # pylint: disable=too-many-instance-attributes

    def __init__(self,
                 direction=AjpRequestDirection.WEB_SERVER_TO_SERVLET_CONTAINER,
                 method=None,
                 protocol='HTTP/1.1',
                 req_uri=None,
                 remote_addr=None,
                 remote_host=None,
                 server_name=None,
                 server_port=DEFAULT_REQUEST_SERVER_PORT,
                 is_ssl=False,
                 request_headers={},
                 attributes=[],
                 data_stream=None):
        self._direction = direction
        self._method = method
        self._protocol = protocol
        self._req_uri = req_uri
        self._remote_addr = remote_addr
        self._remote_host = remote_host
        self._server_name = server_name
        self._server_port = server_port
        self._is_ssl = is_ssl
        self._num_headers = 0
        self._request_headers = request_headers
        self._attributes = attributes
        self._data_stream = data_stream

    @property
    def method(self):
        'Returns the AJP/HTTP method'
        return self._method

    @property
    def protocol(self):
        'Returns the protocol for this AjpForwardRequest'
        return self._protocol

    @property
    def req_uri(self):
        'Returns the `req_uri` for this AjpForwardRequest'
        return self._req_uri

    @property
    def remote_addr(self):
        'Returns the `remote_addr` for this AjpForwardRequest'
        return self._remote_addr

    @property
    def remote_host(self):
        'Returns the `remote_host` for this AjpForwardRequest'
        return self._remote_host

    @property
    def server_name(self):
        'Returns the `server_name` for this AjpForwardRequest'
        return self._server_name

    @property
    def server_port(self):
        'Returns the `server_port` for this AjpForwardRequest'
        return self._server_port

    @property
    def is_ssl(self):
        'Returns the `is_ssl` for this AjpForwardRequest'
        return self._is_ssl

    @property
    def request_headers(self):
        'Returns the `request_headers` for this AjpForwardRequest'
        return self._request_headers

    @property
    def request_attributes(self):
        'Returns the `attributes` for this AjpForwardRequest'
        return self._attributes

    @property
    def data_stream(self):
        'Returns the data for this AjpForwardRequest'
        return self._data_stream

    def __repr__(self):
        return '<AjpForwardRequest: [%s], remote_host=%s, req_uri=%s, request_headers=%s>' % (
            self._method.name, self._remote_host, self._req_uri, self._request_headers)

    def serialize_to_packet(self):
        'Returns the bytes object to send to the servlet container.'
        return self._serialize_forward_request()

    def serialize_data_to_packet(self):
        '''Generator that serializes the request body into packets to 
        the servlet container.'''
        if not self._data_stream:
            return
        data = self._data_stream.read(self.MAX_REQUEST_LENGTH)
        while True:
            if len(data) > 0:
                packet = struct.pack('>H', len(data))
                packet += data
                packet_header = struct.pack(
                    '>bbH',
                    self._direction.first_bytes[0],
                    self._direction.first_bytes[1],
                    len(packet))
                yield packet_header + packet
            else:
                yield struct.pack('>bbH', self._direction.first_bytes[0],
                                  self._direction.first_bytes[1], 0x00)
                break
            data = self._data_stream.read(self.MAX_REQUEST_LENGTH)

    def _serialize_forward_request(self):
        'Serializes the forward request.'
        packet = b''
        packet = struct.pack(
            'bb',
            AjpPacketHeadersToContainer.FORWARD_REQUEST.value,
            self._method.value)
        packet += pack_as_string(self._protocol)
        packet += pack_as_string(self._req_uri)
        packet += pack_as_string(self._remote_addr)
        packet += pack_as_string(self._remote_host)
        packet += pack_as_string(self._server_name)
        packet += struct.pack('>h', self._server_port)
        packet += struct.pack('?', self._is_ssl)
        packet += self._serialize_headers()
        packet += self._serialize_attributes()

        packet_header = struct.pack(
            '>bbh',
            self._direction.first_bytes[0],
            self._direction.first_bytes[1],
            len(packet))
        return packet_header + packet

    def _serialize_headers(self):
        '''
        Returns the bytes object containing the number of headers and the
        serialized headers.
        '''
        hdr_packet = struct.pack('>h', len(self._request_headers))
        for hdr_name in self._request_headers:
            if isinstance(hdr_name, AjpHeader):
                # Need to split the code into 2 bytes before packing it.
                hdr_packet += struct.pack('BB', hdr_name.value >>
                                          8, hdr_name.value & 0x0F)
            else:
                hdr_packet += pack_as_string(hdr_name)
            hdr_val = self._request_headers[hdr_name]
            if isinstance(hdr_val, list):
                hdr_val = ','.join(hdr_val)
            hdr_packet += pack_as_string(hdr_val)

        return hdr_packet

    def _serialize_attributes(self):
        ' Returns the bytes object containing the serialized attributes.'
        attr_packet = b''
        for attr in self._attributes:
            # Assume self._attributes contain only ATTRIBUTE types
            # whose name field is a type of AjpAttribute
            attr_packet += struct.pack('b', attr.ajp_attr.code)
            if attr.ajp_attr == AjpAttribute.REQ_ATTRIBUTE:
                nm, val = attr.value
                attr_packet += pack_as_string(nm)
                attr_packet += pack_as_string(val)
            else:
                attr_packet += pack_as_string(attr.value)

        attr_packet += struct.pack('B', AjpAttribute.ARE_DONE.code)
        return attr_packet


class AjpResponse:
    '''
    Represents a response from the servlet container.

    See https://tomcat.apache.org/connectors-doc/ajp/ajpv13a.html.
    '''

    def __init__(self):
        self._status_code = None
        self._status_msg = None
        self._response_headers = {}
        self._ajp_request = None
        self._content = None

    def __repr__(self):
        return '<AjpResponse: [%d, %s]>' % (
            self._status_code, self._status_msg.decode('utf-8'))

    @property
    def status_code(self):
        'Returns the status code.'
        return self._status_code

    @property
    def status_msg(self):
        'Returns the status message'
        return self._status_msg

    @property
    def headers(self):
        'Returns the response headers'
        return self._response_headers

    @property
    def request(self):
        'Returns the request for this response.'
        return self._ajp_request

    @property
    def text(self):
        'Returns the content as text for this response'
        # return self._content.decode('utf-8')
        return self._content

    @property
    def content(self):
        'Returns content as bytes'
        return self._content

    @staticmethod
    def parse(sock, ajp_request, prefix_code=0, resp_buffer=None):
        '''
        Parse the response from the servlet container and return the 
        AjpResponse object.

        :param sock: the raw socket to read the response from.
        :param ajp_request: the request made that will generate the
            response.
        :param prefix_code: any previously read prefix code as part
            of a response from sending data (default is 0).
        :param resp_buffer: BytesIO object containing and data as part
            of a response from sending data (default is None).
        :class:`AjpResponse <AjpResponse>` object
        :rtype: ajp4py.AjpResponse
        '''
        ajp_resp = AjpResponse()
        _data = b''
        _resp_buffer = resp_buffer
        _resp_content = b''
        _prefix_code = prefix_code
        while _prefix_code != AjpPacketHeadersFromContainer.END_RESPONSE:

            if not _resp_buffer:
                _data = sock.recv(5)
                _magic, _data_len, _prefix_code = unpack_bytes(
                    '>HHb', BytesIO(_data))
                _resp_buffer = BytesIO(sock.recv(_data_len - 1))

            if _prefix_code == AjpPacketHeadersFromContainer.SEND_HEADERS:

                status_code, = unpack_bytes('>H', _resp_buffer)
                _, = unpack_as_string(_resp_buffer)
                headers_sz, = unpack_bytes('>H', _resp_buffer)
                response_headers = {}
                for _ in range(headers_sz):
                    header_name_len, = unpack_bytes('>H', _resp_buffer)
                    if header_name_len < AjpSendHeaders.CONTENT_TYPE.value:
                        header_n, = unpack_as_string_length(
                            _resp_buffer, header_name_len)
                        header_v, = unpack_as_string(_resp_buffer)
                    else:
                        header_n = header_case(
                            AjpSendHeaders(header_name_len).name)
                        header_v, = unpack_as_string(_resp_buffer)
                    response_headers[header_n] = header_v

                setattr(ajp_resp, '_response_headers', response_headers)
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

            elif _prefix_code == AjpPacketHeadersFromContainer.GET_BODY_CHUNK:

                if _resp_buffer:
                    _, = unpack_bytes('>H', _resp_buffer)

            else:

                AJP4PY_LOGGER.error('Unknown value for _prefix_code:%d', _prefix_code)
                raise NotImplementedError

            # Clear the response buffer for the next iteration.
            _resp_buffer = None

        setattr(ajp_resp, '_ajp_request', ajp_request)
        setattr(ajp_resp, '_content', _resp_content)
        return ajp_resp
