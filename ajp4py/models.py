'''
models.py
=========

Basic objects used for communication bodies with a servlet container.
'''
import struct
from collections import namedtuple

from .ajp_types import (AjpAttribute, AjpHeader, AjpPacketHeadersToContainer,
                        AjpRequestDirection)
from .utils import pack_as_string

# pylint: disable=C0103,R0902,R0913,R0914,W0102

# Used by AjpForwardRequest to avoid magic numbers.
DEFAULT_REQUEST_SERVER_PORT = 80

# AjpForwardRequest uses this namedtuple for building a list of request
# attributes.
ATTRIBUTE = namedtuple('Attribute', 'ajp_attr, value')


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
            if data:
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
        return '<AjpResponse: [{0}, {1}]>'.format(
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
