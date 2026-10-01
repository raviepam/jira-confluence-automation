# Module 10 Completion Report

## Instruction Files
```text
instructions/create-status-report.agent.md
instructions/creating-instructions.agent.md
instructions/identify-repeated-task-patterns.agent.md
instructions/main.agent.md
```

## main.agent.md Contents
```markdown
# Instructions Catalog

Each entry links to a focused project instruction. Load the linked file completely when its keywords match the task.

- [`./create-status-report.agent.md`](./create-status-report.agent.md) — Create concise weekly status reports.
  + Keywords: weekly status, status report, accomplishments, blockers, next week
- [`./creating-instructions.agent.md`](./creating-instructions.agent.md) — Create and maintain project instructions and their IDE entry points.
  + Keywords: create instruction, update instruction, instruction catalog, Copilot setup
- [`./identify-repeated-task-patterns.agent.md`](./identify-repeated-task-patterns.agent.md) — Identify recurring patterns and consolidation opportunities in task backlogs.
  + Keywords: repeated tasks, recurring patterns, duplicate backlog items, consolidate tasks
```

## Sample Instruction
- File: instructions/identify-repeated-task-patterns.agent.md
- Contents:
```text
- **Input format:** Accept a Markdown backlog or an explicit path to one. Read the complete source, including task IDs, phase headings, descriptions, dependencies, and status markers. If the source is missing or inaccessible, ask for it instead of inferring tasks.
- **Processing:** Extract each task's action, target, outcome, phase, dependencies, and status; normalize wording while preserving meaning.
- **Processing:** Group tasks that repeat the same action or deliverable across the backlog. Cite task IDs for every group and describe the shared pattern briefly.
- **Processing:** Distinguish exact duplicates from intentional lifecycle repetition, such as defining, implementing, integrating, testing, and documenting the same capability.
- **Processing:** Identify consolidation opportunities by proposing shared acceptance criteria, a parent task, or cross-references; preserve necessary phase-specific ownership and verification.
- **Output format:** Return Markdown with a `Repeated Patterns` section and a `Consolidation Opportunities` section. Use bullets that include task IDs, the overlap, and whether the repetition is duplicative or intentional.
- **Output format:** If no meaningful repetition exists, state that in one bullet and do not invent patterns.
- **Constraints:** Do not edit the backlog unless explicitly asked. Do not mark tasks complete, change priorities, or assume statuses beyond the source.
- **Constraints:** Do not label tasks duplicates solely because they share a topic; compare their action, deliverable, and acceptance outcome.
- **Constraints:** Keep findings concise, factual, and actionable. Preserve uncertainty and do not infer unstated dependencies.
```
