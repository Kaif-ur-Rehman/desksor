# Desksor

**Give your AI eyes. Let it see everything on your computer.**

---

You use Claude Code. You use Cursor.  
They are brilliant. But they are blind.

They cannot see your browser console.  
They cannot see your Excel data.  
They cannot see errors in your running app.  
They cannot see what is open on your screen.

You spend half your day copy-pasting context into AI that should already know.

**Desksor fixes this.**

---

## The difference

**Without Desksor**
```
You:    "Claude, here is the error..." [paste]
You:    "And here is the network request..." [paste]
You:    "And the variable looks like..." [paste]
Claude: "I see, the problem is..."
```

**With Desksor**
```
You:    "Claude, fix the bug."
Claude reads your console, your code, your app state.
Claude: "Fixed. Line 42."
```

---

## How it works

Every Windows app has an invisible structured map called the **Accessibility Tree** — every button, field, menu, and value. Updated in real time. Always accurate.

Desksor reads this map and gives your AI direct access to every app on your computer. No screenshots. No pixel guessing. Real structure.

```python
from desksor import Agent
import asyncio

agent = Agent()

# see what is open
asyncio.run(agent.get_open_apps())
# → ["Excel", "Chrome", "VS Code", "Slack"]

# read any app
asyncio.run(agent.read("Excel"))
# → full structure: every cell, button, menu

# click anything by name — never breaks
asyncio.run(agent.click("Excel", "Save"))
# → done in 50ms

# type into anything
asyncio.run(agent.type("Notepad", "Text Area", "Hello"))
# → instant via clipboard paste
```

---

## Why it never breaks

Traditional automation breaks when apps update:
```python
# old way — breaks when button moves
pyautogui.click(x=342, y=156)

# Desksor — works forever
agent.click("Excel", "Save")
# "Save" is always called "Save" even when design changes
```

Apps update their design. Buttons move. Colors change.  
The structure stays the same.  
Desksor reads the structure. **It never breaks.**

---

## Install

```bash
pip install pywinauto pyautogui websockets pyperclip openpyxl
```

```bash
git clone https://github.com/Kaif-ur-Rehman/desksor
cd desksor
python smoke_test.py
```

If you see `ALL SMOKE TESTS PASSED` — you are ready.

---

## Add to Claude Code

Find your config file:
```
Windows: C:\Users\NAME\AppData\Roaming\Claude\claude_desktop_config.json
```

Add this:
```json
{
  "mcpServers": {
    "desksor": {
      "command": "node",
      "args": ["C:/full/path/to/desksor/mcp/server.js"]
    }
  }
}
```

Install MCP dependencies:
```bash
cd mcp
npm install
```

Restart Claude. Done.

**Claude can now see your entire computer.**

---

## Add to Cursor

Same as Claude Code. Open Cursor settings. Find MCP section. Add the same config above. Restart Cursor.

---

## What your AI can see

| What | How | Speed |
|---|---|---|
| Any open app — buttons, fields, menus | Accessibility tree | 50ms |
| Browser console errors | Chrome debug port | 80ms |
| Browser page structure | Chrome debug port | 80ms |
| Any file content | Direct file system | 10ms |
| Any folder listing | Direct file system | 10ms |
| Clipboard content | System API | 5ms |
| Running processes | System API | 10ms |
| Active window | System API | 5ms |

---

## What your AI can do

```python
agent.click("Excel", "Save")           # click any element by name
agent.type("Slack", "Message", "Hi")   # type into any field
agent.key_press("ctrl+s")              # any keyboard shortcut
agent.scroll("Chrome", "down", 3)      # scroll anywhere
agent.open_app("Notepad")              # open any app
agent.save_app("Word")                 # save any document
agent.right_click("VS Code", "file")   # right click anything
```

---

## Smart context — minimum tokens

Desksor never dumps your entire PC into AI.  
AI asks for exactly what it needs. Nothing more.

```python
# start here — costs ~100 tokens
agent.context()
# → {open_apps, active_window, clipboard, browser_tab, recent_error}

# then read what you need — costs ~200 tokens
agent.read("Excel")

# or just one element — costs ~10 tokens
agent.read_element("Excel", "A1")

# full tree only when needed — costs ~2000 tokens
agent.read("Excel", full=True)
```

---

## Browser features

Launch Chrome with debug port first:
```bash
chrome.exe --remote-debugging-port=9222
```

Then:
```python
agent.browser.read_console()   # all console errors
agent.browser.read_network()   # all network requests
agent.browser.read_page()      # full page structure
agent.browser.read_tabs()      # all open tabs
```

Claude reads your browser console directly.  
No copy pasting errors ever again.

---

## Use in your own AI code

```python
from desksor import Agent
import asyncio

agent = Agent()

# get smart context first
context = asyncio.run(agent.context())
# AI reads this and decides what to look at

# read specific app
result = asyncio.run(agent.read("Excel"))
# AI gets structure, decides what to click

# execute action
asyncio.run(agent.click("Excel", "Save"))
# done
```

---

## Start WebSocket server

For external integrations and custom AI tools:

```bash
python -m desksor.server
# Desksor running on ws://localhost:7823
```

Send JSON commands:
```json
{"action": "click", "app": "Excel", "element": "Save", "id": "req_1"}
```

Get JSON results:
```json
{"id": "req_1", "success": true, "data": {}, "error": null, "time_ms": 48}
```

---

## Privacy

Desksor runs **100% locally.**  
No data leaves your computer.  
No analytics. No telemetry. No tracking.

You can verify this — every line of code is on GitHub.

**Password fields always return empty string.**  
This is a Windows security feature built into the OS.  
Even Desksor cannot read them. Nobody can via accessibility API.

Desksor only reads apps when your code explicitly calls it.  
It does not run in background reading your screen constantly.  
It reads on demand. Nothing more.

Want to see exactly what Desksor can read? Run this:

```python
from desksor import Agent
agent = Agent()
import asyncio
print(asyncio.run(agent.read("Notepad")))
```

Everything it can see — you can see first.  
No surprises. No hidden access.

---

## Requirements

- Windows 10 or 11
- Python 3.8 or higher
- Node.js 18 or higher (for MCP server)
- Chrome with `--remote-debugging-port=9222` (for browser features)

---

## Run examples

```bash
python examples/basic_click.py
python examples/read_excel.py
python examples/control_browser.py
python examples/ai_with_context.py
python examples/never_breaks.py
```

---

## Run tests

```bash
python -m pytest tests/ -v
```

---

## Works with

- ✅ Claude Code
- ✅ Cursor
- ✅ Any MCP-compatible tool
- ✅ Your own Python AI code
- ✅ Any tool that connects via WebSocket

---

## Cloud version

Free version works on your machine only.  
Cloud version works on any user's machine globally.  
Mac and Linux support. Knowledge graph. Action logs. Reliability scores.

**In Devlopment — starts at $9/month**

---

## License

MIT — free forever for local use.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to contribute.

---

*Built by [Aivorize](https://github.com/Kaif-ur-Rehman)*  
*desksor — AI sees clearly. Finally.*
