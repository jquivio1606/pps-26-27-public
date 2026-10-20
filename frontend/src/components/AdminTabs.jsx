import { NavLink } from "react-router-dom";

import { useAuth } from "../context/AuthContext";

/**
 * Pestañas del panel de gestión.
 *
 * El jefe (manager) ve "Catálogo" y "Entradas" (puede cancelar reservas);
 * el informático (admin) ve además "Usuarios" y "Sistema".
 */
export default function AdminTabs() {
  const { isAdmin } = useAuth();

  const tabs = [
    { to: "/admin", label: "Catálogo", end: true },
    { to: "/admin/entradas", label: "Entradas" },
    ...(isAdmin
      ? [
          { to: "/admin/usuarios", label: "Usuarios" },
          { to: "/admin/sistema", label: "Sistema" },
        ]
      : []),
  ];

  return (
    <div className="ca-tabs ca-tabs-nav" role="tablist">
      {tabs.map((tab) => (
        <NavLink
          key={tab.to}
          to={tab.to}
          end={tab.end}
          role="tab"
          className={({ isActive }) => `ca-tab${isActive ? " active" : ""}`}
        >
          {tab.label}
        </NavLink>
      ))}
    </div>
  );
}
