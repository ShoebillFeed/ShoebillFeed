import { describe, expect, it } from "vitest";
import { sourceTypeIcon } from "./sourceTypeIcon";

describe("sourceTypeIcon", () => {
  it("returns a distinct icon for each known source type", () => {
    const known = ["rss", "reddit", "youtube", "email", "mastodon"];
    const icons = known.map(sourceTypeIcon);
    expect(new Set(icons).size).toBe(known.length);
  });

  it("falls back to a generic icon for unknown source types", () => {
    expect(sourceTypeIcon("some-unrecognized-type")).toBe("📄");
  });
});
