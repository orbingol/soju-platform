import { describe, expect, it } from 'vitest';

import { sanitizeHtml } from './sanitize-html';

describe('sanitizeHtml', () => {
  it('returns empty for empty input', () => {
    expect(sanitizeHtml('')).toBe('');
  });

  it('keeps allowlisted markup used in topic descriptions', () => {
    const html =
      '<p>Use <strong>위</strong> and <em>에</em>. <br> Also <b>bold</b> <i>italic</i>.</p>';
    expect(sanitizeHtml(html)).toBe(
      '<p>Use <strong>위</strong> and <em>에</em>. <br> Also <b>bold</b> <i>italic</i>.</p>',
    );
  });

  it('allows safe http(s) and hash hrefs on anchors', () => {
    expect(sanitizeHtml('<a href="https://example.com/x">link</a>')).toBe(
      '<a href="https://example.com/x">link</a>',
    );
    expect(sanitizeHtml('<a href="http://example.com">link</a>')).toBe(
      '<a href="http://example.com">link</a>',
    );
    expect(sanitizeHtml('<a href="#section">jump</a>')).toBe('<a href="#section">jump</a>');
  });

  it('strips unsafe hrefs and non-href attributes', () => {
    expect(sanitizeHtml('<a href="javascript:alert(1)">x</a>')).toBe('<a>x</a>');
    expect(sanitizeHtml('<a href="https://ok.test" onclick="evil()" class="x">x</a>')).toBe(
      '<a href="https://ok.test">x</a>',
    );
  });

  it('strips scripts, event handlers, and style', () => {
    expect(sanitizeHtml('<p onclick="x">hi</p>')).toBe('<p>hi</p>');
    expect(sanitizeHtml('<script>alert(1)</script><p>ok</p>')).toBe('<p>ok</p>');
    expect(sanitizeHtml('<style>.x{color:red}</style><p>ok</p>')).toBe('<p>ok</p>');
    expect(sanitizeHtml('<span style="color:red">x</span>')).toBe('<span>x</span>');
  });

  it('unwraps unknown tags and escapes raw text', () => {
    expect(sanitizeHtml('<div><p>nested</p></div>')).toBe('<p>nested</p>');
    expect(sanitizeHtml('<p>a < b</p>')).toBe('<p>a &lt; b</p>');
  });

  it('keeps lists', () => {
    expect(sanitizeHtml('<ul><li>one</li><li>two</li></ul>')).toBe(
      '<ul><li>one</li><li>two</li></ul>',
    );
    expect(sanitizeHtml('<ol><li>one</li></ol>')).toBe('<ol><li>one</li></ol>');
  });
});
