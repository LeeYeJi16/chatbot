from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv  
import os  

load_dotenv()

app = FastAPI()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 요청 body 구조 정의
class ChatRequest(BaseModel):
    message: str

# API 엔드포인트
@app.post("/recommend")
def chat(request: ChatRequest):
    response = client.chat.completions.create(
        model="gpt-4.1-nano",
        messages=[
            {"role": "user", "content": request.message}
        ],
    )

    return {
        "response": response.choices[0].message.content
    }