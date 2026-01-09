from __future__ import annotations # for Python 3.7-3.9 compatibility

from langgraph.graph import StateGraph, START, END 
from langgraph.checkpoint.sqlite import SqliteSaver

from state import GraphState
from config import CHECKPOINT_DB_PATH 
from nodes import (
    init_state,
    root_router,
    lead_ask_question,
    lead_process_answer,
    confirm_profile,
    confirm_parse,
    summary_generate,
    handoff_error,
)
from validators import compute_missing


def build_graph():
    graph = StateGraph(GraphState)

    # Nodes
    graph.add_node("root_router", root_router)
    graph.add_node("lead_ask_question", lead_ask_question)
    graph.add_node("lead_process_answer", lead_process_answer)
    graph.add_node("confirm_profile", confirm_profile)
    graph.add_node("confirm_parse", confirm_parse)
    graph.add_node("summary_generate", summary_generate)
    graph.add_node("handoff_error", handoff_error)

    # Start
    graph.add_edge(START, "root_router")

    # Router conditional edges - determines next action
    def route_from_router(state: GraphState) -> str:
        # Check if user just responded (new HumanMessage after our question)
        # Only process if we haven't just processed this message
        if state.get("messages") and not state.get("just_processed", False):
            from langchain_core.messages import HumanMessage, AIMessage
            msgs = state["messages"]

            # Ensure at least 2 messages to check last two messages 
            if len(msgs) >= 2:
                # to get last two messages
                last_msg = msgs[-1]
                second_last = msgs[-2]
                
                # If last is human and second last was AI asking something
                if isinstance(last_msg, HumanMessage) and isinstance(second_last, AIMessage):
                    # Route to processor based on status
                    if state["status"] == "collecting" and state.get("last_field_asked"):
                        return "lead_process_answer"
                    elif state["status"] == "confirming":
                        return "confirm_parse"
        
        if state["status"] == "done":
            return "end"
        if state["status"] == "handoff":
            return "handoff_error"
        if state["status"] == "ready_to_summarize" and state["user_confirmed"]:
            return "summary_generate"

        missing = compute_missing(state["profile"], state["required_fields"], state["optional_fields"])
        if missing:
            return "lead_ask_question"

        # nothing missing -> confirm
        return "confirm_profile"

    graph.add_conditional_edges(
        "root_router",
        route_from_router,
        { 
            "lead_ask_question": "lead_ask_question", # ask next question
            "lead_process_answer": "lead_process_answer", # process answer
            "confirm_profile": "confirm_profile", # show confirmation
            "confirm_parse": "confirm_parse", # parse confirmation
            "summary_generate": "summary_generate", # generate summary
            "handoff_error": "handoff_error", # handoff on error
            "end": END, # finished
        }
    )

    # After asking question, wait for user (END causes interrupt with checkpointer)
    graph.add_edge("lead_ask_question", END)

    # After processing answer, route again
    graph.add_edge("lead_process_answer", "root_router")

    # After showing confirmation, wait for user (END causes interrupt) 
    # why not route again? because we wait for user confirmation 
    graph.add_edge("confirm_profile", END)

    # After parsing confirmation, conditionally route
    def route_after_confirm_parse(state: GraphState) -> str:
        # If we just asked for clarification (collecting status, user_confirmed=False, just_processed=False)
        # wait for user input
        if state["status"] == "collecting" and not state.get("just_processed", True):
            return "end"
        # If user confirmed and ready to summarize
        if state["status"] == "ready_to_summarize":
            return "router"
        # Otherwise continue routing (e.g., after applying edits)
        return "router"
    
    graph.add_conditional_edges(
        "confirm_parse",
        route_after_confirm_parse,
        {
            "end": END,
            "router": "root_router",
        }
    )

    # Summary finishes
    graph.add_edge("summary_generate", END)

    # Handoff waits
    graph.add_edge("handoff_error", END)

    # Checkpointer - create connection
    import sqlite3
    conn = sqlite3.connect(CHECKPOINT_DB_PATH, check_same_thread=False)
    saver = SqliteSaver(conn)
    app = graph.compile(checkpointer=saver)

    return app, init_state
