const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...options?.headers },
  });
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`);
  return res.json();
}

export const api = {
  overview: () => apiFetch<Overview>("/api/dashboard/overview"),
  history: (limit = 50) => apiFetch<PostedImage[]>(`/api/dashboard/history?limit=${limit}`),
  logs: (limit = 100) => apiFetch<PlatformLog[]>(`/api/dashboard/logs?limit=${limit}`),
  platforms: () => apiFetch<PlatformStatus>("/api/dashboard/platforms"),
  settings: () => apiFetch<AppSettings>("/api/dashboard/settings"),
  pause: () => apiFetch<{ status: string }>("/api/dashboard/pause", { method: "POST" }),
  resume: () => apiFetch<{ status: string }>("/api/dashboard/resume", { method: "POST" }),
  trigger: () => apiFetch<{ status: string; message: string }>("/api/dashboard/trigger", { method: "POST" }),
  triggerBulk: () => apiFetch<{ status: string; message: string }>("/api/dashboard/trigger-bulk", { method: "POST" }),
  triggerLatest: () => apiFetch<{ status: string; message: string }>("/api/dashboard/trigger-latest", { method: "POST" }),
};

// ── Types ────────────────────────────────────────────────────────────────────

export interface Overview {
  total_posted: number;
  posted_today: number;
  automation_paused: boolean;
  last_run_at: string;
  next_run_at: string;
  schedule: string;
  max_posts_per_day: number;
}

export interface PostedImage {
  id: number;
  drive_file_id: string;
  file_name: string;
  folder_path: string;
  posted_at: string;
  instagram: number;
  facebook: number;
  caption_used: string;
  cloudinary_url: string;
}

export interface PlatformLog {
  id: number;
  drive_file_id: string;
  platform: string;
  status: string;
  response: string;
  attempt: number;
  logged_at: string;
}

export interface PlatformStatus {
  instagram: boolean;
  facebook: boolean;
  google_drive: boolean;
  openai: boolean;
  server_url: boolean;
}

export interface AppSettings {
  schedule_hour: number;
  schedule_minute: number;
  post_interval_minutes: number;
  max_posts_per_day: number;
  openai_model: string;
}
