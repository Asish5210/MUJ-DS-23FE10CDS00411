# MUJ-DS-23FE10CDS00411 - Generative AI Emotion-Aware Interactive RPG

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

## Repository Structure
According to the Capstone Project Guidelines:
```text
.
├── README.md               # Student info, project overview, instructions
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
**Generative AI Emotion-Aware Interactive RPG** is an emotion-aware interactive AI application powered by local LLM inference (Ollama / Llama 3.2) and dynamic multimodal scene generation. The system interprets player emotions in real time to dynamically steer narrative tone, game choices, and visual immersion.

### Key Features
- **Emotion Engine:** Evaluates sentiment, urgency, and intensity from player inputs.
- **Dynamic Storytelling:** Tailors narrative progression to emotional states.
- **Generative Media:** Real-time scene art generation matching mood and environment.
- **Interactive UI:** Atmospheric, cinematic interface with real-time feedback.

---

## Getting Started

### Prerequisites
- Python 3.10+
- [Ollama](https://ollama.com/) with `llama3.2` model installed:
  ```bash
  ollama run llama3.2
  ```

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/Asish5210/MUJ-DS-23FE10CDS00411.git
   cd MUJ-DS-23FE10CDS00411/code
   ```
2. Install dependencies:
   ```bash
   pip install flask requests
   ```
3. Run the application:
   ```bash
   python app.py
   ```
4. Open `http://localhost:5000` in your browser.

---

## Weekly Updates & Milestones
- [x] Step 1: Join Organization & Configure GitHub profile
- [x] Step 2: Create Personal Repository (`MUJ-DS-23FE10CDS00411`)
- [x] Step 3: Add Instructor (`@sandeepmbm`) as collaborator
- [x] Step 4 & 5: Repository Structure and Documentation setup
- [ ] Step 6: Regular weekly commits and feature enhancements
- [ ] Step 7: Team Capstone Repository integration
- [ ] Step 8: Individual contributions and module testing
- [ ] Step 9: GitHub Issues tracking
- [ ] Step 10: Pull Request workflow
- [ ] Step 11: Final deliverables (presentations, reports, code)
