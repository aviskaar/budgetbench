---
phase: 07-cli-profile-command
plan: 07
type: execute
wave: 1
depends_on: ["06-06"]
files_modified: [src/budgetbench/cli.py, src/budgetbench/profile.py, src/budgetbench/__init__.py, tests/test_profile.py]
autonomous: true
requirements: [PROF-04, PROF-05]
---

<objective>
Build the `budgetbench profile` CLI command that prints a human-readable hardware report with model+tier recommendation, plus `--json` export. Also expose `budgetbench.profile()` as a Python callable.

Purpose: Give users a one-command way to discover their optimal model + budget tier.
Output: CLI module, profile module, tests.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
</execution_context>

<context>
@.planning/ROADMAP.md
@.planning/phases/07-cli-profile-command/07-CONTEXT.md
</context>

<tasks>

<task type="auto">
   <name>Task 1: Implement profile() function</name>
   <files>src/budgetbench/profile.py</files>
   <action>
    Create `src/budgetbench/profile.py` with a `profile()` function:
     - Import `detect_hardware` from `budgetbench.utils.hardware`.
     - Import `detect_best_model` from `budgetbench.utils.recommendation`.
     - Call `detect_hardware()` to get HardwareReport.
     - Call `detect_best_model(report)` to get RecommendationReport.
     - Merge both dicts into a single dict with keys: `hardware` (the hardware report) and `recommendation` (the recommendation report).
     - Return the merged dict.
   </action>
   <verify>
     <automated>python -c "from budgetbench.profile import profile; print(profile()['recommendation']['model_name'])"</automated>
   </verify>
   <done>profile() function combines hardware detection and recommendation into a single return value.</done>
</task>

<task type="auto">
   <name>Task 2: Wire up package export</name>
   <files>src/budgetbench/__init__.py</files>
   <action>
    Update `src/budgetbench/__init__.py` to export `profile`:
     - `from .profile import profile`
     - This enables `import budgetbench; budgetbench.profile()`
   </action>
   <verify>
     <automated>python -c "import budgetbench; r = budgetbench.profile(); assert 'recommendation' in r"</automated>
   </verify>
   <done>budgetbench.profile() is importable and returns the combined report dict.</done>
</task>

<task type="auto">
   <name>Task 3: Implement CLI entry point</name>
   <files>src/budgetbench/cli.py</files>
   <action>
    Create `src/budgetbench/cli.py` with argparse:
     - Subcommand: `budgetbench profile`
     - Flag: `--json` — outputs JSON instead of formatted text
     - On `profile`: call `profile()`, format as human-readable text or JSON, print to stdout
     - Formatted output:
       ```
       BudgetBench Hardware Profile
       ============================
       GPU:      <model or CPU-only>
       VRAM:     <GB> GB
       CPU:      <model> (<cores> cores)
       RAM:      <GB> GB

       Recommendation: <model_name> @ <tier> tier
       VRAM needed: <needed> GB / <available> GB
       ```
     - `if __name__ == "__main__"` guard with argparse setup.
   </action>
   <verify>
     <automated>python -m budgetbench.cli profile</automated>
   </verify>
   <done>CLI prints formatted hardware report with recommendation on `budgetbench profile`.</done>
</task>

<task type="auto">
   <name>Task 4: Write tests</name>
   <files>tests/test_profile.py</files>
   <action>
    Write tests for profile functionality:
     - `test_profile_returns_dict`: profile() returns dict with 'hardware' and 'recommendation' keys.
     - `test_profile_hardware_keys`: hardware dict has expected keys (gpu_model, vram_gb, cpu_model, cpu_cores, ram_gb, cpu_only).
     - `test_profile_recommendation_keys`: recommendation dict has expected keys (model_name, budget_tier, vram_needed_gb, etc.).
     - `test_profile_json_output`: verify JSON serialization works (json.dumps doesn't raise).
     - `test_importable`: `import budgetbench; budgetbench.profile()` works.
   </action>
   <verify>
     <automated>python -m pytest tests/test_profile.py -v</automated>
   </verify>
   <done>All profile tests pass.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries
| Boundary | Description |
|----------|-------------|
| CLI → hardware detection | Trusted local execution, no network |

## STRIDE Threat Register
| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-07-07-01 | Injection | CLI args | n/a | argparse handles all parsing, no shell invocation. |
</threat_model>

<verification>
1. `budgetbench profile` prints formatted hardware report with recommendation.
2. `budgetbench profile --json` outputs valid JSON.
3. `import budgetbench; budgetbench.profile()` returns the combined report dict.
4. All tests pass.
</verification>

<success_criteria>
1. Running `budgetbench profile` prints a formatted hardware report showing GPU, CPU, RAM, and model+tier recommendation.
2. Running `budgetbench profile --json` outputs valid JSON containing the same hardware data and recommendation.
3. The CLI command is importable and callable from Python: `budgetbench.profile()` returns the report dict.
</success_criteria>

<output>
After completion, create `.planning/phases/07-cli-profile-command/07-SUMMARY.md` and `07-VERIFICATION.md`
</output>
