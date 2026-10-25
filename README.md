# 🤖 AI Chatbot with Gemini API, Conversation Memory & RAG
Live Website Link:https://ai-chatbot-rag-2.onrender.com


An AI-powered chatbot web application built using **Python, Flask, Gemini API, SQLite3, and RAG (Retrieval-Augmented Generation)**.

The application provides conversational AI responses, maintains conversation history, and allows users to upload PDF documents and ask questions based on their content.

---

## 🚀 Features

- 💬 AI-powered conversational chatbot
- 🤖 Gemini API integration
- 🧠 Conversation memory using SQLite3
- 📄 PDF upload functionality
- 🔍 Retrieval-Augmented Generation (RAG)
- ✂️ PDF text extraction and document chunking
- 🔎 Retrieval of relevant information from uploaded documents
- 🌐 Interactive web interface
- 🔗 Frontend-backend integration using API requests
- 🗑️ Clear conversation history functionality
- ⚠️ Error handling for API failures and temporary server issues

---

## 🛠️ Tech Stack

| Technology | Purpose |
|------------|---------|
| HTML | Frontend structure |
| CSS | User interface styling |
| JavaScript | Frontend interaction and API requests |
| Python | Backend programming |
| Flask | Web framework |
| Gemini API | AI-generated responses |
| SQLite3 | Conversation memory |
| RAG | PDF-based question answering |
| VS Code | Development environment |

---

## 🏗️ Project Architecture

```text
User
  │
  ▼
Frontend
HTML + CSS + JavaScript
  │
  │ API Request
  ▼
Flask Backend
  │
  ├──────────────► Gemini API
  │                    │
  │                    ▼
  │              AI Response
  │
  ├──────────────► SQLite3
  │                    │
  │                    ▼
  │             Conversation History
  │
  └──────────────► RAG System
                       │
                       ▼
                  PDF Processing
                       │
                 ┌─────┴─────┐
                 ▼           ▼
            Text Extraction  Chunking
                               │
                               ▼
                         Relevant Chunks
                               │
                               ▼
                            Gemini
