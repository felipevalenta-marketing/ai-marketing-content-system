import { createApiClient } from "../api/client";
import { DEFAULT_API_BASE_URL } from "../utils/constants";
import { useLocalState } from "./useLocalState";

export function useApi() {
  const [apiBaseUrl, setApiBaseUrl] = useLocalState<string>("amcs:api-base-url", DEFAULT_API_BASE_URL);
  const client = createApiClient(apiBaseUrl);

  return {
    apiBaseUrl,
    setApiBaseUrl,
    client,
  };
}
