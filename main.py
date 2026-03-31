from __future__ import annotations

"""LensLogic FastAPI service.

Endpoints:
- POST  /process           Upload photo → returns job_id (async)
- GET   /status/{job_id}   Poll pipeline progress
- GET   /download/{job_id} Stream reconstructed code file
- GET   /tree/{job_id}     Return JSON code tree
"""

import uuid
from pathlib import Path
from typing import Any, Optional

import cv2
import numpy as np
from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pipeline.detector import TextDetector
from pipeline.exporter import CodeExporter
from pipeline.ocr import CodeOCR
from pipeline.preprocessor import ImagePreprocessor
from pipeline.reconstructor import CodeReconstructor
from pydantic import BaseModel

app = FastAPI(title="LensLogic", version="1.0.0")

preprocessor = ImagePreprocessor()
detector = TextDetector(confidence_threshold=0.5)
ocr = CodeOCR(model_name="microsoft/trocr-base-handwritten")
reconstructor = CodeReconstructor()
exporter = CodeExporter(output_dir="outputs")

jobs: dict[str, dict[str, Any]] = {}


class JobStatus(BaseModel):
    job_id: str
    status: str
    result: Optional[dict] = None
    error: Optional[str] = None


@app.post("/process", response_model=JobStatus)
async def process_image(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
) -> JobStatus:
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(400, "File must be an image")

    job_id = str(uuid.uuid4())[:8]
    jobs[job_id] = {"status": "pending", "result": None, "error": None}

    image_bytes = await file.read()
    background_tasks.add_task(_run_pipeline, job_id, image_bytes)

    return JobStatus(job_id=job_id, status="pending")


def _run_pipeline(job_id: str, image_bytes: bytes) -> None:
    try:
        jobs[job_id]["status"] = "processing"

        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("Could not decode image")

        processed = preprocessor.process(image)
        regions = detector.detect(processed)
        if not regions:
            raise ValueError("No text regions detected")

        ocr_lines = ocr.transcribe_regions(processed, regions)
        code = reconstructor.reconstruct(ocr_lines)
        result = exporter.export(code, job_id=job_id)

        jobs[job_id]["status"] = "done"
        jobs[job_id]["result"] = result
    except Exception as exc:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(exc)


@app.get("/status/{job_id}", response_model=JobStatus)
def status(job_id: str) -> JobStatus:
    if job_id not in jobs:
        raise HTTPException(404, "Job not found")
    job = jobs[job_id]
    return JobStatus(
        job_id=job_id,
        status=job["status"],
        result=job.get("result"),
        error=job.get("error"),
    )


@app.get("/tree/{job_id}")
def get_tree(job_id: str) -> dict:
    if job_id not in jobs or jobs[job_id]["status"] != "done":
        raise HTTPException(404, "Job not ready or not found")
    return jobs[job_id]["result"]["code_tree"]


@app.get("/download/{job_id}")
def download_file(job_id: str) -> FileResponse:
    if job_id not in jobs or jobs[job_id]["status"] != "done":
        raise HTTPException(404, "Job not ready or not found")

    fp = Path(jobs[job_id]["result"]["file_path"])
    return FileResponse(str(fp), media_type="text/plain", filename=fp.name)
