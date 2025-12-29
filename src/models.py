from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

@dataclass
class ClickUpTask:
    internal_id: str
    title: str
    description: str = ""
    status: str = "to do" 
    priority: Optional[int] = None 
    tags: List[str] = field(default_factory=list)
    assignee_emails: List[str] = field(default_factory=list)
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    attachment_paths: List[str] = field(default_factory=list)