import { beforeEach, describe, expect, it } from "vitest";
import { useFilterStore } from "./filterStore";

const initialState = useFilterStore.getState();

beforeEach(() => {
  useFilterStore.setState(initialState, true);
});

describe("useFilterStore", () => {
  it("toggleCategory adds an id that isn't selected yet", () => {
    useFilterStore.getState().toggleCategory("cat-1");
    expect(useFilterStore.getState().selectedCategoryIds).toEqual(["cat-1"]);
  });

  it("toggleCategory removes an id that's already selected", () => {
    useFilterStore.getState().toggleCategory("cat-1");
    useFilterStore.getState().toggleCategory("cat-1");
    expect(useFilterStore.getState().selectedCategoryIds).toEqual([]);
  });

  it("toggleCategory preserves other selected ids", () => {
    useFilterStore.getState().toggleCategory("cat-1");
    useFilterStore.getState().toggleCategory("cat-2");
    useFilterStore.getState().toggleCategory("cat-1");
    expect(useFilterStore.getState().selectedCategoryIds).toEqual(["cat-2"]);
  });

  it("clearCategories empties the selection", () => {
    useFilterStore.getState().toggleCategory("cat-1");
    useFilterStore.getState().toggleCategory("cat-2");
    useFilterStore.getState().clearCategories();
    expect(useFilterStore.getState().selectedCategoryIds).toEqual([]);
  });

  it("toggleSource behaves independently of toggleCategory", () => {
    useFilterStore.getState().toggleCategory("cat-1");
    useFilterStore.getState().toggleSource("src-1");
    expect(useFilterStore.getState().selectedCategoryIds).toEqual(["cat-1"]);
    expect(useFilterStore.getState().selectedSourceIds).toEqual(["src-1"]);
  });

  it("setTab switches the active tab and clears the custom tab selection", () => {
    useFilterStore.getState().setCustomTab("custom-42");
    useFilterStore.getState().setTab("relevant");
    expect(useFilterStore.getState().activeTab).toBe("relevant");
    expect(useFilterStore.getState().activeCustomTabId).toBeNull();
  });
});
