import { useState, useEffect } from 'react';
import { BellPlus, X, PlusCircle, AlertCircle } from 'lucide-react';
import type { CreateAlertDTO, AlertResponse, AlarmDirection, AlarmType } from '../../services/alertsApi';
import { createAlert } from '../../services/alertsApi';

interface CreateAlertModalProps {
    isOpen: boolean;
    initialSymbol?: string | null;
    onClose: () => void;
    onSuccess?: () => void;
}

export function CreateAlertModal({
    isOpen,
    initialSymbol,
    onClose,
    onSuccess,
}: CreateAlertModalProps) {
    const [coinSymbol, setCoinSymbol] = useState(initialSymbol || '');
    const [alarmType, setAlarmType] = useState<AlarmType>('ABSOLUTE_PRICE');
    const [direction, setDirection] = useState<AlarmDirection>('ABOVE');
    const [targetPrice, setTargetPrice] = useState('');
    const [targetPercentage, setTargetPercentage] = useState('');
    const [timeframeMinutes, setTimeframeMinutes] = useState('15');
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);

    // Sync initialSymbol wenn sich die Modal-Props ändern
    useEffect(() => {
        if (initialSymbol) {
            setCoinSymbol(initialSymbol);
        }
    }, [initialSymbol]);

    if (!isOpen) return null;

    const handleCreateAlert = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);
        setLoading(true);

        try {
            const response = await fetch('http://localhost:8000/api/alerts', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({
                    symbol: coinSymbol,
                    alarm_type: alarmType,
                    direction: direction,
                    target_price: alarmType === 'ABSOLUTE_PRICE' ? parseFloat(targetPrice) : null,
                    target_percentage: alarmType !== 'ABSOLUTE_PRICE' ? parseFloat(targetPercentage) : null,
                    timeframe_minutes: alarmType === 'TIMEFRAME_PERCENTAGE' ? parseInt(timeframeMinutes) : null,
                }),
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.detail || 'Fehler beim Erstellen des Alarms.');
            }

            if (onSuccess) onSuccess();
            onClose();
        } catch (err: any) {
            setError(err.message || 'Ein unerwarteter Fehler ist aufgetreten.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4">
            <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-2xl relative animate-in fade-in zoom-in-95 duration-150">

                {/* Header */}
                <div className="flex items-center justify-between border-b border-slate-800/60 pb-3 mb-5">
                    <h2 className="text-base font-bold text-white flex items-center gap-2">
                        <PlusCircle className="w-5 h-5 text-indigo-400" />
                        Neuen Alarm anlegen
                    </h2>
                    <button
                        onClick={onClose}
                        className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-colors"
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Error Alert */}
                {error && (
                    <div className="mb-4 p-3 bg-rose-500/10 border border-rose-500/20 text-rose-400 rounded-lg text-xs flex items-center gap-2">
                        <AlertCircle className="w-4 h-4 shrink-0" />
                        <span>{error}</span>
                    </div>
                )}

                {/* Formular */}
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

                    <div className="pt-2 flex gap-3">
                        <button
                            type="button"
                            onClick={onClose}
                            className="w-1/2 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold rounded-lg transition-all text-xs"
                        >
                            Abbrechen
                        </button>
                        <button
                            type="submit"
                            disabled={loading}
                            className="w-1/2 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-semibold rounded-lg shadow-lg shadow-indigo-600/20 transition-all flex items-center justify-center gap-2 text-xs"
                        >
                            <PlusCircle className="w-4 h-4" /> {loading ? 'Speichere...' : 'Alarm Speichern'}
                        </button>
                    </div>
                </form>

            </div>
        </div>
    );
}