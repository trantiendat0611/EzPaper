"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { BookOpenText, FolderHeart, Sparkles, UserPlus } from "lucide-react";
import { loginUser, registerUser } from "@/lib/api";

export default function RegisterPage() {
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setIsSubmitting(true);

    try {
      await registerUser({ email, password, full_name: fullName || undefined });
      await loginUser(email, password);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
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
        <p className="page-subtitle">Tạo không gian đọc báo khoa học của riêng bạn.</p>
        <form className="form" onSubmit={handleSubmit}>
          {error ? <div className="error">{error}</div> : null}
          <div className="field">
            <label htmlFor="fullName">Họ và tên</label>
            <input id="fullName" value={fullName} onChange={(event) => setFullName(event.target.value)} />
          </div>
          <div className="field">
            <label htmlFor="email">Email</label>
            <input id="email" type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
          </div>
          <div className="field">
            <label htmlFor="password">Mật khẩu</label>
            <input
              id="password"
              type="password"
              minLength={8}
              maxLength={72}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
          </div>
          <button className="button" type="submit" disabled={isSubmitting}>
            <UserPlus size={18} />
            {isSubmitting ? "Đang tạo tài khoản..." : "Tạo tài khoản"}
          </button>
          <p className="meta">
            Đã có tài khoản? <Link className="text-link" href="/login">Đăng nhập</Link>
          </p>
        </form>
      </section>
      <section className="auth-visual">
        <div className="auth-copy">
          <h2 className="page-title">Xây thư viện bài báo của riêng bạn</h2>
          <p className="page-subtitle">
            Lưu trữ bài báo, tự động tách phần nội dung và ghi chú giải thích tiếng Việt cho từng phần.
          </p>
          <div className="auth-feature-list">
            <div className="auth-feature">
              <span className="auth-feature-icon">
                <Sparkles size={18} />
              </span>
              <span className="auth-feature-text">Phân tích bằng AI, dễ hiểu cho người mới</span>
            </div>
            <div className="auth-feature">
              <span className="auth-feature-icon">
                <FolderHeart size={18} />
              </span>
              <span className="auth-feature-text">Thư viện cá nhân, sắp xếp gọn gàng</span>
            </div>
            <div className="auth-feature">
              <span className="auth-feature-icon">
                <BookOpenText size={18} />
              </span>
              <span className="auth-feature-text">Đọc theo từng phần: tóm tắt, giải thích, nguyên văn</span>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
