import { authStore } from "$lib/stores/auth";

const API_BASE_URL =
  import.meta.env.VITE_API_URL || "/api/v1";

export { API_BASE_URL };


export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function toHeadersRecord(headers?: HeadersInit): Record<string, string> {
  if (!headers) {
    return {};
  }

  if (headers instanceof Headers) {
    return Object.fromEntries(headers.entries());
  }

  if (Array.isArray(headers)) {
    return Object.fromEntries(headers);
  }

  return { ...headers };
}

function clearAuthOnUnauthorized(status: number): void {
  if (status === 401) {
    authStore.clearToken();
  }
}

async function buildErrorMessage(response: Response): Promise<string> {
  const fallback = response.statusText || "Request failed";
  try {
    const error = await response.clone().json();
    return error.detail || error.message || fallback;
  } catch {
    try {
      const errorText = await response.text();
      return errorText || fallback;
    } catch {
      return fallback;
    }
  }
}

async function requestInternal<T>(
  endpoint: string,
  options: RequestInit = {},
  responseType: "json" | "blob" = "json",
): Promise<T> {
  const fetchOptions = { ...options };
  const credentials = fetchOptions.credentials || "include";
  const headers = toHeadersRecord(fetchOptions.headers);

  const hasBody = fetchOptions.body !== undefined && fetchOptions.body !== null;
  const isFormDataBody = typeof FormData !== "undefined" && fetchOptions.body instanceof FormData;
  if (hasBody && !isFormDataBody && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  const requestUrl = endpoint.startsWith("http")
    ? endpoint
    : `${API_BASE_URL}${endpoint}`;

  const response = await fetch(requestUrl, {
    ...fetchOptions,
    credentials,
    headers,
  });

  if (!response.ok) {
    clearAuthOnUnauthorized(response.status);
    const message = await buildErrorMessage(response);
    throw new ApiError(
      response.status,
      message,
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  if (responseType === "blob") {
    return response.blob() as Promise<T>;
  }

  return response.json() as Promise<T>;
}

export async function request<T>(
  endpoint: string,
  options?: RequestInit,
): Promise<T> {
  return requestInternal<T>(endpoint, options, "json");
}

export async function requestFormData<T>(
  endpoint: string,
  formData: FormData,
  options?: Omit<RequestInit, "body" | "method">,
): Promise<T> {
  return requestInternal<T>(endpoint, {
    ...options,
    method: "POST",
    body: formData,
  });
}

export async function requestBlob(
  endpoint: string,
  options?: RequestInit,
): Promise<Blob> {
  return requestInternal<Blob>(endpoint, options, "blob");
}
