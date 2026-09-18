export type Methodology = "Agile" | "Traditional";

export type ConfidenceBand = {
  key: "close" | "moderate" | "high";
  label: string;
  description: string;
};

export type DecisionDriver = {
  key: string;
  label: string;
  projectScore: number;
  agileReference: number;
  traditionalReference: number;
  agileDistance: number;
  traditionalDistance: number;
  directionalFit: number;
  preferredMethod: Methodology | "Balanced";
};

export type EvidenceContribution = {
  key: string;
  label: string;
  coverage: number;
  contribution: number;
};

const SIGNAL_LABELS: Record<string, string> = {
  timeline_adherence: "Timeline constraints",
  budget_accuracy: "Budget constraints",
  product_quality: "Quality assurance",
  user_satisfaction: "User feedback need",
  communication_effectiveness: "Collaboration readiness",
  security_integration: "Security and assurance",
  system_integration_effectiveness: "Integration and dependencies",
};

const CONSTRUCT_LABELS: Record<string, string> = {
  FLEXIBILITY: "Flexibility",
  PERFORMANCE: "Performance",
  STRICTNESS: "Strictness",
};

const CONSTRUCT_KEYS = ["FLEXIBILITY", "PERFORMANCE", "STRICTNESS"];

export function formatDecisionSignal(value: string): string {
  return SIGNAL_LABELS[value]
    ?? value
      .split("_")
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
      .join(" ");
}

export function confidenceBand(scoreGap: number): ConfidenceBand {
  if (scoreGap >= 20) {
    return { key: "high", label: "High confidence", description: "The score gap is at least 20 points." };
  }
  if (scoreGap >= 10) {
    return { key: "moderate", label: "Moderate confidence", description: "The score gap is between 10 and 19.9 points." };
  }
  return { key: "close", label: "Close decision", description: "The score gap is below 10 points and needs stakeholder review." };
}

export function buildDecisionDrivers({
  dimensions,
  project,
  agile,
  traditional,
}: {
  dimensions: string[];
  project: number[];
  agile: number[];
  traditional: number[];
}): DecisionDriver[] {
  return dimensions
    .map((key, index) => {
      const projectScore = project[index];
      const agileReference = agile[index];
      const traditionalReference = traditional[index];

      if (![projectScore, agileReference, traditionalReference].every(Number.isFinite)) {
        return null;
      }

      const agileDistance = Math.abs(projectScore - agileReference);
      const traditionalDistance = Math.abs(projectScore - traditionalReference);
      const directionalFit = traditionalDistance - agileDistance;
      const preferredMethod = directionalFit === 0 ? "Balanced" : directionalFit > 0 ? "Agile" : "Traditional";

      return {
        key,
        label: formatDecisionSignal(key),
        projectScore,
        agileReference,
        traditionalReference,
        agileDistance,
        traditionalDistance,
        directionalFit,
        preferredMethod,
      };
    })
    .filter((driver): driver is DecisionDriver => driver !== null)
    .sort((left, right) => Math.abs(right.directionalFit) - Math.abs(left.directionalFit));
}

export function buildEvidenceContributions({
  coverage,
  contribution,
}: {
  coverage: Record<string, number>;
  contribution: Record<string, number>;
}): EvidenceContribution[] {
  return CONSTRUCT_KEYS.map((key) => ({
    key,
    label: CONSTRUCT_LABELS[key],
    coverage: clamp(coverage[key] ?? 0, 0, 1),
    contribution: clamp(contribution[key] ?? 0, 0, 1),
  }));
}

export function averageEvidenceCoverage(contributions: EvidenceContribution[]): number {
  if (!contributions.length) return 0;
  return contributions.reduce((total, item) => total + item.coverage, 0) / contributions.length;
}

export function chartMagnitude(drivers: DecisionDriver[]): number {
  const maximum = Math.max(0, ...drivers.map((driver) => Math.abs(driver.directionalFit)));
  return Math.max(1, Math.ceil(maximum * 2) / 2);
}

function clamp(value: number, minimum: number, maximum: number): number {
  return Math.min(maximum, Math.max(minimum, value));
}
