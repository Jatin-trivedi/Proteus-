export type Agent = {
  agent_id: string;
  hostname: string | null;
  os: string;
  ip: string;
  arch: string;
  status: string;
  last_seen: string | null;
};

export type Script = {
  script_id: string;
  name: string;
  code: string;
  hash_before: string | null;
  hash_after: string | null;
  created_at: string;
};

export type Deployment = {
  deploy_id: string;
  script_id: string;
  agent_id: string;
  status: string;
  deployed_at: string;
  executed_at: string | null;
  result_id: string | null;
  script_name: string | null;
  hostname: string | null;
};

export type Result = {
  result_id: string;
  agent_id: string;
  script_id: string;
  submitted_at: string;
  data_encrypted: string;
};

const API_BASE_URL = ((import.meta.env as Record<string, string | undefined>)["VITE_API_BASE_URL"] || "/api/v1").replace(/\/$/, "");

export async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const token = localStorage.getItem("access_token");
  const headers = new Headers(options?.headers);
  headers.set("Accept", "application/json");
  if (options?.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    const message = body && typeof body.error === "string" ? body.error : `Request failed (${response.status})`;
    throw new Error(message);
  }
  return body as T;
}
