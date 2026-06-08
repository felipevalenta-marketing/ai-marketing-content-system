import { useState } from "react";
import { API_ENDPOINTS } from "../api/endpoints";
import { Button } from "../components/Button";
import { Badge } from "../components/Badge";
import { Card } from "../components/Card";
import { ErrorState } from "../components/ErrorState";
import { JsonViewer } from "../components/JsonViewer";
import { LoadingState } from "../components/LoadingState";
import { MarkdownPreview } from "../components/MarkdownPreview";
import { SectionHeader } from "../components/SectionHeader";
import { StatusPill } from "../components/StatusPill";
import type { ApiClient } from "../api/client";
import type { GenerateRequest } from "../types/api";
import type { WorkspaceProps } from "./shared";
import { useLocalState } from "../hooks/useLocalState";
import { CONTENT_DEFAULTS, CONTENT_TYPE_OPTIONS } from "../utils/constants";
import { extractMarkdown, formatCount, getStatusLabel } from "../utils/formatting";
import { IS_DEMO_MODE } from "../utils/demo";

interface ContentStudioProps extends WorkspaceProps {
  onSnapshot: (key: string, data: unknown) => void;
}

const AUTH_TOKEN_KEY = "amcs:auth-token";
const DEMO_GENERATE_LOGIN = {
  email: "admin@test.com",
  password: "Test12345!",
};

const DEFAULT_PROMPT = "Write a warm Instagram post for Wenzel Partner about a premium Mallorca home, with a clear hook, concise caption, CTA, and 3 to 5 relevant hashtags.";

function readStoredToken(): string {
  try {
    return window.localStorage.getItem(AUTH_TOKEN_KEY) ?? "";
  } catch {
    return "";
  }
}

function writeStoredToken(token: string) {
  try {
    if (token) {
      window.localStorage.setItem(AUTH_TOKEN_KEY, token);
    } else {
      window.localStorage.removeItem(AUTH_TOKEN_KEY);
    }
  } catch {
    // ignore local storage failures in demo and local dev
  }
}

function toText(value: unknown): string {
  if (typeof value === "string") {
    return value.trim();
  }
  if (value == null) {
    return "";
  }
  return String(value).trim();
}

function maybeParseJson(value: unknown): Record<string, unknown> | null {
  if (!value) {
    return null;
  }
  if (typeof value === "object" && !Array.isArray(value)) {
    return value as Record<string, unknown>;
  }
  if (typeof value !== "string") {
    return null;
  }
  try {
    const parsed = JSON.parse(value);
    return parsed && typeof parsed === "object" && !Array.isArray(parsed) ? (parsed as Record<string, unknown>) : null;
  } catch {
    return null;
  }
}

function extractStructuredOutput(result: any) {
  const root = maybeParseJson(result);
  const formatted = maybeParseJson(result?.formatted_output) ?? maybeParseJson(result?.content) ?? maybeParseJson(result?.generated_content) ?? root ?? {};
  const markdown =
    toText(result?.markdown_report?.markdown) ||
    toText(result?.markdown) ||
    toText(formatted.markdown) ||
    extractMarkdown(result) ||
    "";

  const hashtags = Array.isArray(formatted.hashtags)
    ? formatted.hashtags.map((tag) => toText(tag)).filter(Boolean)
    : Array.isArray(result?.hashtags)
      ? result.hashtags.map((tag: unknown) => toText(tag)).filter(Boolean)
      : [];

  const isImagePrompt = String(result?.content_type ?? formatted.content_type ?? "").trim() === "image_prompt";
  const isVideoScript = String(result?.content_type ?? formatted.content_type ?? "").trim() === "video_script";
  const isPropertyDescription = String(result?.content_type ?? formatted.content_type ?? "").trim() === "property_description";
  const isAdCopy = String(result?.content_type ?? formatted.content_type ?? "").trim() === "ad_copy";

  return {
    contentType: toText(formatted.content_type ?? result?.content_type),
    hook: toText(formatted.hook ?? formatted.title ?? formatted.headline ?? result?.hook ?? result?.title ?? result?.headline),
    caption: toText(formatted.caption ?? formatted.description ?? formatted.summary ?? formatted.script ?? result?.caption ?? result?.description ?? result?.summary ?? result?.script),
    cta: toText(formatted.cta ?? result?.cta),
    hashtags,
    title: toText(formatted.title ?? formatted.headline ?? result?.title ?? result?.headline),
    description: toText(formatted.description ?? formatted.long_description ?? formatted.short_description ?? result?.description ?? result?.long_description ?? result?.short_description),
    highlights: Array.isArray(formatted.highlights)
      ? formatted.highlights.map((item: unknown) => toText(item)).filter(Boolean)
      : Array.isArray(result?.highlights)
        ? result.highlights.map((item: unknown) => toText(item)).filter(Boolean)
        : [],
    headline: toText(formatted.headline ?? result?.headline),
    primaryText: toText(formatted.primary_text ?? formatted.body_copy ?? result?.primary_text ?? result?.body_copy),
    imagePrompt: toText(formatted.image_prompt ?? formatted.prompt ?? result?.image_prompt ?? result?.prompt),
    style: toText(formatted.style ?? formatted.visual_style ?? result?.style ?? result?.visual_style),
    camera: toText(formatted.camera ?? formatted.camera_direction ?? result?.camera ?? result?.camera_direction),
    lighting: toText(formatted.lighting ?? formatted.lighting_style ?? result?.lighting ?? result?.lighting_style),
    negativePrompt: toText(formatted.negative_prompt ?? result?.negative_prompt),
    scene1: toText(formatted.scene_1 ?? formatted.scene1 ?? formatted.script ?? result?.scene_1 ?? result?.script),
    scene2: toText(formatted.scene_2 ?? formatted.scene2 ?? result?.scene_2),
    scene3: toText(formatted.scene_3 ?? formatted.scene3 ?? result?.scene_3),
    voiceover: toText(formatted.voiceover ?? formatted.voiceover_direction ?? result?.voiceover),
    isImagePrompt,
    isVideoScript,
    isPropertyDescription,
    isAdCopy,
    markdown,
  };
}

async function ensureBackendToken(client: ApiClient): Promise<string | null> {
  const existingToken = readStoredToken();
  if (existingToken) {
    return existingToken;
  }
  if (!IS_DEMO_MODE) {
    return null;
  }
  const response = await client.login(DEMO_GENERATE_LOGIN);
  const token = response.success ? toText(response.data?.access_token) : "";
  if (token) {
    writeStoredToken(token);
    return token;
  }
  return null;
}

export function ContentStudio({ client, onSnapshot }: ContentStudioProps) {
  const [prompt, setPrompt] = useLocalState<string>("amcs:content-prompt", DEFAULT_PROMPT);
  const [contentType, setContentType] = useLocalState<string>("amcs:content-type", CONTENT_DEFAULTS.content_type);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [authNote, setAuthNote] = useState("");

  const handleSubmit = async () => {
    const cleanPrompt = prompt.trim();
    if (!cleanPrompt) {
      setError("Please enter a prompt before generating.");
      return;
    }

    setLoading(true);
    setError("");
    setAuthNote("");

    try {
      const token = await ensureBackendToken(client);
      if (IS_DEMO_MODE && !token) {
        setError("Unable to authenticate to the presentation backend.");
        setLoading(false);
        return;
      }

      const payload: GenerateRequest = {
        brand: CONTENT_DEFAULTS.brand,
        platform: CONTENT_DEFAULTS.platform,
        content_type: contentType,
        objective: CONTENT_DEFAULTS.objective,
        audience: CONTENT_DEFAULTS.audience,
        location: CONTENT_DEFAULTS.location,
        property_type: CONTENT_DEFAULTS.property_type,
        prompt: cleanPrompt,
        extra_notes: cleanPrompt,
        report: true,
        markdown: true,
        persist: false,
        dry_run: false,
      };

      const response = await client.generateContent(payload);
      if (response.success && response.data) {
        const data = response.data as any;
        setResult(data);
        onSnapshot("generate", data);
        setAuthNote(token ? "Authenticated for generation." : "");
      } else {
        setResult(null);
        setError(response.errors?.[0] ?? "Unable to generate content.");
      }
    } catch (submitError) {
      setResult(null);
      setError(submitError instanceof Error ? submitError.message : "Unable to generate content.");
    } finally {
      setLoading(false);
    }
  };

  const output = extractStructuredOutput(result);
  const tokenSummary = result?.token_summary ?? result?.token_usage ?? {};
  const costSummary = result?.cost_summary ?? result?.cost_usage ?? {};
  const generatedMarkdown = output.markdown || extractMarkdown(result);
  const hashtags = output.hashtags;
  const selectedContentType = String(contentType ?? result?.content_type ?? "").trim();
  const resolvedContentType = selectedContentType || output.contentType;
  const showImagePromptFields = resolvedContentType === "image_prompt" || output.contentType === "image_prompt" || output.isImagePrompt;
  const showVideoScriptFields = resolvedContentType === "video_script" || output.contentType === "video_script" || output.isVideoScript;
  const showPropertyDescriptionFields = resolvedContentType === "property_description" || output.contentType === "property_description" || output.isPropertyDescription;
  const showAdCopyFields = resolvedContentType === "ad_copy" || output.contentType === "ad_copy" || output.isAdCopy;
  const showInstagramReelFields = resolvedContentType === "instagram_reel" || output.contentType === "instagram_reel";
  const showSocialCopyFields = ["instagram_post", "linkedin_post", "facebook_post"].includes(resolvedContentType) || ["instagram_post", "linkedin_post", "facebook_post"].includes(output.contentType);
  const shouldShowCaptionAndHashtags = showSocialCopyFields || showInstagramReelFields;
  const generatedDescription = showImagePromptFields
    ? "Image prompt, style, camera, lighting, and the raw backend response."
    : showVideoScriptFields
      ? "Hook, three reel scenes, voiceover, CTA, and the raw backend response."
      : showPropertyDescriptionFields
        ? "Title, description, highlights, CTA, and the raw backend response."
        : showAdCopyFields
          ? "Headline, primary text, description, CTA, and the raw backend response."
          : showInstagramReelFields
            ? "Hook, reel script, scene direction, CTA, and the raw backend response."
            : "Hook, caption, CTA, hashtags, and the raw backend response.";

  return (
    <div className="content-grid">
      <Card>
        <SectionHeader
          title="Content Studio"
          description="Generate platform-ready social copy or a structured image prompt from a single prompt."
          actions={<StatusPill status={String(result?.approval_status ?? result?.status ?? "ready")} />}
        />

        <div className="stack">
          <label className="field field--full">
            <span>Prompt</span>
            <textarea
              className="textarea"
              value={prompt}
              onChange={(event) => setPrompt(event.target.value)}
              placeholder="Describe the tone, property, audience, or angle you want for the post."
            />
          </label>

          <div className="row wrap">
            <Badge tone="neutral">wenzel_partner</Badge>
            <Badge tone="neutral">{contentType.replace("_", " ")}</Badge>
            <label className="field">
              <span>Content Type</span>
              <select className="select" value={contentType} onChange={(event) => setContentType(event.target.value)}>
                {CONTENT_TYPE_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            {IS_DEMO_MODE ? <Badge tone="warning">Demo Mode</Badge> : null}
            {authNote ? <Badge tone="success">{authNote}</Badge> : null}
          </div>

          <div className="button-row">
            <Button type="button" variant="primary" onClick={handleSubmit} disabled={loading}>
              {loading ? "Generating..." : "Generate Content"}
            </Button>
          </div>

          {loading ? <LoadingState label="Generating content..." /> : null}
          {error ? <ErrorState message={error} /> : null}
        </div>
      </Card>

      <Card className="panel--sticky">
        <SectionHeader
          title="Generated Content"
          description={generatedDescription}
        />
        {result ? (
          <div className="result-panel">
            <StatusPill status={String(result.status ?? result.approval_status ?? "completed")} />
            {showImagePromptFields ? (
              <div className="grid-2">
                <div className="metric-card">
                  <p className="metric-card__label">Image Prompt</p>
                  <p className="metric-card__value">{output.imagePrompt || "No image prompt returned."}</p>
                </div>
                <div className="metric-card">
                  <p className="metric-card__label">Negative Prompt</p>
                  <p className="metric-card__value">{output.negativePrompt || "No negative prompt returned."}</p>
                </div>
              </div>
            ) : null}

            {showImagePromptFields ? (
              <div className="grid-2">
                <div className="metric-card">
                  <p className="metric-card__label">Style</p>
                  <p className="metric-card__value">{output.style || "No style returned."}</p>
                </div>
                <div className="metric-card">
                  <p className="metric-card__label">Camera</p>
                  <p className="metric-card__value">{output.camera || "No camera direction returned."}</p>
                </div>
              </div>
            ) : null}

            {showImagePromptFields ? (
              <div className="section">
                <h3>Lighting</h3>
                <p>{output.lighting || "No lighting returned."}</p>
              </div>
            ) : null}

            {showVideoScriptFields ? (
              <>
                <div className="grid-2">
                  <div className="metric-card">
                    <p className="metric-card__label">Hook</p>
                    <p className="metric-card__value">{output.hook || "No hook returned."}</p>
                  </div>
                  <div className="metric-card">
                    <p className="metric-card__label">CTA</p>
                    <p className="metric-card__value">{output.cta || "No CTA returned."}</p>
                  </div>
                </div>

                <div className="section">
                  <h3>Scene 1</h3>
                  <p>{output.scene1 || "No scene 1 returned."}</p>
                </div>

                <div className="section">
                  <h3>Scene 2</h3>
                  <p>{output.scene2 || "No scene 2 returned."}</p>
                </div>

                <div className="section">
                  <h3>Scene 3</h3>
                  <p>{output.scene3 || "No scene 3 returned."}</p>
                </div>

                <div className="section">
                  <h3>Voiceover</h3>
                  <p>{output.voiceover || "No voiceover returned."}</p>
                </div>
              </>
            ) : null}

            {showPropertyDescriptionFields ? (
              <>
                <div className="grid-2">
                  <div className="metric-card">
                    <p className="metric-card__label">Title</p>
                    <p className="metric-card__value">{output.title || "No title returned."}</p>
                  </div>
                  <div className="metric-card">
                    <p className="metric-card__label">CTA</p>
                    <p className="metric-card__value">{output.cta || "No CTA returned."}</p>
                  </div>
                </div>

                <div className="section">
                  <h3>Description</h3>
                  <p>{output.description || "No description returned."}</p>
                </div>

                <div className="section">
                  <h3>Highlights</h3>
                  <div className="row wrap">
                    {output.highlights.length ? output.highlights.map((item) => <Badge key={item} tone="neutral">{item}</Badge>) : <span className="muted">No highlights returned.</span>}
                  </div>
                </div>
              </>
            ) : null}

            {showAdCopyFields ? (
              <>
                <div className="grid-2">
                  <div className="metric-card">
                    <p className="metric-card__label">Headline</p>
                    <p className="metric-card__value">{output.headline || "No headline returned."}</p>
                  </div>
                  <div className="metric-card">
                    <p className="metric-card__label">CTA</p>
                    <p className="metric-card__value">{output.cta || "No CTA returned."}</p>
                  </div>
                </div>

                <div className="section">
                  <h3>Primary Text</h3>
                  <p>{output.primaryText || "No primary text returned."}</p>
                </div>

                <div className="section">
                  <h3>Description</h3>
                  <p>{output.description || "No description returned."}</p>
                </div>
              </>
            ) : null}

            {showInstagramReelFields && !showVideoScriptFields ? (
              <>
                <div className="grid-2">
                  <div className="metric-card">
                    <p className="metric-card__label">Hook</p>
                    <p className="metric-card__value">{output.hook || "No hook returned."}</p>
                  </div>
                  <div className="metric-card">
                    <p className="metric-card__label">CTA</p>
                    <p className="metric-card__value">{output.cta || "No CTA returned."}</p>
                  </div>
                </div>

                <div className="section">
                  <h3>Script</h3>
                  <p>{output.caption || "No script returned."}</p>
                </div>

                <div className="section">
                  <h3>Scene Direction</h3>
                  <p>{output.scene1 || "No scene direction returned."}</p>
                </div>

                <div className="section">
                  <h3>Hashtags</h3>
                  <div className="row wrap">
                    {hashtags.length ? hashtags.map((tag) => <Badge key={tag} tone="neutral">{tag}</Badge>) : <span className="muted">No hashtags returned.</span>}
                  </div>
                </div>
              </>
            ) : null}

            {!showImagePromptFields && !showVideoScriptFields && !showPropertyDescriptionFields && !showAdCopyFields && !showInstagramReelFields ? (
              <>
                <div className="grid-2">
                  <div className="metric-card">
                    <p className="metric-card__label">Hook</p>
                    <p className="metric-card__value">{output.hook || "No hook returned."}</p>
                  </div>
                  <div className="metric-card">
                    <p className="metric-card__label">CTA</p>
                    <p className="metric-card__value">{output.cta || "No CTA returned."}</p>
                  </div>
                </div>

                {shouldShowCaptionAndHashtags ? (
                  <>
                    <div className="section">
                      <h3>Caption</h3>
                      <p>{output.caption || "No caption returned."}</p>
                    </div>

                    <div className="section">
                      <h3>Hashtags</h3>
                      <div className="row wrap">
                        {hashtags.length ? hashtags.map((tag) => <Badge key={tag} tone="neutral">{tag}</Badge>) : <span className="muted">No hashtags returned.</span>}
                      </div>
                    </div>
                  </>
                ) : null}
              </>
            ) : null}

            {generatedMarkdown ? <MarkdownPreview markdown={generatedMarkdown} title="Generated Markdown" /> : null}

            <div className="grid-2">
              <div className="metric-card">
                <p className="metric-card__label">Input Tokens</p>
                <p className="metric-card__value">{formatCount(Number(tokenSummary?.input_tokens ?? 0))}</p>
              </div>
              <div className="metric-card">
                <p className="metric-card__label">Total Cost</p>
                <p className="metric-card__value">{String(costSummary?.total_cost ?? "-")}</p>
              </div>
            </div>

            <JsonViewer data={result} title="Backend Response" />
          </div>
        ) : (
          <div className="empty-state">Enter a prompt and click Generate Content to preview the backend response.</div>
        )}
      </Card>
    </div>
  );
}
