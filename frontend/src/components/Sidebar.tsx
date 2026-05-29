import { NAV_ITEMS } from "../api/endpoints";
import type { ConfigResponseData } from "../types/api";
import { Badge } from "./Badge";
import { getRoleLabel, getRoleTone } from "../utils/formatting";

interface SidebarProps {
  activePage: string;
  onSelectPage: (page: string) => void;
  config: ConfigResponseData | null;
  role: string;
  permissions: string[];
}

export function Sidebar({ activePage, onSelectPage, config, role, permissions }: SidebarProps) {
  const enabledModules = config?.feature_flags ? Object.values(config.feature_flags).filter(Boolean).length : 0;
  const hasPermission = (permission?: string) => {
    if (!permission) return true;
    return permissions.includes("admin:all") || permissions.includes(permission);
  };
  const hasAnyPermission = (anyOf?: string[]) => {
    if (!anyOf || !anyOf.length) return true;
    return permissions.includes("admin:all") || anyOf.some((permission) => permissions.includes(permission));
  };
  const visibleItems = NAV_ITEMS.filter((item) => hasPermission((item as any).permission) && hasAnyPermission((item as any).anyOf)).filter((item) => {
    if (item.id === "dashboard") return true;
    if (!permissions.length) return item.id === "dashboard";
    return true;
  });

  return (
    <aside className="sidebar">
      <div className="sidebar__panel">
        <div className="section">
          <strong>Workspace</strong>
          <span>{config?.default_brand ?? "wenzel_partner"}</span>
          <Badge tone={getRoleTone(role)}>{getRoleLabel(role)}</Badge>
        </div>
        <div className="section" style={{ marginTop: 16 }}>
          <span className="badge badge-neutral">{enabledModules} enabled modules</span>
        </div>
      </div>
      <nav className="sidebar__nav">
        {visibleItems.map((item) => (
          <button
            key={item.id}
            type="button"
            className={`sidebar__button ${activePage === item.id ? "is-active" : ""}`}
            onClick={() => onSelectPage(item.id)}
          >
            <div>
              <strong>{item.label}</strong>
            </div>
            <span>{item.hint}</span>
          </button>
        ))}
      </nav>
    </aside>
  );
}
