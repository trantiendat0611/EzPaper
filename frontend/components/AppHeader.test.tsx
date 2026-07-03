import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { AppHeader } from "./AppHeader";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

describe("AppHeader", () => {
  it("renders the brand and sign-out button", () => {
    render(<AppHeader />);
    expect(screen.getByText("EzPaper")).toBeDefined();
    expect(screen.getByText("Đăng xuất")).toBeDefined();
  });

  it("shows the user email when provided", () => {
    render(<AppHeader email="reader@example.com" />);
    expect(screen.getByText("reader@example.com")).toBeDefined();
  });
});
