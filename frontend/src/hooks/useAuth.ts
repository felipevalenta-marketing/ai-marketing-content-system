import { useEffect, useState } from "react";
import type { ApiClient } from "../api/client";
import type { AuthResult, LoginRequest, RegisterRequest, UserProfile, UserProfileUpdateRequest } from "../types/api";

const AUTH_TOKEN_KEY = "amcs:auth-token";

function readToken(): string {
  try {
    return window.localStorage.getItem(AUTH_TOKEN_KEY) ?? "";
  } catch {
    return "";
  }
}

function writeToken(token: string) {
  try {
    if (token) {
      window.localStorage.setItem(AUTH_TOKEN_KEY, token);
    } else {
      window.localStorage.removeItem(AUTH_TOKEN_KEY);
    }
  } catch {
    // ignore storage errors
  }
}

export interface UseAuthResult {
  token: string;
  currentUser: UserProfile | null;
  loading: boolean;
  error: string | null;
  isAuthenticated: boolean;
  login: (payload: LoginRequest) => Promise<AuthResult>;
  register: (payload: RegisterRequest) => Promise<AuthResult>;
  logout: () => Promise<void>;
  refreshCurrentUser: () => Promise<void>;
  updateProfile: (payload: UserProfileUpdateRequest) => Promise<AuthResult>;
}

export function useAuth(client: ApiClient): UseAuthResult {
  const [token, setToken] = useState<string>(() => readToken());
  const [currentUser, setCurrentUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState<boolean>(Boolean(token));
  const [error, setError] = useState<string | null>(null);

  const refreshCurrentUser = async () => {
    if (!readToken()) {
      setCurrentUser(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    const response = await client.getCurrentUser();
    if (response.success && response.data?.user) {
      setCurrentUser(response.data.user as UserProfile);
      setError(null);
    } else {
      setCurrentUser(null);
      setError(response.errors?.[0] ?? "Authentication required.");
      writeToken("");
      setToken("");
    }
    setLoading(false);
  };

  useEffect(() => {
    void refreshCurrentUser();
  }, [client]);

  const login = async (payload: LoginRequest) => {
    setLoading(true);
    const response = await client.login(payload);
    if (response.success && response.data?.access_token) {
      writeToken(String(response.data.access_token));
      setToken(String(response.data.access_token));
      if (response.data.user) {
        setCurrentUser(response.data.user as UserProfile);
      }
      setError(null);
    } else {
      setError(response.errors?.[0] ?? "Login failed.");
    }
    setLoading(false);
    return (response.data ?? {}) as AuthResult;
  };

  const register = async (payload: RegisterRequest) => {
    setLoading(true);
    const response = await client.register(payload);
    if (response.success && response.data?.access_token) {
      writeToken(String(response.data.access_token));
      setToken(String(response.data.access_token));
      if (response.data.user) {
        setCurrentUser(response.data.user as UserProfile);
      }
      setError(null);
    } else {
      setError(response.errors?.[0] ?? "Registration failed.");
    }
    setLoading(false);
    return (response.data ?? {}) as AuthResult;
  };

  const logout = async () => {
    await client.logout();
    writeToken("");
    setToken("");
    setCurrentUser(null);
    setError(null);
  };

  const updateProfile = async (payload: UserProfileUpdateRequest) => {
    const response = await client.updateProfile(payload);
    if (response.success && response.data?.user) {
      setCurrentUser(response.data.user as UserProfile);
    } else {
      setError(response.errors?.[0] ?? "Profile update failed.");
    }
    return (response.data ?? {}) as AuthResult;
  };

  return {
    token,
    currentUser,
    loading,
    error,
    isAuthenticated: Boolean(token && currentUser),
    login,
    register,
    logout,
    refreshCurrentUser,
    updateProfile,
  };
}
