"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { UserPlus } from "lucide-react";
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
        <h1 className="brand">EzPaper</h1>
        <p className="page-subtitle">Create your reader workspace</p>
        <form className="form" onSubmit={handleSubmit}>
          {error ? <div className="error">{error}</div> : null}
          <div className="field">
            <label htmlFor="fullName">Full name</label>
            <input id="fullName" value={fullName} onChange={(event) => setFullName(event.target.value)} />
          </div>
          <div className="field">
            <label htmlFor="email">Email</label>
            <input id="email" type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
          </div>
          <div className="field">
            <label htmlFor="password">Password</label>
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
            Create account
          </button>
          <p className="meta">
            Already have an account? <Link className="text-link" href="/login">Sign in</Link>
          </p>
        </form>
      </section>
      <section className="auth-visual">
        <div className="auth-copy">
          <h2 className="page-title">EzPaper</h2>
          <p className="page-subtitle">
            Build a personal library of papers with structured sections and Vietnamese reading notes.
          </p>
        </div>
      </section>
    </main>
  );
}
