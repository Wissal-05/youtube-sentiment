import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.predictor import SentimentPredictor
from src.api.schemas import BatchRequest, BatchResponse, HealthResponse

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("api")
VERSION = "1.0.0"
state = {"predictor": None}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Le modèle est chargé UNE SEULE FOIS, au démarrage du serveur
    try:
        state["predictor"] = SentimentPredictor()
        log.info("Modèle chargé")
    except Exception as e:
        log.error("Échec du chargement du modèle : %s", e)
    yield


app = FastAPI(title="YouTube Sentiment API", version=VERSION, lifespan=lifespan)

# CORS : autorise les requêtes venant de l'extension Chrome
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["GET", "POST", "OPTIONS"], allow_headers=["*"])


@app.exception_handler(Exception)
async def unhandled(request: Request, exc: Exception):
    log.exception("Erreur non gérée sur %s", request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Erreur interne du serveur"})


@app.get("/health", response_model=HealthResponse)
def health():
    p = state["predictor"]
    return HealthResponse(status="ok" if p else "degraded", model_loaded=p is not None,
                          n_features=len(p.vectorizer.vocabulary_) if p else None,
                          version=VERSION)


@app.post("/predict_batch", response_model=BatchResponse)
def predict_batch(req: BatchRequest):
    p = state["predictor"]
    if p is None:
        raise HTTPException(status_code=503, detail="Modèle non chargé")
    t0 = time.perf_counter()
    predictions, stats = p.predict_batch(req.comments)
    ms = round((time.perf_counter() - t0) * 1000, 2)
    log.info("predict_batch : %d commentaires en %.1f ms", len(req.comments), ms)
    return {"predictions": predictions, "statistics": stats, "processing_time_ms": ms}