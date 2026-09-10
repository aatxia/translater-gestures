import { describe, expect, it } from "vitest";
import { groupGlossesForDisplay } from "./glossDisplay";

describe("groupGlossesForDisplay", () => {
  it("renders each regular gloss as its own item", () => {
    const items = groupGlossesForDisplay(["I", "WANT", "WATER"]);

    expect(items.map((item) => item.label)).toEqual(["I", "WANT", "WATER"]);
    expect(items.every((item) => !item.isFingerspell)).toBe(true);
  });

  it("collapses a run of fingerspelling tokens into one spelled-word item", () => {
    const items = groupGlossesForDisplay(["FS_О", "FS_К", "FS_С", "FS_А", "FS_Н", "FS_А"]);

    expect(items).toHaveLength(1);
    expect(items[0]?.isFingerspell).toBe(true);
    expect(items[0]?.label).toBe("🔤 Оксана");
  });

  it("groups a fingerspelled run inside a larger sequence without touching the rest", () => {
    const items = groupGlossesForDisplay(["I", "LIKE", "FS_О", "FS_К", "FS_С", "FS_А", "FS_Н", "FS_У"]);

    expect(items.map((item) => item.label)).toEqual(["I", "LIKE", "🔤 Оксану"]);
    expect(items.map((item) => item.isFingerspell)).toEqual([false, false, true]);
  });

  it("handles an empty sequence", () => {
    expect(groupGlossesForDisplay([])).toEqual([]);
  });
});
