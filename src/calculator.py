"""Bandwidth maths and threshold-based alert classification (pure functions)."""
from typing import Optional

NORMAL, WARNING, CRITICAL = "NORMAL", "WARNING", "CRITICAL"
_SEVERITY = {NORMAL: 0, WARNING: 1, CRITICAL: 2}


def compute_rate(prev_value: int, curr_value: int, elapsed: float) -> float:
    """Units per second from two cumulative counter readings.

    A counter that goes backwards (reset/wrap) or a non-positive time gap gives 0.
    """
    if elapsed <= 0 or curr_value < prev_value:
        return 0.0
    return (curr_value - prev_value) / elapsed


def bytes_to_kbps(bytes_per_sec: float) -> float:
    """Kilobytes per second (1 KB = 1024 bytes)."""
    return bytes_per_sec / 1024.0


def bytes_to_mbps(bytes_per_sec: float) -> float:
    """Megabits per second (1 Mbps = 1,000,000 bits/s)."""
    return bytes_per_sec * 8 / 1_000_000


def bytes_to_mb(total_bytes: int) -> float:
    return total_bytes / (1024 * 1024)


def utilization_percent(up_bps: float, down_bps: float,
                        capacity_mbps: Optional[float]) -> Optional[float]:
    """Link utilisation in %, or None if the OS gave no link capacity.

    Links are full duplex, so the busier direction is compared with capacity.
    """
    if not capacity_mbps or capacity_mbps <= 0:
        return None
    return max(bytes_to_mbps(up_bps), bytes_to_mbps(down_bps)) / capacity_mbps * 100.0


def classify(up_bps: float, down_bps: float, util_pct: Optional[float], cfg) -> str:
    """Return NORMAL / WARNING / CRITICAL.

    Rule 1: combined throughput (up + down, in Mbps) against warning_mbps / critical_mbps.
    Rule 2: only if utilisation is known, compare it with the utilisation thresholds.
    The more severe result wins.
    """
    total_mbps = bytes_to_mbps(up_bps + down_bps)
    level = NORMAL
    if total_mbps >= cfg.critical_mbps:
        level = CRITICAL
    elif total_mbps >= cfg.warning_mbps:
        level = WARNING
    if util_pct is not None:
        util_level = NORMAL
        if util_pct >= cfg.critical_utilization_percent:
            util_level = CRITICAL
        elif util_pct >= cfg.warning_utilization_percent:
            util_level = WARNING
        if _SEVERITY[util_level] > _SEVERITY[level]:
            level = util_level
    return level


def message_for(status: str) -> str:
    return {
        NORMAL: "Network traffic is normal.",
        WARNING: "WARNING: High bandwidth usage detected!",
        CRITICAL: "CRITICAL: Very high traffic - possible congestion!",
    }[status]
