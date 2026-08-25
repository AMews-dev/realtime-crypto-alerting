
import { ProtectedRoute } from './components/layout/ProtectedRoute'
import { MainLayout } from './components/layout/MainLayout'
import './App.css'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthPage } from './features/auth/pages/AuthPage';
import { AlertsPage } from './features/alerts/AlertsPage'
import { DashboardPage } from './features/coins/pages/DashboardPage'
function App() {

  return (
    <BrowserRouter>
      <Routes>
        {/* Öffentliche Routen (kein Login erforderlich) */}
       <Route path="/login" element={<AuthPage />} />
        <Route path="/register" element={<AuthPage />} />

        {/* Geschützte Routen (nur mit Valid Token erreichbar) */}
        <Route element={<ProtectedRoute />}>
         {  <Route element={<MainLayout />}>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/alerts" element={<AlertsPage />} />
          </Route> }
        </Route>

        {/* Fallback für unbekannte URLs -> Zurück zum Dashboard */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
