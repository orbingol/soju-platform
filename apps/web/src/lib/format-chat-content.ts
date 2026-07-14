/** Escape HTML so chat content can be safely rendered with {@html}. */
function escapeHtml(text: string): string {
  return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

/** Normalize common LaTeX / markdown arrows models emit. */
function normalizeArrows(text: string): string {
  return text
    .replace(/\$\s*\\rightarrow\s*\$/gi, '→')
    .replace(/\$\s*\\Rightarrow\s*\$/gi, '⇒')
    .replace(/\$\s*\\to\s*\$/gi, '→')
    .replace(/\\rightarrow/gi, '→')
    .replace(/\\Rightarrow/gi, '⇒')
    .replace(/\\to\b/gi, '→');
}

/** Inline markdown: **bold** and *italic* (after HTML escape). */
function formatInline(text: string): string {
  let html = escapeHtml(text);
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/(?<!\*)\*(?!\*)([^*\n]+?)(?<!\*)\*(?!\*)/g, '<em>$1</em>');
  return html;
}

/**
 * Render assistant chat text as safe HTML.
 * Supports bold, italic, simple bullets, horizontal rules, and arrow symbols.
 */
export function formatChatContent(content: string): string {
  if (!content) return '';

  const lines = normalizeArrows(content).split('\n');
  const parts: string[] = [];
  let inList = false;

  const closeList = () => {
    if (inList) {
      parts.push('</ul>');
      inList = false;
    }
  };

  for (const line of lines) {
    const trimmed = line.trim();

    if (/^---+$/.test(trimmed)) {
      closeList();
      parts.push('<hr class="chat-bubble__rule" />');
      continue;
    }

    const bullet = trimmed.match(/^([*-])\s+(.+)$/);
    if (bullet) {
      if (!inList) {
        parts.push('<ul class="chat-bubble__list">');
        inList = true;
      }
      parts.push(`<li>${formatInline(bullet[2])}</li>`);
      continue;
    }

    closeList();

    if (trimmed === '') {
      parts.push('<div class="chat-bubble__break"></div>');
      continue;
    }

    parts.push(`<p class="chat-bubble__p">${formatInline(line)}</p>`);
  }

  closeList();
  return parts.join('');
}
