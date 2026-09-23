# Security Study Notebook

## Setup

From the repository root, enter the homework directory and create or sync its virtual environment with `uv`:

```bash
cd hw2
uv sync
```

Set the Google Cloud project and Gemini model in your shell. Google Cloud Application Default Credentials / Vertex AI authentication must already be configured for your account.

```bash
export GOOGLE_CLOUD_PROJECT="your-google-cloud-project-id"
export GOOGLE_MODEL="gemini-3.6-flash"
```

## Add study documents and build the database

Place `.txt`, `.pdf`, or `.md` study documents in `study_docs/`. Then run the ingestion script to create or update the homework database at `rag_data/.chromadb`:

```bash
uv run python ingest_study_docs.py
```

## Run the app

Start Chainlit on port 8000:

```bash
uv run chainlit run app.py --port 8000
```

Open the local URL printed by Chainlit in your browser.
