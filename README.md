# 🤖 Multi-Agent Lead Collection System

An intelligent lead collection system powered by **LangGraph** and **OpenAI GPT-4**, featuring a true multi-agent architecture with specialized agents for orchestration, data collection, and summary generation.

## 📋 Overview

This system uses a **multi-agent orchestrator pattern** to collect user information through natural conversation, validate data using LLM intelligence, and generate professional summaries. The architecture separates concerns into three specialized agents:

- **Root Agent** - Orchestrates workflow and routing decisions
- **Lead Agent** - Interacts with users to collect profile information
- **Summary Agent** - Generates professional summaries (backend only)

## 🏗️ Architecture

### System Architecture

```
                    ┌─────────────────────────────────────┐
                    │   MULTI-AGENT SYSTEM ARCHITECTURE   │
                    └─────────────────────────────────────┘

                                  👤 USER
                                    │
                                    │ Natural Language
                                    │ Conversation
                                    ↓
                    ┌──────────────────────────────────┐
                    │        LEAD AGENT                │
                    │      (User-Facing Layer)         │
                    │                                  │
                    │  ✓ Generate Questions (LLM)      │
                    │  ✓ Extract Data (LLM)            │
                    │  ✓ Validate Fields (LLM)         │
                    │  ✓ Confirm Profile               │
                    └──────────┬──────────┬────────────┘
                               │          │
                    ┌──────────┘          └──────────┐
                    │                                │
                    │ Routing                        │ Profile Data
                    │                                │
                    ▼                                ▼
    ┌───────────────────────────┐    ┌──────────────────────────────┐
    │      ROOT AGENT           │    │      SUMMARY AGENT           │
    │  (Orchestration Layer)    │    │     (Backend Layer)          │
    │                           │    │                              │
    │  ✓ Initialize System      │    │  ✓ Validate Profile          │
    │  ✓ Route Between Agents   │◄───┤  ✓ Generate Summary (LLM)   │
    │  ✓ Manage State           │    │  ✓ Retry Logic (3x)          │
    │  ✓ Finalize Output        │    │  ✓ Template Fallback         │
    └───────────────────────────┘    └──────────────────────────────┘
                    │
                    │ Final Summary
                    ▼
                  👤 USER
```

### Agent Responsibilities

```
╔═══════════════════════════════════════════════════════════════════╗
║                        ROOT AGENT                                 ║
║                      (Orchestrator)                               ║
╠═══════════════════════════════════════════════════════════════════╣
║  • NO direct user interaction                                     ║
║  • Initializes system state                                       ║
║  • Routes requests to Lead/Summary agents                         ║
║  • Manages overall workflow                                       ║
║  • Presents final summary to user                                 ║
╚═══════════════════════════════════════════════════════════════════╝

╔═══════════════════════════════════════════════════════════════════╗
║                        LEAD AGENT                                 ║
║                      (User-Facing)                                ║
╠═══════════════════════════════════════════════════════════════════╣
║  • Direct user conversation                                       ║
║  • LLM-generated contextual questions                             ║
║  • LLM-based data extraction from natural language                ║
║  • LLM-powered validation (email, phone, age, etc.)               ║
║  • Profile confirmation and editing                               ║
║  • Collects: name, email, mobile, age, city                       ║
╚═══════════════════════════════════════════════════════════════════╝

╔═══════════════════════════════════════════════════════════════════╗
║                      SUMMARY AGENT                                ║
║                        (Backend)                                  ║
╠═══════════════════════════════════════════════════════════════════╣
║  • NO user interaction (pure backend)                             ║
║  • Validates complete profile data                                ║
║  • Generates professional summary via LLM                         ║
║  • Automatic retry mechanism (up to 3 attempts)                   ║
║  • Template fallback on failure                                   ║
╚═══════════════════════════════════════════════════════════════════╝
```

### Detailed Flow Diagram

```
START
  │
  ▼
┌──────────────────┐
│  ROOT ROUTER     │  Entry Point
│  (Decision Node) │
└────────┬─────────┘
         │
         ├─── First Run? ──────────┐
         │                         ▼
         │                   ┌──────────────┐
         │                   │  ROOT INIT   │  Initialize State
         │                   └──────┬───────┘
         │                          │
         ▼                          ▼
    ┌────────────────────────────────────────┐
    │         LEAD AGENT PHASE               │
    │    (User Interaction Loop)             │
    ├────────────────────────────────────────┤
    │                                        │
    │  ┌─────────────────┐                  │
    │  │   LEAD ASK      │  Ask for field   │
    │  └────────┬────────┘                  │
    │           │                           │
    │           ▼                           │
    │      [WAIT FOR USER INPUT]            │
    │           │                           │
    │           ▼                           │
    │  ┌─────────────────┐                  │
    │  │ LEAD PROCESS    │  Extract &       │
    │  │                 │  Validate        │
    │  └────────┬────────┘                  │
    │           │                           │
    │           ▼                           │
    │  ┌─────────────────┐                  │
    │  │  ROOT ROUTER    │  More fields?    │
    │  └────────┬────────┘                  │
    │           │                           │
    │      YES──┴──NO                       │
    │       │       │                       │
    │       └───────┼─────► Continue Loop   │
    │               │                       │
    │               ▼                       │
    │  ┌─────────────────┐                  │
    │  │ LEAD CONFIRM    │  Show profile    │
    │  └────────┬────────┘                  │
    │           │                           │
    │           ▼                           │
    │      [WAIT FOR CONFIRMATION]          │
    │           │                           │
    │           ▼                           │
    │  ┌─────────────────┐                  │
    │  │LEAD CONFIRM     │  Parse yes/no/   │
    │  │    PARSE        │  edit            │
    │  └────────┬────────┘                  │
    │           │                           │
    └───────────┼────────────────────────────┘
                │
         Confirmed?
                │
                ▼
    ┌────────────────────────────┐
    │   SUMMARY AGENT PHASE      │
    │      (Backend Only)        │
    ├────────────────────────────┤
    │                            │
    │  ┌──────────────────┐      │
    │  │  SUMMARY AGENT   │      │
    │  │                  │      │
    │  │  1. Validate     │      │
    │  │  2. Call LLM     │      │
    │  │  3. Generate     │      │
    │  │  4. Retry x3     │      │
    │  │  5. Fallback     │      │
    │  └────────┬─────────┘      │
    │           │                │
    └───────────┼─────────────────┘
                │
                ▼
    ┌────────────────────┐
    │  ROOT FINALIZE     │  Show summary
    └────────┬───────────┘
             │
             ▼
            END
```

### State Transitions

```
 ┌─────────────────────────────────────────────────────────────┐
 │                    SESSION LIFECYCLE                        │
 └─────────────────────────────────────────────────────────────┘

  [START]
     │
     ▼
  ┌──────┐
  │ INIT │  System initialized
  └───┬──┘
      │
      ▼
  ┌────────────┐
  │ COLLECTING │◄───┐  Gathering user data
  └─────┬──────┘    │
        │           │  Loop: Ask → Process → Validate
        │           │
        ├───────────┘
        │
        │  All fields collected
        ▼
  ┌────────────┐
  │ CONFIRMING │  Show data for approval
  └─────┬──────┘
        │
        ├─── Edit? ───► Back to COLLECTING
        │
        │  Confirmed
        ▼
  ┌──────────────────┐
  │ GENERATING       │  Backend processing
  │ SUMMARY          │
  └─────┬────────────┘
        │
        ▼
  ┌───────────┐
  │ COMPLETED │  Session end
  └───────────┘
        │
        ▼
     [END]
```

## ✨ Features

### 🧠 LLM-Powered Intelligence
- **Dynamic Question Generation**: Contextual questions based on conversation flow
- **Smart Data Extraction**: Extracts structured data from natural language
- **Intelligent Validation**: LLM validates email, phone, age, and other fields
- **Decision Making**: LLM decides when enough data is collected

### 🔄 Multi-Agent Architecture
- **Root Agent**: Pure orchestrator with no user interaction
- **Lead Agent**: Handles all user-facing conversation
- **Summary Agent**: Backend processing with retry logic

### 💾 State Management
- **Persistent State**: SqliteSaver checkpointer maintains conversation
- **Thread-based Sessions**: Each conversation has unique thread ID
- **Resume Capability**: Can continue conversations across restarts

### 🛡️ Robust Error Handling
- **Validation Fallbacks**: Falls back to regex if LLM validation fails
- **Retry Logic**: Summary agent retries 3 times on failure
- **Max Attempts**: Prevents infinite loops on invalid data
- **Error Messages**: Clear, helpful error messages for users

## 📁 Project Structure

```
summary-agent/
├── multi_agent_cli.py          # CLI interface for user interaction
├── multi_agent_graph.py        # LangGraph builder with routing logic
├── multi_agent_state.py        # State definition (TypedDict)
├── root_agent.py               # Root Agent (orchestrator)
├── lead_agent.py               # Lead Agent (data collector)
├── summary_agent.py            # Summary Agent (backend)
├── config.py                   # Configuration (API keys, fields)
├── prompts.py                  # System prompts for each agent
├── validators.py               # Utility functions (normalize, validate, missing)
├── requirements.txt            # Python dependencies
├── MULTI_AGENT_ARCHITECTURE.md # Detailed architecture documentation
└── README.md                   # This file
```

## 🚀 Installation

### Prerequisites
- Python 3.10 or higher
- OpenAI API key

### Setup

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd summary-agent
```

2. **Create virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
export OPENAI_API_KEY="your-openai-api-key"
```

Or create a `.env` file:
```
OPENAI_API_KEY=your-openai-api-key
```

## 🎮 Usage

### Run the Multi-Agent System

```bash
python3 multi_agent_cli.py
```

### Example Conversation

```
======================================================================
                 🤖 MULTI-AGENT LEAD COLLECTION SYSTEM                 
======================================================================

📋 Architecture:
  • ROOT AGENT   - Orchestrates workflow
  • LEAD AGENT   - Collects your information
  • SUMMARY AGENT - Generates summary (backend)

======================================================================

🔗 Session ID: abc123...

💬 Agent: What is your name?
👤 You: John Doe

💬 Agent: What is your email address?
👤 You: john@example.com

💬 Agent: What is your mobile number?
👤 You: +1234567890

💬 Agent: How old are you?
👤 You: 30

💬 Agent: Which city are you from?
👤 You: New York

💬 Agent: Let me confirm your information:

📋 Profile:
  • Name: John Doe
  • Email: john@example.com
  • Mobile: +1234567890
  • Age: 30
  • City: New York

Is this correct? (yes/no)
👤 You: yes

✅ **Profile Saved Successfully!**

Meet John Doe, a 30-year-old professional from New York. 
Contact: john@example.com | +1234567890

Thank you for providing your information!
```

## 🎯 How It Works

### 1. Initialization
- System starts with `root_router` as entry point
- Detects first run and initializes state via `root_init`
- Sets required fields: name, email, mobile, age, city

### 2. Data Collection (Lead Agent)
- **Ask Question**: LLM generates contextual question for missing field
- **Wait**: System waits for user input (graph ends at checkpoint)
- **Process**: User responds → graph resumes at `root_router` → routes to `lead_process`
- **Extract**: LLM extracts structured data from natural language
- **Validate**: LLM validates extracted value (with regex fallback)
- **Repeat**: Loop continues until all fields collected

### 3. Confirmation (Lead Agent)
- Displays collected data to user
- Asks for confirmation (yes/no/edit)
- If edits requested: LLM extracts edit commands and updates profile
- If confirmed: Sets status to `generating_summary`

### 4. Summary Generation (Summary Agent)
- Backend-only agent (no user interaction)
- Validates profile data
- Calls LLM to generate professional summary
- Retries up to 3 times on failure
- Falls back to template if all retries fail

### 5. Finalization (Root Agent)
- Presents summary to user
- Marks session as completed
- Ends conversation

## 🔧 Configuration

Edit `config.py` to customize:

```python
# Required fields
REQUIRED_FIELDS = ["name", "email", "mobile"]

# Optional fields
OPTIONAL_FIELDS = ["age", "city"]

# Max attempts per field
MAX_ATTEMPTS_PER_FIELD = 3

# Checkpoint database
CHECKPOINT_DB_PATH = "checkpoints.sqlite3"
```

## 🧪 Key Components

### Root Agent (`root_agent.py`)
- `root_init()`: Initializes system state
- `root_router()`: Decides which agent handles next
- `root_finalize()`: Presents final summary

### Lead Agent (`lead_agent.py`)
- `lead_ask_question()`: Generates contextual questions via LLM
- `lead_process_answer()`: Extracts and validates data via LLM
- `lead_confirm_profile()`: Shows collected data for confirmation
- `lead_confirm_parse()`: Handles yes/no/edit responses
- `_validate_with_llm()`: LLM-based field validation
- `_llm_decide_ready_to_confirm()`: LLM decides readiness

### Summary Agent (`summary_agent.py`)
- `summary_validate_and_generate()`: Validates + generates summary
- Retry logic with 3 attempts
- Template fallback for resilience

## 🔍 Debugging

Enable debug output by checking terminal logs:
- `🤖 ROOT AGENT` - Orchestrator decisions
- `📝 LEAD AGENT` - User interaction flow
- `📊 SUMMARY AGENT` - Backend processing

## 📊 Graph Visualization

The system uses LangGraph's conditional edges:

```python
graph.add_conditional_edges(
    "root_router",
    root_router,  # Decision function
    {
        "root_init": "root_init",
        "lead_ask": "lead_ask",
        "lead_process": "lead_process",
        "lead_confirm": "lead_confirm",
        "summary_agent": "summary_agent",
        "end": END,
    }
)
```

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📝 License

MIT License - feel free to use this project for learning or commercial purposes.

## 🙏 Acknowledgments

- **LangGraph** - State machine orchestration
- **OpenAI** - GPT-4 language model
- **LangChain** - LLM integration framework

---

**Built with ❤️ using LangGraph and OpenAI GPT-4**