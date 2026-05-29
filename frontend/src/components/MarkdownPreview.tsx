import { useState } from "react";
import { Button } from "./Button";
import { sanitizeObject } from "../utils/sanitization";

interface MarkdownPreviewProps {
  markdown?: string;
  title?: string;
}

export function MarkdownPreview({ markdown, title = "Markdown Preview" }: MarkdownPreviewProps) {
  const [copied, setCopied] = useState(false);
  const safeMarkdown = typeof markdown === "string" ? String(sanitizeObject(markdown)) : "";

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(safeMarkdown);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1200);
    } catch {
      // clipboard can be unavailable in some browsers
    }
  };

  if (!safeMarkdown) {
    return <div className="empty-state">No markdown preview available yet.</div>;
  }

  return (
    <div className="section">
      <div className="copy-row">
        <Button type="button" variant="secondary" onClick={handleCopy}>
          {copied ? "Copied" : "Copy Markdown"}
        </Button>
      </div>
      <details open>
        <summary>{title}</summary>
        <pre className="code-block">{safeMarkdown}</pre>
      </details>
    </div>
  );
}
