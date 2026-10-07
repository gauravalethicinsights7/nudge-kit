// Tiny standalone module so client.ts (the fetch layer) and AuthContext.tsx
// (the React layer) can both read/write the JWT without importing each
// other. A registered `onUnauthorized` callback lets AuthContext react to a
// 401 from any request (expired/invalid token) without client.ts needing to
// know about React Router.

const STORAGE_KEY = "nudge.jwt";

let token: string | null = localStorage.getItem(STORAGE_KEY);
let onUnauthorized: (() => void) | null = null;

export function getToken(): string | null {
  return token;
}

export function setToken(next: string | null): void {
  token = next;
  if (next) {
    localStorage.setItem(STORAGE_KEY, next);
  } else {
    localStorage.removeItem(STORAGE_KEY);
  }
}

export function setUnauthorizedHandler(handler: () => void): void {
  onUnauthorized = handler;
}

export function notifyUnauthorized(): void {
  onUnauthorized?.();
}
