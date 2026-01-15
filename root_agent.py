"""
Root Agent - Main orchestrator that decides routing between agents
"""
from __future__ import annotations
from typing import Dict, Any
from langchain_core.messages import HumanMessage, AIMessage
from multi_agent_state import MultiAgentState
from validators import compute_missing

def root_init(state: MultiAgentState) -> Dict[str, Any]:
    """Initialize the multi-agent system"""
    print("\n" + "="*60)
    print("🤖 ROOT AGENT - Initializing Multi-Agent System")
    print("="*60)
    
    from config import REQUIRED_FIELDS, OPTIONAL_FIELDS, MAX_ATTEMPTS_PER_FIELD
    
    return {
        "messages": [],
        "profile": {},
        "current_agent": "root",
        "status": "init",
        "lead_last_field_asked": None,
        "lead_required_fields": list(REQUIRED_FIELDS),
        "lead_optional_fields": list(OPTIONAL_FIELDS),
        "lead_attempts_per_field": {},
        "lead_max_attempts": MAX_ATTEMPTS_PER_FIELD,
        "lead_errors": [],
        "lead_just_processed": False,
        "lead_user_confirmed": False,
        "summary_text": None,
        "summary_status": "pending",
        "summary_error": None,
        "airtable_record_id": None,
    }

def root_router(state: MultiAgentState) -> str:
    """Root Agent decides which agent should handle next"""
    print(f"\n🤖 ROOT AGENT - Status: {state.get('status', 'None')}, Current Agent: {state.get('current_agent', 'None')}")
    
    # First time - need to initialize
    if not state.get("status") or state.get("status") == "":
        print("🤖 ROOT AGENT - → First invocation, initializing system")
        return "root_init"
    
    status = state["status"]
    
    # System completed
    if status == "completed":
        print("🤖 ROOT AGENT - ✓ System completed, ending")
        return "end"
    
    # System failed
    if status == "failed":
        print("🤖 ROOT AGENT - ✗ System failed, ending")
        return "end"
    
    # User just confirmed, send to Summary Agent
    if status == "generating_summary":
        print("🤖 ROOT AGENT - → Routing to SUMMARY AGENT")
        return "summary_agent"
    
    # Check if user responded to Lead Agent's question
    msgs = state["messages"]
    if len(msgs) >= 2 and isinstance(msgs[-1], HumanMessage) and isinstance(msgs[-2], AIMessage):
        if not state.get("lead_just_processed", False):
            if state["status"] == "confirming":
                print("🤖 ROOT AGENT - → User responded to confirmation, routing to LEAD AGENT (confirm parse)")
                return "lead_confirm_parse"
            elif state["status"] == "collecting":
                print("🤖 ROOT AGENT - → User responded to question, routing to LEAD AGENT (process)")
                return "lead_process"
    
    # Determine if we need to collect data or confirm
    missing = compute_missing(
        state["profile"], 
        state["lead_required_fields"], 
        state["lead_optional_fields"]
    )
    
    if missing:
        print(f"🤖 ROOT AGENT - → Missing fields: {missing}, routing to LEAD AGENT (ask)")
        return "lead_ask"
    
    # All data collected, need confirmation
    if not state.get("lead_user_confirmed", False):
        print("🤖 ROOT AGENT - → All data collected, routing to LEAD AGENT (confirm)")
        return "lead_confirm"
    
    # Shouldn't reach here
    print("🤖 ROOT AGENT - → Default routing to LEAD AGENT")
    return "lead_ask"

def root_finalize(state: MultiAgentState) -> Dict[str, Any]:
    """Root Agent finalizes and shows summary to user"""
    print("\n🤖 ROOT AGENT - Finalizing and presenting summary to user")
    
    summary = state.get("summary_text", "No summary available")
    airtable_record_id = state.get("airtable_record_id")
    
    # Build final message - user sees a clean response
    # They don't see the complexity of agents or API calls
    if airtable_record_id:
        storage_status = "✅ Your information has been securely saved."
    else:
        storage_status = "📋 Your information has been recorded."
    
    final_message = AIMessage(content=f"""
✅ **Profile Saved Successfully!**

{summary}

{storage_status}

Thank you for providing your information!
""")
    
    return {
        "messages": [final_message],
        "status": "completed",
        "current_agent": "root",
    }
