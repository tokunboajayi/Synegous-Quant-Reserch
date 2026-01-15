import torch
import torch.nn as nn
import numpy as np
from typing import List, Tuple
from dataclasses import dataclass

@dataclass
class ModelConfig:
    input_dim: int = 8
    d_model: int = 64
    n_heads: int = 4
    n_layers: int = 2
    dropout: float = 0.1
    quantiles: List[float] = None
    
    def __post_init__(self):
        if self.quantiles is None:
            self.quantiles = [0.5, 0.9, 0.95]

class QuantileLoss(nn.Module):
    """Pinball loss for quantile regression."""
    def __init__(self, quantiles: List[float]):
        super().__init__()
        self.quantiles = quantiles
        
    def forward(self, preds: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        """
        preds: (batch, n_quantiles)
        targets: (batch,)
        """
        losses = []
        for i, q in enumerate(self.quantiles):
            pred = preds[:, i]
            diff = targets - pred
            loss = torch.max(q * diff, (q - 1) * diff)
            losses.append(loss.mean())
        return sum(losses) / len(losses)

class ImpactTransformer(nn.Module):
    """
    Transformer encoder for predicting IS quantiles.
    Input: Sequence of microstructure features
    Output: Quantiles of IS (p50, p90, p95)
    """
    def __init__(self, config: ModelConfig):
        super().__init__()
        self.config = config
        
        # Input projection
        self.input_proj = nn.Linear(config.input_dim, config.d_model)
        
        # Positional encoding
        self.pos_encoding = nn.Parameter(torch.randn(1, 100, config.d_model) * 0.01)
        
        # Transformer encoder
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=config.d_model,
            nhead=config.n_heads,
            dim_feedforward=config.d_model * 4,
            dropout=config.dropout,
            batch_first=True
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=config.n_layers)
        
        # Output head (one output per quantile)
        self.output_head = nn.Linear(config.d_model, len(config.quantiles))
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        x: (batch, seq_len, input_dim)
        returns: (batch, n_quantiles)
        """
        batch_size, seq_len, _ = x.shape
        
        # Project input
        x = self.input_proj(x)  # (batch, seq, d_model)
        
        # Add positional encoding
        x = x + self.pos_encoding[:, :seq_len, :]
        
        # Encode
        x = self.encoder(x)  # (batch, seq, d_model)
        
        # Pool (mean)
        x = x.mean(dim=1)  # (batch, d_model)
        
        # Predict quantiles
        out = self.output_head(x)  # (batch, n_quantiles)
        
        return out

class ImpactPredictor:
    """
    Wrapper for training and inference.
    """
    def __init__(self, config: ModelConfig = None):
        self.config = config or ModelConfig()
        self.model = ImpactTransformer(self.config)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        
    def train(self, 
              X_train: np.ndarray, 
              y_train: np.ndarray,
              epochs: int = 50,
              batch_size: int = 32,
              lr: float = 1e-3) -> List[float]:
        """
        Train the model.
        X_train: (n_samples, seq_len, input_dim)
        y_train: (n_samples,) - IS values
        """
        self.model.train()
        
        optimizer = torch.optim.Adam(self.model.parameters(), lr=lr)
        loss_fn = QuantileLoss(self.config.quantiles)
        
        X_t = torch.tensor(X_train, dtype=torch.float32).to(self.device)
        y_t = torch.tensor(y_train, dtype=torch.float32).to(self.device)
        
        n_samples = X_t.shape[0]
        losses = []
        
        for epoch in range(epochs):
            perm = torch.randperm(n_samples)
            epoch_loss = 0.0
            n_batches = 0
            
            for i in range(0, n_samples, batch_size):
                idx = perm[i:i+batch_size]
                x_batch = X_t[idx]
                y_batch = y_t[idx]
                
                optimizer.zero_grad()
                preds = self.model(x_batch)
                loss = loss_fn(preds, y_batch)
                loss.backward()
                optimizer.step()
                
                epoch_loss += loss.item()
                n_batches += 1
                
            avg_loss = epoch_loss / n_batches
            losses.append(avg_loss)
            
            if (epoch + 1) % 10 == 0:
                print(f"Epoch {epoch+1}/{epochs} - Loss: {avg_loss:.4f}")
                
        return losses
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Returns quantile predictions.
        X: (n_samples, seq_len, input_dim)
        returns: (n_samples, n_quantiles)
        """
        self.model.eval()
        with torch.no_grad():
            X_t = torch.tensor(X, dtype=torch.float32).to(self.device)
            preds = self.model(X_t).cpu().numpy()
        return preds
    
    def save(self, path: str):
        torch.save({
            "config": self.config,
            "state_dict": self.model.state_dict()
        }, path)
        
    def load(self, path: str):
        checkpoint = torch.load(path, map_location=self.device)
        self.config = checkpoint["config"]
        self.model = ImpactTransformer(self.config)
        self.model.load_state_dict(checkpoint["state_dict"])
        self.model.to(self.device)
