// Thin fetch wrapper around the backend REST API.
//
// Both functions throw an Error whose `.message` is the server-provided detail
// (or a network message), so callers can surface it directly to the user.

const API_BASE = ""; // same origin (frontend served by FastAPI)

async function parseError(response) {
  // FastAPI returns {"detail": "..."} for HTTPException, or a validation array
  // for 422 responses. Normalise both into a readable string.
  try {
    const body = await response.json();
    if (typeof body.detail === "string") return body.detail;
    if (Array.isArray(body.detail)) {
      return body.detail
        .map((e) => `${(e.loc || []).join(".")}: ${e.msg}`)
        .join("\n");
    }
    return JSON.stringify(body);
  } catch {
    return `${response.status} ${response.statusText}`;
  }
}

// eslint-disable-next-line no-unused-vars
async function getDefaults() {
  const response = await fetch(`${API_BASE}/api/defaults`);
  if (!response.ok) throw new Error(await parseError(response));
  return response.json();
}

// eslint-disable-next-line no-unused-vars
async function runSimulation(payload) {
  const response = await fetch(`${API_BASE}/api/run_simulation`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error(await parseError(response));
  return response.json();
}
