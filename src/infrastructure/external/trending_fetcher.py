"""
Trending Content Fetchers - Data sources for wizard inspiration bases
Provides: News, Memes, Philosopher Quotes, Poetry Excerpts
"""

import os
import aiohttp
import random
from typing import Dict, List, Optional
from datetime import datetime
import structlog

logger = structlog.get_logger()


class TrendingNewsFetcher:
    """
    Fetch trending news headlines for timely content hooks
    
    Uses NewsAPI (free tier: 100 requests/day)
    Fallback: Curated list if API unavailable
    """
    
    def __init__(self):
        self.api_key = os.getenv("NEWSAPI_KEY", "")
        self.base_url = "https://newsapi.org/v2/top-headlines"
        self.logger = logger.bind(component="news_fetcher")
    
    async def fetch_trending(
        self,
        category: str = "business",
        count: int = 5
    ) -> List[Dict]:
        """
        Fetch trending news headlines
        
        Args:
            category: "business", "technology", "general"
            count: Number of headlines to return (max 5)
        
        Returns:
            List of news items with title, description, source, url
        """
        
        # Try API if key available
        if self.api_key and self.api_key != "":
            try:
                return await self._fetch_from_api(category, count)
            except Exception as e:
                self.logger.warning(f"NewsAPI failed, using fallback: {e}")
        
        # Fallback to curated list
        return self._get_fallback_news(category, count)
    
    async def _fetch_from_api(self, category: str, count: int) -> List[Dict]:
        """Fetch from NewsAPI"""
        
        params = {
            "apiKey": self.api_key,
            "category": category,
            "language": "en",
            "pageSize": count,
            "country": "us"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(self.base_url, params=params) as response:
                if response.status != 200:
                    raise Exception(f"NewsAPI returned {response.status}")
                
                data = await response.json()
                articles = data.get("articles", [])
                
                return [
                    {
                        "id": f"news_{i}",
                        "title": article.get("title", ""),
                        "description": article.get("description", "")[:200],
                        "source": article.get("source", {}).get("name", "Unknown"),
                        "url": article.get("url", ""),
                        "published_at": article.get("publishedAt", "")
                    }
                    for i, article in enumerate(articles)
                    if article.get("title")
                ]
    
    def _get_fallback_news(self, category: str, count: int) -> List[Dict]:
        """Curated fallback news when API unavailable"""
        
        fallback_items = {
            "business": [
                {
                    "id": "news_1",
                    "title": "AI Adoption Accelerates Across Fortune 500 Companies",
                    "description": "Major corporations are integrating AI tools into daily operations, with productivity gains reported across departments.",
                    "source": "TechCrunch",
                    "url": "",
                    "published_at": datetime.now().isoformat()
                },
                {
                    "id": "news_2",
                    "title": "Remote Work Policies Continue to Evolve Post-Pandemic",
                    "description": "Companies are finding hybrid models that balance flexibility with collaboration needs.",
                    "source": "WSJ",
                    "url": "",
                    "published_at": datetime.now().isoformat()
                },
                {
                    "id": "news_3",
                    "title": "Wellness Spending Hits Record High Among Professionals",
                    "description": "Investment in self-care and workplace wellness programs reaches new peaks as burnout concerns grow.",
                    "source": "Forbes",
                    "url": "",
                    "published_at": datetime.now().isoformat()
                },
                {
                    "id": "news_4",
                    "title": "The Great Resignation Continues with New Talent Dynamics",
                    "description": "Workers are prioritizing work-life balance and company culture in job decisions.",
                    "source": "Harvard Business Review",
                    "url": "",
                    "published_at": datetime.now().isoformat()
                },
                {
                    "id": "news_5",
                    "title": "Gen Z Reshapes Workplace Expectations and Norms",
                    "description": "Younger professionals are demanding transparency, purpose, and flexibility from employers.",
                    "source": "Fast Company",
                    "url": "",
                    "published_at": datetime.now().isoformat()
                }
            ],
            "technology": [
                {
                    "id": "news_6",
                    "title": "ChatGPT and AI Tools Transform Knowledge Work",
                    "description": "Professionals report significant time savings using AI assistants for writing and research.",
                    "source": "The Verge",
                    "url": "",
                    "published_at": datetime.now().isoformat()
                },
                {
                    "id": "news_7",
                    "title": "Zoom Fatigue Prompts Return to In-Person Meetings",
                    "description": "Companies are experimenting with hybrid formats to reduce video call burnout.",
                    "source": "CNET",
                    "url": "",
                    "published_at": datetime.now().isoformat()
                }
            ],
            "general": [
                {
                    "id": "news_8",
                    "title": "Modern Professionals Seek Meaning Over Money",
                    "description": "Survey shows career fulfillment now ranks higher than compensation for many workers.",
                    "source": "Psychology Today",
                    "url": "",
                    "published_at": datetime.now().isoformat()
                }
            ]
        }
        
        items = fallback_items.get(category, fallback_items["business"])
        return items[:count]


class TrendingMemeFetcher:
    """
    Fetch trending memes and cultural references safe for LinkedIn
    
    For MVP: Curated list of evergreen, professional memes
    Future: Can integrate Reddit API or Know Your Meme
    """
    
    def __init__(self):
        self.logger = logger.bind(component="meme_fetcher")
    
    async def fetch_trending(self, count: int = 5) -> List[Dict]:
        """
        Fetch LinkedIn-appropriate meme references
        
        Returns:
            List of memes with name, context, usage notes
        """
        return self._get_curated_memes()[:count]
    
    def _get_curated_memes(self) -> List[Dict]:
        """Curated list of safe, evergreen memes for professional use"""
        
        return [
            {
                "id": "meme_1",
                "name": "Distracted Boyfriend",
                "source": "Distracted Boyfriend Meme",
                "context": "Choosing between old habits and better alternatives",
                "usage": "Perfect for: comparing traditional vs modern approaches, old vs new priorities",
                "content": "The classic meme of choosing between what you have and what you want - great for discussing workplace change and priorities.",
                "professional_angle": "Use to illustrate choosing innovation over comfort zones"
            },
            {
                "id": "meme_2",
                "name": "Is This a Pigeon?",
                "source": "Is This a Pigeon? Meme",
                "context": "Misidentifying something obvious",
                "usage": "Perfect for: calling out misunderstood concepts, workplace confusion",
                "content": "The anime meme about mistaking things - ideal for discussing common workplace misunderstandings.",
                "professional_angle": "Use to highlight common industry misconceptions"
            },
            {
                "id": "meme_3",
                "name": "Two Buttons",
                "source": "Daily Struggle (Two Buttons) Meme",
                "context": "Difficult decision between two options",
                "usage": "Perfect for: work-life balance dilemmas, tough choices",
                "content": "Character sweating over which button to press - represents modern professional dilemmas.",
                "professional_angle": "Use for relatable workplace decision paralysis"
            },
            {
                "id": "meme_4",
                "name": "Drake Hotline Bling",
                "source": "Drake Hotline Bling Meme",
                "context": "Rejecting one thing, approving another",
                "usage": "Perfect for: showing preferences, comparing solutions",
                "content": "Drake rejecting vs approving - a classic preference format.",
                "professional_angle": "Use to show evolved workplace practices"
            },
            {
                "id": "meme_5",
                "name": "This Is Fine Dog",
                "source": "This Is Fine Meme",
                "context": "Pretending everything is okay when it's not",
                "usage": "Perfect for: workplace stress, burnout, denial",
                "content": "Dog sitting in burning room saying 'this is fine' - resonates with workplace stress.",
                "professional_angle": "Use to acknowledge workplace burnout honestly"
            },
            {
                "id": "meme_6",
                "name": "Galaxy Brain",
                "source": "Expanding Brain Meme",
                "context": "Levels of thinking from simple to transcendent",
                "usage": "Perfect for: showing evolution of ideas, wisdom levels",
                "content": "Brain expanding through levels - great for showing professional growth.",
                "professional_angle": "Use to illustrate career or skill progression"
            },
            {
                "id": "meme_7",
                "name": "Woman Yelling at Cat",
                "source": "Woman Yelling at Cat Meme",
                "context": "Mismatched arguments or perspectives",
                "usage": "Perfect for: communication breakdowns, misaligned expectations",
                "content": "Woman yelling at confused cat at dinner table - perfect for workplace miscommunication.",
                "professional_angle": "Use for manager/employee expectation misalignment"
            },
            {
                "id": "meme_8",
                "name": "Spider-Man Pointing",
                "source": "Spider-Man Pointing Meme",
                "context": "Two identical things or hypocrisy",
                "usage": "Perfect for: similar problems, calling out double standards",
                "content": "Two Spider-Men pointing at each other - great for identifying similar issues.",
                "professional_angle": "Use for industry-wide similar challenges"
            }
        ]


class PhilosophyDatabase:
    """
    Static database of philosopher quotes relevant to professional life
    Curated for workplace wisdom and business philosophy
    """
    
    PHILOSOPHERS = {
        "Marcus Aurelius": {
            "era": "Stoic Roman Emperor",
            "bio": "Roman Emperor and Stoic philosopher",
            "quotes": [
                {
                    "id": "phil_1",
                    "text": "You have power over your mind - not outside events. Realize this, and you will find strength.",
                    "context": "Stoic philosophy on control and acceptance",
                    "workplace_angle": "Perfect for discussing workplace stress management and what we can control",
                    "themes": ["control", "mindfulness", "resilience"]
                },
                {
                    "id": "phil_2",
                    "text": "Waste no more time arguing what a good man should be. Be one.",
                    "context": "Action over deliberation",
                    "workplace_angle": "Great for discussing execution over endless planning",
                    "themes": ["action", "leadership", "execution"]
                },
                {
                    "id": "phil_3",
                    "text": "The impediment to action advances action. What stands in the way becomes the way.",
                    "context": "Obstacles as opportunities",
                    "workplace_angle": "Perfect for reframing workplace challenges",
                    "themes": ["obstacles", "growth", "perspective"]
                }
            ]
        },
        "Seneca": {
            "era": "Stoic philosopher and statesman",
            "bio": "Roman Stoic philosopher, advisor to Nero",
            "quotes": [
                {
                    "id": "phil_4",
                    "text": "We suffer more often in imagination than in reality.",
                    "context": "Anxiety and anticipation",
                    "workplace_angle": "Ideal for discussing workplace anxiety and overthinking",
                    "themes": ["anxiety", "mindfulness", "reality"]
                },
                {
                    "id": "phil_5",
                    "text": "It is not that we have a short time to live, but that we waste a lot of it.",
                    "context": "Time management and priorities",
                    "workplace_angle": "Perfect for productivity and priority discussions",
                    "themes": ["time", "productivity", "priorities"]
                }
            ]
        },
        "Alan Watts": {
            "era": "Modern philosopher (1915-1973)",
            "bio": "British philosopher who popularized Eastern philosophy for Western audiences",
            "quotes": [
                {
                    "id": "phil_6",
                    "text": "Trying to define yourself is like trying to bite your own teeth.",
                    "context": "The paradox of self-awareness",
                    "workplace_angle": "Great for discussing authentic leadership and self-discovery",
                    "themes": ["identity", "authenticity", "paradox"]
                },
                {
                    "id": "phil_7",
                    "text": "The only way to make sense out of change is to plunge into it, move with it, and join the dance.",
                    "context": "Embracing change",
                    "workplace_angle": "Perfect for change management and adaptability",
                    "themes": ["change", "adaptability", "flow"]
                }
            ]
        },
        "Lao Tzu": {
            "era": "Ancient Chinese philosopher",
            "bio": "Founder of Taoism, author of Tao Te Ching",
            "quotes": [
                {
                    "id": "phil_8",
                    "text": "A journey of a thousand miles begins with a single step.",
                    "context": "Starting and persistence",
                    "workplace_angle": "Ideal for discussing large projects and career journeys",
                    "themes": ["beginnings", "persistence", "journey"]
                },
                {
                    "id": "phil_9",
                    "text": "Nature does not hurry, yet everything is accomplished.",
                    "context": "Patience and natural timing",
                    "workplace_angle": "Perfect for discussing sustainable pace and avoiding burnout",
                    "themes": ["patience", "sustainability", "pace"]
                }
            ]
        },
        "Naval Ravikant": {
            "era": "Modern entrepreneur & philosopher",
            "bio": "Tech entrepreneur, investor, and modern philosophical voice",
            "quotes": [
                {
                    "id": "phil_10",
                    "text": "Seek wealth, not money or status. Wealth is having assets that earn while you sleep.",
                    "context": "True wealth definition",
                    "workplace_angle": "Great for discussing value creation vs. appearance",
                    "themes": ["wealth", "value", "leverage"]
                },
                {
                    "id": "phil_11",
                    "text": "Specific knowledge is found by pursuing your genuine curiosity and passion.",
                    "context": "Career differentiation",
                    "workplace_angle": "Perfect for discussing unique career development",
                    "themes": ["expertise", "curiosity", "differentiation"]
                }
            ]
        }
    }
    
    def get_all_philosophers(self) -> List[Dict]:
        """Get list of all available philosophers"""
        return [
            {
                "id": name.lower().replace(" ", "_"),
                "name": name,
                "era": data["era"],
                "bio": data["bio"],
                "quote_count": len(data["quotes"])
            }
            for name, data in self.PHILOSOPHERS.items()
        ]
    
    def get_philosopher_quotes(self, philosopher_name: str) -> List[Dict]:
        """Get all quotes from a specific philosopher"""
        data = self.PHILOSOPHERS.get(philosopher_name, {})
        quotes = data.get("quotes", [])
        
        # Add philosopher name to each quote
        for quote in quotes:
            quote["philosopher"] = philosopher_name
            quote["source"] = philosopher_name
        
        return quotes
    
    def get_random_quote(self, philosopher: Optional[str] = None) -> Dict:
        """Get a random quote, optionally from specific philosopher"""
        if philosopher and philosopher in self.PHILOSOPHERS:
            quotes = self.PHILOSOPHERS[philosopher]["quotes"]
        else:
            # Get all quotes from all philosophers
            quotes = []
            for phil_data in self.PHILOSOPHERS.values():
                quotes.extend(phil_data["quotes"])
        
        quote = random.choice(quotes) if quotes else {}
        
        # Add metadata
        if quote:
            # Find which philosopher this quote belongs to
            for phil_name, phil_data in self.PHILOSOPHERS.items():
                if quote in phil_data["quotes"]:
                    quote["philosopher"] = phil_name
                    quote["source"] = phil_name
                    break
        
        return quote


class PoetryDatabase:
    """
    Static database of poetry excerpts relevant to professional life
    Curated for inspiration, humanity, and depth
    """
    
    POETS = {
        "Mary Oliver": {
            "bio": "American poet (1935-2019), known for nature and life contemplation",
            "style": "Contemplative, accessible, nature-focused",
            "excerpts": [
                {
                    "id": "poet_1",
                    "text": "Tell me, what is it you plan to do with your one wild and precious life?",
                    "poem": "The Summer Day",
                    "context": "Purpose and intentionality",
                    "workplace_angle": "Perfect for discussing career purpose and life choices",
                    "themes": ["purpose", "life", "choices"]
                },
                {
                    "id": "poet_2",
                    "text": "Someone I loved once gave me a box full of darkness. It took me years to understand that this too, was a gift.",
                    "poem": "The Uses of Sorrow",
                    "context": "Growth through difficulty",
                    "workplace_angle": "Ideal for discussing learning from challenges",
                    "themes": ["growth", "challenges", "perspective"]
                }
            ]
        },
        "Rumi": {
            "bio": "13th-century Persian poet and Sufi mystic",
            "style": "Spiritual, transcendent, deeply human",
            "excerpts": [
                {
                    "id": "poet_3",
                    "text": "Let yourself be silently drawn by the strange pull of what you really love. It will not lead you astray.",
                    "poem": "Essential Rumi",
                    "context": "Following authentic passion",
                    "workplace_angle": "Great for discussing following your calling",
                    "themes": ["passion", "authenticity", "calling"]
                },
                {
                    "id": "poet_4",
                    "text": "The wound is the place where the Light enters you.",
                    "poem": "Essential Rumi",
                    "context": "Transformation through pain",
                    "workplace_angle": "Perfect for reframing setbacks as growth opportunities",
                    "themes": ["transformation", "healing", "growth"]
                }
            ]
        },
        "Maya Angelou": {
            "bio": "American poet and civil rights activist (1928-2014)",
            "style": "Powerful, resilient, human dignity",
            "excerpts": [
                {
                    "id": "poet_5",
                    "text": "There is no greater agony than bearing an untold story inside you.",
                    "poem": "I Know Why the Caged Bird Sings",
                    "context": "The importance of expression",
                    "workplace_angle": "Ideal for encouraging authenticity and voice",
                    "themes": ["voice", "expression", "authenticity"]
                },
                {
                    "id": "poet_6",
                    "text": "You may not control all the events that happen to you, but you can decide not to be reduced by them.",
                    "poem": "Letter to My Daughter",
                    "context": "Resilience and agency",
                    "workplace_angle": "Perfect for discussing workplace resilience",
                    "themes": ["resilience", "agency", "strength"]
                }
            ]
        },
        "David Whyte": {
            "bio": "Contemporary poet focusing on work and organizational life",
            "style": "Deeply relevant to professional contexts",
            "excerpts": [
                {
                    "id": "poet_7",
                    "text": "Start close in, don't take the second step or the third, start with the first thing close in, the step you don't want to take.",
                    "poem": "Start Close In",
                    "context": "Beginning with the difficult",
                    "workplace_angle": "Perfect for discussing taking action on hard tasks",
                    "themes": ["action", "courage", "beginning"]
                },
                {
                    "id": "poet_8",
                    "text": "The courageous conversation might be to our surprise, with ourselves.",
                    "poem": "Consolations",
                    "context": "Self-honesty",
                    "workplace_angle": "Great for leadership and self-awareness",
                    "themes": ["honesty", "self-awareness", "courage"]
                }
            ]
        },
        "Hafiz": {
            "bio": "14th-century Persian poet",
            "style": "Joyful, wise, celebratory",
            "excerpts": [
                {
                    "id": "poet_9",
                    "text": "Even after all this time, the sun never says to the earth, 'You owe me.' Look what happens with a love like that. It lights the whole sky.",
                    "poem": "The Gift",
                    "context": "Unconditional giving",
                    "workplace_angle": "Ideal for discussing leadership and generosity",
                    "themes": ["generosity", "leadership", "giving"]
                }
            ]
        }
    }
    
    def get_all_poets(self) -> List[Dict]:
        """Get list of all available poets"""
        return [
            {
                "id": name.lower().replace(" ", "_"),
                "name": name,
                "bio": data["bio"],
                "style": data["style"],
                "excerpt_count": len(data["excerpts"])
            }
            for name, data in self.POETS.items()
        ]
    
    def get_poet_excerpts(self, poet_name: str) -> List[Dict]:
        """Get all excerpts from a specific poet"""
        data = self.POETS.get(poet_name, {})
        excerpts = data.get("excerpts", [])
        
        # Add poet name to each excerpt
        for excerpt in excerpts:
            excerpt["poet"] = poet_name
            excerpt["source"] = poet_name
        
        return excerpts
    
    def get_random_excerpt(self, poet: Optional[str] = None) -> Dict:
        """Get a random excerpt, optionally from specific poet"""
        if poet and poet in self.POETS:
            excerpts = self.POETS[poet]["excerpts"]
        else:
            # Get all excerpts from all poets
            excerpts = []
            for poet_data in self.POETS.values():
                excerpts.extend(poet_data["excerpts"])
        
        excerpt = random.choice(excerpts) if excerpts else {}
        
        # Add metadata
        if excerpt:
            # Find which poet this excerpt belongs to
            for poet_name, poet_data in self.POETS.items():
                if excerpt in poet_data["excerpts"]:
                    excerpt["poet"] = poet_name
                    excerpt["source"] = poet_name
                    break
        
        return excerpt