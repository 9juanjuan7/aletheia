# 🔍 Aletheia

**Exposing funding conflicts and health misinformation through AI-powered analysis**

Aletheia is a Chrome extension that helps you evaluate health information by following the money. Instead of blindly trusting credentials, it reveals who funds publications, their conflicts of interest, and presents counter-perspectives from independent sources.

## 🎯 Why Aletheia?

- **Funding > Credentials**: A PhD funded by Pfizer is less credible than an independent researcher
- **Expose Conflicts**: See pharmaceutical sponsorships, industry ties, and hidden agendas
- **Counter-Perspectives**: Automatically finds alternative viewpoints from different funding sources
- **Follow the Money**: The #1 indicator of credibility is who pays for the research

## ✨ Features

- 🔬 **Publication Analysis**: Research ownership, funding sources, and conflicts of interest
- 📊 **Credibility Scoring**: 0-10 rating based on funding transparency (not credentials)
- 🔄 **Counter-Perspectives**: Find opposing viewpoints from independent sources
- 🚩 **Red/Green Flags**: Instant warnings about bias and propaganda
- 💾 **Growing Database**: Every analysis builds a shared knowledge base

## 🛠️ Tech Stack

**Frontend**
- JavaScript (Vanilla)
- Chrome Extension API
- HTML5/CSS3

**Backend**
- Python 3.10+
- Flask + Flask-CORS
- BeautifulSoup4

**AI/APIs**
- OpenAI GPT-4o-mini
- Tavily Search API

**Data**
- JSON (current)
- PostgreSQL (planned)

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Chrome browser
- API Keys: [OpenAI](https://platform.openai.com/api-keys) and [Tavily](https://tavily.com)

### Installation

1. **Clone the repo**
```
git clone https://github.com/yourusername/aletheia.git
cd aletheia
```

2. **Set up backend**
```
cd backend
python -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Configure API keys**
Create `backend/.env`:
```
OPENAI_API_KEY=your_openai_key
TAVILY_API_KEY=your_tavily_key
```

4. **Run backend**
```
python app.py
```
- Server runs on http://localhost:5000

5. **Install extension**
- Open Chrome → `chrome://extensions/`
- Enable "Developer mode"
- Click "Load unpacked" → Select `extension/` folder
- Pin Aletheia icon to toolbar

### Usage

1. Visit any health article (e.g., medicalnewstoday.com)
2. Click the Aletheia extension icon
3. View credibility analysis, funding sources, and counter-perspectives

## 📊 How It Works

1. **User clicks extension** → Analysis begins
2. **Research publication** → AI searches for ownership, funding, conflicts
3. **Calculate credibility** → Score based on funding transparency
4. **Find counter-perspective** → Search for alternative viewpoints
5. **Compare sources** → Show credibility gaps and recommendations

## 🎓 Credibility Scoring

**Start at 5.0, then adjust:**

✅ **Add Points:**
- +2.0: Links to peer-reviewed studies
- +2.0: Independent/nonprofit funding
- +1.0: Zero retractions

❌ **Subtract Points:**
- -3.0: Owned by industry they cover
- -2.0: Pharma/supplement sponsorship
- -2.0: No source citations

**Key Principle:** Funding independence matters more than impressive credentials.

## 📁 Project Structure
```
aletheia/
├── backend/
│ ├── app.py # Flask API
│ ├── services/
│ │ └── publication_researcher.py
│ ├── data/
│ │ ├── publications.json # Growing database
│ │ └── myths.json
│ └── requirements.txt
└── extension/
├── manifest.json
├── background.js
└── sidebar/
├── sidebar.html
├── sidebar.js
└── sidebar.css
```
## 🗺️ Roadmap

- [x] Chrome extension with manual analysis
- [x] Publication research & credibility scoring
- [x] Counter-perspective search
- [x] Funding transparency analysis
- [ ] PostgreSQL migration
- [ ] Topic clustering & consensus tracking
- [ ] Community features
- [ ] Blockchain integration (Sui)

## ⚠️ Disclaimer

Aletheia is a research tool. Always consult qualified healthcare professionals for medical decisions.

---

**Built with skepticism. Powered by independence.**

*"Follow the money, find the truth."*



