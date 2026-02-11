# 🌾 Smart Farming AI Assistant (Endee RAG)

An intelligent **Smart Farming System** that combines **IoT, Django, and AI-powered semantic search** to help farmers monitor environmental conditions and identify crop diseases using a **Vector Database (Endee)**.

---

## 🚀 Project Overview

This project provides:

* Real-time farm monitoring (Temperature, Humidity, Soil Moisture, Air Quality)
* AI-powered crop disease assistant
* Semantic search using vector embeddings
* Efficient disease retrieval using **Endee Vector Database**
* Web interface built with **Django**

The system helps farmers make data-driven decisions, reduce crop loss, and improve productivity.

---

## 🧠 AI Architecture (RAG with Endee)

This project uses **Retrieval-Augmented Generation (RAG)**.

### Workflow

1. Crop disease data is converted into embeddings using:

   ```
   sentence-transformers/all-MiniLM-L6-v2 (384 dimensions)
   ```

2. Embeddings are stored in:
   **Endee Vector Database**

3. When a user enters symptoms:

```
User Query (Symptoms)
        ↓
Sentence Transformer → Embedding
        ↓
Endee Similarity Search
        ↓
Top Matching Disease Retrieved
        ↓
Disease Details + Treatment Returned
```

This approach:

* Avoids hallucinations
* Provides accurate domain-specific responses
* Works efficiently on low-memory systems

---

## 🛠️ Tech Stack

* Python
* Django
* Endee (Vector Database)
* Sentence Transformers
* Docker
* HTML, CSS, Bootstrap
* IoT Sensors (NodeMCU – optional integration)

---

## 📁 Project Structure

```
project_root/
│
├── chatbot/                 # Endee RAG chatbot app
├── detection/               # Crop disease detection module
├── templates/               # HTML templates
├── ingest_embeddings.py     # Script to generate and upload embeddings
├── manage.py
├── requirements.txt
│
└── endee/                   # Endee server source (Docker setup)
```

---

## ⚙️ Setup Instructions

### 1️⃣ Clone Repository

```
git clone https://github.com/ShekharPatil9120/endee-rag-semantic-search.git
cd endee-rag-semantic-search
```

---

### 2️⃣ Create Virtual Environment

```
python -m venv venv
venv\Scripts\activate
```

Install dependencies:

```
pip install -r requirements.txt
```

---

### 3️⃣ Start Endee Server

Go to Endee folder:

```
cd endee
```

Build Docker image:

```
docker build -t endee-oss:latest -f infra/Dockerfile .
```

Create persistent storage:

```
docker volume create endee-data
```

Run Endee container:

```
docker run -d --name endee-oss -p 8080:8080 -v endee-data:/var/lib/endee --restart unless-stopped endee-oss:latest
```

Check if running:

```
docker ps
```

Endee API will be available at:

```
http://localhost:8080/api/v1
```

---

### 4️⃣ Create and Upload Embeddings

Go back to project root and run:

```
python ingest_embeddings.py
```

This will:

* Load crop disease dataset
* Generate embeddings
* Store vectors in Endee index: **crop_diseases**

---

### 5️⃣ Run Django Server

```
python manage.py runserver
```

Open in browser:

Home:

```
http://localhost:8000
```

Chatbot:

```
http://localhost:8000/chat/
```

---

## 💬 Example Query

**Input**

```
rice leaves have brown spots
```

**Output**

```
Crop: Rice
Disease: Brown Spot
Treatment: ...
Confidence: 0.72
```

---

## ✨ Features

* Semantic disease search (not keyword-based)
* Confidence score for results
* Lightweight embedding model (384-dim)
* Persistent vector storage using Docker volume
* Clean Django integration
* Works locally without external APIs

---

## 🔮 Future Enhancements

* Image-based disease detection (CNN)
* Voice assistant for farmers
* Mobile application
* Cloud deployment
* Multilingual support

---

## ⭐ Why Endee?

* Lightweight and fast vector database
* Local deployment (no external dependency)
* Efficient similarity search
* Ideal for domain-specific AI applications

---

## 📌 Important Notes

Do NOT commit the following to GitHub:

```
venv/
venv_dialogflow/
__pycache__/
docker volumes
build folders
.env
```

---

## 👨‍💻 Author

**Shekhar Patil**
GitHub: https://github.com/ShekharPatil9120

---

## 📄 License

This project is for educational and research purposes.
