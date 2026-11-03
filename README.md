# Inkloom AI — Intelligent Brand Governance & Compliance Platform
**Team Name:** lovyeoune  
**Event:** CodeNexus India 2026 (Round 2 Build)

## Overview
Inkloom AI is a pre-publication brand governance platform that reviews content against approved corporate guidelines, facts, and design assets. Instead of bluntly blocking content, the system detects tone drift, terminology errors, and unverified claims, providing explainable feedback and smart corrections.

## Core Features
- **Semantic Rule Checking:** Uses Retrieval-Augmented Generation (RAG) to cross-reference text against company rulebooks.
- **Explainable Feedback:** Clearly highlights why content failed a guideline and offers context-aware suggestions.
- **Collaborative Workflows:** Supports role-based reviews and revision tracking.

## Tech Stack
- **AI Engine:** Python, FastAPI, Google Gemini API, LangChain
- **Frontend:** React.js / HTML5 & CSS3
- **Database & Storage:** PostgreSQL & Vector Store (ChromaDB / Pinecone)

## Repository Structure
- `ai-engine/` - Core Python scripts for RAG guideline matching and compliance auditing.
- `backend/` - Node.js/Python API endpoints, authentication, and user roles.
- `frontend/` - React dashboard UI for creators and reviewers.

## Getting Started (AI Engine)
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
