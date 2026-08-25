import { Navigate, Outlet } from 'react-router-dom';
import { useAuthStore } from '../../features/auth/authStore';

export function ProtectedRoute() {
const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  if (!isAuthenticated) {
    // Leitet nicht eingeloggte User zur Login-Seite um
    return <Navigate to="/login" replace />;
  }

  // Rendert die untergeordneten geschützten Routen
  return <Outlet />;
}