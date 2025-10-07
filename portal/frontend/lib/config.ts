// portal/frontend/lib/config.ts
"use client";

// Use the Railway deployment URL from environment variable
export const API_BASE = (
  process.env.NEXT_PUBLIC_API_URL || 
  process.env.NEXT_PUBLIC_API_BASE || 
  "http://localhost:8080"
).replace(/\/+$/, "");

// Helper to build LinkedIn login URL with redirect back to current page
export const linkedInLoginUrl = (includeOrg = true, currentUrl?: string) => {
  const params = new URLSearchParams();
  if (includeOrg) params.set("include_org", "true");
  if (currentUrl) params.set("redirect", currentUrl);
  
  const queryString = params.toString();
  return `${API_BASE}/auth/linkedin/login${queryString ? `?${queryString}` : ""}`;
};

// Enhanced error type
export class ApiError extends Error {
  status: number;
  detail?: string;
  help?: string;
  
  constructor(status: number, message: string, detail?: string, help?: string) {
    super(message);
    this.status = status;
    this.detail = detail;
    this.help = help;
    this.name = "ApiError";
  }
}

// Parse error response
async function parseErrorResponse(res: Response, path: string, method: string): Promise<ApiError> {
  let errorData: any = {};
  
  try {
    const contentType = res.headers.get("content-type");
    if (contentType?.includes("application/json")) {
      errorData = await res.json();
    } else {
      const text = await res.text();
      errorData = { detail: text || `${method} ${path} failed: ${res.status}` };
    }
  } catch {
    errorData = { detail: `${method} ${path} failed: ${res.status}` };
  }
  
  const message = errorData.detail || errorData.error || errorData.message || `Request failed: ${res.status}`;
  return new ApiError(res.status, message, errorData.detail, errorData.help);
}

// GET request with enhanced error handling
export async function apiGet<T>(path: string, options?: RequestInit): Promise<T> {
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      credentials: "include",
      headers: { 
        "Content-Type": "application/json",
        "Accept": "application/json",
      },
      cache: "no-store",
      mode: "cors",
      ...options,
    });
    
    if (!res.ok) {
      throw await parseErrorResponse(res, path, "GET");
    }
    
    // Handle empty responses
    const contentLength = res.headers.get("content-length");
    if (contentLength === "0") {
      return {} as T;
    }
    
    return res.json();
  } catch (error) {
    if (error instanceof ApiError) throw error;
    
    // Network or other errors
    throw new ApiError(
      0, 
      `Network error: ${error instanceof Error ? error.message : "Unknown error"}`,
      `Failed to connect to API at ${API_BASE}`,
      "Check your internet connection and verify the API is running"
    );
  }
}

// POST request with enhanced error handling
export async function apiPost<T>(
  path: string, 
  body?: unknown,
  options?: RequestInit
): Promise<T> {
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      method: "POST",
      credentials: "include",
      headers: { 
        "Content-Type": "application/json",
        "Accept": "application/json",
      },
      body: body !== undefined ? JSON.stringify(body) : undefined,
      cache: "no-store",
      mode: "cors",
      ...options,
    });
    
    if (!res.ok) {
      throw await parseErrorResponse(res, path, "POST");
    }
    
    // Handle empty responses
    const contentLength = res.headers.get("content-length");
    if (contentLength === "0") {
      return {} as T;
    }
    
    return res.json();
  } catch (error) {
    if (error instanceof ApiError) throw error;
    
    // Network or other errors
    throw new ApiError(
      0,
      `Network error: ${error instanceof Error ? error.message : "Unknown error"}`,
      `Failed to connect to API at ${API_BASE}`,
      "Check your internet connection and verify the API is running"
    );
  }
}

// DELETE request
export async function apiDelete<T = void>(
  path: string,
  options?: RequestInit
): Promise<T> {
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      method: "DELETE",
      credentials: "include",
      headers: { 
        "Content-Type": "application/json",
        "Accept": "application/json",
      },
      cache: "no-store",
      mode: "cors",
      ...options,
    });
    
    if (!res.ok) {
      throw await parseErrorResponse(res, path, "DELETE");
    }
    
    // Handle empty responses
    const contentLength = res.headers.get("content-length");
    if (contentLength === "0") {
      return {} as T;
    }
    
    return res.json();
  } catch (error) {
    if (error instanceof ApiError) throw error;
    
    throw new ApiError(
      0,
      `Network error: ${error instanceof Error ? error.message : "Unknown error"}`,
      `Failed to connect to API at ${API_BASE}`,
      "Check your internet connection and verify the API is running"
    );
  }
}

// Helper to check if user is authenticated
export async function checkAuth(): Promise<boolean> {
  try {
    await apiGet("/api/me");
    return true;
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) {
      return false;
    }
    throw error;
  }
}

// Helper to handle API errors in components
export function getErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.help) {
      return `${error.message}. ${error.help}`;
    }
    return error.message;
  }
  
  if (error instanceof Error) {
    return error.message;
  }
  
  return "An unexpected error occurred";
}

// Helper to determine if an error is an auth error
export function isAuthError(error: unknown): boolean {
  return error instanceof ApiError && error.status === 401;
}

// Helper to get the current page URL for redirect
export function getCurrentUrl(): string {
  if (typeof window !== "undefined") {
    return window.location.href;
  }
  return "";
}