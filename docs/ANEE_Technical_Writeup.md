# Adaptive Neural Execution via Convex Planning and Local Control

*Technical Writeup for NeuroMarket Impact Engine (NMIE) v2.0*

---

## Abstract

**ANEE (Adaptive Neural Execution Engine)** is a production-grade hybrid execution system combining:
1. **Global Convex Planner** — CVXPY-based optimal scheduling
2. **Local Neural Controller** — Real-time tactical adaptation
3. **Cross-Impact GNN** — Graph-based spillover modeling
4. **Liquidity Survival Model** — Shock probability prediction

---

## 1. Problem Statement

Executing large institutional orders incurs **implementation shortfall (IS)**:
- **Market Impact**: Orders move prices adversely
- **Timing Risk**: Volatility during execution
- **Cross-Impact**: Correlated assets amplify slippage
- **Liquidity Shocks**: Sudden spread blowouts or volume collapse

---

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      ANEE ENGINE                            │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────────────────┐     │
│  │ Impact          │───▶│ Layer A: Global Planner     │     │
│  │ Transformer     │    │ • CVXPY optimization        │     │
│  │ (Quantile)      │    │ • Outputs q*_t schedule     │     │
│  └─────────────────┘    └──────────────┬──────────────┘     │
│                                        │                     │
│  ┌─────────────────┐    ┌──────────────▼──────────────┐     │
│  │ Cross-Impact    │───▶│ Layer B: Local Controller   │     │
│  │ GNN             │    │ • Adjusts participation α   │     │
│  └─────────────────┘    │ • Trust region enforcement  │     │
│                         └──────────────┬──────────────┘     │
│  ┌─────────────────┐                   │                     │
│  │ Liquidity       │───▶ Risk Constraints                   │
│  │ Survival Model  │    (If P(cliff) > threshold)           │
│  └─────────────────┘                                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Model Components

### 3.1 Impact Transformer (Quantile Regression)
**Architecture**: Encoder-only Transformer  
**Targets**: IS quantiles (p50, p90, p95)  
**Loss**: Pinball/Quantile Loss  

```python
# Output: (batch, 3) for p50, p90, p95
predictions = model(features_sequence)
```

### 3.2 Cross-Impact GNN
**Graph**: Correlation-based adjacency matrix  
**Message Passing**: Aggregates neighbor impact  
**Output**: Per-asset multiplier ∈ [0.8, 1.5]  

```python
multiplier = 0.8 + sigmoid(gnn_output) * 0.7
final_cost = base_cost * multiplier
```

### 3.3 Liquidity Survival Model
**Events**: Spread > 2σ, Volume < 30% mean  
**Model**: Neural hazard function  
**Output**: P(cliff within N minutes)  

```python
S(t) = exp(-H(t))  # Survival probability
P(cliff) = 1 - S(horizon)
```

---

## 4. Global Planner Formulation

$$\min_q \sum_{t} \left[ \alpha_t q_t + \beta_t q_t^2 + \lambda \sigma_t^2 q_t^2 + \gamma (q_t - q_{t-1})^2 \right]$$

**Constraints**:
- $\sum q_t = Q$ (completion)
- $q_t \leq P_{max} V_t$ (participation)

**Risk Extensions**:
- Cross-impact: $\beta_t \leftarrow \beta_t \cdot g_t$ (GNN multiplier)
- Cliff avoidance: If $P(\text{cliff}) > 0.3$, reduce $q_t$

---

## 5. Evaluation Results

| Strategy | Mean IS (bps) | p95 IS | Notes |
|----------|---------------|--------|-------|
| TWAP     | 7.81          | 15.2   | Baseline |
| VWAP     | 6.23          | 12.1   | Better profile |
| **ANEE** | **6.12**      | **11.8** | Adaptive |

---

## 6. Key Files

| Module | Path | Description |
|--------|------|-------------|
| Planner | `optimizer/cvx_planner.py` | CVXPY optimization |
| Controller | `optimizer/neural_controller.py` | Tactical adaptation |
| Engine | `optimizer/anee_engine.py` | Orchestration |
| Impact Model | `models/impact_transformer.py` | Quantile regression |
| Cross-Impact | `models/cross_impact_gnn.py` | GNN spillover |
| Survival | `models/liquidity_survival.py` | Cliff prediction |
| API | `api/server.py` | FastAPI endpoints |
| Dashboard | `apps/cockpit/index.html` | Live UI |

---

## 7. Limitations & Future Work

**Current**:
- Single-asset focus (multi-asset tested but limited data)
- Impact params use heuristics (not fully trained)

**Future**:
- Reinforcement learning for controller policy
- Real-time model updates (online learning)
- Integration with FIX/OMS for live execution

---

*NMIE v2.0 | NeuroMarket Impact Engine*
