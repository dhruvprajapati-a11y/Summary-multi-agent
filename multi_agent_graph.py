"""
Multi-Agent Graph - Root Agent orchestrates Lead and Summary agents
"""
from __future__ import annotations

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver

from multi_agent_state import MultiAgentState
from config import CHECKPOINT_DB_PATH

# Import agents
from root_agent import root_init, root_router, root_finalize
from lead_agent import (
    lead_ask_question,
    lead_process_answer,
    lead_confirm_profile,
    lead_confirm_parse,
)
from summary_agent import summary_validate_and_generate


def build_multi_agent_graph():
    """Build multi-agent graph with Root, Lead, and Summary agents"""
    
    graph = StateGraph(MultiAgentState)
    
    # ========================================
    # ROOT AGENT NODES
    # ========================================
    graph.add_node("root_init", root_init)
    graph.add_node("root_router", lambda state: state)  # Pass-through node for routing
    graph.add_node("root_finalize", root_finalize)
    
    # ========================================
    # LEAD AGENT NODES
    # ========================================
    graph.add_node("lead_ask", lead_ask_question)
    graph.add_node("lead_process", lead_process_answer)
    graph.add_node("lead_confirm", lead_confirm_profile)
    graph.add_node("lead_confirm_parse", lead_confirm_parse)
    
    # ========================================
    # SUMMARY AGENT NODE (Backend)
    # ========================================
    graph.add_node("summary_agent", summary_validate_and_generate)
    
    # ========================================
    # GRAPH FLOW
    # ========================================
    
    # Entry point - use root_router as entry, it will handle initialization
    graph.set_entry_point("root_router")
    
    # Root router can optionally call root_init if needed
    # (we'll handle this in the routing logic)
    
    # After Lead Agent asks question, wait for user input (then re-enter at root_router)
    graph.add_edge("lead_ask", END)
    
    # After Lead Agent processes answer, go to root router to decide next step
    graph.add_edge("lead_process", "root_router")
    
    # After confirmation shown, wait for user input
    graph.add_edge("lead_confirm", END)
    
    # After parsing confirmation, go to root router to decide next step
    graph.add_edge("lead_confirm_parse", "root_router")
    
    # After Summary Agent generates summary, go to root finalize
    graph.add_edge("summary_agent", "root_finalize")
    
    # After finalization, end
    graph.add_edge("root_finalize", END)
    
    # ========================================
    # ROOT ROUTER - Conditional Edges
    # ========================================
    graph.add_conditional_edges(
        "root_router",
        root_router,
        {
            "root_init": "root_init",  # Initialize on first run
            "lead_ask": "lead_ask",
            "lead_process": "lead_process",
            "lead_confirm": "lead_confirm",
            "lead_confirm_parse": "lead_confirm_parse",
            "summary_agent": "summary_agent",
            "end": END,
        }
    )
    
    # After root_init completes, go back to root_router
    graph.add_edge("root_init", "root_router")
    
    # ========================================
    # CHECKPOINTER
    # ========================================
    import sqlite3
    conn = sqlite3.connect(CHECKPOINT_DB_PATH, check_same_thread=False)
    memory = SqliteSaver(conn)
    
    # Compile graph
    app = graph.compile(checkpointer=memory)
    
    return app, root_init


if __name__ == "__main__":
    # Test the graph structure
    app, init = build_multi_agent_graph()
    
    print("\n" + "="*60)
    print("Multi-Agent Graph Structure:")
    print("="*60)
    print("\nNodes:")
    for node in app.get_graph().nodes:
        print(f"  • {node}")
    
    print("\nEdges:")
    for edge in app.get_graph().edges:
        print(f"  • {edge}")
    
    print("\n" + "="*60)
    print("✓ Multi-agent graph compiled successfully!")
    print("="*60)
