export function formatDate(value: string): string {
  return new Intl.DateTimeFormat("vi", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export function getStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    uploaded: "Đã tải lên",
    processing: "Đang xử lý",
    completed: "Đã trích xuất",
    analyzing: "Đang phân tích",
    analyzed: "Đã phân tích",
    failed: "Thất bại",
  };

  return labels[status] ?? status;
}

export function getStatusTone(status: string): string {
  if (status === "failed") {
    return "danger";
  }

  if (status === "uploaded" || status === "processing" || status === "analyzing") {
    return "pending";
  }

  return "ready";
}
