'''
utils.py
========

General-purpose utilities that are not categorized by any other module.
'''
import struct
from io import BytesIO


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


def data_to_bytes(data):
    '''
    Returns a BytesIO type whose content is the byte representation
    of the given type.

    :param data: the data to convert to bytes.
    :return: a BytesIO object.
    '''
    request_data = None
    if data is None:
        request_data = BytesIO(b'')
    elif isinstance(data, str):
        request_data = BytesIO(bytearray(data, 'utf-8'))
    else:
        request_data = BytesIO(data)
    return request_data
