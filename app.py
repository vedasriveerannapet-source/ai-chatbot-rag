from flask import Flask, render_template, request, jsonify, session
from google import genai
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

from rag import (
    extract_text_from_pdf,
    create_chunks,
    search_document
)

import os
import time
import sqlite3
import uuid


# ==========================================
# LOAD ENVIRONMENT VARIABLES
# ==========================================

load_dotenv()


# ==========================================
# FLASK APP
# ==========================================

app = Flask(__name__)

app.secret_key = os.getenv(
    "FLASK_SECRET_KEY",
    "change-this-secret-key"
)


# ==========================================
# UPLOAD CONFIGURATION
# ==========================================

UPLOAD_FOLDER = "uploads"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ==========================================
# RAG DOCUMENT MEMORY
# ==========================================

document_chunks = []
document_name = None


# ==========================================
# GEMINI CLIENT
# ==========================================

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


# ==========================================
# DATABASE
# ==========================================

DATABASE = "chat_history.db"


def get_db_connection():

    connection = sqlite3.connect(DATABASE)

    connection.row_factory = sqlite3.Row

    return connection


def create_database():

    connection = get_db_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT NOT NULL,
            role TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.commit()

    connection.close()


create_database()


# ==========================================
# HOME PAGE
# ==========================================

@app.route("/")
def home():

    return render_template("index.html")


# ==========================================
# CHAT API
# ==========================================

@app.route("/chat", methods=["POST"])
def chat():

    global document_chunks
    global document_name

    # --------------------------------------
    # Get request data
    # --------------------------------------

    data = request.get_json(silent=True)

    if not data:

        return jsonify({
            "reply": "Invalid request."
        }), 400


    message = data.get("message", "").strip()


    if not message:

        return jsonify({
            "reply": "Please enter a message."
        }), 400


    # --------------------------------------
    # Create conversation ID
    # --------------------------------------

    if "conversation_id" not in session:

        session["conversation_id"] = str(uuid.uuid4())


    conversation_id = session["conversation_id"]


    # --------------------------------------
    # Get previous conversation
    # --------------------------------------

    connection = get_db_connection()

    previous_messages = connection.execute("""
        SELECT role, message
        FROM messages
        WHERE conversation_id = ?
        ORDER BY id ASC
    """, (conversation_id,)).fetchall()

    connection.close()


    # --------------------------------------
    # RAG SEARCH
    # --------------------------------------

    relevant_chunks = search_document(
        document_chunks,
        message,
        top_k=4
    )


    # --------------------------------------
    # Build document context
    # --------------------------------------

    document_context = ""


    if relevant_chunks:

        document_context = "\n\n".join(
            [
                f"[Page {chunk['page']}]\n{chunk['text']}"
                for chunk in relevant_chunks
            ]
        )


    # --------------------------------------
    # Build current prompt
    # --------------------------------------

    if document_context:

        current_prompt = f"""
You are an AI assistant.

The user has uploaded a document named:
{document_name}

Use the document context below when answering the
user's question.

DOCUMENT CONTEXT:

{document_context}


USER QUESTION:

{message}


INSTRUCTIONS:

- Answer using the document context when relevant.
- Do not invent information from the document.
- If the requested information is not present in the
  document, clearly say that it was not found in the
  uploaded document.
- You may still answer general questions when appropriate.
"""

    else:

        current_prompt = message


    # --------------------------------------
    # Build conversation for Gemini
    # --------------------------------------

    contents = []


    for previous in previous_messages:

        contents.append({
            "role": previous["role"],
            "parts": [
                {
                    "text": previous["message"]
                }
            ]
        })


    # Add current user message

    contents.append({
        "role": "user",
        "parts": [
            {
                "text": current_prompt
            }
        ]
    })


    # --------------------------------------
    # Ask Gemini
    # --------------------------------------

    for attempt in range(3):

        try:

            print(
                f"Sending request to Gemini... "
                f"Attempt {attempt + 1}/3"
            )


            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=contents
            )


            reply = response.text


            print(
                "Gemini response received successfully."
            )


            # ----------------------------------
            # Save USER message
            # ----------------------------------

            connection = get_db_connection()

            connection.execute("""
                INSERT INTO messages
                (conversation_id, role, message)
                VALUES (?, ?, ?)
            """, (
                conversation_id,
                "user",
                message
            ))


            # ----------------------------------
            # Save BOT message
            # ----------------------------------

            connection.execute("""
                INSERT INTO messages
                (conversation_id, role, message)
                VALUES (?, ?, ?)
            """, (
                conversation_id,
                "model",
                reply
            ))


            connection.commit()

            connection.close()


            # ----------------------------------
            # Send response to frontend
            # ----------------------------------

            return jsonify({
                "reply": reply
            }), 200


        except Exception as e:

            error_message = str(e)

            print(
                f"GEMINI ERROR "
                f"(Attempt {attempt + 1}/3): "
                f"{repr(e)}"
            )


            # ----------------------------------
            # Temporary Gemini server problem
            # ----------------------------------

            if (
                "503" in error_message
                or "UNAVAILABLE" in error_message
            ):

                if attempt < 2:

                    wait_time = 2 ** attempt

                    time.sleep(wait_time)

                    continue


                return jsonify({
                    "reply":
                    "Gemini is temporarily busy. "
                    "Please try again in a few seconds."
                }), 503


            # ----------------------------------
            # Rate limit / quota
            # ----------------------------------

            if (
                "429" in error_message
                or "RESOURCE_EXHAUSTED" in error_message
                or "rate limit" in error_message.lower()
                or "quota" in error_message.lower()
            ):

                return jsonify({
                    "reply":
                    "Gemini API rate limit or quota "
                    "has been reached."
                }), 429


            # ----------------------------------
            # Other errors
            # ----------------------------------

            return jsonify({
                "reply":
                f"Gemini error: {error_message}"
            }), 500


    return jsonify({
        "reply":
        "Gemini is temporarily unavailable."
    }), 503


# ==========================================
# PDF UPLOAD
# ==========================================

@app.route("/upload", methods=["POST"])
def upload_document():

    global document_chunks
    global document_name


    # --------------------------------------
    # Check file
    # --------------------------------------

    if "file" not in request.files:

        return jsonify({
            "message": "No file uploaded."
        }), 400


    file = request.files["file"]


    if file.filename == "":

        return jsonify({
            "message": "Please select a PDF."
        }), 400


    if not file.filename.lower().endswith(".pdf"):

        return jsonify({
            "message": "Only PDF files are supported."
        }), 400


    # --------------------------------------
    # Save PDF
    # --------------------------------------

    filename = secure_filename(file.filename)

    filepath = os.path.join(
        app.config["UPLOAD_FOLDER"],
        filename
    )


    file.save(filepath)


    # --------------------------------------
    # Extract and process PDF
    # --------------------------------------

    try:

        pages = extract_text_from_pdf(filepath)

        document_chunks = create_chunks(pages)

        document_name = filename


        print(
            f"PDF uploaded: {filename}"
        )

        print(
            f"Pages extracted: {len(pages)}"
        )

        print(
            f"Chunks created: {len(document_chunks)}"
        )


        return jsonify({
            "message":
                f"{filename} uploaded successfully.",
            "pages":
                len(pages),
            "chunks":
                len(document_chunks)
        })


    except Exception as e:

        print(
            "PDF ERROR:",
            repr(e)
        )


        return jsonify({
            "message":
                f"Could not process PDF: {str(e)}"
        }), 500


# ==========================================
# CLEAR CONVERSATION
# ==========================================

@app.route("/clear-chat", methods=["POST"])
def clear_chat():

    conversation_id = session.get(
        "conversation_id"
    )


    if conversation_id:

        connection = get_db_connection()

        connection.execute("""
            DELETE FROM messages
            WHERE conversation_id = ?
        """, (conversation_id,))

        connection.commit()

        connection.close()


    return jsonify({
        "message": "Conversation cleared."
    })


# ==========================================
# RUN APPLICATION
# ==========================================

if __name__ == "__main__":

    app.run(debug=True)