import { json } from '@sveltejs/kit';

import { dev } from '$app/environment';

function isLoopbackAddress(address: string): boolean {
  const host = address
    .trim()
    .toLowerCase()
    .replace(/^\[|\]$/g, '');
  return host === '127.0.0.1' || host === '::1' || host === 'localhost' || host === '::ffff:127.0.0.1' || host.startsWith('127.');
}

/** True when the browser is talking to a localhost-bound Vite/dev server (incl. Docker publish). */
function isLocalhostHostHeader(request: Request): boolean {
  const host = (request.headers.get('host') ?? '').split(',')[0]?.trim().toLowerCase() ?? '';
  const hostname = host.replace(/^\[|\]$/g, '').split(':')[0] ?? '';
  return hostname === 'localhost' || hostname === '127.0.0.1' || hostname === '::1';
}

/**
 * Guard for dev-only, localhost-only API endpoints.
 *
 * The web app is a static build (`@sveltejs/adapter-static`); `+server.ts` routes only run
 * under `vite dev`, never in production. Callers must still set `export const prerender = false`
 * and check this guard first thing so a static build never bakes a fallback response in.
 *
 * Returns a 403 JSON `Response` when the check fails, else `null` (caller should proceed).
 */
export function devLocalOnlyGuard(request: Request, getClientAddress: () => string, label: string): Response | null {
  if (!dev) {
    return json({ error: `${label} is dev-only` }, { status: 403 });
  }

  let clientAddress = '';
  try {
    clientAddress = getClientAddress();
  } catch {
    clientAddress = '';
  }

  if (!isLoopbackAddress(clientAddress) && !isLocalhostHostHeader(request)) {
    return json({ error: `${label} is localhost-only` }, { status: 403 });
  }

  return null;
}
