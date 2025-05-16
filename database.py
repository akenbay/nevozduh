import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

DB_FILE = "database.json"
IMAGES_DIR = "images"

class Database:
    @staticmethod
    def _read() -> Dict:
        with open(DB_FILE) as f:
            return json.load(f)
    
    @staticmethod
    def _write(data: Dict) -> None:
        with open(DB_FILE, 'w') as f:
            json.dump(data, f, indent=2)

    @staticmethod
    def initialize_games():
        """Create games for the next 7 days with different levels"""
        data = Database._read()
        today = datetime.today()
        
        data["games"] = []
        game_id = 1
        
        levels = ["beginner", "intermediate", "professional"]
        
        for day in range(7):
            date = (today + timedelta(days=day)).strftime("%Y-%m-%d")
            
            # Create games for each level
            for i, level in enumerate(levels):
                data["games"].append({
                    "id": game_id,
                    "date": date,
                    "time": f"{10+i*2}:00-{11+i*2}:00",
                    "field": f"{level.capitalize()} Field",
                    "photo": f"{level}_field.jpg",
                    "address": f"{100+i} {level.capitalize()} Avenue, Sports City",
                    "level": level,
                    "max_players": 8 if level == "beginner" else 10,
                    "price": 400 if level == "beginner" else (500 if level == "intermediate" else 600),
                    "players": [],
                    "description": f"{level.capitalize()} level game"
                })
                game_id += 1
        
        Database._write(data)

    @staticmethod
    def get_available_dates() -> List[str]:
        dates = set()
        data = Database._read()
        for game in data["games"]:
            dates.add(game["date"])
        return sorted(dates)

    @staticmethod
    def get_games_by_date(date: str) -> List[Dict]:
        data = Database._read()
        return [game for game in data["games"] if game["date"] == date]

    @staticmethod
    def get_games_by_level(level: str) -> List[Dict]:
        data = Database._read()
        return [game for game in data["games"] if game["level"] == level]

    @staticmethod
    def get_game(game_id: int) -> Optional[Dict]:
        data = Database._read()
        for game in data["games"]:
            if game["id"] == game_id:
                return game
        return None

    @staticmethod
    def register_player(game_id: int, user_id: int, user_data: Dict) -> bool:
        data = Database._read()
        
        # Add user if not exists
        if str(user_id) not in data["users"]:
            data["users"][str(user_id)] = user_data
        
        # Find game and register player
        for game in data["games"]:
            if game["id"] == game_id and len(game["players"]) < game["max_players"]:
                if user_id not in game["players"]:
                    game["players"].append(user_id)
                    Database._write(data)
                    return True
        return False

    @staticmethod
    def create_payment(game_id: int, user_id: int) -> str:
        data = Database._read()
        game = Database.get_game(game_id)
        if not game:
            return ""
            
        payment_id = f"pay_{user_id}_{datetime.now().timestamp()}"
        
        data["payments"][payment_id] = {
            "game_id": game_id,
            "user_id": user_id,
            "amount": game["price"],
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }
        
        Database._write(data)
        return payment_id

    @staticmethod
    def confirm_payment(payment_id: str) -> bool:
        data = Database._read()
        if payment_id not in data["payments"]:
            return False
            
        payment = data["payments"][payment_id]
        if payment["status"] == "completed":
            return False
            
        # Register the player
        for game in data["games"]:
            if game["id"] == payment["game_id"]:
                if payment["user_id"] not in game["players"]:
                    game["players"].append(payment["user_id"])
                    payment["status"] = "completed"
                    Database._write(data)
                    return True
        return False

    @staticmethod
    def get_user(user_id: int) -> Optional[Dict]:
        data = Database._read()
        return data["users"].get(str(user_id))

    @staticmethod
    def create_user(user_id: int, name: str, phone: str, level: str) -> None:
        data = Database._read()
        data["users"][str(user_id)] = {
            "name": name,
            "phone": phone, 
            "level": level
        }
        Database._write(data)