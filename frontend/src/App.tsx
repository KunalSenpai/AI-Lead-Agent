import {
  BrowserRouter,
  Routes,
  Route,
  Navigate,
  Outlet,
  useLocation,
} from "react-router-dom";

import { useEffect, useState } from "react";

import { AppShell } from "./components/layout/AppShell";
import { ToastProvider } from "./components/ui/Toast";

import { supabase } from "./lib/supabase";

import { Dashboard } from "./pages/Dashboard";
import { Leads } from "./pages/Leads";
import { AddLead } from "./pages/AddLead";
import { LeadDetail } from "./pages/LeadDetail";
import { Pending } from "./pages/Pending";
import { Sent } from "./pages/Sent";
import { Settings } from "./pages/Settings";
import { Login } from "./pages/Login";

const TITLES: Record<string, string> = {
  "/dashboard": "Dashboard",
  "/leads": "Leads",
  "/leads/new": "Add Lead",
  "/pending": "Pending Approval",
  "/sent": "Sent",
  "/settings": "Settings",
};

function pageTitle(pathname: string): string {
  if (TITLES[pathname]) return TITLES[pathname];

  if (/^\/leads\/\d+$/.test(pathname)) {
    return "Lead Detail";
  }

  if (pathname === "/login") {
    return "Login";
  }

  return "AI Lead Agent";
}

function ProtectedRoute() {
  const [loading, setLoading] = useState(true);
  const [authenticated, setAuthenticated] = useState(false);

  useEffect(() => {
    let mounted = true;

    async function checkSession() {
      const {
        data: { session },
      } = await supabase.auth.getSession();

      if (!mounted) return;

      setAuthenticated(Boolean(session));
      setLoading(false);
    }

    checkSession();

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(
      (_event, session) => {
        if (!mounted) return;

        setAuthenticated(Boolean(session));
        setLoading(false);
      }
    );

    return () => {
      mounted = false;
      subscription.unsubscribe();
    };
  }, []);

  if (loading) {
    return <div>Checking authentication...</div>;
  }

  if (!authenticated) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}

function Shell() {
  const location = useLocation();

  return (
    <AppShell title={pageTitle(location.pathname)}>
      <Routes>
        {/* Public route */}
        <Route path="/login" element={<Login />} />

        {/* Protected application routes */}
        <Route element={<ProtectedRoute />}>
          <Route
            path="/"
            element={<Navigate to="/dashboard" replace />}
          />

          <Route
            path="/dashboard"
            element={<Dashboard />}
          />

          <Route
            path="/leads"
            element={<Leads />}
          />

          <Route
            path="/leads/new"
            element={<AddLead />}
          />

          <Route
            path="/leads/:id"
            element={<LeadDetail />}
          />

          <Route
            path="/pending"
            element={<Pending />}
          />

          <Route
            path="/sent"
            element={<Sent />}
          />

          <Route
            path="/settings"
            element={<Settings />}
          />

          <Route
            path="*"
            element={<Navigate to="/dashboard" replace />}
          />
        </Route>
      </Routes>
    </AppShell>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <ToastProvider>
        <Shell />
      </ToastProvider>
    </BrowserRouter>
  );
}