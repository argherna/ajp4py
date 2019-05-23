'''
ajp_types.py
'''
from enum import Enum, IntEnum

# No magic numbers! I **HATE** them! Use these enums instead.

DEFAULT_AJP_SERVER_PORT = 8009

class AjpPacketHeadersToContainer(IntEnum):
    ''' Enumeration of the packets sent from a web server to a
    servlet container.

    See https://tomcat.apache.org/connectors-doc/ajp/ajpv13a.html.
    '''
    # Begin the request-processing cycle with the following data
    FORWARD_REQUEST = 0x02

    # The web server asks the container to shut itself down.
    SHUTDOWN = 0x07

    # The web server asks the container to take control (secure
    # login phase).
    PING = 0x08

    # The web server asks the container to respond quickly with
    # a CPong.
    CPING = 0x0A


class AjpPacketHeadersFromContainer(IntEnum):
    ''' Enumeration of the packets sent from a servlet container
    to a web server.

    See https://tomcat.apache.org/connectors-doc/ajp/ajpv13a.html.
    '''
    # Send a chunk of the body from the servlet container to the
    # web server (and presumably, onto the browser).
    SEND_BODY_CHUNK = 0x03

    # Send the response headers from the servlet container to the
    # web server (and presumably, onto the browser).
    SEND_HEADERS = 0x04

    # Marks the end of the response (and thus the request-handling
    # cycle).
    END_RESPONSE = 0x05

    # Get further data from the request if it hasn't all been
    # transferred yet.
    GET_BODY_CHUNK = 0x06

    # The reply to a CPing request.
    CPONG_REPLY = 0x09


class AjpCommand(IntEnum):
    ''' Enumeration of the HTTP methods/AJP Commands.

    See http://tomcat.apache.org/connectors-doc/ajp/ajpv13a.html#method.
    '''
    OPTIONS = 0x01
    GET = 0x02
    HEAD = 0x03
    POST = 0x04
    PUT = 0x05
    DELETE = 0x06
    TRACE = 0x07
    PROPFIND = 0x08
    PROPPATCH = 0x09
    MKCOL = 0x0A
    COPY = 0x0B
    MOVE = 0x0C
    LOCK = 0x0D
    UNLOCK = 0x0E
    ACL = 0x0F
    REPORT = 0x10
    VERSION_CONTROL = 0x11
    CHECKIN = 0x12
    CHECKOUT = 0x13
    UNCHECKOUT = 0x14
    SEARCH = 0x15
    MKWORKSPACE = 0x16
    UPDATE = 0x17
    LABEL = 0x18
    MERGE = 0x19
    BASELINE_CONTROL = 0x1A
    MKACTIVITY = 0x1B


class AjpHeader(IntEnum):
    ''' Enumeration of AJP headers.

    See http://tomcat.apache.org/connectors-doc/ajp/ajpv13a.html#Headers.
    '''
    SC_REQ_ACCEPT = 0xA001
    SC_REQ_ACCEPT_CHARSET = 0xA002
    SC_REQ_ACCEPT_ENCODING = 0xA003
    SC_REQ_ACCEPT_LANGUAGE = 0xA004
    SC_REQ_AUTHORIZATION = 0xA005
    SC_REQ_CONNECTION = 0xA006
    SC_REQ_CONTENT_TYPE = 0xA007
    SC_REQ_CONTENT_LENGTH = 0xA008
    SC_REQ_COOKIE = 0xA009
    SC_REQ_COOKIE2 = 0xA00A
    SC_REQ_HOST = 0xA00B
    SC_REQ_PRAGMA = 0xA00C
    SC_REQ_REFERER = 0xA00D
    SC_REQ_USER_AGENT = 0xA00E


class AjpAttribute(Enum):
    ''' Enumeration of AJP attributes.

    Attributes have a code and a name that is used by the protocol.
    Additional meta information is included with each attribute like
    if it is optional by the protocol and any notes specified by
    the protocol.

    See http://tomcat.apache.org/connectors-doc/ajp/ajpv13a.html#Attributes.
    '''
    CONTEXT = (0x01, 'context', True, 'Not currently implemented')
    SERVLET_PATH = (0x02, 'servlet_path', True, 'Not currently implemented')
    REMOTE_USER = (0x03, 'remote_user')
    AUTH_TYPE = (0x04, 'auth_type')
    QUERY_STRING = (0x05, 'query_string')
    ROUTE = (0x06, 'route')
    SSL_CERT = (0x07, 'ssl_cert')
    SSL_CIPHER = (0x08, 'ssl_cipher')
    SSL_SESSION = (0x09, 'ssl_session')
    REQ_ATTRIBUTE = (0x0A, 'req_attribute', True,
                     'Name (the name of the attribute follows)')
    SSL_KEY_SIZE = (0x0B, 'ssl_key_size')
    SECRET = (0x0C, 'secret')
    STORED_METHOD = (0x0D, 'stored_method')
    ARE_DONE = (0xFF, 'are_done', False)

    def __init__(self, ajp_code, ajp_attr_name,
                 is_optional=True, ajp_note=None):
        self.ajp_code = ajp_code
        self.ajp_attr_name = ajp_attr_name
        self.is_optional = is_optional
        self.ajp_note = ajp_note

    @property
    def code(self):
        'Returns the AJP Attribute code.'
        return self.ajp_code

    @property
    def attr_name(self):
        'Returns the AJP Attribute name.'
        return self.ajp_attr_name

    @property
    def information(self):
        '''Returns AJP Attribute information string.

        The information string is formatted as follows:

        * `?<name>` - if the Attribute is optional for implementation.
        * `<name>` - if the Attribute is required for implementation.
        '''
        if self.is_optional:
            return '?{0}'.format(self.ajp_attr_name)

        return self.ajp_attr_name

    @property
    def note(self):
        '''Returns this AJP Attribute's note.

        This is meta information only.
        '''
        if self.ajp_note is None:
            return ''

        return self.ajp_note

    @property
    def optional(self):
        'Returns `True` if this Attribute is optional.'
        return self.is_optional

    def __str__(self):
        return self.ajp_attr_name


class AjpSendHeaders(Enum):
    '''Enumeration of known response headers.

    See https://tomcat.apache.org/connectors-doc/ajp/ajpv13a.html#Send_Headers.
    '''
    CONTENT_TYPE = 0xA001
    CONTENT_LANGUAGE = 0xA002
    CONTENT_LENGTH = 0xA003
    DATE = 0xA004
    LAST_MODIFIED = 0xA005
    LOCATION = 0xA006
    SET_COOKIE = 0xA007
    SET_COOKIE2 = 0xA008
    SERVLET_ENGINE = 0xA009
    STATUS = 0xA00A
    WWW_AUTHENTICATE = 0xA00B


class AjpStatus(Enum):
    '''Enumeration of AJP status codes.

    These are the same as an HTTP status code.

    See https://tomcat.apache.org/connectors-doc/ajp/ajpv13a.html#Send_Headers.

    See https://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html.
    '''

    # Unexpected values (does not conform to HTTP standard, but makes
    # the code not give back None types)
    UNKNOWN = (0, 'Unknown Status')

    # Informational 1xx
    CONTINUE = (100, 'Continue')
    SWITCHING_PROTOCOLS = (101, 'Switching Protocols')
    PROCESSING = (102, 'Processing')

    # Successful 2xx
    OK = (200, 'OK')
    CREATED = (201, 'Created')
    ACCEPTED = (202, 'Accepted')
    NON_AUTHORITATIVE_INFORMATION = (203, 'Non-authoritative Information')
    NO_CONTENT = (204, 'No Content')
    RESET_CONTENT = (205, 'Reset Content')
    PARTIAL_CONTENT = (206, 'Partial Content')
    MULTI_STATUS = (207, 'Multi-Status')
    ALREADY_REPORTED = (208, 'Already Reported')
    IM_USED = (226, 'IM Used')

    # Redirection 3xx
    MULTIPLE_CHOICES = (300, 'Multiple Choices')
    MOVED_PERMANENTLY = (301, 'Moved Permanently')
    FOUND = (302, 'Found')
    SEE_OTHER = (303, 'See Other')
    NOT_MODIFIED = (304, 'Not Modified')
    USE_PROXY = (305, 'Use Proxy')
    TEMPORARY_REDIRECT = (307, 'Temporary Redirect')
    PERMANENT_REDIRECT = (308, 'Permanent Redirect')

    # Client error 4xx
    BAD_REQUEST = (400, 'Bad Request')
    UNAUTHORIZED = (401, 'Unauthorized')
    PAYMENT_REQUIRED = (402, 'Payment Required')
    FORBIDDEN = (403, 'Forbidden')
    NOT_FOUND = (404, 'Not Found')
    METHOD_NOT_ALLOWED = (405, 'Method Not Allowed')
    NOT_ACCEPTABLE = (406, 'Not Acceptable')
    PROXY_AUTHENTICATION_REQUIRED = (407, 'Proxy Authentication Required')
    REQUEST_TIMEOUT = (408, 'Request Timeout')
    CONFLICT = (409, 'Conflict')
    GONE = (410, 'Gone')
    LENGTH_REQUIRED = (411, 'Length Required')
    PRECONDITION_FAILED = (412, 'Precondition Failed')
    PAYLOAD_TOO_LARGE = (413, 'Payload Too Large')
    REQUEST_URI_TOO_LONG = (414, 'Request-URI Too Long')
    UNSUPPORTED_MEDIA_TYPE = (415, 'Unsupported Media Type')
    REQUESTED_RANGE_NOT_SATISFIABLE = (416, 'Requested Range Not Satisfiable')
    EXPECTATION_FAILED = (417, 'Expectation Failed')
    IM_A_TEAPOT = (418, 'I\'m a teapot')
    MISDIRECTED_REQUEST = (421, 'Misdirected Request')
    UNPROCESSABLE_ENTITY = (422, 'Unprocessable Entity')
    LOCKED = (423, 'Locked')
    FAILED_DEPENDENCY = (424, 'Failed Dependency')
    UPGRADE_REQUIRED = (426, 'Upgrade Required')
    PRECONDITION_REQUIRED = (428, 'Precondition Required')
    TOO_MANY_REQUESTS = (429, 'Too Many Requests')
    REQUEST_HEADER_FIELDS_TOO_LARGE = (431, 'Request Header Fields Too Large')
    CONNECTION_CLOSED_WITHOUT_RESPONSE = (
        444, 'Connection Closed Without Response')
    UNAVAILABLE_FOR_LEGAL_REASONS = (451, 'Unavailable For Legal Reasons')
    CLIENT_CLOSED_REQUEST = (499, 'Client Closed Request')

    # Server error 5xx
    INTERNAL_SERVER_ERROR = (500, 'Internal Server Error')
    NOT_IMPLEMENTED = (501, 'Not Implemented')
    BAD_GATEWAY = (502, 'Bad Gateway')
    SERVICE_UNAVAILABLE = (503, 'Service Unavailable')
    GATEWAY_TIMEOUT = (504, 'Gateway Timeout')
    HTTP_VERSION_NOT_SUPPORTED = (505, 'HTTP Version Not Supported')
    VARIANT_ALSO_NEGOTIATES = (506, 'Variant Also Negotiates')
    INSUFFICIENT_STORAGE = (507, 'Insufficient Storage')
    LOOP_DETECTED = (508, 'Loop Detected')
    NOT_EXTENDED = (510, 'Not Extended')
    NETWORK_AUTHENTICATION_REQUIRED = (511, 'Network Authentication Required')
    NETWORK_CONNECT_TIMEOUT_ERROR = (599, 'Network Connect Timeout Error')

    def __init__(self, status_code, status_title):
        self.status_code = status_code
        self.status_title = status_title

    @property
    def code(self):
        'Return the AJP (HTTP) status code.'
        return self.status_code

    @property
    def description(self):
        'Return the AJP (HTTP) status description/title in upper case.'
        return self.status_title.upper()

    @property
    def title(self):
        'Returns the AJP (HTTP) status title.'
        return self.status_title

    def __str__(self):
        return '{0} {1}'.format(self.status_code, self.status_title)


# Server will give back a status code number. This dict will give back
# the enum type that we will work with in the code.
_STATUS_BY_CODE = {
    AjpStatus.CONTINUE.code: AjpStatus.CONTINUE,
    AjpStatus.SWITCHING_PROTOCOLS.code: AjpStatus.SWITCHING_PROTOCOLS,
    AjpStatus.PROCESSING.code: AjpStatus.PROCESSING,
    AjpStatus.OK.code: AjpStatus.OK,
    AjpStatus.CREATED.code: AjpStatus.CREATED,
    AjpStatus.ACCEPTED.code: AjpStatus.ACCEPTED,
    AjpStatus.NON_AUTHORITATIVE_INFORMATION.code: AjpStatus.NON_AUTHORITATIVE_INFORMATION,
    AjpStatus.NO_CONTENT.code: AjpStatus.NO_CONTENT,
    AjpStatus.RESET_CONTENT.code: AjpStatus.RESET_CONTENT,
    AjpStatus.PARTIAL_CONTENT.code: AjpStatus.PARTIAL_CONTENT,
    AjpStatus.MULTI_STATUS.code: AjpStatus.MULTI_STATUS,
    AjpStatus.ALREADY_REPORTED.code: AjpStatus.ALREADY_REPORTED,
    AjpStatus.IM_USED.code: AjpStatus.IM_USED,
    AjpStatus.MULTIPLE_CHOICES.code: AjpStatus.MULTIPLE_CHOICES,
    AjpStatus.MOVED_PERMANENTLY.code: AjpStatus.MOVED_PERMANENTLY,
    AjpStatus.FOUND.code: AjpStatus.FOUND,
    AjpStatus.SEE_OTHER.code: AjpStatus.SEE_OTHER,
    AjpStatus.NOT_MODIFIED.code: AjpStatus.NOT_MODIFIED,
    AjpStatus.USE_PROXY.code: AjpStatus.USE_PROXY,
    AjpStatus.TEMPORARY_REDIRECT.code: AjpStatus.TEMPORARY_REDIRECT,
    AjpStatus.PERMANENT_REDIRECT.code: AjpStatus.PERMANENT_REDIRECT,
    AjpStatus.BAD_REQUEST.code: AjpStatus.BAD_REQUEST,
    AjpStatus.UNAUTHORIZED.code: AjpStatus.UNAUTHORIZED,
    AjpStatus.PAYMENT_REQUIRED.code: AjpStatus.PAYMENT_REQUIRED,
    AjpStatus.FORBIDDEN.code: AjpStatus.FORBIDDEN,
    AjpStatus.NOT_FOUND.code: AjpStatus.NOT_FOUND,
    AjpStatus.METHOD_NOT_ALLOWED.code: AjpStatus.METHOD_NOT_ALLOWED,
    AjpStatus.NOT_ACCEPTABLE.code: AjpStatus.NOT_ACCEPTABLE,
    AjpStatus.PROXY_AUTHENTICATION_REQUIRED.code: AjpStatus.PROXY_AUTHENTICATION_REQUIRED,
    AjpStatus.REQUEST_TIMEOUT.code: AjpStatus.REQUEST_TIMEOUT,
    AjpStatus.CONFLICT.code: AjpStatus.CONFLICT,
    AjpStatus.GONE.code: AjpStatus.GONE,
    AjpStatus.LENGTH_REQUIRED.code: AjpStatus.LENGTH_REQUIRED,
    AjpStatus.PRECONDITION_FAILED.code: AjpStatus.PRECONDITION_FAILED,
    AjpStatus.PAYLOAD_TOO_LARGE.code: AjpStatus.PAYLOAD_TOO_LARGE,
    AjpStatus.REQUEST_URI_TOO_LONG.code: AjpStatus.REQUEST_URI_TOO_LONG,
    AjpStatus.UNSUPPORTED_MEDIA_TYPE.code: AjpStatus.UNSUPPORTED_MEDIA_TYPE,
    AjpStatus.REQUESTED_RANGE_NOT_SATISFIABLE.code: AjpStatus.REQUESTED_RANGE_NOT_SATISFIABLE,
    AjpStatus.EXPECTATION_FAILED.code: AjpStatus.EXPECTATION_FAILED,
    AjpStatus.IM_A_TEAPOT.code: AjpStatus.IM_A_TEAPOT,
    AjpStatus.MISDIRECTED_REQUEST.code: AjpStatus.MISDIRECTED_REQUEST,
    AjpStatus.UNPROCESSABLE_ENTITY.code: AjpStatus.UNPROCESSABLE_ENTITY,
    AjpStatus.LOCKED.code: AjpStatus.LOCKED,
    AjpStatus.FAILED_DEPENDENCY.code: AjpStatus.FAILED_DEPENDENCY,
    AjpStatus.UPGRADE_REQUIRED.code: AjpStatus.UPGRADE_REQUIRED,
    AjpStatus.PRECONDITION_REQUIRED.code: AjpStatus.PRECONDITION_REQUIRED,
    AjpStatus.TOO_MANY_REQUESTS.code: AjpStatus.TOO_MANY_REQUESTS,
    AjpStatus.REQUEST_HEADER_FIELDS_TOO_LARGE.code: AjpStatus.REQUEST_HEADER_FIELDS_TOO_LARGE,
    AjpStatus.CONNECTION_CLOSED_WITHOUT_RESPONSE.code: AjpStatus.CONNECTION_CLOSED_WITHOUT_RESPONSE,
    AjpStatus.UNAVAILABLE_FOR_LEGAL_REASONS.code: AjpStatus.UNAVAILABLE_FOR_LEGAL_REASONS,
    AjpStatus.CLIENT_CLOSED_REQUEST.code: AjpStatus.CLIENT_CLOSED_REQUEST,
    AjpStatus.INTERNAL_SERVER_ERROR.code: AjpStatus.INTERNAL_SERVER_ERROR,
    AjpStatus.NOT_IMPLEMENTED.code: AjpStatus.NOT_IMPLEMENTED,
    AjpStatus.BAD_GATEWAY.code: AjpStatus.BAD_GATEWAY,
    AjpStatus.SERVICE_UNAVAILABLE.code: AjpStatus.SERVICE_UNAVAILABLE,
    AjpStatus.GATEWAY_TIMEOUT.code: AjpStatus.GATEWAY_TIMEOUT,
    AjpStatus.HTTP_VERSION_NOT_SUPPORTED.code: AjpStatus.HTTP_VERSION_NOT_SUPPORTED,
    AjpStatus.VARIANT_ALSO_NEGOTIATES.code: AjpStatus.VARIANT_ALSO_NEGOTIATES,
    AjpStatus.INSUFFICIENT_STORAGE.code: AjpStatus.INSUFFICIENT_STORAGE,
    AjpStatus.LOOP_DETECTED.code: AjpStatus.LOOP_DETECTED,
    AjpStatus.NOT_EXTENDED.code: AjpStatus.NOT_EXTENDED,
    AjpStatus.NETWORK_AUTHENTICATION_REQUIRED.code: AjpStatus.NETWORK_AUTHENTICATION_REQUIRED,
    AjpStatus.NETWORK_CONNECT_TIMEOUT_ERROR.code: AjpStatus.NETWORK_CONNECT_TIMEOUT_ERROR
}


def lookup_status_by_code(ajp_code):
    'Returns the AjpStatus of the given code or None if not found.'
    try:
        return _STATUS_BY_CODE[ajp_code]
    except KeyError:
        return AjpStatus.UNKNOWN


class AjpRequestDirection(Enum):
    'Enumeration of the request directions.'
    WEB_SERVER_TO_SERVLET_CONTAINER = ((0x12, 0x34))
    SERVLET_CONTAINER_TO_WEB_SERVER = ((0x41, 0x42))

    def __init__(self, *first_bytes):
        self._first_bytes = first_bytes

    @property
    def first_bytes(self):
        'Returns the first bytes for serializing the request packet'
        return self._first_bytes


def header_case(enum_name):
    'Converts the given name from ENUM_CASE to Header-Case'
    hdr_case = enum_name.title()
    return str(hdr_case).replace('_', '-')
