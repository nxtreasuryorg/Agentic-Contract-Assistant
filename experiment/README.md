# Experimental Contract Manipulation Evaluation

Judge-led critic loop for semantic contract edits across multiple models, with brief RTF reporting and dynamic configuration. All work is isolated to `exp/` (does not modify `nxtChat/`).

## Overview
- **Inputs**: Original contracts (RTF), scenario JSONs describing edits (counterparty, domicile, blame/liability shift, clause add/delete), acceptance criteria.
- **Flow**: Generate → Judge (LLM-as-judge) → Revise (using judge suggestions) for up to 5 attempts per model. Early stop on satisfaction; otherwise mark unsatisfied.
- **Outputs**: Brief `report.rtf` with metrics and statuses, plus a `manifest.json` and per-attempt artifacts.
- **Providers**: AWS Bedrock (Converse API) and optional SageMaker deployed endpoints. Credentials are loaded from `Agent-3.0/.env` (configurable).

## Directory Layout
- `converted/rtf/`
  - `legal agreement 2.rtf` (sample_1)
  - `sample 2.rtf` (sample_2)
- `prompts/`
  - `sample_1_generate.jinja`, `sample_1_judge.jinja`, `sample_1_revise.jinja`
  - `sample_2_generate.jinja`, `sample_2_judge.jinja`, `sample_2_revise.jinja`
- `config/config.yaml` (dynamic settings; no hardcoding in code)
- `runners/evaluate.py` (CLI orchestrator)
- `scenarios/`
  - `schema.json` (scenario shape)
  - `example_sample_1.json` (example scenario)
- `results/<timestamp>/` (reports and artifacts per run)

## Setup
1. use conda activate contract
2. Verify AWS credentials and region are available. By default, we load from `Agent-3.0/.env` as configured in `config/config.yaml`.

Environment variables expected (in `.env` or your environment):
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_SESSION_TOKEN` (if applicable)
- `AWS_REGION` or `AWS_DEFAULT_REGION`

## Configuration
Edit `exp/config/config.yaml` to adjust everything dynamically:
- **credentials.dotenv_path**: default `../Agent-3.0/.env` (relative to `exp/`), points to `/home/ec2-user/cb/Agent-3.0/.env`.
- **dataset**: maps logical keys to document filenames under `converted/rtf/`.
- **prompts**: per-document mapping to Jinja templates.
- **judge**: judge model ID (Bedrock), thresholds, and `max_attempts` (default 5).
- **models**: roster to evaluate. Each item:
  - `provider: bedrock` with `id` like `ai21.j2-mid-v1`, `amazon.titan-text-premier-v1:0`, etc.
  - `provider: sagemaker_endpoint` with `id` set to an existing endpoint name you manage.
- **runtime**: timeouts and parallelism.
- **acceptance_criteria**: default weights and required criteria (can be overridden per-scenario).

## Scenarios
- Define scenario JSON under `exp/scenarios/` (see `schema.json`).
- Include any of:
  - `counterparty_update` (name, registration_code, VAT, address, email)
  - `domicile_shift` (governing_law, venue, arbitration_body, arbitration_rules)
  - `blame_shift` (from_party, to_party, clauses)
  - `clause_add` (array of {tag, insert_after_section, rtf_text})
  - `clause_delete` (array of {section, reason})
- Optionally override `acceptance_criteria` for that scenario.

Example: `scenarios/example_sample_1.json` is provided for quick smoke testing.

## Running an Evaluation
From the `exp/` directory, run the CLI to process a document key with a scenario file:

```bash
python3 runners/evaluate.py --document sample_1 --scenario scenarios/example_sample_1.json
```

Flags:
- `--config` to point to a different YAML (default `config/config.yaml`).
- `--document` must be one of `sample_1` (HashKey brokerage) or `sample_2` (Vespia T&C).
- `--scenario` is a path to your scenario JSON.

On success, the command prints the path to the new run folder under `results/<timestamp>/`.

## Outputs
Each run creates a folder `results/<timestamp>/` containing:
- `report.rtf` (brief summary per model with status, attempts, runtimes, average judge score, and artifacts path)
- `manifest.json` (full run metadata, models, judge settings, attempts, metrics)
- `models/<model-id-sanitized>/attempt_k/`
  - `gen_prompt.txt`, `candidate.rtf`
  - `judge_prompt.txt`, `judge.json` (or `judge_raw.txt` if JSON parse fails)

If a model remains unsatisfied after `max_attempts` (default 5), the report includes a note and the `judge.json` highlights `unmet_criteria` and `revision_suggestions`.

## Judge-led Critic Loop
- The judge determines whether instructions were correctly processed and provides structured `revision_suggestions`.
- The loop runs up to `max_attempts`. If `overall_satisfied` and `instruction_followed` are both true, we stop early.
- Otherwise, we apply `revise` prompts using the judge’s suggestions and iterate.

## Adding/Changing Models
- **Bedrock**: add to `models` with `provider: bedrock` and the `id` of the model (e.g., `mistral.mistral-large-2407-v1:0`). Ensure your AWS account has access.
- **SageMaker endpoint**: add to `models` with `provider: sagemaker_endpoint` and set `id` to the deployed endpoint name. This framework does not auto-deploy endpoints.

## Notes & Constraints
- Do not hardcode models, credentials, or paths in code. Use `config/config.yaml`.
- Keep experiments in `exp/`; do not modify `nxtChat/` unless explicitly instructed.
- Prompts are document-specific and live under `prompts/`. Adjust as needed, but keep output formats strict (RTF for generate/revise; JSON for judge).

## Troubleshooting
- Missing credentials: verify `Agent-3.0/.env` and that `credentials.dotenv_path` resolves correctly.
- Access errors on models: confirm Bedrock model availability and AWS region; for SageMaker, confirm the endpoint exists and is in the same region.
- Judge JSON parse failures: the system captures raw output and continues with a conservative revision suggestion. You can tune judge prompts or thresholds in config.
