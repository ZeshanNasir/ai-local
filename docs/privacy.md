# Privacy and network boundaries

Running a model locally is not the same as keeping task data on the machine. This page records what was observed and what was not.

## The request path (OpenCode with a local model)

1. The user's prompt and the files the agent reads go to the OpenCode process.
2. OpenCode sends them to the model server at `127.0.0.1:11434` (Ollama).
3. Ollama runs the model on the local GPU and returns the reply.

OpenCode may also keep session history on disk. That was not inspected.

## What was observed

A polling snapshot (`lsof`) of TCP connections during each scored session, classified as loopback, private network or other. Addresses are not stored in the result files; only the class and count.

- **Ollama:** loopback connections only, in every session.
- **OpenCode, minimal config** (local provider only, no tool servers): loopback connections plus **three to four connections to non-local endpoints** in every session. A separate one-line session (`Reply with the single word OK.`) showed two such endpoints: one that resolved to a public cloud provider's host name and one address that did not resolve. Their purpose was not identified, and the content of the traffic was not inspected, so it is **unknown whether any of it carries prompt content**. Plausible causes include update checks and model catalogue lookups; that is a guess, not a finding.
- **OpenCode, the operator's normal config** contains two remote tool servers (documentation lookup and code search). A session with that config can send queries to them. This was read from the config file and not exercised.

## What was not measured

Outbound traffic payloads, DNS queries, behaviour over a long session, other harnesses, telemetry settings, or what the operating system logs. A short polling window can miss brief connections.

## What a deployment would need before claiming "no data leaves the device"

An egress test with a firewall or proxy that blocks everything except loopback during a representative session; a review of each harness's telemetry, update and tool-server settings; and a decision on where session logs live and who can read them. Without those, the accurate statement is: *the model server used loopback only; the harness was not shown to be silent.*

## The method

`python3 -m labbench net --processes ollama,opencode --seconds 60` records endpoint classes for named processes over a window. It is a sketch of a check, not an audit.
