from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List

@dataclass
class ClickUpTask:
    internal_id: str
    title: str
    description: str = ""
    status: Optional[str] = None
    priority: Optional[int] = None
    tags: List[str] = field(default_factory=list)
    
    # Routing and Assignment
    category: str = "general"          # e.g., "security", "dev", "infra"
    target_list_id: Optional[str] = None # Overrides default list if provided
    
    assignees: List[int] = field(default_factory=list) 
    checklists: List[str] = field(default_factory=list) 
    due_date: Optional[int] = None
    custom_fields: Dict[str, Any] = field(default_factory=dict)