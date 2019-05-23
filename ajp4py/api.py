'''
api.py
======

Implements the API for sending AJP requests.
'''

from urllib.parse import urlparse

from .ajp_types import DEFAULT_AJP_SERVER_PORT, AjpCommand
from .models import AjpForwardRequest, AjpAttribute
from .protocol import AjpConnection


def request(ajp_cmd, url, params=None, headers=None,
            attributes=None):
    r'''
    Send a generic request to the servlet container.

    :type ajp_cmd: An AjpCommand (equiv. to HTTP method)
    :param url: Url in the form `ajp://host[:port][/path]`
    :param params: (optional) Dictionary of parameters that will
        be converted into the query string.
    :param headers: (optional) Dictionary of request headers
    :param attributes: (optional) Dictionary of request attributes
    :return: :class:`AjpResponse <AjpResponse>` object
    :rtype: ajp4py.AjpResponse
    '''
    parsed_url = urlparse(url)
    host_name = parsed_url.netloc.split(':')[0]
    port = parsed_url.port or DEFAULT_AJP_SERVER_PORT

    if params:
        q_params = ['='.join([nm, val]) for nm, val in params.items()]
        if not attributes:
            attributes = {}
        attributes[AjpAttribute.QUERY_STRING] = '&'.join(q_params)

    ajp_req = AjpForwardRequest(method=ajp_cmd,
                                req_uri=parsed_url.path,
                                remote_host=host_name,
                                request_headers=headers or {},
                                attributes=attributes or {})

    with AjpConnection(host_name, port) as ajp_conn:
        ajp_resp = ajp_conn.send_and_receive(ajp_req)

    return ajp_resp


def get(url, params=None, **kwargs):
    r'''
    Sends a GET command to the servlet container.

    :param url: Url in the form `ajp://host[:port][/path]`
    :param params: (optional) Dictionary of parameters that will
        be converted into the query string.
    :param headers: (optional) Dictionary of request headers
    :param attributes: (optional) Dictionary of request attributes
    :return: :class:`AjpResponse <AjpResponse>` object
    :rtype: ajp4py.AjpResponse
    '''
    return request(AjpCommand.GET, url, params=params, **kwargs)


def post():
    pass


def put():
    pass


def delete():
    pass


def head():
    pass


def options():
    pass


def trace():
    pass
