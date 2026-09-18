import { afterEach, describe, expect, it, vi } from "vitest";
import { adminDelete } from "@/lib/adminApi";

describe("adminDelete", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("sends the server safety confirmation for destructive maintenance actions", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          success: true,
          message: "Deleted",
          data: { incomplete_sessions: 2 },
        }),
        { status: 200, headers: { "Content-Type": "application/json" } }
      )
    );

    await adminDelete("/api/v1/admin/assessment-activity/incomplete", "token", {
      confirmation: "RESET INCOMPLETE DATA",
    });

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/admin/assessment-activity/incomplete"),
      expect.objectContaining({
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
          Authorization: "Bearer token",
        },
        body: JSON.stringify({ confirmation: "RESET INCOMPLETE DATA" }),
      })
    );
  });

  it("keeps existing assessment deletes bodyless", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({ success: true, message: "Deleted", data: null }),
        { status: 200, headers: { "Content-Type": "application/json" } }
      )
    );

    await adminDelete("/api/v1/admin/assessments/42", "token");

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/admin/assessments/42"),
      {
        method: "DELETE",
        headers: { Authorization: "Bearer token" },
      }
    );
  });
});
