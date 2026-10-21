# Homework 04.2: Custom MCP Server and Agent

**Project:** Security Investigation Assistant  
**FAU ID:** cholenweger2022

## Overview

This project uses a FastMCP server to provide simulated login events and a
FastAgent-powered Gemini assistant to investigate them. The agent connects to
the custom security server and the published Git MCP server over local standard
input/output (stdio) connections.

## Custom security MCP server

`mcp-server.py` uses the official Python MCP SDK and FastMCP. It contains a
small, fixed dataset of simulated login records with timestamps, usernames, IP
addresses, and successful or failed results. The IP addresses are reserved for
documentation examples.

The server provides three tools:

- **`list_security_events`** returns all recorded events in timestamp order.
- **`detect_failed_logins`** counts failed attempts by IP address and returns
  addresses with at least two failures.
- **`investigate_ip`** returns all events recorded for a requested IP address.

## Published Git MCP server

The agent also connects to `mcp-server-git`, a published MCP server for working
with Git repositories. It lets the agent inspect repository history and changes
alongside the security event data.

The repository path is set in `fast-agent.yaml` using `--repository`. The agent
instructions also provide the repository root as `repo_path` when calling Git
tools. Update both locations if the project is stored somewhere other than
`/home/cholenweger2022/gensec-code`.

## Installation

Install [uv](https://docs.astral.sh/uv/) if it is not already available. From
the repository root, sync the dependencies listed in `pyproject.toml` and
`uv.lock`:

```bash
cd hw4
uv sync
```

This installs FastAgent, the MCP Python SDK, and `mcp-server-git` into the
project environment.

## Configure Gemini

Set your Gemini API key in the shell environment. Do not add the key to source
files:

```bash
export GOOGLE_API_KEY="your-Gemini-API-key"
```

The default model is `google.gemini-3.8-flash`. To select another model, set
`GOOGLE_MODEL` before launching the agent, for example:

```bash
export GOOGLE_MODEL="google.gemini-3.5-flash-lite"
```

## Launch the agent

Run this from the `hw4` directory after setting `GOOGLE_API_KEY`:

```bash
uv run python agent.py
```

FastAgent starts both configured MCP servers as local subprocesses and opens an
interactive chat. The custom server runs `uv run python mcp-server.py`; the Git
server runs `uv run python -m mcp_server_git` with the configured repository
path.

## Example investigation prompt

> Find IP addresses with repeated failed logins. Investigate each IP, then
> inspect recent Git commits and changes in this repository for authentication
> or login-related modifications. Summarize the evidence and distinguish the
> event data from your conclusions.

## Known limitations

- The login events are simulated and static; they are not live system logs.
- Gemini API requests may encounter **429** rate-limit or **503** availability
  errors. Retry later if a request fails for either reason.
- Git MCP tools need the correct repository path. The configured path and the
  path in the agent instructions must match the location of the repository.
- The agent requires a valid `GOOGLE_API_KEY` and access to the Gemini API.
