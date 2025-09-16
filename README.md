
# UE5 Blueprint MCP Server

A **Python-based MCP server** that wraps Unreal Engine 5 (UE5) Blueprint APIs, enabling **LLM-powered interactions** with Blueprints.
This allows AI agents to perform operations such as modifying Blueprints, editing visual scripting graphs, and managing variables, functions, and components.

---

## Features

The MCP server runs in **streamable HTTP mode**, built on **FastMCP** to call web APIs provided by a custom UE plugin.
The plugin exposes a web API by wrapping **UE Editor Utility C++ APIs**, supporting:

### Blueprint Management

* Create Blueprints
* Compile Blueprints
* Get Blueprint variables, functions, and graph details

### Blueprint Functions

* Create, edit, and delete functions

### Blueprint Visual Scripting

* Add function calls nodes
* Add custom or built-in events nodes
* Add variable getter/setter nodes
* Add generic, math, cast, and struct nodes
* Connect or break pin connections
* Set pin default values
* Get supported node types

### Blueprint Variables

* Add, delete, rename, and set default values

### Blueprint Components

* Get, add, rename, remove, or reparent components
* Get and set component properties

---

## Installation

1. Navigate to your project’s `Plugins` folder:

   ```bash
   cd <YourUEProject>/Plugins
   ```

2. Clone the repository:

   ```bash
   git clone https://github.com/cutehusky/ue5-mcp.git
   ```

3. Enable the plugin **UE5\_MCP** in the UE5 **Plugins** tab.

4. (Optional) Create a Python environment.

5. Install Python dependencies for the MCP server:

   ```bash
   cd Python/MCP
   pip install mcp httpx python-dotenv
   ```

---

## Usage

### Running the MCP Server

1. In the UE5 Editor, go to **Windows > UE5\_MCP** to start the Blueprint API.
   Select the desired port.

2. Configure the `.env` file with your UE API endpoint:

   ```env
   PORT=<your_port_to_run_mcp_server>
   UE5_REST_API_URL=http://localhost:<your_port>
   ```

3. Start the MCP server:

   ```bash
   python mcp_server.py
   ```

---

## Roadmap

* Support for more UE5 node types (e.g., animations, AI behaviors).
* Asset browser and asset management support.
* Tools to fetch UE documentation for LLMs.
* Enhanced error handling with detailed API failure messages.

---

## Contributing

You can contribute by:

* Adding more tools wrapping additional UE5 Blueprint APIs.
* Extending tooling to fetch UE documentation (built-in classes, graph nodes, methods).
* Improving tool docstrings with LLM-friendly guidance.
* Expanding graph manipulation to support additional node types.

---

## License

MIT License

