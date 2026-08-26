import { useEffect, useState } from 'react';
import { useAuthStore } from '../../auth/authStore';
import { TrendingUp, TrendingDown, BellPlus, Wifi, WifiOff } from 'lucide-react';

interface CoinData {
  symbol: string;
  name: string;
  price: number;
  change24h: number;
}

export function DashboardPage() {
  const token = useAuthStore((state) => state.isAuthenticated);
  const [coins, setCoins] = useState<Record<string, CoinData>>({
    BTCUSDT: { symbol: 'BTCUSDT', name: 'Bitcoin', price: 95000, change24h: 2.4 },
    ETHUSDT: { symbol: 'ETHUSDT', name: 'Ethereum', price: 3400, change24h: -1.2 },
    SOLUSDT: { symbol: 'SOLUSDT', name: 'Solana', price: 180, change24h: 5.8 },
  });
  const [isConnected, setIsConnected] = useState(false);

  // WebSocket-Verbindung zu FastAPI
  useEffect(() => {
    if (!token) return;

    // Ersetze die URL durch deine FastAPI WebSocket Route
    const ws = new WebSocket(`ws://localhost:8000/ws/coins?token=${token}`);

    ws.onopen = () => setIsConnected(true);
    ws.onclose = () => setIsConnected(false);
    ws.onerror = () => setIsConnected(false);

    ws.onmessage = (event) => {
      const updatedData: CoinData = JSON.parse(event.data);
      setCoins((prevCoins) => ({
        ...prevCoins,
        [updatedData.symbol]: {
          ...prevCoins[updatedData.symbol],
          ...updatedData,
        },
      }));
    };

    return () => ws.close();
  }, [token]);

  return (
    <div className="space-y-6">
      {/* Top Bar / Status */}
      <div className="flex items-center justify-between bg-slate-900/60 backdrop-blur-md p-6 rounded-2xl border border-slate-800">
        <div>
          <h1 className="text-2xl font-bold text-white">Crypto Market Overview</h1>
          <p className="text-sm text-slate-400 mt-1">Echtzeit-Kurse direkt über dein FastAPI Backend</p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium border border-slate-700 bg-slate-950">
          {isConnected ? (
            <>
              <Wifi className="w-4 h-4 text-emerald-400 animate-pulse" />
              <span className="text-emerald-400">Live Verbunden</span>
            </>
          ) : (
            <>
              <WifiOff className="w-4 h-4 text-rose-400" />
              <span className="text-rose-400">Getrennt</span>
            </>
          )}
        </div>
      </div>

      {/* Coin Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {Object.values(coins).map((coin) => {
          const isPositive = coin.change24h >= 0;

          return (
            <div
              key={coin.symbol}
              className="bg-slate-900/40 backdrop-blur-md border border-slate-800/80 rounded-2xl p-6 hover:border-slate-700 transition-all shadow-xl relative overflow-hidden group"
            >
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="text-lg font-bold text-white">{coin.name}</h3>
                  <span className="text-xs font-mono text-slate-400">{coin.symbol}</span>
                </div>
                <div
                  className={`flex items-center gap-1 text-xs font-bold px-2.5 py-1 rounded-lg ${
                    isPositive
                      ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                      : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                  }`}
                >
                  {isPositive ? <TrendingUp className="w-3.5 h-3.5" /> : <TrendingDown className="w-3.5 h-3.5" />}
                  <span>{isPositive ? `+${coin.change24h}%` : `${coin.change24h}%`}</span>
                </div>
              </div>

              {/* Price Display */}
              <div className="mt-6 mb-4">
                <span className="text-xs text-slate-500 block mb-1">Aktueller Kurs</span>
                <span className="text-3xl font-extrabold font-mono text-white tracking-tight">
                  ${coin.price.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                </span>
              </div>

              {/* Action Button */}
              <button className="w-full mt-2 bg-slate-800 hover:bg-emerald-500 hover:text-slate-950 text-slate-200 font-medium py-2 rounded-xl transition-all duration-200 flex items-center justify-center gap-2 text-sm border border-slate-700/60">
                <BellPlus className="w-4 h-4" />
                <span>Alarm setzen</span>
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}