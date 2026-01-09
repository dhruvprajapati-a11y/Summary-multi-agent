# Multi-Agent System Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    MULTI-AGENT SYSTEM                           │
│                                                                 │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐ │
│  │ ROOT AGENT   │─────→│ LEAD AGENT   │      │SUMMARY AGENT │ │
│  │              │      │              │      │              │ │
│  │ Orchestrator │      │ User-Facing  │      │   Backend    │ │
│  │   (Router)   │      │  (Collector) │      │ (Generator)  │ │
│  └──────┬───────┘      └──────┬───────┘      └──────┬───────┘ │
│         │                     │                     │         │
│         │   Routes based on   │   Validates &       │         │
│         │   status & state    │   generates         │         │
│         │                     │   summary           │         │
│         └─────────────────────┴─────────────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

## Detailed Flow

```
START
  │
  ▼
┌──────────────────┐
│   root_init      │  Initialize system, set status="init"
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  root_router     │  Decision: Where to route?
└────────┬─────────┘
         │
         ▼
┌────────────────────────────────────────────┐
│  LEAD AGENT PHASE (User Interaction)      │
├────────────────────────────────────────────┤
│                                            │
│  ┌─────────────────┐                      │
│  │  lead_ask       │ Ask for missing field│
│  └────────┬────────┘                      │
│           │                               │
│           ▼                               │
│         END (Wait for user input)         │
│           │                               │
│  User responds "John"                     │
│           │                               │
│           ▼                               │
│  ┌─────────────────┐                      │
│  │ root_router     │ Detect user message │
│  └────────┬────────┘                      │
│           │                               │
│           ▼                               │
│  ┌─────────────────┐                      │
│  │ lead_process    │ Extract & validate  │
│  └────────┬────────┘                      │
│           │                               │
│           ▼                               │
│  Back to root_router                      │
│           │                               │
│  (Repeat until all fields collected)      │
│           │                               │
│           ▼                               │
│  ┌─────────────────┐                      │
│  │ lead_confirm    │ Show all data       │
│  └────────┬────────┘                      │
│           │                               │
│           ▼                               │
│         END (Wait for confirmation)       │
│           │                               │
│  User responds "Yes"                      │
│           │                               │
│           ▼                               │
│  ┌─────────────────┐                      │
│  │lead_confirm     │ Parse: User         │
│  │    _parse       │ confirmed!          │
│  └────────┬────────┘ Set status=          │
│           │         "generating_summary"  │
└───────────┼────────────────────────────────┘
            │
            ▼
┌───────────────────────────────────────────────┐
│  ROOT AGENT ROUTING                           │
│  Detects status="generating_summary"          │
│  Routes to → SUMMARY AGENT                    │
└───────────┬───────────────────────────────────┘
            │
            ▼
┌────────────────────────────────────────────┐
│  SUMMARY AGENT PHASE (Backend Only)        │
├────────────────────────────────────────────┤
│                                            │
│  ┌──────────────────────┐                 │
│  │ summary_validate_    │                 │
│  │   and_generate       │                 │
│  │                      │                 │
│  │ 1. Validate profile  │                 │
│  │ 2. Call LLM          │                 │
│  │ 3. Generate summary  │                 │
│  │ 4. Retry on error    │                 │
│  │ 5. Fallback if needed│                 │
│  └──────────┬───────────┘                 │
│             │                             │
│             │ Set status="completed"      │
│             │ Set summary_text            │
└─────────────┼─────────────────────────────┘
              │
              ▼
┌──────────────────────┐
│  root_finalize       │  Format & show summary to user
└──────────┬───────────┘
           │
           ▼
          END (Completed)
```

## Agent Responsibilities

### ROOT AGENT (Orchestrator)
- **Does NOT** interact with user directly
- **Decides** routing based on status
- **Coordinates** between Lead and Summary agents
- **Manages** overall workflow state

**Key Nodes:**
- `root_init` - Initialize system
- `root_router` - Decision making
- `root_finalize` - Present final summary

### LEAD AGENT (User-Facing)
- **Interacts** with user via chat
- **Collects** profile data (name, email, mobile, age, city)
- **Validates** user input
- **Confirms** data with user before handoff

**Key Nodes:**
- `lead_ask_question` - Ask for missing fields
- `lead_process_answer` - Extract & validate data
- `lead_confirm_profile` - Show collected data
- `lead_confirm_parse` - Handle confirmation/edits

### SUMMARY AGENT (Backend)
- **NO user interaction** - pure backend
- **Receives** validated profile from Lead Agent
- **Generates** professional summary using LLM
- **Handles** errors with retry logic and fallback

**Key Node:**
- `summary_validate_and_generate` - Validate + Generate

## State Flow

```
MultiAgentState {
  // Shared
  messages: []              // Conversation history
  profile: {}               // User data
  current_agent: "root"     // Active agent
  status: "init"            // Workflow status
  
  // Lead Agent
  lead_last_field_asked: null
  lead_required_fields: ["name", "email", "mobile", "age", "city"]
  lead_user_confirmed: false
  lead_just_processed: false
  
  // Summary Agent
  summary_text: null
  summary_status: "pending"
}
```

## Example Execution

```
User: <starts system>
ROOT: Initialize → Route to Lead Agent

LEAD: "What's your full name?"
User: "John Doe"
ROOT: Route to Lead Agent (process)
LEAD: Extract "John Doe" → Validate ✓ → Store

ROOT: Route to Lead Agent (ask next)
LEAD: "What's your email?"
User: "john@example.com"
ROOT: Route to Lead Agent (process)
LEAD: Extract "john@example.com" → Validate ✓ → Store

... (continues for mobile, age, city) ...

ROOT: All fields collected → Route to Lead Agent (confirm)
LEAD: "Please confirm: Name: John Doe, Email: john@example.com..."
User: "Yes"
ROOT: User confirmed → Route to Summary Agent

SUMMARY: 🎯 Validate profile ✓
SUMMARY: 🎯 Call LLM...
SUMMARY: 🎯 Generated: "Meet John Doe, a 30-year-old..."

ROOT: Summary complete → Finalize
ROOT: Show to user: "✅ Profile Saved! [summary]"

System: COMPLETED
```

## Key Features

✅ **Clear Separation**: Each agent has distinct responsibilities
✅ **No User Interaction in Backend**: Summary Agent is pure backend
✅ **Robust Error Handling**: Validation, retry, fallback
✅ **Stateful Workflow**: Checkpointer maintains conversation
✅ **Flexible Routing**: Root Agent handles all decisions
✅ **LLM-Powered**: Natural language understanding throughout

## Run the System

```bash
cd "/Users/dhruvrajkotia/Documents/Dhruv Prajapati/summary-agent"
python3 multi_agent_cli.py
```

## Files Created

1. `multi_agent_state.py` - State definition
2. `root_agent.py` - Root orchestrator agent
3. `lead_agent.py` - Lead collection agent
4. `summary_agent.py` - Summary generation agent
5. `multi_agent_graph.py` - Graph builder
6. `multi_agent_cli.py` - CLI interface
