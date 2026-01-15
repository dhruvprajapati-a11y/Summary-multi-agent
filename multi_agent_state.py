from __future__ import annotations

from typing import Dict, List, Optional, Literal, Annotated
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

# Agent types
AgentType = Literal["root", "lead", "summary"]

# Overall status
Status = Literal["init", "collecting", "validating", "confirming", "generating_summary", "completed", "failed"]

class MultiAgentState(TypedDict):
    """State for multi-agent system with Root, Lead, and Summary agents"""
    
    # === SHARED STATE ===
    messages: Annotated[List[BaseMessage], add_messages]
    profile: Dict[str, str]  # Collected user data
    
    # === ROOT AGENT STATE ===
    current_agent: AgentType  # Which agent is active
    status: Status  # Overall workflow status
    
    # === LEAD AGENT STATE ===
    lead_last_field_asked: Optional[str]
    lead_required_fields: List[str]
    lead_optional_fields: List[str]
    lead_attempts_per_field: Dict[str, int]
    lead_max_attempts: int
    lead_errors: List[Dict[str, str]]
    lead_just_processed: bool
    lead_user_confirmed: bool
    
    # === SUMMARY AGENT STATE ===
    summary_text: Optional[str]
    summary_status: Literal["pending", "processing", "completed", "failed"]
    summary_error: Optional[str]
    
    # === AIRTABLE INTEGRATION ===
    airtable_record_id: Optional[str]  # ID of saved record in Airtable
