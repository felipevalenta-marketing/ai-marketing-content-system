import { useEffect, useState } from "react";
import { isUnauthorizedResponse } from "../api/client";
import { DEMO_USER, IS_DEMO_MODE } from "../utils/demo";

type ProfileProps = {
  client: any;
  auth: any;
  onNavigate?: (page: string) => void;
};

type UserProfile = {
  id?: string;
  user_id?: string;
  email?: string;
  display_name?: string;
  name?: string;
  roles?: string[];
  permissions?: string[];
  organizations?: string[];
  teams?: string[];
};

function normalizeUser(payload: any): UserProfile | null {
  const candidate = payload?.data?.user ?? payload?.data ?? payload?.user ?? payload;
  if (!candidate || typeof candidate !== "object") {
    return null;
  }
  return candidate as UserProfile;
}

export function Profile({ client, auth, onNavigate }: ProfileProps) {
  const [profile, setProfile] = useState<UserProfile | null>(() => (IS_DEMO_MODE ? (DEMO_USER as UserProfile) : auth?.currentUser ?? null));
  const [isLoading, setIsLoading] = useState<boolean>(() => (!IS_DEMO_MODE ? !auth?.currentUser : false));
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (IS_DEMO_MODE) {
      setProfile(DEMO_USER as UserProfile);
      setIsLoading(false);
      setError(null);
      return;
    }
    let active = true;

    async function loadProfile() {
      if (!auth?.isAuthenticated || !client) {
        if (active) {
          setIsLoading(false);
        }
        return;
      }

      if (active) {
        setIsLoading(true);
        setError(null);
      }

      try {
        const response = await client.getCurrentUser();
        if (!response?.success) {
          const message = isUnauthorizedResponse(response) ? "Your session expired. Please log in again." : response?.errors?.[0] || "Unable to load profile.";
          throw new Error(message);
        }
        const nextProfile = normalizeUser(response);
        if (active && nextProfile) {
          setProfile(nextProfile);
        }
      } catch (loadError: any) {
        if (active) {
          setError(loadError?.message || "Unable to load profile.");
        }
      } finally {
        if (active) {
          setIsLoading(false);
        }
      }
    }

    loadProfile();

    return () => {
      active = false;
    };
  }, [auth?.isAuthenticated, client]);

  const currentUser = profile ?? auth?.currentUser ?? null;
  const organizationList = currentUser?.organizations ?? [];
  const teamList = currentUser?.teams ?? [];
  const permissionList = currentUser?.permissions ?? [];
  const roleList = currentUser?.roles ?? [];
  const displayName = currentUser?.display_name || currentUser?.name || currentUser?.email || "User";

  return (
    <div className="space-y-6">
      <header className="space-y-2">
        <h1 className="text-3xl font-bold text-slate-900">Profile</h1>
        <p className="text-sm text-slate-600">Review your authenticated account and access context.</p>
      </header>

      {isLoading ? (
        <div className="rounded-2xl border border-slate-200 bg-white p-6 text-sm text-slate-600">
          Loading profile...
        </div>
      ) : null}

      {error ? (
        <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
          <div className="font-semibold">Profile data unavailable</div>
          <div>{error}</div>
          <div className="mt-2 text-xs text-amber-800">
            Your session remains active. This is an optional profile fetch error.
          </div>
        </div>
      ) : null}

      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-900">{displayName}</h2>
        <p className="text-sm text-slate-600">{currentUser?.email || "No email available"}</p>

        <dl className="mt-6 grid gap-4 sm:grid-cols-2">
          <div>
            <dt className="text-xs uppercase tracking-wide text-slate-500">Roles</dt>
            <dd className="mt-1 text-sm text-slate-900">{roleList.length > 0 ? roleList.join(", ") : "None"}</dd>
          </div>
          <div>
            <dt className="text-xs uppercase tracking-wide text-slate-500">Permissions</dt>
            <dd className="mt-1 text-sm text-slate-900">
              {permissionList.length > 0 ? permissionList.join(", ") : "None"}
            </dd>
          </div>
          <div>
            <dt className="text-xs uppercase tracking-wide text-slate-500">Organizations</dt>
            <dd className="mt-1 text-sm text-slate-900">
              {organizationList.length > 0 ? organizationList.join(", ") : "None"}
            </dd>
          </div>
          <div>
            <dt className="text-xs uppercase tracking-wide text-slate-500">Teams</dt>
            <dd className="mt-1 text-sm text-slate-900">{teamList.length > 0 ? teamList.join(", ") : "None"}</dd>
          </div>
        </dl>

        <div className="mt-6 flex gap-3">
          {onNavigate ? (
            <button
              type="button"
              onClick={() => onNavigate("dashboard")}
              className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700"
            >
              Back to Dashboard
            </button>
          ) : null}
        </div>
      </section>
    </div>
  );
}

export default Profile;
