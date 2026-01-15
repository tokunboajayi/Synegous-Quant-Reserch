
import sys
import os
sys.path.append(os.getcwd())
sys.path.append("..") # For mnx if needed

print(f"Python: {sys.executable}")
try:
    import lightgbm
    print("Direct import lightgbm: SUCCESS")
except ImportError as e:
    print(f"Direct import lightgbm: FAILED {e}")

try:
    from nmie.nmie.models import lgbm_impact
    print("Import nmie.models.lgbm_impact: SUCCESS")
except ImportError as e:
    print(f"Import nmie.models.lgbm_impact: FAILED {e}")
    # Inspect raw file
    with open("nmie/nmie/models/lgbm_impact.py") as f:
        print("Head of lgbm_impact.py:")
        print(f.read(300))
