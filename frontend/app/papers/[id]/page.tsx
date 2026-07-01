"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { ArrowLeft, BookMarked, Brain, CheckCircle2, FileText, Layers, RefreshCw, Trash2 } from "lucide-react";
import { AppHeader } from "@/components/AppHeader";
import { analyzePaper, deletePaper, getCurrentUser, getPaper, PaperDetail, User } from "@/lib/api";
import { getToken } from "@/lib/auth";
import { formatDate, getStatusLabel, getStatusTone } from "@/lib/format";

export default function PaperDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [paper, setPaper] = useState<PaperDetail | null>(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  async function loadData() {
    setError("");
    setIsLoading(true);
    try {
      const [currentUser, paperDetail] = await Promise.all([getCurrentUser(), getPaper(params.id)]);
      setUser(currentUser);
      setPaper(paperDetail);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load paper");
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
  }, [params.id, router]);

  async function handleAnalyze() {
    if (!paper) {
      return;
    }

    setIsAnalyzing(true);
    setError("");
    try {
      const analyzed = await analyzePaper(paper.id);
      setPaper(analyzed);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed");
    } finally {
      setIsAnalyzing(false);
    }
  }

  async function handleDelete() {
    if (!paper) {
      return;
    }

    const confirmed = window.confirm("Xóa bài báo này và các phần đã trích xuất?");
    if (!confirmed) {
      return;
    }

    setIsDeleting(true);
    setError("");
    try {
      await deletePaper(paper.id);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed");
      setIsDeleting(false);
    }
  }

  const analyzedSections = paper?.sections.filter((section) => section.summary_vi && section.explanation_vi).length ?? 0;
  const canAnalyze = Boolean(paper && paper.sections.length > 0 && paper.status !== "analyzing");

  return (
    <main className="app-shell">
      <AppHeader email={user?.email} />
      <section className="container">
        <div className="toolbar">
          <div>
            <Link className="text-link" href="/dashboard">
              <ArrowLeft size={16} /> Quay lại
            </Link>
            <h1 className="page-title">{paper?.title ?? "Bài báo"}</h1>
            {paper ? <p className="page-subtitle">{paper.original_filename} · {formatDate(paper.created_at)}</p> : null}
          </div>
          <div className="upload-row">
            {paper ? <span className={`status ${getStatusTone(paper.status)}`}>{getStatusLabel(paper.status)}</span> : null}
            <button className="button secondary" type="button" onClick={() => void loadData()} title="Làm mới">
              <RefreshCw size={17} />
            </button>
            <button className="button" type="button" onClick={handleAnalyze} disabled={!canAnalyze || isAnalyzing}>
              <Brain size={18} />
              {isAnalyzing ? "Đang phân tích..." : "Phân tích"}
            </button>
            <button className="button danger" type="button" onClick={handleDelete} disabled={!paper || isDeleting}>
              <Trash2 size={18} />
              {isDeleting ? "Đang xóa..." : "Xóa"}
            </button>
          </div>
        </div>

        {paper ? (
          <div className="stats-grid">
            <div className="stat">
              <span className="stat-icon">
                <Layers size={20} />
              </span>
              <span className="stat-body">
                <span className="stat-value">{paper.sections.length}</span>
                <span className="stat-label">Số phần</span>
              </span>
            </div>
            <div className="stat">
              <span className="stat-icon">
                <CheckCircle2 size={20} />
              </span>
              <span className="stat-body">
                <span className="stat-value">{analyzedSections}</span>
                <span className="stat-label">Phần đã phân tích</span>
              </span>
            </div>
            <div className="stat">
              <span className="stat-icon">
                <BookMarked size={20} />
              </span>
              <span className="stat-body">
                <span className="stat-value">{paper.abstract ? "Có" : "Không"}</span>
                <span className="stat-label">Tìm thấy tóm tắt</span>
              </span>
            </div>
          </div>
        ) : null}

        {error ? <div className="error">{error}</div> : null}

        {isLoading ? (
          <div className="empty-state">Đang tải...</div>
        ) : !paper ? (
          <div className="empty-state">Không tìm thấy bài báo</div>
        ) : (
          <div className="detail-grid">
            <nav className="section-nav">
              <div className="section-nav-title">Các phần</div>
              {paper.sections.map((section) => (
                <a href={`#section-${section.id}`} key={section.id}>
                  {section.title}
                </a>
              ))}
            </nav>
            <article className="reader">
              {paper.sections.length === 0 ? (
                <div className="empty-state">Chưa có phần nào</div>
              ) : (
                paper.sections.map((section) => (
                  <section className="section" id={`section-${section.id}`} key={section.id}>
                    <div className="section-heading">
                      <h2>{section.title}</h2>
                      <span className="meta">{section.section_type}</span>
                    </div>
                    {section.summary_vi ? (
                      <div className="analysis-band">
                        <span className="analysis-label">Tóm tắt</span>
                        <div className="section-text">{section.summary_vi}</div>
                      </div>
                    ) : null}
                    {section.explanation_vi ? (
                      <div className="analysis-band">
                        <span className="analysis-label">Giải thích</span>
                        <div className="section-text">{section.explanation_vi}</div>
                      </div>
                    ) : null}
                    <div className="source-block">
                      <span className="analysis-label">
                        <FileText size={14} />
                        Nội dung gốc
                      </span>
                      <div className="section-text">{section.raw_text}</div>
                    </div>
                  </section>
                ))
              )}
            </article>
          </div>
        )}
      </section>
    </main>
  );
}
