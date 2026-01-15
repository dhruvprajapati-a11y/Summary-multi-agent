# Multi-Agent System Architecture

## 🎯 No-Code Agent Builder Architecture

This system works exactly like **Voiceflow, Botpress, or other no-code agent platforms**:

1. **You write prompts/config** → System builds agents automatically
2. **Root Agent** → Controls flow (user never sees this)
3. **Lead Agent** → Collects data (user-facing)
4. **Summary Agent** → Generates output (backend)
5. **Airtable** → Stores data via REST API

```
┌─────────────────────────────────────────────────────────────────────┐
│                       NO-CODE AGENT BUILDER                         │
│                                                                     │
│   ┌──────────────────────────────────────────────────────────────┐  │
│   │  agent_config.py - YOU EDIT THIS TO CHANGE BEHAVIOR          │  │
│   │  ├── ROOT_AGENT_PROMPT    → How system navigates             │  │
│   │  ├── LEAD_AGENT_PROMPT    → How to collect data              │  │
│   │  ├── SUMMARY_AGENT_PROMPT → How to generate output           │  │
│   │  ├── REQUIRED_FIELDS      → What data to collect             │  │
│   │  └── AIRTABLE_FIELD_MAPPING → How to store in Airtable       │  │
│   └──────────────────────────────────────────────────────────────┘  │
│                                ↓                                    │
│   ┌──────────────────────────────────────────────────────────────┐  │
│   │                    AGENT SYSTEM                              │  │
│   │                                                              │  │
│   │  ROOT AGENT ──→ LEAD AGENT ──→ SUMMARY AGENT ──→ AIRTABLE    │  │
│   │  (Router)       (Collector)    (Generator)       (Storage)   │  │
│   │                                                              │  │
│   └──────────────────────────────────────────────────────────────┘  │
│                                ↓                                    │
│   ┌──────────────────────────────────────────────────────────────┐  │
│   │  USER sees: Natural conversation, no complexity exposed      │  │
│   └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start - Modify agent_config.py

### Change what data to collect:
```python
REQUIRED_FIELDS = ["name", "email", "mobile"]
OPTIONAL_FIELDS = ["age", "city", "company"]  # Add new field
```

### Change how agents behave:
```python
ROOT_AGENT_PROMPT = """
Your custom instructions for how the system flows...
"""

LEAD_AGENT_PROMPT = """
Your custom personality for collecting data...
"""
```

### Change Airtable mapping:
```python
AIRTABLE_FIELD_MAPPING = {
    "name": "Full Name",      # Maps to your Airtable column
    "email": "Email Address",
    "company": "Company Name",  # New field
}
```

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
SUMMARY: 🎯 Saving to Airtable...
SUMMARY: 🎯 ✓ Data saved! Record ID: rec123...

ROOT: Summary complete → Finalize
ROOT: Show to user: "✅ Profile Saved! [summary]"

System: COMPLETED
```

## Airtable Integration

This is how **no-code agent builders** work - they collect data through conversation and store it via REST API.

```
┌─────────────────────────────────────────────────────────────────┐
│                    DATA FLOW                                    │
│                                                                 │
│  User ──→ Lead Agent ──→ Summary Agent ──→ Airtable            │
│   │         │               │                │                  │
│   │      Collects        Generates         REST API             │
│   │       data           summary           POST                 │
│   │                         │                │                  │
│   └─────────────────────────┴────────────────┘                 │
│                                                                 │
│   User never sees the complexity!                               │
└─────────────────────────────────────────────────────────────────┘
```

### Setting up Airtable

1. **Create Airtable Account**: Go to [airtable.com](https://airtable.com)

2. **Create a Base**: Create a new base called "Leads"

3. **Create Table Columns**:
   | Column Name | Field Type |
   |-------------|------------|
   | Name | Single line text |
   | Email | Email |
   | Mobile | Phone number |
   | Age | Single line text |
   | City | Single line text |
   | Summary | Long text |
   | Created At | Date time |
   | Status | Single select |

4. **Get API Key**: Go to [airtable.com/create/tokens](https://airtable.com/create/tokens)
   - Create a new token with `data.records:read` and `data.records:write` scopes

5. **Get Base ID**: Open your base, look at the URL: `airtable.com/BASEID/...`

6. **Configure Environment**:
   ```bash
   # Add to .env file
   AIRTABLE_API_KEY=pat_your_token_here
   AIRTABLE_BASE_ID=appYourBaseId
   AIRTABLE_TABLE_NAME=Leads
   ```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/airtable/status` | GET | Check Airtable configuration |
| `/api/airtable/leads` | GET | Get all leads from Airtable |

## Key Features

✅ **Clear Separation**: Each agent has distinct responsibilities
✅ **No User Interaction in Backend**: Summary Agent is pure backend
✅ **Robust Error Handling**: Validation, retry, fallback
✅ **Stateful Workflow**: Checkpointer maintains conversation
✅ **Flexible Routing**: Root Agent handles all decisions
✅ **LLM-Powered**: Natural language understanding throughout
✅ **Airtable Integration**: Automatic data storage via REST API

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
7. `airtable_service.py` - Airtable REST API integration
