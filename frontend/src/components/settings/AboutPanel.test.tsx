import { describe, expect, it } from "vitest";
import userEvent from "@testing-library/user-event";
import { render, screen } from "../../test/render";
import AboutPanel from "./AboutPanel";

describe("AboutPanel", () => {
  it("renders the three section headers", () => {
    render(<AboutPanel />);
    expect(screen.getByText("What is Shoebill Feed?")).toBeInTheDocument();
    expect(screen.getByText("How it works")).toBeInTheDocument();
    expect(screen.getByText("Symbols in your feed")).toBeInTheDocument();
  });

  it("shows the symbol legend once expanded, with real icon labels", async () => {
    const user = userEvent.setup();
    render(<AboutPanel />);

    await user.click(screen.getByText("Symbols in your feed"));

    expect(screen.getByText("Relevant")).toBeInTheDocument();
    expect(screen.getByText("Not interested")).toBeInTheDocument();
    expect(screen.getByText("Source icons")).toBeInTheDocument();
    expect(screen.getByText("Category label")).toBeInTheDocument();
  });
});
