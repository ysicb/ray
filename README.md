# Creating Ray Docker Image

## Overview
This project is a chatbot conversation classifier built using FastAPI, Ray Serve, and OpenAI's GPT-4o. It retrieves chatbot conversations from a MySQL database, processes the text, and classifies conversations as successful or unsuccessful based on AI analysis.

### Features
FastAPI for REST API
Ray Serve for scalable AI inference
OpenAI GPT-4o for classification
MySQL Database integration
Docker containerization

### Installation
Prerequisites
Python 3.10+
Docker
OpenAI API key

**1. Clone the Repository**
git clone <your-repo-url>
cd <your-project-folder>

**2. Set Up the Environment**
Using Virtual Environment
python -m venv venv
venv\Scripts\activate  
pip install -r requirements.txt

**3. Configure Environment Variables**
Create a .env file in the project directory and add:
OPENAI_API_KEY=your_openai_api_key

**4. Build the Docker Image**
docker build -t ray-fastapi-app .

**5. Run the Docker Container**
docker run -p 8080:8080 -p 8265:8265 ray-fastapi-app

**6. API Endpoints and Ray Dashboard**
Try and Execute by adding valid Conversation ID:
http://localhost:8080/docs
Access the Dashboard:
http://127.0.0.1:8265/
