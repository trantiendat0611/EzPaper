"use client";

import { useRouter } from "next/navigation";
import { BookOpenText, LogOut } from "lucide-react";
import { clearToken } from "@/lib/auth";

type AppHeaderProps = {
  email?: string;
};

export function AppHeader({ email }: AppHeaderProps) {
  const router = useRouter();

  function handleLogout() {
    clearToken();
    router.push("/login");
  }

  return (
    <header className="topbar">
      <a className="brand" href="/dashboard">
        <span className="brand-mark">
          <BookOpenText size={18} />
        </span>
        EzPaper
      </a>
      <div className="topbar-actions">
        {email ? <span className="user-email">{email}</span> : null}
        <button className="button secondary" type="button" onClick={handleLogout} title="Đăng xuất">
          <LogOut size={17} />
          Đăng xuất
        </button>
      </div>
    </header>
  );
}
