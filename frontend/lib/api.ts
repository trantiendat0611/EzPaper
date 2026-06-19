import { clearToken, getToken, setToken } from "@/lib/auth";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export type User = {
  id: number;
  email: string;
  full_name: string | null;
  is_active: boolean;
  created_at: string;
};

export type Paper = {
  id: number;
  title: string;
  original_filename: string;
  status: string;
  abstract: string | null;
  created_at: string;
  updated_at: string;
};

export type PaperSection = {
  id: number;
  title: string;
  section_type: string;
  order_index: number;
  raw_text: string;
  summary_vi: string | null;
  explanation_vi: string | null;
  created_at: string;
  updated_at: string;
};

export type PaperDetail = Paper & {
  sections: PaperSection[];
};

type RequestOptions = RequestInit & {
  auth?: boolean;
};

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers = new Headers(options.headers);
  const token = getToken();

  if (options.auth !== false && token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  if (options.body && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    clearToken();
  }

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}));
    throw new Error(errorBody.detail ?? "Request failed");
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export async function registerUser(payload: {
  email: string;
  password: string;
  full_name?: string;
}): Promise<User> {
  return request<User>("/auth/register", {
    method: "POST",
    auth: false,
    body: JSON.stringify(payload),
  });
}

export async function loginUser(email: string, password: string): Promise<void> {
  const token = await request<{ access_token: string }>("/auth/login", {
    method: "POST",
    auth: false,
    body: JSON.stringify({ email, password }),
  });
  setToken(token.access_token);
}

export async function getCurrentUser(): Promise<User> {
  return request<User>("/auth/me");
}

export async function listPapers(): Promise<Paper[]> {
  const data = await request<{ items: Paper[] }>("/papers");
  return data.items;
}

export async function uploadPaper(file: File): Promise<Paper> {
  const formData = new FormData();
  formData.append("file", file);
  return request<Paper>("/papers/upload", {
    method: "POST",
    body: formData,
  });
}

export async function getPaper(id: string): Promise<PaperDetail> {
  return request<PaperDetail>(`/papers/${id}`);
}

export async function analyzePaper(id: number): Promise<PaperDetail> {
  return request<PaperDetail>(`/papers/${id}/analyze`, {
    method: "POST",
  });
}

export async function deletePaper(id: number): Promise<void> {
  return request<void>(`/papers/${id}`, {
    method: "DELETE",
  });
}
