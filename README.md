# Multi-agent profile intake with LangGraph

## Setup
pip install -r requirements.txt
export OPENAI_API_KEY="..."

## Run
python cli.py

## Commands
/new   -> start a fresh thread_id
/exit  -> quit

## What it does
- Lead agent collects: name, email, mobile, age, city
- Validates + normalizes
- Confirmation step
- Summary agent outputs final summary
- Uses thread_id + SQLite checkpointing to persist state
