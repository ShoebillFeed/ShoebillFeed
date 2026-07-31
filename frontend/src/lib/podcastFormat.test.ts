import { describe, expect, it } from "vitest";
import { formatDuration } from "./podcastFormat";

describe("formatDuration", () => {
  it("formats whole minutes", () => {
    expect(formatDuration(300)).toBe("5:00");
  });

  it("pads seconds under ten", () => {
    expect(formatDuration(65)).toBe("1:05");
  });

  it("formats zero seconds as 0:00", () => {
    expect(formatDuration(0)).toBe("0:00");
  });

  it("truncates fractional seconds", () => {
    expect(formatDuration(90.9)).toBe("1:30");
  });

  it("returns an empty string for null", () => {
    expect(formatDuration(null)).toBe("");
  });
});
