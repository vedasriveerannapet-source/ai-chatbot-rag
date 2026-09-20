import os
from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ==========================================
# PDF TEXT EXTRACTION
# ==========================================

def extract_text_from_pdf(pdf_path):

    reader = PdfReader(pdf_path)

    pages = []

    for page_number, page in enumerate(reader.pages):

        text = page.extract_text()

        if text:

            pages.append({
                "page": page_number + 1,
                "text": text
            })

    return pages


# ==========================================
# TEXT CHUNKING
# ==========================================

def create_chunks(pages, chunk_size=1000, overlap=200):

    chunks = []

    for page in pages:

        text = page["text"]

        start = 0

        while start < len(text):

            end = start + chunk_size

            chunk_text = text[start:end]

            if chunk_text.strip():

                chunks.append({
                    "page": page["page"],
                    "text": chunk_text
                })

            start += chunk_size - overlap

    return chunks


# ==========================================
# SEARCH DOCUMENT
# ==========================================

def search_document(chunks, question, top_k=4):

    if not chunks:

        return []


    documents = [
        chunk["text"]
        for chunk in chunks
    ]


    vectorizer = TfidfVectorizer(
        stop_words="english"
    )


    try:

        document_vectors = vectorizer.fit_transform(
            documents
        )

        question_vector = vectorizer.transform(
            [question]
        )

    except ValueError:

        return []


    similarities = cosine_similarity(
        question_vector,
        document_vectors
    ).flatten()


    # Get best matching chunks

    best_indices = similarities.argsort()[::-1][:top_k]


    results = []

    for index in best_indices:

        if similarities[index] > 0:

            results.append({
                "page": chunks[index]["page"],
                "text": chunks[index]["text"],
                "score": float(similarities[index])
            })


    return results
if __name__ == "__main__":

    pdf_path = "uploads/test.pdf"

    pages = extract_text_from_pdf(pdf_path)

    print("Pages found:", len(pages))

    chunks = create_chunks(pages)

    print("Chunks created:", len(chunks))

    results = search_document(
        chunks,
        "What is normalization?"
    )

    for result in results:

        print("\nPAGE:", result["page"])
        print(result["text"][:500])