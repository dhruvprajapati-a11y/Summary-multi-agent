"""
FastAPI Server with Streaming for Multi-Agent Lead Collection System
"""
from __future__ import annotations

import os
import uuid
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from langchain_core.messages import HumanMessage, AIMessage

from multi_agent_graph import build_multi_agent_graph

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Verify OpenAI API key
if not os.getenv("OPENAI_API_KEY"):
    print("⚠️  WARNING: OPENAI_API_KEY not found in environment variables")
    print("Please set your OpenAI API key:")
    print("  export OPENAI_API_KEY='your-api-key-here'")
    print("  or create a .env file with: OPENAI_API_KEY=your-api-key-here")

# Check Airtable configuration
if not os.getenv("AIRTABLE_API_KEY") or not os.getenv("AIRTABLE_BASE_ID"):
    print("⚠️  WARNING: Airtable not configured (optional)")
    print("To enable Airtable integration, add to .env:")
    print("  AIRTABLE_API_KEY=your_api_key_here")
    print("  AIRTABLE_BASE_ID=your_base_id_here")
    print("  AIRTABLE_TABLE_NAME=Leads")


# Initialize FastAPI app
app = FastAPI(
    title="Multi-Agent Lead Collection API",
    description="Intelligent lead collection system with streaming responses",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
graph_app = None
sessions: Dict[str, Dict[str, Any]] = {}


@app.on_event("startup")
async def startup_event():
    """Initialize graph on startup"""
    global graph_app
    print("\n" + "="*60)
    print("🚀 Starting Multi-Agent Lead Collection API")
    print("="*60)
    print(f"✓ OpenAI API Key: {'✓ Set' if os.getenv('OPENAI_API_KEY') else '✗ Missing'}")
    print(f"✓ Airtable: {'✓ Configured' if os.getenv('AIRTABLE_API_KEY') and os.getenv('AIRTABLE_BASE_ID') else '✗ Not configured (optional)'}")
    print("Building multi-agent graph...")
    
    try:
        graph_app, _ = build_multi_agent_graph()
        print("✓ Multi-agent graph built successfully!")
    except Exception as e:
        print(f"✗ Failed to build graph: {e}")
        import traceback
        traceback.print_exc()
    
    print("="*60)
    print("Server ready at http://localhost:8000")
    print("API docs at http://localhost:8000/docs")
    print("="*60 + "\n")


# In-memory session storage (use Redis in production)


# ==========================================
# Request/Response Models
# ==========================================

class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None


class SessionResponse(BaseModel):
    thread_id: str
    message: str
    timestamp: str


class StatusResponse(BaseModel):
    thread_id: str
    status: str
    profile: Dict[str, Any]
    timestamp: str


# ==========================================
# API Endpoints
# ==========================================

@app.get("/")
async def root():
    """API health check"""
    return {
        "service": "Multi-Agent Lead Collection System",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "start_session": "/api/session/start",
            "chat": "/api/chat",
            "chat_stream": "/api/chat/stream",
            "status": "/api/session/status/{thread_id}",
            "reset": "/api/session/reset/{thread_id}"
        }
    }


@app.post("/api/session/start", response_model=SessionResponse)
async def start_session():
    """Start a new conversation session"""
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    # Initialize the graph
    try:
        print(f"\n🔗 Starting new session: {thread_id}")
        output = graph_app.invoke({}, config=config)
        print(f"✓ Graph invoked successfully")
        
        # Get the last AI message
        last_message = ""
        if output.get("messages"):
            for msg in reversed(output["messages"]):
                if isinstance(msg, AIMessage):
                    last_message = msg.content
                    break
        
        if not last_message:
            last_message = "Session started. Please provide your information."
        
        # Store session
        sessions[thread_id] = {
            "config": config,
            "created_at": datetime.now().isoformat(),
            "status": output.get("status", "init"),
            "profile": output.get("profile", {})
        }
        
        return SessionResponse(
            thread_id=thread_id,
            message=last_message,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"❌ Error starting session: {str(e)}")
        print(error_details)
        raise HTTPException(status_code=500, detail=f"Failed to start session: {str(e)}")


@app.post("/api/chat", response_model=SessionResponse)
async def chat(request: ChatRequest):
    """Send a message and get response (non-streaming)"""
    thread_id = request.thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    try:
        # Invoke graph with user message
        output = graph_app.invoke(
            {"messages": [HumanMessage(content=request.message)]},
            config=config
        )
        
        # Get the last AI message
        last_message = ""
        if output.get("messages"):
            for msg in reversed(output["messages"]):
                if isinstance(msg, AIMessage):
                    last_message = msg.content
                    break
        
        # Update session
        if thread_id in sessions:
            sessions[thread_id]["status"] = output.get("status", "")
            sessions[thread_id]["profile"] = output.get("profile", {})
        else:
            sessions[thread_id] = {
                "config": config,
                "created_at": datetime.now().isoformat(),
                "status": output.get("status", ""),
                "profile": output.get("profile", {})
            }
        
        return SessionResponse(
            thread_id=thread_id,
            message=last_message,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


@app.get("/api/chat/stream")
async def chat_stream(thread_id: str, message: str):
    """Send a message and get streaming response (Server-Sent Events)"""
    import json
    config = {"configurable": {"thread_id": thread_id}}
    
    async def event_generator():
        """Generate Server-Sent Events"""
        try:
            # Send session info
            yield f"event: session\ndata: {json.dumps({'thread_id': thread_id})}\n\n"
            
            # Stream the graph execution
            for chunk in graph_app.stream(
                {"messages": [HumanMessage(content=message)]},
                config=config,
                stream_mode="updates"
            ):
                # Send each node's output
                for node_name, node_output in chunk.items():
                    # Check for messages in output
                    if "messages" in node_output and node_output["messages"]:
                        for msg in node_output["messages"]:
                            if isinstance(msg, AIMessage):
                                # Stream the AI message - use json.dumps for proper escaping
                                data = {"content": msg.content, "node": node_name}
                                yield f"event: message\ndata: {json.dumps(data)}\n\n"
                                await asyncio.sleep(0.01)  # Small delay for smooth streaming
                    
                    # Send status updates
                    if "status" in node_output:
                        data = {"status": node_output["status"], "node": node_name}
                        yield f"event: status\ndata: {json.dumps(data)}\n\n"
                    
                    # Send profile updates
                    if "profile" in node_output:
                        yield f"event: profile\ndata: {json.dumps(node_output['profile'])}\n\n"
            
            # Get final state
            final_state = graph_app.get_state(config)
            
            # Update session
            if thread_id in sessions:
                sessions[thread_id]["status"] = final_state.values.get("status", "")
                sessions[thread_id]["profile"] = final_state.values.get("profile", {})
            else:
                sessions[thread_id] = {
                    "config": config,
                    "created_at": datetime.now().isoformat(),
                    "status": final_state.values.get("status", ""),
                    "profile": final_state.values.get("profile", {})
                }
            
            # Send completion event
            yield f"event: complete\ndata: {{'status': 'done'}}\n\n"
            
        except Exception as e:
            yield f"event: error\ndata: {{'error': '{str(e)}'}}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@app.get("/api/session/status/{thread_id}", response_model=StatusResponse)
async def get_session_status(thread_id: str):
    """Get current session status and profile"""
    if thread_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[thread_id]
    return StatusResponse(
        thread_id=thread_id,
        status=session.get("status", "unknown"),
        profile=session.get("profile", {}),
        timestamp=datetime.now().isoformat()
    )


@app.delete("/api/session/reset/{thread_id}")
async def reset_session(thread_id: str):
    """Reset/delete a session"""
    if thread_id in sessions:
        del sessions[thread_id]
        return {"message": f"Session {thread_id} reset successfully"}
    else:
        raise HTTPException(status_code=404, detail="Session not found")


@app.get("/api/sessions")
async def list_sessions():
    """List all active sessions"""
    return {
        "total_sessions": len(sessions),
        "sessions": [
            {
                "thread_id": tid,
                "status": info.get("status"),
                "created_at": info.get("created_at"),
                "profile_fields": len(info.get("profile", {}))
            }
            for tid, info in sessions.items()
        ]
    }


# ==========================================
# AIRTABLE ENDPOINTS
# ==========================================
# These endpoints allow viewing leads stored in Airtable
# This is the "admin" view - users never see this

@app.get("/api/airtable/leads")
async def get_airtable_leads(max_records: int = 100):
    """Get leads from Airtable (admin endpoint)"""
    from airtable_service import get_airtable_service
    
    service = get_airtable_service()
    
    if not service.is_configured():
        raise HTTPException(
            status_code=503, 
            detail="Airtable not configured. Set AIRTABLE_API_KEY and AIRTABLE_BASE_ID."
        )
    
    result = service.get_leads(max_records)
    
    if result["success"]:
        return {
            "total": result["count"],
            "leads": result["records"]
        }
    else:
        raise HTTPException(status_code=500, detail=result["error"])


@app.get("/api/airtable/status")
async def get_airtable_status():
    """Check Airtable configuration status"""
    from airtable_service import get_airtable_service
    
    service = get_airtable_service()
    
    return {
        "configured": service.is_configured(),
        "base_id": service.base_id if service.is_configured() else None,
        "table_name": service.table_name,
        "message": "Airtable is ready" if service.is_configured() else "Airtable not configured"
    }


# ==========================================
# Run with: uvicorn api:app --reload --port 8000
# ==========================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
