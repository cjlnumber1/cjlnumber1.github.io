# GeminiCodeWorker MCP Server

An MCP server that delegates coding and analysis work to Gemini — either by
reading local files/directories directly by path, or by taking code, task
descriptions, or logs passed in as text.

## Tools

- **gemini_analyze_local_path(path, objective, focus_files=None)** — reads a
  file or recursively walks a directory (skipping common build/VCS folders
  and binary asset extensions, capped at 60 files) and asks Gemini to analyze
  the aggregated content against a stated objective.
- **gemini_refactor_local_file(file_path, instructions)** — reads a single
  file and asks Gemini to return the complete updated file content per the
  given instructions.
- **gemini_code_delegate(task_description, language="python", constraints="")**
  — asks Gemini to implement a focused coding task (boilerplate, unit tests,
  a specific function) from a description, with no filesystem access.
- **gemini_codebase_analyzer(file_contents_or_logs, analysis_objective)** —
  asks Gemini to diagnose pasted code, multi-file content, or stack traces
  against a stated objective and propose concrete fixes.

## Setup

```bash
pip install -r requirements.txt
export GEMINI_API_KEY="your-api-key"   # or GOOGLE_API_KEY
python server.py
```

## Register with Claude Code

This repo's root `.mcp.json` already registers the server:

```json
{
  "mcpServers": {
    "gemini-code-worker": {
      "command": "python",
      "args": ["mcp-servers/gemini-code-worker/server.py"]
    }
  }
}
```

It deliberately has no `env` block — this is a **public** repository, so
never commit a real `GEMINI_API_KEY` into `.mcp.json`. The server process
inherits environment variables from whatever shell launches Claude Code, so
just export the key in your own shell/profile before starting Claude Code:

```bash
export GEMINI_API_KEY="your-api-key"   # add to your shell profile, not the repo
```

If your MCP client doesn't pass through the parent shell's environment, add
a `.mcp.json` locally (gitignored) with an `env` block instead of editing the
committed one.

## Notes

- Directory scans skip `.git`, `.venv`/`venv`, `node_modules`, `__pycache__`,
  `.idea`, `.vscode`, `dist`, `build`, `.next`, `coverage`, and any other
  dot-directory, plus common binary/lockfile extensions.
- The tools read arbitrary local paths, so only run this server in trusted,
  local development contexts.
