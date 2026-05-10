# MediMind AI — Intelligent Medical Assistant

An AI-powered full-stack medical assistant with multi-modal interaction through text, medical images, voice input, PDF-based knowledge retrieval, and real-time medical information access.

## Features

- **Conversational AI** — Multi-turn medical conversations powered by Gemini 2.5
- **RAG Pipeline** — Retrieval-Augmented Generation from medical PDF documents using ChromaDB
- **Medical Image Analysis** — BiomedCLIP-powered analysis of X-rays, MRIs, skin conditions
- **Voice Interaction** — Speech-to-text and text-to-speech via ElevenLabs
- **Real-Time Web Search** — Latest medical information via Tavily
- **Dark/Light Mode** — Premium healthcare-themed responsive UI
- **Chat History** — SQLite-backed conversation persistence
- **Chat Export** — Download conversation transcripts

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Frontend** | HTML, CSS, JavaScript |
| **Backend** | FastAPI, Uvicorn |
| **LLM** | Google Gemini 2.5 (via LangChain) |
| **Embeddings** | all-MiniLM-L6-v2 (local, free) |
| **Vector DB** | ChromaDB |
| **Routing** | LangGraph |
| **Image AI** | LLaVA model |
| **Voice** | ElevenLabs |
| **Web Search** | Tavily |
| **Database** | SQLite |

## Quick Start

### 1. Install Dependencies

```bash
cd Medical_assistant
pip install -r requirements.txt
```

### 2. Configure API Keys

Edit the `.env` file and paste your API keys:

```
GEMINI_API_KEY=your_gemini_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_key_here
TAVILY_API_KEY=your_tavily_key_here
```

> **Required:** `GEMINI_API_KEY` — Get it from [Google AI Studio](https://aistudio.google.com/apikey)
>
> **Optional:** `ELEVENLABS_API_KEY` — For voice features. Get from [ElevenLabs](https://elevenlabs.io/)
>
> **Optional:** `TAVILY_API_KEY` — For real-time web search. Get from [Tavily](https://tavily.com/)

### 3. Add Medical PDFs (Optional)

Place medical PDF documents in the `medical_docs/` directory. They will be automatically processed on startup.

### 4. Run the Server

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Open the App

Navigate to **http://localhost:8000** in your browser.

## Project Structure

```
Medical_assistant/
├── medical_docs/          # PDF storage for RAG
├── chroma_db/             # ChromaDB vector store
├── backend/
│   ├── main.py            # FastAPI entry point
│   ├── config.py          # Configuration
│   ├── database.py        # SQLite setup
│   ├── chat/
│   │   ├── routes.py      # Chat API endpoints
│   │   ├── models.py      # SQLAlchemy models
│   │   └── memory.py      # Chat memory manager
│   └── ai/
│       ├── graph.py       # LangGraph router
│       ├── rag.py         # RAG pipeline
│       ├── conversational.py  # Gemini AI
│       ├── image_analyzer.py  # BiomedCLIP
│       ├── voice.py       # ElevenLabs
│       └── web_search.py  # Tavily search
├── frontend/
│   ├── index.html         # Dashboard
│   ├── css/               # Stylesheets
│   └── js/                # JavaScript modules
├── .env                   # API keys
└── requirements.txt       # Dependencies
```
## Output
<img width="1600" height="700" alt="image" src="https://github.com/user-attachments/assets/c3a3403e-75c7-41f9-aaf3-afdf316d3361" />



## Disclaimer

MediMind AI is for **educational and informational purposes only**. It is **not** a substitute for professional medical advice, diagnosis, or treatment. Always consult a qualified healthcare provider.
