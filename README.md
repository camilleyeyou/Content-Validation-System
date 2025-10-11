# Jesse A. Eisenbalm LinkedIn Content Validation System

An AI-powered content generation and validation system for LinkedIn posts, featuring multi-agent validation, feedback loops, and **live prompt management** through a web portal.

## 🌐 Live Demo

**🚀 [Try the Web Portal](https://content-validation-system.vercel.app/)** - Generate and manage LinkedIn posts with AI agents!

[![Deploy Status](https://img.shields.io/badge/status-live-success)](https://content-validation-system.vercel.app/)
[![Frontend](https://img.shields.io/badge/frontend-vercel-black)](https://content-validation-system.vercel.app/)

---

## 📌 Quick Links

- 🌐 **[Live Web Portal](https://content-validation-system.vercel.app/)** - Try it now!
- 📝 **[Dashboard](https://content-validation-system.vercel.app/)** - Generate content
- 🤖 **[Prompt Manager](https://content-validation-system.vercel.app/prompts)** - Edit agent prompts
- 📚 **[Documentation](#-documentation)** - Learn more

---

## ⚡ Quick Start (30 seconds)

1. **Visit the live portal:** https://content-validation-system.vercel.app/
2. Click **"Generate Posts"**
3. Copy approved content for LinkedIn
4. Done! ✨

*Want to customize agents? See [Prompt Management](#-prompt-management-system) below.*

---

## 🎯 Overview

This system generates LinkedIn posts for Jesse A. Eisenbalm lip balm brand, validates them through multiple AI agents, and includes advanced feedback loops for continuous improvement. **NEW: Manage agent prompts in real-time through the web portal without code changes.**

### Brand Positioning
- **Product:** Jesse A. Eisenbalm ($8.99)
- **Tagline:** "The only business lip balm that keeps you human in an AI world"
- **Target:** LinkedIn professionals (24-34) dealing with AI workplace automation

## ✨ Key Features

- 🤖 **Multi-Agent Validation** - 6 specialized AI agents for content quality
- 🔄 **Feedback Loop System** - Automatic revision and improvement
- 🎨 **Web Portal Dashboard** - Generate and manage posts through UI
- ⚡ **Live Prompt Management** - Edit agent prompts without code changes
- 📊 **Performance Analytics** - Track approval rates and costs
- 🔐 **Export & Integration** - CSV exports and LinkedIn API ready

## 🏗️ Architecture

```
                    Web Portal (Next.js)
                           |
                    FastAPI Backend
                           |
      ┌────────────────────┴────────────────────┐
      |                                         |
Content Generator              Prompt Manager (NEW)
      |                                         |
      ├─→ [Post 1] ─→ 3 Parallel Validators ──┤
      ├─→ [Post 2] ─→  • Customer (Sarah)     │
      ├─→ [Post 3] ─→  • Business (Marcus)    │
      ├─→ [Post 4] ─→  • Social (Jordan)      │
      └─→ [Post 5] ─→                          │
                           |                    |
                    Decision Router             |
                           |                    |
              ┌────────────┴──────────┐        |
              |                       |         |
         ✅ APPROVED            ❌ REJECTED     |
              |                       |         |
         Export Queue      Feedback Aggregator │
                                    |           |
                           Revision Generator ──┘
                                    |
                            Retry Loop
```

### AI Agents

1. **AdvancedContentGenerator** - Creates posts using 25-element combination protocol
2. **SarahChenValidator** (Customer) - 28-year-old PM, validates authenticity
3. **MarcusWilliamsValidator** (Business) - VP Marketing, validates brand strategy
4. **JordanParkValidator** (Social) - Content strategist, validates engagement potential
5. **FeedbackAggregator** - Analyzes failures and creates improvement plans
6. **RevisionGenerator** - Rewrites posts based on aggregated feedback

## 📋 Requirements

- Python 3.9+
- Node.js 16+ (for web portal)
- OpenAI API key
- 8GB RAM recommended for parallel processing

## 🛠️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/jesse-content-system.git
cd jesse-content-system
```

### 2. Backend Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your OpenAI API key:
# OPENAI_API_KEY=your-key-here
```

### 3. Frontend Setup (Web Portal)

```bash
cd portal/frontend

# Install dependencies
npm install

# Create environment file
echo "NEXT_PUBLIC_API_BASE=http://localhost:8001" > .env.local

# Return to project root
cd ../..
```

### 4. Initialize Configuration

```bash
# Run setup script
python setup_project.py

# This creates:
# - config/config.yaml (system configuration)
# - config/prompts.json (prompt overrides)
# - data/ directories
```

## 🚀 Usage

### Quick Start: Use Live Portal

**✨ No installation needed!** Try the system instantly:

👉 **[https://content-validation-system.vercel.app/](https://content-validation-system.vercel.app/)**

Features:
- ✅ Generate posts with AI agents
- ✅ View approved content
- ✅ Copy posts for LinkedIn
- ✅ Manage agent prompts (requires backend)

### Option 1: Local Development

#### Start Backend
```bash
cd portal/backend
uvicorn app.main:app --reload --port 8001
```

**Start the frontend (new terminal):**
```bash
cd portal/frontend
npm run dev
```

**Access the portal:**
- **Live Production:** https://content-validation-system.vercel.app/
- **Local Development:**
  - Dashboard: http://localhost:3000/
  - Prompt Manager: http://localhost:3000/prompts

**Features:**
- ✅ Generate posts with one click
- ✅ View approved posts instantly
- ✅ Copy posts for LinkedIn
- ✅ Edit agent prompts in real-time
- ✅ A/B test different prompt strategies

### Option 2: Command Line

```bash
# Run complete system test
python tests/test_complete_system.py

# Run with real OpenAI API
OPENAI_API_KEY=your-key python tests/test_complete_system.py
```

## 🎨 Prompt Management System

### Edit Agent Behavior Without Code

1. Navigate to http://localhost:3000/prompts
2. Select an agent (e.g., JordanParkValidator)
3. Edit the system prompt or user prompt template
4. Click "Save Custom Prompts"
5. Run a new batch - changes apply immediately!

### Use Cases

- **A/B Testing**: Test different validation criteria
- **Fine-tuning**: Adjust agent personalities
- **Experimentation**: Try new content strategies
- **Quick Fixes**: Patch issues without code deployment

### Example: Make Jordan More Aggressive

```
Original: "I can make anything go viral except my own stability."
Custom: "I only approve content with viral potential > 8/10. No exceptions."
```

Save → Run batch → See stricter validation!

## 🧪 Testing

### Quick Test (Mock AI)
```bash
python tests/test_phase1.py
```

### Full System Test (Real OpenAI)
```bash
OPENAI_API_KEY=your-key python tests/test_complete_system.py
```

### Test Web Portal
```bash
# Backend
curl http://localhost:8001/api/prompts/agents

# Frontend
# Visit http://localhost:3000 in browser
```

## 📁 Project Structure

```
jesse-content-system/
├── src/
│   ├── domain/              # Core business logic
│   │   ├── models/          # Post, Batch, Validation models
│   │   ├── agents/          # AI agents (6 agents)
│   │   │   ├── base_agent.py
│   │   │   ├── advanced_content_generator.py
│   │   │   ├── feedback_aggregator.py
│   │   │   ├── revision_generator.py
│   │   │   └── validators/  # 3 validator agents
│   │   └── services/        # Orchestration
│   ├── infrastructure/      # External services
│   │   ├── ai/             # OpenAI client
│   │   ├── config/         # Configuration management
│   │   ├── prompts/        # 🆕 Prompt management system
│   │   ├── logging/        # Structured logging
│   │   └── persistence/    # Data export
│   └── application/        # Use cases
├── portal/                  # 🆕 Web Portal
│   ├── backend/
│   │   └── app/
│   │       ├── main.py           # FastAPI server
│   │       └── prompts_routes.py # Prompt API
│   └── frontend/            # Next.js app
│       └── app/
│           ├── page.tsx          # Dashboard
│           └── prompts/
│               └── page.tsx      # Prompt manager
├── config/
│   ├── config.yaml          # System configuration
│   └── prompts.json        # 🆕 Custom prompt overrides
├── tests/                   # Test suites
├── data/                    # Output and logs
│   ├── output/             # Generated posts (CSV)
│   └── logs/               # System logs
└── docs/                    # Documentation
```

## 📊 Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| Approval Rate (Initial) | 20-30% | ✅ 25-35% |
| Approval Rate (After Revision) | 40-50% | ✅ 45-55% |
| Processing Time (5 posts) | <5 minutes | ✅ 2-3 min |
| Cost Per Batch | $2-5 | ✅ $3-4 |
| Quality (Validators Passed) | 2+ | ✅ 2-3 |

## 🎯 Implementation Status

- [x] **Phase 1**: Core Architecture
- [x] **Phase 2**: AI Agents  
- [x] **Phase 3**: Orchestration
- [x] **Phase 4**: Data Export & Analytics
- [x] **Phase 5**: Web Portal & Dashboard
- [x] **Phase 6**: Prompt Management System ✨ NEW
- [ ] **Phase 7**: LinkedIn Integration (In Progress)
- [ ] **Phase 8**: Automated Scheduling

## 🔒 Security

- ✅ Never commit `.env` files
- ✅ API keys loaded from environment variables
- ✅ All sensitive data excluded via `.gitignore`
- ✅ Custom prompts stored in local `config/prompts.json`
- ✅ CORS configured for production

## 📊 Example Output

### Generated Post
```
That moment when your AI assistant schedules a "sync on syncing" 
and you realize: this is it. This is the meeting that breaks you.

Stop. Breathe. Apply Jesse A. Eisenbalm.

Because while machines optimize your calendar into oblivion, 
your lips deserve $8.99 worth of organic beeswax rebellion.

#HumanFirst #MeetingMadness #LinkedInLife
```

### Validation Scores
- Sarah (Customer): 8.2/10 ✅ APPROVED
- Marcus (Business): 7.8/10 ✅ APPROVED  
- Jordan (Social): 8.5/10 ✅ APPROVED

**Result:** Post approved and ready for LinkedIn!

## 🔧 Configuration

Edit `config/config.yaml` to customize:

```yaml
openai:
  model: gpt-4o-mini
  temperature: 0.7
  max_tokens: 600

batch:
  posts_per_batch: 5
  max_revisions: 2
  target_approval_rate: 0.3

brand:
  product_name: Jesse A. Eisenbalm
  price: $8.99
  tagline: "The only business lip balm that keeps you human in an AI world"
```

## 📈 Analytics

View batch metrics in `data/output/batch_metrics.json`:

```json
{
  "batch_id": "batch_abc123",
  "total_posts": 5,
  "approved_posts": 3,
  "approval_rate": 0.60,
  "revision_success_rate": 0.67,
  "total_cost": 3.42,
  "processing_time": 156.7
}
```

## 🐛 Troubleshooting

### Backend won't start
```bash
# Check Python version
python --version  # Should be 3.9+

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check OpenAI key
echo $OPENAI_API_KEY
```

### Frontend won't start
```bash
# Check Node version
node --version  # Should be 16+

# Clear and reinstall
rm -rf node_modules package-lock.json
npm install
```

### Prompts not saving
```bash
# Check config directory exists
ls -la config/

# Check file permissions
chmod 644 config/prompts.json

# Check backend logs for errors
tail -f portal/backend/logs/app.log
```

## 📚 Documentation

- [System Architecture](docs/architecture.md)
- [Agent Configuration](docs/agents.md)
- [API Reference](docs/api.md)
- [Prompt Management Guide](docs/prompts.md)
- [Deployment Guide](docs/deployment.md)

## 🚀 Deployment

### Live Production System

**Frontend (Deployed):** https://content-validation-system.vercel.app/
- Hosted on Vercel
- Auto-deploys from main branch
- Connected to backend API

### Deploy Your Own Backend (Railway/Render/Heroku)

**Note:** The frontend is already deployed at https://content-validation-system.vercel.app/
You only need to deploy your own backend if you want a private instance.

```bash
# Ensure deployment-ready files are used
# (main.py and prompts_routes.py with relative imports)

# Set environment variables:
OPENAI_API_KEY=your-key
PORTAL_BASE_URL=https://content-validation-system.vercel.app
CORS_ALLOW_ORIGINS=https://content-validation-system.vercel.app

# Deploy to your platform
# Railway: railway up
# Render: git push render main
# Heroku: git push heroku main
```

### Deploy Your Own Frontend (Optional)

If you want to customize the frontend, fork and deploy your own:

```bash
cd portal/frontend

# Set environment variable to your backend:
NEXT_PUBLIC_API_BASE=https://your-backend.com

# Deploy to Vercel
vercel deploy --prod

# Or deploy to Netlify
netlify deploy --prod
```

**Current Production Frontend:** https://content-validation-system.vercel.app/

### Connect Local Backend to Live Frontend

Want to test locally with the production frontend?

```bash
# Start your local backend
cd portal/backend
uvicorn app.main:app --port 8001

# Update CORS to allow the live frontend
# In main.py, set:
CORS_ALLOW_ORIGINS=https://content-validation-system.vercel.app

# The live frontend will connect to your local backend
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Authors

- Your Name - Initial work

## 🙏 Acknowledgments

- OpenAI for GPT-4 API
- Anthropic Claude for architecture guidance
- The LinkedIn marketing community

## 📧 Contact

- **Live Portal:** [https://content-validation-system.vercel.app/](https://content-validation-system.vercel.app/)
- Email: your.email@example.com
- LinkedIn: [Your Profile](https://linkedin.com/in/yourprofile)
- GitHub: [https://github.com/yourusername/jesse-content-system](https://github.com/yourusername/jesse-content-system)

---

**Made with ❤️ for keeping humans human in an AI world**