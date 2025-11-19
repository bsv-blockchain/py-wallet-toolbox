"""Stamp log utilities for debugging and tracing.

This module provides utilities for stamping logs with timestamps and
formatting log output for debugging purposes, mirroring TypeScript's stampLog.ts.

Reference: toolbox/ts-wallet-toolbox/src/utility/stampLog.ts
"""

from datetime import UTC, datetime
from typing import Any


def stamp_log(log: str | None | dict[str, Any], line_to_add: str) -> str | None:
    """Add a timestamped line to a log string or object.

    If a log is being kept, add a time stamped line.

    Args:
        log: Optional timestamped log string, or an object with a 'log' property
        line_to_add: Content to add to line

    Returns:
        Extended log with timestamped line_to_add and newline, or None

    Reference: stampLog(log: string | undefined | { log?: string }, lineToAdd: string)
    """
    now = datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    add = f"{now} {line_to_add}\n"

    # Handle object with log property
    if isinstance(log, dict) and isinstance(log.get("log"), str):
        log["log"] = log["log"] + add
        return log["log"]

    # Handle string log
    if isinstance(log, str):
        return log + add

    return None


def stamp_log_format(log: str | None = None) -> str:
    """Format a timestamped log, replacing timestamps with delta milliseconds.

    Looks for two network crossings and adjusts clock for clock skew if found.
    Assumes log built by repeated calls to `stamp_log`.

    Args:
        log: Timestamped log string (each line starts with ISO timestamp, space, rest of line, \\n)

    Returns:
        Reformatted multi-line event log with delta times

    Reference: stampLogFormat(log?: string)
    """
    if not isinstance(log, str):
        return ""

    log_lines = log.split("\n")
    data: list[dict[str, Any]] = []
    last = 0
    new_clocks: list[int] = []

    for line in log_lines:
        space_at = line.find(" ")
        if space_at > -1:
            try:
                when = int(datetime.fromisoformat(line[:space_at].replace("Z", "+00:00")).timestamp() * 1000)
                rest = line[space_at + 1 :]
                delta = when - (last or when)
                new_clock = "**NETWORK**" in rest
                if new_clock:
                    new_clocks.append(len(data))
                data.append({"when": when, "rest": rest, "delta": delta, "newClock": new_clock})
                last = when
            except ValueError as e:
                # If any line has an invalid timestamp, raise error
                raise ValueError(f"Invalid timestamp in log line: {line}") from e

    if not data:
        return ""

    total = data[-1]["when"] - data[0]["when"]

    # Adjust for paired network crossing times and clock skew between clocks
    if len(new_clocks) % 2 == 0 and new_clocks:
        network = total
        last_new_clock = 0
        for new_clock in new_clocks:
            if new_clock > 0:
                network -= data[new_clock - 1]["when"] - data[last_new_clock]["when"]
            last_new_clock = new_clock

        if last_new_clock < len(data):
            network -= data[-1]["when"] - data[last_new_clock]["when"]

        networks = len(new_clocks)
        for new_clock in new_clocks:
            n = network // networks if networks > 1 else network
            data[new_clock]["delta"] = n
            network -= n
            networks -= 1

    # Format output
    start_time = datetime.fromtimestamp(data[0]["when"] / 1000, tz=UTC)
    log2 = f"{start_time.isoformat(timespec='milliseconds').replace('+00:00', 'Z')} Total = {total} msecs\n"

    for d in data:
        df = str(d["delta"])
        df = " " * (8 - len(df)) + df
        log2 += f"{df} {d['rest']}\n"

    return log2
