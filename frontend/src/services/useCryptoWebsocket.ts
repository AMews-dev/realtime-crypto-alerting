import { useEffect, useState } from "react";

export interface CoinTickerInfo {
  price: number;
  change24h: number;
}

export function useCryptoWebSocket() {
  const [prices, setPrices] = useState<Record<string, CoinTickerInfo>>({});
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8000/ws/prices");

    ws.onopen = () => setIsConnected(true);

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        // Prüft das PRICE_UPDATE Signal
        if (data.type === "PRICE_UPDATE" && data.symbol && data.price) {
          setPrices((prev) => ({
            ...prev,
            [data.symbol]: {
              price: data.price,
              // Falls change24h mitgeschickt wird, nutzen wir es. Sonst behalten wir den alten Wert oder 0.
              change24h: data.change24h !== undefined ? data.change24h : (prev[data.symbol]?.change24h || 0),
            },
          }));
        }
      } catch (err) {
        console.error("WS Parse Error:", err);
      }
    };

    ws.onclose = () => setIsConnected(false);

    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      } else if (ws.readyState === WebSocket.CONNECTING) {
        ws.onopen = () => ws.close();
      }
    };
  }, []);

  return { prices, isConnected };
}