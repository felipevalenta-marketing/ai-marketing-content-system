import { FormEvent, useEffect, useState } from "react";
import type { ApiClient } from "../api/client";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { EmptyState } from "../components/EmptyState";
import { SectionHeader } from "../components/SectionHeader";
import { Badge } from "../components/Badge";
import { useAuth } from "../hooks/useAuth";
import type { UserProfile } from "../types/api";

interface ProfileProps {
  client: ApiClient;
  auth: ReturnType<typeof useAuth>;
  onNavigate: (page: string) => void;
}

export function Profile({ auth, onNavigate }: ProfileProps) {
  const [displayName, setDisplayName] = useState("");
  const [settingsText, setSettingsText] = useState("{}");
  const [users, setUsers] = useState<UserProfile[]>([]);
  const [usersError, setUsersError] = useState("");
  const user = auth.currentUser;
  const organizationIds = Array.isArray(user?.organizations) ? user?.organizations : [];

  useEffect(() => {
    setDisplayName(String(user?.display_name ?? ""));
    setSettingsText(JSON.stringify(user?.settings ?? {}, null, 2));
  }, [user]);

  useEffect(() => {
    if (!auth.hasAnyPermission(["user:manage", "admin:all"])) {
      return;
    }
    void client.listUsers().then((response) => {
      if (response.success && response.data?.users) {
        setUsers(response.data.users as UserProfile[]);
        setUsersError("");
      } else {
        setUsers([]);
        setUsersError(response.errors?.[0] ?? "Unable to load users.");
      }
    });
  }, [auth.currentUser?.user_id, auth.permissions.join("|"), auth.role, client]);

  if (!user) {
    return (
      <Card>
        <EmptyState title="No profile loaded" description="Log in to view your account profile." action={<Button type="button" variant="primary" onClick={() => onNavigate("login")}>Go to login</Button>} />
      </Card>
    );
  }

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    let parsedSettings: Record<string, unknown> = {};
    try {
      parsedSettings = settingsText.trim() ? (JSON.parse(settingsText) as Record<string, unknown>) : {};
    } catch {
      parsedSettings = user.settings ?? {};
    }
    await auth.updateProfile({
      display_name: displayName,
      settings: parsedSettings,
    });
  };

  const handleRoleChange = async (userId: string, role: string) => {
    const response = await client.updateUserRole(userId, role);
    if (response.success) {
      const refreshed = await client.listUsers();
      if (refreshed.success && refreshed.data?.users) {
        setUsers(refreshed.data.users as UserProfile[]);
      }
    }
  };

  return (
    <Card>
      <SectionHeader title="Profile" description="Review and update your account details." />
      <div className="grid-2">
        <div className="stack">
          <p><strong>Email:</strong> {user.email ?? "-"}</p>
          <p><strong>Status:</strong> {user.status ?? "active"}</p>
          <p><strong>Created:</strong> {user.created_at ?? "-"}</p>
          <p><strong>Updated:</strong> {user.updated_at ?? "-"}</p>
          <div className="row wrap">
            <Badge tone="neutral">Org: {String(user.active_organization_id ?? "none")}</Badge>
            <Badge tone="neutral">Team: {String(user.active_team_id ?? "none")}</Badge>
          </div>
        </div>
        <form className="stack" onSubmit={handleSubmit}>
          <label className="field">
            <span>Display name</span>
            <input className="input" value={displayName} onChange={(event) => setDisplayName(event.target.value)} />
          </label>
          <label className="field">
            <span>Settings JSON</span>
            <textarea className="textarea" rows={8} value={settingsText} onChange={(event) => setSettingsText(event.target.value)} />
          </label>
          {auth.error ? <p className="error-text">{auth.error}</p> : null}
          <div className="button-row">
            <Button type="submit" variant="primary">
              Save Profile
            </Button>
            <Button type="button" variant="secondary" onClick={() => onNavigate("dashboard")}>
              Back to dashboard
            </Button>
          </div>
        </form>
      </div>
      {organizationIds.length ? (
        <Card>
          <SectionHeader title="Organizations" description="Organizations attached to this user account." />
          <div className="row wrap">
            {organizationIds.map((organizationId) => (
              <Badge key={organizationId} tone="neutral">{organizationId}</Badge>
            ))}
          </div>
        </Card>
      ) : null}
      {auth.hasAnyPermission(["user:manage", "admin:all"]) ? (
        <Card>
          <SectionHeader title="User Management" description="Manage user roles with RBAC permissions." />
          {usersError ? <p className="error-text">{usersError}</p> : null}
          {users.length ? (
            <div className="stack">
              {users.map((entry) => (
                <div key={String(entry.user_id)} className="metric-card">
                  <div className="row-between">
                    <div>
                      <strong>{entry.display_name ?? entry.email}</strong>
                      <p className="muted">{entry.email}</p>
                    </div>
                    <select
                      className="select"
                      value={String(entry.role ?? "viewer")}
                      onChange={async (event) => handleRoleChange(String(entry.user_id ?? ""), event.target.value)}
                      disabled={String(entry.user_id) === String(user.user_id)}
                    >
                      <option value="admin">admin</option>
                      <option value="manager">manager</option>
                      <option value="editor">editor</option>
                      <option value="viewer">viewer</option>
                      <option value="disabled">disabled</option>
                    </select>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState title="No users loaded" description="Users appear here when the API exposes list access." />
          )}
        </Card>
      ) : null}
    </Card>
  );
}
