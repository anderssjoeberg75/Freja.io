---
name: Document Analysis (RAG)
description: Enables analysis of local documents (PDF, Text) using Ollama for embeddings and inference.
---

# Document Analysis Skill

This skill allows Freja to "read" local documents and answer questions based on their content.

## Features
- **Ingest Documents**: Reads PDF or text files, chunks them, and stores vector embeddings locally.
- **Contextual Search**: Finds relevant document sections based on user queries.
- **Privacy-First**: Uses local Ollama models (`nomic-embed-text` or similar) and local ChromaDB. Data never leaves your machine.

## Usage
1.  **Ingest**: "Analyze this report: /path/to/report.pdf"
2.  **Query**: "What does the report say about Q3 revenue?"

## Requirements
- **Ollama**: Must be running locally.
- **Embedding Model**: A model like `nomic-embed-text` must be pulled in Ollama (`ollama pull nomic-embed-text`).
