# Marketplace development contract

Read root `CLAUDE.md` for the repository's existing marketplace constraints and commands; its Claude entry point imports this file. This file adds agent-neutral maintenance policy without moving those rules. Read `docs/protected-main.md` for automation architecture, validation, CI and recovery. No vault access is needed for development checks.

Use a named feature branch and a separate worktree per editing agent; never change another checkout. Run the online `python3 scripts/validate-marketplace.py` and `python3 -m unittest discover -s tests -v` for automation changes. Do not run the bumper against actual manifests merely to test it: use disposable fixtures or an explicitly authorized pin update. No automatic merge, force push, bypass of main protection or plugin release is authorized by a documentation task.

## Code and documentation

Code must explain its own intent through precise names, coherent functions and explicit contracts. Add docstrings or nearby comments for non-obvious inputs/outputs, side effects, failure behavior, invariants and the reasons behind important decisions; do not narrate obvious statements. Complement the code with repository architecture/design documents and operational runbooks. Update code, related docs, examples and tests together in the same PR. Preserve one authoritative implementation of each policy; client adapters refer to it. Documentation is part of completion, not a later task. A reviewer must be able to understand, operate and modify the change without this conversation or private agent memory.
