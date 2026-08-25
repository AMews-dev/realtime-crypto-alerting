import { Outlet } from 'react-router-dom';
import { Navbar } from './Navbar'; // <- Importiere deine Navbar

export function MainLayout() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      {/* Navbar oben anzeigen */}
      <Navbar />

      {/* Hier werden die geschützten Inhalts-Seiten (Dashboard, Alerts) gerendert */}
      <main className="max-w-7xl mx-auto p-6">
        <Outlet />
      </main>
    </div>
  );
}