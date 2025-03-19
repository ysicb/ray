from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import mysql.connector
from bs4 import BeautifulSoup
import json
import html
import re
import os
import pandas as pd
from transformers import pipeline
import ray
from ray import serve

# FastAPI app instance
app = FastAPI()

labels = ["successful", "unsuccessful"]

# Database connection function
def get_connection():
    return mysql.connector.connect(
        host="pcz218dbl23",
        user="prakashd",
        password="TLzWqu8Kyp",
        database="omni_qa_db"
    )

# Define a Pydantic model for structured response
class MessageEntry(BaseModel):
    Sender: str
    Message: str
    Timestamp: str

class ConversationResponse(BaseModel):
    ConversationId: int
    Classification: str
    ConfidenceScore: float
    Conversation: List[MessageEntry]

def clean_text(text):
    """Convert JSON or HTML text into readable format."""
    if text is None:
        return ""

    text = str(text).strip()

    try:
        if text.startswith("{") or text.startswith("["):
            parsed_text = json.loads(text)
            if isinstance(parsed_text, list):  
                return " ".join(item.get("text", "") for item in parsed_text if isinstance(item, dict))
            elif isinstance(parsed_text, dict):
                return " ".join(parsed_text.values())  
    except json.JSONDecodeError:
        pass 

    if "<" in text and ">" in text:  
        soup = BeautifulSoup(text, "html.parser")
        text = soup.get_text(separator=" ")

    text = html.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()

    return text

@serve.deployment()  # Runs this function asynchronously in Ray
class ConversationClassifier:
    def __init__(self):
        self.classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli", device=-1)

    async def __call__(self, conversation_text):
        result = self.classifier(conversation_text, labels)
        classification = result["labels"][0]
        confidence_score = round(result["scores"][0], 2)
        return classification, confidence_score

classifier = serve.run(ConversationClassifier.bind())

async def fetch_and_classify_conversation(conversation_id: int):
    connection = get_connection()
    cursor = connection.cursor()

    # Fetch incoming messages (User Messages)
    cursor.execute(f"SELECT message, conversationincomingtime FROM conversationincoming WHERE conversationId = {conversation_id}")
    incoming = cursor.fetchall()

    # Fetch outgoing messages (Bot Messages)
    cursor.execute(f"SELECT message, conversationoutgoingtime FROM conversationoutgoing WHERE conversationId = {conversation_id}")
    outgoing = cursor.fetchall()

    cursor.close()
    connection.close()

    if not incoming and not outgoing:
        return None, "Conversation ID not found"

    # Create a structured conversation list
    structured_conversation = []
    for message, timestamp in incoming:
        structured_conversation.append({"Sender": "User", "Message": clean_text(message), "Timestamp": str(timestamp)})
    for message, timestamp in outgoing:
        structured_conversation.append({"Sender": "Bot", "Message": clean_text(message), "Timestamp": str(timestamp)})
    
    # Sort the messages by timestamp
    structured_conversation.sort(key=lambda x: x["Timestamp"])

    # Format the text for classification
    conversation_text = " ".join([f"{msg['Sender']}: {msg['Message']}" for msg in structured_conversation])

    # 🔹 Use `await` instead of `ray.get()`
    classification, confidence_score = await classifier.remote(conversation_text)

    return classification, confidence_score, structured_conversation

@app.get("/conversation/{conversation_id}", 
         response_model=ConversationResponse,
         summary="Get conversation classification",
         description="Retrieve the classification result (successful or unsuccessful) and the conversation text for a given conversation ID.")
async def get_conversation_classification(conversation_id: int):
    try:
        classification, confidence_score, conversation = await fetch_and_classify_conversation(conversation_id)
        
        if classification is None:
            raise HTTPException(status_code=404, detail="Conversation ID not found")
        
        return {
            "ConversationId": conversation_id,
            "Classification": classification,
            "ConfidenceScore": confidence_score,
            "Conversation": conversation
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
