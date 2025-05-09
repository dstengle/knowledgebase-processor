# Plan Overview for Task: ROO#PLAN_20250509194005_consolidate_adrs_for_devs

**Parent Task Goal:** Consolidate ADRs for developer implementation. Make a consolidated version of the ADRs with only the pertinent information for implementation so that the developer has concise instructions to follow with respect to architecture decisions. This file will be overwritten over time with a new consolidated view as new ADRs are added.

**Parent Task Context:** [`{{workspace}}/.rooroo/tasks/ROO#PLAN_20250509194005_consolidate_adrs_for_devs/context.md`](../tasks/ROO#PLAN_20250509194005_consolidate_adrs_for_devs/context.md)

## Sub-Tasks:

1.  **Task ID:** `ROO#SUB_consolidate_adrs_for_devs_S001`
    *   **Expert:** `rooroo-analyzer`
    *   **Goal:** List all Markdown files (ADRs) in the `{{workspace}}/docs/architecture/decisions/` directory. Exclude `0000-adr-template.md`. Output the list of full file paths as a JSON array to `{{workspace}}/.rooroo/tasks/ROO#SUB_consolidate_adrs_for_devs_S001/artifacts/rooroo-analyzer/adr_file_paths.json`.
    *   **Context:** [`{{workspace}}/.rooroo/tasks/ROO#SUB_consolidate_adrs_for_devs_S001/context.md`](../tasks/ROO#SUB_consolidate_adrs_for_devs_S001/context.md)

2.  **Task ID:** `ROO#SUB_consolidate_adrs_for_devs_S002`
    *   **Expert:** `rooroo-documenter`
    *   **Goal:** For each ADR file path provided in `{{workspace}}/.rooroo/tasks/ROO#SUB_consolidate_adrs_for_devs_S001/artifacts/rooroo-analyzer/adr_file_paths.json`, read the file and extract the content under the '## Decision' heading. Store these extractions in a JSON object in `{{workspace}}/.rooroo/tasks/ROO#SUB_consolidate_adrs_for_devs_S002/artifacts/rooroo-documenter/extracted_decisions.json`, mapping file path to decision text.
    *   **Context:** [`{{workspace}}/.rooroo/tasks/ROO#SUB_consolidate_adrs_for_devs_S002/context.md`](../tasks/ROO#SUB_consolidate_adrs_for_devs_S002/context.md)
    *   **Depends on:** `ROO#SUB_consolidate_adrs_for_devs_S001`

3.  **Task ID:** `ROO#SUB_consolidate_adrs_for_devs_S003`
    *   **Expert:** `rooroo-documenter`
    *   **Goal:** Consolidate extracted ADR decisions from `{{workspace}}/.rooroo/tasks/ROO#SUB_consolidate_adrs_for_devs_S002/artifacts/rooroo-documenter/extracted_decisions.json` into `{{workspace}}/docs/architecture/consolidated_adr_summary.md` and also save a copy to `{{workspace}}/.rooroo/tasks/ROO#SUB_consolidate_adrs_for_devs_S003/artifacts/rooroo-documenter/consolidated_adr_summary.md`.
    *   **Context:** [`{{workspace}}/.rooroo/tasks/ROO#SUB_consolidate_adrs_for_devs_S003/context.md`](../tasks/ROO#SUB_consolidate_adrs_for_devs_S003/context.md)
    *   **Depends on:** `ROO#SUB_consolidate_adrs_for_devs_S002`