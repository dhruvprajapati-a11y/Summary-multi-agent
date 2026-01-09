#!/usr/bin/env python3
from __future__ import annotations

import uuid

from langchain_core.messages import HumanMessage

from graph import build_graph


def main():
    app, init_state = build_graph()

    thread_id = str(uuid.uuid4())
    state = init_state()
    print(f"Thread ID: {thread_id}")

    # First run: router will ask first question
    out = app.invoke(state, config={"configurable": {"thread_id": thread_id}})
    # Print last assistant message if exists
    if out.get("messages"):
        from langchain_core.messages import AIMessage
        for msg in out["messages"]:
            if isinstance(msg, AIMessage):
                print(f"\nA: {msg.content}")

    while True:
        user = input("\nYou: ").strip()
        if not user:
            continue
        if user == "/exit":
            break
        if user == "/new":
            thread_id = str(uuid.uuid4())
            state = init_state()
            print(f"\nNew Thread ID: {thread_id}")
            out = app.invoke(state, config={"configurable": {"thread_id": thread_id}})
            if out.get("messages"):
                print("\nAssistant:", out["messages"][-1].content)
            continue

        # Add user message to state
        out = app.invoke(
            {"messages": [HumanMessage(content=user)]},
            config={"configurable": {"thread_id": thread_id}}
        )

        # Print any new assistant messages
        if out.get("messages"):
            from langchain_core.messages import AIMessage
            # Find and print only new AI messages
            for msg in reversed(out["messages"]):
                if isinstance(msg, AIMessage):
                    print(f"\nA: {msg.content}")
                    break


if __name__ == "__main__":
    main()
