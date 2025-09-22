#!/usr/bin/env python3
"""
Project setup script - No external dependencies required
Run this first to create the directory structure
"""

import os
import json
from pathlib import Path

def create_project_structure():
    """Create the complete project directory structure"""
    
    # Define directory structure
    directories = [
        "src/domain/models",
        "src/domain/agents",
        "src/domain/agents/validators",
        "src/domain/services",
        "src/infrastructure/ai",
        "src/infrastructure/persistence/repositories",
        "src/infrastructure/monitoring",
        "src/infrastructure/config",
        "src/infrastructure/logging",
        "src/application/use_cases",
        "src/application/dto",
        "src/api",
        "config/prompts/agents",
        "tests/unit",
        "tests/integration",
        "tests/fixtures",
        "data/output",
        "data/logs",
        "data/analytics",
        "scripts",
        "docker",
        "docs",
    ]
    
    # Create directories
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        # Add __init__.py to Python packages
        if directory.startswith("src/") or directory.startswith("tests/"):
            init_file = Path(directory) / "__init__.py"
            init_file.touch()
    
    print("✅ Directory structure created")
    
    # Create requirements.txt FIRST
    create_requirements()
    print("✅ Requirements.txt created")
    
    # Create default config file (using JSON instead of YAML)
    create_default_config()
    print("✅ Default configuration created")
    
    # Create .env.example file
    create_env_example()
    print("✅ Environment example file created")
    
    # Create .gitignore
    create_gitignore()
    print("✅ .gitignore file created")
    
    print("\n🚀 Project structure ready!")
    print("\nNext steps:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Copy .env.example to .env and add your OpenAI API key")
    print("3. Continue with creating the Python files")

def create_requirements():
    """Create requirements.txt file"""
    requirements_content = """# Core dependencies
pydantic>=2.0.0
openai>=1.0.0
aiohttp>=3.9.0
pyyaml>=6.0
structlog>=24.0.0
tenacity>=8.2.0

# Data handling
pandas>=2.0.0
openpyxl>=3.1.0

# Development
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-mock>=3.12.0
black>=23.0.0
mypy>=1.7.0
ruff>=0.1.0

# Optional for enhanced features
redis>=5.0.0
prometheus-client>=0.19.0
rich>=13.0.0
"""
    
    with open("requirements.txt", 'w') as f:
        f.write(requirements_content)

def create_default_config():
    """Create default configuration file in both JSON and YAML format"""
    config_path_json = Path("config/config.json")
    config_path_yaml = Path("config/config.yaml")
    
    default_config = {
        'openai': {
            'api_key': '${OPENAI_API_KEY}',
            'model': 'gpt-4o-mini',
            'temperature': 0.7,
            'max_tokens': 600,
            'timeout': 30
        },
        'batch': {
            'posts_per_batch': 5,
            'max_revisions': 2,
            'target_approval_rate': 0.3,
            'max_total_attempts': 20,
            'min_approvals_required': 2
        },
        'output': {
            'output_dir': 'data/output',
            'approved_posts_file': 'approved_posts.csv',
            'revised_posts_file': 'revised_approved_posts.csv',
            'rejected_posts_file': 'rejected_posts.csv',
            'metrics_file': 'batch_metrics.json'
        },
        'brand': {
            'product_name': 'Jesse A. Eisenbalm',
            'price': '$8.99',
            'tagline': 'The only business lip balm that keeps you human in an AI world',
            'ritual': 'Stop. Breathe. Apply.',
            'target_audience': 'LinkedIn professionals (24-34) dealing with AI workplace automation',
            'voice_attributes': [
                'absurdist modern luxury',
                'wry',
                'human-first'
            ]
        },
        'cultural_references': {
            'tv_shows': [
                'The Office',
                'Mad Men',
                'Silicon Valley',
                'Succession',
                'Ted Lasso'
            ],
            'workplace_themes': [
                'Zoom fatigue',
                'LinkedIn culture',
                'email disasters',
                'open office debates',
                'meeting overload',
                'Monday blues',
                'Friday energy',
                'coffee addiction'
            ],
            'seasonal_themes': [
                'New Year productivity',
                'performance reviews',
                'networking events',
                'holiday parties',
                'summer Fridays',
                'back to office'
            ]
        },
        'logging_level': 'INFO',
        'environment': 'development'
    }
    
    # Save as JSON (no dependencies needed)
    with open(config_path_json, 'w') as f:
        json.dump(default_config, f, indent=2)
    
    # Create YAML format (as plain text for now)
    yaml_content = """openai:
  api_key: ${OPENAI_API_KEY}
  model: gpt-4o-mini
  temperature: 0.7
  max_tokens: 600
  timeout: 30

batch:
  posts_per_batch: 5
  max_revisions: 2
  target_approval_rate: 0.3
  max_total_attempts: 20
  min_approvals_required: 2

output:
  output_dir: data/output
  approved_posts_file: approved_posts.csv
  revised_posts_file: revised_approved_posts.csv
  rejected_posts_file: rejected_posts.csv
  metrics_file: batch_metrics.json

brand:
  product_name: Jesse A. Eisenbalm
  price: $8.99
  tagline: The only business lip balm that keeps you human in an AI world
  ritual: Stop. Breathe. Apply.
  target_audience: LinkedIn professionals (24-34) dealing with AI workplace automation
  voice_attributes:
    - absurdist modern luxury
    - wry
    - human-first

cultural_references:
  tv_shows:
    - The Office
    - Mad Men
    - Silicon Valley
    - Succession
    - Ted Lasso
  workplace_themes:
    - Zoom fatigue
    - LinkedIn culture
    - email disasters
    - open office debates
    - meeting overload
    - Monday blues
    - Friday energy
    - coffee addiction
  seasonal_themes:
    - New Year productivity
    - performance reviews
    - networking events
    - holiday parties
    - summer Fridays
    - back to office

logging_level: INFO
environment: development
"""
    
    with open(config_path_yaml, 'w') as f:
        f.write(yaml_content)

def create_env_example():
    """Create .env.example file"""
    env_content = """# Jesse A. Eisenbalm Content System Environment Variables

# Required: OpenAI API Key
OPENAI_API_KEY=your-openai-api-key-here

# Optional: Override default settings
# ENVIRONMENT=development
# LOG_LEVEL=INFO
# OUTPUT_DIR=data/output

# Optional: Redis for caching (Phase 4)
# REDIS_URL=redis://localhost:6379

# Optional: Monitoring (Phase 4)
# SENTRY_DSN=your-sentry-dsn-here
"""
    
    with open(".env.example", 'w') as f:
        f.write(env_content)

def create_gitignore():
    """Create .gitignore file"""
    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
*.egg-info/
dist/
build/

# Environment
.env
.env.local
.env.*.local

# IDE
.vscode/
.idea/
*.swp
*.swo
.DS_Store

# Project specific
data/logs/
data/output/*.csv
data/output/*.xlsx
data/output/*.json
data/analytics/
*.log

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/
.mypy_cache/

# Temporary
*.tmp
*.bak
~*
"""
    
    with open(".gitignore", 'w') as f:
        f.write(gitignore_content)

if __name__ == "__main__":
    print("="*60)
    print("Jesse A. Eisenbalm Content System - Setup")
    print("="*60)
    create_project_structure()
