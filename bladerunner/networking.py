"""Bladerunner networking functions."""


import socket


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


def _quadrant_to_ip(quadrant):
    """Convert a single binary quadrant to string base 10 integer."""

    return str(int(quadrant, 2))


def _quadrant_to_binary(quadrant):
    """Convert a single quandrant to a binary string."""

    ip_as_int = int(str(quadrant))
    if 0 <= ip_as_int <= 255:
        return bin(ip_as_int)[2:].rjust(8, str(0))


def _ip_to_binary(ip_addr):
    """Convert a dotted quad IP address to a binary string representation."""

    full_binary = []
    for quadrant in ip_addr.split("."):
        quad_binary = _quadrant_to_binary(quadrant)

        if not quad_binary:
            return None

        full_binary.append(quad_binary)

    return "{0:b}".format(int("".join(full_binary), 2)).rjust(32, str(0))


def _binary_to_ip(binary):
    """Convert an binary IP address to dotted quads."""

    ip_address = []
    for quadrant in range(0, len(binary), 8):
        ip_address.append(_quadrant_to_ip(binary[quadrant:quadrant + 8]))
    return ".".join(ip_address)


def _subnet_to_binary(subnet):
    """Convert a CIDR-ish subnet to it's binary representation.

    Args:
        subnet: string, something like N.N.N.N/NN or N.N.N.N/N.N.N.N

    Returns:
        a tuple of binary representations, (network, netmask)
    """

    try:
        net, mask = subnet.split("/")
    except ValueError:
        return None, None

    if "." not in mask:
        mask = int(mask)
        if 0 <= mask <= 32:
            binary_mask = ("1" * mask).ljust(32, "0")
        else:
            # invalid mask size, not that a /0 is much safer...
            return None, None
    else:
        binary_mask = _ip_to_binary(mask)

    return _ip_to_binary(net), binary_mask


def ips_in_subnet(subnet):
    """Given a CIDR-ish network address, return all member IPs.

    Args:
        subnet: string, something like N.N.N.N/NN or N.N.N.N/N.N.N.N

    Returns:
        list of IPv4 addresses without masks
    """

    binary_net, binary_mask = _subnet_to_binary(subnet)
    if binary_mask is None or binary_net is None:
        return None

    for i in range(32):
        if binary_mask[i] != "1":
            subnet_range = int("1" * (32 - i), 2)
            network_section = binary_net[:i]
            break
    else:
        # catches providing a /32 subnet mask, just return the network as an IP
        return [_binary_to_ip(binary_net)]

    members = []
    for ip_ in range(1, subnet_range):  # skip the network address
        ip_ = bin(ip_)[2:].rjust(32 - len(network_section), str(0))
        members.append(_binary_to_ip("{0}{1}".format(network_section, ip_)))

    return members
