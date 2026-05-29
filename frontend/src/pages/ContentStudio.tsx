import { useEffect, useState } from "react";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { ErrorState } from "../components/ErrorState";
import { JsonViewer } from "../components/JsonViewer";
import { LoadingState } from "../components/LoadingState";
import { MarkdownPreview } from "../components/MarkdownPreview";
import { SectionHeader } from "../components/SectionHeader";
import { StatusPill } from "../components/StatusPill";
import { CONTENT_DEFAULTS } from "../utils/constants";
import { extractMarkdown, formatCount, getStatusLabel } from "../utils/formatting";
import type { GenerateRequest } from "../types/api";
import type { WorkspaceProps } from "./shared";
import { useLocalState } from "../hooks/useLocalState";

interface ContentStudioProps extends WorkspaceProps {
  onSnapshot: (key: string, data: unknown) => void;
}

const DEFAULT_FORM: GenerateRequest = {
  ...CONTENT_DEFAULTS,
  report: true,
  markdown: true,
  persist: false,
  dry_run: false,
  extra_notes: "",
};

export function ContentStudio({ client, onSnapshot, activeBrand }: ContentStudioProps) {
  const [form, setForm] = useLocalState<GenerateRequest>("amcs:content-form", DEFAULT_FORM);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (activeBrand && activeBrand !== form.brand) {
      setForm((current) => ({ ...current, brand: activeBrand } as GenerateRequest));
    }
  }, [activeBrand, form.brand, setForm]);

  const update = (key: keyof GenerateRequest, value: unknown) => {
    setForm((current) => ({ ...current, [key]: value } as GenerateRequest));
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError("");
    const response = await client.generateContent(form);
    if (response.success && response.data) {
      const data = response.data as any;
      setResult(data);
      onSnapshot("generate", data);
    } else {
      setError(response.errors?.[0] ?? "Unable to generate content.");
      setResult(null);
    }
    setLoading(false);
  };

  const markdown = extractMarkdown(result);
  const tokenSummary = result?.token_summary ?? result?.token_usage ?? {};
  const costSummary = result?.cost_summary ?? result?.cost_usage ?? {};
  const generatedContent =
    result?.generated_content ?? result?.content ?? (result?.formatted_output as any)?.short_description ?? "-";
  const totalCost = costSummary?.total_cost ?? "-";

  return (
    <div className="content-grid">
      <Card>
        <SectionHeader
          title="Content Studio"
          description="Run the generation pipeline with structured, safe inputs."
          actions={<StatusPill status={String(result?.approval_status ?? result?.status ?? "ready")} />}
        />

        <div className="form-grid">
          {[
            ["brand", "Brand"],
            ["platform", "Platform"],
            ["content_type", "Content Type"],
            ["objective", "Objective"],
            ["audience", "Audience"],
            ["location", "Location"],
            ["property_type", "Property Type"],
          ].map(([key, label]) => (
            <div className="field" key={key}>
              <label htmlFor={key}>{label}</label>
              <input
                id={key}
                className="input"
                value={String(form[key as keyof GenerateRequest] ?? "")}
                onChange={(event) => update(key as keyof GenerateRequest, event.target.value)}
              />
            </div>
          ))}
          <div className="field field--full">
            <label htmlFor="extra_notes">Extra Notes</label>
            <textarea
              id="extra_notes"
              className="textarea"
              value={String(form.extra_notes ?? "")}
              onChange={(event) => update("extra_notes", event.target.value)}
            />
          </div>
          {[
            ["report", "Report"],
            ["markdown", "Markdown"],
            ["persist", "Persist"],
            ["dry_run", "Dry Run"],
          ].map(([key, label]) => (
            <label key={key} className="field" style={{ display: "flex", flexDirection: "row", alignItems: "center", gap: 10 }}>
              <input
                type="checkbox"
                checked={Boolean(form[key as keyof GenerateRequest])}
                onChange={(event) => update(key as keyof GenerateRequest, event.target.checked)}
              />
              <span>{label}</span>
            </label>
          ))}
        </div>

        <div className="button-row" style={{ marginTop: 20 }}>
          <Button type="button" variant="primary" onClick={handleSubmit} disabled={loading}>
            {loading ? "Generating..." : "Run Generate"}
          </Button>
        </div>

        {loading ? <LoadingState label="Generating content..." /> : null}
        {error ? <ErrorState message={error} /> : null}
      </Card>

      <Card className="panel--sticky">
        <SectionHeader title="Result Preview" description="Generated content, summaries, and safe structured JSON." />
        {result ? (
          <div className="result-panel">
            <StatusPill status={String(result.status ?? result.approval_status ?? "completed")} />
            <p>
              <strong>Status:</strong> {getStatusLabel(String(result.status ?? result.approval_status ?? "completed"))}
            </p>
            <p>
              <strong>Generated Content:</strong> {String(generatedContent)}
            </p>
            {markdown ? <MarkdownPreview markdown={markdown} /> : null}
            <div className="grid-2">
              <div className="metric-card">
                <p className="metric-card__label">Input Tokens</p>
                <p className="metric-card__value">{formatCount((tokenSummary as any)?.input_tokens ?? 0)}</p>
              </div>
              <div className="metric-card">
                <p className="metric-card__label">Total Cost</p>
                <p className="metric-card__value">{String(totalCost)}</p>
              </div>
            </div>
            <JsonViewer data={result} title="Safe JSON" />
          </div>
        ) : (
          <div className="empty-state">Run a generation to preview structured content here.</div>
        )}
      </Card>
    </div>
  );
}
