from ctypes import *
import socket
import struct


class socketaddr_in_t(Structure):
    _fields_ = [
        ("sin_family", c_short),
        ("sin_port", c_ushort),
        ("sin_addr.s_addr", c_uint32)
    ]

    _values_ = [
        ("sin_family", [
            (0, 'AF_UNSPEC'),
            (1, 'AF_UNIX'),
            (2, 'AF_INET'),
            (3, 'AF_AX25'),
            (4, 'AF_IPX'),
            (5, 'AF_APPLETALK'),
            (6, 'AF_NETROM'),
            (7, 'AF_BRIDGE'),
            (8, 'AF_AAL5'),
            (9, 'AF_X25'),
            (10, 'AF_INET6'),
            (12, 'AF_MAX')
        ]),
        ("sin_port", lambda p: socket.ntohs(p)),
        ("sin_addr.s_addr", lambda addr: socket.inet_ntoa(struct.pack('<I', addr)))
    ]
