# Excel Financial Analyzer

A chat-based app where you upload Excel/CSV files and ask questions in plain English. The AI analyzes your data and creates charts - all locally, no data leaves your machine.

## Why I Built This

I wanted to use `mcp-server-chart` for generating charts with AI agents. It works great, but there's a catch - it uploads your data to external CDN servers to render charts. Not ideal when you're working with sensitive financial data.

So I swapped it out for `streamlit-gpt-vis` which renders everything locally in your browser. Problem solved.

## What's Inside

```
├── app.py           # Streamlit frontend (chat UI + file upload)
├── api.py           # FastAPI backend (handles requests)
├── agent.py         # LangGraph agent (the brain)
├── tools.py         # Pandas tools for data analysis
├── requirements.txt
└── .env             # Your OpenAI API key goes here
```

## Quick Start

1. Clone and install:
```bash
git clone <repo-url>
cd excel-analyzer
pip install -r requirements.txt
```

2. Add your OpenAI key:
```bash
# Create .env file
OPENAI_API_KEY=your-key-here
```

3. Run both servers:
```bash
# Terminal 1 - API
uvicorn api:app --reload --port 8000

# Terminal 2 - Frontend
streamlit run app.py
```

4. Open http://localhost:8501, upload your file, and start asking questions.

## How It Works

1. You upload an Excel/CSV file
2. You type a question like "show me monthly revenue as a bar chart"
3. The LangGraph agent figures out what pandas code to run
4. It analyzes your data and outputs a chart in `vis-chart` format
5. `streamlit-gpt-vis` renders the chart locally in your browser

No data goes anywhere. It all stays on your machine.

## The Agent

The agent has 3 tools:

- **get_data_info** - Shows column names, types, and sample rows
- **run_analysis** - Executes any pandas code on your data
- **get_column_stats** - Quick stats for a specific column (sum, mean, min, max, etc.)

It also has memory, so you can say things like "now show that as a pie chart" and it remembers what "that" means.

## Chart Types

The agent can create these charts by outputting `vis-chart` markdown:

- Line charts
- Bar charts
- Pie charts
- Column charts
- Area charts
- Scatter plots
- Histograms
- Treemaps

Just ask naturally - "create a bar chart of sales by region" or "plot the trend over time".

## Tech Stack

- **Streamlit** - Frontend
- **FastAPI** - Backend API with SSE streaming
- **LangGraph** - Agent orchestration
- **LangChain + OpenAI** - LLM stuff
- **streamlit-gpt-vis** - Local chart rendering
- **Pandas** - Data analysis

## Requirements

- Python 3.9+
- Node.js (required by streamlit-gpt-vis for rendering)
- OpenAI API key

## FAQ

**Why not just use mcp-server-chart?**
- It uploads your data to alipayobjects CDN to generate chart images. Fine for demos, not great for real business data.

**Why FastAPI + Streamlit instead of just Streamlit?**
- Streaming. I wanted real-time token streaming and step-by-step visibility (showing when tools are being used). SSE from FastAPI makes this smooth.

**Can I use a different LLM?**
- Yeah, swap out `ChatOpenAI` in `agent.py`. Works with any LangChain-compatible model. Claude, local models, whatever.

**How big can my files be?**
- Tested with 11k rows, works fine. It loads everything into memory though, so don't go crazy with million-row files.

**The chart isn't rendering?**
- Make sure Node.js is installed. `streamlit-gpt-vis` needs it.

**Can I add more tools?**
- Yep, just add them in `tools.py` and include them in `get_pandas_tools()`. The agent will figure out when to use them.

## Known Limitations

- Single file at a time (no multi-file joins yet)
- In-memory storage (restart = data gone)
- Needs Node.js installed

## License

MIT - do whatever you want with it.
