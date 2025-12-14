<![CDATA[<div align="center">

# ⚡ GitGradeAnalyzer

### AI-Powered GitHub Repository Analyzer

**See Your Code Like a Recruiter Does**

[![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-00D0AA?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Gemini](https://img.shields.io/badge/Gemini-2.0-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev)
[![Groq](https://img.shields.io/badge/Groq-Llama--3.3-orange?style=for-the-badge)](https://groq.com)

[Features](#-features) • [Demo](#-demo) • [Installation](#-installation) • [Usage](#-usage) • [Architecture](#-architecture) • [API](#-api-reference)

</div>

---

## 🎯 What is GitGradeAnalyzer?

GitGradeAnalyzer is an **intelligent repository evaluation system** that analyzes GitHub repositories from a **recruiter's perspective**. Unlike traditional linters that find bugs, GitGradeAnalyzer assesses what makes a developer **hireable** based on their public code.

> 💡 **The Problem**: Students don't know how their GitHub looks to recruiters. GitGrade bridges that gap.

### The 5 Key Areas Recruiters Evaluate

| Area | What It Measures |
|------|------------------|
| 🏪 **The Storefront** | Documentation, README quality, first impressions |
| 🦴 **The Skeleton** | File structure, code organization, architecture |
| 💪 **Work Ethic** | Commit history, consistency, development patterns |
| 🧪 **Quality Signals** | Tests, CI/CD, linting, code quality practices |
| 💎 **Real-World Value** | Uniqueness, completeness, practical applicability |

---

## ✨ Features

### 🧠 Hybrid AI Engine
- **Fast Mode** (~1-2s): Groq's Llama-3.3-70B for instant feedback
- **Deep Mode** (~20-30s): Google Gemini 2.0 for comprehensive analysis

### 👔 4 Viewer Personas
| Persona | Focus | Use Case |
|---------|-------|----------|
| 👔 **Recruiter** | Hire/No-Hire decisions | Job applications |
| 🧑‍🏫 **Mentor** | Growth roadmaps | Learning & improvement |
| 🔓 **Bug Hunter** | Security vulnerabilities | Security audits |
| 🌍 **GSoC Admin** | Open source readiness | GSoC/Hacktoberfest prep |

### 📊 Comprehensive Output
- **Score**: 0-100 employability rating
- **Level**: Beginner / Intermediate / Advanced
- **Verdict**: Strong Hire → Strong No Hire
- **Resume Bullets**: Copy-paste ready CV points
- **Interview Question**: Based on YOUR specific code
- **Red/Green Flags**: What helps and hurts you
- **Roadmap**: Prioritized action items with specific commands

### 🔍 Smart Analysis
- **4 Investigation Agents**: Structure, Context, Quality, History
- **Universal Parser**: Jupyter notebooks, Docker, K8s, CI/CD
- **Live Deployment Check**: Verifies if your demo works
- **Asset Gallery**: Finds images/videos in your repo

---

## 🚀 Demo

### Input
```
https://github.com/username/my-project
```

### Output
```json
{
  "score": 78,
  "level": "Intermediate",
  "headline": "Solid Foundation Needs Polish",
  "recruiter_verdict": "Hire - Shows professional quality work",
  "resume_bullets": [
    "Built full-stack web application using React and Node.js",
    "Implemented CI/CD pipeline with GitHub Actions",
    "Maintained 80%+ test coverage across codebase"
  ],
  "red_flags": ["No contributing guidelines", "Missing license"],
  "green_flags": ["Clean commit history", "Comprehensive README"],
  "roadmap": [
    {"step": "Add CONTRIBUTING.md", "priority": "High"},
    {"step": "Add MIT License", "priority": "Critical"}
  ]
}
```

---

## 📦 Installation

### Prerequisites
- Python 3.10+
- API Keys (free tier available):
  - [Google Gemini API](https://aistudio.google.com/apikey)
  - [Groq API](https://console.groq.com/keys) (optional, for fast mode)
  - [GitHub Token](https://github.com/settings/tokens) (optional, for higher rate limits)

### Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/gitgrade.git
cd gitgrade

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your API keys

# Run the server
python -m uvicorn src.api.main:app --reload --port 8000
```

### Environment Variables

Create a `.env` file:

```env
# Required: At least one AI API key
GEMINI_API_KEY=your_gemini_api_key
GROQ_API_KEY=your_groq_api_key

# Optional: Higher GitHub rate limits
GITHUB_TOKEN=your_github_token
```

---

## 💻 Usage

### Web Interface
1. Open `http://localhost:8000` in your browser
2. Paste a GitHub repository URL
3. (Optional) Add a live demo URL for deployment verification
4. (Optional) Click "Advanced Options" to select:
   - **Analysis Mode**: Quick Scan (~30s) or Deep Investigation (~2-5min)
   - **Viewer Persona**: Recruiter, Mentor, Bug Hunter, or GSoC Admin
5. Click **Analyze** and wait for results

### API Usage

```python
import httpx

response = httpx.post(
    "http://localhost:8000/api/v1/grade",
    json={
        "repo_url": "https://github.com/facebook/react",
        "mode": "fast",  # or "deep"
        "persona": "recruiter",  # recruiter, mentor, bug_hunter, gsoc_admin
        "deployed_link": "https://react.dev"  # optional
    },
    timeout=120
)

result = response.json()
print(f"Score: {result['score']}/100")
print(f"Verdict: {result['recruiter_verdict']}")
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (Static)                        │
│  index.html → app.js → styles.css                               │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP POST /api/v1/grade
┌────────────────────────────▼────────────────────────────────────┐
│                      FastAPI Backend                             │
│  main.py (Entry) → routes.py (Endpoints)                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                      Orchestrator                                │
│  The central pipeline: Investigate → Scrape → Analyze → Grade   │
└───────┬───────────────┬───────────────┬───────────────┬─────────┘
        │               │               │               │
   ┌────▼────┐     ┌────▼────┐     ┌────▼────┐    ┌────▼────┐
   │ Agents  │     │ GitHub  │     │ Linter  │    │AI Engine│
   │ (4x)    │     │ Scraper │     │ Service │    │ (Hybrid)│
   └─────────┘     └─────────┘     └─────────┘    └─────────┘
```

### Project Structure

```
gitgrade/
├── src/
│   ├── api/
│   │   ├── main.py          # FastAPI app entry point
│   │   └── routes.py        # API endpoints
│   ├── core/
│   │   ├── orchestrator.py  # Main pipeline coordinator
│   │   ├── schemas.py       # Pydantic data models
│   │   ├── personas.py      # 4 viewer personas
│   │   └── config.py        # Environment config
│   ├── services/
│   │   ├── ai_engine.py     # Hybrid AI (Groq + Gemini)
│   │   ├── agents.py        # 4 investigation agents
│   │   ├── github_scraper.py# GitHub API integration
│   │   ├── linter.py        # Static code analysis
│   │   └── file_parser.py   # Universal file parser
│   └── __init__.py
├── static/
│   ├── index.html           # Dashboard UI
│   ├── app.js               # Frontend logic
│   └── styles.css           # Modern dark theme
├── prompts/
│   └── gitgrade_persona.md  # AI system prompt
├── .env.example             # Environment template
├── requirements.txt         # Python dependencies
└── README.md
```

---

## 📡 API Reference

### Grade Repository

```http
POST /api/v1/grade
```

**Request Body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `repo_url` | string | ✅ | GitHub repository URL |
| `mode` | string | ❌ | `fast` (default) or `deep` |
| `persona` | string | ❌ | `mentor` (default), `recruiter`, `bug_hunter`, `gsoc_admin` |
| `deployed_link` | string | ❌ | Live demo URL to verify |

**Response:** Full `GradeReport` JSON object

### Get Options

```http
GET /api/v1/options
```

Returns available personas and analysis modes.

### Health Check

```http
GET /api/v1/health
```

---

## 🛠️ Tech Stack

| Category | Technology |
|----------|------------|
| **Backend** | Python, FastAPI, Uvicorn, Pydantic |
| **AI/LLM** | Google Gemini 2.0, Groq Llama-3.3-70B |
| **HTTP** | httpx (async) |
| **Frontend** | Vanilla HTML/CSS/JS |
| **Styling** | Custom CSS, Inter font |

---

## 📊 Sample Output

```
┌────────────────────────────────────────────────┐
│  ⚡ GitGrade Report                             │
├────────────────────────────────────────────────┤
│  Score: 78/100 (Intermediate)                  │
│  Verdict: "Hire - Shows solid fundamentals"   │
├────────────────────────────────────────────────┤
│  📊 Metrics                                     │
│  ├── Structure: B                              │
│  ├── Docs: A                                   │
│  ├── Tests: C                                  │
│  └── Commits: B                                │
├────────────────────────────────────────────────┤
│  🚩 Red Flags                                   │
│  ├── No CI/CD pipeline                         │
│  └── Missing contributing guidelines           │
├────────────────────────────────────────────────┤
│  ✅ Green Flags                                 │
│  ├── Comprehensive README                      │
│  └── Consistent commit history                 │
├────────────────────────────────────────────────┤
│  🚀 Top Priority Actions                       │
│  1. Add GitHub Actions CI (Critical)           │
│  2. Write unit tests (High)                    │
│  3. Add CONTRIBUTING.md (Medium)               │
└────────────────────────────────────────────────┘
```

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [Google Gemini](https://ai.google.dev) for deep AI analysis
- [Groq](https://groq.com) for lightning-fast inference
- [FastAPI](https://fastapi.tiangolo.com) for the awesome web framework

---

<div align="center">

**Built with ❤️ by [Dayanand & Darpan](https://www.dayananddarpan.me/)**

© 2024 [dayananddarpan.me](https://www.dayananddarpan.me/) | All Rights Reserved

⭐ Star this repo if you found it helpful!

</div>
]]>