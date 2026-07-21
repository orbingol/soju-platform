// With adapter-static `fallback`, pages are only written to disk when prerenderable.
// Root `/` and `/education/` had no +page.server.ts `prerender = true`, so GitHub Pages
// served 404.html for those URLs. Inherit true for all routes (API routes set false).
export const prerender = true;

// GitHub Pages serves project roots as /<repo>/ (trailing slash). Default 'never'
// 404s on first load while in-app links (…/) still work.
export const trailingSlash = 'always';
