import { useCallback, useEffect, useRef, useState } from "react";
import { isUnauthorizedResponse, type ApiClient } from "../api/client";
import { DEMO_ACCESS, DEMO_USER, IS_DEMO_MODE } from "../utils/demo";
import type { AccessSummary, AuthResult, LoginRequest, RegisterRequest, UserProfile, UserProfileUpdateRequest } from "../types/api";

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
  access: AccessSummary | null;
  role: string;
  permissions: string[];
  loading: boolean;
  error: string | null;
  isAuthenticated: boolean;
  login: (payload: LoginRequest) => Promise<AuthResult>;
  register: (payload: RegisterRequest) => Promise<AuthResult>;
  logout: () => Promise<void>;
  refreshCurrentUser: () => Promise<void>;
  updateProfile: (payload: UserProfileUpdateRequest) => Promise<AuthResult>;
  refreshAccess: () => Promise<void>;
  hasPermission: (permission: string) => boolean;
  hasAnyPermission: (permissions: string[]) => boolean;
  hasAllPermissions: (permissions: string[]) => boolean;
}

export function useAuth(client: ApiClient): UseAuthResult {
  const [token, setToken] = useState<string>(() => (IS_DEMO_MODE ? "demo-token" : readToken()));
  const [currentUser, setCurrentUser] = useState<UserProfile | null>(() => (IS_DEMO_MODE ? DEMO_USER : null));
  const [access, setAccess] = useState<AccessSummary | null>(() => (IS_DEMO_MODE ? DEMO_ACCESS : null));
  const [loading, setLoading] = useState<boolean>(() => !IS_DEMO_MODE && Boolean(readToken()));
  const [error, setError] = useState<string | null>(null);
  const refreshInFlightRef = useRef(false);

  const refreshAccess = useCallback(async () => {
    if (IS_DEMO_MODE) {
      setAccess(DEMO_ACCESS);
      return;
    }
    if (!readToken()) {
      setAccess(null);
      return;
    }
    try {
      const response = await client.getMyAccess();
      if (response.success && response.data) {
        setAccess(response.data as AccessSummary);
      } else {
        setAccess(null);
        if (isUnauthorizedResponse(response)) {
          setError(null);
        }
      }
    } catch {
      setAccess(null);
    }
  }, [client]);

  const refreshCurrentUser = useCallback(async () => {
    if (IS_DEMO_MODE) {
      setCurrentUser(DEMO_USER);
      setAccess(DEMO_ACCESS);
      setError(null);
      setLoading(false);
      refreshInFlightRef.current = false;
      return;
    }
    if (refreshInFlightRef.current) {
      return;
    }
    refreshInFlightRef.current = true;
    if (!readToken()) {
      setCurrentUser(null);
      setAccess(null);
      setLoading(false);
      refreshInFlightRef.current = false;
      return;
    }
    setLoading(true);
    try {
      const response = await client.getCurrentUser();
      const userData = response.success && response.data ? ((response.data as AuthResult).user ?? response.data) : null;
      if (response.success && userData) {
        setCurrentUser(userData as UserProfile);
        setError(null);
        await refreshAccess();
      } else {
        setCurrentUser(null);
        setAccess(null);
        setError(isUnauthorizedResponse(response) ? "Your session expired. Please log in again." : response.errors?.[0] ?? "Authentication required.");
        writeToken("");
        setToken("");
      }
    } finally {
      setLoading(false);
      refreshInFlightRef.current = false;
    }
  }, [client, refreshAccess]);

  useEffect(() => {
    if (IS_DEMO_MODE) {
      setCurrentUser(DEMO_USER);
      setAccess(DEMO_ACCESS);
      setError(null);
      setLoading(false);
      return;
    }
    void refreshCurrentUser();
  }, [refreshCurrentUser]);

  const login = useCallback(async (payload: LoginRequest) => {
    if (IS_DEMO_MODE) {
      setLoading(false);
      setCurrentUser(DEMO_USER);
      setAccess(DEMO_ACCESS);
      setError(null);
      return {
        success: true,
        data: {
          access_token: "demo-token",
          token_type: "bearer",
          user: DEMO_USER,
        },
        warnings: [],
        errors: [],
        metadata: {},
      } as AuthResult;
    }
    setLoading(true);
    try {
      const response = await client.login(payload);
      if (response.success && response.data?.access_token) {
        const nextToken = String(response.data.access_token);
        writeToken(nextToken);
        setToken(nextToken);
        setError(null);
        await refreshCurrentUser();
      } else {
        const message = response.errors?.[0] ?? "Login failed.";
        setError(message);
        if (typeof import.meta !== "undefined" && import.meta.env?.DEV) {
          console.error("[auth] login failed", { success: response.success, errors: response.errors, warnings: response.warnings });
        }
      }
      return {
        ...(response.data ?? {}),
        success: response.success,
        warnings: response.warnings,
        errors: response.errors,
        metadata: response.metadata,
      } as AuthResult;
    } finally {
      setLoading(false);
    }
  }, [client, refreshAccess, refreshCurrentUser]);

  const register = useCallback(async (payload: RegisterRequest) => {
    if (IS_DEMO_MODE) {
      setLoading(false);
      setCurrentUser(DEMO_USER);
      setAccess(DEMO_ACCESS);
      setError(null);
      return {
        success: true,
        data: {
          access_token: "demo-token",
          token_type: "bearer",
          user: DEMO_USER,
        },
        warnings: [],
        errors: [],
        metadata: {},
      } as AuthResult;
    }
    setLoading(true);
    try {
      const response = await client.register(payload);
      if (response.success && response.data?.access_token) {
        const nextToken = String(response.data.access_token);
        writeToken(nextToken);
        setToken(nextToken);
        setError(null);
        await refreshCurrentUser();
      } else if (response.success) {
        setError(response.warnings?.[0] ?? "Account created. Please log in.");
        if (typeof import.meta !== "undefined" && import.meta.env?.DEV) {
          console.info("[auth] registration succeeded without token", { warnings: response.warnings });
        }
      } else {
        const message = response.errors?.[0] ?? "Registration failed.";
        setError(message);
        if (typeof import.meta !== "undefined" && import.meta.env?.DEV) {
          console.error("[auth] registration failed", { success: response.success, errors: response.errors, warnings: response.warnings });
        }
      }
      return {
        ...(response.data ?? {}),
        success: response.success,
        warnings: response.warnings,
        errors: response.errors,
        metadata: response.metadata,
      } as AuthResult;
    } finally {
      setLoading(false);
    }
  }, [client, refreshAccess]);

  const logout = useCallback(async () => {
    if (IS_DEMO_MODE) {
      setCurrentUser(DEMO_USER);
      setAccess(DEMO_ACCESS);
      setError(null);
      setLoading(false);
      return;
    }
    await client.logout();
    writeToken("");
    setToken("");
    setCurrentUser(null);
    setAccess(null);
    setError(null);
  }, [client]);

  const updateProfile = useCallback(async (payload: UserProfileUpdateRequest) => {
    if (IS_DEMO_MODE) {
      setCurrentUser((current) => ({
        ...(current ?? DEMO_USER),
        ...payload,
      } as UserProfile));
      setAccess(DEMO_ACCESS);
      setError(null);
      setLoading(false);
      return { success: true } as AuthResult;
    }
    const response = await client.updateProfile(payload);
    if (response.success && response.data?.user) {
      setCurrentUser(response.data.user as UserProfile);
    } else {
      setError(response.errors?.[0] ?? "Profile update failed.");
    }
    return (response.data ?? {}) as AuthResult;
  }, [client]);

  return {
    token,
    currentUser,
    access,
    role: String(access?.role ?? currentUser?.role ?? "viewer"),
    permissions: Array.isArray(access?.permissions) ? access.permissions : Array.isArray(currentUser?.permissions) ? currentUser.permissions : [],
    loading,
    error,
    isAuthenticated: Boolean(token && currentUser),
    login,
    register,
    logout,
    refreshCurrentUser,
    updateProfile,
    refreshAccess,
    hasPermission: (permission: string) => Boolean(access?.access?.[permission] ?? access?.permissions?.includes(permission)),
    hasAnyPermission: (permissions: string[]) => permissions.some((permission) => Boolean(access?.access?.[permission] ?? access?.permissions?.includes(permission))),
    hasAllPermissions: (permissions: string[]) => permissions.every((permission) => Boolean(access?.access?.[permission] ?? access?.permissions?.includes(permission))),
  };
}
