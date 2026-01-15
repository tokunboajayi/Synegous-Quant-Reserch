import torch
import torch.nn as nn
import numpy as np
from typing import List, Tuple
from dataclasses import dataclass

@dataclass
class SurvivalConfig:
    input_dim: int = 8
    hidden_dim: int = 32
    n_layers: int = 2
    max_time: int = 60  # Max prediction horizon

class NeuralSurvival(nn.Module):
    """
    Neural survival model predicting hazard function.
    
    Output: Cumulative hazard at each time step
    P(event by time t) = 1 - exp(-H(t))
    """
    def __init__(self, config: SurvivalConfig):
        super().__init__()
        self.config = config
        
        # Feature encoder
        layers = [nn.Linear(config.input_dim, config.hidden_dim), nn.ReLU()]
        for _ in range(config.n_layers - 1):
            layers.extend([
                nn.Linear(config.hidden_dim, config.hidden_dim),
                nn.ReLU(),
                nn.Dropout(0.1)
            ])
        self.encoder = nn.Sequential(*layers)
        
        # Hazard output (per time step)
        self.hazard_head = nn.Sequential(
            nn.Linear(config.hidden_dim, config.max_time),
            nn.Softplus()  # Hazard must be positive
        )
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        x: (batch, input_dim)
        returns: (batch, max_time) - cumulative hazard at each t
        """
        h = self.encoder(x)
        hazards = self.hazard_head(h)  # Instantaneous hazard
        
        # Cumulative hazard
        cum_hazard = torch.cumsum(hazards, dim=-1)
        
        return cum_hazard
    
    def survival_probability(self, x: torch.Tensor) -> torch.Tensor:
        """Returns S(t) = P(T > t) = exp(-H(t))"""
        cum_hazard = self.forward(x)
        return torch.exp(-cum_hazard)
    
    def event_probability(self, x: torch.Tensor, t: int) -> torch.Tensor:
        """Returns P(event by time t)"""
        survival = self.survival_probability(x)
        return 1 - survival[:, t-1] if t > 0 else torch.zeros(x.shape[0])

class NegLogLikLoss(nn.Module):
    """Negative log-likelihood loss for survival models."""
    def __init__(self):
        super().__init__()
        
    def forward(self, 
                cum_hazard: torch.Tensor, 
                time: torch.Tensor, 
                event: torch.Tensor) -> torch.Tensor:
        """
        cum_hazard: (batch, max_time)
        time: (batch,) - observed time
        event: (batch,) - 1 if event occurred, 0 if censored
        """
        batch_size = cum_hazard.shape[0]
        
        # Get hazard at observed time
        time_idx = time.long().clamp(0, cum_hazard.shape[1] - 1)
        
        # Gather cumulative hazard at time t
        H_t = cum_hazard.gather(1, time_idx.unsqueeze(1)).squeeze(1)
        
        # Log-likelihood
        # For events: log(h(t)) - H(t)
        # For censored: -H(t)
        # Simplified: -H(t) + event * log(h(t))
        
        # Approximate instantaneous hazard
        h_t = cum_hazard.gather(1, time_idx.unsqueeze(1)).squeeze(1)
        if time_idx.max() > 0:
            h_prev = cum_hazard.gather(1, (time_idx - 1).clamp(min=0).unsqueeze(1)).squeeze(1)
            h_t = h_t - h_prev
            
        log_h = torch.log(h_t.clamp(min=1e-8))
        
        loss = -(-H_t + event * log_h)
        
        return loss.mean()

class LiquiditySurvivalPredictor:
    """Wrapper for training and inference."""
    def __init__(self, config: SurvivalConfig = None):
        self.config = config or SurvivalConfig()
        self.model = NeuralSurvival(self.config)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        
    def train(self,
              X: np.ndarray,
              times: np.ndarray,
              events: np.ndarray,
              epochs: int = 50,
              lr: float = 1e-3) -> List[float]:
        """
        Train survival model.
        X: (n_samples, input_dim)
        times: (n_samples,) - observed times
        events: (n_samples,) - event indicators
        """
        self.model.train()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=lr)
        loss_fn = NegLogLikLoss()
        
        X_t = torch.tensor(X, dtype=torch.float32).to(self.device)
        times_t = torch.tensor(times, dtype=torch.float32).to(self.device)
        events_t = torch.tensor(events, dtype=torch.float32).to(self.device)
        
        losses = []
        for epoch in range(epochs):
            optimizer.zero_grad()
            cum_hazard = self.model(X_t)
            loss = loss_fn(cum_hazard, times_t, events_t)
            loss.backward()
            optimizer.step()
            losses.append(loss.item())
            
            if (epoch + 1) % 10 == 0:
                print(f"Epoch {epoch+1}/{epochs} - Loss: {loss.item():.4f}")
                
        return losses
    
    def predict_cliff_probability(self, X: np.ndarray, horizon: int = 30) -> np.ndarray:
        """
        Predict P(liquidity cliff within horizon).
        
        Returns: (n_samples,) probabilities
        """
        self.model.eval()
        with torch.no_grad():
            X_t = torch.tensor(X, dtype=torch.float32).to(self.device)
            survival = self.model.survival_probability(X_t)
            
            # P(event by t) = 1 - S(t)
            horizon_idx = min(horizon - 1, survival.shape[1] - 1)
            prob = 1 - survival[:, horizon_idx]
            
            return prob.cpu().numpy()
            
    def save(self, path: str):
        torch.save({
            "config": self.config,
            "state_dict": self.model.state_dict()
        }, path)
        
    def load(self, path: str):
        checkpoint = torch.load(path, map_location=self.device)
        self.config = checkpoint["config"]
        self.model = NeuralSurvival(self.config)
        self.model.load_state_dict(checkpoint["state_dict"])
        self.model.to(self.device)
