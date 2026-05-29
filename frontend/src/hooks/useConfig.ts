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
    client.getConfiguration().then((response) => {
      if (!active) {
        return;
      }
      if (response.success && response.data) {
        setData(response.data);
        setError("");
        setLoading(false);
        return;
      }
      client.getConfig().then((legacyResponse) => {
        if (!active) {
          return;
        }
        if (legacyResponse.success && legacyResponse.data) {
          setData({
            ...legacyResponse.data,
            configuration: response.data as any,
          });
          setError("");
        } else {
          setError(response.errors?.[0] ?? legacyResponse.errors?.[0] ?? "Unable to load config.");
        }
        setLoading(false);
      });
      return;
    }).catch(() => {
      if (!active) {
        return;
      }
      client.getConfig().then((legacyResponse) => {
        if (!active) {
          return;
        }
        if (legacyResponse.success && legacyResponse.data) {
          setData(legacyResponse.data);
          setError("");
        } else {
          setError("Unable to load config.");
        }
        setLoading(false);
      });
      return;
    });
    return () => {
      active = false;
    };
  }, [apiBaseUrl, refreshIndex]);

  return { data, loading, error, refresh: () => setRefreshIndex((value) => value + 1) };
}
