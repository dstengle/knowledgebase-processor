# Sub-Task: List ADR Files

**Goal:**
List all Markdown files (ADRs) in the `{{workspace}}/docs/architecture/decisions/` directory.
Exclude the template file `0000-adr-template.md`.

**Input:**
- Directory path: [`docs/architecture/decisions/`](docs/architecture/decisions/)

**Output:**
- A JSON file named `adr_file_paths.json` in your task's artifact directory (`{{workspace}}/.rooroo/tasks/ROO#SUB_consolidate_adrs_for_devs_S001/artifacts/rooroo-analyzer/`).
- This JSON file should contain a single array of strings, where each string is the full relative path (from `{{workspace}}`) to an ADR file (e.g., `["docs/architecture/decisions/0001-python-as-implementation-language.md", ...]`).

**Parent Task Context:**
- [`{{workspace}}/.rooroo/tasks/ROO#PLAN_20250509194005_consolidate_adrs_for_devs/context.md`](../ROO#PLAN_20250509194005_consolidate_adrs_for_devs/context.md)