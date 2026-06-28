# XEDR — AI-Powered Endpoint Security Assistant

An AI-powered endpoint monitoring and security analysis system built to explore modern cybersecurity techniques including real-time monitoring, machine learning anomaly detection, and AI-generated threat explanations.

---

## Overview

XEDR is a personal cybersecurity project that combines traditional detection methods with artificial intelligence to help users understand potential security threats on their systems.

The system monitors endpoint activities, detects suspicious behavior using rule-based and machine learning techniques, and generates human-readable explanations using large language models.

---

## Features

* Real-time process monitoring
* Network connection monitoring
* Rule-based threat detection
* Isolation Forest anomaly detection
* AI-generated threat explanations
* Risk scoring system
* FastAPI REST API
* WebSocket real-time updates
* Interactive React dashboard
* Security chat assistant
* PDF incident report generation

---

## Technology Stack

| Layer            | Technology              |
| ---------------- | ----------------------- |
| Backend          | Python, FastAPI         |
| Database         | SQLite, SQLAlchemy      |
| Monitoring       | psutil                  |
| Machine Learning | Scikit-learn            |
| AI               | Groq API (Llama 3.3)    |
| Frontend         | React, TypeScript, Vite |
| Charts           | Recharts                |
| Reports          | ReportLab               |

---

## Project Structure

```text
security-assistant/
│
├── backend/
│   ├── monitor.py
│   ├── detector.py
│   ├── ml_engine.py
│   ├── ai_engine.py
│   ├── api.py
│   ├── database.py
│   ├── report_generator.py
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   ├── public/
│   └── package.json
│
└── README.md
```

---

## Installation

### Clone the repository

```bash
git clone https://github.com/mubashirahmed1002/xedr-security-assistant.git

cd xedr-security-assistant
```

---

### Backend Setup

```bash
python -m venv venv

venv\Scripts\activate

pip install -r backend/requirements.txt
```

Create a `.env` file inside the backend folder:

```env
GROQ_API_KEY=your_api_key_here
```

---

### Frontend Setup

```bash
cd frontend

npm install
```

---

## Running the Project

### Terminal 1 – Monitoring Service

```bash
cd backend

python monitor.py
```

### Terminal 2 – API Server

```bash
cd backend

python api.py
```

### Terminal 3 – Frontend Dashboard

```bash
cd frontend

npm run dev
```

Open:

```text
http://localhost:5173
```

---

## Detection Techniques

### Rule-Based Detection

* High CPU usage detection
* Suspicious directories
* Excessive network connections
* Suspicious ports
* Orphan processes

### Machine Learning Detection

* Isolation Forest algorithm
* Feature scaling
* Behavioral anomaly detection

### AI Analysis

* Groq Llama 3.3 integration
* Human-readable explanations
* Security recommendations

---

## Future Improvements

* Linux support
* Advanced behavioral analysis
* MITRE ATT&CK mapping
* Enhanced reporting
* Cloud deployment
* Additional ML models

---

## Author

**Mubashir Ahmed**

GitHub:
https://github.com/mubashirahmed1002

---

## Disclaimer

This project was created for educational and learning purposes to explore endpoint security, machine learning, and AI-assisted cybersecurity analysis.
