# 🤖 Agentic Coder

A local, privacy-first AI-powered Python project generator. Describe what you want to build in plain English — Agentic Coder plans, writes, tests, and auto-debugs a complete Python project using a locally running LLM via [Ollama](https://ollama.com). No cloud, no API keys, no data leaving your machine.

---

## ✨ Features

- **Natural language input** — describe your project goal and the agent does the rest
- **Multi-agent pipeline** — dedicated agents for planning, coding, testing, and debugging
- **Auto-debug loop** — if generated tests fail, the debugger agent fixes the code automatically (up to a configurable retry limit)
- **Tabbed code editor** — syntax-highlighted, editable code canvas with per-file tabs
- **Diff view** — see exactly what the debugger changed between fix attempts
- **Live log streaming** — real-time colored output panel showing every agent action
- **File tree** — visual status tracker for every file being generated
- **Hardware monitor** — live CPU, RAM, GPU (NVIDIA), and active Ollama model in the sidebar
- **Persistent memory** — SQLite-backed vector memory so the agent learns from past projects
- **Fully local** — runs entirely on your machine via Ollama

---

## 🏗️ Architecture

```
agentic_coder/
├── __init__.py
├── __main__.py              # Entry point
├── config.py                # All configuration (env-based)
├── main.py                  # Dependency injection factory
├── domain/
│   ├── models.py            # Domain entities (FileTask, ProjectPlan…)
│   └── exceptions.py        # Typed custom exceptions
├── infrastructure/
│   ├── llm_client.py        # Ollama generate API client
│   ├── embedder.py          # Ollama embeddings API client
│   ├── memory_store.py      # SQLite vector memory store
│   └── code_runner.py       # Subprocess code/test runner
├── agents/
│   ├── planner.py           # Breaks goal into file tasks
│   ├── coder.py             # Generates Python code per file
│   ├── tester.py            # Generates pytest test files
│   └── debugger.py          # Fixes code on test failure
├── services/
│   └── orchestrator.py      # Coordinates the full agent pipeline
└── ui/
    ├── app.py               # QApplication + theme bootstrap
    ├── theme.py             # VS Code dark theme (single color source)
    ├── main_window.py       # Main window, menu bar, toolbar, status bar
    ├── workers.py           # QThread worker + Python log → Qt signal bridge
    ├── code_canvas.py       # Tabbed editor with diff view and save
    ├── file_tree.py         # Real-time file generation status tree
    ├── sidebar.py           # Project metadata + hardware metrics
    └── log_panel.py         # Live colored log stream panel
```

The project follows **Clean Architecture** — domain logic is fully decoupled from infrastructure and UI. All UI updates cross thread boundaries exclusively via Qt signals.

---

## 🖥️ Requirements

| Requirement | Version |
|---|---|
| Python | 3.10 or newer |
| Ollama | Latest |
| PySide6 | 6.6.0+ |
| requests | 2.31.0+ |
| psutil | 5.9.0+ |
| pytest | 7.4.0+ |

> **GPU metrics** require an NVIDIA GPU with `nvidia-smi` available on your PATH. AMD and Intel GPUs will show N/A — this does not affect functionality.

---

## ⚙️ Installation

### Step 1 — Install Ollama

Download and install Ollama from [https://ollama.com](https://ollama.com), then pull the required models:

```bash
ollama pull qwen2.5-coder:7b-instruct-q4_K_M
ollama pull nomic-embed-text
```

Verify Ollama is running:

```bash
ollama list
```

You should see both models listed.

---

### Step 2 — Clone or download the project

```bash
# If using git
git clone https://github.com/Rikiza89/Coder_agent.git
cd agentic_coder

# Or manually: place the agentic_coder/ folder on your Desktop
```

Your folder structure must look like this — `agentic_coder` must be a subfolder, not the working directory:

```
Desktop/
└── agentic_coder/
    ├── __init__.py
    ├── __main__.py
    ├── config.py
    └── ...
```

---

### Step 3 — Create a virtual environment (recommended)

```bash
# From Desktop (one level above agentic_coder/)
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

---

### Step 4 — Install dependencies

```bash
pip install requests psutil PySide6 pytest pytest-qt
```

---

### Step 5 — Run the application

```bash
# Always run from the PARENT directory of agentic_coder/
# i.e. from Desktop/, not from inside agentic_coder/

cd C:\Users\YourName\Desktop      # Windows
# or
cd ~/Desktop                       # macOS / Linux

python -m agentic_coder
```

> ⚠️ **Important:** Never run `python agentic_coder/__main__.py` directly — this breaks relative imports. Always use `python -m agentic_coder` from the parent folder.

---

## 🚀 Using the Application

### 1. Set your work folder

Click **📁 Work Folder** in the toolbar or request bar, or go to **File → Set Work Folder**.

Select an existing folder or navigate to a new location and confirm. All generated files will be saved here. The current path is always shown in the bottom status bar.

---

### 2. Enter your project goal

Type a plain English description of what you want to build in the **Project Goal** input at the top of the window.

**Example goals:**

```
Build a REST API for a todo app using FastAPI and SQLite
```
```
Create a web scraper that extracts product prices from a URL and saves them to CSV
```
```
Write a CLI tool that converts Markdown files to HTML with a table of contents
```

Be as specific as you like — more detail generally produces better results.

---

### 3. Run the agent

Click **▶ Run Agent** (or press **F5**).

The agent pipeline will start:

| Stage | What happens |
|---|---|
| 🗂️ **Planning** | The planner agent breaks your goal into individual Python files |
| ⚙️ **Coding** | The coder agent generates each file one by one |
| 🧪 **Testing** | The tester agent generates pytest tests for each file |
| 🔧 **Debugging** | If tests fail, the debugger agent fixes the code and retries |
| ✅ **Complete** | All files pass tests and are saved to your work folder |

---

### 4. Monitor progress

While the agent runs you can observe:

- **File Tree (left panel)** — each file shows its current status with icons:
  - ⏳ pending → ⚙️ coding → 🧪 testing → 🔧 debugging → ✅ complete / ❌ failed
- **Progress bar (toolbar)** — overall completion percentage
- **Live log panel (bottom)** — every agent action streamed in real time, color-coded by log level
- **Sidebar (right)** — task counter, CPU/RAM/GPU usage, and the active Ollama model

---

### 5. Review and edit generated code

Each generated file opens automatically as a tab in the **code canvas**:

- **Edit** the code directly in the tab
- Click **💾 Save** to write changes back to disk
- Click **⊕ Diff** (enabled after a debug fix) to see a unified diff of what the debugger changed
- Close any tab with the **✕** button on the tab itself

---

### 6. Stop the agent

Click **⏹ Stop** (or press **F6**) at any time to interrupt the agent. Files generated so far are already saved to disk.

---

### 7. Start a new project

Go to **Agent → Clear Tree & Canvas** (or click **🗑 Clear** in the toolbar) to reset the UI for a new run. Your previously generated files remain on disk.

---

## ⚙️ Configuration

All settings are controlled via environment variables. You can set them in your shell before running, or use the built-in editor via **Config → Edit Environment** in the menu bar.

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_URL` | `http://localhost:11434/api` | Ollama API base URL |
| `OLLAMA_MODEL` | `qwen2.5-coder:7b-instruct-q4_K_M` | Code generation model |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text` | Embedding model for memory |
| `OLLAMA_TIMEOUT` | `120` | Request timeout in seconds |
| `MAX_DEBUG_RETRIES` | `5` | Max auto-debug attempts per file |
| `OUTPUT_DIR` | `output` | Default output directory |

**Example — use a different model:**

```bash
# Windows PowerShell
$env:OLLAMA_MODEL = "codellama:13b"
python -m agentic_coder

# macOS / Linux
OLLAMA_MODEL=codellama:13b python -m agentic_coder
```

---

## 🧠 Memory System

Agentic Coder stores a vector memory of every successfully generated project in `agent_memory.db` (SQLite). On each new run, the planner retrieves relevant past context to improve planning decisions.

- Memory persists across sessions automatically
- To reset memory, delete `agent_memory.db` from your work folder
- Memory uses cosine similarity search — no numpy required

---

## 🔧 Troubleshooting

**`No module named agentic_coder`**
You are running from inside the package folder. Move one level up:
```bash
cd ..
python -m agentic_coder
```

**`Ollama generate API call failed`**
Ollama is not running. Start it with:
```bash
ollama serve
```

**`Model not found`**
The configured model is not pulled. Run:
```bash
ollama pull qwen2.5-coder:7b-instruct-q4_K_M
ollama pull nomic-embed-text
```

**GPU shows N/A**
Either you have no NVIDIA GPU, `nvidia-smi` is not on your PATH, or you are using AMD/Intel. This is informational only and does not affect the agent.

**`psutil not installed` warning in sidebar**
Install it:
```bash
pip install psutil
```

**Tests always fail / max retries exceeded**
Try a larger or more capable model via `OLLAMA_MODEL`, or simplify your project goal into smaller, more focused sub-goals.

---

## 📄 License


MIT License — free to use, modify, and distribute.
