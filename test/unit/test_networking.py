"""Some unit tests for Bladerunner's network utilities."""


import pytest

from bladerunner.networking import can_resolve
from bladerunner.networking import ips_in_subnet


@pytest.mark.parametrize(
    "network, expected",
    (
        ("10.0.0.0/30", ["10.0.0.1", "10.0.0.2"]),
        ("192.168.16.5/32", ["192.168.16.5"]),
        ("10.16.255.16/255.255.255.255", ["10.16.255.16"]),
        ("1.2.3.4", ["1.2.3.4"]),
    ),
    ids=("simple small", "slash 32", "expanded slash 32", "no mask required"),
)
def test_example_networks(network, expected):
    """Test some example network exact conversions."""

    assert ips_in_subnet(network) == expected


@pytest.mark.parametrize(
    "ipaddr, network",
    (
        ("1.2.3.4", "1.2.3.4/16"),
        ("10.17.29.130", "10.17.29.128/255.255.255.252"),
    ),
    ids=("big network", "expanded subnet"),
)
def test_in_network(ipaddr, network):
    """Ensure the ipaddress is in the network via ips_in_subnet."""

    assert ipaddr in ips_in_subnet(network)


@pytest.mark.parametrize(
    "ipaddr",
    (
        "10.10.256.10/24",
        "10.10.10.0/255.255.-2.0",
        "10.10.10.0/255.255.279.0",
        "10.9.8.0/-3",
        "10.9.8.0/34",
    ),
    ids=("invalid ip", "invalid subnet", "mask too big", "invalid slash",
         "oversized slash")
)
def test_invalid_returns_none(ipaddr):
    assert ips_in_subnet(ipaddr) is None


def test_can_resolve():
    """Basic test case for the can_resolve function."""

    assert can_resolve("google.com")
    assert not can_resolve("googly.boogly.doodley-do.1234abcd")
