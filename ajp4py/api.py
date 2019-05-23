'''
api.py
======

Implements the API for sending AJP requests.
'''

from urllib.parse import urlparse

from . import AJP4PY_LOGGER
from .ajp_types import DEFAULT_AJP_SERVER_PORT, AjpCommand, AjpHeader
from .models import AjpForwardRequest
from .protocol import connect, disconnect, send_and_receive


def request(ajp_cmd, url, request_headers=None,
            attributes=None):
    '''
    Send a generic request to the servlet container.
    '''
    parsed_url = urlparse(url)
    host_name = parsed_url.netloc.split(':')[0]

    port = parsed_url.port or DEFAULT_AJP_SERVER_PORT

    ajp_req = AjpForwardRequest(method=ajp_cmd,
                                req_uri=parsed_url.path,
                                remote_host=host_name,
                                request_headers=request_headers or {},
                                attributes=attributes or {})

    ajp_conn = connect(host_name, port)
    ajp_resp = send_and_receive(ajp_conn, ajp_req)
    disconnect(ajp_conn)

    return ajp_resp


def get(url, **kwargs):
    '''
    Sends a GET command to the servlet container.
    '''
    return request(AjpCommand.GET, url, **kwargs)


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
