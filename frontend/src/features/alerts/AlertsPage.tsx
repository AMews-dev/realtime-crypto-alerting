import { useEffect, useState, type SyntheticEvent } from 'react';
import { useAuthStore } from '../auth/authStore';
import type { CreateAlertDTO, AlertResponse, AlarmDirection, AlarmType } from '../../services/alertsApi';
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
  Clock, ArrowUpRight,
  ArrowDownRight,
  ArrowUpDown
} from 'lucide-react';
import { customFetch, getAlerts } from '../../services/apiClient';


export function AlertsPage() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const [alerts, setAlerts] = useState<AlertResponse[]>([]);
  const [loading, setLoading] = useState(true);

  // Formular State
  const [coinSymbol, setCoinSymbol] = useState('BTCUSDT');
  const [alarmType, setAlarmType] = useState<AlarmType>('ABSOLUTE_PRICE');
  const [direction, setDirection] = useState<AlarmDirection>('ABOVE');
  const [targetPrice, setTargetPrice] = useState('95000');
  const [targetPercentage, setTargetPercentage] = useState('5');
  const [timeframeMinutes, setTimeframeMinutes] = useState('15');
  const [error, setError] = useState<string | null>(null);

  // Alarme von FastAPI abrufen
  const fetchAlerts = async () => {
    try {
      setLoading(true)
      const data = await getAlerts()
      setAlerts(data)
    } catch (err: any) {
      console.error('Fehler beim Laden der Alarme', err);
      setError(err.message || 'Fehler beim Laden der Alarme');
    } finally {
      setLoading(false);
    }
  };


  useEffect(() => {
    if (isAuthenticated) {
      fetchAlerts(); // 👈 Von getAlerts() zu fetchAlerts() geändert
    }
  }, [isAuthenticated]);

  // Neuen Alarm erstellen
  const handleCreateAlert = async (e: SyntheticEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);

    try {

      // Daten exakt für dein Postman-Schema aufbereiten
      const payload: CreateAlertDTO = {
        coin_symbol: coinSymbol.toUpperCase(), // z. B. "SOL" oder "BTC"
        alarm_type: alarmType,
        direction: direction,
        target_price: alarmType === 'ABSOLUTE_PRICE' ? parseFloat(targetPrice) : null,
        target_percentage: alarmType !== 'ABSOLUTE_PRICE' ? parseFloat(targetPercentage) : null,
        timeframe_minutes: alarmType === 'TIMEFRAME_PERCENTAGE' ? parseInt(timeframeMinutes, 10) : null,
      };
      console.log(payload)
      await createAlert(payload)
      // Liste neu laden und Formular zurücksetzen
      fetchAlerts();

      // Formular-Reset (Standards)
      setTargetPrice('95000');
      setTargetPercentage('5');
    } catch (err: any) {
      setError(err.message || "Alarm konnte nicht erstellt werden");
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
    <div className="w-full min-h-screen bg-[#0d1117] text-slate-100 p-4 md:p-8">
      <div className="w-full max-w-[1600px] mx-auto space-y-6">

        {/* Header */}
        <div className="flex items-center space-x-4 border-b border-slate-800 pb-5">
          <div className="p-3 bg-indigo-500/10 border border-indigo-500/20 rounded-xl text-indigo-400">
            <Bell className="w-7 h-7" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight">Preis-Alarme</h1>
            <p className="text-xs text-slate-400 mt-0.5">
              Erstelle und verwalte deine automatischen Benachrichtigungen in Echtzeit.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

          {/* Formular (Links) */}
       {/*    <div className="lg:col-span-1 bg-slate-900/40 backdrop-blur-md p-6 rounded-xl border border-slate-800/80 shadow-xl h-fit">
            <h2 className="text-base font-bold text-white mb-5 flex items-center gap-2 border-b border-slate-800/60 pb-3">
              <PlusCircle className="w-5 h-5 text-indigo-400" />
              Neuen Alarm anlegen
            </h2>

            {error && (
              <div className="mb-4 p-3 bg-rose-500/10 border border-rose-500/20 text-rose-400 rounded-lg text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <form onSubmit={handleCreateAlert} className="space-y-4 text-xs font-medium">
              <div>
                <label className="block text-slate-300 mb-1.5 font-semibold">
                  Crypto-Pair / Symbol
                </label>
                <input
                  type="text"
                  value={coinSymbol}
                  onChange={(e) => setCoinSymbol(e.target.value.toUpperCase())}
                  placeholder="z.B. BTCUSDT"
                  required
                  className="w-full px-3 py-2.5 bg-slate-950 border border-slate-800 rounded-lg text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500 transition-colors font-mono"
                />
              </div>

              <div>
                <label className="block text-slate-300 mb-1.5 font-semibold">
                  Alarm-Typ
                </label>
                <select
                  value={alarmType}
                  onChange={(e) => {
                    const newType = e.target.value as AlarmType;
                    setAlarmType(newType);
                    if (newType === 'TIMEFRAME_PERCENTAGE') setDirection('BOTH');
                  }}
                  className="w-full px-3 py-2.5 bg-slate-950 border border-slate-800 rounded-lg text-white focus:outline-none focus:border-indigo-500 transition-colors cursor-pointer"
                >
                  <option value="ABSOLUTE_PRICE">Fester Zielpreis ($)</option>
                  <option value="DYNAMIC_PERCENTAGE">Prozentuale Abweichung (%)</option>
                  <option value="TIMEFRAME_PERCENTAGE">% in Zeitfenster (Pump/Dump)</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-300 mb-1.5 font-semibold">
                  Richtung
                </label>
                <select
                  value={direction}
                  onChange={(e) => setDirection(e.target.value as AlarmDirection)}
                  className="w-full px-3 py-2.5 bg-slate-950 border border-slate-800 rounded-lg text-white focus:outline-none focus:border-indigo-500 transition-colors cursor-pointer"
                >
                  <option value="ABOVE">Steigt über / um (ABOVE)</option>
                  <option value="BELOW">Fällt unter / um (BELOW)</option>
                  <option value="BOTH">Beide Richtungen (BOTH)</option>
                </select>
              </div>

              {alarmType === 'ABSOLUTE_PRICE' && (
                <div>
                  <label className="block text-slate-300 mb-1.5 font-semibold">
                    Zielpreis ($)
                  </label>
                  <input
                    type="number"
                    step="any"
                    value={targetPrice}
                    onChange={(e) => setTargetPrice(e.target.value)}
                    placeholder="95000"
                    required
                    className="w-full px-3 py-2.5 bg-slate-950 border border-slate-800 rounded-lg text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500 transition-colors font-mono"
                  />
                </div>
              )}

              {alarmType !== 'ABSOLUTE_PRICE' && (
                <div>
                  <label className="block text-slate-300 mb-1.5 font-semibold">
                    Prozentwert (%)
                  </label>
                  <input
                    type="number"
                    step="any"
                    value={targetPercentage}
                    onChange={(e) => setTargetPercentage(e.target.value)}
                    placeholder="5"
                    required
                    className="w-full px-3 py-2.5 bg-slate-950 border border-slate-800 rounded-lg text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500 transition-colors font-mono"
                  />
                </div>
              )}

              {alarmType === 'TIMEFRAME_PERCENTAGE' && (
                <div>
                  <label className="block text-slate-300 mb-1.5 font-semibold">
                    Zeitfenster (Minuten)
                  </label>
                  <input
                    type="number"
                    value={timeframeMinutes}
                    onChange={(e) => setTimeframeMinutes(e.target.value)}
                    placeholder="15"
                    required
                    className="w-full px-3 py-2.5 bg-slate-950 border border-slate-800 rounded-lg text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500 transition-colors font-mono"
                  />
                </div>
              )}

              <button
                type="submit"
                className="w-full mt-2 py-2.5 px-4 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold rounded-lg shadow-lg shadow-indigo-600/20 transition-all flex items-center justify-center gap-2 text-sm"
              >
                <PlusCircle className="w-4 h-4" /> Alarm Speichern
              </button>
            </form>
          </div> */}

          {/* Liste (Rechts) */}
          <div className="lg:col-span-2 space-y-4">
            <h2 className="text-base font-bold text-white mb-4">
              Deine Alarme
            </h2>

            {loading ? (
              <div className="p-12 text-center text-slate-500 font-medium text-sm">Lade Alarme...</div>
            ) : alerts.length === 0 ? (
              <div className="p-12 text-center bg-slate-900/30 rounded-xl border border-slate-800/80 text-slate-500 text-sm">
                Keine Alarme vorhanden. Erstelle jetzt deinen ersten Alarm.
              </div>
            ) : (
              <div className="grid grid-cols-1 gap-3">
                {alerts.map((alert) => (
                  <div
                    key={alert.id}
                    className="bg-slate-900/40 backdrop-blur-md p-4 rounded-xl border border-slate-800/80 shadow-lg flex flex-col md:flex-row md:items-center justify-between gap-4 hover:border-slate-700/80 transition-colors"
                  >
                    <div className="space-y-2">
                      <div className="flex items-center gap-3">
                        <span className="text-base font-bold text-white font-mono">
                          {alert.coin_symbol}
                        </span>

                        <span
                          className={`inline-flex items-center gap-1 text-[11px] px-2.5 py-0.5 rounded-md font-bold font-mono ${alert.direction === 'BELOW'
                              ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                              : alert.direction === 'ABOVE'
                                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                                : 'bg-purple-500/10 text-purple-400 border border-purple-500/20'
                            }`}
                        >
                          {alert.direction === 'BELOW' && <ArrowDownRight className="w-3 h-3" />}
                          {alert.direction === 'ABOVE' && <ArrowUpRight className="w-3 h-3" />}
                          {alert.direction === 'BOTH' && <ArrowUpDown className="w-3 h-3" />}
                          {alert.direction}
                        </span>

                        {alert.is_triggered ? (
                          <span className="inline-flex items-center gap-1 text-[11px] px-2.5 py-0.5 rounded-md bg-amber-500/10 text-amber-400 border border-amber-500/20 font-medium">
                            <CheckCircle2 className="w-3 h-3" /> Ausgelöst
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-[11px] px-2.5 py-0.5 rounded-md bg-blue-500/10 text-blue-400 border border-blue-500/20 font-medium">
                            Aktiv
                          </span>
                        )}
                      </div>

                      <div className="flex flex-wrap items-center gap-4 text-xs text-slate-300">
                        {alert.target_price !== null && (
                          <div className="flex items-center gap-1.5">
                            <Target className="w-3.5 h-3.5 text-slate-500" />
                            <span>Zielpreis: <strong className="font-mono text-white">${alert.target_price}</strong></span>
                          </div>
                        )}

                        {alert.target_percentage !== null && (
                          <div className="flex items-center gap-1.5">
                            <Percent className="w-3.5 h-3.5 text-slate-500" />
                            <span>Prozent: <strong className="font-mono text-white">{alert.target_percentage}%</strong></span>
                          </div>
                        )}

                        {alert.timeframe_minutes !== null && (
                          <div className="flex items-center gap-1.5 text-indigo-400">
                            <Clock className="w-3.5 h-3.5" />
                            <span>Zeitfenster: <strong className="font-mono">{alert.timeframe_minutes} Min</strong></span>
                          </div>
                        )}
                      </div>

                      <div className="flex items-center gap-1.5 text-[11px] text-slate-500">
                        <Clock className="w-3 h-3" />
                        <span>Erstellt: {new Date(alert.created_at).toLocaleString('de-DE')}</span>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 self-end md:self-center">
                      <button
                        onClick={() => handleDeleteAlert(alert.id)}
                        className="p-2 text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 border border-transparent hover:border-rose-500/20 rounded-lg transition-all"
                        title="Alarm löschen"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

        </div>
      </div>
    </div>
  );
}
