# Evaluation Methodology for Contract-Agent

## Scope and Purpose

This document formalizes the evaluation methodology used by the Critic agent to assess contract modifications produced by the Actor agent. It is conceptual and implementation-agnostic, intended for an academic and engineering audience. The goals are repeatability, auditability, and alignment with legal correctness and formatting integrity (RTF preservation).

## Design Principles

- Completeness over surface similarity: verify that all requested changes are implemented everywhere they apply.
- Legal coherence and enforceability: changes must not introduce contradictions or weaken legal validity.
- Formatting integrity: preserve the exact RTF structure; content edits must not corrupt formatting.
- Conservative scoring: uncertainty is treated as failure with explicit rationale.
- Machine-readability: outputs are structured for automated gating and analytics.

## Evaluation Dimensions and Weights

The Critic computes a weighted composite score across five dimensions:

- Entity substitution completeness — 25%
- Jurisdiction transformation accuracy — 20%
- Liability reallocation correctness — 20%
- Clause operations success — 20%
- Legal coherence maintenance — 15%

These dimensions are evaluated on a 0.0–1.0 scale each, then combined using the listed weights into an overall score in [0.0, 1.0].

## Critical Failure Triggers (Automatic Deductions)

Certain failure modes carry explicit penalties to the overall score:

- Any broken cross-reference: −0.20
- Missing entity updates: −0.15 per instance
- Incorrect liability direction: −0.20
- Orphaned clauses or definitions: −0.10 per instance
- RTF formatting corruption: −0.10

These penalties are applied conservatively in addition to per-criterion scores.

## Termination Criteria and Quality Gate

- Minimum acceptable overall score: 0.85.
- If `overall_score ≥ 0.85` and no critical failures remain, the evaluation is considered satisfied.
- If `overall_score < 0.85`, the system triggers bounded refinement (up to the configured maximum iterations). If still unsatisfied, a structured failure report is returned.

## Evaluation Process

1. Align on scope: restate user instructions and identify intended changes.
2. Compare original vs. modified artifacts systematically (text and structure).
3. Verify each requested change is fully and correctly implemented.
4. Detect unintended changes and omissions.
5. Validate legal coherence (enforceability, absence of contradictions, correct renumbering/cross-references).
6. Check formatting integrity and document structure (no corruption of RTF elements).
7. Assign per-criterion scores and apply failure penalties as needed.
8. Compute overall weighted score and determine satisfaction.
9. Generate actionable feedback and revision suggestions where required.

## Machine-Readable Output Schema

The Critic produces a JSON evaluation suitable for automated gating and analytics. The following schema illustrates the expected shape (values are examples):

```json
{
  "overall_score": 0.92,
  "criteria_scores": {
    "entity_substitution": 0.95,
    "jurisdiction_transformation": 0.88,
    "liability_reallocation": 0.90,
    "clause_operations": 0.93,
    "legal_coherence": 0.91
  },
  "satisfied": true,
  "unmet_criteria": [],
  "feedback": "Targeted, actionable guidance for any deficiencies",
  "attempt_number": 2,
  "revision_suggestions": [
    {
      "reason": "why change is needed",
      "target_section": "specific location identifier",
      "action": "add/delete/replace/edit",
      "instruction": "precise edit instruction",
      "text_to_insert": "RTF snippet if applicable",
      "constraints": ["maintain numbering", "update cross-references"]
    }
  ],
  "red_flags": ["potential legal risks introduced by modifications"]
}
```

Notes:
- Criteria keys and penalty logic are aligned with the evaluation dimensions listed above.
- Feedback and revision suggestions must be specific and actionable.

## Illustrative Scoring Example (Conceptual)

- Instructions: replace `Entity A` with `Entity B` everywhere; change governing law from `Jurisdiction X` to `Jurisdiction Y`; reverse indemnification.
- Observations: one missed occurrence of `Entity A` (−0.15), all other replacements complete; governing law updated but one forum reference remained outdated; indemnification reversed correctly; numbering cascaded; no cross-reference breakage; RTF integrity preserved.
- Example per-criterion scores: entity substitution 0.85, jurisdiction 0.80, liability 0.95, clause ops 0.92, legal coherence 0.90; overall ≈ 0.88 after weighting and penalty.
- Outcome: satisfied (≥ 0.85) with feedback to fix the residual forum reference.

## Governance and Change Control

- Policy ownership: evaluation criteria and weights are governed centrally to ensure consistency across runs and environments.
- Change management: modify criteria/weights via configuration with documented rationale, impact analysis, and rollback plan.
- Regression discipline: apply the same evaluation to a representative sample of historical cases when criteria change.
- Auditability: persist evaluation artifacts (scores, feedback) in a privacy-compliant manner for later review.

## Limitations and Threats to Validity

- Ambiguity in instructions may lead to conservative failing scores; ensure instructions are specific.
- Over-penalization can occur if detectors are too sensitive; calibrate thresholds with gold sets.
- RTF parsing anomalies (from source files) can masquerade as formatting corruption; isolate parser effects during diagnostics.
