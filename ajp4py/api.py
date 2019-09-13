'''
api.py
======

Implements the API for sending AJP requests.
'''
import socket
from json import dumps
from urllib.parse import urlparse

from .ajp_types import DEFAULT_AJP_SERVER_PORT, AjpCommand
from .models import ATTRIBUTE, AjpAttribute, AjpForwardRequest, AjpHeader
from .protocol import AjpConnection
from .utils import data_to_bytes

# pylint: disable=C0103


def params_to_query_string(params):
    '''
    Returns an ATTRIBUTE named tuple where the name is set to
    `AjpAttribute.QUERY_STRING` and the value is the url-encoded query
    string.

    :param params: dict containing the query parameter name-value pairs.
    :return: ATTRIBUTE named tuple.
    '''
    query = []
    for nm, val in params.items():
        if isinstance(val, list):
            for v in val:
                query.append('='.join([nm, v]))
        else:
            query.append('='.join([nm, val]))

    query_string = None
    if query:
        query_string = ATTRIBUTE(AjpAttribute.QUERY_STRING, '&'.join(query))
    return query_string

# pylint: disable=too-many-arguments


def request(ajp_cmd, url, params=None, data=None, headers=None,
            attributes=None):
    r'''
    Send a generic request to the servlet container.

    :type ajp_cmd: An AjpCommand (equiv. to HTTP method)
    :param url: Url in the form `ajp://host[:port][/path]`
    :param params: (optional) Dictionary of parameters that will
        be converted into the query string.
    :param data: (optional) data sent as the body of the request.
    :param headers: (optional) Dictionary of request headers
    :param attributes: (optional) List of named tuples containing request
        attributes
    :return: :class:`AjpResponse <AjpResponse>` object
    :rtype: ajp4py.AjpResponse
    '''
    parsed_url = urlparse(url)
    host_name = parsed_url.netloc.split(':')[0]
    port = parsed_url.port or DEFAULT_AJP_SERVER_PORT

    if params:
        query_string_attr = params_to_query_string(params)
        if not attributes:
            attributes = []
        attributes.append(query_string_attr)

    io_data = None
    if data:
        if not headers:
            headers = {}
        if isinstance(data, dict):
            data_str = dumps(data)
            io_data = data_to_bytes(data_str)
            headers[AjpHeader.SC_REQ_CONTENT_LENGTH] = str(len(data_str))
        else:
            io_data = data_to_bytes(data)
            headers[AjpHeader.SC_REQ_CONTENT_LENGTH] = str(len(data))

    ajp_req = AjpForwardRequest(method=ajp_cmd,
                                req_uri=parsed_url.path,
                                remote_addr=socket.gethostbyname(
                                    'localhost'),
                                remote_host=socket.gethostname(),
                                server_name=host_name,
                                request_headers=headers or {},
                                attributes=attributes or [],
                                data_stream=io_data)

    with AjpConnection(host_name, port) as ajp_conn:
        ajp_resp = ajp_conn.send_and_receive(ajp_req)

    return ajp_resp


def get(url, params=None, **kwargs):
    r'''
    Sends a GET command to the servlet container.

    :param url: Url in the form `ajp://host[:port][/path]`
    :param params: (optional) query parameter string.
    :param \*\*kwargs: (optional) kwargs that request takes.
    :return: :class:`AjpResponse <AjpResponse>` object
    :rtype: ajp4py.AjpResponse
    '''
    return request(AjpCommand.GET, url, params=params, **kwargs)


def post(url, data=None, **kwargs):
    r'''
    Sends a POST command to the servlet container.

    :param url: Url in the form `ajp://host[:port][/path]`
    :param data: (optional) data sent as the body of the request.
    :param \*\*kwargs: optional kwargs that request takes.
    :return: :class:`AjpResponse <AjpResponse>` object
    :rtype: ajp4py.AjpResponse
    '''
    return request(AjpCommand.POST, url, data=data, **kwargs)


def put(url, data=None, **kwargs):
    r'''
    Sends a PUT command to the servlet container.

    :param url: Url in the form `ajp://host[:port][/path]`
    :param data: (optional) data sent as the body of the request.
    :param \*\*kwargs: optional kwargs that request takes.
    :return: :class:`AjpResponse <AjpResponse>` object
    :rtype: ajp4py.AjpResponse
    '''
    return request(AjpCommand.PUT, url, data=data, **kwargs)


def delete(url, **kwargs):
    r'''
    Sends a DELETE command to the servlet container.

    :param url: Url in the form `ajp://host[:port][/path]`
    :param \*\*kwargs: (optional) kwargs that request takes.
    :return: :class:`AjpResponse <AjpResponse>` object
    :rtype: ajp4py.AjpResponse
    '''
    return request(AjpCommand.DELETE, url, **kwargs)


def head(url, **kwargs):
    r'''
    Sends a HEAD command to the servlet container.

    :param url: Url in the form `ajp://host[:port][/path]`
    :param \*\*kwargs: (optional) kwargs that request takes.
    :return: :class:`AjpResponse <AjpResponse>` object
    :rtype: ajp4py.AjpResponse
    '''
    return request(AjpCommand.HEAD, url, **kwargs)


def options(url, **kwargs):
    r'''
    Sends an OPTIONS command to the servlet container.

    :param url: Url in the form `ajp://host[:port][/path]`
    :param \*\*kwargs: (optional) kwargs that request takes.
    :return: :class:`AjpResponse <AjpResponse>` object
    :rtype: ajp4py.AjpResponse
    '''
    return request(AjpCommand.OPTIONS, url, **kwargs)


def copy(url, **kwargs):
    r'''
    Sends a COPY (WebDav) command to the servlet container.

    :param url: Url in the form `ajp://host[:port][/path]`
    :param \*\*kwargs: (optional) kwargs that request takes.
    :return: :class:`AjpResponse <AjpResponse>` object
    :rtype: ajp4py.AjpResponse
    '''
    return request(AjpCommand.COPY, url, **kwargs)