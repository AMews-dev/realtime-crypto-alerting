import { useEffect, useState, type SyntheticEvent } from 'react';
import { useAuthStore } from '../auth/authStore';
import type {  CreateAlertDTO, AlertResponse } from '../../services/alertsApi';
import { createAlert } from '../../services/alertsApi';
import { 
  Bell, 
  Trash2, 
  PlusCircle, 
  AlertCircle, 
  CheckCircle2, 
  TrendingDown, 
  TrendingUp, 
  Target, 
  Percent, 
  Clock 
} from 'lucide-react';

export function AlertsPage() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const [alerts, setAlerts] = useState<AlertResponse[]>([]);
  const [loading, setLoading] = useState(true);
  
  // Formular State
  const [coinsymbol, set_Coinsymbol] = useState('SOL');
  const [type, setType] = useState<'PERCENTAGE_DROP' | 'TARGET_PRICE'>('PERCENTAGE_DROP');
  const [value, setValue] = useState('5');
  const [error, setError] = useState<string | null>(null);

  // Alarme von FastAPI abrufen
  const fetchAlerts = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/alerts', {
        credentials: "include"
      });
      if (response.ok) {
        const data = await response.json();
        setAlerts(data);
      }
    } catch (err) {
      console.error('Fehler beim Laden der Alarme', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, [isAuthenticated]);

  // Neuen Alarm erstellen
  const handleCreateAlert = async (e: SyntheticEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);

  try {
      const parsedValue = parseFloat(value);

      // Daten exakt für dein Postman-Schema aufbereiten
      const payload: CreateAlertDTO = {
        coin_symbol: coinsymbol, // z. B. "SOL" oder "BTC"
        is_active: true,
        activation_price: null,
        // Unterscheidung je nach gewähltem Alert-Typ:
        target_percentage: type === 'PERCENTAGE_DROP' ? parsedValue : null,
        target_price: type === 'TARGET_PRICE' ? parsedValue : null,
        direction: type === 'PERCENTAGE_DROP' ? 'DOWN' : 'UP',
      };
      console.log(payload)
      await createAlert(payload)
      // Liste neu laden und Formular zurücksetzen
      fetchAlerts();
      setValue('5');
    } catch (err: any) {
      setError(err.message ||"Alarm konnte nicht erstellt werden");
    }
  };

  // Alarm löschen
  const handleDeleteAlert = async (id: number) => {
    try {
      const response = await fetch(`http://localhost:8000/api/alerts/${id}`, {
        method: 'DELETE',
        credentials: "include"
      });

      if (response.ok) {
        setAlerts((prev) => prev.filter((a) => a.id !== id));
      }
    } catch (err) {
      console.error('Löschen fehlgeschlagen', err);
    }
  };

 return (
    <div className="max-w-6xl mx-auto p-6 space-y-8">
      {/* Header */}
      <div className="flex items-center space-x-3 border-b pb-4 border-gray-200 dark:border-gray-800">
        <Bell className="w-8 h-8 text-indigo-600 dark:text-indigo-400" />
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Preis-Alarme</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Erstelle und verwalte deine automatischen Benachrichtigungen.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Formular-Spalte */}
        <div className="lg:col-span-1 bg-white dark:bg-gray-900 p-6 rounded-xl border border-gray-200 dark:border-gray-800 shadow-sm h-fit">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <PlusCircle className="w-5 h-5 text-indigo-500" /> Neuen Alarm anlegen
          </h2>

          {error && (
            <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 rounded-lg text-sm flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleCreateAlert} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Crypto-Pair / Symbol
              </label>
              <input
                type="text"
                value={coinsymbol}
                onChange={(e) => set_Coinsymbol(e.target.value.toUpperCase())}
                placeholder="z.B. BTCUSDT, SOL"
                required
                className="w-full px-3 py-2 border rounded-lg border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500 outline-none"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Alarm-Typ
              </label>
              <select
                value={type}
                onChange={(e) => setType(e.target.value as 'PERCENTAGE_DROP' | 'TARGET_PRICE')}
                className="w-full px-3 py-2 border rounded-lg border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500 outline-none"
              >
                <option value="PERCENTAGE_DROP">Prozentualer Abfall (%)</option>
                <option value="TARGET_PRICE">Ziel-Preis ($)</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {type === 'PERCENTAGE_DROP' ? 'Prozentwert (%)' : 'Zielpreis ($)'}
              </label>
              <input
                type="number"
                step="any"
                value={value}
                onChange={(e) => setValue(e.target.value)}
                placeholder={type === 'PERCENTAGE_DROP' ? 'z.B. 5' : 'z.B. 95000'}
                required
                className="w-full px-3 py-2 border rounded-lg border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500 outline-none"
              />
            </div>

            <button
              type="submit"
              className="w-full py-2 px-4 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded-lg shadow transition-colors flex items-center justify-center gap-2"
            >
              <PlusCircle className="w-4 h-4" /> Alarm Speichern
            </button>
          </form>
        </div>

        {/* Listen-Spalte */}
        <div className="lg:col-span-2 space-y-4">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Aktive & Vergangene Alarme
          </h2>

          {loading ? (
            <div className="p-8 text-center text-gray-500">Alarme werden geladen...</div>
          ) : alerts.length === 0 ? (
            <div className="p-8 text-center bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 text-gray-500">
              Noch keine Alarme vorhanden. Erstelle deinen ersten Alarm auf der linken Seite.
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4">
              {alerts.map((alert) => (
                <div
                  key={alert.id}
                  className="bg-white dark:bg-gray-900 p-5 rounded-xl border border-gray-200 dark:border-gray-800 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4"
                >
                  <div className="space-y-2">
                    {/* Header der Karte: Symbol + Badges */}
                    <div className="flex items-center gap-3">
                      <span className="text-lg font-bold text-gray-900 dark:text-white">
                        {alert.coin_symbol}
                      </span>

                      {/* Direction Badge */}
                      <span
                        className={`inline-flex items-center gap-1 text-xs px-2.5 py-0.5 rounded-full font-medium ${
                          alert.direction === 'DOWN'
                            ? 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-400'
                            : 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-400'
                        }`}
                      >
                        {alert.direction === 'DOWN' ? (
                          <TrendingDown className="w-3 h-3" />
                        ) : (
                          <TrendingUp className="w-3 h-3" />
                        )}
                        {alert.direction}
                      </span>

                      {/* Triggered Badge */}
                      {alert.is_triggered ? (
                        <span className="inline-flex items-center gap-1 text-xs px-2.5 py-0.5 rounded-full bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-400 font-medium">
                          <CheckCircle2 className="w-3 h-3" /> Ausgelöst
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-xs px-2.5 py-0.5 rounded-full bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-400 font-medium">
                          Aktiv
                        </span>
                      )}
                    </div>

                    {/* Alarm-Details (Ziel-Preis oder Prozent) */}
                    <div className="flex flex-wrap items-center gap-4 text-sm text-gray-600 dark:text-gray-300">
                      {alert.target_percentage !== null && (
                        <div className="flex items-center gap-1">
                          <Percent className="w-4 h-4 text-gray-400" />
                          <span>Ziel-Abfall: <strong>{alert.target_percentage}%</strong></span>
                        </div>
                      )}

                      {alert.target_price !== null && (
                        <div className="flex items-center gap-1">
                          <Target className="w-4 h-4 text-gray-400" />
                          <span>Ziel-Preis: <strong>${alert.target_price}</strong></span>
                        </div>
                      )}

                      {alert.activation_price !== null && (
                        <div className="text-xs text-gray-400">
                          (Startpreis: ${alert.activation_price})
                        </div>
                      )}
                    </div>

                    {/* Datumsanzeige */}
                    <div className="flex items-center gap-1 text-xs text-gray-400">
                      <Clock className="w-3 h-3" />
                      <span>Erstellt am: {new Date(alert.created_at).toLocaleString('de-DE')}</span>
                    </div>
                  </div>

                  {/* Aktionen */}
                  <div className="flex items-center gap-2 self-end md:self-center">
                    <button
                      onClick={() => handleDeleteAlert(alert.id)}
                      className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                      title="Alarm löschen"
                    >
                      <Trash2 className="w-5 h-5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}