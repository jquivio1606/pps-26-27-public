/**
 * Cliente HTTP de la API de Cinema.
 *
 * Por defecto apunta al backend desplegado en Render. Se puede cambiar en
 * tiempo de compilación con la variable de entorno `VITE_API_BASE`:
 *
 *   VITE_API_BASE=https://otro-backend.com  -> ese backend
 *   VITE_API_BASE=/                         -> mismo origen (FastAPI sirve
 *                                              el frontend y la API juntos)
 */

const DEFAULT_API_BASE = "https://pps-26-27-back.onrender.com";

const configuredBase = import.meta.env.VITE_API_BASE;
const API_BASE = (configuredBase === undefined ? DEFAULT_API_BASE : configuredBase).replace(
  /\/+$/,
  ""
);

/** URL absoluta de un recurso de la API (para enlaces y redirecciones). */
export function apiUrl(path = "") {
  return API_BASE + path;
}

export class ApiError extends Error {
  constructor(status, detail) {
    super(detail);
    this.name = "ApiError";
    this.status = status;
  }
}

let authToken = null;
let onUnauthorized = null;

/** Token Bearer que se añadirá a las peticiones. */
export function setAuthToken(token) {
  authToken = token || null;
}

/** Callback que se invoca cuando la API responde 401 (token caducado). */
export function setUnauthorizedHandler(handler) {
  onUnauthorized = handler;
}

function extractMessage(data, status) {
  if (data && typeof data === "object" && data.detail) {
    if (Array.isArray(data.detail)) return data.detail.map((e) => e.msg).join(" · ");
    if (typeof data.detail === "string") return data.detail;
  }
  return `Error ${status}`;
}

export async function api(path, { method = "GET", body, form = false } = {}) {
  const headers = {};
  if (authToken) headers.Authorization = `Bearer ${authToken}`;

  let payload;
  if (form) {
    headers["Content-Type"] = "application/x-www-form-urlencoded";
    payload = new URLSearchParams(body).toString();
  } else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }

  let res;
  try {
    res = await fetch(API_BASE + path, { method, headers, body: payload });
  } catch {
    throw new ApiError(0, "No se pudo conectar con la API. ¿Está el servidor arrancado?");
  }

  const text = await res.text();
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = text;
  }

  if (!res.ok) {
    if (res.status === 401 && authToken && onUnauthorized) onUnauthorized();
    throw new ApiError(res.status, extractMessage(data, res.status));
  }
  return data;
}
