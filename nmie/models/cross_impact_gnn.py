import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import List, Tuple
from dataclasses import dataclass

@dataclass
class GNNConfig:
    n_node_features: int = 8
    hidden_dim: int = 32
    n_layers: int = 2
    dropout: float = 0.1

class GraphConvLayer(nn.Module):
    """Simple graph convolution layer."""
    def __init__(self, in_dim: int, out_dim: int):
        super().__init__()
        self.linear = nn.Linear(in_dim, out_dim)
        self.self_linear = nn.Linear(in_dim, out_dim)
        
    def forward(self, x: torch.Tensor, adj: torch.Tensor) -> torch.Tensor:
        """
        x: (batch, n_nodes, in_dim)
        adj: (batch, n_nodes, n_nodes) - adjacency matrix
        """
        # Aggregate neighbors
        neighbor_agg = torch.bmm(adj, x)  # (batch, n_nodes, in_dim)
        
        # Combine self + neighbor
        out = self.linear(neighbor_agg) + self.self_linear(x)
        return F.relu(out)

class CrossImpactGNN(nn.Module):
    """
    Graph Neural Network for predicting cross-impact multipliers.
    
    Input: Node features (microstructure stats) + Adjacency matrix
    Output: Per-node cross-impact multiplier
    """
    def __init__(self, config: GNNConfig):
        super().__init__()
        self.config = config
        
        # Input projection
        self.input_proj = nn.Linear(config.n_node_features, config.hidden_dim)
        
        # GNN layers
        self.gnn_layers = nn.ModuleList([
            GraphConvLayer(config.hidden_dim, config.hidden_dim)
            for _ in range(config.n_layers)
        ])
        
        # Output head (multiplier in [0, 1] range, then scaled)
        self.output_head = nn.Sequential(
            nn.Linear(config.hidden_dim, 16),
            nn.ReLU(),
            nn.Linear(16, 1),
            nn.Sigmoid()  # Output in [0, 1]
        )
        
    def forward(self, x: torch.Tensor, adj: torch.Tensor) -> torch.Tensor:
        """
        x: (batch, n_nodes, n_features)
        adj: (batch, n_nodes, n_nodes)
        
        Returns: (batch, n_nodes) - multipliers scaled to [0.8, 1.5]
        """
        # Project
        h = self.input_proj(x)  # (batch, n_nodes, hidden)
        
        # GNN layers
        for layer in self.gnn_layers:
            h = layer(h, adj)
            
        # Per-node output
        out = self.output_head(h).squeeze(-1)  # (batch, n_nodes)
        
        # Scale to [0.8, 1.5]
        multipliers = 0.8 + out * 0.7
        
        return multipliers

class CrossImpactPredictor:
    """Wrapper for training and inference."""
    def __init__(self, config: GNNConfig = None):
        self.config = config or GNNConfig()
        self.model = CrossImpactGNN(self.config)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        
    def predict(self, node_features: np.ndarray, adj_matrix: np.ndarray) -> np.ndarray:
        """
        Predict cross-impact multipliers.
        
        node_features: (n_nodes, n_features)
        adj_matrix: (n_nodes, n_nodes)
        
        Returns: (n_nodes,) multipliers
        """
        self.model.eval()
        with torch.no_grad():
            x = torch.tensor(node_features, dtype=torch.float32).unsqueeze(0).to(self.device)
            adj = torch.tensor(adj_matrix, dtype=torch.float32).unsqueeze(0).to(self.device)
            
            # Normalize adjacency (add self-loops, degree normalize)
            adj = adj + torch.eye(adj.shape[1], device=self.device).unsqueeze(0)
            deg = adj.sum(dim=-1, keepdim=True).clamp(min=1)
            adj = adj / deg
            
            out = self.model(x, adj)
            return out.squeeze(0).cpu().numpy()
            
    def save(self, path: str):
        torch.save({
            "config": self.config,
            "state_dict": self.model.state_dict()
        }, path)
        
    def load(self, path: str):
        checkpoint = torch.load(path, map_location=self.device)
        self.config = checkpoint["config"]
        self.model = CrossImpactGNN(self.config)
        self.model.load_state_dict(checkpoint["state_dict"])
        self.model.to(self.device)
