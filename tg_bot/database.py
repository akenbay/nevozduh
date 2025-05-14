import json
from typing import Dict, Any, List

DB_FILE = "database.json"

class Database:
    @staticmethod
    def read() -> Dict[str, Any]:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    
    @staticmethod
    def write(data: Dict[str, Any]) -> None:
        with open(DB_FILE, "w") as f:
            json.dump(data, f, indent=2)
    
    @staticmethod
    def get_available_slots() -> List[Dict]:
        data = Database.read()
        return [slot for slot in data["time_slots"] if slot["available"]]
    
    @staticmethod
    def join_slot(slot_id: int, user_id: int, user_name: str) -> Dict:
        data = Database.read()
        
        # Add user to users registry if not exists
        if str(user_id) not in data["users"]:
            data["users"][str(user_id)] = {"name": user_name}
        
        # Find the slot and add player
        for slot in data["time_slots"]:
            if slot["id"] == slot_id:
                if user_id not in slot["players"]:
                    slot["players"].append(user_id)
                    if len(slot["players"]) >= slot["max_players"]:
                        slot["available"] = False
                Database.write(data)
                return slot
        return None
    
    @staticmethod
    def get_slot_info(slot_id: int) -> Dict:
        data = Database.read()
        for slot in data["time_slots"]:
            if slot["id"] == slot_id:
                return slot
        return None
    
    @staticmethod
    def get_user(user_id: int) -> Dict:
        data = Database.read()
        return data["users"].get(str(user_id))