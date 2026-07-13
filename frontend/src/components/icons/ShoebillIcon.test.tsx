import { describe, expect, it } from "vitest";
import { render } from "../../test/render";
import { ShoebillIcon } from "./ShoebillIcon";

describe("ShoebillIcon", () => {
  it("renders an svg sized to the default", () => {
    const { container } = render(<ShoebillIcon />);
    const svg = container.querySelector("svg");
    expect(svg).toHaveAttribute("width", "24");
    expect(svg).toHaveAttribute("height", "24");
  });

  it("respects a custom size prop", () => {
    const { container } = render(<ShoebillIcon size={40} />);
    const svg = container.querySelector("svg");
    expect(svg).toHaveAttribute("width", "40");
    expect(svg).toHaveAttribute("height", "40");
  });

  it("passes through a custom className", () => {
    const { container } = render(<ShoebillIcon className="text-indigo-600" />);
    expect(container.querySelector("svg")).toHaveClass("text-indigo-600");
  });
});
