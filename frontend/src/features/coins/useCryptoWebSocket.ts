import { useEffect, useState } from "react";

export function useCryptoPrices() {
  const [prices, setPrices] = useState<Record<string, number>>({});

  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8000/ws/prices");

    ws.onopen = () => {
      console.log("🟢 WebSocket verbunden");
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "PRICE_UPDATE" && data.symbol && data.price) {
          setPrices((prev) => ({
            ...prev,
            [data.symbol]: data.price,
          }));
        } else if (data.symbol && data.price) {
          setPrices((prev) => ({
            ...prev,
            [data.symbol]: data.price,
          }));
        }
      } catch (err) {
        console.error("Fehler beim Parsen:", err);
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

  return prices;
}