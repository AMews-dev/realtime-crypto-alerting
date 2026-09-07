import { Outlet, useNavigate } from 'react-router-dom';
import { Navbar } from './Navbar'; // <- Importiere deine Navbar
import { useState, useEffect } from 'react';

export function MainLayout() {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const checkSessionAndBackend = async () => {
      try {
        // try to get acces token
        const response = await fetch("http://localhost:8000/api/auth/refresh", {
          method: "POST",
          credentials: "include"
        });
        if (response.ok) {
          setIsAuthenticated(true)
        } else {
          setIsAuthenticated(false)
          navigate("login")
        }
      } catch (err) {
        console.error("backend nicht ereichbar", err)
        setIsAuthenticated(false)
        navigate("login")
      };
    }
      checkSessionAndBackend();
    }, [navigate]);

  if (isAuthenticated === null) {
    return (
      <div className="min-h-screen w-full bg-slate-950 flex items-center justify-center text-slate-400">
        <p className="animate-pulse">Verbindung zum Server wird geprüft...</p>
      </div>
    );
  }

  return (
    // min-h-screen und w-full zwingen das Layout auf 100% Breite & Höhe
    <div className="min-h-screen w-full bg-slate-950 text-slate-100 flex flex-col">
      {/* Navbar spannt sich über die volle Breite */}
      <Navbar />

      {/* Hauptinhalt nimmt 100% der restlichen Fläche ein */}
      <main className="flex-1 w-full flex flex-col">
        <Outlet />
      </main>
    </div>
  );
}