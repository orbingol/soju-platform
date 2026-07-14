/** Minimal typing for Document Picture-in-Picture (Chromium + newer Firefox). */
export interface DocumentPictureInPictureOptions {
  width?: number;
  height?: number;
  disallowReturnToOpener?: boolean;
  preferInitialWindowPlacement?: boolean;
}

export interface DocumentPictureInPicture {
  readonly window: Window | null;
  requestWindow(options?: DocumentPictureInPictureOptions): Promise<Window>;
}

declare global {
  interface Window {
    documentPictureInPicture?: DocumentPictureInPicture;
  }
}

export function supportsDocumentPictureInPicture(): boolean {
  return typeof window !== 'undefined' && 'documentPictureInPicture' in window;
}

/** Copy stylesheets and theme attrs so the pop-out window matches the app. */
export function copyDocumentChrome(target: Window): void {
  const { document: doc } = target;
  doc.head.replaceChildren();
  doc.documentElement.className = document.documentElement.className;
  const theme = document.documentElement.getAttribute('data-theme');
  if (theme) {
    doc.documentElement.setAttribute('data-theme', theme);
  } else {
    doc.documentElement.removeAttribute('data-theme');
  }

  for (const node of document.querySelectorAll('link[rel="stylesheet"], style')) {
    doc.head.appendChild(node.cloneNode(true));
  }

  // Constructable stylesheets (Vite HMR / some browsers).
  try {
    if (document.adoptedStyleSheets?.length) {
      doc.adoptedStyleSheets = [...document.adoptedStyleSheets];
    }
  } catch {
    // Ignore if the target document rejects adopted sheets.
  }
}

export interface OpenChatPopoutOptions {
  width?: number;
  height?: number;
  title?: string;
}

/**
 * Open a floating chat window: Document PiP when available, otherwise a popup.
 * Returns null if the browser blocked the popup.
 */
export async function openChatPopoutWindow(options: OpenChatPopoutOptions = {}): Promise<Window | null> {
  const width = options.width ?? 400;
  const height = options.height ?? 560;
  const title = options.title ?? 'Chat';

  let win: Window | null = null;

  if (supportsDocumentPictureInPicture() && window.documentPictureInPicture) {
    try {
      win = await window.documentPictureInPicture.requestWindow({ width, height });
    } catch {
      win = null;
    }
  }

  if (!win) {
    win = window.open('', 'soju-chat-popout', `popup=yes,width=${width},height=${height},noopener=no`);
  }

  if (!win) return null;

  copyDocumentChrome(win);
  win.document.title = title;
  win.document.body.className = 'chat-popout-body';
  win.document.body.replaceChildren();
  return win;
}
