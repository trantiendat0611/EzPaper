"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import {
  ArrowLeft,
  BookMarked,
  Brain,
  CheckCircle2,
  FileText,
  Layers,
  MessageCircleQuestion,
  RefreshCw,
  RotateCw,
  Send,
  Sparkles,
  Trash2,
} from "lucide-react";
import { AppHeader } from "@/components/AppHeader";
import { useToast } from "@/components/Toast";
import {
  analyzePaper,
  analyzeSection,
  askQuestion,
  deletePaper,
  getCurrentUser,
  getPaper,
  listQuestions,
  PaperDetail,
  PaperQuestion,
  User,
} from "@/lib/api";
import { getToken } from "@/lib/auth";
import { formatDate, getStatusLabel, getStatusTone, isInProgressStatus } from "@/lib/format";

export default function PaperDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const { showToast } = useToast();
  const [user, setUser] = useState<User | null>(null);
  const [paper, setPaper] = useState<PaperDetail | null>(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [questions, setQuestions] = useState<PaperQuestion[]>([]);
  const [questionInput, setQuestionInput] = useState("");
  const [isAsking, setIsAsking] = useState(false);

  async function loadData() {
    setError("");
    setIsLoading(true);
    try {
      const [currentUser, paperDetail] = await Promise.all([getCurrentUser(), getPaper(params.id)]);
      setUser(currentUser);
      setPaper(paperDetail);
      listQuestions(paperDetail.id)
        .then(setQuestions)
        .catch(() => {});
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

  useEffect(() => {
    if (!paper || !isInProgressStatus(paper.status)) {
      return;
    }
    const interval = setInterval(() => {
      getPaper(params.id)
        .then(setPaper)
        .catch(() => {});
    }, 3000);
    return () => clearInterval(interval);
  }, [paper, params.id]);

  async function handleAnalyze() {
    if (!paper) {
      return;
    }

    setIsAnalyzing(true);
    try {
      const analyzed = await analyzePaper(paper.id);
      setPaper(analyzed);
      showToast("Đang phân tích bài báo...", "info");
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Phân tích thất bại", "error");
    } finally {
      setIsAnalyzing(false);
    }
  }

  async function handleRetrySection(sectionId: number) {
    if (!paper) {
      return;
    }

    try {
      const updated = await analyzeSection(paper.id, sectionId);
      setPaper(updated);
      showToast("Đang phân tích lại phần này...", "info");
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Phân tích lại thất bại", "error");
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
    try {
      await deletePaper(paper.id);
      showToast("Đã xóa bài báo", "success");
      router.push("/dashboard");
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Xóa thất bại", "error");
      setIsDeleting(false);
    }
  }

  async function handleAsk() {
    if (!paper) {
      return;
    }

    const question = questionInput.trim();
    if (!question) {
      return;
    }

    setIsAsking(true);
    try {
      const created = await askQuestion(paper.id, question);
      setQuestions((current) => [...current, created]);
      setQuestionInput("");
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Không trả lời được câu hỏi", "error");
    } finally {
      setIsAsking(false);
    }
  }

  const analyzedSections = paper?.sections.filter((section) => section.summary_vi && section.explanation_vi).length ?? 0;
  const canAnalyze = Boolean(paper && paper.sections.length > 0 && paper.status !== "analyzing");
  const canAsk = Boolean(paper && paper.sections.length > 0);

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

        {canAsk ? (
          <div className="qa-panel">
            <div className="qa-header">
              <MessageCircleQuestion size={18} />
              Hỏi đáp về bài báo
            </div>
            <div className="qa-history">
              {questions.length === 0 ? (
                <div className="qa-empty">
                  <Sparkles size={16} />
                  Đặt câu hỏi bất kỳ về nội dung bài báo, AI sẽ trả lời dựa trên bài báo của bạn.
                </div>
              ) : (
                questions.map((item) => (
                  <div className="qa-item" key={item.id}>
                    <div className="qa-question">
                      <span className="qa-badge">Hỏi</span>
                      <span>{item.question}</span>
                    </div>
                    <div className="qa-answer">{item.answer}</div>
                  </div>
                ))
              )}
            </div>
            <form
              className="qa-form"
              onSubmit={(event) => {
                event.preventDefault();
                void handleAsk();
              }}
            >
              <input
                className="qa-input"
                type="text"
                placeholder="Đặt câu hỏi về bài báo..."
                value={questionInput}
                onChange={(event) => setQuestionInput(event.target.value)}
                disabled={isAsking}
              />
              <button className="button" type="submit" disabled={isAsking || !questionInput.trim()}>
                <Send size={17} />
                {isAsking ? "Đang hỏi..." : "Gửi"}
              </button>
            </form>
          </div>
        ) : null}

        {error ? <div className="error">{error}</div> : null}

        {isLoading ? (
          <div className="reader">
            <span className="skeleton skeleton-title" />
            <span className="skeleton skeleton-line" />
            <span className="skeleton skeleton-line" />
            <span className="skeleton skeleton-line short" />
          </div>
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
                      <div className="section-heading-meta">
                        <span className="meta">{section.section_type}</span>
                        {!section.summary_vi ? (
                          <button
                            className="button secondary button-sm"
                            type="button"
                            onClick={() => void handleRetrySection(section.id)}
                            disabled={paper.status === "analyzing"}
                          >
                            <RotateCw size={14} />
                            Thử lại
                          </button>
                        ) : null}
                      </div>
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
