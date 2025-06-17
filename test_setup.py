"""
Simple test to verify the setup works
"""

try:
    from src.liquidplanner_mcp.config import get_config
    from src.liquidplanner_mcp.server import LiquidPlannerMCPServer
    
    print("✅ All imports successful!")
    print("✅ Configuration loading works!")
    
    # Test config (will use defaults/env vars)
    config = get_config("testing")
    print(f"✅ Test config loaded: {config.liquidplanner_base_url}")
    
except Exception as e:
    print(f"❌ Setup error: {e}")
