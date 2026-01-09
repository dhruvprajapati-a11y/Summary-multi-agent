"""
Summary Agent - Backend agent that generates summaries (no user interaction)
"""
from __future__ import annotations
from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from multi_agent_state import MultiAgentState
from prompts import SUMMARY_SYSTEM
import time

def _llm(model: str = "gpt-4o-mini", temperature: float = 0.7) -> ChatOpenAI:
    return ChatOpenAI(model=model, temperature=temperature, timeout=30, max_retries=2)

# ==========================================
# SUMMARY AGENT - Backend Summary Generation
# ==========================================

def summary_validate_and_generate(state: MultiAgentState) -> Dict[str, Any]:
    """
    Summary Agent generates summary based on collected profile.
    No user interaction; runs in backend.
    1. Uses LLM to generate summary.
    2. Validates summary.
    3. If fails, retries with exponential backoff.
    4. If all retries fail, falls back to template-based summary.
    5. Updates state with summary and status.
    6. Marks overall status as 'completed' or 'failed'.
    7. Returns updated state.
    """
    print("\n🎯 SUMMARY AGENT - Starting (Backend - No User Interaction)")
    print("="*60)
    
    profile = state["profile"]

    # no any concept of skipped fields in summary agent, it just summarizes whatever is present in profile simple text
    profile_text = "\n".join(f"{field.title()}: {value}" for field, value in profile.items())
    
    # Generate summary using LLM
    print("🎯 SUMMARY AGENT - Generating summary...")

    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            print(f"🎯 SUMMARY AGENT - Attempt {attempt + 1}/{max_retries}")
            
            llm = _llm()
            start_time = time.time()
            
            resp = llm.invoke([
                SystemMessage(content=SUMMARY_SYSTEM),
                HumanMessage(content=f"Create a professional lead summary for:\n\n{profile_text}")
            ])
            
            elapsed = time.time() - start_time
            summary = resp.content.strip()
            
            # Validate summary
            if len(summary) < 50:
                raise ValueError("Summary too short")
            
            print(f"🎯 SUMMARY AGENT - ✓ Summary generated in {elapsed:.2f}s")
            print(f"🎯 SUMMARY AGENT - Summary preview: {summary[:100]}...")
            
            return {
                "summary_text": summary,
                "summary_status": "completed",
                "status": "completed",
                "current_agent": "summary",
            }
        
        except Exception as e:
            print(f"🎯 SUMMARY AGENT - ⚠️ Attempt {attempt + 1} failed: {e}")
            
            if attempt == max_retries - 1:
                # Fallback to template-based summary
                print("🎯 SUMMARY AGENT - Using fallback template")
                fallback = _generate_fallback_summary(profile)
                
                return {
                    "summary_text": fallback,
                    "summary_status": "completed",
                    "status": "completed",
                    "current_agent": "summary",
                    "summary_error": f"Used fallback due to: {str(e)}",
                }
            
            # Wait before retry
            wait_time = 2 ** attempt
            print(f"🎯 SUMMARY AGENT - Retrying in {wait_time}s...")
            time.sleep(wait_time)
    
    # Should never reach here
    return {
        "summary_status": "failed",
        "summary_error": "All retry attempts failed",
        "status": "failed",
        "current_agent": "summary",
    }

def _generate_fallback_summary(profile: Dict[str, Any]) -> str:
    """Generate simple template-based summary without LLM"""
    print("🎯 SUMMARY AGENT - Generating fallback summary")
    
    summary_lines = ["📊 Lead Profile Summary", ""]
    for field, value in profile.items():
        summary_lines.append(f"- {field.title()}: {value}")

    summary_lines.extend([
        "",
        "✅ Status: Profile collected and validated",
        f"⏰ Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}"
    ])
    return "\n".join(summary_lines)
