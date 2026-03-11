# Installing Pheme for Codex

## Installation

1. Clone the repo and install dependencies:

   ```bash
   git clone https://github.com/divyekant/pheme.git ~/.codex/pheme
   cd ~/.codex/pheme
   uv venv
   uv pip install -e ".[dev]"
   ```

2. Add the Pheme MCP server to `~/.codex/config.toml`:

   ```toml
   [mcp_servers.pheme]
   command = "/Users/<you>/.codex/pheme/.venv/bin/python"
   args = ["-m", "server"]
   cwd = "/Users/<you>/.codex/pheme"
   ```

3. Symlink the skill into Codex discovery:

   ```bash
   mkdir -p ~/.agents/skills
   ln -s ~/.codex/pheme/skills/pheme ~/.agents/skills/pheme
   ```

4. Restart Codex so it discovers the MCP server and skill.

## Route Config

Codex route overrides can live at:

- Project-level: `.codex/pheme-routes.yaml`
- User-level: `~/.codex/pheme-routes.yaml`
