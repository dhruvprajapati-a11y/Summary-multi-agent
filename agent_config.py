"""
AGENT CONFIGURATION - No-Code Agent Builder Style
=================================================

This is how no-code agent builders work:
- You define the system behavior in ONE config file
- Root Agent reads this and orchestrates everything
- Lead Agent collects the fields you specify
- Summary Agent generates output and stores in Airtable

Just modify this file to change how the entire system works!
"""

# ==========================================
# 🤖 ROOT AGENT CONFIGURATION
# ==========================================
# This prompt defines how the entire system navigates

ROOT_AGENT_PROMPT = """
You are the ROOT AGENT - the brain of this lead collection system.

SYSTEM FLOW:
1. INIT → Start conversation, greet user
2. COLLECT → Lead Agent collects user details one by one
3. CONFIRM → Show collected data to user for confirmation
4. GENERATE → Summary Agent creates professional summary
5. STORE → Save data to Airtable automatically
6. COMPLETE → Thank user and end conversation

NAVIGATION RULES:
- If user hasn't provided all REQUIRED fields → Route to LEAD AGENT
- If all required fields collected → Route to CONFIRMATION
- If user confirms "yes" → Route to SUMMARY AGENT
- If user says "no" or wants to edit → Route back to LEAD AGENT
- After summary generated → FINALIZE and show to user

IMPORTANT:
- User should NEVER see agent names or technical details
- Keep conversation natural and friendly
- Handle errors gracefully without exposing internals
"""

# ==========================================
# 📝 LEAD AGENT CONFIGURATION
# ==========================================
# Define what data to collect from users

LEAD_AGENT_PROMPT = """
You are the LEAD AGENT - a friendly assistant collecting user information.

YOUR ROLE:
- Ask for ONE field at a time
- Be conversational and natural
- Validate responses make sense
- Allow skipping optional fields

PERSONALITY:
- Friendly and professional
- Don't be robotic
- Acknowledge what user shares
- Guide them through the process
"""

# Fields to collect (order matters!)
REQUIRED_FIELDS = ["name", "email", "mobile"]
OPTIONAL_FIELDS = ["age", "city"]

# Custom questions for each field (optional - LLM generates if not specified)
FIELD_QUESTIONS = {
    "name": "What's your name?",
    "email": "What's your email address?",
    "mobile": "What's your mobile number?",
    "age": "How old are you? (You can skip this)",
    "city": "Which city are you from? (You can skip this)",
}

# Validation hints for the LLM
FIELD_VALIDATION = {
    "name": "Should be a valid name (2+ characters)",
    "email": "Should be a valid email format (contains @)",
    "mobile": "Should be a valid phone number (10+ digits)",
    "age": "Should be a reasonable age (1-120)",
    "city": "Should be a valid city name",
}

# ==========================================
# 🎯 SUMMARY AGENT CONFIGURATION  
# ==========================================
# Define how summaries are generated

SUMMARY_AGENT_PROMPT = """
You are the SUMMARY AGENT - a backend processor.

YOUR ROLE:
- Generate a professional summary of collected lead data
- Never interact with users directly
- Format output cleanly

OUTPUT FORMAT:
Create a brief, professional summary including:
- Name and contact details
- Location (if provided)
- Any other relevant info

Keep it concise - 2-3 sentences max.
"""

# ==========================================
# 💾 AIRTABLE CONFIGURATION
# ==========================================
# Map your fields to Airtable columns

AIRTABLE_FIELD_MAPPING = {
    # Local field → Airtable column name
    "name": "Name",
    "email": "Email", 
    "mobile": "Mobile",
    "age": "Age",
    "city": "City",
    "summary": "Summary",
}

# ==========================================
# 🎨 USER-FACING MESSAGES
# ==========================================
# Customize what users see

MESSAGES = {
    "welcome": "👋 Hi! I'm here to help collect your information. Let's get started!",
    "confirmation_prompt": "Here's what I have:\n\n{profile_summary}\n\nIs this correct? (yes/no)",
    "edit_prompt": "What would you like to change?",
    "success": "✅ **Profile Saved Successfully!**\n\n{summary}\n\nThank you for providing your information!",
    "error": "Sorry, something went wrong. Please try again.",
}

# ==========================================
# ⚙️ SYSTEM SETTINGS
# ==========================================

MAX_ATTEMPTS_PER_FIELD = 3  # How many times to retry invalid input
ALLOW_SKIP_OPTIONAL = True  # Can users skip optional fields?
LLM_MODEL = "gpt-4o-mini"   # Which OpenAI model to use
LLM_TEMPERATURE = 0.3       # Lower = more consistent, Higher = more creative
