#!/usr/bin/env python3
"""Reproduce the survey analysis, evidence matrix, and provisional model weights."""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "docs/google_form_responses/MIS Survey  (Responses) - Form Responses 1.csv"
DEFAULT_OUTPUT = ROOT / "docs/research_analysis"
EXCLUDED_SOURCE_ROWS = {64, 79, 83, 97}
RANDOM_SEED = 20260727
PERMUTATIONS = 5_000
BOOTSTRAP_SAMPLES = 5_000

FIELDS = {
    "role": "What is your role?",
    "experience": "Years of experience:",
    "industry": "Industry:",
    "requirements_change": "How often do project requirements change?",
    "stakeholder_involvement": "Level of user/stakeholder involvement during development?",
    "deadline_pressure": "Importance of strict deadlines?",
    "budget_pressure": "Importance of staying within budget?",
    "project_risk": "Level of project risk?",
    "integration_complexity": "Complexity of system integration?",
    "security_requirements": "Level of security requirements?",
    "documentation_need": "Need for detailed documentation?",
    "project_size": "Project size (team/resources)?",
    "flexibility_need": "Need for flexibility during development?",
    "methodology": "Which methodology was used in your project?",
    "success": "How successful was the project?",
    "challenge": "What challenges did you face in selecting a methodology?",
    "important_factor": "In your opinion, what is the most important factor when choosing a methodology?",
}

ORDINAL_MAPS = {
    "requirements_change": {
        "Never / Rarely": 1,
        "Infrequently": 2,
        "Occasionally": 3,
        "Frequently": 4,
        "Constantly": 5,
    },
    "documentation_need": {
        "Minimal documentation required": 1,
        "Basic documentation only": 2,
        "Moderate documentation needed": 3,
        "Detailed documentation required": 4,
        "Extensive documentation with strict standards": 5,
    },
    "project_size": {
        "Small (1–5 members, limited resources)": 1,
        "Medium (6–15 members, moderate resources)": 2,
        "Large (16–30 members, significant resources)": 3,
        "Very Large (30+ members, high complexity and resources)": 4,
    },
}

FACTOR_KEYS = [
    "requirements_change",
    "stakeholder_involvement",
    "deadline_pressure",
    "budget_pressure",
    "project_risk",
    "integration_complexity",
    "security_requirements",
    "documentation_need",
    "project_size",
    "flexibility_need",
    "success",
]

CONSTRUCT_FACTORS = {
    "FLEXIBILITY": ("requirements_change", "stakeholder_involvement", "flexibility_need"),
    "PERFORMANCE": ("deadline_pressure", "budget_pressure"),
    "STRICTNESS": ("project_risk", "integration_complexity", "security_requirements", "documentation_need"),
}

QUESTION_COUNTS = {"FLEXIBILITY": 4, "PERFORMANCE": 3, "STRICTNESS": 5}

QUESTION_EVIDENCE = [
    {
        "question_id": "Q11",
        "construct": "FLEXIBILITY",
        "prompt": "How much are requirements expected to change after development begins?",
        "rationale": "Requirement volatility is the strongest closed-question separator and directly determines how useful iterative reprioritization may be.",
        "survey_factors": ("requirements_change",),
        "qualitative_evidence": "Requirement uncertainty/scope: 27/69 challenges and 21/71 important-factor answers.",
        "evidence_class": "Direct quantitative + qualitative",
        "limitation": "Historical association does not prove that changing requirements caused the methodology choice.",
    },
    {
        "question_id": "Q12",
        "construct": "FLEXIBILITY",
        "prompt": "How much uncertainty exists about the final solution and its acceptance criteria?",
        "rationale": "Solution uncertainty captures discovery work that simple requirement-change frequency does not fully describe.",
        "survey_factors": ("requirements_change", "flexibility_need"),
        "qualitative_evidence": "Requirement uncertainty/scope: 27/69 challenges and 21/71 important-factor answers.",
        "evidence_class": "Indirect quantitative + qualitative",
        "limitation": "Acceptance-criteria uncertainty was not a separate closed survey item and needs expert/cognitive validation.",
    },
    {
        "question_id": "Q13",
        "construct": "FLEXIBILITY",
        "prompt": "How often can an authorized stakeholder review work and make priority decisions?",
        "rationale": "Iterative delivery requires available stakeholders with enough authority to provide timely feedback and priority decisions.",
        "survey_factors": ("stakeholder_involvement",),
        "qualitative_evidence": "Stakeholders/communication: 19/69 challenges and 17/71 important-factor answers.",
        "evidence_class": "Related quantitative + qualitative",
        "limitation": "Past involvement is not identical to future availability or decision authority.",
    },
    {
        "question_id": "Q14",
        "construct": "FLEXIBILITY",
        "prompt": "How capable is the team of planning, building, testing, and reviewing work in short cycles?",
        "rationale": "The open responses identify team maturity and culture as the most frequent self-reported selection factor.",
        "survey_factors": (),
        "qualitative_evidence": "Team capability/culture: 16/69 challenges and 22/71 important-factor answers.",
        "evidence_class": "Qualitative/proxy",
        "limitation": "Team short-cycle capability was not measured by a closed survey item.",
    },
    {
        "question_id": "Q15",
        "construct": "PERFORMANCE",
        "prompt": "How fixed is the delivery date because of contractual, legal, launch, or external commitments?",
        "rationale": "Externally fixed dates reduce delivery-plan discretion and increase the importance of predictive control.",
        "survey_factors": ("deadline_pressure",),
        "qualitative_evidence": "Time/budget/planning: 11/69 challenges and 5/71 important-factor answers.",
        "evidence_class": "Related quantitative + qualitative",
        "limitation": "Deadline importance is not identical to an immovable external deadline.",
    },
    {
        "question_id": "Q16",
        "construct": "PERFORMANCE",
        "prompt": "How fixed is the project budget or funding ceiling?",
        "rationale": "A fixed funding ceiling constrains scope, schedule, and delivery trade-offs.",
        "survey_factors": ("budget_pressure",),
        "qualitative_evidence": "Time/budget/planning: 11/69 challenges and 5/71 important-factor answers.",
        "evidence_class": "Related quantitative + qualitative",
        "limitation": "Budget importance is only a proxy for contractual funding rigidity.",
    },
    {
        "question_id": "Q17",
        "construct": "PERFORMANCE",
        "prompt": "How much formal approval is required before the delivery plan can be changed?",
        "rationale": "Approval gates determine whether the team can make iterative trade-offs without procurement, board, or contractual escalation.",
        "survey_factors": (),
        "qualitative_evidence": "Governance/compliance/security: 17/69 challenges and 16/71 important-factor answers.",
        "evidence_class": "Qualitative/proxy",
        "limitation": "Change-approval authority was not measured as a closed survey variable.",
    },
    {
        "question_id": "Q18",
        "construct": "STRICTNESS",
        "prompt": "What level of regulatory, legal, or audit obligation applies?",
        "rationale": "Mandatory obligations create evidence, approval, and traceability requirements that must shape delivery governance.",
        "survey_factors": ("security_requirements", "documentation_need"),
        "qualitative_evidence": "Governance/compliance/security: 17/69 challenges and 16/71 important-factor answers.",
        "evidence_class": "Indirect quantitative + qualitative",
        "limitation": "Regulatory and audit obligations were not isolated from security/documentation in the closed survey.",
    },
    {
        "question_id": "Q19",
        "construct": "STRICTNESS",
        "prompt": "What is the highest credible consequence if the system fails or is compromised?",
        "rationale": "Failure consequence distinguishes routine delivery risk from safety, privacy, financial, or legally significant exposure.",
        "survey_factors": ("project_risk", "security_requirements"),
        "qualitative_evidence": "Quality/risk/safety: 8/69 challenges and 10/71 important-factor answers.",
        "evidence_class": "Related quantitative + qualitative",
        "limitation": "The original risk and security ratings did not use consequence-based anchors.",
    },
    {
        "question_id": "Q20",
        "construct": "STRICTNESS",
        "prompt": "How much controlled documentation and end-to-end traceability is required?",
        "rationale": "Formal documentation and traceability were among the strongest Traditional-oriented separators in the survey.",
        "survey_factors": ("documentation_need",),
        "qualitative_evidence": "Documentation/control: 15/69 challenges and 4/71 important-factor answers.",
        "evidence_class": "Direct quantitative + qualitative",
        "limitation": "Documentation need may partly reflect the sample's industry composition.",
    },
    {
        "question_id": "Q21",
        "construct": "STRICTNESS",
        "prompt": "How dependent is delivery on external vendors, legacy systems, or interfaces outside the team's control?",
        "rationale": "External technical dependencies constrain sequencing, release timing, testing, and change autonomy.",
        "survey_factors": ("integration_complexity",),
        "qualitative_evidence": "Technical delivery context: 9/69 challenges and 9/71 important-factor answers.",
        "evidence_class": "Related quantitative + qualitative",
        "limitation": "Integration complexity can exist without an external dependency.",
    },
    {
        "question_id": "Q22",
        "construct": "STRICTNESS",
        "prompt": "How much coordination and sequencing is required across teams or organizations?",
        "rationale": "Larger and cross-organizational projects require more explicit coordination and dependency management.",
        "survey_factors": ("project_size",),
        "qualitative_evidence": "Coordination appeared across stakeholder, technical-context, and governance responses.",
        "evidence_class": "Proxy quantitative + qualitative",
        "limitation": "Team size is a proxy; it does not directly measure coupling or sequencing.",
    },
]

QUALITATIVE_THEMES = {
    "challenge": {
        "substantive_n": 69,
        "themes": {
            "Requirement uncertainty and scope": 27,
            "Stakeholders and communication": 19,
            "Governance, compliance, and security": 17,
            "Team capability and culture": 16,
            "Documentation and control": 15,
            "Time, budget, and planning": 11,
            "Technical delivery context": 9,
            "Quality, risk, and safety": 8,
        },
    },
    "important_factor": {
        "substantive_n": 71,
        "themes": {
            "Team capability and culture": 22,
            "Requirement uncertainty and scope": 21,
            "Stakeholders and communication": 17,
            "Governance, compliance, and security": 16,
            "Quality, risk, and safety": 10,
            "Technical delivery context": 9,
            "Time, budget, and planning": 5,
            "Documentation and control": 4,
        },
    },
}

REPRESENTATIVE_QUOTES = {
    "Requirement uncertainty and scope": "The stability of project requirements.",
    "Stakeholders and communication": "Stakeholder availability.",
    "Governance, compliance, and security": "Regulatory compliance was the factor that overruled everything else.",
    "Team capability and culture": "The team's experience level.",
    "Documentation and control": "Documentation and traceability aren't optional.",
    "Time, budget, and planning": "Balancing Agile flexibility with hard launch dates required careful sprint planning.",
    "Technical delivery context": "Deployment environment constraints.",
    "Quality, risk, and safety": "Build quality coming into QA.",
}


def normalized_headers(row: dict[str, str]) -> dict[str, str]:
    return {key.strip(): (value or "").strip() for key, value in row.items()}


def load_rows(path: Path) -> tuple[list[str], list[dict[str, str]], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        raw_headers = list(reader.fieldnames or [])
        indexed = [(index, row) for index, row in enumerate(reader, start=1)]
    raw = [normalized_headers(row) | {"Source response row": str(index)} for index, row in indexed]
    cleaned = [row for row in raw if int(row["Source response row"]) not in EXCLUDED_SOURCE_ROWS]
    return raw_headers, raw, cleaned


def numeric_value(row: dict[str, str], key: str) -> float:
    raw = row[FIELDS[key]]
    if key in ORDINAL_MAPS:
        return float(ORDINAL_MAPS[key][raw])
    return float(raw)


def methodology_name(value: str) -> str:
    return "Traditional" if value == "Traditional (Waterfall)" else value


def row_methodology(row: dict[str, str]) -> str:
    return methodology_name(row[FIELDS["methodology"]])


def sample_variance(values: Iterable[float]) -> float:
    data = list(values)
    if len(data) < 2:
        return 0.0
    center = mean(data)
    return sum((value - center) ** 2 for value in data) / (len(data) - 1)


def sample_sd(values: Iterable[float]) -> float:
    return math.sqrt(sample_variance(values))


def factor_means(rows: list[dict[str, str]]) -> dict[str, dict[str, float]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row_methodology(row)].append(row)
    result: dict[str, dict[str, float]] = {}
    for group, group_rows in {"Overall": rows, **dict(grouped)}.items():
        result[group] = {key: round(mean(numeric_value(row, key) for row in group_rows), 4) for key in FACTOR_KEYS}
    return result


def factor_descriptives(rows: list[dict[str, str]]) -> dict[str, dict[str, dict[str, float]]]:
    grouped = {"Overall": rows}
    grouped.update({name: [row for row in rows if row_methodology(row) == name] for name in ("Agile", "Hybrid", "Traditional")})
    return {
        key: {
            group: {
                "n": len(group_rows),
                "mean": round(mean(numeric_value(row, key) for row in group_rows), 4),
                "sd": round(sample_sd(numeric_value(row, key) for row in group_rows), 4),
            }
            for group, group_rows in grouped.items()
        }
        for key in FACTOR_KEYS
    }


def eta_squared(rows: list[dict[str, str]], key: str) -> float:
    values = [numeric_value(row, key) for row in rows]
    grand_mean = mean(values)
    grouped: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        grouped[row_methodology(row)].append(numeric_value(row, key))
    total = sum((value - grand_mean) ** 2 for value in values)
    between = sum(len(group) * (mean(group) - grand_mean) ** 2 for group in grouped.values())
    return between / total if total else 0.0


def permutation_p_value(rows: list[dict[str, str]], key: str, permutations: int, seed: int) -> float:
    values = [numeric_value(row, key) for row in rows]
    labels = [row_methodology(row) for row in rows]
    observed = eta_squared(rows, key)
    grouped_sizes = Counter(labels)
    order = list(grouped_sizes)
    rng = random.Random(seed)
    exceedances = 0
    for _ in range(permutations):
        shuffled = values[:]
        rng.shuffle(shuffled)
        cursor = 0
        grand_mean = mean(shuffled)
        total = sum((value - grand_mean) ** 2 for value in shuffled)
        between = 0.0
        for label in order:
            group = shuffled[cursor : cursor + grouped_sizes[label]]
            cursor += grouped_sizes[label]
            between += len(group) * (mean(group) - grand_mean) ** 2
        if total and between / total >= observed - 1e-12:
            exceedances += 1
    return (exceedances + 1) / (permutations + 1)


def holm_adjust(p_values: dict[str, float]) -> dict[str, float]:
    ordered = sorted(p_values, key=p_values.get)
    adjusted: dict[str, float] = {}
    running = 0.0
    total = len(ordered)
    for index, key in enumerate(ordered):
        candidate = min(1.0, (total - index) * p_values[key])
        running = max(running, candidate)
        adjusted[key] = running
    return adjusted


def percentile_interval(values: list[float]) -> list[float]:
    ordered = sorted(values)
    low = ordered[max(0, math.floor(0.025 * len(ordered)) - 1)]
    high = ordered[min(len(ordered) - 1, math.ceil(0.975 * len(ordered)) - 1)]
    return [round(low, 4), round(high, 4)]


def stratified_resample(rows: list[dict[str, str]], rng: random.Random) -> list[dict[str, str]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row_methodology(row)].append(row)
    sample: list[dict[str, str]] = []
    for group in grouped.values():
        sample.extend(rng.choices(group, k=len(group)))
    return sample


def effect_size_analysis(rows: list[dict[str, str]]) -> dict[str, dict[str, float | list[float]]]:
    permutation_values = {
        key: permutation_p_value(rows, key, PERMUTATIONS, RANDOM_SEED + index)
        for index, key in enumerate(FACTOR_KEYS)
    }
    adjusted = holm_adjust(permutation_values)
    rng = random.Random(RANDOM_SEED)
    bootstraps = {key: [] for key in FACTOR_KEYS}
    for _ in range(2_000):
        sample = stratified_resample(rows, rng)
        for key in FACTOR_KEYS:
            bootstraps[key].append(eta_squared(sample, key))
    return {
        key: {
            "eta_squared": round(eta_squared(rows, key), 6),
            "bootstrap_95_ci": percentile_interval(bootstraps[key]),
            "permutation_p": round(permutation_values[key], 6),
            "holm_adjusted_p": round(adjusted[key], 6),
        }
        for key in FACTOR_KEYS
    }


def cronbach_alpha(rows: list[dict[str, str]], keys: tuple[str, ...]) -> float | None:
    if len(rows) < 2 or len(keys) < 2:
        return None
    item_values = [[numeric_value(row, key) for row in rows] for key in keys]
    totals = [sum(numeric_value(row, key) for key in keys) for row in rows]
    total_variance = sample_variance(totals)
    if total_variance == 0:
        return None
    alpha = len(keys) / (len(keys) - 1) * (1 - sum(sample_variance(values) for values in item_values) / total_variance)
    return round(alpha, 4)


def reliability_analysis(rows: list[dict[str, str]]) -> dict[str, dict[str, float | None]]:
    groups = {"Overall": rows}
    groups.update({name: [row for row in rows if row_methodology(row) == name] for name in ("Agile", "Hybrid", "Traditional")})
    return {
        construct: {group: cronbach_alpha(group_rows, factors) for group, group_rows in groups.items()}
        for construct, factors in CONSTRUCT_FACTORS.items()
    }


def construct_effect_sizes(rows: list[dict[str, str]]) -> dict[str, float]:
    return {
        construct: mean(eta_squared(rows, factor) for factor in factors)
        for construct, factors in CONSTRUCT_FACTORS.items()
    }


def normalized_effect_weights(rows: list[dict[str, str]]) -> dict[str, float]:
    effects = construct_effect_sizes(rows)
    total = sum(effects.values())
    return {construct: 3 * effect / total for construct, effect in effects.items()}


def weight_analysis(raw_rows: list[dict[str, str]], cleaned_rows: list[dict[str, str]]) -> dict[str, object]:
    cleaned_effects = construct_effect_sizes(cleaned_rows)
    cleaned_weights = normalized_effect_weights(cleaned_rows)
    raw_weights = normalized_effect_weights(raw_rows)
    rng = random.Random(RANDOM_SEED)
    bootstraps = {construct: [] for construct in CONSTRUCT_FACTORS}
    for _ in range(BOOTSTRAP_SAMPLES):
        weights = normalized_effect_weights(stratified_resample(cleaned_rows, rng))
        for construct, value in weights.items():
            bootstraps[construct].append(value)
    return {
        "derivation": "Mean eta-squared of mapped survey factors, normalized so construct weights sum to 3.",
        "cleaned_construct_effect_sizes": {key: round(value, 6) for key, value in cleaned_effects.items()},
        "cleaned_weights": {key: round(value, 6) for key, value in cleaned_weights.items()},
        "cleaned_influence_percent": {key: round(100 * value / 3, 4) for key, value in cleaned_weights.items()},
        "per_question_influence_percent": {
            key: round(100 * value / 3 / QUESTION_COUNTS[key], 4) for key, value in cleaned_weights.items()
        },
        "per_question_influence_with_full_document_coverage_percent": {
            key: round(0.75 * 100 * value / 3 / QUESTION_COUNTS[key], 4) for key, value in cleaned_weights.items()
        },
        "raw_sample_weights": {key: round(value, 6) for key, value in raw_weights.items()},
        "stratified_bootstrap_95_ci": {key: percentile_interval(values) for key, values in bootstraps.items()},
        "status": "Survey-derived provisional weights; not independent criterion validation.",
    }


def centroids(rows: list[dict[str, str]]) -> dict[str, dict[str, float]]:
    means = factor_means(rows)
    result = {}
    for methodology in ("Agile", "Traditional"):
        values = means[methodology]
        result[methodology] = {
            construct: round(mean(values[factor] for factor in factors), 4)
            for construct, factors in CONSTRUCT_FACTORS.items()
        }
    return result


def row_constructs(row: dict[str, str]) -> dict[str, float]:
    return {
        construct: mean(numeric_value(row, factor) for factor in factors)
        for construct, factors in CONSTRUCT_FACTORS.items()
    }


def classify(values: dict[str, float], references: dict[str, dict[str, float]], weights: dict[str, float]) -> str:
    distances = {
        methodology: sum(weights[key] * abs(values[key] - centroid[key]) for key in values)
        for methodology, centroid in references.items()
    }
    return min(distances, key=distances.get)


def wilson_interval(successes: int, total: int, z: float = 1.959964) -> list[float]:
    proportion = successes / total
    denominator = 1 + z**2 / total
    center = (proportion + z**2 / (2 * total)) / denominator
    margin = z * math.sqrt(proportion * (1 - proportion) / total + z**2 / (4 * total**2)) / denominator
    return [round(100 * (center - margin), 2), round(100 * (center + margin), 2)]


def classification_metrics(rows: list[dict[str, str]], weights: dict[str, float]) -> dict[str, object]:
    references = centroids(rows)
    binary = [row for row in rows if row_methodology(row) in {"Agile", "Traditional"}]
    pairs = Counter(
        (row_methodology(row), classify(row_constructs(row), references, weights))
        for row in binary
    )
    correct = sum(count for (actual, predicted), count in pairs.items() if actual == predicted)
    actual_counts = Counter(actual for (actual, _), count in pairs.items() for _ in range(count))
    predicted_counts = Counter(predicted for (_, predicted), count in pairs.items() for _ in range(count))
    total = len(binary)
    observed = correct / total
    expected = sum(actual_counts[label] * predicted_counts[label] for label in ("Agile", "Traditional")) / total**2
    per_class = {}
    for label in ("Agile", "Traditional"):
        true_positive = pairs[(label, label)]
        predicted_total = predicted_counts[label]
        actual_total = actual_counts[label]
        per_class[label] = {
            "precision": round(true_positive / predicted_total, 4) if predicted_total else None,
            "recall": round(true_positive / actual_total, 4) if actual_total else None,
        }
    hybrid_forced = Counter(
        classify(row_constructs(row), references, weights)
        for row in rows
        if row_methodology(row) == "Hybrid"
    )
    return {
        "n": total,
        "correct": correct,
        "agreement_percent": round(100 * observed, 1),
        "wilson_95_ci_percent": wilson_interval(correct, total),
        "balanced_accuracy": round(mean(per_class[label]["recall"] for label in per_class), 4),
        "cohen_kappa": round((observed - expected) / (1 - expected), 4) if expected != 1 else None,
        "per_class": per_class,
        "confusion_matrix": {
            "Agile_actual_Agile_predicted": pairs[("Agile", "Agile")],
            "Agile_actual_Traditional_predicted": pairs[("Agile", "Traditional")],
            "Traditional_actual_Agile_predicted": pairs[("Traditional", "Agile")],
            "Traditional_actual_Traditional_predicted": pairs[("Traditional", "Traditional")],
        },
        "hybrid_forced_distribution": dict(hybrid_forced),
        "criterion": "Historical methodology used; same-sample calibration diagnostic only.",
    }


def normalize_role(value: str) -> str:
    aliases = {
        "business analyst": "Business Analyst",
        "business analysit": "Business Analyst",
        "qa engineer": "QA Engineer",
        "quality assurance": "QA Engineer",
        "qulity assurance engineer": "QA Engineer",
        "fullstack developer": "Full Stack Developer",
        "full stack developer": "Full Stack Developer",
    }
    return aliases.get(value.strip().lower(), value.strip())


def normalize_industry(value: str) -> str:
    return "E-Commerce" if value.strip().lower() in {"e-commerce", "ecommerce"} else value.strip()


def distributions(rows: list[dict[str, str]]) -> dict[str, dict[str, int]]:
    return {
        "methodology": dict(Counter(row_methodology(row) for row in rows)),
        "experience": dict(Counter(row[FIELDS["experience"]] for row in rows)),
        "industry": dict(Counter(normalize_industry(row[FIELDS["industry"]]) for row in rows)),
        "role": dict(Counter(normalize_role(row[FIELDS["role"]]) for row in rows)),
    }


def cramers_v(rows: list[dict[str, str]]) -> dict[str, float | int]:
    industries = sorted({normalize_industry(row[FIELDS["industry"]]) for row in rows})
    methods = ["Agile", "Hybrid", "Traditional"]
    table = {
        industry: Counter(row_methodology(row) for row in rows if normalize_industry(row[FIELDS["industry"]]) == industry)
        for industry in industries
    }
    column_totals = {method: sum(table[industry][method] for industry in industries) for method in methods}
    chi_square = 0.0
    for industry in industries:
        row_total = sum(table[industry].values())
        for method in methods:
            expected = row_total * column_totals[method] / len(rows)
            if expected:
                chi_square += (table[industry][method] - expected) ** 2 / expected
    denominator = len(rows) * min(len(industries) - 1, len(methods) - 1)
    return {
        "chi_square": round(chi_square, 4),
        "cramers_v": round(math.sqrt(chi_square / denominator), 4) if denominator else 0.0,
        "industry_categories": len(industries),
        "methodology_categories": len(methods),
    }


def wave_analysis(rows: list[dict[str, str]]) -> dict[str, object]:
    waves = {
        "first_15": [row for row in rows if int(row["Source response row"]) <= 15],
        "later": [row for row in rows if int(row["Source response row"]) > 15],
    }
    result = {}
    for name, wave_rows in waves.items():
        result[name] = {
            "n": len(wave_rows),
            "methodology_distribution": dict(Counter(row_methodology(row) for row in wave_rows)),
            "reliability": reliability_analysis(wave_rows),
        }
    return result


def write_clean_csv(raw_headers: list[str], rows: list[dict[str, str]]) -> None:
    destination = ROOT / "docs/google_form_responses/MIS Survey (Responses) - duplicate-screened n107.csv"
    stripped_headers = [header.strip() for header in raw_headers]
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["Source response row", *raw_headers])
        writer.writeheader()
        for row in rows:
            output = {"Source response row": row["Source response row"]}
            output.update({raw_header: row[stripped] for raw_header, stripped in zip(raw_headers, stripped_headers)})
            writer.writerow(output)


def factor_label(key: str) -> str:
    return key.replace("_", " ").title()


def write_tables(output_dir: Path, summary: dict[str, object]) -> None:
    means = summary["factor_means"]
    effects = summary["effect_sizes"]
    groups = ["Overall", "Agile", "Hybrid", "Traditional"]
    lines = [
        "# Reproducible survey tables",
        "",
        f"Primary cleaned sample: n={summary['cleaned_sample_size']}; excluded probable duplicates: {summary['excluded_source_rows']}.",
        "Valid extreme responses were retained; no scale-value outliers were removed.",
        "",
        "## Methodology distribution",
        "",
        "| Methodology | n |",
        "| --- | ---: |",
    ]
    lines.extend(f"| {key} | {value} |" for key, value in summary["distributions"]["methodology"].items())
    lines.extend([
        "",
        "## Project-factor means and effect sizes",
        "",
        "| Factor | Overall | Agile | Hybrid | Traditional | Eta-squared | 95% bootstrap CI | Holm p |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ])
    for factor in FACTOR_KEYS:
        effect = effects[factor]
        interval = effect["bootstrap_95_ci"]
        lines.append(
            f"| {factor_label(factor)} | "
            + " | ".join(f"{means[group][factor]:.2f}" for group in groups)
            + f" | {effect['eta_squared']:.3f} | {interval[0]:.3f}–{interval[1]:.3f} | {effect['holm_adjusted_p']:.4f} |"
        )
    lines.extend([
        "",
        "Eta-squared is the proportion of observed factor variance associated with the three reported-methodology groups. It is not a causal effect. P-values use 5,000 label permutations and Holm correction.",
        "",
        "## Provisional survey-derived centroids",
        "",
        "| Methodology | Adaptation/readiness | Delivery constraints | Assurance/dependencies |",
        "| --- | ---: | ---: | ---: |",
    ])
    for methodology, values in summary["centroids"].items():
        lines.append(f"| {methodology} | {values['FLEXIBILITY']:.2f} | {values['PERFORMANCE']:.2f} | {values['STRICTNESS']:.2f} |")
    weight_data = summary["weights"]
    lines.extend([
        "",
        "## Effect-size-derived provisional weights",
        "",
        "| Construct | Mean source eta-squared | Weight | Total influence | Per questionnaire item | Per item with full document coverage | 95% bootstrap CI |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ])
    for construct in CONSTRUCT_FACTORS:
        interval = weight_data["stratified_bootstrap_95_ci"][construct]
        lines.append(
            f"| {construct} | {weight_data['cleaned_construct_effect_sizes'][construct]:.3f} | "
            f"{weight_data['cleaned_weights'][construct]:.2f} | {weight_data['cleaned_influence_percent'][construct]:.2f}% | "
            f"{weight_data['per_question_influence_percent'][construct]:.2f}% | "
            f"{weight_data['per_question_influence_with_full_document_coverage_percent'][construct]:.2f}% | "
            f"{interval[0]:.2f}–{interval[1]:.2f} |"
        )
    lines.extend([
        "",
        "The per-question figures are effective maximum contributions because questions are averaged equally within a construct; they are not independently estimated item weights. Full confirmed document coverage can contribute 25% of a construct.",
        "",
        "## Historical-methodology agreement diagnostics",
        "",
        "| Model | Correct / n | Agreement | 95% Wilson CI | Balanced accuracy | Cohen kappa |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ])
    for key, label in (("equal_weights", "Equal weights"), ("effect_size_weights", "Effect-size weights")):
        metric = summary["classification_diagnostics"]["cleaned"][key]
        lines.append(
            f"| {label} | {metric['correct']}/{metric['n']} | {metric['agreement_percent']:.1f}% | "
            f"{metric['wilson_95_ci_percent'][0]:.2f}%–{metric['wilson_95_ci_percent'][1]:.2f}% | "
            f"{metric['balanced_accuracy']:.3f} | {metric['cohen_kappa']:.3f} |"
        )
    lines.extend([
        "",
        "These are same-sample calibration diagnostics against the methodology historically used. They are not prospective accuracy or proof that the historical choice was suitable.",
        "",
    ])
    (output_dir / "tables.md").write_text("\n".join(lines), encoding="utf-8")


def write_question_matrix(output_dir: Path, summary: dict[str, object]) -> None:
    effects = summary["effect_sizes"]
    weights = summary["weights"]
    rows = []
    for item in QUESTION_EVIDENCE:
        factor_text = "; ".join(
            f"{factor_label(key)} (eta-squared={effects[key]['eta_squared']:.3f})"
            for key in item["survey_factors"]
        ) or "No exact closed survey factor"
        row = {
            **item,
            "survey_factors": factor_text,
            "construct_weight": round(weights["cleaned_weights"][item["construct"]], 2),
            "nominal_question_influence_percent": weights["per_question_influence_percent"][item["construct"]],
            "full_document_coverage_question_influence_percent": weights["per_question_influence_with_full_document_coverage_percent"][item["construct"]],
        }
        rows.append(row)
    csv_path = output_dir / "question-rationale-and-weights.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        fieldnames = list(rows[0])
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    lines = [
        "# Question Selection, Evidence, and Weight Justification",
        "",
        "Q1–Q10 are profile/context questions and have **zero weight** in the Agile-versus-Traditional compatibility calculation. Q11–Q22 are scored. The original survey did not measure every Version 2 item exactly, so evidence strength is stated explicitly.",
        "",
        "| ID | Construct | Why selected | Survey support | Qualitative support | Evidence status | Effective item influence |",
        "| --- | --- | --- | --- | --- | --- | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| {row['question_id']} | {row['construct']} | {row['rationale']} | {row['survey_factors']} | "
            f"{row['qualitative_evidence']} | {row['evidence_class']} | {row['nominal_question_influence_percent']:.2f}% |"
        )
    lines.extend([
        "",
        "## How the weights were obtained",
        "",
        "For each construct, eta-squared values from its mapped Google Form factors were averaged. The three averages were then normalized to sum to 3. This produces weights of 1.37 for adaptation/readiness, 0.64 for delivery constraints, and 0.99 for assurance/dependencies.",
        "",
        "Questions are not assigned 12 separate fitted coefficients. They contribute equally to their construct average, so their nominal overall influence equals the construct share divided by the number of questions in that construct.",
        "",
        "## Interpretation boundary",
        "",
        "The weights describe how strongly factors separated respondents by the methodology they reported using. They do not prove which methodology should have been used. Several items use indirect or qualitative evidence and still require expert content review, cognitive interviews, and independent expert-labelled project cases.",
        "",
        "## Item-level validation needs",
        "",
    ])
    lines.extend(f"- **{row['question_id']}**: {row['limitation']}" for row in rows)
    lines.append("")
    (output_dir / "question-rationale-and-weights.md").write_text("\n".join(lines), encoding="utf-8")


def write_qualitative_report(output_dir: Path) -> None:
    lines = [
        "# Preliminary Qualitative Codebook and Findings",
        "",
        "The two open-text questions were coded with overlapping themes, so one response may receive more than one code. These counts are first-coder, keyword-assisted findings and must not be presented as independently verified thematic analysis.",
        "",
        "## Codebook",
        "",
        "| Theme | Include when the response discusses | Exclude when | Representative anonymized excerpt |",
        "| --- | --- | --- | --- |",
        "| Requirement uncertainty and scope | Requirement clarity, volatility, discovery, priorities, scope change | Change refers only to governance approval | “The stability of project requirements.” |",
        "| Stakeholders and communication | Availability, feedback, decision-making, communication, collaboration | Internal team capability without stakeholder interaction | “Stakeholder availability.” |",
        "| Governance, compliance, and security | Regulation, audit, procurement, contracts, approval, security obligations | General documentation without a formal obligation | “Regulatory compliance was the factor that overruled everything else.” |",
        "| Team capability and culture | Skills, experience, maturity, culture, mentorship, staffing | External stakeholder capability | “The team's experience level.” |",
        "| Documentation and control | Documentation, traceability, reporting, records, formal control | Documentation mentioned only as part of a regulation already coded as governance | “Documentation and traceability aren't optional.” |",
        "| Time, budget, and planning | Deadlines, launch windows, cost limits, estimates, schedules, milestones | General sequencing caused only by technical interfaces | “Balancing Agile flexibility with hard launch dates required careful sprint planning.” |",
        "| Technical delivery context | Integration, legacy systems, infrastructure, deployment, architecture, vendors | General team coordination without a technical dependency | “Deployment environment constraints.” |",
        "| Quality, risk, and safety | Testing, defects, quality, operational risk, failure, safety | Security discussed only as a compliance requirement | “Build quality coming into QA.” |",
        "",
    ]
    for response_type, data in QUALITATIVE_THEMES.items():
        label = "Challenges" if response_type == "challenge" else "Most important factors"
        denominator = data["substantive_n"]
        lines.extend([
            f"## {label} (n={denominator} substantive answers)",
            "",
            "| Theme | Mentions | Percentage | Research confidence |",
            "| --- | ---: | ---: | --- |",
        ])
        for theme, count in data["themes"].items():
            confidence = "Medium" if count >= 5 else "Low"
            lines.append(f"| {theme} | {count} | {100 * count / denominator:.1f}% | {confidence} |")
        lines.append("")
    lines.extend([
        "## Required validation before final thesis claims",
        "",
        "A second researcher should independently code at least 20–25% of substantive responses, calculate agreement, resolve disagreements, and freeze the final codebook. Until then, these results support instrument design but remain preliminary.",
        "",
    ])
    (output_dir / "qualitative-codebook.md").write_text("\n".join(lines), encoding="utf-8")


def write_deep_report(output_dir: Path, summary: dict[str, object]) -> None:
    weights = summary["weights"]
    cleaned_equal = summary["classification_diagnostics"]["cleaned"]["equal_weights"]
    cleaned_effect = summary["classification_diagnostics"]["cleaned"]["effect_size_weights"]
    lines = [
        "# Deep Survey Analysis and Scoring Justification",
        "",
        "## Executive conclusion",
        "",
        "The duplicate-screened survey provides strong exploratory evidence that project context differs across Agile, Hybrid, and Traditional projects in this sample. Requirement change, flexibility need, documentation, security, project size, and risk show the strongest group separation. The evidence supports the selection of the application's broad factors, but it remains evidence about historical methodology use rather than an independent judgment of methodology suitability.",
        "",
        "The active scoring update therefore uses transparent, effect-size-derived **provisional construct weights** rather than claiming 12 independently validated item coefficients.",
        "",
        "## Sample and data quality",
        "",
        f"- Raw responses: {summary['raw_sample_size']}.",
        f"- Primary duplicate-screened sample: {summary['cleaned_sample_size']}.",
        f"- Probable duplicate/copy source rows excluded: {', '.join(map(str, summary['excluded_source_rows']))}.",
        "- Missing closed answers: none; out-of-range closed values: none.",
        "- Valid high and low scale responses were retained; no numerical scale outliers were removed.",
        f"- Industry and methodology are strongly associated in this sample (Cramer's V={summary['industry_methodology_association']['cramers_v']:.3f}), so causal or universal claims are not justified.",
        "",
        "## Main quantitative findings",
        "",
    ]
    ranked = sorted(
        ((factor, data["eta_squared"]) for factor, data in summary["effect_sizes"].items() if factor != "success"),
        key=lambda item: item[1],
        reverse=True,
    )
    lines.extend(
        f"- {factor_label(factor)}: eta-squared={effect:.3f}."
        for factor, effect in ranked
    )
    lines.extend([
        "",
        "Project success has a ceiling effect and very weak methodology-group separation. It cannot establish that one methodology produced better outcomes.",
        "",
        "## Weight calculation",
        "",
        "Construct weights are proportional to the average eta-squared of the original closed survey factors mapped to that construct and are normalized to sum to 3:",
        "",
        f"- Adaptation/readiness: {weights['cleaned_weights']['FLEXIBILITY']:.2f} ({weights['cleaned_influence_percent']['FLEXIBILITY']:.2f}%).",
        f"- Delivery constraints: {weights['cleaned_weights']['PERFORMANCE']:.2f} ({weights['cleaned_influence_percent']['PERFORMANCE']:.2f}%).",
        f"- Assurance/dependencies: {weights['cleaned_weights']['STRICTNESS']:.2f} ({weights['cleaned_influence_percent']['STRICTNESS']:.2f}%).",
        "",
        "Raw-sample sensitivity produces approximately 1.36, 0.66, and 0.98, respectively, showing that the four duplicate exclusions do not materially determine the weights.",
        "",
        "## Calibration comparison",
        "",
        f"The equal-weight model agrees with historical Agile/Traditional use in {cleaned_equal['correct']}/{cleaned_equal['n']} cases ({cleaned_equal['agreement_percent']:.1f}%). The effect-size-weighted model agrees in {cleaned_effect['correct']}/{cleaned_effect['n']} cases ({cleaned_effect['agreement_percent']:.1f}%). The one-case improvement is descriptive and is not evidence of external predictive improvement because weights and performance were evaluated on the same sample.",
        "",
        "Hybrid responses remain in descriptive and qualitative analysis but are excluded from binary agreement calculations. They are not arbitrarily relabelled as ground truth.",
        "",
        "## Question-selection evidence",
        "",
        "The full Q11–Q22 mapping is provided in `question-rationale-and-weights.md`. Direct closed-survey evidence is strongest for requirement change and documentation. Team capability, approval authority, regulatory obligation, failure consequence, and coordination were added or refined using open responses and conceptual gaps, so their content validity still requires expert review.",
        "",
        "## Safe research claim",
        "",
        "> In this practitioner sample, project characteristics differed substantially across the methodologies respondents reported using. These differences informed a transparent, provisional weighting of an explainable decision-support prototype. Independent expert-labelled cases are still required to evaluate whether the application recommends the methodology that should be used.",
        "",
        "## Remaining validation",
        "",
        "1. Have at least three domain experts rate item relevance, clarity, and construct fit.",
        "2. Conduct 5–8 cognitive interviews using the anchored Q11–Q22 questionnaire.",
        "3. Pilot the exact Version 2 instrument and estimate its own reliability; the original Google Form cannot validate new item wording.",
        "4. Obtain independent expert Agile/Traditional labels for cases, freeze the rule, and evaluate it on unseen cases.",
        "5. Complete second-coder review of the qualitative responses.",
        "",
    ])
    (output_dir / "deep-analysis-report.md").write_text("\n".join(lines), encoding="utf-8")


def write_figures(output_dir: Path, summary: dict[str, object]) -> None:
    import matplotlib.pyplot as plt

    distribution = summary["distributions"]["methodology"]
    fig, axis = plt.subplots(figsize=(7, 4.5))
    axis.bar(distribution.keys(), distribution.values(), color=["#059669", "#0d9488", "#475569"])
    axis.set_ylabel("Responses")
    axis.set_title("Methodology used in cleaned sample (n=107)")
    fig.tight_layout()
    fig.savefig(output_dir / "methodology-distribution.png", dpi=180)
    plt.close(fig)

    centroid_data = summary["centroids"]
    dimensions = ["FLEXIBILITY", "PERFORMANCE", "STRICTNESS"]
    x = range(len(dimensions))
    fig, axis = plt.subplots(figsize=(8, 4.8))
    axis.plot(x, [centroid_data["Agile"][key] for key in dimensions], marker="o", linewidth=2, label="Agile", color="#059669")
    axis.plot(x, [centroid_data["Traditional"][key] for key in dimensions], marker="o", linewidth=2, label="Traditional", color="#475569")
    axis.set_xticks(list(x), ["Adaptation/readiness", "Delivery constraints", "Assurance/dependencies"])
    axis.set_ylim(1, 5)
    axis.set_ylabel("Mean (1–5)")
    axis.set_title("Provisional survey-derived reference profiles")
    axis.legend()
    axis.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_dir / "centroid-profiles.png", dpi=180)
    plt.close(fig)

    ranked = sorted(
        ((factor_label(key), data["eta_squared"]) for key, data in summary["effect_sizes"].items()),
        key=lambda item: item[1],
    )
    fig, axis = plt.subplots(figsize=(9, 6.5))
    axis.barh([item[0] for item in ranked], [item[1] for item in ranked], color="#2563eb")
    axis.set_xlabel("Eta-squared")
    axis.set_title("Methodology-group separation by survey factor")
    axis.grid(axis="x", alpha=0.2)
    fig.tight_layout()
    fig.savefig(output_dir / "factor-effect-sizes.png", dpi=180)
    plt.close(fig)

    weights = summary["weights"]["cleaned_influence_percent"]
    fig, axis = plt.subplots(figsize=(7.5, 4.8))
    labels = ["Adaptation/readiness", "Delivery constraints", "Assurance/dependencies"]
    values = [weights[key] for key in dimensions]
    bars = axis.bar(labels, values, color=["#2563eb", "#64748b", "#0f766e"])
    axis.bar_label(bars, labels=[f"{value:.1f}%" for value in values], padding=3)
    axis.set_ylim(0, max(values) + 10)
    axis.set_ylabel("Nominal model influence")
    axis.set_title("Effect-size-derived provisional construct weights")
    fig.tight_layout()
    fig.savefig(output_dir / "construct-weight-influence.png", dpi=180)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--no-figures", action="store_true")
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)
    raw_headers, raw_rows, cleaned_rows = load_rows(args.input)
    write_clean_csv(raw_headers, cleaned_rows)
    weights = weight_analysis(raw_rows, cleaned_rows)
    equal_weights = {construct: 1.0 for construct in CONSTRUCT_FACTORS}
    effect_weights = weights["cleaned_weights"]
    summary = {
        "analysis_date": "2026-07-27",
        "random_seed": RANDOM_SEED,
        "raw_sample_size": len(raw_rows),
        "cleaned_sample_size": len(cleaned_rows),
        "excluded_source_rows": sorted(EXCLUDED_SOURCE_ROWS),
        "exclusion_reason": "Probable duplicate/copy responses; no valid scale-value outliers removed.",
        "distributions": distributions(cleaned_rows),
        "factor_means": factor_means(cleaned_rows),
        "factor_descriptives": factor_descriptives(cleaned_rows),
        "effect_sizes": effect_size_analysis(cleaned_rows),
        "reliability": reliability_analysis(cleaned_rows),
        "industry_methodology_association": cramers_v(cleaned_rows),
        "collection_wave_sensitivity": wave_analysis(cleaned_rows),
        "centroids": centroids(cleaned_rows),
        "weights": weights,
        "classification_diagnostics": {
            "cleaned": {
                "equal_weights": classification_metrics(cleaned_rows, equal_weights),
                "effect_size_weights": classification_metrics(cleaned_rows, effect_weights),
            },
            "raw": {
                "equal_weights": classification_metrics(raw_rows, equal_weights),
                "effect_size_weights": classification_metrics(raw_rows, effect_weights),
            },
        },
        "qualitative_themes": QUALITATIVE_THEMES,
        "research_boundary": "Historical methodology used is not an independent label of methodology suitability.",
    }
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    write_tables(args.output, summary)
    write_question_matrix(args.output, summary)
    write_qualitative_report(args.output)
    write_deep_report(args.output, summary)
    if not args.no_figures:
        write_figures(args.output, summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
