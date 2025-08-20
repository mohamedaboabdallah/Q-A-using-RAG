# Q-A-using-RAG

A Question-Answering application powered by **Retrieval-Augmented Generation (RAG)**.  
It allows users to upload documents, extract content, store embeddings, and query them using LLMs.  
The system has a **Flask backend** and a **React frontend**.

---
## Project demo link:
- [PAPYRUS](https://papyrus-production-b97b.up.railway.app/login)
## 📂 Project Structure

```plaintext
Q-A-using-RAG/
│
├── backend/                    # Backend service (Flask API)
│   ├── database/               # Database  (not tracked in Git, created automatically while running)
│   ├── chroma_store/           # Chroma storage and retrieval logic
│   ├── llms/                   # LLM interaction utilities
│   ├── text_extraction/        # Text and document extraction scripts
│   ├── user_auth/              # User authentication logic
│   ├── .env                    # Environment variables (not tracked in Git)
│   ├── requirements.txt        # Python dependencies
│   ├── server.py               # Main Flask server
|   └── .gitignore              # Git ignore rules for backend
│
├── frontend/                   # Frontend service (React)
│   ├── public/                 # Static assets
│   ├── src/                    # React components and logic
│   ├── package.json            # Node.js dependencies
|   |── .gitignore              # Git ignore rules for frontend
│   └── package-lock.json       # Dependency lock file
│
└── README.md                   # Project documentation
```

---

## 🚀 Features

- **Document Upload & Parsing** (PDF, DOCX, TXT, etc.)
- **Text Embedding & Storage** using Chroma
- **Semantic Search** on uploaded content
- **LLM-powered Question Answering**
- **User Authentication** for secure access
- **Full-Stack Architecture** with Flask (Backend) & React (Frontend)

---

## 🛠️ Installation

### 1️⃣ Clone the repository
```bash
git clone https://github.com/mohamedaboabdallah/Q-A-using-RAG.git
cd Q-A-using-RAG
```

### 2️⃣ Backend Setup
```bash
cd backend
conda create --name q_a_rag python=3.10 -y
conda activate q_a_rag
pip install -r requirements.txt
cd ..
```

### 3️⃣ Frontend Setup
```bash
cd frontend
npm install
```

---

## ⚙️ Environment Variables

Create a `.env` file inside `backend/` with the following keys:

```env
GROQ_API_KEY=your_groq_api_key
SECRET_KEY=your_app_secret
JWT_EXPIRATION=3600
JWT_REFRESH_EXPIRATION=86400
JWT_SECRET_KEY=your_jwt_secret
currency_key=your_currency_api_key
news_key=your_news_api_key
```

### 🔑 How to Get the Keys

- **GROQ_API_KEY** — Sign up at [Groq Cloud](https://console.groq.com/) and create an API key from the dashboard.  
- **news_key** - Sign up at [TheNewsApi](https://www.thenewsapi.com/) and create an API key from the dashboard.  
- **currency_key** - Sign up at [Currency Layer](https://currencylayer.com/) and create an API key from the dashboard.
- **SECRET_KEY** — A random string used by your application for cryptographic signing. You can generate one in Python:
  ```python
  import secrets
  print(secrets.token_hex(32))
  ```
- **JWT_EXPIRATION** — Time in seconds for access token expiration (e.g., `3600` = 1 hour).  
- **JWT_REFRESH_EXPIRATION** — Time in seconds for refresh token expiration (e.g., `86400` = 1 day).  
- **JWT_SECRET_KEY** — Secret used to sign JWT tokens (should be long & random). Generate with:
  ```python
  import secrets
  print(secrets.token_hex(32))
  ```
---

## ▶️ Running the Application

### Start Backend (Flask API)
```bash
cd backend
python server.py
```
Backend will run by default at: **http://localhost:5000**

### Start Frontend (React App)
```bash
cd frontend
npm start
```
Frontend will run by default at: **http://localhost:3000**

---

## 📦 Requirements

Backend dependencies are listed in:
```
backend/requirements.txt
```
Frontend dependencies are listed in:
```
frontend/package.json
```

---
## 🤝 Contributing
Pull requests are welcome!  
For major changes, please open an issue first to discuss what you’d like to change.  
---

## 📧 Contact

For any inquiries, reach out via GitHub issues or email me at mohamed541416@gmail.com.  
