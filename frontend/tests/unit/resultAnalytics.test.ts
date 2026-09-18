import { describe, expect, it } from "vitest";
import {
  averageEvidenceCoverage,
  buildDecisionDrivers,
  buildEvidenceContributions,
  chartMagnitude,
  confidenceBand,
} from "@/lib/resultAnalytics";

describe("result analytics", () => {
  it("uses the configured confidence thresholds", () => {
    expect(confidenceBand(0).key).toBe("close");
    expect(confidenceBand(9.99).key).toBe("close");
    expect(confidenceBand(10).key).toBe("moderate");
    expect(confidenceBand(19.99).key).toBe("moderate");
    expect(confidenceBand(20).key).toBe("high");
  });

  it("ranks valid signals by relative reference proximity", () => {
    const drivers = buildDecisionDrivers({
      dimensions: ["timeline_adherence", "security_integration", "incomplete"],
      project: [4, 1, 3],
      agile: [5, 4],
      traditional: [2, 1],
    });

    expect(drivers).toHaveLength(2);
    expect(drivers[0]).toMatchObject({ key: "security_integration", preferredMethod: "Traditional", directionalFit: -3 });
    expect(drivers[1]).toMatchObject({ key: "timeline_adherence", preferredMethod: "Agile", directionalFit: 1 });
    expect(chartMagnitude(drivers)).toBe(3);
  });

  it("marks an equidistant signal as balanced", () => {
    const [driver] = buildDecisionDrivers({
      dimensions: ["product_quality"],
      project: [3],
      agile: [2],
      traditional: [4],
    });

    expect(driver.preferredMethod).toBe("Balanced");
    expect(driver.directionalFit).toBe(0);
  });

  it("clamps document values and reports average construct coverage", () => {
    const contributions = buildEvidenceContributions({
      coverage: { FLEXIBILITY: 1.2, PERFORMANCE: 0.5, STRICTNESS: -0.2 },
      contribution: { FLEXIBILITY: 0.25, PERFORMANCE: 0.125, STRICTNESS: 0 },
    });

    expect(contributions.map((item) => item.coverage)).toEqual([1, 0.5, 0]);
    expect(averageEvidenceCoverage(contributions)).toBe(0.5);
  });
});
