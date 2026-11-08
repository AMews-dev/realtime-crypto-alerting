import { useEffect, useState } from "react";

export interface CoinTickerInfo {
  price: number;
  change24h: number;
  pair: string
}


export function useCryptoTickers() {
  const [tickers, setTickers] = useState<Record<string, CoinTickerInfo>>({});

  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8000/ws/prices");

    ws.onopen = () => {
      console.log("🟢 WebSocket verbunden");
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
            if (data.type === "PRICE_UPDATE" && data.symbol && data.price) {
          setTickers((prev) => ({
            ...prev,
            [data.symbol]: {
              price: data.price,
              // Falls change24h mitgeschickt wird, nutzen wir es. Sonst behalten wir den alten Wert oder 0.
              change24h: data.change24h !== undefined ? data.change24h : (prev[data.symbol]?.change24h || 0),
              pair: data.pair
            },
          }));
        }
      } catch (err) {
        console.error("WS Parse Error:", err);
      }
    };
    ws.onerror = (error) => {
      console.error("WebSocket Fehler:", error);
    };

    // 🚀 FIX: Abfangen des abgebrochenen Handshakes
    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      } else if (ws.readyState === WebSocket.CONNECTING) {
        // Falls React im Strict Mode unmountet, bevor die Verbindung steht:
        ws.onopen = () => ws.close();
      }
    };
  }, []);

  return tickers;
}