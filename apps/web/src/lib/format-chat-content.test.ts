import { describe, expect, it } from 'vitest';

import { formatChatContent } from './format-chat-content';

describe('formatChatContent', () => {
  it('returns empty string for empty content', () => {
    expect(formatChatContent('')).toBe('');
  });

  it('escapes HTML', () => {
    expect(formatChatContent('<script>alert(1)</script>')).toBe('<p class="chat-bubble__p">&lt;script&gt;alert(1)&lt;/script&gt;</p>');
  });

  it('renders bold and italic', () => {
    expect(formatChatContent('Use **-(으)ㄹ 거예요** for plans.')).toContain('<strong>-(으)ㄹ 거예요</strong>');
    expect(formatChatContent('Say *annyeong*.')).toContain('<em>annyeong</em>');
  });

  it('renders bullet lists and rules', () => {
    const html = formatChatContent('Cases:\n* **읽다** to read\n* **마시다** to drink\n---\nDone.');
    expect(html).toContain('<ul class="chat-bubble__list">');
    expect(html).toContain('<li><strong>읽다</strong> to read</li>');
    expect(html).toContain('<hr class="chat-bubble__rule" />');
    expect(html).toContain('Done.');
  });

  it('turns LaTeX arrows into unicode', () => {
    expect(formatChatContent('읽다 $\\rightarrow$ 읽을 거예요')).toContain('→');
    expect(formatChatContent('가다 $ \\to $ 갈 거예요')).toContain('→');
  });
});
