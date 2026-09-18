from dataclasses import dataclass

from app.model.admin_model import RuleConfig
from app.model.assessment_model import AnswerInput


@dataclass
class EngineResult:
    recommendation: str
    agile_score: float
    traditional_score: float
    construct_scores: dict[str, float]
    rationale: str


class EngineService:
    @staticmethod
    def _avg(values: list[int]) -> float:
        return sum(values) / len(values) if values else 0.0

    def compute(self, answers: list[AnswerInput], rules: RuleConfig) -> EngineResult:
        grouped: dict[str, list[int]] = {"FLEXIBILITY": [], "PERFORMANCE": [], "STRICTNESS": []}
        for answer in answers:
            grouped[answer.construct_key].append(answer.value)

        construct_scores = {k: self._avg(v) for k, v in grouped.items()}
        return self.compute_from_construct_scores(construct_scores, rules)

    def compute_from_construct_scores(self, construct_scores: dict[str, float], rules: RuleConfig) -> EngineResult:
        normalized_scores = {
            key: float(construct_scores.get(key, 0.0))
            for key in ("FLEXIBILITY", "PERFORMANCE", "STRICTNESS")
        }
        weighted = {k: normalized_scores[k] * rules.construct_weights[k] for k in normalized_scores}
        agile_gap = sum(abs(weighted[k] - (rules.agile_baseline[k] * rules.construct_weights[k])) for k in weighted)
        traditional_gap = sum(
            abs(weighted[k] - (rules.traditional_baseline[k] * rules.construct_weights[k])) for k in weighted
        )
        gap_scale = (
            4.0 * sum(float(value) for value in rules.construct_weights.values())
            if rules.compatibility_normalization == "weighted_range"
            else 15.0
        )
        agile_score = max(0.0, 100.0 - (agile_gap / gap_scale) * 100.0)
        traditional_score = max(0.0, 100.0 - (traditional_gap / gap_scale) * 100.0)

        if rules.strictness_override_enabled and normalized_scores["STRICTNESS"] >= rules.strictness_threshold:
            recommendation = "Traditional"
        else:
            recommendation = "Agile" if agile_score >= traditional_score else "Traditional"

        rationale = (
            f"Flexibility {normalized_scores['FLEXIBILITY']:.2f}, "
            f"Performance {normalized_scores['PERFORMANCE']:.2f}, "
            f"Strictness {normalized_scores['STRICTNESS']:.2f}."
        )
        return EngineResult(
            recommendation=recommendation,
            agile_score=round(agile_score, 2),
            traditional_score=round(traditional_score, 2),
            construct_scores={k: round(v, 2) for k, v in normalized_scores.items()},
            rationale=rationale,
        )
