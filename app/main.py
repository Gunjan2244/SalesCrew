from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import asyncio
from crew_backend import crew

app = FastAPI(title="CrewAI Chatbot")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def get_chat_ui(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_text("👋 Welcome to CrewAI Chatbot! Type your message below.")

    while True:
        try:
            user_msg = await websocket.receive_text()
            if user_msg.lower() in ["exit", "quit"]:
                summary = crew.get_context_summary()
                await websocket.send_text(f"📊 Session Summary:\n{summary}")
                await websocket.close()
                break

            agent_name, reply = await asyncio.to_thread(crew.route_message, user_msg)
            await websocket.send_text(f"🧠 {agent_name}: {reply}")

        except Exception as e:
            await websocket.send_text(f"⚠️ Error: {str(e)}")
            break

@app.get("/summary")
async def get_summary():
    return crew.get_context_summary()
