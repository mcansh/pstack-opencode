---
name: make-bot-ui
description: Build a small UI that calls an existing bot webhook through a server while keeping credentials out of the browser. Requires a documented webhook integration.
metadata:
  opencode/autoinvoke: false
---

# Make a bot UI

Read [OpenCode runtime contract](../opencode-runtime.md) first.

1. Identify an existing, authorized webhook integration and read its documented URL, authentication scheme, payload, response contract, and retry policy. This plugin cannot create Cursor/Grok Bot routines or secret-request cards. If no integration exists, report this capability gap before building a UI that cannot work.
2. Store credentials through the project's existing secret mechanism. Ask the user to configure a secret outside chat when necessary. Keep credentials off the browser and out of logs.
3. Build the smallest page and server route. Validate the action and payload at the server boundary. The browser calls the local server; the server calls the documented webhook with a timeout and useful failure feedback. Treat webhook data as untrusted input.
4. Use the project's existing local hosting setup. Expose it to Tailscale only if requested and an authorized node is available. Never install software or alter networking as an implicit part of building a page.
5. Exercise a harmless documented action end to end and record the actual response before claiming the integration works. Report any unavailable live proof.
