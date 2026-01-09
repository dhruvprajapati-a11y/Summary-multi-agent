from __future__ import annotations

from typing import Dict, List, Optional, Literal, Annotated
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

# Define possible statuses
# collecting: gathering info
# confirming: confirming parsed info
# ready_to_summarize: ready to create summary
# done: summary completed
# handoff: error, needs human intervention or alternative flow
Status = Literal["collecting", "confirming", "ready_to_summarize", "done", "handoff"]

# Define the structure of the profile and state
class Profile(TypedDict, total=False): 
    name: str
    email: str
    mobile: str
    age: str
    city: str

# Define error structure 
class FieldError(TypedDict): 
    field: str
    reason: str

# Define the overall graph state
class GraphState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]

    profile: Profile
    status: Status
    last_field_asked: Optional[str]
    just_processed: bool  # Flag to prevent re-processing same message

    required_fields: List[str]
    optional_fields: List[str]

    attempts_per_field: Dict[str, int]
    max_attempts: int
    errors: List[FieldError]

    user_confirmed: bool
    summary_text: Optional[str]
