from __future__ import annotations

from typing import Dict, Any, List, Optional, Tuple

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from state import GraphState
from config import REQUIRED_FIELDS, OPTIONAL_FIELDS, MAX_ATTEMPTS_PER_FIELD
from validators import normalize, validate, compute_missing

from prompts import LEAD_SYSTEM, SUMMARY_SYSTEM

# If you want OpenAI-backed responses:
from langchain_openai import ChatOpenAI


# Helper: LLM instance 
def _llm(model: str = "gpt-4o-mini", temperature: float = 0.2) -> ChatOpenAI:
    return ChatOpenAI(model=model, temperature=temperature)


def init_state() -> GraphState:
    print("Initializing graph state...")
    return {
        "messages": [],
        "profile": {},
        "status": "collecting",
        "last_field_asked": None,
        "just_processed": False,
        "required_fields": list(REQUIRED_FIELDS),
        "optional_fields": list(OPTIONAL_FIELDS),
        "attempts_per_field": {},
        "max_attempts": MAX_ATTEMPTS_PER_FIELD,
        "errors": [],
        "user_confirmed": False,
        "summary_text": None,
    }


# -------------------------
# Node 1: Root Router
# -------------------------
def root_router(state: GraphState) -> Dict[str, Any]:
    print("\nNode 1 - Root Router")
    # Deterministic routing based on state status and messages
    if state["status"] == "done":
        return {}

    if state["status"] == "handoff":
        return {}

    if state["status"] == "ready_to_summarize" and state["user_confirmed"]:
        return {}

    # If we're confirming, next is confirm_parse after user speaks (handled by graph edges)
    # Otherwise decide based on missing fields
    missing = compute_missing(state["profile"], state["required_fields"], state["optional_fields"])
    print(f"Missing fields: {missing}")
    if missing:
        state["status"] = "collecting"
    else:
        if state["status"] != "confirming":
            state["status"] = "confirming"

    return {"status": state["status"]}


# -------------------------
# Node 2: Lead Ask Question
# -------------------------
def lead_ask_question(state: GraphState) -> Dict[str, Any]:
    
    print("\nNode 2 - Lead Ask Question")
    # Determine next missing field to ask   

    missing = compute_missing(state["profile"], state["required_fields"], state["optional_fields"])
    
    # If nothing missing, nothing to ask 
    if not missing:
        return {}

    field = missing[0]
    state["last_field_asked"] = field

    print(f"Asking for field: {field}")
    print(f"Last field asked set to: {state['last_field_asked']}")

    # Predefined questions per field
    questions = {
        "name": "What’s your full name?",
        "email": "What’s your email address?",
        "mobile": "What’s your mobile number? (Include country code if possible)",
        "age": "What’s your age? (You can type 'skip')",
        "city": "Which city are you in? (You can type 'skip')",
    }

    # If we have a recent validation error for this field, add a hint.
    hint = ""
    for err in reversed(state["errors"]):
        if err["field"] == field:
            hint = f"\n\nNote: {err['reason']}"
            break

    # Ask the question
    msg = AIMessage(content=questions[field] + hint)
    state["messages"].append(msg)
    state["status"] = "collecting"
    return {"messages": state["messages"], "last_field_asked": field, "status": state["status"], "just_processed": False}


# -------------------------
# Helpers: extraction from free text
# -------------------------
def _extract_candidates(text: str) -> Dict[str, str]:
    """
    Lightweight extraction:
    - email via regex
    - age via 'age: 22' or standalone number if context is age question
    - phone via digits pattern
    - city/name are best captured by last_field_asked (unless user says 'city is X', 'name is Y')
    out: Dict[str, str] = {
        "email": ...,
        "mobile": ...,
        "age": ...,
        "city": ...,
        "name": ...,
    }
    """
    out: Dict[str, str] = {}


    import re # means regular expressions import

    # Email
    from validators import EMAIL_RE
    m = EMAIL_RE.search(text)
    if m:
        out["email"] = m.group(0)

    # Mobile (very naive) 
    phone_m = re.search(r"(\+?\d[\d\s\-]{7,}\d)", text)
    if phone_m:
        out["mobile"] = phone_m.group(1)

    # Age patterns - more flexible matching
    # Match "age: 22", "age is 22", "my age is 22", "age = 22", or just a number after "age"
    age_m = re.search(r"(?:my\s+)?age\s*(?:is|:|=)?\s*(\d{1,3}|skip)\b", text, flags=re.I)
    if age_m:
        out["age"] = age_m.group(1)
    
    # City patterns - more flexible
    # Match "city: NYC", "city is NYC", "my city is NYC", "in NYC", etc.
    city_m = re.search(r"(?:(?:my\s+)?city\s*(?:is|:|=)\s*)?(?:in\s+)?([A-Z][A-Za-z ]{1,20})\s*(?:city)?", text)
    if city_m:
        potential_city = city_m.group(1).strip()
        # Avoid matching common words
        if potential_city.lower() not in {"the", "my", "is", "to", "change", "update"}:
            out["city"] = potential_city

    # Name patterns - more flexible
    # Match "name: John", "name is John", "my name is John", etc.
    name_m = re.search(r"(?:my\s+)?name\s*(?:is|:|=)\s*([A-Z][A-Za-z ]{1,30})\b", text)
    if name_m:
        out["name"] = name_m.group(1).strip()

    print(f"Extracted candidates: {out}")
    return out


def _set_error(state: GraphState, field: str, reason: str) -> None:
    state["errors"].append({"field": field, "reason": reason})
    state["attempts_per_field"][field] = state["attempts_per_field"].get(field, 0) + 1


# -------------------------
# Node 3: Lead Process Answer
# -------------------------
def lead_process_answer(state: GraphState) -> Dict[str, Any]:

    print("\nNode 3 - Lead Process Answer")

    # Find last user message
    last_user = None
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage): # isinstance means checking the type of the message
            last_user = msg
            break
    if not last_user:
        return {}

    # Extract text from last user message, example: "My email is ..."
    text = last_user.content.strip() 
    last_field = state.get("last_field_asked")

    # Use LLM to extract fields from user message
    llm = _llm()
    extraction_prompt = f"""Extract user information from this message: "{text}"
    
Last field asked: {last_field}
Current profile: {state['profile']}

Return ONLY a JSON object with extracted fields like: {{"name": "John Doe", "email": "john@example.com"}}
If the user said 'skip', include that field with value "skip".
If no information found, return empty object {{}}."""
    
    resp = llm.invoke([
        SystemMessage(content=LEAD_SYSTEM),
        HumanMessage(content=extraction_prompt)
    ])
    
    # Parse LLM response to get candidates
    import json
    try:
        # Try to extract JSON from response
        content = resp.content.strip()
        # Remove markdown code blocks if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        candidates = json.loads(content.strip())
    except:
        # Fallback to regex extraction if LLM response isn't valid JSON
        candidates = _extract_candidates(text)
    
    # Always attempt to fill last_field if not extracted and we know what we asked
    if last_field and last_field not in candidates and text:
        candidates[last_field] = text

    # Validate + store
    for field, raw in candidates.items():

        val = normalize(field, raw)
        ok, reason = validate(field, val)

        if ok:
            # allow "skip" values to be stored as "skipped" marker (optional)
            if field in state["optional_fields"] and val.lower() == "skip":
                state["profile"][field] = "skipped"
            else:
                state["profile"][field] = val
        else:
            _set_error(state, field, reason)

            # If attempts exceeded for a required field -> handoff
            attempts = state["attempts_per_field"].get(field, 0)
            if field in state["required_fields"] and attempts >= state["max_attempts"]:
                state["status"] = "handoff"
                return {"status": state["status"], "profile": state["profile"], "errors": state["errors"]}

    # Decide next status
    missing = compute_missing(state["profile"], state["required_fields"], state["optional_fields"])
    if missing:
        print(f"Still missing fields after processing: {missing}")
        state["status"] = "collecting"
    else:
        print("All required fields collected.")
        state["status"] = "confirming"
        print("Now moving to confirming status")

    return {"profile": state["profile"], "status": state["status"], "errors": state["errors"], "just_processed": True}


# -------------------------
# Node 4: Confirm Profile (show summary to confirm)
# -------------------------
def confirm_profile(state: GraphState) -> Dict[str, Any]:

    print("\nNode 4 - Confirm Profile")
    
    p = state["profile"]
    lines = [
        "Please confirm these details:",
        f"- Name: {p.get('name','')}",
        f"- Email: {p.get('email','')}",
        f"- Mobile: {p.get('mobile','')}",
        f"- Age: {p.get('age','(not provided)')}", # if age skipped, show (not provided)
        f"- City: {p.get('city','(not provided)')}", # if city skipped, show (not provided)
        "",
        "Reply **Yes** to confirm, or tell me what to change (e.g., “change email to …”)."
    ]
    msg = AIMessage(content="\n".join(lines))
    print(f"Confirm message: {msg.content}")
    state["messages"].append(msg)
    state["status"] = "confirming"
    return {"messages": state["messages"], "status": state["status"], "just_processed": False}


# -------------------------
# Node 5: Confirm Parse
# -------------------------
def confirm_parse(state: GraphState) -> Dict[str, Any]:

    print("\nNode 5 - Confirm Parse")
    
    # last user message
    last_user = None
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            last_user = msg
            break
    if not last_user:
        return {}

    text = last_user.content.strip().lower()

    # Simple yes detection
    if text in {"yes", "y", "confirm", "correct", "ok", "okay"}:
        state["user_confirmed"] = True
        state["status"] = "ready_to_summarize"
        print("User confirmed! Ready to summarize.")
        return {"user_confirmed": state["user_confirmed"], "status": state["status"], "just_processed": True} 

    # Otherwise interpret as edit request (lightweight)
    candidates = _extract_candidates(last_user.content)

    print(f"Edit candidates from user: {candidates}")
    
    # If user said "change X to Y" but regex didn't catch, fallback to LLM (optional)
    if not candidates:
        # Minimal fallback: if they mention a field name, ask them to provide it clearly.
        msg = AIMessage(
            content="Got it — which field should I update (name/email/mobile/age/city), and what’s the new value?"
        )
        state["messages"].append(msg)
        state["status"] = "collecting"
        return {"messages": state["messages"], "status": state["status"], "user_confirmed": False, "just_processed": False}

    # Apply edits with validation
    for field, raw in candidates.items():
        val = normalize(field, raw)
        ok, reason = validate(field, val)
        if ok:
            # means store the value or "skipped" marker 
            # if user said "skip" for an optional field, store "skipped"
            state["profile"][field] = "skipped" if (field in state["optional_fields"] and val.lower() == "skip") else val
        else:
            _set_error(state, field, reason)
            msg = AIMessage(content=f"That {field} looks invalid. {reason} Please try again.")
            state["messages"].append(msg)
            state["status"] = "collecting"
            state["user_confirmed"] = False
            return {"messages": state["messages"], "status": state["status"], "errors": state["errors"], "just_processed": False}

    state["user_confirmed"] = False
    # If anything now missing again, go collecting; otherwise reconfirm quickly
    missing = compute_missing(state["profile"], state["required_fields"], state["optional_fields"])
    state["status"] = "collecting" if missing else "confirming"
    return {"profile": state["profile"], "status": state["status"], "user_confirmed": False, "just_processed": True}


# -------------------------
# Node 6: Summary Agent
# -------------------------
def summary_generate(state: GraphState) -> Dict[str, Any]:

    print("\nNode 6 - Summary Generate")

    p = state["profile"]

    # Option A: deterministic summary (no LLM needed)
    # text = "\n".join([
    #     "User Info Summary",
    #     f"- Name: {p.get('name','')}",
    #     f"- Email: {p.get('email','')}",
    #     f"- Mobile: {p.get('mobile','')}",
    #     f"- Age: {p.get('age','(not provided)')}",
    #     f"- City: {p.get('city','(not provided)')}",
    # ])

    # Option B: LLM enhanced summary (uncomment to use)
    llm = _llm()
    resp = llm.invoke([
        SystemMessage(content=SUMMARY_SYSTEM),
        HumanMessage(content=f"Profile:\n{p}\n\nWrite a clean summary.")
    ])
    text = resp.content

    print(f"Generated summary: {text}")

    state["summary_text"] = text
    state["status"] = "done"
    state["messages"].append(AIMessage(content=text))
    return {"summary_text": text, "status": state["status"], "messages": state["messages"]}


# -------------------------
# Node 7: Handoff/Error
# -------------------------
def handoff_error(state: GraphState) -> Dict[str, Any]:

    print("\nNode 7 - Handoff Error")

    msg = AIMessage(
        content="I’m having trouble confirming one of the required details after multiple attempts. "
                "Would you like to try again, or should we continue without it?"
    )

    print(f"Handoff message: {msg.content}")

    state["messages"].append(msg)
    # keep status = handoff until user response; router can decide next
    state["status"] = "handoff"
    return {"messages": state["messages"], "status": state["status"]}
