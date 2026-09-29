import React from 'react';

/**
 * Helper function to parse inline markdown (bold, italics, code, links)
 * into clean React elements without raw markdown characters leaking.
 */
function parseInlineMarkdown(text) {
  if (!text) return '';

  // Tokenize string by markdown elements: `code`, **bold**, *italic*, [link](url)
  const tokens = [];
  let remaining = text;
  let keyIdx = 0;

  while (remaining.length > 0) {
    // 1. Check for `inline code`
    const codeMatch = remaining.match(/^`([^`]+)`/);
    if (codeMatch) {
      tokens.push(
        <code
          key={`code-${keyIdx++}`}
          className="px-1.5 py-0.5 rounded bg-cyan-950/60 border border-cyan-500/30 text-cyan-200 font-mono text-[11px]"
        >
          {codeMatch[1]}
        </code>
      );
      remaining = remaining.slice(codeMatch[0].length);
      continue;
    }

    // 2. Check for **bold**
    const boldMatch = remaining.match(/^\*\*([^*]+)\*\*/);
    if (boldMatch) {
      tokens.push(
        <strong key={`bold-${keyIdx++}`} className="font-semibold text-white">
          {boldMatch[1]}
        </strong>
      );
      remaining = remaining.slice(boldMatch[0].length);
      continue;
    }

    // 3. Check for *italic* (or _italic_)
    const italicMatch = remaining.match(/^\*([^*]+)\*/) || remaining.match(/^_([^_]+)_/);
    if (italicMatch) {
      tokens.push(
        <em key={`italic-${keyIdx++}`} className="italic text-slate-300">
          {italicMatch[1]}
        </em>
      );
      remaining = remaining.slice(italicMatch[0].length);
      continue;
    }

    // 4. Check for [label](url)
    const linkMatch = remaining.match(/^\[([^\]]+)\]\(([^)]+)\)/);
    if (linkMatch) {
      tokens.push(
        <a
          key={`link-${keyIdx++}`}
          href={linkMatch[2]}
          target="_blank"
          rel="noopener noreferrer"
          className="text-cyan-400 hover:text-cyan-300 underline underline-offset-2"
        >
          {linkMatch[1]}
        </a>
      );
      remaining = remaining.slice(linkMatch[0].length);
      continue;
    }

    // Plain text chunk up to next delimiter
    const nextSpecial = remaining.search(/[`*_[\]]/);
    if (nextSpecial === -1) {
      tokens.push(remaining);
      break;
    } else if (nextSpecial === 0) {
      // Escaped or unmatched delimiter, consume single char
      tokens.push(remaining[0]);
      remaining = remaining.slice(1);
    } else {
      tokens.push(remaining.slice(0, nextSpecial));
      remaining = remaining.slice(nextSpecial);
    }
  }

  return tokens;
}

/**
 * FormattedMessage Component
 * 
 * Cleanly renders markdown text containing headings (###), bold (**),
 * italics (*), bullet lists (•, -, *), numbered lists (1.), and code
 * into styled typography without showing raw markdown syntax symbols.
 */
export function FormattedMessage({ text, className = '' }) {
  if (!text) return null;

  // Split lines
  const lines = text.split('\n');
  const renderedElements = [];
  let currentList = null;
  let listKey = 0;

  const flushList = () => {
    if (currentList) {
      if (currentList.type === 'bullet') {
        renderedElements.push(
          <ul key={`list-${listKey++}`} className="space-y-1.5 my-2">
            {currentList.items.map((item, idx) => (
              <li key={idx} className="flex items-start gap-2 text-slate-200">
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 shrink-0 mt-1.5" />
                <span className="flex-1 leading-relaxed">{parseInlineMarkdown(item)}</span>
              </li>
            ))}
          </ul>
        );
      } else if (currentList.type === 'numbered') {
        renderedElements.push(
          <ol key={`list-${listKey++}`} className="space-y-1.5 my-2">
            {currentList.items.map((item, idx) => (
              <li key={idx} className="flex items-start gap-2.5 text-slate-200">
                <span className="font-mono text-[11px] font-bold text-cyan-400 shrink-0 mt-0.5">
                  {idx + 1}.
                </span>
                <span className="flex-1 leading-relaxed">{parseInlineMarkdown(item)}</span>
              </li>
            ))}
          </ol>
        );
      }
      currentList = null;
    }
  };

  lines.forEach((rawLine, lineIdx) => {
    const line = rawLine.trim();

    if (!line) {
      flushList();
      return;
    }

    // Heading 3: ### Heading
    if (line.startsWith('### ')) {
      flushList();
      renderedElements.push(
        <h4
          key={`h3-${lineIdx}`}
          className="text-[13px] font-bold text-cyan-300 tracking-wide mt-3 mb-1.5 flex items-center gap-1.5"
        >
          <span>{parseInlineMarkdown(line.slice(4))}</span>
        </h4>
      );
      return;
    }

    // Heading 2: ## Heading
    if (line.startsWith('## ')) {
      flushList();
      renderedElements.push(
        <h3
          key={`h2-${lineIdx}`}
          className="text-sm font-bold text-cyan-200 tracking-wide mt-3 mb-1.5"
        >
          {parseInlineMarkdown(line.slice(3))}
        </h3>
      );
      return;
    }

    // Heading 1: # Heading
    if (line.startsWith('# ')) {
      flushList();
      renderedElements.push(
        <h2
          key={`h1-${lineIdx}`}
          className="text-sm font-extrabold text-cyan-100 tracking-wide mt-3.5 mb-2"
        >
          {parseInlineMarkdown(line.slice(2))}
        </h2>
      );
      return;
    }

    // Bullet List Item: •, -, or * at start of line
    const bulletMatch = line.match(/^[•\-\*]\s+(.*)$/);
    if (bulletMatch) {
      if (!currentList || currentList.type !== 'bullet') {
        flushList();
        currentList = { type: 'bullet', items: [] };
      }
      currentList.items.push(bulletMatch[1]);
      return;
    }

    // Numbered List Item: 1. Item
    const numMatch = line.match(/^(\d+)\.\s+(.*)$/);
    if (numMatch) {
      if (!currentList || currentList.type !== 'numbered') {
        flushList();
        currentList = { type: 'numbered', items: [] };
      }
      currentList.items.push(numMatch[2]);
      return;
    }

    // Normal Paragraph line
    flushList();
    renderedElements.push(
      <p key={`p-${lineIdx}`} className="text-slate-200 leading-relaxed my-1">
        {parseInlineMarkdown(line)}
      </p>
    );
  });

  flushList();

  return <div className={`formatted-message space-y-1 ${className}`}>{renderedElements}</div>;
}
