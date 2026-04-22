# Copilot Instructions

Python pipeline for importing bank transaction CSVs, cleaning and categorizing rows, enriching locations, and exporting analysis-ready CSV files.

## Stack

| Category | Tools |
|---|---|
| Language | Python |
| Core deps | pandas, numpy |
| Automation | GitHub Actions, pre-commit |
| Config | Poetry, pyproject.toml |
| Logging | loguru |
| Testing | pytest, hypothesis |
| Quality | ruff, black, isort, mypy |

## Language

- Always use English in all responses, comments, commit messages, documentation, and any other output — no exceptions.

## Planning

- Save all plans to `.agent/plans/` folder
- Naming convention: `{sequence}.{plan-name}.md` (e.g., `1.auth-setup.md`, `2.document-ingestion.md`)
- Plans should be detailed enough to execute without ambiguity
- Each task in the plan must include at least one validation test to verify it works
- Assess complexity and single-pass feasibility - can an agent realistically complete this in one go?
- Include a complexity indicator at the top of each plan:
  - ✅ **Simple** - Single-pass executable, low risk
  - ⚠️ **Medium** - May need iteration, some complexity
  - 🔴 **Complex** - Break into sub-plans before executing

## Development Flow

1. **Plan** - Create a detailed plan and save it to `.agent/plans/`
2. **Build** - Execute the plan to implement the feature
3. **Validate** - Test and verify the implementation works correctly. Use browser testing where applicable via an appropriate MCP
4. **Iterate** - Fix any issues found during validation

## Progress

Check PROGRESS.md for current module status. Update it as you complete tasks.
