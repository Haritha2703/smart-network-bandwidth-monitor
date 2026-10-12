"""Terminal rendering."""
import sys

_COLORS = {"NORMAL": "\033[32m", "WARNING": "\033[33m", "CRITICAL": "\033[31m"}
_RESET = "\033[0m"
BAR = "=" * 52
THIN = "-" * 52


def supports_color() -> bool:
    return sys.stdout.isatty()


def colorize(text, status, enabled):
    return f"{_COLORS.get(status, '')}{text}{_RESET}" if enabled else text


def render(state, events, color=False) -> str:
    util = state["utilization"]
    util_text = (f"{util:.1f} %" if util is not None
                 else "Unavailable (OS reports no link speed)")
    status = colorize(state["status"], state["status"], color)
    lines = [
        BAR,
        " SMART NETWORK BANDWIDTH MONITORING AND ALERT SYSTEM",
        BAR,
        "Monitoring Status : ACTIVE",
        f"Network Interface : {state['interface']}",
        f"IP Address        : {state['ip'] or 'Not available'}",
        f"Link Capacity     : {state['capacity_text']}",
        "",
        "---------------- NETWORK STATISTICS ----------------",
        f"Upload Speed      : {state['up_kbps']:.2f} KB/s  ({state['up_mbps']:.3f} Mbps)",
        f"Download Speed    : {state['down_kbps']:.2f} KB/s  ({state['down_mbps']:.3f} Mbps)",
        f"Total Data Sent   : {state['sent_mb']:.2f} MB",
        f"Total Data Received: {state['recv_mb']:.2f} MB",
        f"Packets/s Out/In  : {state['pps_out']:.0f} / {state['pps_in']:.0f}",
        f"Errors / Drops    : {state['errors']} / {state['drops']} (since start)",
        f"Bandwidth Usage   : {util_text}",
        f"Alert Status      : {status}",
        THIN,
        "",
    ]
    lines.extend(events if events else ["Waiting for first measurement..."])
    lines += ["", "Monitoring continues... Press CTRL+C to stop."]
    return "\n".join(lines)


def print_interfaces(interfaces):
    print(f"{'Interface':<14}{'Status':<8}{'IPv4 address':<18}{'Link speed'}")
    print("-" * 56)
    for i in interfaces:
        speed = f"{i.speed_mbps} Mbps" if i.speed_mbps else "unknown"
        print(f"{i.name:<14}{'UP' if i.is_up else 'DOWN':<8}{i.ipv4 or '-':<18}{speed}")
