import { NavLink } from "react-router-dom";
import { LayoutDashboard, Users, Clock, Send, Settings, Sparkles, X } from "lucide-react";

interface SidebarProps {
  open: boolean;
  onClose: () => void;
}

const NAV_ITEMS = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/leads", label: "Leads", icon: Users },
  { to: "/pending", label: "Pending Approval", icon: Clock },
  { to: "/sent", label: "Sent", icon: Send },
];

export function Sidebar({ open, onClose }: SidebarProps) {
  return (
    <>
      {open && <div className="sidebar-scrim" onClick={onClose} aria-hidden="true" />}
      <nav
        className={`sidebar ${open ? "sidebar-open" : ""}`}
        aria-label="Primary navigation"
      >
        <div className="sidebar-header">
          <div className="sidebar-logo">
            <Sparkles size={18} />
            <span>AI Lead Agent</span>
          </div>
          <button className="sidebar-close" onClick={onClose} aria-label="Close menu">
            <X size={18} />
          </button>
        </div>

        <ul className="sidebar-nav">
          {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
            <li key={to}>
              <NavLink
                to={to}
                onClick={onClose}
                className={({ isActive }) => `sidebar-link ${isActive ? "sidebar-link-active" : ""}`}
              >
                <Icon size={17} />
                {label}
              </NavLink>
            </li>
          ))}
        </ul>

        <div className="sidebar-footer">
          <NavLink
            to="/settings"
            onClick={onClose}
            className={({ isActive }) => `sidebar-link ${isActive ? "sidebar-link-active" : ""}`}
          >
            <Settings size={17} />
            Settings
          </NavLink>
        </div>
      </nav>
    </>
  );
}
