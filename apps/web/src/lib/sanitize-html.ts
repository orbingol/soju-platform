/** Tags allowed in curated topic-section HTML. */
const ALLOWED_TAGS = new Set(['p', 'strong', 'em', 'b', 'i', 'br', 'ul', 'ol', 'li', 'a', 'span']);

/** Void / self-closing tags in the allowlist. */
const VOID_TAGS = new Set(['br']);

/** Tags whose contents must be dropped entirely. */
const DROP_WITH_CONTENT = new Set(['script', 'style', 'iframe', 'object', 'embed', 'noscript']);

function escapeText(text: string): string {
  return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function isSafeHref(href: string): boolean {
  const value = href.trim();
  if (!value) return false;
  if (value.startsWith('#')) return true;
  try {
    const url = new URL(value);
    return url.protocol === 'http:' || url.protocol === 'https:';
  } catch {
    return false;
  }
}

/** Keep only a safe `href` on `<a>`; drop all other attributes. */
function sanitizeOpenTag(tag: string, rawAttrs: string): string {
  if (tag === 'br') return '<br>';
  if (tag !== 'a') return `<${tag}>`;

  const match = rawAttrs.match(/\bhref\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+))/i);
  const href = match?.[1] ?? match?.[2] ?? match?.[3] ?? '';
  if (!isSafeHref(href)) return '<a>';
  return `<a href="${escapeText(href)}">`;
}

/**
 * Allowlist-sanitize HTML for `{@html}` (topic section descriptions).
 * No DOM / DOMPurify — safe in browser and Node unit tests.
 */
export function sanitizeHtml(input: string): string {
  if (!input) return '';

  let i = 0;
  let out = '';
  let dropDepth = 0;

  while (i < input.length) {
    if (input[i] !== '<') {
      const next = input.indexOf('<', i);
      const chunk = next === -1 ? input.slice(i) : input.slice(i, next);
      if (dropDepth === 0) out += escapeText(chunk);
      i = next === -1 ? input.length : next;
      continue;
    }

    // Comments
    if (input.startsWith('<!--', i)) {
      const end = input.indexOf('-->', i + 4);
      i = end === -1 ? input.length : end + 3;
      continue;
    }

    const afterLt = i + 1;
    const isClosing = input[afterLt] === '/';
    const nameStart = isClosing ? afterLt + 1 : afterLt;
    const nameMatch = input.slice(nameStart).match(/^([a-zA-Z][a-zA-Z0-9]*)/);

    // Bare `<` or invalid tag → treat as text
    if (!nameMatch) {
      if (dropDepth === 0) out += '&lt;';
      i = afterLt;
      continue;
    }

    const tag = nameMatch[1].toLowerCase();
    const afterName = nameStart + nameMatch[1].length;
    const close = input.indexOf('>', afterName);
    if (close === -1) {
      if (dropDepth === 0) out += '&lt;';
      i = afterLt;
      continue;
    }

    const rawAttrs = input.slice(afterName, close);
    const selfClosing = !isClosing && (rawAttrs.trimEnd().endsWith('/') || VOID_TAGS.has(tag));
    i = close + 1;

    if (DROP_WITH_CONTENT.has(tag)) {
      if (isClosing) {
        if (dropDepth > 0) dropDepth -= 1;
      } else if (!selfClosing) {
        dropDepth += 1;
      }
      continue;
    }

    if (dropDepth > 0) continue;

    if (!ALLOWED_TAGS.has(tag)) {
      continue;
    }

    if (isClosing) {
      if (!VOID_TAGS.has(tag)) out += `</${tag}>`;
      continue;
    }

    out += sanitizeOpenTag(tag, rawAttrs);
    if (selfClosing && !VOID_TAGS.has(tag)) {
      out += `</${tag}>`;
    }
  }

  return out;
}
