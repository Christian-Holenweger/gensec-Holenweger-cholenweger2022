"""Interactive AI agent for investigating simulated security events and Git history.

FastAgent connects to the security and Git MCP servers configured in
``fast-agent.yaml``. Set ``GOOGLE_API_KEY`` before starting the program. The
model can be changed with the ``GOOGLE_MODEL`` environment variable.
"""

import asyncio
import os
from pathlib import Path

from fast_agent import FastAgent


DEFAULT_MODEL = "google.gemini-3.8-flash"
MODEL = os.getenv("GOOGLE_MODEL", DEFAULT_MODEL)
CONFIG_FILE = Path(__file__).with_name("fast-agent.yaml")

fast = FastAgent("Security Investigation Assistant", config_path=str(CONFIG_FILE))


@fast.agent(
    name="security-investigator",
    instruction=(
        "You are a security investigation assistant. Use the security event tools "
        "to identify suspicious login activity. When the user asks about repository "
        "history, use the Git MCP tools to inspect commits and changes. You may "
        "combine evidence from both servers, and should clearly distinguish facts "
        "returned by tools from your conclusions. "
        "When using Git MCP tools, always set repo_path to "
        "/home/cholenweger2022/gensec-code, which is the Git repository root. "
        "Never use '.' or the hw4 directory as repo_path. "
    ),
    model=MODEL,
    servers=["security_logs", "git_history"],
    default=True,
)
async def main() -> None:
    """Start the configured MCP connections and open the interactive chat."""
    if not os.getenv("GOOGLE_API_KEY"):
        raise RuntimeError(
            "Set GOOGLE_API_KEY in your environment before starting the assistant."
        )

    # FastAgent starts both configured stdio MCP servers for this session.
    async with fast.run() as agent:
        await agent.interactive()


if __name__ == "__main__":
    asyncio.run(main())
