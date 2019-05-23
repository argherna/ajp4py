'''
models.py
=========

Basic objects used for communication bodies with a servlet container.
'''
import logging
import struct

from . import AJP4PY_LOGGER
from .ajp_types import (AjpAttribute, AjpHeader, AjpPacketHeadersFromContainer,
                        AjpPacketHeadersToContainer, AjpRequestDirection,
                        AjpSendHeaders, header_case, lookup_status_by_code)

# Used by AjpForwardRequest to avoid magic numbers.
DEFAULT_REQUEST_SERVER_PORT = 80


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
    :param host_name: target host of this request.
    :param server_port: target port of this request.
    '''

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
                 attributes={}):
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
    def attributes(self):
        'Returns the `attributes` for this AjpForwardRequest'
        return self._attributes

    def __repr__(self):
        return '<AjpForwardRequest: [%s], remote_host=%s, req_uri=%s, request_headers=%s>' % (
            self._method.name, self._remote_host, self._req_uri, self._request_headers)

    def serialize_to_packet(self):
        'Returns the bytes object to send to the servlet container.'
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
        hdr_packet = struct.pack('>h', self._num_headers)
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
        for attr_name in self._attributes:
            if isinstance(attr_name, AjpAttribute):
                attr_packet += struct.pack('b', attr_name.code)
            else:
                attr_packet += pack_as_string(attr_name)
            attr_val = self._attributes[attr_name]
            if isinstance(attr_val, list):
                attr_val = ','.join(attr_val)
            attr_packet += pack_as_string(self._attributes[attr_name])

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
        return int(self._status_code)

    @property
    def status_msg(self):
        'Returns the status message'
        return self._status_msg.decode('utf-8')

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
        return self._content.decode('utf-8')

    @staticmethod
    def parse(buffer, ajp_request):
        'Parses the response buffer and returns the AjpResponse'
        ajp_resp = AjpResponse()
        resp_content = b''
        while True:
            _, data_len, prefix_code = unpack_bytes('>HHb', buffer)

            if prefix_code == AjpPacketHeadersFromContainer.SEND_HEADERS:

                status_code, = unpack_bytes('>H', buffer)
                status_msg, = unpack_as_string(buffer)
                headers_sz, = unpack_bytes('>H', buffer)
                response_headers = {}
                for _ in range(headers_sz):
                    header_name_len, = unpack_bytes('>H', buffer)
                    if header_name_len < AjpSendHeaders.CONTENT_TYPE.value:
                        header_n, = unpack_as_string_length(
                            buffer, header_name_len)
                        header_v, = unpack_as_string(buffer)
                    else:
                        header_n = header_case(
                            AjpSendHeaders(header_name_len).name)
                        header_v, = unpack_as_string(buffer)
                    response_headers[header_n] = header_v

                setattr(ajp_resp, '_response_headers', response_headers)
                setattr(ajp_resp, '_status_code', status_code)
                if status_code == status_msg:
                    setattr(
                        ajp_resp,
                        '_status_msg',
                        lookup_status_by_code(status_code).description)
                else:
                    setattr(ajp_resp, '_status_msg', status_msg)

            elif prefix_code == AjpPacketHeadersFromContainer.SEND_BODY_CHUNK:

                data_len, = unpack_bytes('>H', buffer)
                resp_content += buffer.read(data_len + 1)
                continue

            elif prefix_code == AjpPacketHeadersFromContainer.END_RESPONSE:

                _, = unpack_bytes('b', buffer)
                break

            elif prefix_code == AjpPacketHeadersFromContainer.GET_BODY_CHUNK:

                _, = unpack_bytes('>H', buffer)

            else:

                raise NotImplementedError

        setattr(ajp_resp, '_content', resp_content)
        setattr(ajp_resp, '_ajp_request', ajp_request)

        return ajp_resp
