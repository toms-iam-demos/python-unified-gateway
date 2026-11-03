"""Shared navigation with canonical root and catalog-owned collections."""
GROUPS = [
    {"title": "Home", "items": [("Home", "/")]},
    {"title": "Demo catalog", "items": [("Demo catalog", "/catalog"), ("Invitations", "/catalog?area=workups")]},
    {"title": "Build", "items": [("API reference", "/build"), ("App Center", "/catalog?area=extensions")]},
    {"title": "Workspaces", "items": [("Agents", "/workspaces/agents"), ("MCP", "/workspaces/mcp"), ("HAM", "/workspaces/ham")]},
    {"title": "Resources", "items": [("Guides", "/resources")]},
]
