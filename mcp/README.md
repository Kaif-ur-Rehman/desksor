# Desksor MCP Server

Connect Claude Code and Cursor to Desksor — giving your AI eyes and hands on Windows.

## Prerequisites

**1. Install Desksor Python library**
```bash
pip install desksor
```

**2. Start the Desksor WebSocket server**
```bash
python -m desksor.server
```
You should see: `Desksor running on ws://localhost:7823`

**3. Install MCP server dependencies**
```bash
cd mcp
npm install
```

---

## Connect to Claude Desktop

Edit `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "desksor": {
      "command": "node",
      "args": ["C:/path/to/desksor/mcp/server.js"]
    }
  }
}
```

Replace `C:/path/to/desksor` with the actual path where you cloned/installed Desksor.

Restart Claude Desktop. You should see Desksor tools available in the tool list.

---

## Connect to Cursor

Add to Cursor's MCP settings (`.cursor/mcp.json` in your project or global settings):

```json
{
  "mcpServers": {
    "desksor": {
      "command": "node",
      "args": ["/absolute/path/to/desksor/mcp/server.js"]
    }
  }
}
```

---

## Available Tools

| Tool | Description |
|------|-------------|
| `desksor_read` | Read full structure of any open app |
| `desksor_click` | Click any element in any app by name |
| `desksor_type` | Type text into any element |
| `desksor_find` | Search for element in any app |
| `desksor_open_apps` | List all open applications |
| `desksor_key_press` | Press keyboard shortcuts |
| `desksor_browser_console` | Read browser console messages |
| `desksor_browser_page` | Read current browser page DOM |
| `desksor_files_list` | List files in a directory |
| `desksor_files_read` | Read any file content |
| `desksor_system_info` | CPU, RAM, disk usage |

---

## Example Conversation with Claude

```
You: Fix the bug in my app.

Claude uses desksor_browser_console → sees "TypeError: Cannot read property 'map' of undefined on line 42"
Claude uses desksor_files_read → reads your source file
Claude identifies the bug
Claude: "The array 'items' can be null. I'll add a null check."
[Claude fixes your code]
Done. No copy-pasting.
```

---

## Troubleshooting

**"Cannot connect to Desksor (ws://localhost:7823)"**
→ The Python server is not running. Run: `python -m desksor.server`

**"Chrome not in debug mode"**
→ Launch Chrome with: `chrome.exe --remote-debugging-port=9222`

**"Could not find app 'Excel'"**
→ Make sure Excel is open and visible. Use `desksor_open_apps` to see available apps.
