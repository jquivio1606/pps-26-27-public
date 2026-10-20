import { useEffect } from "react";
import { HashRouter, Navigate, Route, Routes, useLocation } from "react-router-dom";

import { ToastProvider } from "./context/ToastContext";
import { AuthProvider } from "./context/AuthContext";
import { UIProvider } from "./context/UIContext";

import Header from "./components/Header";
import Footer from "./components/Footer";
import ProtectedRoute from "./components/ProtectedRoute";
import ToastStack from "./components/ToastStack";
import MovieModal from "./components/MovieModal";
import AuthModal from "./components/AuthModal";
import BookingModal from "./components/BookingModal";

import HomePage from "./pages/HomePage";
import ShowtimesPage from "./pages/ShowtimesPage";
import TicketsPage from "./pages/TicketsPage";
import AdminPage from "./pages/AdminPage";
import ManageTicketsPage from "./pages/ManageTicketsPage";
import UsersPage from "./pages/UsersPage";
import SystemPage from "./pages/SystemPage";
import DashboardPage from "./pages/DashboardPage";

function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "auto" });
  }, [pathname]);
  return null;
}

export default function App() {
  return (
    <ToastProvider>
      <AuthProvider>
        <UIProvider>
          <HashRouter>
            <ScrollToTop />
            <Header />
            <main className="ca-main">
              <Routes>
                <Route path="/" element={<HomePage />} />
                <Route path="/funciones" element={<ShowtimesPage />} />
                <Route
                  path="/mis-entradas"
                  element={
                    <ProtectedRoute message="Para ver tus entradas, inicia sesión.">
                      <TicketsPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/dashboard"
                  element={
                    <ProtectedRoute
                      roles={["manager", "admin"]}
                      message="Solo el personal puede ver las estadísticas."
                    >
                      <DashboardPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/admin"
                  element={
                    <ProtectedRoute
                      roles={["manager", "admin"]}
                      message="Acceso restringido: solo personal de la casa."
                    >
                      <AdminPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/admin/entradas"
                  element={
                    <ProtectedRoute
                      roles={["manager", "admin"]}
                      message="Acceso restringido: solo personal de la casa."
                    >
                      <ManageTicketsPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/admin/usuarios"
                  element={
                    <ProtectedRoute
                      admin
                      message="Solo el administrador puede gestionar usuarios."
                    >
                      <UsersPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/admin/sistema"
                  element={
                    <ProtectedRoute
                      admin
                      message="Solo el administrador puede ver el sistema."
                    >
                      <SystemPage />
                    </ProtectedRoute>
                  }
                />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </main>
            <Footer />

            <MovieModal />
            <AuthModal />
            <BookingModal />
            <ToastStack />
          </HashRouter>
        </UIProvider>
      </AuthProvider>
    </ToastProvider>
  );
}
