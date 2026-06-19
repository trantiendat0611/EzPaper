"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { LogIn } from "lucide-react";
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
        <h1 className="brand">EzPaper</h1>
        <p className="page-subtitle">Research reading workspace</p>
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
            Sign in
          </button>
          <p className="meta">
            New to EzPaper? <Link className="text-link" href="/register">Create account</Link>
          </p>
        </form>
      </section>
      <section className="auth-visual">
        <div className="auth-copy">
          <h2 className="page-title">EzPaper</h2>
          <p className="page-subtitle">
            A focused reader for uploaded scientific papers, section extraction, and Vietnamese explanations.
          </p>
        </div>
      </section>
    </main>
  );
}
