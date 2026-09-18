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

const API_BASE_URL = (
  (import.meta.env as Record<string, string | undefined>)["VITE_API_BASE_URL"] || "/api/v1"
).replace(/\/$/, "");

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

// In-memory cache for high-speed client routing (0ms latency on navigation)
const apiCache = new Map<string, { data: unknown; timestamp: number }>();
const pendingGets = new Map<string, Promise<unknown>>();
const CACHE_TTL_MS = 15000; // 15 seconds fresh TTL

export function clearApiCache(pathPrefix?: string) {
  if (!pathPrefix) {
    apiCache.clear();
    return;
  }
  for (const key of apiCache.keys()) {
    if (key.startsWith(pathPrefix)) {
      apiCache.delete(key);
    }
  }
}

export async function apiFetch<T>(
  path: string,
  options?: RequestInit & { bypassCache?: boolean }
): Promise<T> {
  const method = (options?.method || "GET").toUpperCase();
  const token = localStorage.getItem("access_token");
  const headers = new Headers(options?.headers);
  headers.set("Accept", "application/json");

  if (options?.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (token) {
    headers.set("Authorization", "Bearer " + token);
  }

  const isGet = method === "GET";
  const cacheKey = `${path}?${token || ""}`;

  // If GET and cache exists and is fresh and not bypassed, return instantly
  if (isGet && !options?.bypassCache) {
    const cached = apiCache.get(cacheKey);
    if (cached && Date.now() - cached.timestamp < CACHE_TTL_MS) {
      // Return cached copy immediately (0ms)
      // Background revalidate if older than 3 seconds
      if (Date.now() - cached.timestamp > 3000) {
        fetch(`${API_BASE_URL}${path}`, { ...options, headers })
          .then((res) => (res.ok ? res.json() : null))
          .then((newData) => {
            if (newData) {
              apiCache.set(cacheKey, { data: newData, timestamp: Date.now() });
            }
          })
          .catch(() => {});
      }
      return cached.data as T;
    }
    const pending = pendingGets.get(cacheKey);
    if (pending) return pending as Promise<T>;
  }

  // Mutating requests invalidate cache
  if (!isGet) {
    clearApiCache();
  }

  const request = (async () => {
    const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });
    const body = await response.json().catch(() => null);

    if (!response.ok) {
      if (response.status === 401) {
        window.dispatchEvent(new Event("proteus:auth-expired"));
      }
      const message =
        body && typeof body.error === "string" ? body.error : `Request failed (${response.status})`;
      throw new ApiError(message, response.status);
    }

    if (isGet) {
      apiCache.set(cacheKey, { data: body, timestamp: Date.now() });
    }

    return body as T;
  })();

  if (isGet && !options?.bypassCache) {
    pendingGets.set(cacheKey, request);
    request.finally(() => pendingGets.delete(cacheKey)).catch(() => {});
  }

  return request;
}
