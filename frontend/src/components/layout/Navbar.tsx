import { Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../features/auth/authStore';
import { Bell, LayoutDashboard, LogOut, Zap } from 'lucide-react';

export function Navbar() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <nav className="border-b border-slate-800 bg-slate-900/80 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 font-bold text-xl text-emerald-400">
            <Zap className="w-6 h-6 fill-emerald-400" />
            <span>CryptoAlerts</span>
          </Link>

          {/* Nav Links */}
          <div className="flex items-center gap-6">
            <Link
              to="/"
              className="flex items-center gap-2 text-slate-300 hover:text-emerald-400 font-medium transition-colors"
            >
              <LayoutDashboard className="w-4 h-4" />
              <span>Dashboard</span>
            </Link>
            <Link
              to="/alerts"
              className="flex items-center gap-2 text-slate-300 hover:text-emerald-400 font-medium transition-colors"
            >
              <Bell className="w-4 h-4" />
              <span>Meine Alarme</span>
            </Link>
          </div>

          {/* User Status & Logout */}
          <div className="flex items-center gap-4">
            {user && (
              <span className="text-sm text-slate-400 hidden sm:inline">
                {user.email}
              </span>
            )}
            <button
              onClick={handleLogout}
              className="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 text-slate-200 px-3.5 py-1.5 rounded-lg border border-slate-700 text-sm font-medium transition-all"
            >
              <LogOut className="w-4 h-4" />
              <span>Abmelden</span>
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
}