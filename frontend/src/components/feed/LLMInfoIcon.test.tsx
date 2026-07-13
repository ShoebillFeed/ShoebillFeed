import { describe, expect, it } from "vitest";
import userEvent from "@testing-library/user-event";
import { render, screen } from "../../test/render";
import { LLMInfoIcon } from "./LLMInfoIcon";

describe("LLMInfoIcon", () => {
  it("renders nothing when there's no provider", () => {
    const { container } = render(<LLMInfoIcon provider={null} model={null} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("combines provider and model into the tooltip label", () => {
    render(<LLMInfoIcon provider="anthropic" model="claude-haiku-4-5" />);
    expect(screen.getByText("anthropic · claude-haiku-4-5")).toBeInTheDocument();
  });

  it("falls back to just the provider name when model is unknown", () => {
    render(<LLMInfoIcon provider="ollama" model={null} />);
    expect(screen.getByText("ollama")).toBeInTheDocument();
  });

  it("shows the custom fields description when provided", () => {
    render(<LLMInfoIcon provider="anthropic" model="claude-haiku-4-5" fields="Source summary" />);
    expect(screen.getByText("Source summary")).toBeInTheDocument();
  });

  it("toggles the tooltip open on click", async () => {
    const user = userEvent.setup();
    render(<LLMInfoIcon provider="anthropic" model="claude-haiku-4-5" />);

    const button = screen.getByRole("button", { name: /llm info/i });
    const tooltipText = screen.getByText("anthropic · claude-haiku-4-5");

    expect(tooltipText.parentElement).toHaveClass("opacity-0");
    await user.click(button);
    expect(tooltipText.parentElement).toHaveClass("opacity-100");
    await user.click(button);
    expect(tooltipText.parentElement).toHaveClass("opacity-0");
  });

  it("closes the tooltip when clicking outside", async () => {
    const user = userEvent.setup();
    render(
      <div>
        <LLMInfoIcon provider="anthropic" model="claude-haiku-4-5" />
        <button>outside</button>
      </div>
    );

    await user.click(screen.getByRole("button", { name: /llm info/i }));
    const tooltipText = screen.getByText("anthropic · claude-haiku-4-5");
    expect(tooltipText.parentElement).toHaveClass("opacity-100");

    await user.click(screen.getByText("outside"));
    expect(tooltipText.parentElement).toHaveClass("opacity-0");
  });
});
