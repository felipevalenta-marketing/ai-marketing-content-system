import type { UserProfile } from "../types/api";
import { useState } from "react";
import { Badge } from "./Badge";
import { Button } from "./Button";
import { Card } from "./Card";
import { getRoleTone, getRoleLabel } from "../utils/formatting";
import { IS_DEMO_MODE } from "../utils/demo";

interface UserMenuProps {
  user: UserProfile | null;
  role: string;
  permissions?: string[];
  organizations?: string[];
  teams?: string[];
  roles?: string[];
  onProfile: () => void;
  onLogout: () => void;
}

export function UserMenu({ user, role, permissions = [], organizations = [], teams = [], roles = [], onProfile, onLogout }: UserMenuProps) {
  const [open, setOpen] = useState(false);

  if (!user) {
    return null;
  }

  if (IS_DEMO_MODE) {
    return null;
  }

  return (
    <div className="user-menu">
      <Button type="button" variant="secondary" className="user-menu__trigger" onClick={() => setOpen((value) => !value)}>
        {user.display_name || user.email || "User"}
      </Button>
      {open ? (
        <Card className="user-menu__panel">
          <div className="stack">
            <div className="row-between">
              <div>
                <strong>{user.display_name || user.email || "User"}</strong>
                <p className="muted">{user.email}</p>
              </div>
              <Badge tone={user.status === "inactive" ? "warning" : user.status === "suspended" ? "error" : "success"}>{String(user.status ?? "active")}</Badge>
            </div>
            <div className="row-between">
              <Badge tone={getRoleTone(role || user.role)}>{getRoleLabel(role || user.role)}</Badge>
              <span className="muted">{permissions.length} permissions</span>
            </div>
            <div className="row wrap">
              <span className="muted">{organizations.length} organizations</span>
              <span className="muted">{teams.length} teams</span>
              <span className="muted">{roles.length} roles</span>
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
      ) : null}
    </div>
  );
}
