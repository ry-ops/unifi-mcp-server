# MCP Server UniFi

A server implementation for managing and controlling UniFi network devices through MCP (Management Control Protocol). This server enables natural language interactions with your UniFi network using AI agents like Goose and Claude by wrapping the UniFi Network API.

## Features

- Query UniFi sites and devices using natural language through AI agents
- Local server implementation that connects to your UniFi Network application
- Compatible with both Goose AI and Claude Desktop
- Secure API key-based authentication

## Prerequisites

- Python 3.8 or higher
- `uv` package manager
- UniFi Network application
- UniFi API key (obtained from UniFi console)

## Setup

1. Create an API key:
   - Go to your UniFi console at https://unifi.ui.com
   - Navigate to Settings » Control Plane » Integrations
   - Click "Create API Key"

2. Clone and set up the repository:
```bash
git clone https://github.com/zcking/mcp-server-unifi
cd mcp-server-unifi
uv venv
source .venv/bin/activate  # On Unix/macOS
# or
.venv\Scripts\activate  # On Windows
```

3. Install dependencies:
```bash
uv sync
```

4. Configure environment variables:
```bash
export UNIFI_API_KEY="your_api_key_here"
```

## Running the Server

Start the MCP development server:

```bash
uv run mcp dev main.py
```

The MCP Inspector will be available at http://localhost:5173 for testing and debugging.

## AI Agent Integration

### Goose AI Setup

1. Open Goose and go to Settings » Extensions » Add custom extension
2. Configure the extension:
   - ID: unifi
   - Name: unifi
   - Description: Get information about your UniFi network
   - Command: `/Users/username/.local/bin/uv --directory /path/to/mcp-server-unifi run main.py`
   - Environment Variables: Set UNIFI_API_KEY to your API key

### Claude Desktop Setup

1. Open Claude and go to Settings » Developer » Edit Config
2. Add to your `claude_desktop_config.json`:
```json
{
    "mcpServers": {
        "unifi": {
            "command": "/Users/username/.local/bin/uv",
            "args": [
                "--directory",
                "/path/to/mcp-server-unifi",
                "run",
                "main.py"
            ]
        }
    }
}
```

