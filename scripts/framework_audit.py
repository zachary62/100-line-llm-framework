"""Reproduce the framework comparison table in chapter 1.

Every framework number the book prints comes out of this script, run against a
pinned commit. Nothing is quoted from a blog post, a README, or a benchmark
someone else ran. Re-run it yourself:

    python scripts/framework_audit.py --clone          # ~2 min, git only
    python scripts/framework_audit.py

What it measures, identically for every framework:

  framework LOC    non-blank, non-comment lines of Python in the packages the
                   vendor authors and a plain `pip install <framework>` puts on
                   your disk, excluding tests, docs, and examples. LangChain's
                   number therefore includes langchain-core, the four langgraph
                   packages, and langsmith, because installing `langchain`
                   installs all of them.
  packages         every package pip resolves transitively, counted from the
                   repo's own uv.lock rather than from an install, so the number
                   is reproducible offline.
  public API       names exported from the package's top-level __all__: the
                   vocabulary you have to learn before "hello world".

Nothing is installed and no API key is needed. Only git.
"""
import argparse
import ast
import pathlib
import subprocess
import sys
import tomllib

SKIP_DIRS = {"tests", "test", "docs", "examples", "scripts", "benchmarks", "bench"}

# Repos, each pinned to the last stable release of Q1 2026.
# name: (repo, release tag, commit the tag pointed to when measured).
# The checkout uses the commit, because a tag can be moved and a commit can't.
REPOS = {
    "langchain": ("https://github.com/langchain-ai/langchain", "langchain==1.2.14", "90087ce6bf"),
    "langgraph": ("https://github.com/langchain-ai/langgraph", "1.1.4", "5c9c1d598d"),
    "langsmith-sdk": ("https://github.com/langchain-ai/langsmith-sdk", "v0.7.23", "9530f8b6a7"),
    "langchain-community": ("https://github.com/langchain-ai/langchain-community", "libs/community/v0.4.1", "39be54ca85"),
    "deepagents": ("https://github.com/langchain-ai/deepagents", "deepagents==0.4.12", "ad7afc0bd3"),
    "crewAI": ("https://github.com/crewAIInc/crewAI", "1.12.2", "6193e082e1"),
    "autogen": ("https://github.com/microsoft/autogen", "python-v0.7.5", "83afbf5857"),
    "smolagents": ("https://github.com/huggingface/smolagents", "v1.24.0", "4e18069c71"),
    "PocketFlow": ("https://github.com/The-Pocket/PocketFlow", "main", "f74d023f"),
}

# label -> (pinned version, [vendor-authored package dirs], lock file, lock root)
FRAMEWORKS = [
    ("LangChain", "langchain 1.2.14", [
        "langchain/libs/langchain_v1/langchain",
        "langchain/libs/core/langchain_core",
        "langgraph/libs/langgraph/langgraph",
        "langgraph/libs/checkpoint/langgraph",
        "langgraph/libs/prebuilt/langgraph",
        "langgraph/libs/sdk-py/langgraph_sdk",
        "langsmith-sdk/python/langsmith",
    ], "langchain/libs/langchain_v1/uv.lock", "langchain"),
    ("LangChain Classic", "langchain-classic 1.0.3",
     ["langchain/libs/langchain/langchain_classic"], None, None),
    ("LangChain Community", "langchain-community 0.4.1",
     ["langchain-community/libs/community/langchain_community"], None, None),
    ("LangGraph", "langgraph 1.1.4", [
        "langgraph/libs/langgraph/langgraph",
        "langgraph/libs/checkpoint/langgraph",
        "langgraph/libs/prebuilt/langgraph",
        "langgraph/libs/sdk-py/langgraph_sdk",
    ], "langgraph/libs/langgraph/uv.lock", "langgraph"),
    ("deepagents", "deepagents 0.4.12",
     ["deepagents/libs/deepagents/deepagents"], "deepagents/libs/deepagents/uv.lock", "deepagents"),
    ("CrewAI", "crewai 1.12.2",
     ["crewAI/lib/crewai/src/crewai"], "crewAI/uv.lock", "crewai"),
    ("AutoGen", "autogen-agentchat 0.7.5", [
        "autogen/python/packages/autogen-core/src/autogen_core",
        "autogen/python/packages/autogen-agentchat/src/autogen_agentchat",
    ], "autogen/python/uv.lock", "autogen-agentchat"),
    ("smolagents", "smolagents 1.24.0", ["smolagents/src/smolagents"], None, None),
    ("PocketFlow", "100 lines", ["PocketFlow/pocketflow"], None, None),
]


def clone(base):
    for name, (url, tag, commit) in REPOS.items():
        into = base / name
        if not into.exists():
            print(f"# cloning {name}", file=sys.stderr)
            subprocess.run(["git", "clone", "--filter=blob:none", "-q", url, str(into)], check=True)
        subprocess.run(["git", "-C", str(into), "fetch", "--tags", "-q"], check=False)
        r = subprocess.run(["git", "-C", str(into), "checkout", "-q", commit])
        if r.returncode:  # shallow mirror or GC'd commit: fall back to the tag
            r = subprocess.run(["git", "-C", str(into), "checkout", "-q", tag])
        if r.returncode:
            print(f"# WARNING: {name} has neither commit {commit} nor tag {tag}, left at HEAD", file=sys.stderr)


def count_loc(root):
    total = files = 0
    if not root.exists():
        return None, 0
    for path in sorted(root.rglob("*.py")):
        if SKIP_DIRS & set(path.parts) or path.name.startswith("test_"):
            continue
        files += 1
        for line in path.read_text(errors="ignore").splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                total += 1
    return total, files


def count_public_api(root):
    init = root / "__init__.py"
    if not init.exists():
        return None
    try:
        tree = ast.parse(init.read_text(errors="ignore"))
    except SyntaxError:
        return None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    if isinstance(node.value, (ast.List, ast.Tuple, ast.Set)):
                        return len(node.value.elts)
    return None


def resolve_deps(lock_path, root_pkg):
    """Transitive runtime dependencies, straight out of the repo's uv.lock."""
    if not lock_path or not lock_path.exists():
        return None
    data = tomllib.loads(lock_path.read_text())
    graph = {p["name"]: [d["name"] for d in p.get("dependencies", [])] for p in data.get("package", [])}
    if root_pkg not in graph:
        return None
    seen, queue = set(), list(graph[root_pkg])
    while queue:
        name = queue.pop()
        if name in seen:
            continue
        seen.add(name)
        queue.extend(graph.get(name, []))
    return len(seen)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot-dir", default="framework-snapshots",
                    help="where the pinned clones live (created by --clone)")
    ap.add_argument("--clone", action="store_true", help="clone and check out every pinned snapshot first")
    args = ap.parse_args()
    base = pathlib.Path(args.snapshot_dir).expanduser()
    base.mkdir(parents=True, exist_ok=True)
    if args.clone:
        clone(base)

    rows = []
    for label, version, pkg_dirs, lock, lock_root in FRAMEWORKS:
        loc = files = 0
        for d in pkg_dirs:
            n, f = count_loc(base / d)
            if n is None:
                print(f"# missing {base / d} (run with --clone)", file=sys.stderr)
                continue
            loc, files = loc + n, files + f
        api = count_public_api(base / pkg_dirs[0])
        deps = resolve_deps(base / lock if lock else None, lock_root)
        rows.append((label, version, loc, files, api, deps))

    width = max(len(r[0]) for r in rows)
    print(f"| {'Framework'.ljust(width)} | Pinned at | Framework LOC | .py files | Public API | Packages installed |")
    print(f"|{'-' * (width + 2)}|---|---:|---:|---:|---:|")
    for label, version, loc, files, api, deps in rows:
        print(f"| {label.ljust(width)} | {version} | {loc:,} | {files:,} | "
              f"{api if api is not None else '-'} | {deps if deps is not None else '-'} |")


if __name__ == "__main__":
    main()
