import { useEffect, useState, type SyntheticEvent } from 'react';
import { useAuthStore } from '../auth/authStore';
import { Bell, Trash2, PlusCircle, AlertCircle, CheckCircle2, TrendingDown, Target } from 'lucide-react';

interface AlertItem {
  id: string;
  symbol: string;
  type: 'PERCENTAGE_DROP' | 'TARGET_PRICE';
  value: number; // z. B. 5 (für 5%) oder 90000 (für $90k)
  created_at: string;
}

export function AlertsPage() {
  const token = useAuthStore((state) => state.token);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [loading, setLoading] = useState(true);
  
  // Formular State
  const [symbol, setSymbol] = useState('BTCUSDT');
  const [type, setType] = useState<'PERCENTAGE_DROP' | 'TARGET_PRICE'>('PERCENTAGE_DROP');
  const [value, setValue] = useState('5');
  const [error, setError] = useState<string | null>(null);

  // Alarme von FastAPI abrufen
  const fetchAlerts = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/alerts', {
        headers: { Authorization: `Bearer ${token}` },
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
  }, [token]);

  // Neuen Alarm erstellen
  const handleCreateAlert = async (e: SyntheticEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);

    try {
      const response = await fetch('http://localhost:8000/api/alerts', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          symbol,
          type,
          value: parseFloat(value),
        }),
      });

      if (!response.ok) {
        throw new Error('Alarm konnte nicht erstellt werden');
      }

      // Liste neu laden und Formular zurücksetzen
      fetchAlerts();
      setValue('5');
    } catch (err: any) {
      setError(err.message);
    }
  };

  // Alarm löschen
  const handleDeleteAlert = async (id: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/alerts/${id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.ok) {
        setAlerts((prev) => prev.filter((a) => a.id !== id));
      }
    } catch (err) {
      console.error('Löschen fehlgeschlagen', err);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
      
      {/* Linke Spalte: Formular zum Erstellen */}
      <div className="lg:col-span-1 bg-slate-900/60 backdrop-blur-md border border-slate-800 p-6 rounded-2xl h-fit shadow-xl">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2.5 bg-emerald-500/10 rounded-xl text-emerald-400">
            <PlusCircle className="w-5 h-5" />
          </div>
          <h2 className="text-xl font-bold text-white">Neuen Alarm anlegen</h2>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-rose-500/10 border border-rose-500/20 text-rose-400 rounded-xl text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleCreateAlert} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
              Cryptocurrency
            </label>
            <select
              value={symbol}
              onChange={(e) => setSymbol(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-white text-sm focus:outline-none focus:border-emerald-500"
            >
              <option value="BTCUSDT">Bitcoin (BTC/USDT)</option>
              <option value="ETHUSDT">Ethereum (ETH/USDT)</option>
              <option value="SOLUSDT">Solana (SOL/USDT)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
              Alarm-Typ
            </label>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => {
                  setType('PERCENTAGE_DROP');
                  setValue('5');
                }}
                className={`flex items-center justify-center gap-1.5 p-2.5 rounded-xl border text-xs font-semibold transition-all ${
                  type === 'PERCENTAGE_DROP'
                    ? 'bg-emerald-500/10 border-emerald-500 text-emerald-400'
                    : 'bg-slate-950 border-slate-800 text-slate-400'
                }`}
              >
                <TrendingDown className="w-3.5 h-3.5" />
                <span>% Abfall</span>
              </button>
              <button
                type="button"
                onClick={() => {
                  setType('TARGET_PRICE');
                  setValue('90000');
                }}
                className={`flex items-center justify-center gap-1.5 p-2.5 rounded-xl border text-xs font-semibold transition-all ${
                  type === 'TARGET_PRICE'
                    ? 'bg-emerald-500/10 border-emerald-500 text-emerald-400'
                    : 'bg-slate-950 border-slate-800 text-slate-400'
                }`}
              >
                <Target className="w-3.5 h-3.5" />
                <span>Zielpreis ($)</span>
              </button>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
              {type === 'PERCENTAGE_DROP' ? 'Prozentualer Abfall (%)' : 'Zielpreis in USD ($)'}
            </label>
            <input
              type="number"
              step="any"
              required
              value={value}
              onChange={(e) => setValue(e.target.value)}
              placeholder={type === 'PERCENTAGE_DROP' ? 'z. B. 5' : 'z. B. 95000'}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-white text-sm focus:outline-none focus:border-emerald-500"
            />
          </div>

          <button
            type="submit"
            className="w-full bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold py-3 rounded-xl transition-all shadow-lg shadow-emerald-500/20 text-sm mt-2"
          >
            Alarm Speichern
          </button>
        </form>
      </div>

      {/* Rechte Spalte: Aktive Alarme Liste */}
      <div className="lg:col-span-2 bg-slate-900/60 backdrop-blur-md border border-slate-800 p-6 rounded-2xl shadow-xl">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-violet-500/10 rounded-xl text-violet-400">
              <Bell className="w-5 h-5" />
            </div>
            <h2 className="text-xl font-bold text-white">Aktive Alarme</h2>
          </div>
          <span className="text-xs bg-slate-800 text-slate-300 font-mono px-2.5 py-1 rounded-full border border-slate-700">
            {alerts.length} Aktiv
          </span>
        </div>

        {loading ? (
          <p className="text-slate-500 text-sm">Lade Alarme...</p>
        ) : alerts.length === 0 ? (
          <div className="text-center py-12 border border-dashed border-slate-800 rounded-xl">
            <CheckCircle2 className="w-8 h-8 text-slate-600 mx-auto mb-2" />
            <p className="text-slate-400 text-sm">Keine aktiven Alarme vorhanden.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {alerts.map((alert) => (
              <div
                key={alert.id}
                className="flex items-center justify-between bg-slate-950 border border-slate-800/80 p-4 rounded-xl hover:border-slate-700 transition-all"
              >
                <div className="flex items-center gap-4">
                  <div className="p-2 bg-slate-900 rounded-lg text-slate-300 font-mono text-xs font-bold">
                    {alert.symbol}
                  </div>
                  <div>
                    <span className="text-sm font-semibold text-white block">
                      {alert.type === 'PERCENTAGE_DROP'
                        ? `Fällt um mindestens ${alert.value}%`
                        : `Erreicht Zielpreis von $${alert.value.toLocaleString()}`}
                    </span>
                    <span className="text-xs text-slate-500">
                      Typ: {alert.type === 'PERCENTAGE_DROP' ? 'Prozentual' : 'Absolut'}
                    </span>
                  </div>
                </div>

                <button
                  onClick={() => handleDeleteAlert(alert.id)}
                  className="p-2 text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition-colors"
                  title="Alarm löschen"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

    </div>
  );
}