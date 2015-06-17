"""Bladerunner networking functions."""


from six import u

import socket
import ipaddress


def can_resolve(target):
    """Tries to look up a hostname then bind to that IP address.

    Args:
        target: a hostname or IP address as a string

    Returns:
        True if the target is resolvable to a valid IP address
    """

    try:
        socket.getaddrinfo(target, None)
        return True
    except socket.error:
        return False


def ips_in_subnet(subnet):
    """Given a CIDR-ish network address, return all member IPs.

    Args:
        subnet: string, something like N.N.N.N/NN or N.N.N.N/N.N.N.N

    Returns:
        list of IPv4 addresses without masks
    """

    try:
        interface = ipaddress.ip_interface(u(subnet))
    except ValueError:
        return None
    else:
        return [str(host) for host in interface.network.hosts()] or \
               [str(interface.network.network_address)]
