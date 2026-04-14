/**
 * Base API client for Imporsan Prospect backend.
 * Vite proxies /api/* → http://localhost:5001/api during development.
 */

const PROSPECT_API_BASE = "/api";

/**
 * Thin fetch wrapper that throws a structured error on API or network failures.
 *
 * @param {string} path     - e.g. "/analysis/upload"
 * @param {RequestInit} init
 * @returns {Promise<any>}  - parsed JSON body
 */
export async function prospectApiFetch(path, init = {}) {
  let response;
  try {
    response = await fetch(`${PROSPECT_API_BASE}${path}`, init);
  } catch {
    throw new Error(
      "No se pudo conectar con el servidor de análisis. Verifica que el backend esté corriendo."
    );
  }

  const json = await response.json().catch(() => null);

  if (!response.ok || (json && json.success === false)) {
    throw new Error(json?.error || `Error del servidor (HTTP ${response.status})`);
  }

  return json;
}
