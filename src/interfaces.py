"""Network interface discovery and raw byte-counter access (via psutil)."""
import socket
from dataclasses import dataclass
from typing import List, Optional

import psutil


class InterfaceError(Exception):
    """Raised when an interface is missing or its counters cannot be read."""


@dataclass
class InterfaceInfo:
    name: str
    ipv4: Optional[str]
    is_up: bool
    speed_mbps: Optional[int]  # None when the OS does not report a link speed
    has_counters: bool


@dataclass
class Counters:
    bytes_sent: int
    bytes_recv: int
    packets_sent: int
    packets_recv: int
    errors: int  # errin + errout
    drops: int   # dropin + dropout


def list_interfaces() -> List[InterfaceInfo]:
    addrs = psutil.net_if_addrs()
    stats = psutil.net_if_stats()
    counters = psutil.net_io_counters(pernic=True)
    result = []
    for name, addr_list in addrs.items():
        ipv4 = next((a.address for a in addr_list if a.family == socket.AF_INET), None)
        st = stats.get(name)
        speed = st.speed if st and st.speed and st.speed > 0 else None
        result.append(InterfaceInfo(name, ipv4, bool(st and st.isup), speed, name in counters))
    return sorted(result, key=lambda i: i.name)


def select_interface(preferred: Optional[str] = "auto") -> InterfaceInfo:
    """Return the interface to monitor, or raise InterfaceError with a helpful message."""
    interfaces = list_interfaces()
    if preferred and preferred != "auto":
        for info in interfaces:
            if info.name == preferred:
                if not info.has_counters:
                    raise InterfaceError(f"Interface '{preferred}' has no traffic counters.")
                return info
        names = ", ".join(i.name for i in interfaces) or "none"
        raise InterfaceError(f"Interface '{preferred}' not found. Available interfaces: {names}")

    usable = [i for i in interfaces if i.is_up and i.has_counters
              and i.ipv4 and not i.ipv4.startswith("127.")]
    if not usable:  # fall back to any non-loopback interface that is up
        usable = [i for i in interfaces if i.is_up and i.has_counters
                  and not (i.ipv4 or "").startswith("127.") and not i.name.startswith("lo")]
    if not usable:
        raise InterfaceError("No active network interface found. Connect to Wi-Fi/Ethernet "
                             "or run: python3 main.py --list")
    for info in usable:  # macOS Wi-Fi/Ethernet is normally en0
        if info.name == "en0":
            return info
    totals = psutil.net_io_counters(pernic=True)
    return max(usable, key=lambda i: totals[i.name].bytes_sent + totals[i.name].bytes_recv)


def read_counters(name: str) -> Counters:
    io = psutil.net_io_counters(pernic=True)
    if name not in io:
        raise InterfaceError(f"Interface '{name}' is no longer available.")
    c = io[name]
    return Counters(c.bytes_sent, c.bytes_recv, c.packets_sent, c.packets_recv,
                    c.errin + c.errout, c.dropin + c.dropout)
