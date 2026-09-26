import assert from "node:assert/strict";
import test from "node:test";
import worker from "./worker.js";

test("validates relay auth and strips the shared secret before manager forwarding", async () => {
  let forwardedRequest;
  const env = {
    C2_AUTH: "relay-test-secret",
    BACKEND_URL: "https://manager.example",
    RELAY_MTLS: {
      fetch: async (resource, init) => {
        forwardedRequest = { resource, init };
        return new Response("manager response");
      },
    },
  };

  const response = await worker.fetch(
    new Request("https://relay.example/api/v1/status", {
      headers: {
        "X-C2-Auth": "relay-test-secret",
        Authorization: "Bearer user-token",
      },
    }),
    env,
  );

  assert.equal(response.status, 200);
  assert.equal(forwardedRequest.resource, "https://manager.example/api/v1/status");
  assert.equal(forwardedRequest.init.headers.get("X-C2-Auth"), null);
  assert.equal(
    forwardedRequest.init.headers.get("Authorization"),
    "Bearer user-token",
  );
});

test("rejects invalid relay auth without forwarding the request", async () => {
  let forwarded = false;
  const env = {
    C2_AUTH: "relay-test-secret",
    BACKEND_URL: "https://manager.example",
    RELAY_MTLS: {
      fetch: async () => {
        forwarded = true;
        return new Response("unexpected");
      },
    },
  };

  const response = await worker.fetch(
    new Request("https://relay.example/api/v1/status", {
      headers: { "X-C2-Auth": "wrong-secret" },
    }),
    env,
  );

  assert.equal(response.status, 302);
  assert.equal(forwarded, false);
});
