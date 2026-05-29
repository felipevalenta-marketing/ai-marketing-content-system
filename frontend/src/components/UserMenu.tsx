import type { UserProfile } from "../types/api";
import { Badge } from "./Badge";
import { Button } from "./Button";
import { Card } from "./Card";

interface UserMenuProps {
  user: UserProfile | null;
  onProfile: () => void;
  onLogout: () => void;
}

export function UserMenu({ user, onProfile, onLogout }: UserMenuProps) {
  if (!user) {
    return null;
  }

  return (
    <Card>
      <div className="stack">
        <div className="row-between">
          <div>
            <strong>{user.display_name || user.email || "User"}</strong>
            <p className="muted">{user.email}</p>
          </div>
          <Badge tone={user.status === "inactive" ? "warning" : user.status === "suspended" ? "error" : "success"}>{String(user.status ?? "active")}</Badge>
        </div>
        <div className="button-row">
          <Button type="button" variant="secondary" onClick={onProfile}>
            Profile
          </Button>
          <Button type="button" variant="secondary" onClick={onLogout}>
            Logout
          </Button>
        </div>
      </div>
    </Card>
  );
}
