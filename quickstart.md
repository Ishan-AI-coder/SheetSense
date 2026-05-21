# 🚀 SheetSense Quickstart & Installation Guide

Welcome to **SheetSense**! This guide will help you get your Agentic Data Analyst up and running.

## 📋 Prerequisites

* **Python 3.10+**
* **uv**
  * Mac/Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`
  * Windows: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`

---

## 🛠️ Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/sheetsense.git
cd sheetsense
```

### 2. Install Dependencies

```bash
uv sync
```

### 3. Configure Environment Variables

Create a `.env` file in the root directory:

```bash
touch .env
```

Add your API key:

```env
GEMINI_API_KEY="your_google_gemini_api_key_here"
```
* **Google Gemini API:** Get your key from [Google AI Studio](https://aistudio.google.com/app/api-keys).
---

## 🏃‍♂️ Running the Application

Launch the Streamlit frontend:

```bash
uv run streamlit run app.py
```

---

## 💡 Basic Usage Flow

### Upload Data

Open `http://localhost:8501` and upload your CSV or XLSX file.

### Review Summary

The Summarization Agent generates a zero-shot Markdown report based on pre-computed statistics.

### Ask Questions

Use the main chat interface to ask mathematically specific questions. The Q&A agent will execute Pandas code to find the exact answer.

### Visualize

Ask for a chart (e.g., `"Plot a bar chart of sales by region"`). The Plotting Agent will write, sanitize, and execute the visualization code in the sandbox.

### Chart Q&A

Once a chart is rendered, use the localized chat form below the plot to ask specific questions about the visualized data.