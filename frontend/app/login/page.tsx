"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { BookOpenText, Languages, LogIn, Sparkles } from "lucide-react";
import { loginUser } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setIsSubmitting(true);

    try {
      await loginUser(email, password);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="auth-shell">
      <section className="auth-panel">
        <h1 className="brand">
          <span className="brand-mark">
            <BookOpenText size={18} />
          </span>
          EzPaper
        </h1>
        <p className="page-subtitle">Chào mừng trở lại không gian đọc báo khoa học của bạn.</p>
        <form className="form" onSubmit={handleSubmit}>
          {error ? <div className="error">{error}</div> : null}
          <div className="field">
            <label htmlFor="email">Email</label>
            <input id="email" type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
          </div>
          <div className="field">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
          </div>
          <button className="button" type="submit" disabled={isSubmitting}>
            <LogIn size={18} />
            {isSubmitting ? "Đang đăng nhập..." : "Đăng nhập"}
          </button>
          <p className="meta">
            Chưa có tài khoản? <Link className="text-link" href="/register">Tạo tài khoản</Link>
          </p>
        </form>
      </section>
      <section className="auth-visual">
        <div className="auth-copy">
          <h2 className="page-title">Hiểu bài báo khoa học chưa bao giờ dễ đến vậy</h2>
          <p className="page-subtitle">
            Tải lên bài báo PDF, EzPaper tự động trích xuất từng phần và giải thích lại bằng tiếng Việt dễ hiểu.
          </p>
          <div className="auth-feature-list">
            <div className="auth-feature">
              <span className="auth-feature-icon">
                <Sparkles size={18} />
              </span>
              <span className="auth-feature-text">Tóm tắt & giải thích từng phần bằng AI</span>
            </div>
            <div className="auth-feature">
              <span className="auth-feature-icon">
                <Languages size={18} />
              </span>
              <span className="auth-feature-text">Diễn giải tiếng Việt gần gũi, dễ tiếp cận</span>
            </div>
            <div className="auth-feature">
              <span className="auth-feature-icon">
                <BookOpenText size={18} />
              </span>
              <span className="auth-feature-text">Lưu trữ và quản lý thư viện bài báo cá nhân</span>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
