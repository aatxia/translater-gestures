import { describe, expect, it } from "vitest";
import { groupGlossesForDisplay } from "./glossDisplay";

describe("groupGlossesForDisplay", () => {
  it("renders each regular gloss as its own item", () => {
    const items = groupGlossesForDisplay(["I", "WANT", "WATER"]);

    expect(items.map((item) => item.label)).toEqual(["I", "WANT", "WATER"]);
    expect(items.every((item) => !item.isFingerspell)).toBe(true);
  });

  it("collapses a run of fingerspelling tokens into one spelled-word item", () => {
    const letters = ["FS_О", "FS_К", "FS_С", "FS_А", "FS_Н", "FS_А"];
    const items = groupGlossesForDisplay(letters);

    expect(items).toHaveLength(1);
    expect(items[0]?.isFingerspell).toBe(true);
    expect(items[0]?.label).toBe("Оксана");
    expect(items[0]?.tokens).toEqual(letters);
  });

  it("gives each regular gloss item its own single-token tokens array", () => {
    const items = groupGlossesForDisplay(["I", "WANT"]);

    expect(items.map((item) => item.tokens)).toEqual([["I"], ["WANT"]]);
  });

  it("groups a fingerspelled run inside a larger sequence without touching the rest", () => {
    const items = groupGlossesForDisplay(["I", "LIKE", "FS_О", "FS_К", "FS_С", "FS_А", "FS_Н", "FS_У"]);

    expect(items.map((item) => item.label)).toEqual(["I", "LIKE", "Оксану"]);
    expect(items.map((item) => item.isFingerspell)).toEqual([false, false, true]);
  });

  it("handles an empty sequence", () => {
    expect(groupGlossesForDisplay([])).toEqual([]);
  });

  it("renders an underscore in a multi-word gloss token as a space, not the raw symbol", () => {
    const items = groupGlossesForDisplay(["YOU_PL", "WORK_N", "DO_POBACHENNYA"]);

    expect(items.map((item) => item.label)).toEqual(["YOU PL", "WORK N", "DO POBACHENNYA"]);
    expect(items.some((item) => item.label.includes("_"))).toBe(false);
  });
});
