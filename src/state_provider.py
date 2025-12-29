import json
import os
from typing import Optional

class BaseStateProvider:
    def get(self, internal_id: str) -> Optional[str]:
        raise NotImplementedError
        
    def set(self, internal_id: str, clickup_id: Optional[str]):
        raise NotImplementedError

class JSONStateProvider(BaseStateProvider):
    def __init__(self, file_path="sync_state.json"):
        self.file_path = file_path
        self._state = self._load()

    def _load(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r") as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def get(self, internal_id):
        return self._state.get(str(internal_id))

    def set(self, internal_id, clickup_id):
        if clickup_id is None:
            self._state.pop(str(internal_id), None)
        else:
            self._state[str(internal_id)] = clickup_id
            
        with open(self.file_path, "w") as f:
            json.dump(self._state, f, indent=4)