from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from organizer import run_organizer

import json
import webbrowser
import threading
import uvicorn

def open_browser():
    webbrowser.open("http://localhost:8000")

if __name__ == "__main__":
    threading.Timer(1.5, open_browser).start()
    uvicorn.run(app, host="127.0.0.1", port=8000)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

class OrganizeRequest(BaseModel):
    folder: str

@app.post("/organize")
def organize_files(request: OrganizeRequest):
    result = run_organizer(request.folder)
    return {"summary": result}

@app.get("/organize-stream")
def organize_files_stream(folder: str):
    def event_stream():
        logs = []

        def log_callback(msg):
            logs.append(f"data: {json.dumps({'type': 'log', 'text': msg})}\n\n")
        #yeild tool calls logs
        yield f"data: {json.dumps({'type': 'log', 'text': 'Starting...'})}\n\n"

        summary = run_organizer(folder, log_callback)

        for log in logs:
            yield log
        #yield final summary
        yield f"data: {json.dumps({'type': 'summary', 'text': summary})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")