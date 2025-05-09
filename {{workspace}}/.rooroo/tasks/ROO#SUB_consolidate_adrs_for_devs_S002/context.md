# Sub-Task: Extract "Decision" Sections from ADRs

**Goal:**
For each ADR file path provided in the input JSON, read the ADR file and extract the content under the "## Decision" heading (and any sub-headings under it, until the next H2 heading or end of file).

**Input:**
- JSON file path from previous step: [`{{workspace}}/.rooroo/tasks/ROO#SUB_consolidate_adrs_for_devs_S001/artifacts/rooroo-analyzer/adr_file_paths.json`](../ROO#SUB_consolidate_adrs_for_devs_S001/artifacts/rooroo-analyzer/adr_file_paths.json)
  (This file contains a JSON array of ADR file paths relative to `{{workspace}}`.)

**Output:**
- A JSON file named `extracted_decisions.json` in your task's artifact directory (`{{workspace}}/.rooroo/tasks/ROO#SUB_consolidate_adrs_for_devs_S002/artifacts/rooroo-documenter/`).
- This JSON file should contain a single JSON object where keys are the ADR file paths (e.g., `"docs/architecture/decisions/0001-python-as-implementation-language.md"`) and values are the extracted "Decision" section content as a string.
  Example:
  ```json
  {
    "docs/architecture/decisions/0001-python-as-implementation-language.md": "Python will be the primary language...",
    "docs/architecture/decisions/0002-pydantic-for-data-models.md": "Pydantic will be used for data modeling..."
  }
  ```

**Parent Task Context:**
- [`{{workspace}}/.rooroo/tasks/ROO#PLAN_20250509194005_consolidate_adrs_for_devs/context.md`](../../ROO#PLAN_20250509194005_consolidate_adrs_for_devs/context.md)