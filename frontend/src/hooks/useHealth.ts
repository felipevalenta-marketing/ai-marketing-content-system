import { useEffect, useState } from "react";
import type { HealthResponseData } from "../types/api";
import { createApiClient } from "../api/client";

export function useHealth(apiBaseUrl: string) {
  const [data, setData] = useState<HealthResponseData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>("");
  const [refreshIndex, setRefreshIndex] = useState(0);

  useEffect(() => {
    let active = true;
    const client = createApiClient(apiBaseUrl);
    setLoading(true);
    client.getHealth().then((response) => {
      if (!active) {
        return;
      }
      if (response.success && response.data) {
        setData(response.data);
        setError("");
      } else {
        setError(response.errors?.[0] ?? "Unable to load health status.");
      }
      setLoading(false);
    });
    return () => {
      active = false;
    };
  }, [apiBaseUrl, refreshIndex]);

  return { data, loading, error, refresh: () => setRefreshIndex((value) => value + 1) };
}
