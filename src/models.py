from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class ClickUpTask:
    internal_id: str  # Your system's ID (e.g., "order_101")
    title: str
    description: str = ""
    #assignees: List[int] = field(default_factory=list) # ClickUp User IDs
    #priority: Optional[int] = None # 1: Urgent, 2: High, 3: Normal, 4: Low
    status: Optional[str] = None