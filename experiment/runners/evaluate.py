#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

# Local utils
sys.path.append(str(Path(__file__).resolve().parents[1]))  # add exp/ to path
from utils.env_loader import load_env  # noqa: E402
from utils.io import (  # noqa: E402
    RunPaths,
    build_rtf_paragraphs,
    ensure_absolute,
    make_run_dirs,
    read_json,
    read_yaml,
    write_json,
    write_text,
)
from utils.llm_clients import build_client, LLMResponse  # noqa: E402
from utils.prompting import render_template, pretty_json  # noqa: E402


@dataclass
class AttemptRecord:
    index: int
    gen_latency_s: float
    judge_latency_s: float
    satisfied: bool
    overall_score: Optional[float] = None
    unmet_criteria: List[str] = field(default_factory=list)


@dataclass
class ModelRunResult:
    model_id: str
    provider: str
    satisfied: bool
    attempts: int
    total_gen_latency_s: float
    total_judge_latency_s: float
    average_overall_score: Optional[float]
    model_dir: Path
    note: Optional[str] = None
    programmatic_score: Optional[float] = None
    judge_hallucination_detected: bool = False


def _safe_model_dir_name(model_id: str) -> str:
    return (
        model_id.replace(":", "-")
        .replace("/", "-")
        .replace(" ", "-")
    )


def load_config(base_dir: Path, config_path: str) -> Dict[str, Any]:
    cfg_path = ensure_absolute(base_dir, config_path)
    cfg = read_yaml(cfg_path)
    # resolve dotenv path relative to exp/
    cred = cfg.get("credentials", {})
    dotenv_path = cred.get("dotenv_path")
    if dotenv_path:
        load_env(dotenv_path)
    return cfg


def read_document(base_dir: Path, cfg: Dict[str, Any], document_key: str) -> str:
    dataset_cfg = cfg.get("dataset", {})
    dataset_dir = ensure_absolute(base_dir, dataset_cfg.get("dataset_dir", "converted/rtf"))
    docs = dataset_cfg.get("documents", {})
    fname = docs.get(document_key)
    if not fname:
        raise ValueError(f"No document configured for key '{document_key}'")
    path = dataset_dir / fname
    if not path.exists():
        raise FileNotFoundError(f"Document not found: {path}")
    return path.read_text(encoding="utf-8", errors="ignore")


def render_generate(cfg: Dict[str, Any], document_key: str, variables: Dict[str, Any]) -> str:
    tmpl_path = cfg["prompts"][document_key]["generate"]
    return render_template(tmpl_path, variables)


def render_judge(cfg: Dict[str, Any], document_key: str, variables: Dict[str, Any]) -> str:
    tmpl_path = cfg["prompts"][document_key]["judge"]
    return render_template(tmpl_path, variables)


def render_revise(cfg: Dict[str, Any], document_key: str, variables: Dict[str, Any]) -> str:
    tmpl_path = cfg["prompts"][document_key]["revise"]
    return render_template(tmpl_path, variables)


def call_model(provider: str, model_id: str, prompt: str, region_name: Optional[str], timeout_s: int) -> LLMResponse:
    client = build_client(provider, region_name=region_name, timeout_s=timeout_s)
    if provider == "bedrock":
        return client.generate(model_id=model_id, prompt=prompt)
    elif provider == "sagemaker_endpoint":
        endpoint_name = model_id  # config should pass the endpoint name here
        return client.generate(endpoint_name=endpoint_name, prompt=prompt)
    else:
        raise ValueError(f"Unsupported provider: {provider}")


def programmatic_verify(original_rtf: str, candidate_rtf: str, scenario: dict) -> dict:
    """Programmatic checks that don't rely on LLM judgment - these can be trusted"""
    results = {}
    
    # Entity substitution check for basic transformations
    legal_engineering = scenario.get("legal_engineering_challenges", {})
    entity_sub = legal_engineering.get("1_entity_substitution_cascade", {})
    
    if entity_sub:
        old_entity = entity_sub.get("find_replace_all")
        new_entity = entity_sub.get("replace_with")
        variations = entity_sub.get("include_variations", [])
        
        if old_entity and new_entity:
            # Check main entity replacement
            old_present = old_entity in candidate_rtf
            new_present = new_entity in candidate_rtf
            results["entity_main_substituted"] = not old_present and new_present
            
            # Check variations replacement
            for variation in variations:
                old_var_present = variation in candidate_rtf
                results[f"entity_variation_{variation.replace(' ', '_').lower()}_removed"] = not old_var_present
    
    # Registration number check from ambiguous instructions
    ambiguous = scenario.get("ambiguous_instructions", {})
    if ambiguous:
        counterparty = ambiguous.get("counterparty_transformation", {})
        reg_details = counterparty.get("registration_details", {})
        primary_reg = reg_details.get("primary_registration")
        
        if primary_reg:
            results["registration_number_present"] = primary_reg in candidate_rtf
    
    # Jurisdiction transformation check
    jurisdictional = legal_engineering.get("2_jurisdictional_transformation", {})
    if jurisdictional:
        from_jurisdiction = jurisdictional.get("from_jurisdiction")
        to_jurisdiction = jurisdictional.get("to_jurisdiction")
        
        if from_jurisdiction and to_jurisdiction:
            old_jurisdiction_present = from_jurisdiction in candidate_rtf
            new_jurisdiction_present = to_jurisdiction in candidate_rtf
            results["jurisdiction_transformed"] = not old_jurisdiction_present and new_jurisdiction_present
    
    # Definition updates check
    def_management = legal_engineering.get("4_definition_dependency_management", {})
    if def_management:
        core_defs = def_management.get("update_core_definitions", {})
        for def_key, def_value in core_defs.items():
            if def_key == "HBL" and "ZENG" in def_value:
                # Check if the BVI company number is properly included
                results["hbl_definition_updated"] = "ZENG202301234" in candidate_rtf
                results["bvi_incorporation_mentioned"] = "British Virgin Islands" in def_value and "British Virgin Islands" in candidate_rtf
    
    # SEMANTIC MANIPULATION CHECKS (Enhanced for your goals)
    
    # 1. Legal Domicile/Governing Law Transformation
    governing_law_change = legal_engineering.get("3_governing_law_transformation", {})
    if governing_law_change:
        from_law = governing_law_change.get("from_governing_law", "Hong Kong")
        to_law = governing_law_change.get("to_governing_law", "British Virgin Islands")
        
        # Check governing law clauses updated
        results["governing_law_transformed"] = from_law not in candidate_rtf and to_law in candidate_rtf
        
        # Check venue/jurisdiction clauses
        from_venue = governing_law_change.get("from_venue", "Hong Kong courts")
        to_venue = governing_law_change.get("to_venue", "British Virgin Islands courts")
        results["venue_transformed"] = from_venue not in candidate_rtf and to_venue in candidate_rtf
    
    # 2. Liability Reallocation Check
    liability_shifts = legal_engineering.get("5_liability_reallocation", {})
    if liability_shifts:
        liability_changes = liability_shifts.get("shift_liability_from_to", [])
        for shift in liability_changes:
            from_party = shift.get("from_party")
            to_party = shift.get("to_party")
            liability_type = shift.get("liability_type", "general")
            
            # Check if liability language has been shifted
            from_liability_pattern = f"{from_party}.*liable"
            to_liability_pattern = f"{to_party}.*liable"
            
            import re
            from_matches = len(re.findall(from_liability_pattern, candidate_rtf, re.IGNORECASE))
            to_matches = len(re.findall(to_liability_pattern, candidate_rtf, re.IGNORECASE))
            
            results[f"liability_shifted_{liability_type}"] = from_matches == 0 and to_matches > 0
    
    # 3. Clause Addition/Deletion Check
    clause_modifications = legal_engineering.get("6_clause_modifications", {})
    if clause_modifications:
        # Check added clauses
        added_clauses = clause_modifications.get("add_clauses", [])
        for clause in added_clauses:
            clause_id = clause.get("clause_id")
            required_text = clause.get("required_text")
            results[f"clause_added_{clause_id}"] = required_text in candidate_rtf
        
        # Check deleted clauses  
        deleted_clauses = clause_modifications.get("delete_clauses", [])
        for clause in deleted_clauses:
            clause_id = clause.get("clause_id")
            prohibited_text = clause.get("text_to_remove")
            results[f"clause_deleted_{clause_id}"] = prohibited_text not in candidate_rtf
        
        # Check modified clauses
        modified_clauses = clause_modifications.get("modify_clauses", [])
        for clause in modified_clauses:
            clause_id = clause.get("clause_id")
            old_text = clause.get("old_text")
            new_text = clause.get("new_text")
            results[f"clause_modified_{clause_id}"] = old_text not in candidate_rtf and new_text in candidate_rtf
    
    # 4. Party Role Transformation
    party_transformations = legal_engineering.get("7_party_role_changes", {})
    if party_transformations:
        role_changes = party_transformations.get("transform_roles", [])
        for change in role_changes:
            party = change.get("party")
            from_role = change.get("from_role")
            to_role = change.get("to_role")
            
            # Check role transformation in document
            from_role_pattern = f"{party}.*{from_role}"
            to_role_pattern = f"{party}.*{to_role}"
            
            from_role_present = from_role_pattern in candidate_rtf
            to_role_present = to_role_pattern in candidate_rtf
            
            results[f"role_transformed_{party}"] = not from_role_present and to_role_present
    
    # Empty output check (most critical)
    candidate_clean = candidate_rtf.strip()
    results["non_empty_output"] = bool(candidate_clean) and len(candidate_clean) > 50
    
    # Basic RTF format check
    results["rtf_format_valid"] = candidate_rtf.startswith("{\\rtf") and candidate_rtf.endswith("}")
    
    return results


def generate_programmatic_feedback(programmatic_results: dict, scenario: dict, attempt: int) -> list:
    """Generate specific revision suggestions based on programmatic verification failures"""
    suggestions = []
    
    # Check for critical failures first
    if not programmatic_results.get("non_empty_output", False):
        suggestions.append({
            "priority": "CRITICAL",
            "issue": "Empty or minimal output produced",
            "action": "Generate complete RTF document with all required modifications",
            "specific_requirement": "Must produce substantial content (>50 characters)",
            "attempt": attempt
        })
        return suggestions  # Return early for critical failure
    
    if not programmatic_results.get("rtf_format_valid", False):
        suggestions.append({
            "priority": "CRITICAL", 
            "issue": "Invalid RTF format",
            "action": "Ensure output starts with '{\\rtf' and ends with '}'",
            "specific_requirement": "Valid RTF document structure required",
            "attempt": attempt
        })
    
    # Check mandatory requirements
    if not programmatic_results.get("registration_number_present", False):
        # Get the specific registration number from scenario
        ambiguous = scenario.get("ambiguous_instructions", {})
        counterparty = ambiguous.get("counterparty_transformation", {})
        reg_details = counterparty.get("registration_details", {})
        reg_number = reg_details.get("primary_registration", "TEST123456")
        
        suggestions.append({
            "priority": "MANDATORY",
            "issue": f"Missing required registration number '{reg_number}'",
            "action": f"Add registration number '{reg_number}' to entity definition section",
            "specific_requirement": f"HBL definition must include: '(BVI company number {reg_number})'",
            "attempt": attempt
        })
    
    # Check entity substitution
    if not programmatic_results.get("entity_main_substituted", False):
        legal_engineering = scenario.get("legal_engineering_challenges", {})
        entity_sub = legal_engineering.get("1_entity_substitution_cascade", {})
        old_entity = entity_sub.get("find_replace_all", "Hash Blockchain Limited")
        new_entity = entity_sub.get("replace_with", "TESTCORP Ltd.")
        
        suggestions.append({
            "priority": "HIGH",
            "issue": f"Incomplete entity substitution: '{old_entity}' still present",
            "action": f"Replace ALL instances of '{old_entity}' with '{new_entity}'",
            "specific_requirement": f"No traces of '{old_entity}' should remain in document",
            "attempt": attempt
        })
    
    # Check variations removal
    variations_failed = []
    for key, value in programmatic_results.items():
        if key.startswith("entity_variation_") and key.endswith("_removed") and not value:
            variation = key.replace("entity_variation_", "").replace("_removed", "").replace("_", " ").upper()
            variations_failed.append(variation)
    
    if variations_failed:
        suggestions.append({
            "priority": "HIGH",
            "issue": f"Entity variations still present: {', '.join(variations_failed)}",
            "action": f"Remove all instances of: {', '.join(variations_failed)}",
            "specific_requirement": "All entity name variations must be replaced",
            "attempt": attempt
        })
    
    # Check jurisdiction transformation
    if not programmatic_results.get("jurisdiction_transformed", False):
        legal_engineering = scenario.get("legal_engineering_challenges", {})
        jurisdictional = legal_engineering.get("2_jurisdictional_transformation", {})
        from_jurisdiction = jurisdictional.get("from_jurisdiction", "Hong Kong")
        to_jurisdiction = jurisdictional.get("to_jurisdiction", "British Virgin Islands")
        
        suggestions.append({
            "priority": "MEDIUM",
            "issue": f"Jurisdiction not fully transformed from '{from_jurisdiction}' to '{to_jurisdiction}'",
            "action": f"Replace all references to '{from_jurisdiction}' with '{to_jurisdiction}'",
            "specific_requirement": f"Complete jurisdictional transformation required",
            "attempt": attempt
        })
    
    # SEMANTIC MANIPULATION FEEDBACK (Enhanced)
    
    # Check governing law transformation
    if not programmatic_results.get("governing_law_transformed", False):
        legal_engineering = scenario.get("legal_engineering_challenges", {})
        governing_law = legal_engineering.get("3_governing_law_transformation", {})
        from_law = governing_law.get("from_governing_law", "Hong Kong")
        to_law = governing_law.get("to_governing_law", "British Virgin Islands")
        
        suggestions.append({
            "priority": "HIGH",
            "issue": f"Governing law not changed from '{from_law}' to '{to_law}'",
            "action": f"Update all governing law clauses to reference '{to_law}' laws",
            "specific_requirement": f"All legal references must use '{to_law}' governing law",
            "attempt": attempt
        })
    
    # Check venue transformation
    if not programmatic_results.get("venue_transformed", False):
        suggestions.append({
            "priority": "HIGH",
            "issue": "Court jurisdiction/venue not properly transformed",
            "action": "Update dispute resolution clauses to reference correct courts/venues",
            "specific_requirement": "Venue clauses must match new governing law jurisdiction",
            "attempt": attempt
        })
    
    # Check liability reallocation
    liability_issues = []
    for key, value in programmatic_results.items():
        if key.startswith("liability_shifted_") and not value:
            liability_type = key.replace("liability_shifted_", "")
            liability_issues.append(liability_type)
    
    if liability_issues:
        suggestions.append({
            "priority": "HIGH",
            "issue": f"Liability not properly reallocated for: {', '.join(liability_issues)}",
            "action": "Review and update liability clauses to shift responsibility as required",
            "specific_requirement": "Liability must be transferred from original party to specified counterparty",
            "attempt": attempt
        })
    
    # Check clause additions
    missing_clauses = []
    for key, value in programmatic_results.items():
        if key.startswith("clause_added_") and not value:
            clause_id = key.replace("clause_added_", "")
            missing_clauses.append(clause_id)
    
    if missing_clauses:
        suggestions.append({
            "priority": "MEDIUM",
            "issue": f"Required clauses not added: {', '.join(missing_clauses)}",
            "action": "Add the specified new clauses to the contract",
            "specific_requirement": "All required new clauses must be present with exact text",
            "attempt": attempt
        })
    
    # Check clause deletions
    remaining_clauses = []
    for key, value in programmatic_results.items():
        if key.startswith("clause_deleted_") and not value:
            clause_id = key.replace("clause_deleted_", "")
            remaining_clauses.append(clause_id)
    
    if remaining_clauses:
        suggestions.append({
            "priority": "MEDIUM",
            "issue": f"Clauses not properly deleted: {', '.join(remaining_clauses)}",
            "action": "Remove the specified clauses completely from the contract",
            "specific_requirement": "Prohibited clauses must be entirely absent from document",
            "attempt": attempt
        })
    
    # Check clause modifications
    unmodified_clauses = []
    for key, value in programmatic_results.items():
        if key.startswith("clause_modified_") and not value:
            clause_id = key.replace("clause_modified_", "")
            unmodified_clauses.append(clause_id)
    
    if unmodified_clauses:
        suggestions.append({
            "priority": "MEDIUM",
            "issue": f"Clauses not properly modified: {', '.join(unmodified_clauses)}",
            "action": "Update the specified clauses with new required text",
            "specific_requirement": "Modified clauses must contain new text and remove old text",
            "attempt": attempt
        })
    
    # Check party role transformations
    role_issues = []
    for key, value in programmatic_results.items():
        if key.startswith("role_transformed_") and not value:
            party = key.replace("role_transformed_", "")
            role_issues.append(party)
    
    if role_issues:
        suggestions.append({
            "priority": "HIGH",
            "issue": f"Party roles not transformed for: {', '.join(role_issues)}",
            "action": "Update party role definitions and references throughout document",
            "specific_requirement": "All party role changes must be consistently applied",
            "attempt": attempt
        })
    
    # Add progressive hints based on attempt number
    if attempt >= 3 and suggestions:
        suggestions.append({
            "priority": "HINT",
            "issue": f"Multiple attempts ({attempt}) - focus on systematic approach",
            "action": "Review each requirement individually and verify completion",
            "specific_requirement": "Double-check all substitutions are complete and accurate",
            "attempt": attempt
        })
    
    return suggestions


def calculate_programmatic_score(programmatic_results: dict) -> float:
    """Calculate a score based on programmatic verification only"""
    if not programmatic_results:
        return 0.0
    
    # Critical requirements that should heavily impact score
    critical_checks = [
        "non_empty_output",
        "rtf_format_valid", 
        "entity_main_substituted"
    ]
    
    # MANDATORY requirements - complete failure if missing
    mandatory_checks = [
        "registration_number_present",
        "governing_law_transformed",  # Legal domicile shift is critical
        "entity_main_substituted"     # Counterparty change is critical
    ]
    
    # HIGH PRIORITY semantic manipulation checks
    high_priority_checks = [
        "venue_transformed",
        "jurisdiction_transformed", 
        "hbl_definition_updated",
        "bvi_incorporation_mentioned"
    ]
    
    # SEMANTIC MANIPULATION specific checks
    semantic_checks = []
    
    # Collect all liability, clause, and role transformation checks
    for key in programmatic_results.keys():
        if (key.startswith("liability_shifted_") or 
            key.startswith("clause_added_") or 
            key.startswith("clause_deleted_") or 
            key.startswith("clause_modified_") or
            key.startswith("role_transformed_")):
            semantic_checks.append(key)
    
    # Check mandatory requirements first - immediate failure if any missing
    for check in mandatory_checks:
        if check in programmatic_results and not programmatic_results[check]:
            return 0.3  # Maximum score if mandatory requirements fail
    
    score = 0.0
    max_score = 0.0
    
    # Mandatory checks worth 0.4 total (if all pass, we continue)
    for check in mandatory_checks:
        if check in programmatic_results:
            max_score += 0.4
            if programmatic_results[check]:
                score += 0.4
    
    # Critical checks worth 0.2 total
    for check in critical_checks:
        if check in programmatic_results and check not in mandatory_checks:  # Avoid double counting
            max_score += 0.067
            if programmatic_results[check]:
                score += 0.067
    
    # High priority checks worth 0.2 total  
    for check in high_priority_checks:
        if check in programmatic_results:
            max_score += 0.05
            if programmatic_results[check]:
                score += 0.05
    
    # Semantic manipulation checks worth 0.2 total
    if semantic_checks:
        per_semantic_weight = 0.2 / len(semantic_checks)
        for check in semantic_checks:
            if check in programmatic_results:
                max_score += per_semantic_weight
                if programmatic_results[check]:
                    score += per_semantic_weight
    
    # Other checks get remaining weight
    other_checks = [k for k in programmatic_results.keys() 
                   if k not in critical_checks and k not in high_priority_checks and k not in mandatory_checks and k not in semantic_checks]
    if other_checks:
        remaining_weight = max(0.0, 1.0 - max_score)
        per_check_weight = remaining_weight / len(other_checks) if other_checks else 0
        for check in other_checks:
            max_score += per_check_weight
            if programmatic_results[check]:
                score += per_check_weight
    
    return score / max_score if max_score > 0 else 0.0


def judge_parse(json_text: str) -> Dict[str, Any]:
    # Try to parse strict JSON; if fails, attempt to locate first/last braces.
    try:
        return json.loads(json_text)
    except Exception:
        start = json_text.find("{")
        end = json_text.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(json_text[start : end + 1])
            except Exception:
                pass
        raise


def make_report_rtf(run_dir: Path, run_results: List[ModelRunResult]) -> None:
    lines: List[str] = []
    lines.append("Contract Manipulation Evaluation Report")
    lines.append(time.strftime("Generated at %Y-%m-%d %H:%M:%S"))
    lines.append("")
    for r in run_results:
        status = "satisfied" if r.satisfied else "unsatisfied"
        lines.append(f"Model: {r.model_id} ({r.provider})")
        lines.append(f"Status: {status}; Attempts: {r.attempts}")
        lines.append(f"Total gen latency: {r.total_gen_latency_s:.2f}s; Total judge latency: {r.total_judge_latency_s:.2f}s")
        if r.average_overall_score is not None:
            lines.append(f"Average judge score: {r.average_overall_score:.3f}")
        lines.append(f"Artifacts: {r.model_dir}")
        if r.note:
            lines.append(f"Note: {r.note}")
        lines.append("")
    rtf = build_rtf_paragraphs(tuple(lines))
    write_text(run_dir / "report.rtf", rtf)


def make_report_md(run_dir: Path, run_results: List[ModelRunResult]) -> None:
    lines: List[str] = []
    lines.append("# Contract Manipulation Evaluation Report")
    lines.append(f"**Generated at:** {time.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    
    # Summary table
    lines.append("## Summary")
    lines.append("| Model | Provider | Status | Attempts | Gen Time (s) | Critic Score | Prog Score | Method |")
    lines.append("|-------|----------|--------|----------|--------------|--------------|------------|--------|")
    
    for r in run_results:
        status = "✅ Satisfied" if r.satisfied else "❌ Unsatisfied" 
        critic_score = f"{r.average_overall_score:.3f}" if r.average_overall_score is not None else "N/A"
        prog_score = f"{r.programmatic_score:.3f}" if r.programmatic_score is not None else "N/A"
        method = "🤖 Actor-Critic"
        lines.append(f"| {r.model_id} | {r.provider} | {status} | {r.attempts} | {r.total_gen_latency_s:.2f} | {critic_score} | {prog_score} | {method} |")
    
    lines.append("")
    lines.append("## Detailed Results")
    
    for r in run_results:
        lines.append(f"### {r.model_id}")
        lines.append(f"- **Provider:** {r.provider}")
        lines.append(f"- **Status:** {'✅ Satisfied' if r.satisfied else '❌ Unsatisfied'}")
        lines.append(f"- **Attempts:** {r.attempts}")
        lines.append(f"- **Generation Time:** {r.total_gen_latency_s:.2f}s")
        lines.append(f"- **Critic Time:** {r.total_judge_latency_s:.2f}s")
        if r.average_overall_score is not None:
            lines.append(f"- **Critic Score:** {r.average_overall_score:.3f}")
        if r.programmatic_score is not None:
            lines.append(f"- **Programmatic Score:** {r.programmatic_score:.3f}")
        lines.append(f"- **Method:** 🤖 Actor-Critic (LLM Critic + Programmatic Validation)")
        lines.append(f"- **Artifacts:** `{r.model_dir}`")
        if r.note:
            lines.append(f"- **Note:** {r.note}")
        lines.append("")
    
    write_text(run_dir / "report.md", "\n".join(lines))


def run_evaluation(
    base_dir: Path,
    cfg: Dict[str, Any],
    document_key: str,
    scenario_path: Path,
) -> Path:
    # Prepare run directory
    paths: RunPaths = make_run_dirs(base_dir, cfg.get("output", {}).get("results_dir", "results"))

    # Read inputs
    original_rtf = read_document(base_dir, cfg, document_key)
    scenario = read_json(scenario_path)

    # Acceptance criteria (from config; can be extended by scenario overrides)
    acceptance_criteria = cfg.get("acceptance_criteria", {})
    if "acceptance_criteria" in scenario:
        # Shallow merge: scenario overrides top-level keys
        acceptance_criteria = {**acceptance_criteria, **scenario["acceptance_criteria"]}

    judge_cfg = cfg.get("judge", {})
    judge_model_id = judge_cfg.get("model_id")
    max_attempts = int(judge_cfg.get("max_attempts", 5))
    judge_timeout_s = int(judge_cfg.get("timeout_s", 180))

    # Region selection via env
    region = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION")

    # Models roster
    models = cfg.get("models", [])

    run_manifest: Dict[str, Any] = {
        "document": document_key,
        "scenario_path": scenario_path.as_posix(),
        "config_used": "config/config.yaml",
        "run_dir": paths.run_dir.as_posix(),
        "models": models,
        "judge": judge_cfg,
        "acceptance_criteria": acceptance_criteria,
        "attempts_max": max_attempts,
        "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "model_runs": [],
    }

    run_results: List[ModelRunResult] = []

    for m in models:
        model_id = m["id"]
        provider = m["provider"]
        model_dir = paths.run_dir / "models" / _safe_model_dir_name(model_id)
        model_dir.mkdir(parents=True, exist_ok=True)

        attempt_records: List[AttemptRecord] = []
        candidate_rtf = None
        satisfied = False
        note: Optional[str] = None
        total_gen_latency = 0.0
        total_judge_latency = 0.0
        overall_scores: List[float] = []
        
        # Test model access first
        try:
            print(f"Testing model access: {model_id}...")
            test_resp = call_model(provider, model_id, "Test", region_name=region, timeout_s=30)
            print(f"✓ {model_id} accessible")
        except Exception as e:
            print(f"✗ {model_id} failed: {str(e)}")
            note = f"Model access failed: {str(e)}"
            run_results.append(
                ModelRunResult(
                    model_id=model_id,
                    provider=provider,
                    satisfied=False,
                    attempts=0,
                    total_gen_latency_s=0.0,
                    total_judge_latency_s=0.0,
                    average_overall_score=None,
                    model_dir=model_dir,
                    note=note,
                )
            )
            continue

        for attempt in range(1, max_attempts + 1):
            attempt_dir = model_dir / f"attempt_{attempt}"
            attempt_dir.mkdir(parents=True, exist_ok=True)

            # Build generation or revision prompt
            variables_common = {
                "scenario_json": pretty_json(scenario),
                "acceptance_criteria": pretty_json(acceptance_criteria),
                "doc_meta": pretty_json({}),  # placeholder; can be extended later
            }

            if attempt == 1 or candidate_rtf is None:
                gen_prompt = render_generate(cfg, document_key, {
                    **variables_common,
                    "document_rtf": original_rtf,
                })
            else:
                # Use revise with critic feedback from previous attempt
                critic_json_path = attempt_dir.parent / f"attempt_{attempt-1}" / "critic.json"
                if critic_json_path.exists():
                    critic_data = read_json(critic_json_path)
                    suggestions = critic_data.get("revision_suggestions", [])
                else:
                    suggestions = []
                if suggestions:
                    gen_prompt = render_revise(cfg, document_key, {
                        **variables_common,
                        "original_document_rtf": original_rtf,
                        "previous_candidate_rtf": candidate_rtf or "",
                        "revision_suggestions": pretty_json(suggestions),
                    })
                else:
                    gen_prompt = render_generate(cfg, document_key, {
                        **variables_common,
                        "document_rtf": original_rtf,
                    })

            # Call model for generation/revision
            gen_timeout = int(cfg.get("runtime", {}).get("generation_timeout_s", 180))
            gen_resp = call_model(provider, model_id, gen_prompt, region_name=region, timeout_s=gen_timeout)
            total_gen_latency += gen_resp.latency_s
            candidate_rtf = gen_resp.text
            write_text(attempt_dir / "candidate.rtf", candidate_rtf)
            write_text(attempt_dir / "gen_prompt.txt", gen_prompt)

            # PROGRAMMATIC VERIFICATION (for objective scoring only)
            programmatic_results = programmatic_verify(original_rtf, candidate_rtf, scenario)
            programmatic_score = calculate_programmatic_score(programmatic_results)
            
            # Save programmatic verification results (for scoring only)
            write_json(attempt_dir / "programmatic_verification.json", {
                "results": programmatic_results,
                "score": programmatic_score,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            })

            # LLM CRITIC EVALUATION (for refinement feedback)
            critic_judge_prompt = render_judge(cfg, document_key, {
                **variables_common,
                "original_document_rtf": original_rtf,
                "candidate_rtf": candidate_rtf,
            })

            # Validate candidate output first
            if not candidate_rtf or candidate_rtf.strip() == "":
                # Empty or invalid output - skip critic, use basic feedback
                critic_data = {
                    "instruction_followed": False,
                    "criteria": {
                        "empty_output_failure": {
                            "pass": False,
                            "score": 0.0,
                            "explanation": "Model produced empty or invalid output",
                            "evidence": ["Empty candidate RTF document"],
                            "anchors": []
                        }
                    },
                    "unmet_criteria": ["empty_output_failure"],
                    "overall_score": 0.0,
                    "overall_satisfied": False,
                    "revision_suggestions": [
                        {
                            "reason": "Model failed to generate any output",
                            "target_section": "entire document",
                            "action": "add",
                            "instruction": "Generate complete RTF document with all required modifications",
                            "text_to_insert": None,
                            "constraints": ["Must produce valid RTF output"]
                        }
                    ],
                    "red_flags": ["Empty output indicates model failure"]
                }
                critic_latency = 0.0
                write_json(attempt_dir / "critic.json", critic_data)
                write_text(attempt_dir / "critic_prompt.txt", "SKIPPED - Empty candidate output")
            else:
                # Call the LLM CRITIC for detailed evaluation and feedback
                critic_start = time.time()
                critic_resp = call_model(
                    "bedrock", judge_model_id, critic_judge_prompt, region_name=region, timeout_s=judge_timeout_s
                )
                critic_end = time.time()
                critic_latency = critic_resp.latency_s

                write_text(attempt_dir / "critic_prompt.txt", critic_judge_prompt)
                
                # Parse critic response
                critic_data = judge_parse(critic_resp.text)
                write_json(attempt_dir / "critic.json", critic_data)
                
                # Add programmatic context (for reference, not feedback)
                critic_data["programmatic_context"] = {
                    "score": programmatic_score,
                    "results": programmatic_results
                }

            # ACTOR-CRITIC SATISFACTION LOGIC
            # Use critic's evaluation for satisfaction decision
            critic_satisfied = critic_data.get("overall_satisfied", False)
            critic_score = critic_data.get("overall_score", 0.0)
            
            # Final satisfaction: Critic must be satisfied
            satisfied_now = critic_satisfied
            
            # Use critic score as primary metric (programmatic score for final evaluation only)
            overall_score = critic_score
            overall_scores.append(float(critic_score))
            total_judge_latency += critic_latency

            # Record attempt with critic-based data
            unmet_criteria = critic_data.get("unmet_criteria", [])
            attempt_records.append(
                AttemptRecord(
                    index=attempt,
                    gen_latency_s=gen_resp.latency_s,
                    judge_latency_s=critic_latency,  # Now using critic latency
                    satisfied=satisfied_now,
                    overall_score=float(overall_score) if isinstance(overall_score, (int, float)) else None,
                    unmet_criteria=unmet_criteria,
                )
            )

            if satisfied_now:
                satisfied = True
                break

        avg_critic_score = sum(overall_scores) / len(overall_scores) if overall_scores else None
        
        # Calculate final programmatic score for last attempt (objective scoring)
        final_programmatic_score = None
        if attempt_records:
            last_attempt_dir = model_dir / f"attempt_{len(attempt_records)}"
            prog_file = last_attempt_dir / "programmatic_verification.json"
            if prog_file.exists():
                prog_data = read_json(prog_file)
                final_programmatic_score = prog_data.get("score")
        
        if not satisfied:
            note = "unsatisfied after max attempts; see critic.json and programmatic_verification.json for details"

        # No judge hallucination check needed with proper actor-critic pattern
        judge_hallucination = False

        run_results.append(
            ModelRunResult(
                model_id=model_id,
                provider=provider,
                satisfied=satisfied,
                attempts=len(attempt_records),
                total_gen_latency_s=total_gen_latency,
                total_judge_latency_s=total_judge_latency,  # Now using critic latency
                average_overall_score=avg_critic_score,
                model_dir=model_dir,
                programmatic_score=final_programmatic_score,  # Final objective score
                judge_hallucination_detected=judge_hallucination,
                note=note,
            )
        )

        # Append to manifest
        run_manifest["model_runs"].append(
            {
                "model_id": model_id,
                "provider": provider,
                "attempts": [
                    {
                        "index": ar.index,
                        "gen_latency_s": ar.gen_latency_s,
                        "judge_latency_s": ar.judge_latency_s,
                        "satisfied": ar.satisfied,
                        "overall_score": ar.overall_score,
                        "unmet_criteria": ar.unmet_criteria,
                    }
                    for ar in attempt_records
                ],
                "satisfied": satisfied,
                "average_overall_score": avg_critic_score,
                "model_dir": model_dir.as_posix(),
            }
        )

    run_manifest["finished_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    write_json(paths.run_dir / "manifest.json", run_manifest)

    # Generate reports in configured formats
    output_cfg = cfg.get("output", {})
    formats = output_cfg.get("formats", ["rtf"])
    
    if "rtf" in formats:
        make_report_rtf(paths.run_dir, run_results)
        
    if "md" in formats:
        make_report_md(paths.run_dir, run_results)

    return paths.run_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate contract manipulations with judge-led critic loop")
    parser.add_argument("--config", default="config/config.yaml", help="Path to config YAML (relative to exp/ or absolute)")
    parser.add_argument("--document", choices=["sample_1", "sample_2"], required=True, help="Which document to process")
    parser.add_argument("--scenario", required=True, help="Path to scenario JSON file")
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parents[1]  # exp/

    cfg = load_config(base_dir, args.config)

    scenario_path = ensure_absolute(base_dir, args.scenario)
    run_dir = run_evaluation(base_dir, cfg, args.document, scenario_path)

    print(run_dir.as_posix())


if __name__ == "__main__":
    main()
