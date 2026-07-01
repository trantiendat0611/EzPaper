"use client";

import Link from "next/link";
import { ChangeEvent, useEffect, useState } from "react";
import { BrainCircuit, FileCheck2, FileUp, Files, RefreshCw } from "lucide-react";
import { AppHeader } from "@/components/AppHeader";
import { getCurrentUser, listPapers, Paper, uploadPaper, User } from "@/lib/api";
import { getToken } from "@/lib/auth";
import { formatDate, getStatusLabel, getStatusTone } from "@/lib/format";
import { useRouter } from "next/navigation";

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [papers, setPapers] = useState<Paper[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);

  async function loadData() {
    setError("");
    setIsLoading(true);
    try {
      const [currentUser, paperItems] = await Promise.all([getCurrentUser(), listPapers()]);
      setUser(currentUser);
      setPapers(paperItems);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load dashboard");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    void loadData();
  }, [router]);

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    setFile(event.target.files?.[0] ?? null);
  }

  async function handleUpload() {
    if (!file) {
      return;
    }

    setError("");
    setIsUploading(true);
    try {
      const uploaded = await uploadPaper(file);
      setFile(null);
      router.push(`/papers/${uploaded.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setIsUploading(false);
    }
  }

  const analyzedCount = papers.filter((paper) => paper.status === "analyzed").length;
  const extractedCount = papers.filter((paper) => paper.status === "completed" || paper.status === "analyzed").length;

  return (
    <main className="app-shell">
      <AppHeader email={user?.email} />
      <section className="container">
        <div className="toolbar">
          <div>
            <h1 className="page-title">Bài báo của bạn</h1>
            <p className="page-subtitle">Tải lên, trích xuất và xem lại các bài báo khoa học.</p>
          </div>
          <div className="upload-row">
            <input className="file-input" type="file" accept="application/pdf,.pdf" onChange={handleFileChange} />
            <button className="button" type="button" disabled={!file || isUploading} onClick={handleUpload}>
              <FileUp size={18} />
              {isUploading ? "Đang tải lên..." : "Tải lên"}
            </button>
            <button className="button secondary" type="button" onClick={() => void loadData()} title="Làm mới">
              <RefreshCw size={17} />
            </button>
          </div>
        </div>

        <div className="stats-grid">
          <div className="stat">
            <span className="stat-icon">
              <Files size={20} />
            </span>
            <span className="stat-body">
              <span className="stat-value">{papers.length}</span>
              <span className="stat-label">Bài báo</span>
            </span>
          </div>
          <div className="stat">
            <span className="stat-icon">
              <FileCheck2 size={20} />
            </span>
            <span className="stat-body">
              <span className="stat-value">{extractedCount}</span>
              <span className="stat-label">Đã trích xuất</span>
            </span>
          </div>
          <div className="stat">
            <span className="stat-icon">
              <BrainCircuit size={20} />
            </span>
            <span className="stat-body">
              <span className="stat-value">{analyzedCount}</span>
              <span className="stat-label">Đã phân tích</span>
            </span>
          </div>
        </div>

        {error ? <div className="error">{error}</div> : null}

        {isLoading ? (
          <div className="empty-state">Đang tải...</div>
        ) : papers.length === 0 ? (
          <div className="empty-state">Chưa có bài báo nào. Chọn một file PDF để bắt đầu.</div>
        ) : (
          <div className="grid">
            {papers.map((paper) => (
              <Link className="paper-card" href={`/papers/${paper.id}`} key={paper.id}>
                <span className={`status ${getStatusTone(paper.status)}`}>{getStatusLabel(paper.status)}</span>
                <h2>{paper.title}</h2>
                <span className="meta">{paper.original_filename}</span>
                <span className="meta">{formatDate(paper.created_at)}</span>
              </Link>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}
