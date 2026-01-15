# Synegious Flows: Research Engine Guide

Welcome to the **Synegious Flows** Research Engine. This guide will help you operate the platform for autonomous quantitative discovery and alpha validation.

---

## 1. Installation

### Docker (Recommended)
The easiest way to run Synegious is via Docker. This ensures all dependencies (Python libraries, Node.js frontend, and the C++ based MNX components) are correctly configured.

```bash
docker-compose up --build -d
```

### Local Development
If you need to modify the Python core or React frontend locally:

**Backend:**
```bash
pip install -r requirements.txt
python -m nmie.cli.serve
```

**Frontend:**
```bash
cd apps/graphdash_new
npm install
npm run dev
```

---

## 2. Configuration

### Alpaca Integration
To see live P&L and connect to the broker bridge, you must provide your Alpaca Paper Trading credentials in a `.env` file at the root:

```env
APCA_API_KEY_ID=PK...
APCA_API_SECRET_KEY=...
```

### Market Data
The platform defaults to `yfinance` for free, live market data. If you wish to use Polygon.io or IEX for higher-fidelity data, you can add their keys to the `.env` as well.

---

## 3. Core Workflows

### 🏎️ Running the Nexus
1. Navigate to the **Synegious Nexus** tab.
2. Select your ticker universe (e.g., `["SPY", "QQQ", "TSLA"]`).
3. Click **Start Nexus**.
4. The engine will detect the market regime and automatically validate strategies from the library.

### 🧪 Model Training (MNX)
To train the LightGBM ranker on custom features:
```bash
python -m nmie.cli.train_models --ticker SPY --start 2023-01-01
```

### 📈 Portfolio Intelligence
Use the **Deep Intelligence** tab to calculate Markowitz-optimal weights. The platform fetches real historical returns to build the covariance matrix, moving away from simulated assumptions.

---

## 4. Troubleshooting

- **Container Start Failure**: Ensure ports `8000` (API) and `5173` (Frontend) are not being used by other applications.
- **No P&L Data**: Verify your Alpaca keys are valid and that you are using "Paper Trading" credentials.
- **Frontend Build Errors**: If building from source, ensure you have Node.js 18+ installed.

---

## 🛡️ Support & Maintenance
This project is an advanced quantitative research tool. Always verify strategy performance in a sandbox environment before deploying capital.
