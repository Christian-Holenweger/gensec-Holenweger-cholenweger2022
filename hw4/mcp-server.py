"""MCP server that provides tools for exploring simulated security login events.

The event data is fictional and uses documentation-only IP address ranges. Run
this file with Python to start the server over the standard input/output
transport used by MCP clients.
"""

from mcp.server.fastmcp import FastMCP


mcp = FastMCP("security-investigation-assistant")

# A small, fictional set of login events for demonstrations and coursework.
# IP addresses are from ranges reserved for documentation and examples.
SECURITY_EVENTS = [
    {
        "timestamp": "2026-10-20T08:14:22Z",
        "username": "analyst1",
        "ip_address": "192.0.2.10",
        "successful": True,
    },
    {
        "timestamp": "2026-10-20T08:31:05Z",
        "username": "j.smith",
        "ip_address": "198.51.100.24",
        "successful": False,
    },
    {
        "timestamp": "2026-10-20T08:32:17Z",
        "username": "j.smith",
        "ip_address": "198.51.100.24",
        "successful": False,
    },
    {
        "timestamp": "2026-10-20T08:34:49Z",
        "username": "admin",
        "ip_address": "198.51.100.24",
        "successful": False,
    },
    {
        "timestamp": "2026-10-20T09:02:11Z",
        "username": "m.chen",
        "ip_address": "203.0.113.7",
        "successful": True,
    },
    {
        "timestamp": "2026-10-20T09:18:36Z",
        "username": "service_backup",
        "ip_address": "203.0.113.44",
        "successful": False,
    },
    {
        "timestamp": "2026-10-20T09:20:02Z",
        "username": "service_backup",
        "ip_address": "203.0.113.44",
        "successful": True,
    },
    {
        "timestamp": "2026-10-20T10:45:53Z",
        "username": "a.patel",
        "ip_address": "192.0.2.10",
        "successful": True,
    },
    {
        "timestamp": "2026-10-20T11:07:28Z",
        "username": "root",
        "ip_address": "198.51.100.88",
        "successful": False,
    },
    {
        "timestamp": "2026-10-20T11:08:41Z",
        "username": "root",
        "ip_address": "198.51.100.88",
        "successful": False,
    },
]


@mcp.tool()
def list_security_events() -> list[dict[str, str | bool]]:
    """Return every simulated security login event in timestamp order."""
    return [event.copy() for event in SECURITY_EVENTS]


@mcp.tool()
def detect_failed_logins() -> list[dict[str, int | str]]:
    """List IP addresses with at least two failed login attempts.

    Each result includes the IP address and its failed-attempt count. Successful
    logins do not reduce the failed-attempt count.
    """
    failed_counts: dict[str, int] = {}
    for event in SECURITY_EVENTS:
        if not event["successful"]:
            ip_address = str(event["ip_address"])
            failed_counts[ip_address] = failed_counts.get(ip_address, 0) + 1

    return [
        {"ip_address": ip_address, "failed_attempts": count}
        for ip_address, count in sorted(failed_counts.items())
        if count >= 2
    ]


@mcp.tool()
def investigate_ip(ip_address: str) -> list[dict[str, str | bool]]:
    """Return all recorded login events for the supplied IP address.

    The comparison ignores surrounding whitespace and letter case. An IP
    address with no matching events returns an empty list.
    """
    requested_ip = ip_address.strip().lower()
    return [
        event.copy()
        for event in SECURITY_EVENTS
        if str(event["ip_address"]).lower() == requested_ip
    ]


if __name__ == "__main__":
    mcp.run(transport="stdio")
