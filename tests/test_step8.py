from nmie.labeling.cross_impact_graph import build_correlation_graph, compute_cross_impact_multiplier
from nmie.models.cross_impact_gnn import CrossImpactPredictor, GNNConfig
from nmie.labeling.liquidity_labels import detect_liquidity_events, create_survival_labels
from nmie.models.liquidity_survival import LiquiditySurvivalPredictor, SurvivalConfig
from nmie.store.feature_store import FeatureStore
import numpy as np

def test_cross_impact():
    print("=== Testing Cross-Impact GNN ===")
    
    store = FeatureStore()
    
    # Load sample data
    bars_spy = store.load_bars("SPY", "2025-12-01")
    
    if bars_spy.is_empty():
        print("No data available for testing")
        return
        
    # Build mock graph with single ticker
    bars_dict = {"SPY": bars_spy}
    graph = build_correlation_graph(bars_dict)
    
    print(f"Graph: {graph.n_nodes} nodes")
    print(f"Adjacency shape: {graph.adjacency.shape}")
    
    # Test GNN prediction
    config = GNNConfig(n_node_features=8)
    predictor = CrossImpactPredictor(config)
    
    # Mock features
    node_features = np.random.randn(graph.n_nodes, 8).astype(np.float32)
    multipliers = predictor.predict(node_features, graph.adjacency)
    
    print(f"Multipliers: {multipliers}")
    print(f"Range: [{multipliers.min():.2f}, {multipliers.max():.2f}]")

def test_liquidity_survival():
    print("\n=== Testing Liquidity Survival Model ===")
    
    store = FeatureStore()
    bars = store.load_bars("SPY", "2025-12-01")
    
    if bars.is_empty():
        print("No data available")
        return
        
    # Detect events
    events = detect_liquidity_events(bars)
    print(f"Detected {len(events)} liquidity events")
    
    for e in events[:5]:
        print(f"  {e.event_type}: severity={e.severity:.2f}")
        
    # Create survival labels
    labels = create_survival_labels(bars)
    print(f"Survival labels: {labels.height} rows")
    
    # Test model
    config = SurvivalConfig(input_dim=8)
    predictor = LiquiditySurvivalPredictor(config)
    
    # Mock prediction
    X = np.random.randn(10, 8).astype(np.float32)
    probs = predictor.predict_cliff_probability(X, horizon=30)
    
    print(f"Cliff probabilities (sample): {probs}")
    print(f"Range: [{probs.min():.3f}, {probs.max():.3f}]")

if __name__ == "__main__":
    test_cross_impact()
    test_liquidity_survival()
