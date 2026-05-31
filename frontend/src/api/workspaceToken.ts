const WORKSPACE_TOKEN_KEY = 'tradingcoach.workspaceToken';

export function getWorkspaceToken(): string | null {
  if (typeof window === 'undefined') return null;
  return window.localStorage.getItem(WORKSPACE_TOKEN_KEY);
}

export function setWorkspaceToken(token: string): void {
  if (typeof window === 'undefined') return;
  window.localStorage.setItem(WORKSPACE_TOKEN_KEY, token);
}

export function clearWorkspaceToken(): void {
  if (typeof window === 'undefined') return;
  window.localStorage.removeItem(WORKSPACE_TOKEN_KEY);
}

export { WORKSPACE_TOKEN_KEY };
