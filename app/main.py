from fastapi import FastAPI, WebSocket, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBearer
        # Validate token and get user
from jose import jwt, JWTError
from auth import SECRET_KEY, ALGORITHM
from pydantic import BaseModel
from typing import Optional
import asyncio
from crew_backend import crew
from auth import (
    register_user, authenticate_user, get_current_user,
    UserRegister, UserLogin, save_user_session, load_user_session,
    users_collection
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


class ProfileUpdate(BaseModel):
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zipcode: Optional[str] = None
    country: Optional[str] = None


@app.put("/api/update-profile")
async def update_profile(
    profile_data: ProfileUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update user profile information"""
    # Prepare update data
    update_data = {
        k: v for k, v in profile_data.dict().items() 
        if v is not None
    }
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No data to update"
        )
    
    # Update user in database
    result = await users_collection.update_one(
        {"email": current_user["email"]},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )
    
    # Get updated user data
    updated_user = await users_collection.find_one({"email": current_user["email"]})
    
    return {
        "message": "Profile updated successfully",
        "user": {
            "email": updated_user["email"],
            "full_name": updated_user["full_name"],
            "phone": updated_user.get("phone"),
            "address": updated_user.get("address"),
            "city": updated_user.get("city"),
            "state": updated_user.get("state"),
            "zipcode": updated_user.get("zipcode"),
            "country": updated_user.get("country")
        }
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
    user_email = None
    
    try:
        # Wait for authentication message with timeout
        auth_message = await asyncio.wait_for(
            websocket.receive_text(), 
            timeout=10.0
        )
        
        try:
            auth_data = json.loads(auth_message)
            token = auth_data.get("token")
        except json.JSONDecodeError:
            await websocket.send_text(json.dumps({
                "agent": "System",
                "message": "❌ Invalid authentication format",
                "product_ids": []
            }))
            await websocket.close()
            return
        
        if not token:
            await websocket.send_text(json.dumps({
                "agent": "System",
                "message": "❌ Authentication token required",
                "product_ids": []
            }))
            await websocket.close()
            return
        
        # Validate token
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            email = payload.get("sub")
            
            if not email:
                await websocket.send_text(json.dumps({
                    "agent": "System",
                    "message": "❌ Invalid token payload",
                    "product_ids": []
                }))
                await websocket.close()
                return
            
            user = await users_collection.find_one({"email": email})
            
            if not user:
                await websocket.send_text(json.dumps({
                    "agent": "System",
                    "message": "❌ User not found",
                    "product_ids": []
                }))
                await websocket.close()
                return
                
        except JWTError as e:
            print(f"JWT validation error: {e}")
            await websocket.send_text(json.dumps({
                "agent": "System",
                "message": "❌ Invalid or expired token",
                "product_ids": []
            }))
            await websocket.close()
            return
        
        # Authentication successful
        user_email = user["email"]
        user_name = user["full_name"]
        
        # Load user's previous session
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
            
            welcome_msg = f"👋 Welcome back, {user_name}! Your previous session has been restored."
            await websocket.send_text(json.dumps({
                "agent": "System",
                "message": welcome_msg,
                "product_ids": []
            }))
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
            
            welcome_msg = f"👋 Welcome {user_name}! Start chatting with our AI agents."
            await websocket.send_text(json.dumps({
                "agent": "System",
                "message": welcome_msg,
                "product_ids": []
            }))
        
        # Store active session
        active_sessions[user_email] = websocket
        
        # Main message loop
        while True:
            try:
                user_msg = await websocket.receive_text()
                
                if user_msg.lower() in ["exit", "quit"]:
                    # Save session before closing
                    await save_user_session(user_email, crew.context)
                    summary = crew.get_context_summary()
                    await websocket.send_text(json.dumps({
                        "agent": "System",
                        "message": f"📊 Session Summary:\n{json.dumps(summary, indent=2)}",
                        "product_ids": []
                    }))
                    await websocket.send_text(json.dumps({
                        "agent": "System",
                        "message": "👋 Session saved. See you next time!",
                        "product_ids": []
                    }))
                    break
                
                # Process message
                agent_name, reply, product_ids = await asyncio.to_thread(
                    crew.route_message, 
                    user_msg
                )
                
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
                print(f"Error processing message: {e}")
                import traceback
                traceback.print_exc()
                
                error_data = {
                    "agent": "System",
                    "message": f"⚠️ Error: {str(e)}",
                    "product_ids": []
                }
                await websocket.send_text(json.dumps(error_data))
                break
        
    except asyncio.TimeoutError:
        print("WebSocket authentication timeout")
        try:
            await websocket.send_text(json.dumps({
                "agent": "System",
                "message": "❌ Authentication timeout",
                "product_ids": []
            }))
        except:
            pass
        await websocket.close()
        return
        
    except Exception as e:
        print(f"WebSocket connection error: {e}")
        import traceback
        traceback.print_exc()
        
        try:
            error_data = {
                "agent": "System",
                "message": f"⚠️ Connection error: {str(e)}",
                "product_ids": []
            }
            await websocket.send_text(json.dumps(error_data))
        except:
            pass
        
    finally:
        # Clean up
        if user_email and user_email in active_sessions:
            del active_sessions[user_email]
        
        try:
            await websocket.close()
        except:
            pass

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
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)