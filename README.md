<div align="center">

# ⚡ GitGradeAnalyzer

### AI-Powered GitHub Repository Analyzer

**See Your Code Like a Recruiter Does**

[![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-00D0AA?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Gemini](https://img.shields.io/badge/Gemini-2.0-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev)
[![Groq](https://img.shields.io/badge/Groq-Llama--3.3-orange?style=for-the-badge)](https://groq.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

<br>

[🚀 Features](#-features) · [⚡ Quick Start](#-quick-start) · [📖 Usage](#-usage) · [🏗️ Architecture](#️-architecture) · [📡 API](#-api-reference)

<br>

<img src="https://raw.githubusercontent.com/dayanandXdarpan/Gitgrade/main/static/demo.gif" alt="GitGrade Demo" width="800">

</div>

---

## 🎯 The Problem We Solve

> **Students don't know how their GitHub looks to recruiters.**

Your GitHub is your portfolio, but most developers have no idea what signals they're sending to potential employers. Are your commit messages professional? Is your README convincing? Does your project structure show experience?

**GitGrade** bridges that gap by analyzing repositories exactly like a **Senior Engineering Manager** would during a hiring review.

---

## ✨ Features

<table>
<tr>
<td width="50%">

### 🧠 Hybrid AI Engine
| Mode | Speed | Best For |
|------|-------|----------|
| ⚡ **Fast** | ~2 sec | Quick feedback |
| 🔬 **Deep** | ~30 sec | Comprehensive analysis |

Uses **Groq (Llama-3.3-70B)** for instant responses and **Google Gemini 2.0** for deep analysis.

</td>
<td width="50%">

### 👔 4 Viewer Personas
| Persona | Focus |
|---------|-------|
| 👔 Recruiter | Hire/No-Hire decisions |
| 🧑‍🏫 Mentor | Growth & learning paths |
| 🔓 Bug Hunter | Security vulnerabilities |
| 🌍 GSoC Admin | Open source readiness |

</td>
</tr>
</table>

### 📊 What You Get

| Output | Description |
|--------|-------------|
| **Score (0-100)** | Employability rating based on 5 key areas |
| **Skill Level** | Beginner / Intermediate / Advanced |
| **Recruiter Verdict** | Strong Hire → Strong No Hire |
| **Resume Bullets** | Copy-paste ready CV points |
| **Interview Question** | Technical Q based on YOUR code |
| **Red/Green Flags** | What helps and hurts you |
| **Improvement Roadmap** | Prioritized action items |

### 🔍 The 5 Key Areas We Evaluate

```
┌─────────────────────────────────────────────────────────────────┐
│  🏪 THE STOREFRONT     │  First impressions, README, docs      │
├─────────────────────────────────────────────────────────────────┤
│  🦴 THE SKELETON       │  File structure, code organization    │
├─────────────────────────────────────────────────────────────────┤
│  💪 WORK ETHIC         │  Commit history, consistency          │
├─────────────────────────────────────────────────────────────────┤
│  🧪 QUALITY SIGNALS    │  Tests, CI/CD, linting                │
├─────────────────────────────────────────────────────────────────┤
│  💎 REAL-WORLD VALUE   │  Uniqueness, practical applicability  │
└─────────────────────────────────────────────────────────────────┘
```

## ⚡ Quick Start

### Prerequisites

- **Python 3.10+**
- **API Keys** (free tier available):
  - [Google Gemini API](https://aistudio.google.com/apikey) - For deep analysis
  - [Groq API](https://console.groq.com/keys) - For fast mode (optional)
  - [GitHub Token](https://github.com/settings/tokens) - For higher rate limits (optional)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/dayanandXdarpan/Gitgrade.git
cd Gitgrade

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment variables
cp .env.example .env
# Edit .env and add your API keys:
#   GEMINI_API_KEY=your_key_here
#   GROQ_API_KEY=your_key_here (optional)
#   GITHUB_TOKEN=your_token_here (optional)

# 4. Run the server
python -m uvicorn src.api.main:app --reload --port 8000

# 5. Open in browser
# http://localhost:8000
```

---

## 📖 Usage

### 🌐 Web Interface

1. Open `http://localhost:8000`
2. Paste any public GitHub repository URL
3. *(Optional)* Add a live demo URL
4. *(Optional)* Select analysis mode and persona
5. Click **Analyze** and get your report!

### 🔌 API Usage

```python
import httpx

response = httpx.post(
    "http://localhost:8000/api/v1/grade",
    json={
        "repo_url": "https://github.com/facebook/react",
        "mode": "fast",           # "fast" or "deep"
        "persona": "recruiter",   # recruiter, mentor, bug_hunter, gsoc_admin
        "deployed_link": "https://react.dev"  # optional
    },
    timeout=120
)

result = response.json()
print(f"Score: {result['score']}/100")
print(f"Verdict: {result['recruiter_verdict']}")
print(f"Resume Bullets: {result['resume_bullets']}")
```

### 📋 Sample Output

```json
{
  "score": 78,
  "level": "Intermediate",
  "headline": "Solid Foundation Needs Polish",
  "recruiter_verdict": "Hire - Shows professional quality work",
  "summary": "Well-structured project with clean code. Documentation is strong but test coverage needs improvement.",
  "resume_bullets": [
    "Built full-stack web application using React and Node.js",
    "Implemented CI/CD pipeline with GitHub Actions",
    "Maintained clean commit history with conventional commits"
  ],
  "interview_question": "I noticed you used Redux for state management. Can you explain why you chose Redux over Context API for this project?",
  "red_flags": ["No unit tests", "Missing contributing guidelines"],
  "green_flags": ["Comprehensive README", "Clean commit history", "Proper .gitignore"],
  "metrics": {
    "structure_rating": "B",
    "docs_rating": "A",
    "test_rating": "D",
    "commit_rating": "B"
  },
  "roadmap": [
    {"step": "Add unit tests", "priority": "Critical", "impact": "Major employability boost"},
    {"step": "Add CONTRIBUTING.md", "priority": "High", "impact": "Shows collaboration readiness"},
    {"step": "Set up GitHub Actions CI", "priority": "High", "impact": "Demonstrates DevOps knowledge"}
  ]
}
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    🌐 Frontend (Static)                         │
│              index.html + app.js + styles.css                   │
└───────────────────────────┬─────────────────────────────────────┘
                            │ POST /api/v1/grade
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ⚡ FastAPI Backend                            │
│                   main.py → routes.py                           │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    🎯 Orchestrator                               │
│         The Brain: Coordinates the entire pipeline              │
└──────┬──────────┬──────────┬──────────┬──────────┬──────────────┘
       │          │          │          │          │
       ▼          ▼          ▼          ▼          ▼
   ┌───────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
   │Agents │ │ GitHub │ │ Linter │ │   AI   │ │ Deploy │
   │ (4x)  │ │Scraper │ │Service │ │ Engine │ │ Verify │
   └───────┘ └────────┘ └────────┘ └────────┘ └────────┘
```

### 📁 Project Structure

```
GitGrade/
│
├── 📂 src/
│   ├── 📂 api/
│   │   ├── main.py              # FastAPI entry point
│   │   └── routes.py            # API endpoints
│   │
│   ├── 📂 core/
│   │   ├── orchestrator.py      # Main pipeline coordinator
│   │   ├── schemas.py           # Pydantic data models
│   │   ├── personas.py          # 4 viewer personas
│   │   └── config.py            # Environment config
│   │
│   └── 📂 services/
│       ├── ai_engine.py         # Hybrid AI (Groq + Gemini)
│       ├── agents.py            # 4 investigation agents
│       ├── github_scraper.py    # GitHub API integration
│       ├── linter.py            # Static code analysis
│       └── universal_parser.py  # Polyglot file parser
│
├── 📂 static/
│   ├── index.html               # Dashboard UI
│   ├── app.js                   # Frontend logic
│   └── styles.css               # Modern dark theme
│
├── 📂 prompts/
│   └── gitgrade_persona.md      # AI system prompt
│
├── .env.example                 # Environment template
├── requirements.txt             # Dependencies
├── render.yaml                  # Render deployment config
└── README.md                    # You are here!
```

---

## 📡 API Reference

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Web dashboard |
| `POST` | `/api/v1/grade` | Analyze repository |
| `GET` | `/api/v1/options` | Available personas & modes |
| `GET` | `/api/v1/health` | Health check |

### POST `/api/v1/grade`

**Request Body:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `repo_url` | string | ✅ | - | GitHub repository URL |
| `mode` | string | ❌ | `fast` | `fast` or `deep` |
| `persona` | string | ❌ | `mentor` | `recruiter`, `mentor`, `bug_hunter`, `gsoc_admin` |
| `deployed_link` | string | ❌ | - | Live demo URL to verify |

**Response:** Complete `GradeReport` JSON object

---

## 🛠️ Tech Stack

| Category | Technologies |
|----------|-------------|
| **Backend** | Python 3.10+, FastAPI, Uvicorn, Pydantic |
| **AI/LLM** | Google Gemini 2.0, Groq Llama-3.3-70B |
| **HTTP Client** | httpx (async) |
| **Frontend** | HTML5, CSS3, Vanilla JavaScript |
| **Deployment** | Render, Docker (optional) |

---

## 🚀 Deployment

### Deploy on Render (Free)

live website -https://gitgrade-analyzer.onrender.com (LLM quotas limited)

1. Fork this repository
2. Go to [render.com](https://render.com) → New Web Service
3. Connect your GitHub repo
4. Add environment variables:
   - `GEMINI_API_KEY`
   - `GROQ_API_KEY`
   - `GITHUB_TOKEN` (optional)
5. Deploy! 🎉

The `render.yaml` is already configured for one-click deployment.

---

## 🤝 Contributing

Contributions are welcome! Here's how:

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/amazing-feature`
3. **Commit** your changes: `git commit -m 'Add amazing feature'`
4. **Push** to branch: `git push origin feature/amazing-feature`
5. **Open** a Pull Request

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [Google Gemini](https://ai.google.dev) - Deep AI analysis
- [Groq](https://groq.com) - Lightning-fast inference
- [FastAPI](https://fastapi.tiangolo.com) - Modern Python web framework

---

<div align="center">

### Built with ❤️ by [Dayanand Darpan](https://www.dayananddarpan.me/)

© 2025 [dayananddarpan.me](https://www.dayananddarpan.me/) | All Rights Reserved

<br>

**⭐ Star this repo if you found it helpful!**

<br>

[🔝 Back to Top](#-gitgrade)

</div>
