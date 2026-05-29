import { beforeEach, describe, expect, it, vi } from 'vitest';
import {
  clearWorkspaceToken,
  getWorkspaceToken,
  setWorkspaceToken,
  WORKSPACE_TOKEN_KEY,
} from './workspaceToken';

describe('workspace token storage', () => {
  const store = new Map<string, string>();

  beforeEach(() => {
    store.clear();
    Object.defineProperty(window, 'localStorage', {
      configurable: true,
      value: {
        getItem: vi.fn((key: string) => store.get(key) ?? null),
        setItem: vi.fn((key: string, value: string) => {
          store.set(key, value);
        }),
        removeItem: vi.fn((key: string) => {
          store.delete(key);
        }),
      },
    });
  });

  it('stores and clears the anonymous workspace token', () => {
    expect(getWorkspaceToken()).toBeNull();

    setWorkspaceToken('token-123');

    expect(getWorkspaceToken()).toBe('token-123');
    expect(window.localStorage.getItem(WORKSPACE_TOKEN_KEY)).toBe('token-123');

    clearWorkspaceToken();

    expect(getWorkspaceToken()).toBeNull();
  });
});
