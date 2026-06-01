/**
 * First-party, privacy-light analytics.
 *
 * Sends anonymous funnel events to our own backend (same-origin via the
 * Vercel /api proxy) instead of a third-party script — fast and reachable
 * from mainland China. No PII: a random anon id + event name + path + an
 * optional channel tag (?ref=xhs) captured on first visit.
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1';
const ANON_KEY = 'tc_anon_id';
const REF_KEY = 'tc_ref';

function getAnonId(): string {
  try {
    let id = localStorage.getItem(ANON_KEY);
    if (!id) {
      id =
        (crypto as Crypto)?.randomUUID?.() ??
        `a_${Date.now().toString(36)}${Math.floor(Math.random() * 1e9).toString(36)}`;
      localStorage.setItem(ANON_KEY, id);
    }
    return id;
  } catch {
    return 'anon';
  }
}

/** Capture ?ref= on first landing and remember it for later events. */
function getRef(): string {
  try {
    const fromUrl = new URLSearchParams(window.location.search).get('ref');
    if (fromUrl) {
      localStorage.setItem(REF_KEY, fromUrl.slice(0, 40));
      return fromUrl.slice(0, 40);
    }
    return localStorage.getItem(REF_KEY) || '';
  } catch {
    return '';
  }
}

export function track(name: string, extra?: { path?: string }): void {
  try {
    const body = JSON.stringify({
      name,
      anon_id: getAnonId(),
      path: extra?.path ?? window.location.pathname,
      ref: getRef(),
    });
    // fire-and-forget; never block or throw into the UI
    fetch(`${API_BASE}/analytics/event`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body,
      keepalive: true,
    }).catch(() => {});
  } catch {
    /* no-op */
  }
}
