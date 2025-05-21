from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel
import os
import logging
import sys
from speech_recognition_utils import SpeechProcessor, capture_audio
from audio_processing import is_valid_audio, extract_features
import tempfile
from typing import Dict, Any, Optional
from .config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("api")

# Initialize app with metadata
app = FastAPI(
    title="Waray Speech Recognition API",
    description="API for analyzing pronunciation in Waray language learning",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize speech processor (singleton)
speech_processor = None

def get_speech_processor():
    """Get or initialize speech processor singleton."""
    global speech_processor
    if speech_processor is None:
        try:
            speech_processor = SpeechProcessor(
                model_path=settings.MODEL_PATH,
                encoder_path=settings.ENCODER_PATH
            )
            logger.info(f"Speech processor initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing speech processor: {e}")
            raise HTTPException(
                status_code=500, 
                detail="Speech recognition service unavailable"
            )
    return speech_processor

class PredictionResponse(BaseModel):
    """Schema for prediction response."""
    predicted_word: Optional[str] = None
    confidence: Optional[float] = None
    phoneme_confidence: Optional[Dict[str, float]] = None
    pronunciation_errors: Optional[list] = None

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    try:
        # Check if speech processor can be initialized
        processor = get_speech_processor()
        return {
            "status": "healthy",
            "model_loaded": processor.model is not None
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@app.post("/predict-speech/", response_model=PredictionResponse)
async def predict_speech(
    audio: UploadFile = File(...), 
    expected_word: str = None,
    processor: SpeechProcessor = Depends(get_speech_processor)
):
    """Process uploaded audio and return speech recognition results."""
    # Validate content type
    if not audio.content_type.startswith("audio/"):
        raise HTTPException(
            status_code=400, 
            detail="File must be audio format"
        )
    
    # Save the uploaded file temporarily
    temp_audio_path = tempfile.mktemp(suffix='.wav')
    try:
        # Read in chunks to control memory usage
        max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        file_size = 0
        with open(temp_audio_path, "wb") as temp_file:
            chunk = await audio.read(1024)
            while chunk:
                file_size += len(chunk)
                if file_size > max_size:
                    raise HTTPException(
                        status_code=413,
                        detail=f"File too large (max {settings.MAX_UPLOAD_SIZE_MB}MB)"
                    )
                temp_file.write(chunk)
                chunk = await audio.read(1024)
        
        # Process with speech processor
        predicted_word, confidence, phoneme_confidence = processor.predict_speech(
            temp_audio_path, expected_word
        )
        
        # Get pronunciation errors if available
        pronunciation_errors = getattr(processor, 'pronunciation_errors', [])
        
        return {
            "predicted_word": predicted_word,
            "confidence": float(confidence) if confidence is not None else None,
            "phoneme_confidence": {k: float(v) for k, v in phoneme_confidence.items()} if phoneme_confidence else None,
            "pronunciation_errors": pronunciation_errors
        }
    
    except Exception as e:
        logger.error(f"Error processing speech: {e}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")
    
    finally:
        # Clean up temp file
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)

if __name__ == "__main__":
    logger.info(f"Starting API server on {settings.API_HOST}:{settings.API_PORT}")
    uvicorn.run(
        "server.api:app", 
        host=settings.API_HOST, 
        port=settings.API_PORT,
        reload=not settings.PRODUCTION,
        workers=4 if settings.PRODUCTION else 1
    )