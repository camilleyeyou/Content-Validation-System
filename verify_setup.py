#!/usr/bin/env python3
"""
Verify cost tracking setup
Run from project root: python3 verify_setup.py
"""

import sys
from pathlib import Path

print("="*60)
print("COST TRACKING SETUP VERIFICATION")
print("="*60)

# 1. Check if cost tracker is in the right place
cost_tracker_path = Path("src/infrastructure/cost_tracking/cost_tracker.py")
print(f"\n1. Cost Tracker File:")
print(f"   Path: {cost_tracker_path}")
print(f"   Exists: {cost_tracker_path.exists()}")

if cost_tracker_path.exists():
    with open(cost_tracker_path) as f:
        content = f.read()
    
    # Check for new methods
    has_set_agent_name = "def set_agent_name" in content
    has_set_context = "def set_context" in content
    has_project_root_fix = "Found project root via directory search" in content
    
    print(f"   Has set_agent_name: {has_set_agent_name}")
    print(f"   Has set_context: {has_set_context}")
    print(f"   Has path fix: {has_project_root_fix}")
    
    if not all([has_set_agent_name, has_set_context, has_project_root_fix]):
        print("   ❌ Cost tracker needs update!")
    else:
        print("   ✅ Cost tracker is updated")
else:
    print("   ❌ Cost tracker not found!")

# 2. Check if openai_client.py is updated
openai_client_path = Path("src/infrastructure/ai/openai_client.py")
print(f"\n2. OpenAI Client File:")
print(f"   Path: {openai_client_path}")
print(f"   Exists: {openai_client_path.exists()}")

if openai_client_path.exists():
    with open(openai_client_path) as f:
        content = f.read()
    
    has_cost_import = "from src.infrastructure.cost_tracking.cost_tracker import get_cost_tracker" in content
    has_tracking_in_generate = "self.cost_tracker.track_api_call" in content
    has_set_agent_name_method = "def set_agent_name(self, name: str):" in content
    
    print(f"   Has cost tracker import: {has_cost_import}")
    print(f"   Has tracking code: {has_tracking_in_generate}")
    print(f"   Has set_agent_name method: {has_set_agent_name_method}")
    
    if not all([has_cost_import, has_tracking_in_generate, has_set_agent_name_method]):
        print("   ❌ OpenAI client needs update!")
    else:
        print("   ✅ OpenAI client is updated")
else:
    print("   ❌ OpenAI client not found!")

# 3. Check if content_generation_agent.py is updated
agent_path = Path("src/domain/agents/advanced_content_generator.py")
if not agent_path.exists():
    agent_path = Path("src/domain/agents/content_generation_agent.py")

print(f"\n3. Content Generation Agent:")
print(f"   Path: {agent_path}")
print(f"   Exists: {agent_path.exists()}")

if agent_path.exists():
    with open(agent_path) as f:
        content = f.read()
    
    has_set_agent_call = "set_agent_name" in content
    has_set_context_call = "set_context" in content
    has_hasattr_check = "hasattr(self.ai_client, 'set_agent_name')" in content
    
    print(f"   Calls set_agent_name: {has_set_agent_call}")
    print(f"   Calls set_context: {has_set_context_call}")
    print(f"   Has safety checks: {has_hasattr_check}")
    
    if has_set_agent_call and has_set_context_call:
        if has_hasattr_check:
            print("   ✅ Agent is updated with safety checks")
        else:
            print("   ⚠️  Agent updated but missing safety checks (may cause MockAIClient error)")
    else:
        print("   ❌ Agent needs update!")
else:
    print("   ❌ Agent not found!")

# 4. Check data directory
data_dir = Path("data/costs")
print(f"\n4. Data Directory:")
print(f"   Path: {data_dir}")
print(f"   Exists: {data_dir.exists()}")

if data_dir.exists():
    api_calls = data_dir / "api_calls.json"
    if api_calls.exists():
        import json
        with open(api_calls) as f:
            calls = json.load(f)
        print(f"   API calls tracked: {len(calls)}")
        
        if calls:
            latest = calls[-1]
            print(f"   Latest call:")
            print(f"     Agent: {latest.get('agent_name')}")
            print(f"     Cost: ${latest.get('total_cost')}")
            print(f"     Batch: {latest.get('batch_id')}")
            print(f"     Post: {latest.get('post_number')}")
    else:
        print("   ❌ No api_calls.json found")
else:
    print("   ❌ Data directory not found!")

print("\n" + "="*60)
print("SUMMARY")
print("="*60)

all_good = (
    cost_tracker_path.exists() and 
    openai_client_path.exists() and 
    agent_path.exists() and
    data_dir.exists()
)

if all_good:
    print("✅ All files are in place!")
    print("\nIf you're still seeing errors:")
    print("1. Make sure you replaced content_generation_agent.py with the safe version")
    print("2. Restart the backend")
    print("3. Generate a new post")
    print("4. Check if dashboard updates")
else:
    print("❌ Some files are missing or not updated")
    print("\nPlease:")
    print("1. Download all the corrected files")
    print("2. Replace them in the correct locations")
    print("3. Restart the backend")