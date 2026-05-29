import { FormEvent, useEffect, useState } from "react";
import type { ApiClient } from "../api/client";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { EmptyState } from "../components/EmptyState";
import { SectionHeader } from "../components/SectionHeader";
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
  const user = auth.currentUser;

  useEffect(() => {
    setDisplayName(String(user?.display_name ?? ""));
    setSettingsText(JSON.stringify(user?.settings ?? {}, null, 2));
  }, [user]);

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

  return (
    <Card>
      <SectionHeader title="Profile" description="Review and update your account details." />
      <div className="grid-2">
        <div className="stack">
          <p><strong>Email:</strong> {user.email ?? "-"}</p>
          <p><strong>Status:</strong> {user.status ?? "active"}</p>
          <p><strong>Created:</strong> {user.created_at ?? "-"}</p>
          <p><strong>Updated:</strong> {user.updated_at ?? "-"}</p>
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
    </Card>
  );
}
