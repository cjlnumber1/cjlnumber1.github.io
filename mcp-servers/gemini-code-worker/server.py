import os
from pathlib import Path
from fastmcp import FastMCP
from google import genai
from google.genai import types

mcp = FastMCP("GeminiCodeWorker")
client = genai.Client()

# Directories and files to always ignore when scanning paths
IGNORED_DIRS = {
    ".git", ".venv", "venv", "node_modules", "__pycache__",
    ".idea", ".vscode", "dist", "build", ".next", "coverage"
}
IGNORED_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf",
    ".zip", ".tar", ".gz", ".pyc", ".lock", ".svg", ".woff", ".woff2"
}

def _collect_file_content(path_str: str, max_files: int = 60) -> tuple[str, int]:
    """Reads a file or recursively traverses a folder, aggregating content with path headers."""
    target_path = Path(path_str).expanduser().resolve()

    if not target_path.exists():
        raise FileNotFoundError(f"Path does not exist: {target_path}")

    aggregated_text = []
    file_count = 0

    if target_path.is_file():
        try:
            content = target_path.read_text(encoding="utf-8", errors="replace")
            return f"--- File: {target_path} ---\n{content}\n", 1
        except Exception as e:
            return f"--- File: {target_path} (Failed to read: {e}) ---\n", 0

    # Directory walk
    for root, dirs, files in os.walk(target_path):
        # Prune ignored directories in-place
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.startswith(".")]

        for file in files:
            file_path = Path(root) / file
            if file_path.suffix.lower() in IGNORED_EXTENSIONS:
                continue

            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
                aggregated_text.append(f"--- File: {file_path.relative_to(target_path)} ---\n{content}\n")
                file_count += 1
            except Exception:
                continue

            if file_count >= max_files:
                aggregated_text.append(f"\n[Warning: Reached limit of {max_files} files. Truncated.]\n")
                break
        if file_count >= max_files:
            break

    return "\n".join(aggregated_text), file_count


@mcp.tool()
def gemini_analyze_local_path(
    path: str,
    objective: str,
    focus_files: list[str] | None = None
) -> str:
    """
    Read a local file or an entire directory by path and pass its full content directly to Gemini.
    Claude only needs to pass the path string on the filesystem.

    Args:
        path: Absolute or home-relative path (e.g., '~/projects/backend' or '/app/src/utils.py')
        objective: What Gemini should look for (e.g., 'Find memory leaks', 'Propose refactoring')
        focus_files: Optional list of relative filenames to specifically restrict the analysis to.
    """
    try:
        content, count = _collect_file_content(path)
    except Exception as e:
        return f"Error reading filesystem at '{path}': {str(e)}"

    prompt = f"""
    You are an expert code architect analyzing local project files.

    Target Path: {path}
    Files Ingested: {count}
    Primary Objective: {objective}
    Focus Guidance: {focus_files if focus_files else "Entire ingested context"}

    Files Content:
    ==============
    {content}
    ==============

    Provide a clear, structured technical analysis addressing the objective, highlighting
    exact file paths and line contexts where appropriate.
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    return response.text


@mcp.tool()
def gemini_refactor_local_file(
    file_path: str,
    instructions: str
) -> str:
    """
    Reads a specific local file, has Gemini generate the complete refactored version
    or patch according to instructions, and returns the modified code.

    Args:
        file_path: Absolute or home-relative path to a specific single file.
        instructions: What modifications, features, or fixes to implement.
    """
    target = Path(file_path).expanduser().resolve()
    if not target.is_file():
        return f"Error: '{file_path}' is not a valid file."

    try:
        source_code = target.read_text(encoding="utf-8")
    except Exception as e:
        return f"Error reading file '{file_path}': {str(e)}"

    prompt = f"""
    You are an autonomous senior developer tasked with refactoring/updating a file.

    File Path: {target}
    Instructions: {instructions}

    Original Content:
    -----------------
    {source_code}
    -----------------

    Return the complete, updated file content ready to replace the original.
    Minimize conversational commentary; enclose the code in standard triple-backtick markdown blocks.
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.1,
        ),
    )
    return response.text


if __name__ == "__main__":
    mcp.run()
