import { useCallback, useEffect, useRef, useState } from "react";
import type { HealthResponseData } from "../types/api";
import { createApiClient } from "../api/client";

export function useHealth(apiBaseUrl: string, enabled = true) {
  const [data, setData] = useState<HealthResponseData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>("");
  const [refreshIndex, setRefreshIndex] = useState(0);
  const inFlightRef = useRef(false);
  const hasLoadedRef = useRef(false);

  const loadHealth = useCallback(async () => {
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
      const response = await client.getHealth();
      if (response.success && response.data) {
        setData(response.data);
        setError("");
      } else {
        setError(response.errors?.[0] ?? "Unable to load health status.");
      }
      setLoading(false);
      hasLoadedRef.current = true;
    } finally {
      inFlightRef.current = false;
    }
  }, [apiBaseUrl, enabled]);

  useEffect(() => {
    void loadHealth();
  }, [loadHealth, refreshIndex]);

  return { data, loading, error, hasLoaded: hasLoadedRef.current, refresh: () => setRefreshIndex((value) => value + 1) };
}
