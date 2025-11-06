from fastapi import FastAPI, WebSocket, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBearer
import asyncio
from crew_backend import crew
from auth import (
    register_user, authenticate_user, get_current_user,
    UserRegister, UserLogin, save_user_session, load_user_session
)
import json

app = FastAPI(title="CrewAI Chatbot")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

security = HTTPBearer()

# Store active WebSocket sessions by email
active_sessions = {}


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Redirect to login page"""
    return RedirectResponse(url="/login")


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})


@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    """Chat page - requires authentication via token in localStorage"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request):
    """Profile page - requires authentication via token in localStorage"""
    return templates.TemplateResponse("profile.html", {"request": request})


@app.post("/api/register")
async def register(user_data: UserRegister):
    """Register new user"""
    try:
        result = await register_user(user_data)
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.post("/api/login")
async def login(user_data: UserLogin):
    """Login existing user"""
    try:
        result = await authenticate_user(user_data)
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.get("/api/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user info"""
    return {
        "email": current_user["email"],
        "full_name": current_user["full_name"],
        "phone": current_user.get("phone"),
        "address": current_user.get("address"),
        "city": current_user.get("city"),
        "state": current_user.get("state"),
        "zipcode": current_user.get("zipcode"),
        "country": current_user.get("country")
    }


@app.get("/api/products/{product_id}")
async def get_product(product_id: int):
    """Get product details by ID"""
    for product in crew.product_rag.products:
        if product.get('id') == product_id:
            return product
    raise HTTPException(status_code=404, detail="Product not found")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    # First message should contain the JWT token
    try:
        auth_message = await websocket.receive_text()
        auth_data = json.loads(auth_message)
        token = auth_data.get("token")
        
        if not token:
            await websocket.send_text("❌ Authentication required")
            await websocket.close()
            return
        
        # Validate token and get user
        from jose import jwt, JWTError
        from auth import SECRET_KEY, ALGORITHM, users_collection
        
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            email = payload.get("sub")
            user = await users_collection.find_one({"email": email})
            
            if not user:
                await websocket.send_text("❌ Invalid authentication")
                await websocket.close()
                return
                
        except JWTError:
            await websocket.send_text("❌ Invalid token")
            await websocket.close()
            return
        
        # Load user's previous session
        user_email = user["email"]
        user_name = user["full_name"]
        saved_session = await load_user_session(user_email)
        
        if saved_session:
            # Restore context for this user
            crew.context = saved_session
            # Update customer info with current user details
            crew.context["customer_info"]["name"] = user_name
            crew.context["customer_info"]["email"] = user_email
            crew.context["customer_info"]["phone"] = user.get("phone", "")
            crew.context["customer_info"]["address"] = user.get("address", "")
            crew.context["customer_info"]["city"] = user.get("city", "")
            crew.context["customer_info"]["state"] = user.get("state", "")
            crew.context["customer_info"]["zipcode"] = user.get("zipcode", "")
            crew.context["customer_info"]["country"] = user.get("country", "")
            await websocket.send_text(f"👋 Welcome back, {user_name}! Your previous session has been restored.")
        else:
            # Initialize new session with user info
            crew.context["customer_info"]["name"] = user_name
            crew.context["customer_info"]["email"] = user_email
            crew.context["customer_info"]["phone"] = user.get("phone", "")
            crew.context["customer_info"]["address"] = user.get("address", "")
            crew.context["customer_info"]["city"] = user.get("city", "")
            crew.context["customer_info"]["state"] = user.get("state", "")
            crew.context["customer_info"]["zipcode"] = user.get("zipcode", "")
            crew.context["customer_info"]["country"] = user.get("country", "")
            await websocket.send_text(f"👋 Welcome {user_name}! Start chatting with our AI agents.")
        
        # Store active session
        active_sessions[user_email] = websocket
        
        while True:
            try:
                user_msg = await websocket.receive_text()
                
                if user_msg.lower() in ["exit", "quit"]:
                    # Save session before closing
                    await save_user_session(user_email, crew.context)
                    summary = crew.get_context_summary()
                    await websocket.send_text(f"📊 Session Summary:\n{json.dumps(summary, indent=2)}")
                    await websocket.send_text("👋 Session saved. See you next time!")
                    break
                
                # Process message
                agent_name, reply, product_ids = await asyncio.to_thread(crew.route_message, user_msg)
                
                # Send response with product IDs
                response_data = {
                    "agent": agent_name,
                    "message": reply,
                    "product_ids": product_ids
                }
                await websocket.send_text(json.dumps(response_data))
                
                # Auto-save session periodically
                await save_user_session(user_email, crew.context)
                
            except Exception as e:
                error_data = {
                    "agent": "System",
                    "message": f"⚠️ Error: {str(e)}",
                    "product_ids": []
                }
                await websocket.send_text(json.dumps(error_data))
                break
        
        # Clean up
        if user_email in active_sessions:
            del active_sessions[user_email]
        
        await websocket.close()
        
    except Exception as e:
        error_data = {
            "agent": "System",
            "message": f"⚠️ Connection error: {str(e)}",
            "product_ids": []
        }
        await websocket.send_text(json.dumps(error_data))
        await websocket.close()


@app.get("/api/summary")
async def get_summary(current_user: dict = Depends(get_current_user)):
    """Get chat summary for authenticated user"""
    return crew.get_context_summary()


@app.post("/api/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """Logout user - save session"""
    email = current_user["email"]
    await save_user_session(email, crew.context)
    return {"message": "Logged out successfully"}

if __name__ == "__main__":
    import os
    import uvicorn

    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)