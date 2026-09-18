import { describe, expect, it } from "vitest";
import { validateHumanText } from "@/lib/textValidation";

describe("validateHumanText", () => {
  it.each([
    ["", "Please enter at least 2 characters."],
    ["A", "Please enter at least 2 characters."],
    ["aaaaaa", "Please enter a valid response."],
    ["!@#$%^& hello", "Response contains too many symbols."],
    ["bcdfghjkl", "Please enter a valid response."],
  ])("rejects invalid response %j", (value, message) => {
    expect(validateHumanText(value)).toBe(message);
  });

  it.each(["Maya Fernando", "Ceylon Transit Systems", "Operations Renewal", "R&D Platform 2027"])(
    "accepts meaningful response %j",
    (value) => expect(validateHumanText(value)).toBeNull(),
  );
});
