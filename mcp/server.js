#!/usr/bin/env node
/**
 * mcp/server.js
 *
 * MCP server for Desksor — exposes Desksor capabilities as MCP tools
 * so Claude Code and Cursor can control any Windows app.
 *
 * Run with: node server.js
 *
 * Prerequisites:
 *   1. pip install desksor
 *   2. python -m desksor.server   (start on ws://localhost:7823)
 *   3. node server.js             (start this MCP server)
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { WebSocket } from "ws";

// ─── Desksor WebSocket connection ──────────────────────────────────────────

const DESKSOR_URL = "ws://localhost:7823";
let _msgId = 1;

/**
 * Send a command to the Desksor Python server and return the result.
 * Creates a fresh connection per call for simplicity and reliability.
 */
async function desksorCall(command) {
  return new Promise((resolve, reject) => {
    const id = `mcp_${_msgId++}`;
    let ws;

    const timeout = setTimeout(() => {
      try { ws.close(); } catch {}
      reject(new Error(
        "Desksor server timed out. Make sure it's running:\n" +
        "  python -m desksor.server"
      ));
    }, 15000);

    try {
      ws = new WebSocket(DESKSOR_URL);
    } catch (err) {
      clearTimeout(timeout);
      reject(new Error(
        "Cannot connect to Desksor server. Start it with:\n" +
        "  pip install desksor\n" +
        "  python -m desksor.server"
      ));
      return;
    }

    ws.on("error", (err) => {
      clearTimeout(timeout);
      reject(new Error(
        "Cannot connect to Desksor (ws://localhost:7823). " +
        "Make sure Python Desksor server is running:\n" +
        "  python -m desksor.server"
      ));
    });

    ws.on("open", () => {
      ws.send(JSON.stringify({ ...command, id }));
    });

    ws.on("message", (data) => {
      clearTimeout(timeout);
      try {
        const response = JSON.parse(data.toString());
        ws.close();
        if (response.success) {
          resolve(response.data);
        } else {
          reject(new Error(response.error || "Desksor action failed."));
        }
      } catch (parseErr) {
        ws.close();
        reject(new Error(`Invalid response from Desksor: ${data}`));
      }
    });
  });
}

// ─── Tool definitions ────────────────────────────────────────────────────────

const TOOLS = [
  {
    name: "desksor_read",
    description:
      "Read the full structure of any open Windows application using the accessibility tree. " +
      "Returns all UI elements with their names, types, values, and positions. " +
      "Use this to understand what is visible on screen in any app.",
    inputSchema: {
      type: "object",
      properties: {
        app_name: {
          type: "string",
          description: "Name of the open application (e.g. 'Excel', 'Notepad', 'Chrome')",
        },
      },
      required: ["app_name"],
    },
  },
  {
    name: "desksor_click",
    description:
      "Click any element in any open Windows application by its name. " +
      "Uses the accessibility tree — never breaks when UI updates. " +
      "Example: click 'Save' in 'Excel'.",
    inputSchema: {
      type: "object",
      properties: {
        app_name: {
          type: "string",
          description: "Name of the open application",
        },
        element_name: {
          type: "string",
          description: "Name of the element to click (partial match works)",
        },
      },
      required: ["app_name", "element_name"],
    },
  },
  {
    name: "desksor_type",
    description:
      "Type text into any element in any open Windows application. " +
      "Clears existing content first. " +
      "Example: type 'Hello World' into 'Text Editor' in 'Notepad'.",
    inputSchema: {
      type: "object",
      properties: {
        app_name: {
          type: "string",
          description: "Name of the open application",
        },
        element_name: {
          type: "string",
          description: "Name of the element to type into",
        },
        text: {
          type: "string",
          description: "Text to type into the element",
        },
      },
      required: ["app_name", "element_name", "text"],
    },
  },
  {
    name: "desksor_find",
    description:
      "Search for a specific UI element within an open application. " +
      "Returns matching elements with their positions and current values. " +
      "Use this before clicking to verify an element exists.",
    inputSchema: {
      type: "object",
      properties: {
        app_name: {
          type: "string",
          description: "Name of the open application",
        },
        query: {
          type: "string",
          description: "Partial element name to search for (case-insensitive)",
        },
      },
      required: ["app_name", "query"],
    },
  },
  {
    name: "desksor_open_apps",
    description:
      "Get a list of all currently open applications on the Windows desktop. " +
      "Returns app names, window titles, process IDs, and handles.",
    inputSchema: {
      type: "object",
      properties: {},
      required: [],
    },
  },
  {
    name: "desksor_key_press",
    description:
      "Press a keyboard shortcut on the currently active application. " +
      "Examples: 'ctrl+s' to save, 'ctrl+z' to undo, 'alt+f4' to close, 'enter', 'escape'.",
    inputSchema: {
      type: "object",
      properties: {
        keys: {
          type: "string",
          description: "Key combination (e.g. 'ctrl+s', 'alt+f4', 'enter', 'ctrl+shift+p')",
        },
      },
      required: ["keys"],
    },
  },
  {
    name: "desksor_browser_console",
    description:
      "Read all console messages (errors, warnings, logs) from the active Chrome/Edge browser tab. " +
      "Requires Chrome launched with --remote-debugging-port=9222.",
    inputSchema: {
      type: "object",
      properties: {
        tab_id: {
          type: "string",
          description: "Optional browser tab ID (defaults to active tab)",
        },
      },
      required: [],
    },
  },
  {
    name: "desksor_browser_page",
    description:
      "Read the full DOM structure and all interactive elements of the current browser page. " +
      "Returns buttons, links, inputs, and their text/positions. " +
      "Requires Chrome with --remote-debugging-port=9222.",
    inputSchema: {
      type: "object",
      properties: {
        tab_id: {
          type: "string",
          description: "Optional browser tab ID (defaults to active tab)",
        },
      },
      required: [],
    },
  },
  {
    name: "desksor_files_list",
    description:
      "List all files and folders in a directory on the Windows file system. " +
      "Returns names, sizes, types, and modification dates.",
    inputSchema: {
      type: "object",
      properties: {
        path: {
          type: "string",
          description: "Directory path to list (e.g. 'C:/Users/username/Documents')",
        },
      },
      required: ["path"],
    },
  },
  {
    name: "desksor_files_read",
    description:
      "Read the content of any file on the Windows file system. " +
      "Supports: .txt .py .js .json .csv .md .html .xlsx .pdf and more.",
    inputSchema: {
      type: "object",
      properties: {
        path: {
          type: "string",
          description: "Full path to the file to read",
        },
      },
      required: ["path"],
    },
  },
  {
    name: "desksor_system_info",
    description:
      "Get current Windows system information: CPU usage, RAM usage, disk usage, " +
      "Python version, and platform details.",
    inputSchema: {
      type: "object",
      properties: {},
      required: [],
    },
  },
];

// ─── Server setup ─────────────────────────────────────────────────────────────

const server = new Server(
  {
    name: "desksor",
    version: "0.1.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// List available tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return { tools: TOOLS };
});

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    let command = {};

    switch (name) {
      case "desksor_read":
        command = { action: "read", app: args.app_name };
        break;
      case "desksor_click":
        command = { action: "click", app: args.app_name, element: args.element_name };
        break;
      case "desksor_type":
        command = { action: "type", app: args.app_name, element: args.element_name, text: args.text };
        break;
      case "desksor_find":
        command = { action: "find", app: args.app_name, query: args.query };
        break;
      case "desksor_open_apps":
        command = { action: "get_open_apps" };
        break;
      case "desksor_key_press":
        command = { action: "key_press", keys: args.keys };
        break;
      case "desksor_browser_console":
        command = { action: "browser_console", tab_id: args.tab_id };
        break;
      case "desksor_browser_page":
        command = { action: "browser_page", tab_id: args.tab_id };
        break;
      case "desksor_files_list":
        command = { action: "files_list", path: args.path };
        break;
      case "desksor_files_read":
        command = { action: "files_read", path: args.path };
        break;
      case "desksor_system_info":
        command = { action: "system_info" };
        break;
      default:
        throw new Error(`Unknown tool: ${name}`);
    }

    const result = await desksorCall(command);
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(result, null, 2),
        },
      ],
    };
  } catch (error) {
    return {
      content: [
        {
          type: "text",
          text: `Error: ${error.message}`,
        },
      ],
      isError: true,
    };
  }
});

// ─── Start ────────────────────────────────────────────────────────────────────

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Desksor MCP server running. Tools available to Claude Code / Cursor.");
}

main().catch((err) => {
  console.error("Fatal error:", err);
  process.exit(1);
});
