import { useState } from "react";
import { safeJsonStringify, sanitizeObject } from "../utils/sanitization";
import { Button } from "./Button";

interface JsonViewerProps {
  data: unknown;
  title?: string;
}

export function JsonViewer({ data, title = "JSON Preview" }: JsonViewerProps) {
  const [copied, setCopied] = useState(false);
  const safeData = sanitizeObject(data);
  const text = safeJsonStringify(safeData, 2);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1200);
    } catch {
      // clipboard may be unavailable in local demos
    }
  };

  return (
    <div className="section">
      <div className="copy-row">
        <Button type="button" variant="secondary" onClick={handleCopy}>
          {copied ? "Copied" : "Copy JSON"}
        </Button>
      </div>
      <details open>
        <summary>{title}</summary>
        <pre className="code-block">{text}</pre>
      </details>
    </div>
  );
}
