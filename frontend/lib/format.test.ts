import { describe, expect, it } from "vitest";

import { getStatusLabel, getStatusTone, isInProgressStatus } from "./format";

describe("getStatusLabel", () => {
  it("maps known statuses to Vietnamese labels", () => {
    expect(getStatusLabel("completed")).toBe("Đã trích xuất");
    expect(getStatusLabel("analyzed")).toBe("Đã phân tích");
    expect(getStatusLabel("failed")).toBe("Thất bại");
  });

  it("returns the raw status for unknown values", () => {
    expect(getStatusLabel("mystery")).toBe("mystery");
  });
});

describe("getStatusTone", () => {
  it("returns danger for failed", () => {
    expect(getStatusTone("failed")).toBe("danger");
  });

  it("returns pending for in-progress statuses", () => {
    expect(getStatusTone("uploaded")).toBe("pending");
    expect(getStatusTone("processing")).toBe("pending");
    expect(getStatusTone("analyzing")).toBe("pending");
  });

  it("returns ready for finished statuses", () => {
    expect(getStatusTone("completed")).toBe("ready");
    expect(getStatusTone("analyzed")).toBe("ready");
  });
});

describe("isInProgressStatus", () => {
  it("is true only while work is pending", () => {
    expect(isInProgressStatus("processing")).toBe(true);
    expect(isInProgressStatus("analyzing")).toBe(true);
    expect(isInProgressStatus("completed")).toBe(false);
    expect(isInProgressStatus("failed")).toBe(false);
  });
});
