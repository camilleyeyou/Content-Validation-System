#!/usr/bin/env python3
"""
Verification script for news integration
Run this from project root to check if everything is set up correctly
"""

import sys
from pathlib import Path

print("=" * 70)
print("  NEWS INTEGRATION VERIFICATION")
print("=" * 70)
print()

# Get project root
project_root = Path.cwd()
print(f"📁 Current directory: {project_root}")
print()

# Check file structure
print("1. Checking file structure...")
print("-" * 70)

required_files = {
    "src/infrastructure/news/__init__.py": "Init file",
    "src/infrastructure/news/news_service.py": "News service",
    "src/infrastructure/news/news_converter.py": "News converter",
    "portal/backend/app/news_routes.py": "News routes",
}

all_exist = True
for file_path, description in required_files.items():
    full_path = project_root / file_path
    if full_path.exists():
        print(f"✅ {description}: {file_path}")
    else:
        print(f"❌ {description} MISSING: {file_path}")
        all_exist = False

print()

if not all_exist:
    print("⚠️  Some files are missing. Please copy them to the correct locations.")
    print()
    sys.exit(1)

# Check if we can import
print("2. Checking imports...")
print("-" * 70)

# Add project root to path (same as main.py does)
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from src.infrastructure.news import get_news_service
    print("✅ Can import: get_news_service")
except ImportError as e:
    print(f"❌ Cannot import get_news_service: {e}")
    sys.exit(1)

try:
    from src.infrastructure.news import news_to_inspiration_base
    print("✅ Can import: news_to_inspiration_base")
except ImportError as e:
    print(f"❌ Cannot import news_to_inspiration_base: {e}")
    sys.exit(1)

try:
    from src.infrastructure.news import format_news_for_wizard_display
    print("✅ Can import: format_news_for_wizard_display")
except ImportError as e:
    print(f"❌ Cannot import format_news_for_wizard_display: {e}")
    sys.exit(1)

try:
    from src.infrastructure.news import group_news_by_category
    print("✅ Can import: group_news_by_category")
except ImportError as e:
    print(f"❌ Cannot import group_news_by_category: {e}")
    sys.exit(1)

try:
    from src.infrastructure.news import get_trending_keywords
    print("✅ Can import: get_trending_keywords")
except ImportError as e:
    print(f"❌ Cannot import get_trending_keywords: {e}")
    sys.exit(1)

print()

# Check NewsService can be instantiated
print("3. Checking NewsService instantiation...")
print("-" * 70)

try:
    news_service = get_news_service()
    print(f"✅ NewsService created")
    print(f"   Cache directory: {news_service.cache_dir}")
    print(f"   API key set: {'Yes' if news_service.api_key else 'No (will fail to fetch)'}")
except Exception as e:
    print(f"❌ Failed to create NewsService: {e}")
    sys.exit(1)

print()

# Check news_routes.py can be imported
print("4. Checking news_routes.py...")
print("-" * 70)

try:
    # Add backend to path
    backend_dir = project_root / "portal" / "backend"
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))
    
    from app.news_routes import router
    print("✅ news_routes.py imports successfully")
    print(f"   Routes: {len(router.routes)} endpoints")
except ImportError as e:
    print(f"❌ Cannot import news_routes: {e}")
    sys.exit(1)

print()

# Summary
print("=" * 70)
print("  ✅ ALL CHECKS PASSED!")
print("=" * 70)
print()
print("Next steps:")
print("1. Set NEWS_API_KEY in your .env file")
print("2. Start your server: cd portal/backend && python -m app.main")
print("3. Test endpoint: curl http://localhost:8001/api/news/tech")
print()
print("If you get import errors when starting the server:")
print("  - Make sure you're running from the project root")
print("  - Check that __init__.py is in src/infrastructure/news/")
print("  - Verify all functions exist in news_converter.py")
print()