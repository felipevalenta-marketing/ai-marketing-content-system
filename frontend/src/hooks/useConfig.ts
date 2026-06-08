import { useCallback, useEffect, useRef, useState } from "react";
import type { ConfigResponseData } from "../types/api";
import { createApiClient } from "../api/client";

export function useConfig(apiBaseUrl: string, enabled = true) {
  const [data, setData] = useState<ConfigResponseData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>("");
  const [refreshIndex, setRefreshIndex] = useState(0);
  const inFlightRef = useRef(false);
  const hasLoadedRef = useRef(false);
  const refresh = useCallback(() => setRefreshIndex((value) => value + 1), []);

  const loadConfig = useCallback(async () => {
    if (!enabled) {
      inFlightRef.current = false;
      setLoading(false);
      setError("");
      return;
    }
    if (inFlightRef.current) {
      return;
    }
    inFlightRef.current = true;
    const client = createApiClient(apiBaseUrl);
    setLoading(true);
    try {
      const response = await client.getConfiguration();
      if (response.success && response.data) {
        setData(response.data);
        setError("");
        hasLoadedRef.current = true;
        return;
      }
      const legacyResponse = await client.getConfig();
      if (legacyResponse.success && legacyResponse.data) {
        setData({
          ...legacyResponse.data,
          configuration: response.data as any,
        });
        setError("");
      } else {
        setData(null);
        setError(response.errors?.[0] ?? legacyResponse.errors?.[0] ?? "Unable to load config.");
      }
      hasLoadedRef.current = true;
    } catch (loadError) {
      setData(null);
      setError(loadError instanceof Error ? loadError.message : "Unable to load config.");
      hasLoadedRef.current = true;
    } finally {
      setLoading(false);
      inFlightRef.current = false;
    }
  }, [apiBaseUrl, enabled]);

  useEffect(() => {
    void loadConfig();
  }, [loadConfig, refreshIndex]);

  return { data, loading, error, hasLoaded: hasLoadedRef.current, refresh };
}
