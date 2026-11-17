#!/bin/bash
# Connects Claude Code to X's official MCP server, read-only.
# The token is typed here, not in chat, so it never appears in a conversation.
set -e
read -r -s -p "Paste your X app Bearer token, then press Return: " TOKEN
echo
if [ -z "$TOKEN" ]; then echo "No token entered, nothing changed."; exit 1; fi
claude mcp remove x --scope user >/dev/null 2>&1 || true
claude mcp add --transport http --scope user x "https://api.x.com/mcp?read_only=true" \
  --header "Authorization: Bearer $TOKEN"
echo "Added. Checking the connection..."
claude mcp list 2>/dev/null | grep -E "^x:" || echo "Not listed yet; start a new Claude session and check again."
