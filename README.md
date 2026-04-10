# Rolo AI Card Generator

Rolo is an intelligent, multi-agent business card generator that transforms a simple URL and contact details into stunning, production-ready digital business cards. It combines a sophisticated **FastAPI + LangGraph** AI backend with a rich, interactive **Next.js** frontend.

## 🚀 Features

*   **Multi-Agent AI Pipeline**: Powered by LangGraph and Groq LLMs.
*   **Automated Research**: Scrapes websites via Playwright to dynamically extract logos, descriptions, and brand color palettes.
*   **Smart Template Selection**: Automatically categorizes businesses (Tech, Corporate, Creative, Vibrant, Personal) to select the perfect matching layout.
*   **Self-Correcting Layouts**: A built-in "Critic" agent validates the JSON layout schema and requests self-corrections on the fly.
*   **Lightning-Fast Regeneration**: Hate the first design? Hit "Regenerate" to instantly cycle through the remaining layout concepts using cached brand data.
*   **Modern Frontend Experience**: Interactive drag-and-drop Next.js workspace offering canvas-like customization, with a responsive hero UI.

## 🏗️ Architecture

### 1. Frontend (`/frontend`)
The frontend is built with **Next.js 15 (React 19)**, **Tailwind CSS**, and modern glassmorphism UI components. It serves as both the data collector and the final interactive rendering engine.
*   **Rendering**: Renders absolute-positioned components via an AI-generated coordinate system (`hCoords`/`vCoords`) matching a JSON schema.
*   **Run**: `npm run dev` running on `http://localhost:3000`

### 2. Backend API (`/backend`)
A pure Python backend driven by **FastAPI**.
*   **Agents**:
    *   `planner.py` - Validates the URL and fields.
    *   `research.py` - Scrapes brand colors, OpenGraph data, and descriptions.
    *   `enrichment.py` - Fills any leftover schema gaps.
    *   `template_selection.py` - Assesses the industry & selects one of 10 handcrafted visual templates.
    *   `fill.py` - Maps the data into the JSON template.
    *   `critic.py` - Validates layout ratios and truncates visual overflows.
*   **Run**: `uvicorn backend.main:app --reload` on `http://localhost:8000`

## 🛠️ Getting Started

### Prerequisites
*   Node.js > 18
*   Python 3.10+
*   [Groq API Key](https://console.groq.com/keys)

### Backend Setup
1. Clone the repository.
2. Create your virtual environment: 
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install fastapi uvicorn langgraph playwright pydantic python-dotenv groq beautifulsoup4
   playwright install
   ```
4. Create a `.env` file in the root directory:
   ```env
   GROQ_API_KEY=your_groq_key_here
   ```
5. Run the API:
   ```bash
   uvicorn backend.main:app --reload
   ```

### Frontend Setup
1. In a new terminal, navigate to the `frontend` directory.
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the Next.js server:
   ```bash
   npm run dev
   ```
4. Visit `http://localhost:3000` and start generating!

## 🤝 Next Steps & Regeneration
Any time you hit "Regenerate" on the frontend, the system caches your Playwright web data to skip the heavy scraping lifting—instantly fetching a new layout template from the backend without reusing any previously dismissed templates in that session!
