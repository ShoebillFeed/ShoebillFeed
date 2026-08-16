import { beforeEach, describe, expect, it } from "vitest";
import { useAnalyseTrendsStore } from "./analyseTrendsStore";

const initialState = useAnalyseTrendsStore.getState();

beforeEach(() => {
  useAnalyseTrendsStore.setState(initialState, true);
  localStorage.clear();
});

describe("useAnalyseTrendsStore", () => {
  it("setTopics replaces the topic list", () => {
    const topics = [{ id: "t1", label: "AI", keywords: ["ai", "llm"] }];
    useAnalyseTrendsStore.getState().setTopics(topics);
    expect(useAnalyseTrendsStore.getState().topics).toEqual(topics);
  });

  it("setTopics preserves a user-picked color", () => {
    const topics = [{ id: "t1", label: "AI", keywords: ["ai"], color: "#ff00aa" }];
    useAnalyseTrendsStore.getState().setTopics(topics);
    expect(useAnalyseTrendsStore.getState().topics[0].color).toBe("#ff00aa");
  });

  it("setCategoryIds/setSourceIds replace their respective lists", () => {
    useAnalyseTrendsStore.getState().setCategoryIds(["cat-1", "cat-2"]);
    useAnalyseTrendsStore.getState().setSourceIds(["src-1"]);
    expect(useAnalyseTrendsStore.getState().categoryIds).toEqual(["cat-1", "cat-2"]);
    expect(useAnalyseTrendsStore.getState().sourceIds).toEqual(["src-1"]);
  });

  it("setDays accepts a finite window or null for all time", () => {
    useAnalyseTrendsStore.getState().setDays(365);
    expect(useAnalyseTrendsStore.getState().days).toBe(365);
    useAnalyseTrendsStore.getState().setDays(null);
    expect(useAnalyseTrendsStore.getState().days).toBeNull();
  });

  it("persists topics to localStorage so they survive a reload", () => {
    const topics = [{ id: "t1", label: "Climate", keywords: ["climate change"] }];
    useAnalyseTrendsStore.getState().setTopics(topics);

    const stored = JSON.parse(localStorage.getItem("shoebill-feed-trends") ?? "{}");
    expect(stored.state.topics).toEqual(topics);
  });
});
