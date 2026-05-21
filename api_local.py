# api_local.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sentiment_analyzer import mon_ia
import uvicorn

app = FastAPI(title="Sentiment Analysis API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TextRequest(BaseModel):
    text: str

@app.get("/")
def home():
    return {"status": "ok", "message": "Sentiment Analysis API"}

@app.get("/health")
def health():
    return {"status": "healthy", "service": "sentiment-api"}

@app.post("/predict")
def predict(request: TextRequest):
    result = mon_ia(request.text)
    return {
        "text": request.text,
        "sentiment": result["sentiment"],
        "confidence": result["confiance"],
        "language": result["lang"]
    }

if __name__ == "__main__":
    print("="*50)
    print("🚀 API de Sentiment Analysis")
    print("="*50)
    print("📡 http://localhost:8001")
    print("📚 Documentation: http://localhost:8001/docs")
    print("="*50)
    uvicorn.run(app, host="0.0.0.0", port=8001)
