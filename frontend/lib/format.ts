export function formatDate(value: string): string {
  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export function getStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    uploaded: "Uploaded",
    processing: "Processing",
    completed: "Extracted",
    analyzing: "Analyzing",
    analyzed: "Analyzed",
    failed: "Failed",
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
