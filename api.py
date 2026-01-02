import json
import pandas as pd
from io import BytesIO
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager

from tools import set_dataframe, get_dataframe
from agent import create_agent, stream_query

_agent = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _agent
    _agent = await create_agent()
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    query: str
    thread_id: str = "default"


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(400, "No file provided")

    ext = file.filename.split(".")[-1].lower()
    if ext not in ["xlsx", "xls", "csv"]:
        raise HTTPException(400, "Only xlsx, xls, csv files supported")

    contents = await file.read()

    try:
        if ext == "csv":
            df = pd.read_csv(BytesIO(contents))
        else:
            df = pd.read_excel(BytesIO(contents))
    except Exception as e:
        raise HTTPException(400, f"Failed to read file: {str(e)}")

    set_dataframe(df)

    return {"filename": file.filename, "rows": len(df), "columns": list(df.columns)}


@app.post("/query/stream")
async def query_stream(request: QueryRequest):
    if get_dataframe() is None:
        raise HTTPException(400, "No data uploaded. Please upload a file first.")

    if _agent is None:
        raise HTTPException(500, "Agent not initialized")

    async def event_generator():
        async for event in stream_query(_agent, request.query, request.thread_id):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/data/preview")
async def preview_data():
    df = get_dataframe()
    if df is None:
        raise HTTPException(400, "No data uploaded")

    return {
        "columns": list(df.columns),
        "dtypes": {col: str(df[col].dtype) for col in df.columns},
        "preview": df.head(5).to_dict(orient="records"),
    }
