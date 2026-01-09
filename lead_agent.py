"""
Lead Agent - Collects user information through conversation
"""
from __future__ import annotations
from typing import Dict, Any
import json
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from multi_agent_state import MultiAgentState
from validators import compute_missing
from prompts import LEAD_SYSTEM

def _llm(model: str = "gpt-4o-mini", temperature: float = 0.2) -> ChatOpenAI:
    return ChatOpenAI(model=model, temperature=temperature)

# ==========================================
# LEAD AGENT - Data Collection
# ==========================================

def lead_ask_question(state: MultiAgentState) -> Dict[str, Any]:
    """Lead Agent asks for next missing field using LLM"""
    print("\n📝 LEAD AGENT - Asking question (LLM-generated)")
    
    missing = compute_missing(
        state["profile"], 
        state["lead_required_fields"], 
        state["lead_optional_fields"]
    )
    
    if not missing:
        return {"status": "confirming"}
    
    field = missing[0]
    print(f"📝 LEAD AGENT - Asking for field: {field}")
    
    # Use LLM to generate contextual question
    llm = _llm()
    
    # Build context
    context_parts = [
        f"You need to ask the user for their {field}.",
        f"Current profile data: {state['profile']}",
    ]
    
    # Add error hint if there were validation issues
    for err in reversed(state["lead_errors"]):
        if err["field"] == field:
            context_parts.append(f"Previous attempt failed: {err['reason']}")
            break
    
    # Add field-specific guidance
    if field in state["lead_optional_fields"]:
        context_parts.append(f"Note: {field} is optional - user can skip it.")
    
    question_prompt = "\n".join(context_parts)
    
    try:
        resp = llm.invoke([
            SystemMessage(content=LEAD_SYSTEM),
            HumanMessage(content=question_prompt)
        ])
        question = resp.content.strip()
        print(f"📝 LEAD AGENT - LLM generated question: {question[:100]}...")
    except Exception as e:
        print(f"📝 LEAD AGENT - LLM question generation failed: {e}, using fallback")
        # Fallback to simple question
        question = f"What's your {field}?"
        if field in state["lead_optional_fields"]:
            question += " (You can type 'skip')"
    
    return {
        "messages": [AIMessage(content=question)],
        "lead_last_field_asked": field,
        "lead_just_processed": False,
        "status": "collecting",
        "current_agent": "lead",
    }

def lead_process_answer(state: MultiAgentState) -> Dict[str, Any]:
    """Lead Agent processes user's answer using LLM"""
    print("\n📝 LEAD AGENT - Processing answer")
    
    # Find last user message
    last_user = None
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            last_user = msg
            break
    
    if not last_user:
        return {"lead_just_processed": True}
    
    text = last_user.content.strip()
    last_field = state.get("lead_last_field_asked")
    
    if not last_field:
        return {"lead_just_processed": True}
    
    # Use LLM to extract information
    llm = _llm()
    extraction_prompt = f"""Extract user information from this message: "{text}"

Field we asked for: {last_field}
Current profile: {state['profile']}

Return ONLY a JSON object with extracted fields like: {{"name": "John Doe", "email": "john@example.com"}}
If the user said 'skip', include that field with value "skip".
If no information found, return empty object {{}}.
"""
    
    try:
        resp = llm.invoke([
            SystemMessage(content=LEAD_SYSTEM),
            HumanMessage(content=extraction_prompt)
        ])
        
        content = resp.content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()
        
        candidates = json.loads(content)
    except Exception as e:
        print(f"📝 LEAD AGENT - LLM extraction failed: {e}, using text as value")
        candidates = {last_field: text}
    
    # Always attempt to fill last_field if not extracted
    if last_field not in candidates and text:
        candidates[last_field] = text
    
    print(f"📝 LEAD AGENT - Extracted: {candidates}")
    
    # Validate using LLM instead of regex patterns
    updates = {"lead_just_processed": True}
    new_profile = state["profile"].copy()
    new_errors = state["lead_errors"].copy()
    new_attempts = state["lead_attempts_per_field"].copy()
    
    # Validate each extracted field
    for field, raw in candidates.items():

        
        # Use LLM to validate the extracted value
        is_valid, reason = _validate_with_llm(field, raw, state["lead_optional_fields"])
        
        if is_valid:
            if field in state["lead_optional_fields"] and raw.lower() == "skip":
                new_profile[field] = "skipped"
            else:
                new_profile[field] = raw
            print(f"📝 LEAD AGENT - ✓ {field} = {raw} (LLM validated)")
        else:
            new_errors.append({"field": field, "reason": reason})
            new_attempts[field] = new_attempts.get(field, 0) + 1
            print(f"📝 LEAD AGENT - ✗ {field} validation failed (LLM): {reason}")
            
            # Check if max attempts exceeded
            if field in state["lead_required_fields"] and new_attempts[field] >= state["lead_max_attempts"]:
                print(f"📝 LEAD AGENT - Max attempts exceeded for {field}")
                updates["status"] = "failed"
                return updates
    
    updates["profile"] = new_profile
    updates["lead_errors"] = new_errors
    updates["lead_attempts_per_field"] = new_attempts
    
    # Use LLM to decide if we have enough information to proceed
    should_proceed = _llm_decide_ready_to_confirm(
        new_profile, 
        state["lead_required_fields"],
        state["lead_optional_fields"]
    )
    
    if should_proceed:
        print("📝 LEAD AGENT - ✓ LLM decided: Ready to confirm")
        updates["status"] = "confirming"
    else:
        print(f"📝 LEAD AGENT - LLM decided: Continue collecting")
        updates["status"] = "collecting"
    
    return updates

def lead_confirm_profile(state: MultiAgentState) -> Dict[str, Any]:
    """Lead Agent shows collected data for confirmation"""
    print("\n📝 LEAD AGENT - Showing confirmation")
    
    profile = state["profile"]
    lines = ["📋 Please confirm these details:"]
    
    for field, value in profile.items():
        display_value = value if value != "skipped" else "(skipped)"
        lines.append(f"  • {field.title()}: {display_value}")
    
    lines.append("\n✅ Reply **Yes** to confirm, or tell me what to change (e.g., 'change age to 30')")
    
    return {
        "messages": [AIMessage(content="\n".join(lines))],
        "status": "confirming",
        "lead_just_processed": False,
        "current_agent": "lead",
    }

def lead_confirm_parse(state: MultiAgentState) -> Dict[str, Any]:
    """Lead Agent parses user's confirmation or edit request"""
    print("\n📝 LEAD AGENT - Parsing confirmation")
    
    last_user = None
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            last_user = msg
            break
    
    if not last_user:
        return {"lead_just_processed": True}
    
    text = last_user.content.strip().lower()
    
    # Check for confirmation
    if text in {"yes", "y", "confirm", "correct", "ok", "okay", "looks good"}:
        print("📝 LEAD AGENT - ✓ User confirmed! Handing off to Summary Agent")
        return {
            "lead_user_confirmed": True,
            "status": "generating_summary",
            "lead_just_processed": True,
            "current_agent": "root",
        }
    
    # Extract edits using LLM
    print("📝 LEAD AGENT - User wants to make changes")
    candidates = _extract_edits_llm(last_user.content, state["profile"])
    
    if not candidates:
        return {
            "messages": [AIMessage(content="Sorry, I didn't understand. Please tell me specifically what to change (e.g., 'change age to 30')")],
            "lead_just_processed": True,
        }
    
    # Apply edits
    new_profile = state["profile"].copy()
    for field, raw in candidates.items():
        ok, _ = _validate_with_llm(field, raw, state["lead_optional_fields"])
        if ok:
            new_profile[field] = "skipped" if (field in state["lead_optional_fields"] and raw.lower() == "skip") else raw
            print(f"📝 LEAD AGENT - Updated {field} = {raw}")
    
    return {
        "profile": new_profile,
        "status": "confirming",
        "lead_just_processed": True,
    }

def _extract_edits_llm(text: str, profile: Dict[str, Any]) -> Dict[str, str]:
    """Use LLM to extract edit requests from natural language"""
    llm = _llm()
    
    prompt = f"""Extract field edits from user message.

Available fields: {list(profile.keys())}
User said: "{text}"

Return ONLY a JSON object with field names as keys and new values as values.
Example: {{"age": "30", "email": "new@example.com"}}

If no edits found, return empty object: {{}}
"""
    
    try:
        resp = llm.invoke([HumanMessage(content=prompt)])
        content = resp.content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        edits = json.loads(content.strip())
        print(f"📝 LEAD AGENT - Extracted edits: {edits}")
        return edits
    except Exception as e:
        print(f"📝 LEAD AGENT - Failed to extract edits: {e}")
        return {}

def _validate_with_llm(field: str, value: str, optional_fields: list) -> tuple[bool, str]:
    """Use LLM to validate field value"""
    print(f"📝 LEAD AGENT - Validating {field}={value} with LLM...")
    
    # Skip validation for skipped optional fields
    if field in optional_fields and value.lower() == "skip":
        return True, ""
    
    llm = _llm()
    
    validation_rules = {
        "name": "Must be a valid full name (at least 2 characters, letters and spaces only)",
        "email": "Must be a valid email address format (user@domain.com)",
        "mobile": "Must be a valid phone number (at least 10 digits, can include country code)",
        "age": "Must be a number between 1 and 120",
        "city": "Must be a valid city name (at least 2 characters, letters and spaces only)",
    }
    
    rule = validation_rules.get(field, "Must be a valid value")
    
    prompt = f"""Validate this user input:

Field: {field}
Value: "{value}"
Validation rule: {rule}

Respond with ONLY a JSON object:
{{"valid": true, "reason": ""}} if valid
{{"valid": false, "reason": "specific error message"}} if invalid

Examples:
- email "john@example.com" → {{"valid": true, "reason": ""}}
- email "notanemail" → {{"valid": false, "reason": "Invalid email format"}}
- age "25" → {{"valid": true, "reason": ""}}
- age "abc" → {{"valid": false, "reason": "Age must be a number"}}
"""
    
    try:
        resp = llm.invoke([HumanMessage(content=prompt)])
        content = resp.content.strip()
        
        # Parse JSON response
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        
        result = json.loads(content.strip())
        is_valid = result.get("valid", False)
        reason = result.get("reason", "Unknown validation error")
        
        print(f"📝 LEAD AGENT - LLM validation: {'✓ Valid' if is_valid else '✗ Invalid'}")
        return is_valid, reason
        
    except Exception as e:
        print(f"📝 LEAD AGENT - LLM validation failed: {e}, falling back to regex")

def _llm_decide_ready_to_confirm(profile: Dict[str, str], required_fields: list, optional_fields: list) -> bool:
    """Use LLM to decide if we have enough information to proceed to confirmation"""
    print(f"📝 LEAD AGENT - Asking LLM: Ready to confirm?")
    
    llm = _llm()
    
    prompt = f"""Analyze if we have enough user information to proceed:

Required fields: {required_fields}
Optional fields: {optional_fields}
Current profile: {profile}

Rules:
- ALL required fields must have valid values (not empty, not "skipped")
- Optional fields can be missing or "skipped"
- Return true only if ALL required fields are present

Respond with ONLY a JSON object:
{{"ready": true, "reason": "All required fields collected"}}
or
{{"ready": false, "reason": "Missing: field1, field2"}}
"""
    
    try:
        resp = llm.invoke([HumanMessage(content=prompt)])
        content = resp.content.strip()
        
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        
        result = json.loads(content.strip())
        ready = result.get("ready", False)
        reason = result.get("reason", "")
        
        print(f"📝 LEAD AGENT - LLM decision: {'✓ Ready' if ready else f'✗ Not ready - {reason}'}")
        return ready
        
    except Exception as e:
        print(f"📝 LEAD AGENT - LLM decision failed: {e}, using fallback logic")
        # Fallback: check if all required fields present
        missing = compute_missing(profile, required_fields, optional_fields)
        return len(missing) == 0

