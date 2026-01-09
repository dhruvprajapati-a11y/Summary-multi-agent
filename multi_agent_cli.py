#!/usr/bin/env python3
"""
Multi-Agent CLI - Command-line interface for the multi-agent system
"""
from __future__ import annotations

import uuid
from langchain_core.messages import HumanMessage, AIMessage

from multi_agent_graph import build_multi_agent_graph


def main():
    """Main CLI loop"""
    
    print("\n" + "="*70)
    print("🤖 MULTI-AGENT LEAD COLLECTION SYSTEM".center(70))
    print("="*70)
    print("\n📋 Architecture:")
    print("  • ROOT AGENT   - Orchestrates workflow")
    print("  • LEADGEN AT   - Collects your information")
    print("  • SUMMARY AGENT - Generates summary (backend)")
    print("\n" + "="*70 + "\n")
    
    # Build graph
    app, init_state = build_multi_agent_graph()
    
    # Create thread
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    print(f"🔗 Session ID: {thread_id}\n")
    
    # Initialize - invoke with empty dict to start from entry point
    out = app.invoke({}, config=config)
    
    # Main conversation loop
    while True:
        # Check if completed
        if out.get("status") == "completed":
            # Show final message
            if out.get("messages"):
                for msg in out["messages"]:
                    if isinstance(msg, AIMessage):
                        print(f"\n{msg.content}")
            print("\n" + "="*70)
            print("✅ SESSION COMPLETED".center(70))
            print("="*70 + "\n")
            break
        
        # Check if failed
        if out.get("status") == "failed":
            print("\n" + "="*70)
            print("❌ SESSION FAILED".center(70))
            print("="*70)
            error = out.get("summary_error", "Unknown error")
            print(f"\nError: {error}\n")
            break
        
        # Show agent's message
        if out.get("messages"):
            last_msg = out["messages"][-1]
            if isinstance(last_msg, AIMessage):
                print(f"\n💬 Agent: {last_msg.content}")
        
        # Get user input
        try:
            user_input = input("\n👤 You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nGoodbye! 👋\n")
            break
        
        if not user_input:
            continue
        
        # Check for exit commands
        if user_input.lower() in ["exit", "quit", "bye", "/exit"]:
            print("\nGoodbye! 👋\n")
            break
        
        # New thread
        if user_input.lower() == "/new":
            thread_id = str(uuid.uuid4())
            config = {"configurable": {"thread_id": thread_id}}
            print(f"\n🔗 New Session ID: {thread_id}\n")
            out = app.invoke({}, config=config)
            continue
        
        # Send user message to graph - it will resume from where it left off
        out = app.invoke(
            {"messages": [HumanMessage(content=user_input)]},
            config=config
        )


if __name__ == "__main__":
    main()
