import { useMemo } from 'react';

interface ContentRendererProps {
  html: string;
  className?: string;
}

export default function ContentRenderer({ html, className }: ContentRendererProps) {
  const sanitized = useMemo(() => {
    // Basic sanitization: remove script tags, event handlers
    return html
      .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
      .replace(/\s+on\w+\s*=\s*"[^"]*"/gi, '')
      .replace(/\s+on\w+\s*=\s*'[^']*'/gi, '');
  }, [html]);

  return (
    <div
      className={`prose-content ${className || ''}`}
      dangerouslySetInnerHTML={{ __html: sanitized }}
    />
  );
}
