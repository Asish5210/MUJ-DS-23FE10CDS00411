# MUJ-DS-23FE10CDS00411 - Generative AI Emotion-Aware Interactive RPG

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/Asish5210/MUJ-DS-23FE10CDS00411)

## Student & Course Information
- **Name:** Asish Patro
- **Registration Number:** 23FE10CDS00411
- **Branch:** Computer Science & Engineering (Data Science)
- **Batch:** Batch F
- **Project Title:** Generative AI Emotion-Aware Interactive RPG
- **GitHub Username:** [Asish5210](https://github.com/Asish5210)
- **Training Program:** Manipal University Jaipur - Batch F Capstone Training Program
- **Instructor / Evaluator:** [@sandeepmbm](https://github.com/sandeepmbm)

---

## 🚀 Live Deployment on Render

This project is configured for **1-Click Free Deployment on Render**:

### Method 1: Automatic Blueprint (1-Click)
Click the button below to instantly deploy to Render:
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/Asish5210/MUJ-DS-23FE10CDS00411)

### Method 2: Manual Dashboard Deploy
1. Sign in to [Render Dashboard](https://dashboard.render.com/) with GitHub.
2. Click **New +** > **Web Service**.
3. Select your repository: `Asish5210/MUJ-DS-23FE10CDS00411`.
4. Render automatically detects the configuration:
   - **Environment:** `Python`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT`
5. Click **Create Web Service**. Your live URL will be ready in 1-2 minutes!

*(Optional: In Render Environment Variables, you can add `GROQ_API_KEY` to enable free cloud Llama 3.1 inference)*

---

## Repository Structure
According to the Capstone Project Guidelines:
```text
.
├── render.yaml             # Render 1-click deployment blueprint
├── requirements.txt        # Production dependencies (Flask, Gunicorn, Requests)
├── Procfile                # WSGI process manager
├── README.md               # Student info, live demo link, documentation
├── assignments/            # Coursework and assignments
├── notebooks/              # Jupyter notebooks and data exploration
├── code/                   # Source code and application scripts
│   ├── app.py              # Main Flask application
│   ├── emotion_engine.py   # Emotion detection & state engine
│   └── templates/          # Web interface templates
│       └── index.html
├── resources/              # Datasets, assets, and documentation
├── presentations/          # Slides and demo presentations
└── capstone/               # Capstone project deliverables & reports
```

---

## Project Overview
**Generative AI Emotion-Aware Interactive RPG** is an emotion-aware interactive AI adventure game featuring dynamic multimodal scene generation and real-time narrative adaptation.

### Key Features
- **Emotion Engine:** Evaluates sentiment, urgency, and intensity from player inputs in real time.
- **Dynamic Storytelling:** Tailors narrative progression to emotional states.
- **Adaptive Cloud Engine:** Guaranteed 100% uptime with seamless multi-genre procedural beats.
- **Generative Media:** Real-time scene art generation matching mood and environment.
- **Interactive UI:** Atmospheric, cinematic interface with real-time feedback.

---

## Getting Started Locally

### Prerequisites
- Python 3.10+
- (Optional) [Ollama](https://ollama.com/) with `llama3.2` model installed:
  ```bash
  ollama run llama3.2
  ```

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/Asish5210/MUJ-DS-23FE10CDS00411.git
   cd MUJ-DS-23FE10CDS00411
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python app.py
   ```
4. Open `http://localhost:5000` in your browser.

---

## Milestones & Status
- [x] Step 1: Join Organization & Configure GitHub profile
- [x] Step 2: Create Personal Repository (`MUJ-DS-23FE10CDS00411`)
- [x] Step 3: Add Instructor (`@sandeepmbm`) as collaborator
- [x] Step 4 & 5: Repository Structure and Documentation setup
- [x] Step 6: Render cloud deployment configured
- [ ] Step 7: Team Capstone Repository integration
- [ ] Step 8: Individual contributions and module testing
- [x] Step 9: GitHub Issues tracking
- [ ] Step 10: Pull Request workflow
- [ ] Step 11: Final deliverables (presentations, reports, code)
