import { NAV_ITEMS } from "../api/endpoints";
import type { ConfigResponseData } from "../types/api";

interface SidebarProps {
  activePage: string;
  onSelectPage: (page: string) => void;
  config: ConfigResponseData | null;
}

export function Sidebar({ activePage, onSelectPage, config }: SidebarProps) {
  const enabledModules = config?.feature_flags ? Object.values(config.feature_flags).filter(Boolean).length : 0;

  return (
    <aside className="sidebar">
      <div className="sidebar__panel">
        <div className="section">
          <strong>Workspace</strong>
          <span>{config?.default_brand ?? "wenzel_partner"}</span>
        </div>
        <div className="section" style={{ marginTop: 16 }}>
          <span className="badge badge-neutral">{enabledModules} enabled modules</span>
        </div>
      </div>
      <nav className="sidebar__nav">
        {NAV_ITEMS.map((item) => (
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
