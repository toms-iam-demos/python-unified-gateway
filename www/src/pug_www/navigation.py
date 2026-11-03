"""Shared navigation registry; content and menus have stable canonical URLs."""
GROUPS = [
    {"title": "Catalog", "items": [("Demo catalog", "/catalog")]},
    {"title": "Build", "items": [("API reference", "/build")]},
    {"title": "Demos", "items": [("Demo space", "/demos"), ("Data Studio", "/demos/data-studio")]},
    {"title": "Workspaces", "items": [("Agents", "/workspaces/agents"), ("MCP", "/workspaces/mcp"), ("HAM", "/workspaces/ham")]},
    {"title": "Resources", "items": [("Guides", "/resources")]},
]
