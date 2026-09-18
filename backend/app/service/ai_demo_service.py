from __future__ import annotations

from collections import Counter


class AIDemoService:
    STAGE_LABELS = {
        "ingest": "Document intake",
        "extract": "Candidate signal extraction",
        "align": "Answer-to-document alignment",
        "score": "Methodology scoring",
        "explain": "Recommendation explanation",
    }

    @staticmethod
    def _signal_candidates(profile, documents: list, construct_scores: dict[str, float]) -> list[dict[str, object]]:
        candidates: list[dict[str, object]] = []
        project_type = str(getattr(profile, "project_type", "") or "").lower()
        industry = str(getattr(profile, "industry", "") or "").lower()
        duration = str(getattr(profile, "duration", "") or "").lower()

        if documents:
            candidates.append(
                {
                    "key": "document_count",
                    "label": "Supporting documents present",
                    "value": len(documents),
                    "confidence": "high",
                    "source": "documents",
                }
            )
        if "integration" in project_type:
            candidates.append(
                {
                    "key": "integration_complexity",
                    "label": "Integration-heavy delivery context",
                    "value": "candidate",
                    "confidence": "moderate",
                    "source": "profile",
                }
            )
        if industry in {"banking & finance", "government", "healthcare"}:
            candidates.append(
                {
                    "key": "compliance_pressure",
                    "label": "Potential compliance pressure",
                    "value": "candidate",
                    "confidence": "moderate",
                    "source": "profile",
                }
            )
        if "year" in duration:
            candidates.append(
                {
                    "key": "long_horizon_coordination",
                    "label": "Long delivery horizon",
                    "value": "candidate",
                    "confidence": "moderate",
                    "source": "profile",
                }
            )
        if float(construct_scores.get("FLEXIBILITY", 0.0)) >= 3.5:
            candidates.append(
                {
                    "key": "change_tolerance",
                    "label": "High change tolerance",
                    "value": round(float(construct_scores["FLEXIBILITY"]), 2),
                    "confidence": "high",
                    "source": "answers",
                }
            )
        if float(construct_scores.get("STRICTNESS", 0.0)) >= 3.5:
            candidates.append(
                {
                    "key": "governance_controls",
                    "label": "Higher governance expectation",
                    "value": round(float(construct_scores["STRICTNESS"]), 2),
                    "confidence": "high",
                    "source": "answers",
                }
            )
        return candidates

    def build_trace(
        self,
        *,
        profile,
        documents: list,
        construct_scores: dict[str, float],
        recommendation: str,
        score_gap: float,
    ) -> tuple[list[dict[str, object]], dict[str, object]]:
        candidates = self._signal_candidates(profile, documents, construct_scores)
        document_names = [str(getattr(document, "filename", "")) for document in documents]
        trace = [
            {
                "stage": "ingest",
                "label": self.STAGE_LABELS["ingest"],
                "status": "completed",
                "detail": f"Registered {len(documents)} supporting document(s) for the assessment draft.",
                "artifacts": document_names,
                "duration_ms": 850 + (len(documents) * 180),
            },
            {
                "stage": "extract",
                "label": self.STAGE_LABELS["extract"],
                "status": "completed",
                "detail": "Simulated OCR and chunk review prepared candidate evidence markers for later verification.",
                "artifacts": candidates,
                "duration_ms": 1400 + (len(candidates) * 120),
            },
            {
                "stage": "align",
                "label": self.STAGE_LABELS["align"],
                "status": "completed",
                "detail": "Compared questionnaire answers with candidate document signals. No answer was auto-overridden in demo mode.",
                "artifacts": {
                    "matched_signals": [candidate["key"] for candidate in candidates],
                    "document_backed_answers": min(len(candidates), 3),
                },
                "duration_ms": 1100 + (len(candidates) * 90),
            },
            {
                "stage": "score",
                "label": self.STAGE_LABELS["score"],
                "status": "completed",
                "detail": f"Calculated methodology fit with a {round(score_gap, 2)} point gap favoring {recommendation}.",
                "artifacts": {
                    "construct_scores": {key: round(float(value), 2) for key, value in construct_scores.items()},
                    "recommendation": recommendation,
                },
                "duration_ms": 920,
            },
            {
                "stage": "explain",
                "label": self.STAGE_LABELS["explain"],
                "status": "completed",
                "detail": "Prepared a demo explanation trail showing what the future AI pipeline would present to reviewers.",
                "artifacts": {
                    "note": "Candidate signals are explanatory only. They are not authoritative extracted facts.",
                },
                "duration_ms": 760,
            },
        ]
        summary = {
            "documents_processed": len(documents),
            "trace_steps": len(trace),
            "candidate_signals": candidates,
            "document_filenames": document_names,
            "demo_mode": True,
            "explanation_scope": "candidate_signals_only",
        }
        return trace, summary

    @staticmethod
    def aggregate_stage_frequency(results: list) -> dict[str, int]:
        counts: Counter[str] = Counter()
        for result in results:
            for step in result.ai_demo_trace or []:
                stage = str(step.get("stage") or "")
                if stage:
                    counts[stage] += 1
        return dict(counts)

    @staticmethod
    def aggregate_candidate_signal_frequency(results: list) -> dict[str, int]:
        counts: Counter[str] = Counter()
        for result in results:
            summary = result.ai_demo_summary or {}
            for signal in summary.get("candidate_signals", []):
                if not isinstance(signal, dict):
                    continue
                key = str(signal.get("key") or "")
                if key:
                    counts[key] += 1
        return dict(counts)
