import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pydantic import BaseModel, Field

class OpenAIConfig(BaseModel):
    """OpenAI API configuration"""
    api_key: str
    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 600
    timeout: int = 30

class GoogleConfig(BaseModel):
    """Google Gemini API configuration for image generation"""
    api_key: str = Field(default="", description="Google API key for Gemini")
    image_model: str = Field(
        default="gemini-2.5-flash-image",
        description="Image generation model (gemini-2.5-flash-image)"
    )
    use_images: bool = Field(default=True, description="Enable image generation")

class BatchConfig(BaseModel):
    """Batch processing configuration"""
    posts_per_batch: int = 1  # Generate 1 post with 1 image at a time
    max_revisions: int = 2
    target_approval_rate: float = 0.3
    max_total_attempts: int = 20
    min_approvals_required: int = 2

class OutputConfig(BaseModel):
    """Output file configuration"""
    output_dir: str = "data/output"
    approved_posts_file: str = "approved_posts.csv"
    revised_posts_file: str = "revised_approved_posts.csv"
    rejected_posts_file: str = "rejected_posts.csv"
    metrics_file: str = "batch_metrics.json"

class BrandConfig(BaseModel):
    """Brand configuration for Jesse A. Eisenbalm"""
    product_name: str = "Jesse A. Eisenbalm"
    price: str = "$8.99"
    tagline: str = "The only business lip balm that keeps you human in an AI world"
    ritual: str = "Stop. Breathe. Apply."
    target_audience: str = "LinkedIn professionals (24-34) dealing with AI workplace automation"
    voice_attributes: List[str] = Field(default_factory=lambda: [
        "absurdist modern luxury", 
        "wry", 
        "human-first"
    ])

class CulturalReferencesConfig(BaseModel):
    """Cultural references configuration"""
    tv_shows: List[str] = Field(default_factory=lambda: [
        "The Office", "Mad Men", "Silicon Valley", "Succession", "Ted Lasso"
    ])
    workplace_themes: List[str] = Field(default_factory=lambda: [
        "Zoom fatigue", "LinkedIn culture", "email disasters", 
        "open office debates", "meeting overload"
    ])
    seasonal_themes: List[str] = Field(default_factory=lambda: [
        "New Year productivity", "performance reviews", 
        "networking events", "holiday parties"
    ])

@dataclass
class AppConfig:
    """Main application configuration"""
    openai: OpenAIConfig
    google: GoogleConfig
    batch: BatchConfig
    output: OutputConfig
    brand: BrandConfig
    cultural_references: CulturalReferencesConfig
    
    logging_level: str = "INFO"
    environment: str = "development"
    
    @classmethod
    def from_yaml(cls, config_path: str = "config/config.yaml") -> 'AppConfig':
        """Load configuration from YAML file"""
        path = Path(config_path)
        
        # Create default config if it doesn't exist
        if not path.exists():
            cls.create_default_config(path)
        
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        
        # Override with environment variables if they exist
        if api_key := os.getenv('OPENAI_API_KEY'):
            if 'openai' not in data:
                data['openai'] = {}
            data['openai']['api_key'] = api_key
        
        if google_api_key := os.getenv('GOOGLE_API_KEY'):
            if 'google' not in data:
                data['google'] = {}
            data['google']['api_key'] = google_api_key
        
        return cls(
            openai=OpenAIConfig(**data.get('openai', {})),
            google=GoogleConfig(**data.get('google', {})),
            batch=BatchConfig(**data.get('batch', {})),
            output=OutputConfig(**data.get('output', {})),
            brand=BrandConfig(**data.get('brand', {})),
            cultural_references=CulturalReferencesConfig(**data.get('cultural_references', {})),
            logging_level=data.get('logging_level', 'INFO'),
            environment=data.get('environment', 'development')
        )
    
    @staticmethod
    def create_default_config(path: Path) -> None:
        """Create default configuration file"""
        default_config = {
            'openai': {
                'api_key': 'your-openai-api-key-here',
                'model': 'gpt-4o-mini',
                'temperature': 0.7,
                'max_tokens': 600,
                'timeout': 30
            },
            'google': {
                'api_key': 'your-google-api-key-here',
                'image_model': 'gemini-2.5-flash-image',
                'use_images': True
            },
            'batch': {
                'posts_per_batch': 1,
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
                'tv_shows': ['The Office', 'Mad Men', 'Silicon Valley', 'Succession', 'Ted Lasso'],
                'workplace_themes': ['Zoom fatigue', 'LinkedIn culture', 'email disasters', 
                                    'open office debates', 'meeting overload'],
                'seasonal_themes': ['New Year productivity', 'performance reviews', 
                                   'networking events', 'holiday parties']
            },
            'logging_level': 'INFO',
            'environment': 'development'
        }
        
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            yaml.dump(default_config, f, default_flow_style=False, sort_keys=False)