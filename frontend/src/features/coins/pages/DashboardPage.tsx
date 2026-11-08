import { useEffect, useState } from 'react';
import { useAuthStore } from '../../auth/authStore';
import { TrendingUp, TrendingDown, BellPlus, Wifi, WifiOff } from 'lucide-react';
import { CreateAlertModal } from '../../alerts/CreateAlertModal';
import { useCryptoTickers } from '../useCryptoWebSocket';
interface CoinData {
  symbol: string;
  name: string;
  price: number;
  change24h: number;
}

export function DashboardPage() {
  const [selectedCoin, setSelectedCoin] = useState<{ symbol: string; price: number } | null>(null);
  const token = useAuthStore((state) => state.isAuthenticated);
  /*   const [coins, setCoins] = useState<Record<string, CoinData>>({
      BTCUSDT: { symbol: 'BTCUSDT', name: 'Bitcoin', price: 95000, change24h: 2.4 },
      ETHUSDT: { symbol: 'ETHUSDT', name: 'Ethereum', price: 3400, change24h: -1.2 },
      SOLUSDT: { symbol: 'SOLUSDT', name: 'Solana', price: 180, change24h: 5.8 },
    }); */
  // WebSocket-Verbindung zu FastAPI
  const coins = useCryptoTickers();
  const isConnected = Object.keys(coins).length > 0;
  return (
    <div className="w-full min-h-screen bg-[#0d1117] text-slate-100 p-4 md:p-8">
      <div className="w-full max-w-[1600px] mx-auto space-y-6">

        {/* Top Bar / Status */}
        <div className="flex items-center justify-between bg-slate-900/60 backdrop-blur-md p-5 rounded-xl border border-slate-800">
          <div>
            <h1 className="text-xl font-bold text-white">Crypto Market Overview</h1>
            <p className="text-xs text-slate-400 mt-0.5">Echtzeit-Kurse direkt über dein FastAPI Backend</p>
          </div>
          <div className="flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium border border-slate-700 bg-slate-950">
            {Object.keys(coins).length > 0 ? (
              <>
                <Wifi className="w-3.5 h-3.5 text-emerald-400 animate-pulse" />
                <span className="text-emerald-400">Live Verbunden</span>
              </>
            ) : (
              <>
                <WifiOff className="w-3.5 h-3.5 text-rose-400" />
                <span className="text-rose-400">Getrennt</span>
              </>
            )}
          </div>
        </div>

        {/* Tabellenansicht */}
        <div className="w-full overflow-x-auto rounded-xl border border-slate-800/80 bg-slate-900/30 backdrop-blur-md shadow-xl">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-800 text-[13px] font-semibold text-slate-400">
                <th className="py-3.5 px-4">Asset</th>
                <th className="py-3.5 px-4 text-right">Preis</th>
                <th className="py-3.5 px-4 text-right">24h Änderung</th>
                <th className="py-3.5 px-4 text-center">Aktion</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50 text-sm font-medium">
              {Object.keys(coins).length === 0 ? (
                <tr>
                  <td colSpan={4} className="py-12 text-center text-slate-500">
                    <p className="font-semibold">Keine aktiven Coins empfangen.</p>
                    <p className="text-xs mt-1 text-slate-600">Starte einen Bot im Backend, damit Symbole per WebSocket eintreffen.</p>
                  </td>
                </tr>
              ) : (
                // 🚀 Hier korrigiert: Sauberes Mapping ohne doppelte Klammern
                Object.entries(coins).map(([symbol, coinData]) => {
                  const isPositive = coinData.change24h >= 0;
                    console.log(coinData)
                  return (
                    <tr key={symbol} className="hover:bg-slate-800/40 transition-colors group cursor-pointer">

                      {/* Asset Name */}
                      <td className="py-4 px-4 flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center font-bold text-xs text-amber-400 border border-slate-700">
                          {symbol.slice(0, 3)}
                        </div>
                        <div>
                          <span className="font-bold text-white block">{symbol}</span>
                          <span className="text-xs text-slate-400">{coinData.pair}</span>
                       </div>
                      </td>

                      {/* Live Preis */}
                      <td className="py-4 px-4 text-right font-mono font-semibold text-white">
                        ${coinData.price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 4 })}
                      </td>

                      {/* 24h Änderung (Live vom Backend!) */}
                      <td className="py-4 px-4 text-right font-mono">
                        <span className={`inline-flex items-center gap-1 font-bold ${isPositive ? 'text-emerald-400' : 'text-rose-500'}`}>
                          {isPositive ? '+' : ''}{coinData.change24h.toFixed(2)}%
                        </span>
                      </td>

                      {/* Alarm-Button */}
                      <td className="py-4 px-4 text-center">
                        <button
                          onClick={() => setSelectedCoin({ symbol, price: coinData.price })}
                          className="p-2 bg-slate-800 hover:bg-emerald-500 hover:text-slate-950 text-slate-300 rounded-lg transition-all border border-slate-700/60 inline-flex items-center justify-center"
                        >
                          <BellPlus className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Modal für Alarm-Erstellung */}
        <CreateAlertModal
          isOpen={selectedCoin !== null}
          initialSymbol={selectedCoin?.symbol}
          onClose={() => setSelectedCoin(null)}
        />
      </div>
    </div>
  );
}