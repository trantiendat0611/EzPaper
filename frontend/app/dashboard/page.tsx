"use client";

import Link from "next/link";
import { ChangeEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { BrainCircuit, ChevronLeft, ChevronRight, FileCheck2, FileUp, Files, RefreshCw, Search } from "lucide-react";
import { AppHeader } from "@/components/AppHeader";
import { useToast } from "@/components/Toast";
import {
  getCurrentUser,
  getPaperStats,
  listPapers,
  Paper,
  PaperStats,
  uploadPaper,
  User,
} from "@/lib/api";
import { getToken } from "@/lib/auth";
import { formatDate, getStatusLabel, getStatusTone, isInProgressStatus } from "@/lib/format";

const PAGE_SIZE = 12;
const STATUS_OPTIONS = ["uploaded", "processing", "completed", "analyzing", "analyzed", "failed"];

export default function DashboardPage() {
  const router = useRouter();
  const { showToast } = useToast();
  const [user, setUser] = useState<User | null>(null);
  const [stats, setStats] = useState<PaperStats>({ total: 0, extracted: 0, analyzed: 0 });
  const [papers, setPapers] = useState<Paper[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);

  async function loadStats() {
    try {
      setStats(await getPaperStats());
    } catch {
      // Stats are non-critical; leave the previous values in place.
    }
  }

  async function loadPapers(silent = false) {
    if (!silent) {
      setIsLoading(true);
    }
    setError("");
    try {
      const result = await listPapers({ page, pageSize: PAGE_SIZE, search, status: statusFilter });
      setPapers(result.items);
      setTotal(result.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Không tải được danh sách bài báo");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    getCurrentUser().then(setUser).catch(() => {});
    void loadStats();
  }, [router]);

  useEffect(() => {
    if (!getToken()) {
      return;
    }
    void loadPapers();
  }, [page, search, statusFilter]);

  useEffect(() => {
    const timer = setTimeout(() => {
      setSearch(searchInput);
      setPage(1);
    }, 400);
    return () => clearTimeout(timer);
  }, [searchInput]);

  useEffect(() => {
    if (!papers.some((paper) => isInProgressStatus(paper.status))) {
      return;
    }
    const interval = setInterval(() => {
      void loadPapers(true);
      void loadStats();
    }, 3000);
    return () => clearInterval(interval);
  }, [papers]);

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    setFile(event.target.files?.[0] ?? null);
  }

  async function handleUpload() {
    if (!file) {
      return;
    }

    setIsUploading(true);
    try {
      const uploaded = await uploadPaper(file);
      setFile(null);
      showToast("Đã tải lên bài báo, đang xử lý...", "success");
      router.push(`/papers/${uploaded.id}`);
    } catch (err) {
      showToast(err instanceof Error ? err.message : "Tải lên thất bại", "error");
    } finally {
      setIsUploading(false);
    }
  }

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

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
            <button className="button secondary" type="button" onClick={() => void loadPapers()} title="Làm mới">
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
              <span className="stat-value">{stats.total}</span>
              <span className="stat-label">Bài báo</span>
            </span>
          </div>
          <div className="stat">
            <span className="stat-icon">
              <FileCheck2 size={20} />
            </span>
            <span className="stat-body">
              <span className="stat-value">{stats.extracted}</span>
              <span className="stat-label">Đã trích xuất</span>
            </span>
          </div>
          <div className="stat">
            <span className="stat-icon">
              <BrainCircuit size={20} />
            </span>
            <span className="stat-body">
              <span className="stat-value">{stats.analyzed}</span>
              <span className="stat-label">Đã phân tích</span>
            </span>
          </div>
        </div>

        <div className="filter-bar">
          <div className="search-field">
            <Search size={17} className="search-icon" />
            <input
              className="search-input"
              type="search"
              placeholder="Tìm theo tiêu đề..."
              value={searchInput}
              onChange={(event) => setSearchInput(event.target.value)}
            />
          </div>
          <select
            className="filter-select"
            value={statusFilter}
            onChange={(event) => {
              setStatusFilter(event.target.value);
              setPage(1);
            }}
          >
            <option value="">Tất cả trạng thái</option>
            {STATUS_OPTIONS.map((status) => (
              <option key={status} value={status}>
                {getStatusLabel(status)}
              </option>
            ))}
          </select>
        </div>

        {error ? <div className="error">{error}</div> : null}

        {isLoading ? (
          <div className="grid">
            {Array.from({ length: 6 }).map((_, index) => (
              <div className="paper-card skeleton-card" key={index}>
                <span className="skeleton skeleton-pill" />
                <span className="skeleton skeleton-title" />
                <span className="skeleton skeleton-line" />
                <span className="skeleton skeleton-line short" />
              </div>
            ))}
          </div>
        ) : papers.length === 0 ? (
          <div className="empty-state">
            {search || statusFilter
              ? "Không có bài báo nào khớp bộ lọc."
              : "Chưa có bài báo nào. Chọn một file PDF để bắt đầu."}
          </div>
        ) : (
          <>
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

            {totalPages > 1 ? (
              <div className="pagination">
                <button
                  className="button secondary"
                  type="button"
                  disabled={page <= 1}
                  onClick={() => setPage((current) => Math.max(1, current - 1))}
                >
                  <ChevronLeft size={17} />
                  Trước
                </button>
                <span className="pagination-info">
                  Trang {page} / {totalPages}
                </span>
                <button
                  className="button secondary"
                  type="button"
                  disabled={page >= totalPages}
                  onClick={() => setPage((current) => Math.min(totalPages, current + 1))}
                >
                  Sau
                  <ChevronRight size={17} />
                </button>
              </div>
            ) : null}
          </>
        )}
      </section>
    </main>
  );
}
