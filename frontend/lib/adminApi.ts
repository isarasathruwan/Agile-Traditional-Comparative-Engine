import { API_BASE_URL } from "@/lib/api";

type ApiEnvelope<T> = {
  success: boolean;
  message: string;
  data: T | null;
};

type ErrorEnvelope = {
  success?: boolean;
  message?: string;
  error_code?: string | null;
};

export class AdminApiError extends Error {
  status: number;
  errorCode: string | null;

  constructor(message: string, status: number, errorCode: string | null = null) {
    super(message);
    this.name = "AdminApiError";
    this.status = status;
    this.errorCode = errorCode;
  }
}

export function isAdminUnauthenticated(error: unknown): boolean {
  return (
    error instanceof AdminApiError
    && (error.status === 401 || error.errorCode === "AUTH_401")
  );
}

export function isAdminForbidden(error: unknown): boolean {
  return (
    error instanceof AdminApiError
    && (error.status === 403 || error.errorCode === "AUTH_403")
  );
}

async function parseEnvelope<T>(response: Response): Promise<ApiEnvelope<T>> {
  const envelope = (await response.json()) as ApiEnvelope<T> & { error_code?: string | null };
  if (!response.ok || !envelope.success) {
    throw new AdminApiError(
      envelope.message || "Request failed",
      response.status,
      envelope.error_code ?? null
    );
  }
  return envelope;
}

export async function adminGetEnvelope<TEnvelope extends { success: boolean; message: string }>(
  path: string,
  token: string
) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const envelope = (await response.json()) as TEnvelope & ErrorEnvelope;
  if (!response.ok || !envelope.success) {
    throw new AdminApiError(
      envelope.message || "Request failed",
      response.status,
      envelope.error_code ?? null
    );
  }
  return envelope;
}

export async function adminLogin(email: string, password: string) {
  const response = await fetch(`${API_BASE_URL}/api/v1/admin/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const envelope = await parseEnvelope<{ access_token: string; token_type: string }>(response);
  if (!envelope.data) {
    throw new Error("Invalid credentials");
  }
  return envelope.data;
}

export async function adminGet(path: string, token: string) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const envelope = await parseEnvelope<unknown>(response);
  return envelope.data;
}

export async function adminPut(path: string, token: string, body: unknown) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(body),
  });
  const envelope = await parseEnvelope<unknown>(response);
  return envelope.data;
}

export async function adminPost(path: string, token: string, body: unknown) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(body),
  });
  const envelope = await parseEnvelope<unknown>(response);
  return envelope.data;
}

export async function adminDelete(path: string, token: string, body?: unknown) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "DELETE",
    headers: {
      ...(body === undefined ? {} : { "Content-Type": "application/json" }),
      Authorization: `Bearer ${token}`,
    },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  });
  const envelope = await parseEnvelope<unknown>(response);
  return envelope.data;
}

export async function adminOpenFile(path: string, token: string, mode: "preview" | "download", filename?: string) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    throw new AdminApiError(
      mode === "download" ? "Document download failed." : "Document preview failed.",
      response.status
    );
  }
  const responseBlob = await response.blob();
  const blob = new Blob([responseBlob], {
    type: responseBlob.type || response.headers.get("Content-Type") || "application/octet-stream",
  });
  const objectUrl = window.URL.createObjectURL(blob);

  if (mode === "preview") {
    const anchor = document.createElement("a");
    anchor.href = objectUrl;
    anchor.target = "_blank";
    anchor.rel = "noopener noreferrer";
    anchor.click();
    window.setTimeout(() => window.URL.revokeObjectURL(objectUrl), 60_000);
    return;
  }

  const anchor = document.createElement("a");
  anchor.href = objectUrl;
  anchor.download = filename || "assessment-document";
  anchor.click();
  window.URL.revokeObjectURL(objectUrl);
}
