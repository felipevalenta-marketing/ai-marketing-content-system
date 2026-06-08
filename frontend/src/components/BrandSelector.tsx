import { useEffect, useMemo, useRef, useState } from "react";
import type { BrandDefaults, BrandProfile, BrandRegistryEntry } from "../types/api";
import { isUnauthorizedResponse, type ApiClient } from "../api/client";
import { Badge } from "./Badge";
import { LoadingState } from "./LoadingState";
import { DEMO_BRANDS, DEMO_BRAND_DEFAULTS, DEMO_BRAND_PROFILE, IS_DEMO_MODE } from "../utils/demo";

interface BrandSelectorProps {
  client: ApiClient;
  value: string;
  onChange: (value: string) => void;
  onBrandsLoaded?: (brands: BrandRegistryEntry[]) => void;
  brandProfile?: BrandProfile | null;
  brandValidation?: Record<string, unknown> | null;
  brandDefaults?: BrandDefaults | null;
  compact?: boolean;
}

export function BrandSelector({ client, value, onChange, onBrandsLoaded, brandProfile, brandValidation, brandDefaults, compact = false }: BrandSelectorProps) {
  const [brands, setBrands] = useState<BrandRegistryEntry[]>(() => (IS_DEMO_MODE ? (DEMO_BRANDS as BrandRegistryEntry[]) : []));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const hasLoadedRef = useRef(IS_DEMO_MODE);
  const onBrandsLoadedRef = useRef(onBrandsLoaded);

  useEffect(() => {
    onBrandsLoadedRef.current = onBrandsLoaded;
  }, [onBrandsLoaded]);

  useEffect(() => {
    if (IS_DEMO_MODE) {
      return;
    }
    let active = true;
    setLoading(true);
    setError("");
    (async () => {
      try {
        const response = await client.getBrands();
        if (!active) {
          return;
        }
        if (response.success && response.data?.brands) {
          const entries = response.data.brands as BrandRegistryEntry[];
          setBrands(entries);
          onBrandsLoadedRef.current?.(entries);
        } else {
          setBrands([]);
          setError(isUnauthorizedResponse(response) ? "Your session expired. Please log in again." : response.errors?.[0] ?? "No brands available.");
        }
      } catch (loadError) {
        if (!active) {
          return;
        }
        setBrands([]);
        setError(loadError instanceof Error ? loadError.message : "No brands available.");
      } finally {
        if (active) {
          hasLoadedRef.current = true;
          setLoading(false);
        }
      }
    })();
    return () => {
      active = false;
    };
  }, [client]);

  useEffect(() => {
    if (!brands.length) {
      return;
    }
    if (value && brands.some((brand) => brand.brand_id === value)) {
      return;
    }
    const fallback = brands[0]?.brand_id ? String(brands[0].brand_id) : "";
    if (fallback && fallback !== value) {
      onChange(fallback);
    }
  }, [brands, onChange, value]);

  const activeBrand = useMemo(() => brands.find((brand) => brand.brand_id === value) ?? null, [brands, value]);

  if (loading && !hasLoadedRef.current) {
    return <LoadingState label="Loading brands..." />;
  }

  if (!brands.length) {
    if (compact) {
      return (
        <select id="brandSelector" className="select topbar__select" value={value || "wenzel_partner"} onChange={(event) => onChange(event.target.value)}>
          <option value={value || "wenzel_partner"}>{value || "wenzel_partner"}</option>
        </select>
      );
    }
    return (
      <div className="stack">
        <div className="field">
          <label htmlFor="brandSelector">Brand</label>
          <select id="brandSelector" className="select" value={value || "wenzel_partner"} onChange={(event) => onChange(event.target.value)}>
            <option value={value || "wenzel_partner"}>{value || "wenzel_partner"}</option>
          </select>
        </div>
        <p className="muted">{error || "Create a brand folder under brands/ to start."}</p>
        {brandProfile ? (
          <div className="button-row">
            <Badge tone={brandProfile.status === "inactive" ? "warning" : brandProfile.status === "invalid" ? "error" : "success"}>{String(brandProfile.status ?? "active")}</Badge>
            {typeof brandProfile.health_score === "number" ? <Badge tone={brandProfile.health_score >= 80 ? "success" : brandProfile.health_score >= 50 ? "warning" : "error"}>{`${brandProfile.health_score}/100`}</Badge> : null}
          </div>
        ) : null}
      </div>
    );
  }

  if (compact) {
    return (
      <select
        id="brandSelector"
        className="select topbar__select"
        value={value || brands[0]?.brand_id || ""}
        onChange={(event) => onChange(event.target.value)}
      >
        {brands.map((brand) => (
          <option key={brand.brand_id ?? brand.knowledge_path ?? brand.display_name} value={String(brand.brand_id ?? "")}>
            {String(brand.display_name ?? brand.brand_id)}
          </option>
        ))}
      </select>
    );
  }

  return (
    <div className="stack">
      <div className="field">
        <label htmlFor="brandSelector">Brand</label>
        <select id="brandSelector" className="select" value={value || brands[0]?.brand_id || ""} onChange={(event) => onChange(event.target.value)}>
          {brands.map((brand) => (
            <option key={brand.brand_id ?? brand.knowledge_path ?? brand.display_name} value={String(brand.brand_id ?? "")}>
              {String(brand.display_name ?? brand.brand_id)}
            </option>
          ))}
        </select>
      </div>
      <div className="button-row">
        <Badge tone={activeBrand?.status === "partial" || activeBrand?.status === "incomplete" ? "warning" : activeBrand?.status === "invalid" ? "error" : activeBrand?.status === "inactive" ? "warning" : "success"}>
          {String(activeBrand?.status ?? "active")}
        </Badge>
        {typeof brandProfile?.health_score === "number" ? (
          <Badge tone={brandProfile.health_score >= 80 ? "success" : brandProfile.health_score >= 50 ? "warning" : "error"}>{`${brandProfile.health_score}/100`}</Badge>
        ) : null}
        <span className="muted">{String(activeBrand?.display_name ?? activeBrand?.brand_id ?? value)}</span>
      </div>
      {brandValidation?.warnings ? <p className="muted">{Array.isArray(brandValidation.warnings) ? (brandValidation.warnings as string[]).slice(0, 2).join(" | ") : ""}</p> : null}
      {brandDefaults ? (
        <p className="muted">
          {`Defaults: ${String(brandDefaults.default_platform ?? "instagram")} / ${String(brandDefaults.default_content_type ?? "instagram_post")} / ${String(brandDefaults.default_campaign_type ?? "property_launch")}`}
        </p>
      ) : null}
    </div>
  );
}
