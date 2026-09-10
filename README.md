# ⚡ Real-Time Crypto Monitoring & Automated Alert System

A high-performance, event-driven cryptocurrency dashboard built with **FastAPI**, **React (TypeScript)**, and **WebSockets**. The application streams real-time market data from Binance, manages custom user price alerts, and broadcasts instant notifications with sub-second latency.

---

## 🎯 Key Features

- **Real-Time Data Pipeline:** Asynchronous integration with Binance WebSockets processing live tick data.
- **Automated Price Alerts:** In-memory alert evaluation with persistent storage and trigger updates.
- **Scalable Bot Architecture:** Dynamic lifecycle management for isolated bot instances per trading pair.
- **Reactive UI:** Instant price and alert updates using React, custom Hooks, and WebSockets.
- **Resilient Infrastructure:** Automatic reconnect handling for both exchange streams and frontend clients.

---

## 🏗 System Architecture

The application uses an event-driven architecture designed for high throughput and decoupled components:

[ Binance WebSocket Stream ]
│
▼
[ Bot Instance ] ──► (In-Memory Alert Evaluation)
│
▼ (Puts event)
[ asyncio.Queue ]
│
▼ (Listens & Pops event)
[ BotManager ]
│
▼ (Broadcasts JSON)
[ FastAPI WebSocket Endpoint (/ws/prices) ]
│
▼
[ React Frontend (useCryptoWebSocket) ]


### Data Flow Explained:
1. **Exchange Ingestion:** Each `Bot` instance connects to Binance WebSockets and listens for live market prices.
2. **Alert Engine:** Incoming prices are compared against an in-memory RAM cache of active user alerts (`PriceAlarm`).
3. **Internal Pipeline:** Evaluated price events and triggered notifications are pushed to a central `asyncio.Queue`.
4. **Broadcast Manager:** The `BotManager` background task pops items from the queue and broadcasts them to all connected frontend clients over a persistent WebSocket connection.

---

## 🛠 Tech Stack

### Backend
- **Framework:** Python 3.11+, FastAPI
- **Async Runtime:** `asyncio` (Queues, Background Tasks, Lifespan Management)
- **Database & ORM:** PostgreSQL / SQLite, SQLAlchemy
- **Protocols:** WebSockets (`websockets` library)

### Frontend
- **Framework:** React 18+ with TypeScript
- **State & Communication:** Custom React Hooks, Native WebSocket API
- **Tooling:** Vite

---

## 💻 Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker

### 1. Repository Klonen & Datenbank (PostgreSQL)
```bash
git clone https://github.com/AMews-dev/realtime-crypto-alerting.git
cd dein-repo-name

# Startet die PostgreSQL-Datenbank im Hintergrund
docker compose up -d
```

### 2. Backend Setup
Clone the repository:
   ```bash
   cd realtime-crypto-alerting/backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   cd src
   python -m serverpackage.server
   ```
### 3. Frontend Setup
  ```bash
  cd ../frontend
  npm install
  npm run dev
  ```
Open http://localhost:5173 in your browser.

  
   
