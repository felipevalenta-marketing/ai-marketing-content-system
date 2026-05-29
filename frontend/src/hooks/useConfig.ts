import { useEffect, useState } from "react";
import type { ConfigResponseData } from "../types/api";
import { createApiClient } from "../api/client";

export function useConfig(apiBaseUrl: string) {
  const [data, setData] = useState<ConfigResponseData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>("");
  const [refreshIndex, setRefreshIndex] = useState(0);

  useEffect(() => {
    let active = true;
    const client = createApiClient(apiBaseUrl);
    setLoading(true);
    client.getConfig().then((response) => {
      if (!active) {
        return;
      }
      if (response.success && response.data) {
        setData(response.data);
        setError("");
      } else {
        setError(response.errors?.[0] ?? "Unable to load config.");
      }
      setLoading(false);
    });
    return () => {
      active = false;
    };
  }, [apiBaseUrl, refreshIndex]);

  return { data, loading, error, refresh: () => setRefreshIndex((value) => value + 1) };
}
