"""
Utilities module for PacketTrail agent.
"""

import socket
import logging
from collections import namedtuple

import psutil


_logger = logging.getLogger(__name__)


Service = namedtuple('Service', ['interface', 'port', 'proto', 'name'])

def get_running_services():
    """ Returns a list of running Services.

    Note: Requires Root permissions to get a list of all running services."""

    net_ifaces = psutil.net_if_addrs()
    iface_port_tuples = set()

    services = set()
    for conn in psutil.net_connections(kind='inet'):
        if conn.type == socket.SocketKind.SOCK_STREAM:
            proto = 'tcp'
        elif conn.type == socket.SocketKind.SOCK_DGRAM:
            proto = 'udp'
        else:
            proto = ''
        if conn.status == 'LISTEN':
            if conn.pid is not None:
                proc = psutil.Process(conn.pid)
                proc_dict = proc.as_dict(['name', 'exe'])
            else:
                _logger.warning("Ignoring Service(Proto: %s, Port: %d)",
                        proto, conn.laddr.port)
                continue

            local_ip = conn.laddr.ip
            if local_ip in ('127.0.0.1', '::1'):
                interface_name = 'lo'
            elif local_ip in ('0.0.0.0', '::'):
                interface_name = 'any'
            else:
                for iface_name, addrs in net_ifaces.items():
                    interface_name = ''
                    for addr in addrs:
                        if local_ip == addr.address:
                            interface_name = iface_name
                            break
                    if interface_name:
                        break
                else:
                    interface_name = 'lo'

            s = Service(interface_name, conn.laddr.port, proto, proc_dict['name'])
            services.add(s)

    return [s._asdict() for s in services]

if __name__ == '__main__':
    print(get_running_services())

