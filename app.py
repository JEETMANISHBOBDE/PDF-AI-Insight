import os
import fitz  # PyMuPDF
import faiss
import numpy as np
from flask import Flask, request, render_template, jsonify
from sentence_transformers import SentenceTransformer
from openai import OpenAI

# Load API key securely
api_key = os.getenv("OPENAI_API_KEY")  # Recommended way
if not api_key:
    api_key = "api key write"  # Replace with your actual key (Less Secure)

client = OpenAI(api_key=api_key)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'  # Set upload folder

# Load embedding model
embedder = SentenceTransformer('all-MiniLM-L6-v2')

# Initialize FAISS index
d = 384  # Dimension of embeddings
index = faiss.IndexFlatL2(d)
doc_chunks = []  # Store text chunks

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def extract_text_from_pdf(pdf_path):
    """Extracts text from a PDF file."""
    text = ""
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text += page.get_text("text") + "\n"
    return text

def chunk_text(text, chunk_size=500):
    """Splits text into chunks of a given size."""
    words = text.split()
    return [' '.join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]

def add_to_faiss(chunks):
    """Adds text chunks to FAISS index."""
    global doc_chunks
    embeddings = embedder.encode(chunks)
    index.add(np.array(embeddings))
    doc_chunks.extend(chunks)

def retrieve_relevant_chunks(query, top_k=3):
    """Retrieves relevant chunks based on query."""
    query_embedding = embedder.encode([query])
    D, I = index.search(np.array(query_embedding), top_k)
    return [doc_chunks[i] for i in I[0] if i != -1]

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)
    
    text = extract_text_from_pdf(filepath)
    chunks = chunk_text(text)
    add_to_faiss(chunks)
    
    return jsonify({'message': 'File uploaded and processed successfully'})

@app.route('/ask', methods=['POST'])
def ask_question():
    """Handles user questions and fetches response from OpenAI."""
    try:
        data = request.get_json()  # Get JSON data from request
        if not data or "message" not in data:
            return jsonify({"error": "No message provided"}), 400

        user_message = data["message"]  # Extract user message
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": user_message}]
        )
        
        return jsonify({"response": response.choices[0].message["content"]})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Handle errors properly

if __name__ == '__main__':
    app.run(debug=True)
