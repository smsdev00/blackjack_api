"""
═══════════════════════════════════════════════════════════════════════════════
BLACKJACK ROGUELITE - BACKEND ETAPA 3.0
Sistema de Garitos (Oleadas) + Trampas (Power-ups) + Objetos
+ FIX: Game Over cuando saldo < apuesta mínima
+ NEW: Trampa "Peek Next Card" (ver próxima carta del mazo)
+ NEW: Imágenes de croupier por nivel
+ NEW: Sistema de DIFICULTAD (fácil, normal, difícil)
+ NEW: Sistema de WIN STREAK con multiplicadores
+ NEW: Items multiplicadores de bonus
═══════════════════════════════════════════════════════════════════════════════
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Optional
from enum import Enum
from sqlalchemy.orm import Session
import random
import uuid
import os
import json

from database import get_db, init_db, SessionLocal
from models import GameModel, StatsModel, LeaderboardModel

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN BASE
# ═══════════════════════════════════════════════════════════════════════════════

CONFIG = {
    "deck_count": 6,
    "dealer_stand_value": 17,
    "blackjack_payout": 1.5,
    "starting_chips": 500,
    "minimum_bet": 10,
    "maximum_bet": 500,
    "starting_stress": 0,
    "max_stress": 100,
}

# ═══════════════════════════════════════════════════════════════════════════════
# SISTEMA DE DIFICULTAD
# ═══════════════════════════════════════════════════════════════════════════════

DIFFICULTY_SETTINGS = {
    "easy": {
        "name": "Novato",
        "description": "Para los que empiezan en el juego",
        "icon": "🌟",
        "starting_chips": 750,
        "starting_stress": 0,
        "stress_gain_loss": 2,           # Estrés ganado al perder
        "stress_gain_detected": 10,      # Estrés ganado al ser detectado
        "stress_reduction_win": 8,       # Estrés reducido al ganar
        "detection_modifier": -0.10,     # -10% detección base
        "win_streak_multipliers": {      # Multiplicadores de racha
            2: 1.5,   # 2 victorias = x1.5
            3: 2.0,   # 3 victorias = x2
            4: 3.0,   # 4 victorias = x3
            5: 5.0,   # 5+ victorias = x5
        },
        "blackjack_streak_bonus": 1.5,   # Bonus extra si BJ en racha
        "base_streak_multiplier": 1.0,   # Multiplicador base de racha
    },
    "normal": {
        "name": "Tahur",
        "description": "El modo clasico",
        "icon": "🎰",
        "starting_chips": 500,
        "starting_stress": 10,
        "stress_gain_loss": 3,
        "stress_gain_detected": 15,
        "stress_reduction_win": 5,
        "detection_modifier": 0,
        "win_streak_multipliers": {
            2: 2.0,   # 2 victorias = x2
            3: 3.0,   # 3 victorias = x3
            4: 4.0,   # 4 victorias = x4
            5: 10.0,  # 5+ victorias = x10
        },
        "blackjack_streak_bonus": 2.0,
        "base_streak_multiplier": 1.0,
    },
    "hard": {
        "name": "Suicida",
        "description": "Solo para los mas temerarios",
        "icon": "💀",
        "starting_chips": 300,
        "starting_stress": 25,
        "stress_gain_loss": 5,
        "stress_gain_detected": 20,
        "stress_reduction_win": 3,
        "detection_modifier": 0.10,      # +10% detección base
        "win_streak_multipliers": {
            2: 2.5,   # 2 victorias = x2.5
            3: 4.0,   # 3 victorias = x4
            4: 6.0,   # 4 victorias = x6
            5: 15.0,  # 5+ victorias = x15
        },
        "blackjack_streak_bonus": 3.0,
        "base_streak_multiplier": 1.0,
    },
}

# ═══════════════════════════════════════════════════════════════════════════════
# SISTEMA DE GARITOS (OLEADAS)
# ═══════════════════════════════════════════════════════════════════════════════

GARITOS = {
    1: {
        "name": "El Callejón de los Desahuciados",
        "description": "Donde empiezan los perdedores",
        "dealer_name": "Manco Pete",
        "dealer_personality": "distraído",
        "dealer_image": "/images/croupier-1.jpg",
        "chips_to_advance": 1000,
        "min_bet": 10,
        "max_bet": 100,
        "cheat_detection_base": 0.15,  # 15% base de detección
        "special_rules": [],
        "color": "#33ff33",
        "unlocks": ["peek_card"],  # Trampa que desbloqueas al ganar
    },
    2: {
        "name": "La Taberna del Tuerto",
        "description": "Los borrachos apuestan fuerte",
        "dealer_name": "Sally la Sorda",
        "dealer_personality": "lenta",
        "dealer_image": "/images/croupier-2.jpg",
        "chips_to_advance": 2500,
        "min_bet": 25,
        "max_bet": 250,
        "cheat_detection_base": 0.25,
        "special_rules": ["drunk_bonus"],  # +10% en victorias
        "color": "#ffaa00",
        "unlocks": ["swap_card"],
    },
    3: {
        "name": "El Salón Dorado",
        "description": "Aquí juegan los que tienen algo que perder",
        "dealer_name": "Don Rodrigo",
        "dealer_personality": "observador",
        "dealer_image": "/images/croupier-3.jpg",
        "chips_to_advance": 5000,
        "min_bet": 50,
        "max_bet": 500,
        "cheat_detection_base": 0.35,
        "special_rules": ["high_roller"],  # Doblar paga 2.5x
        "color": "#ffd700",
        "unlocks": ["extra_card"],
    },
    4: {
        "name": "La Casa de la Viuda Negra",
        "description": "Muchos entran, pocos salen con sus fichas",
        "dealer_name": "La Viuda",
        "dealer_personality": "despiadada",
        "dealer_image": "/images/croupier-4.jpg",
        "chips_to_advance": 10000,
        "min_bet": 100,
        "max_bet": 1000,
        "cheat_detection_base": 0.45,
        "special_rules": ["widow_curse"],  # Empates son derrotas
        "color": "#ff0066",
        "unlocks": ["mark_deck"],
    },
    5: {
        "name": "El Infierno de Dante",
        "description": "El garito final. Todo o nada.",
        "dealer_name": "El Diablo",
        "dealer_personality": "omnisciente",
        "dealer_image": "/images/croupier-5.jpg",
        "chips_to_advance": None,  # Victoria final
        "min_bet": 500,
        "max_bet": 5000,
        "cheat_detection_base": 0.60,
        "special_rules": ["devils_game"],  # BJ del dealer = pierdes todo
        "color": "#ff0000",
        "unlocks": ["bribe"],
    },
}

# ═══════════════════════════════════════════════════════════════════════════════
# SISTEMA DE TRAMPAS (POWER-UPS ACTIVOS)
# ═══════════════════════════════════════════════════════════════════════════════

TRAMPAS = {
    "peek_card": {
        "name": "Espiar Carta Oculta",
        "description": "Ver la carta oculta del crupier",
        "icon": "👁️",
        "stress_cost": 5,
        "detection_modifier": 0.10,
        "cooldown": 0,  # Puede usarse cada ronda
        "effect": "reveal_dealer",
    },
    "peek_next_card": {
        "name": "Espiar Próxima Carta",
        "description": "Ver la próxima carta que saldrá del mazo",
        "icon": "🔮",
        "stress_cost": 15,
        "detection_modifier": 0.35,  # MUCHO más riesgoso
        "cooldown": 1,
        "effect": "peek_next",
    },
    "swap_card": {
        "name": "Cambiar Carta",
        "description": "Cambia tu peor carta por una del mazo",
        "icon": "🔄",
        "stress_cost": 15,
        "detection_modifier": 0.20,
        "cooldown": 2,
        "effect": "swap_worst",
    },
    "extra_card": {
        "name": "Carta Extra",
        "description": "Roba una carta sin que cuente como Hit",
        "icon": "🃏",
        "stress_cost": 20,
        "detection_modifier": 0.25,
        "cooldown": 3,
        "effect": "free_card",
    },
    "mark_deck": {
        "name": "Marcar Mazo",
        "description": "Ve las próximas 3 cartas del mazo",
        "icon": "✒️",
        "stress_cost": 10,
        "detection_modifier": 0.15,
        "cooldown": 1,
        "effect": "see_deck",
    },
    "bribe": {
        "name": "Sobornar",
        "description": "El crupier 'se equivoca' a tu favor",
        "icon": "💰",
        "stress_cost": 25,
        "detection_modifier": 0.30,
        "chip_cost": 50,  # Cuesta fichas además de estrés
        "cooldown": 5,
        "effect": "dealer_mistake",
    },
}

# ═══════════════════════════════════════════════════════════════════════════════
# SISTEMA DE OBJETOS (POWER-UPS PASIVOS/CONSUMIBLES)
# ═══════════════════════════════════════════════════════════════════════════════

ITEMS = {
    "whiskey": {
        "name": "Whiskey Barato",
        "description": "Reduce 10 de estres",
        "icon": "🥃",
        "price": 25,
        "effect": "reduce_stress",
        "value": 10,
        "consumable": True,
    },
    "cigarro": {
        "name": "Cigarro de la Suerte",
        "description": "La proxima trampa no puede fallar",
        "icon": "🚬",
        "price": 75,
        "effect": "guaranteed_cheat",
        "consumable": True,
    },
    "dado_cargado": {
        "name": "Dado Cargado",
        "description": "+5% probabilidad de BJ esta ronda",
        "icon": "🎲",
        "price": 100,
        "effect": "lucky_draw",
        "consumable": True,
    },
    "gafas_oscuras": {
        "name": "Gafas Oscuras",
        "description": "-10% deteccion de trampas (permanente)",
        "icon": "🕶️",
        "price": 200,
        "effect": "reduce_detection",
        "value": 0.10,
        "consumable": False,
    },
    "anillo_sello": {
        "name": "Anillo con Sello",
        "description": "+15% ganancias en victorias (permanente)",
        "icon": "💍",
        "price": 300,
        "effect": "bonus_winnings",
        "value": 0.15,
        "consumable": False,
    },
    "reloj_bolsillo": {
        "name": "Reloj de Bolsillo",
        "description": "Una vez por garito: repite la ultima ronda",
        "icon": "⏱️",
        "price": 500,
        "effect": "rewind",
        "consumable": True,
        "uses_per_garito": 1,
    },
    # NUEVOS: Items multiplicadores de racha
    "herradura": {
        "name": "Herradura de la Suerte",
        "description": "+25% multiplicador de racha (permanente)",
        "icon": "🧲",
        "price": 400,
        "effect": "streak_multiplier",
        "value": 0.25,
        "consumable": False,
    },
    "trebol": {
        "name": "Trebol de 4 Hojas",
        "description": "+50% multiplicador de racha (permanente)",
        "icon": "🍀",
        "price": 750,
        "effect": "streak_multiplier",
        "value": 0.50,
        "consumable": False,
    },
    "amuleto_diablo": {
        "name": "Amuleto del Diablo",
        "description": "Racha no se pierde en empates (permanente)",
        "icon": "😈",
        "price": 600,
        "effect": "streak_on_push",
        "consumable": False,
    },
    "moneda_maldita": {
        "name": "Moneda Maldita",
        "description": "x2 bonus de racha pero +5 estres por victoria",
        "icon": "🪙",
        "price": 350,
        "effect": "cursed_streak",
        "value": 2.0,
        "consumable": False,
    },
}

# ═══════════════════════════════════════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════════════════════════════════════

class Suit(str, Enum):
    HEARTS = "hearts"
    DIAMONDS = "diamonds"
    CLUBS = "clubs"
    SPADES = "spades"

class GameStatus(str, Enum):
    WAITING_FOR_BET = "waiting_for_bet"
    PLAYER_TURN = "player_turn"
    DEALER_TURN = "dealer_turn"
    ROUND_COMPLETE = "round_complete"
    GAME_OVER = "game_over"
    SHOP = "shop"
    GARITO_TRANSITION = "garito_transition"

class PlayerAction(str, Enum):
    HIT = "hit"
    STAND = "stand"
    DOUBLE = "double"

class CheatResult(str, Enum):
    SUCCESS = "success"
    DETECTED = "detected"
    SUSPICIOUS = "suspicious"

# ═══════════════════════════════════════════════════════════════════════════════
# MODELOS DE DATOS
# ═══════════════════════════════════════════════════════════════════════════════

class Card:
    def __init__(self, rank: str, suit: Suit):
        self.rank = rank
        self.suit = suit
        self.id = f"{rank}-{suit.value}-{uuid.uuid4().hex[:6]}"
    
    def value(self) -> int:
        if self.rank in ['J', 'Q', 'K']:
            return 10
        elif self.rank == 'A':
            return 11
        return int(self.rank)
    
    def to_dict(self) -> Dict:
        return {"rank": self.rank, "suit": self.suit.value, "id": self.id}


class Deck:
    def __init__(self, deck_count: int = 6):
        self.cards: List[Card] = []
        self.reset(deck_count)
    
    def reset(self, deck_count: int):
        self.cards = []
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        
        for _ in range(deck_count):
            for suit in Suit:
                for rank in ranks:
                    self.cards.append(Card(rank, suit))
        
        random.shuffle(self.cards)
    
    def deal(self) -> Card:
        if len(self.cards) < 20:
            self.reset(CONFIG["deck_count"])
        return self.cards.pop()
    
    def peek(self, count: int = 3) -> List[Dict]:
        """Ver las próximas cartas sin sacarlas (en orden de salida)"""
        # Las cartas salen con pop() desde el final, así que invertimos el orden
        return [c.to_dict() for c in reversed(self.cards[-count:])]
    
    def peek_next(self) -> Dict:
        """Ver solo la próxima carta sin sacarla"""
        if self.cards:
            return self.cards[-1].to_dict()
        return None
    
    @property
    def remaining(self) -> int:
        return len(self.cards)


class Hand:
    def __init__(self):
        self.cards: List[Card] = []
        self.bet: int = 0
        self.is_standing: bool = False
        self.is_busted: bool = False
        self.is_blackjack: bool = False
        self.is_doubled: bool = False
    
    def add_card(self, card: Card):
        self.cards.append(card)
        self._check_status()
    
    def remove_worst_card(self) -> Optional[Card]:
        """Quita la carta que menos ayuda (para la trampa swap)"""
        if not self.cards:
            return None
        
        current_value = self.calculate_value()
        worst_card = None
        best_improvement = -999
        
        for i, card in enumerate(self.cards):
            # Simular quitar esta carta
            temp_cards = self.cards[:i] + self.cards[i+1:]
            temp_value = self._calc_value_for_cards(temp_cards)
            
            # Queremos acercarnos a 21 sin pasarnos
            if current_value > 21:
                improvement = current_value - temp_value
            else:
                improvement = 21 - temp_value if temp_value <= 21 else -100
            
            if worst_card is None or (current_value > 21 and improvement > best_improvement):
                worst_card = card
                best_improvement = improvement
        
        if worst_card:
            self.cards.remove(worst_card)
            self._check_status()
        
        return worst_card
    
    def _calc_value_for_cards(self, cards: List[Card]) -> int:
        value = sum(card.value() for card in cards)
        aces = sum(1 for card in cards if card.rank == 'A')
        while value > 21 and aces > 0:
            value -= 10
            aces -= 1
        return value
    
    def calculate_value(self) -> int:
        return self._calc_value_for_cards(self.cards)
    
    def _check_status(self):
        value = self.calculate_value()
        
        if value > 21:
            self.is_busted = True
            self.is_standing = True
        
        if len(self.cards) == 2 and value == 21:
            self.is_blackjack = True
            self.is_standing = True
    
    def can_double(self) -> bool:
        return len(self.cards) == 2 and not self.is_doubled
    
    def to_dict(self, hide_second: bool = False) -> Dict:
        if hide_second and len(self.cards) > 1:
            return {
                "cards": [self.cards[0].to_dict(), {"rank": "?", "suit": "?", "id": "hidden"}],
                "value": self.cards[0].value(),
                "is_standing": self.is_standing,
                "is_busted": False,
                "is_blackjack": False
            }
        
        return {
            "cards": [c.to_dict() for c in self.cards],
            "value": self.calculate_value(),
            "is_standing": self.is_standing,
            "is_busted": self.is_busted,
            "is_blackjack": self.is_blackjack,
            "is_doubled": self.is_doubled
        }


class PlayerInventory:
    def __init__(self):
        self.items: Dict[str, int] = {}  # item_id -> cantidad
        self.passive_effects: Dict[str, float] = {}  # efecto -> valor acumulado
        self.unlocked_cheats: List[str] = ["peek_card", "peek_next_card"]  # Trampas desbloqueadas (peek_next_card disponible desde inicio)
        self.cheat_cooldowns: Dict[str, int] = {}  # trampa -> rondas restantes
        self.guaranteed_cheat: bool = False  # Del cigarro
        self.rewind_available: bool = False
    
    def add_item(self, item_id: str, quantity: int = 1):
        self.items[item_id] = self.items.get(item_id, 0) + quantity
        
        # Aplicar efectos pasivos inmediatamente
        item = ITEMS.get(item_id)
        if item and not item.get("consumable", True):
            effect = item["effect"]
            value = item.get("value", 0)
            self.passive_effects[effect] = self.passive_effects.get(effect, 0) + value
    
    def use_item(self, item_id: str) -> bool:
        if self.items.get(item_id, 0) <= 0:
            return False
        
        item = ITEMS.get(item_id)
        if not item or not item.get("consumable", True):
            return False
        
        self.items[item_id] -= 1
        if self.items[item_id] <= 0:
            del self.items[item_id]
        
        return True
    
    def unlock_cheat(self, cheat_id: str):
        if cheat_id not in self.unlocked_cheats:
            self.unlocked_cheats.append(cheat_id)
    
    def can_use_cheat(self, cheat_id: str) -> bool:
        if cheat_id not in self.unlocked_cheats:
            return False
        return self.cheat_cooldowns.get(cheat_id, 0) <= 0
    
    def use_cheat(self, cheat_id: str):
        cheat = TRAMPAS.get(cheat_id)
        if cheat:
            self.cheat_cooldowns[cheat_id] = cheat.get("cooldown", 0)
    
    def tick_cooldowns(self):
        for cheat_id in list(self.cheat_cooldowns.keys()):
            self.cheat_cooldowns[cheat_id] = max(0, self.cheat_cooldowns[cheat_id] - 1)
    
    def to_dict(self) -> Dict:
        return {
            "items": self.items,
            "passive_effects": self.passive_effects,
            "unlocked_cheats": self.unlocked_cheats,
            "cheat_cooldowns": self.cheat_cooldowns,
            "guaranteed_cheat": self.guaranteed_cheat,
        }


class Game:
    def __init__(self, game_id: str, player_name: str, difficulty: str = "normal"):
        self.id = game_id
        self.player_name = player_name
        self.difficulty = difficulty

        # Obtener configuración de dificultad
        diff_settings = DIFFICULTY_SETTINGS.get(difficulty, DIFFICULTY_SETTINGS["normal"])

        self.player_chips = diff_settings["starting_chips"]
        self.status = GameStatus.WAITING_FOR_BET
        self.stress = diff_settings["starting_stress"]

        # Sistema de garitos
        self.current_garito = 1
        self.garitos_completed: List[int] = []

        # Inventario
        self.inventory = PlayerInventory()

        # Estadísticas
        self.wins = 0
        self.losses = 0
        self.pushes = 0
        self.rounds = 0
        self.cheats_used = 0
        self.cheats_detected = 0

        # Sistema de Win Streak
        self.win_streak = 0           # Racha actual de victorias
        self.max_win_streak = 0       # Racha máxima alcanzada
        self.last_streak_bonus = 0    # Último bonus obtenido por racha

        # Estado de la ronda
        self.deck = Deck(CONFIG["deck_count"])
        self.player_hand: Optional[Hand] = None
        self.dealer_hand: Optional[Hand] = None
        self.current_bet = 0
        self.round_result: Optional[str] = None
        self.round_message: Optional[str] = None

        # Estado de trampas esta ronda
        self.dealer_card_revealed = False
        self.peeked_cards: List[Dict] = []
        self.next_card_peeked: Optional[Dict] = None  # Nueva: próxima carta espiada
        self.cheat_used_this_round: Optional[str] = None

        # Para rewind
        self.last_round_state: Optional[Dict] = None

    def get_difficulty_settings(self) -> Dict:
        """Obtiene la configuración de dificultad actual"""
        return DIFFICULTY_SETTINGS.get(self.difficulty, DIFFICULTY_SETTINGS["normal"])

    def calculate_streak_bonus(self, base_winnings: int, is_blackjack: bool = False) -> tuple:
        """Calcula el bonus por racha de victorias
        Retorna: (winnings_con_bonus, streak_bonus_amount, streak_multiplier)
        """
        if self.win_streak < 2:
            return base_winnings, 0, 1.0

        diff = self.get_difficulty_settings()
        streak_mults = diff["win_streak_multipliers"]

        # Encontrar el multiplicador correcto
        streak_key = min(self.win_streak, 5)  # Máximo nivel es 5
        base_multiplier = streak_mults.get(streak_key, 1.0)

        # Aplicar modificadores de items
        item_streak_bonus = self.inventory.passive_effects.get("streak_multiplier", 0)
        cursed_bonus = self.inventory.passive_effects.get("cursed_streak", 0)

        # Calcular multiplicador final
        final_multiplier = base_multiplier * (1 + item_streak_bonus)
        if cursed_bonus > 0:
            final_multiplier *= cursed_bonus

        # Bonus extra por blackjack en racha
        if is_blackjack and self.win_streak >= 2:
            final_multiplier += diff["blackjack_streak_bonus"]

        streak_bonus = int(base_winnings * (final_multiplier - 1))
        total_winnings = base_winnings + streak_bonus

        return total_winnings, streak_bonus, final_multiplier
    
    def get_garito(self) -> Dict:
        return GARITOS.get(self.current_garito, GARITOS[1])
    
    def check_garito_advancement(self) -> bool:
        """Verifica si el jugador puede avanzar al siguiente garito"""
        garito = self.get_garito()
        chips_needed = garito.get("chips_to_advance")
        
        if chips_needed and self.player_chips >= chips_needed:
            return True
        return False
    
    def can_afford_minimum_bet(self) -> bool:
        """Verifica si el jugador puede pagar la apuesta mínima"""
        garito = self.get_garito()
        min_bet = garito.get("min_bet", CONFIG["minimum_bet"])
        return self.player_chips >= min_bet
    
    def advance_garito(self) -> Dict:
        """Avanza al siguiente garito"""
        if self.current_garito >= 5:
            return {"success": False, "message": "Ya estás en el garito final"}
        
        old_garito = self.get_garito()
        self.garitos_completed.append(self.current_garito)
        self.current_garito += 1
        new_garito = self.get_garito()
        
        # Desbloquear trampa del garito anterior
        for cheat_id in old_garito.get("unlocks", []):
            self.inventory.unlock_cheat(cheat_id)
        
        # Reset rewind para nuevo garito
        if self.inventory.items.get("reloj_bolsillo", 0) > 0:
            self.inventory.rewind_available = True
        
        self.status = GameStatus.SHOP
        
        return {
            "success": True,
            "old_garito": old_garito["name"],
            "new_garito": new_garito["name"],
            "unlocked_cheats": old_garito.get("unlocks", []),
            "message": f"¡Bienvenido a {new_garito['name']}!"
        }
    
    def calculate_detection_chance(self, cheat_id: str) -> float:
        """Calcula la probabilidad de ser detectado al hacer trampa"""
        garito = self.get_garito()
        cheat = TRAMPAS.get(cheat_id, {})
        diff = self.get_difficulty_settings()

        base = garito.get("cheat_detection_base", 0.20)
        modifier = cheat.get("detection_modifier", 0.10)

        # Modificador de dificultad
        diff_modifier = diff.get("detection_modifier", 0)

        # Reducción por objetos pasivos
        reduction = self.inventory.passive_effects.get("reduce_detection", 0)

        # El estrés aumenta la detección
        stress_modifier = self.stress / 200  # +0.5 máximo por estrés

        final = base + modifier + diff_modifier + stress_modifier - reduction
        return max(0.05, min(0.95, final))  # Entre 5% y 95%
    
    def attempt_cheat(self, cheat_id: str) -> Dict:
        """Intenta hacer una trampa"""
        if self.status != GameStatus.PLAYER_TURN:
            return {"success": False, "message": "No es momento de hacer trampas"}
        
        if not self.inventory.can_use_cheat(cheat_id):
            return {"success": False, "message": "Trampa no disponible o en cooldown"}
        
        cheat = TRAMPAS.get(cheat_id)
        if not cheat:
            return {"success": False, "message": "Trampa desconocida"}
        
        # Verificar costo de fichas
        chip_cost = cheat.get("chip_cost", 0)
        if chip_cost > 0 and self.player_chips < chip_cost:
            return {"success": False, "message": "Fichas insuficientes para esta trampa"}
        
        # Verificar cigarro de la suerte
        guaranteed = self.inventory.guaranteed_cheat
        if guaranteed:
            self.inventory.guaranteed_cheat = False
        
        # Calcular detección
        detection_chance = self.calculate_detection_chance(cheat_id)
        roll = random.random()
        
        self.cheats_used += 1
        self.inventory.use_cheat(cheat_id)
        
        # Pagar costo de fichas
        if chip_cost > 0:
            self.player_chips -= chip_cost
        
        # Aumentar estrés
        stress_cost = cheat.get("stress_cost", 10)
        self.stress = min(CONFIG["max_stress"], self.stress + stress_cost)
        
        result = {
            "cheat_id": cheat_id,
            "cheat_name": cheat["name"],
            "detection_chance": f"{detection_chance*100:.0f}%",
            "stress_added": stress_cost,
            "current_stress": self.stress,
        }
        
        if not guaranteed and roll < detection_chance:
            # ¡Detectado!
            diff = self.get_difficulty_settings()
            self.cheats_detected += 1
            penalty = self.current_bet  # Pierdes la apuesta actual
            stress_penalty = diff.get("stress_gain_detected", 15)
            self.stress = min(CONFIG["max_stress"], self.stress + stress_penalty)

            # Perder racha al ser detectado
            self.win_streak = 0

            result["result"] = CheatResult.DETECTED.value
            result["message"] = f"¡{self.get_garito()['dealer_name']} te pillo! Pierdes ${penalty}"
            result["penalty"] = penalty

            # Terminar la ronda como pérdida
            self._end_round("loss", f"¡DETECTADO HACIENDO TRAMPA! -${self.current_bet}")

            return result
        
        # ¡Éxito! Aplicar efecto
        result["result"] = CheatResult.SUCCESS.value
        self.cheat_used_this_round = cheat_id
        
        effect = cheat["effect"]
        
        if effect == "reveal_dealer":
            self.dealer_card_revealed = True
            result["revealed_card"] = self.dealer_hand.cards[1].to_dict()
            result["message"] = f"Ves que el crupier tiene: {self.dealer_hand.cards[1].rank}{self.dealer_hand.cards[1].suit.value}"
        
        elif effect == "peek_next":
            # Nueva trampa: ver la próxima carta del mazo
            self.next_card_peeked = self.deck.peek_next()
            result["next_card"] = self.next_card_peeked
            result["message"] = f"¡La próxima carta será: {self.next_card_peeked['rank']} de {self.next_card_peeked['suit']}!"
        
        elif effect == "swap_worst":
            removed = self.player_hand.remove_worst_card()
            new_card = self.deck.deal()
            self.player_hand.add_card(new_card)
            result["removed_card"] = removed.to_dict() if removed else None
            result["new_card"] = new_card.to_dict()
            result["message"] = f"Cambiaste {removed.rank} por {new_card.rank}"
        
        elif effect == "free_card":
            new_card = self.deck.deal()
            self.player_hand.cards.append(new_card)  # Sin llamar add_card para evitar check de bust
            # Recalcular manualmente
            if self.player_hand.calculate_value() > 21:
                self.player_hand.is_busted = True
            result["new_card"] = new_card.to_dict()
            result["message"] = f"Robaste un {new_card.rank} sin que nadie lo note"
        
        elif effect == "see_deck":
            self.peeked_cards = self.deck.peek(3)
            result["peeked_cards"] = self.peeked_cards
            result["message"] = "Puedes ver las próximas 3 cartas del mazo"
        
        elif effect == "dealer_mistake":
            # El dealer se "equivoca" - le añadimos una carta mala
            bad_card = Card("10", random.choice(list(Suit)))
            self.dealer_hand.add_card(bad_card)
            result["message"] = "El crupier 'accidentalmente' roba una carta de más"
        
        return result
    
    def use_item(self, item_id: str) -> Dict:
        """Usa un objeto consumible"""
        item = ITEMS.get(item_id)
        if not item:
            return {"success": False, "message": "Objeto desconocido"}
        
        if not self.inventory.use_item(item_id):
            return {"success": False, "message": "No tienes ese objeto"}
        
        effect = item["effect"]
        result = {
            "success": True,
            "item_name": item["name"],
            "effect": effect,
        }
        
        if effect == "reduce_stress":
            reduction = item.get("value", 10)
            self.stress = max(0, self.stress - reduction)
            result["message"] = f"Te relajas... Estrés -{reduction}"
            result["new_stress"] = self.stress
        
        elif effect == "guaranteed_cheat":
            self.inventory.guaranteed_cheat = True
            result["message"] = "Tu próxima trampa no fallará..."
        
        elif effect == "lucky_draw":
            # Implementado en deal
            result["message"] = "Sientes que la suerte está de tu lado..."
        
        elif effect == "rewind":
            if self.last_round_state and self.inventory.rewind_available:
                self._restore_round_state(self.last_round_state)
                self.inventory.rewind_available = False
                result["message"] = "El tiempo retrocede..."
            else:
                result["success"] = False
                result["message"] = "No hay ronda que repetir"
        
        return result
    
    def buy_item(self, item_id: str) -> Dict:
        """Compra un objeto en la tienda"""
        if self.status != GameStatus.SHOP:
            return {"success": False, "message": "La tienda está cerrada"}
        
        item = ITEMS.get(item_id)
        if not item:
            return {"success": False, "message": "Objeto desconocido"}
        
        price = item["price"]
        if self.player_chips < price:
            return {"success": False, "message": "Fichas insuficientes"}
        
        self.player_chips -= price
        self.inventory.add_item(item_id)
        
        return {
            "success": True,
            "item_name": item["name"],
            "price": price,
            "remaining_chips": self.player_chips,
            "message": f"Compraste {item['name']} por ${price}"
        }
    
    def leave_shop(self):
        """Salir de la tienda y volver a jugar"""
        self.status = GameStatus.WAITING_FOR_BET
    
    def place_bet(self, amount: int):
        if self.status != GameStatus.WAITING_FOR_BET:
            raise ValueError("No es momento de apostar")
        
        garito = self.get_garito()
        min_bet = garito.get("min_bet", CONFIG["minimum_bet"])
        max_bet = garito.get("max_bet", CONFIG["maximum_bet"])
        
        if amount < min_bet:
            raise ValueError(f"Apuesta mínima en este garito: ${min_bet}")
        
        if amount > self.player_chips:
            raise ValueError("Fichas insuficientes")
        
        if amount > max_bet:
            raise ValueError(f"Apuesta máxima en este garito: ${max_bet}")
        
        # Guardar estado para rewind
        self._save_round_state()
        
        self.current_bet = amount
        self.player_chips -= amount
        self.dealer_card_revealed = False
        self.peeked_cards = []
        self.next_card_peeked = None  # Reset de próxima carta espiada
        self.cheat_used_this_round = None
        
        self._deal_initial_cards()
    
    def _save_round_state(self):
        """Guarda el estado actual para posible rewind"""
        self.last_round_state = {
            "chips": self.player_chips,
            "stress": self.stress,
            "wins": self.wins,
            "losses": self.losses,
            "pushes": self.pushes,
            "rounds": self.rounds,
        }
    
    def _restore_round_state(self, state: Dict):
        """Restaura un estado guardado"""
        self.player_chips = state["chips"]
        self.stress = state["stress"]
        self.wins = state["wins"]
        self.losses = state["losses"]
        self.pushes = state["pushes"]
        self.rounds = state["rounds"]
        self.status = GameStatus.WAITING_FOR_BET
        self.player_hand = None
        self.dealer_hand = None
        self.round_result = None
        self.round_message = None
    
    def _deal_initial_cards(self):
        self.player_hand = Hand()
        self.dealer_hand = Hand()
        self.player_hand.bet = self.current_bet
        self.round_result = None
        self.round_message = None
        
        self.player_hand.add_card(self.deck.deal())
        self.dealer_hand.add_card(self.deck.deal())
        self.player_hand.add_card(self.deck.deal())
        self.dealer_hand.add_card(self.deck.deal())
        
        if self.player_hand.is_blackjack:
            if self.dealer_hand.is_blackjack:
                garito = self.get_garito()
                if "widow_curse" in garito.get("special_rules", []):
                    self._end_round("loss", "¡LA MALDICION DE LA VIUDA! Empate = Derrota")
                else:
                    self._end_round("push", "¡DOBLE BLACKJACK! EMPATE")
            else:
                # Incrementar racha ANTES de calcular bonus
                self.win_streak += 1
                self.max_win_streak = max(self.max_win_streak, self.win_streak)

                base_payout = int(self.current_bet * CONFIG["blackjack_payout"])
                bonus = self.inventory.passive_effects.get("bonus_winnings", 0)
                if bonus > 0:
                    base_payout = int(base_payout * (1 + bonus))

                # Calcular bonus de racha (con flag de blackjack)
                final_payout, streak_bonus, streak_mult = self.calculate_streak_bonus(base_payout, is_blackjack=True)
                self.last_streak_bonus = streak_bonus

                self.player_chips += self.current_bet + final_payout

                if streak_bonus > 0:
                    self._end_round("blackjack", f"¡¡¡BLACKJACK!!! +${base_payout} +${streak_bonus} RACHA x{streak_mult:.1f}!")
                else:
                    self._end_round("blackjack", f"¡¡¡BLACKJACK!!! +${final_payout}")
        else:
            self.status = GameStatus.PLAYER_TURN
    
    def player_action(self, action: PlayerAction):
        if self.status != GameStatus.PLAYER_TURN:
            raise ValueError("No es tu turno")
        
        if action == PlayerAction.HIT:
            self._hit()
        elif action == PlayerAction.STAND:
            self._stand()
        elif action == PlayerAction.DOUBLE:
            self._double()
    
    def _hit(self):
        self.player_hand.add_card(self.deck.deal())
        self.next_card_peeked = None  # Limpiar carta espiada después de usarla
        
        if self.player_hand.is_busted:
            self._end_round("loss", f"¡TE PASASTE! -${self.current_bet}")
        elif self.player_hand.calculate_value() == 21:
            self._stand()
    
    def _stand(self):
        self.player_hand.is_standing = True
        self.status = GameStatus.DEALER_TURN
        self._dealer_play()
    
    def _double(self):
        if not self.player_hand.can_double():
            raise ValueError("No puedes doblar")
        
        if self.player_chips < self.current_bet:
            raise ValueError("Fichas insuficientes para doblar")
        
        self.player_chips -= self.current_bet
        self.current_bet *= 2
        self.player_hand.is_doubled = True
        self.player_hand.add_card(self.deck.deal())
        self.next_card_peeked = None  # Limpiar carta espiada
        
        if self.player_hand.is_busted:
            self._end_round("loss", f"¡TE PASASTE AL DOBLAR! -${self.current_bet}")
        else:
            self._stand()
    
    def _dealer_play(self):
        while self.dealer_hand.calculate_value() < CONFIG["dealer_stand_value"]:
            self.dealer_hand.add_card(self.deck.deal())
        
        self._resolve_round()
    
    def _resolve_round(self):
        player_value = self.player_hand.calculate_value()
        dealer_value = self.dealer_hand.calculate_value()
        garito = self.get_garito()

        # Calcular bonus de ganancias
        bonus = self.inventory.passive_effects.get("bonus_winnings", 0)

        # Regla especial: drunk_bonus
        if "drunk_bonus" in garito.get("special_rules", []):
            bonus += 0.10

        # Regla especial: devils_game - BJ del dealer = pierdes todo
        if "devils_game" in garito.get("special_rules", []) and self.dealer_hand.is_blackjack:
            total_loss = self.player_chips + self.current_bet
            self.player_chips = 0
            self.win_streak = 0
            self._end_round("loss", f"¡EL DIABLO TIENE BLACKJACK! Pierdes todo: ${total_loss}")
            return

        if self.dealer_hand.is_busted:
            # Victoria - incrementar racha
            self.win_streak += 1
            self.max_win_streak = max(self.max_win_streak, self.win_streak)

            base_winnings = int(self.current_bet * (1 + bonus))
            final_winnings, streak_bonus, streak_mult = self.calculate_streak_bonus(base_winnings)
            self.last_streak_bonus = streak_bonus

            self.player_chips += self.current_bet + final_winnings
            if streak_bonus > 0:
                self._end_round("win", f"¡CRUPIER SE PASA! +${base_winnings} +${streak_bonus} RACHA x{streak_mult:.1f}!")
            else:
                self._end_round("win", f"¡CRUPIER SE PASA! +${final_winnings}")

        elif player_value > dealer_value:
            # Victoria - incrementar racha
            self.win_streak += 1
            self.max_win_streak = max(self.max_win_streak, self.win_streak)

            base_winnings = int(self.current_bet * (1 + bonus))
            final_winnings, streak_bonus, streak_mult = self.calculate_streak_bonus(base_winnings)
            self.last_streak_bonus = streak_bonus

            self.player_chips += self.current_bet + final_winnings
            if streak_bonus > 0:
                self._end_round("win", f"¡GANAS! {player_value} vs {dealer_value} → +${base_winnings} +${streak_bonus} RACHA x{streak_mult:.1f}!")
            else:
                self._end_round("win", f"¡GANAS! {player_value} vs {dealer_value} → +${final_winnings}")

        elif player_value < dealer_value:
            self._end_round("loss", f"PIERDES {player_value} vs {dealer_value} → -${self.current_bet}")

        else:
            # Empate
            if "widow_curse" in garito.get("special_rules", []):
                self._end_round("loss", f"¡MALDICION! Empate = Derrota → -${self.current_bet}")
            else:
                # Amuleto del diablo: racha no se pierde en empates
                has_streak_on_push = self.inventory.passive_effects.get("streak_on_push", False)
                if not has_streak_on_push:
                    self.win_streak = 0
                self.player_chips += self.current_bet
                self._end_round("push", f"EMPATE {player_value}")
    
    def _end_round(self, result: str, message: str):
        self.round_result = result
        self.round_message = message
        self.rounds += 1

        diff = self.get_difficulty_settings()

        if result == "win" or result == "blackjack":
            self.wins += 1
            # Reducir estrés al ganar según dificultad
            stress_reduction = diff.get("stress_reduction_win", 5)
            self.stress = max(0, self.stress - stress_reduction)

            # Moneda maldita: +5 estrés por victoria si está activa
            if self.inventory.passive_effects.get("cursed_streak", 0) > 0:
                self.stress = min(CONFIG["max_stress"], self.stress + 5)

        elif result == "loss":
            self.losses += 1
            # Perder racha
            self.win_streak = 0
            # Aumentar estrés al perder según dificultad
            stress_gain = diff.get("stress_gain_loss", 3)
            self.stress = min(CONFIG["max_stress"], self.stress + stress_gain)
        else:
            self.pushes += 1

        # Tick cooldowns de trampas
        self.inventory.tick_cooldowns()

        # Verificar game over - AHORA INCLUYE CHECK DE APUESTA MÍNIMA
        garito = self.get_garito()
        min_bet = garito.get("min_bet", CONFIG["minimum_bet"])

        if self.player_chips <= 0:
            self.status = GameStatus.GAME_OVER
            self.round_message = message  # Mantener mensaje original
        elif self.player_chips < min_bet:
            # NUEVO: Game Over si no puedes pagar la apuesta mínima
            self.status = GameStatus.GAME_OVER
            self.round_message = f"Sin fichas suficientes para la apuesta minima (${min_bet}). Te echan del garito..."
        elif self.stress >= CONFIG["max_stress"]:
            self.status = GameStatus.GAME_OVER
            self.round_message = "¡COLAPSO NERVIOSO! El estres te consume..."
        else:
            self.status = GameStatus.ROUND_COMPLETE
    
    def new_round(self):
        if self.status == GameStatus.GAME_OVER:
            raise ValueError("Game Over")
        
        # Verificar si puede avanzar de garito
        can_advance = self.check_garito_advancement()
        
        self.status = GameStatus.WAITING_FOR_BET
        self.player_hand = None
        self.dealer_hand = None
        self.current_bet = 0
        self.round_result = None
        self.round_message = None
        self.dealer_card_revealed = False
        self.peeked_cards = []
        self.next_card_peeked = None
        
        return {"can_advance_garito": can_advance}
    
    def to_dict(self) -> Dict:
        garito = self.get_garito()
        diff = self.get_difficulty_settings()
        hide_dealer = self.status == GameStatus.PLAYER_TURN and not self.dealer_card_revealed

        # Lista de trampas disponibles con estado
        available_cheats = []
        for cheat_id in self.inventory.unlocked_cheats:
            cheat = TRAMPAS.get(cheat_id, {})
            available_cheats.append({
                "id": cheat_id,
                "name": cheat.get("name", cheat_id),
                "description": cheat.get("description", ""),
                "icon": cheat.get("icon", "?"),
                "stress_cost": cheat.get("stress_cost", 0),
                "chip_cost": cheat.get("chip_cost", 0),
                "can_use": self.inventory.can_use_cheat(cheat_id),
                "cooldown": self.inventory.cheat_cooldowns.get(cheat_id, 0),
                "detection_chance": f"{self.calculate_detection_chance(cheat_id)*100:.0f}%" if self.status == GameStatus.PLAYER_TURN else "?",
            })

        # Calcular próximo multiplicador de racha
        next_streak = self.win_streak + 1
        streak_mults = diff["win_streak_multipliers"]
        next_streak_key = min(next_streak, 5)
        next_multiplier = streak_mults.get(next_streak_key, 1.0) if next_streak >= 2 else 1.0

        # Aplicar modificadores de items al multiplicador mostrado
        item_streak_bonus = self.inventory.passive_effects.get("streak_multiplier", 0)
        cursed_bonus = self.inventory.passive_effects.get("cursed_streak", 0)
        if item_streak_bonus > 0:
            next_multiplier = next_multiplier * (1 + item_streak_bonus)
        if cursed_bonus > 0:
            next_multiplier *= cursed_bonus

        return {
            "id": self.id,
            "player_name": self.player_name,
            "player_chips": self.player_chips,
            "stress": self.stress,
            "max_stress": CONFIG["max_stress"],
            "status": self.status.value,
            "current_bet": self.current_bet,
            "player_hand": self.player_hand.to_dict() if self.player_hand else None,
            "dealer_hand": self.dealer_hand.to_dict(hide_second=hide_dealer) if self.dealer_hand else None,
            "round_result": self.round_result,
            "round_message": self.round_message,

            # Dificultad
            "difficulty": {
                "id": self.difficulty,
                "name": diff["name"],
                "description": diff["description"],
                "icon": diff["icon"],
            },

            # Win Streak
            "win_streak": {
                "current": self.win_streak,
                "max": self.max_win_streak,
                "last_bonus": self.last_streak_bonus,
                "next_multiplier": next_multiplier if next_streak >= 2 else None,
                "multipliers": diff["win_streak_multipliers"],
                "blackjack_bonus": diff["blackjack_streak_bonus"],
            },

            # Garito actual
            "garito": {
                "level": self.current_garito,
                "name": garito["name"],
                "description": garito["description"],
                "dealer_name": garito["dealer_name"],
                "dealer_image": garito.get("dealer_image", "/images/croupier-1.jpg"),
                "color": garito["color"],
                "min_bet": garito["min_bet"],
                "max_bet": garito["max_bet"],
                "chips_to_advance": garito.get("chips_to_advance"),
                "special_rules": garito.get("special_rules", []),
            },
            "can_advance_garito": self.check_garito_advancement(),

            # Inventario y trampas
            "inventory": self.inventory.to_dict(),
            "available_cheats": available_cheats,
            "peeked_cards": self.peeked_cards if self.peeked_cards else None,
            "next_card_peeked": self.next_card_peeked,

            # Stats
            "stats": {
                "wins": self.wins,
                "losses": self.losses,
                "pushes": self.pushes,
                "rounds": self.rounds,
                "cheats_used": self.cheats_used,
                "cheats_detected": self.cheats_detected,
            },

            "deck_remaining": self.deck.remaining,
            "can_double": self.player_hand.can_double() if self.player_hand and self.status == GameStatus.PLAYER_TURN else False,
            "can_afford_double": self.player_chips >= self.current_bet
        }

    def to_db_model(self) -> Dict:
        """Serialize game state for database storage"""
        return {
            "id": self.id,
            "player_name": self.player_name,
            "player_chips": self.player_chips,
            "stress": self.stress,
            "status": self.status.value,
            "difficulty": self.difficulty,
            "current_garito": self.current_garito,
            "garitos_completed": self.garitos_completed,
            "win_streak": self.win_streak,
            "max_win_streak": self.max_win_streak,
            "last_streak_bonus": self.last_streak_bonus,
            "inventory_items": self.inventory.items,
            "inventory_passive_effects": self.inventory.passive_effects,
            "inventory_unlocked_cheats": self.inventory.unlocked_cheats,
            "inventory_cheat_cooldowns": self.inventory.cheat_cooldowns,
            "inventory_guaranteed_cheat": self.inventory.guaranteed_cheat,
            "inventory_rewind_available": self.inventory.rewind_available,
            "current_bet": self.current_bet,
            "player_hand": self._serialize_hand(self.player_hand) if self.player_hand else None,
            "dealer_hand": self._serialize_hand(self.dealer_hand) if self.dealer_hand else None,
            "deck_state": [c.to_dict() for c in self.deck.cards],
            "round_result": self.round_result,
            "round_message": self.round_message,
            "dealer_card_revealed": self.dealer_card_revealed,
            "peeked_cards": self.peeked_cards,
            "next_card_peeked": self.next_card_peeked,
            "cheat_used_this_round": self.cheat_used_this_round,
            "last_round_state": self.last_round_state,
        }

    def _serialize_hand(self, hand: Hand) -> Dict:
        """Serialize a Hand object"""
        return {
            "cards": [c.to_dict() for c in hand.cards],
            "bet": hand.bet,
            "is_standing": hand.is_standing,
            "is_busted": hand.is_busted,
            "is_blackjack": hand.is_blackjack,
            "is_doubled": hand.is_doubled,
        }

    @classmethod
    def from_db_model(cls, db_game: GameModel, stats: StatsModel) -> "Game":
        """Restore game state from database"""
        game = cls.__new__(cls)
        game.id = db_game.id
        game.player_name = db_game.player_name
        game.player_chips = db_game.player_chips
        game.status = GameStatus(db_game.status)
        game.stress = db_game.stress
        game.difficulty = getattr(db_game, 'difficulty', 'normal') or 'normal'
        game.current_garito = db_game.current_garito
        game.garitos_completed = db_game.garitos_completed or []

        # Restore win streak
        game.win_streak = getattr(db_game, 'win_streak', 0) or 0
        game.max_win_streak = getattr(db_game, 'max_win_streak', 0) or 0
        game.last_streak_bonus = getattr(db_game, 'last_streak_bonus', 0) or 0

        # Restore inventory
        game.inventory = PlayerInventory()
        game.inventory.items = db_game.inventory_items or {}
        game.inventory.passive_effects = db_game.inventory_passive_effects or {}
        game.inventory.unlocked_cheats = db_game.inventory_unlocked_cheats or ["peek_card", "peek_next_card"]
        game.inventory.cheat_cooldowns = db_game.inventory_cheat_cooldowns or {}
        game.inventory.guaranteed_cheat = db_game.inventory_guaranteed_cheat or False
        game.inventory.rewind_available = db_game.inventory_rewind_available or False

        # Restore stats
        game.wins = stats.wins if stats else 0
        game.losses = stats.losses if stats else 0
        game.pushes = stats.pushes if stats else 0
        game.rounds = stats.rounds if stats else 0
        game.cheats_used = stats.cheats_used if stats else 0
        game.cheats_detected = stats.cheats_detected if stats else 0

        # Restore round state
        game.current_bet = db_game.current_bet or 0
        game.round_result = db_game.round_result
        game.round_message = db_game.round_message
        game.dealer_card_revealed = db_game.dealer_card_revealed or False
        game.peeked_cards = db_game.peeked_cards or []
        game.next_card_peeked = db_game.next_card_peeked
        game.cheat_used_this_round = db_game.cheat_used_this_round
        game.last_round_state = db_game.last_round_state

        # Restore deck
        game.deck = Deck(CONFIG["deck_count"])
        if db_game.deck_state:
            game.deck.cards = [game._deserialize_card(c) for c in db_game.deck_state]

        # Restore hands
        game.player_hand = game._deserialize_hand(db_game.player_hand) if db_game.player_hand else None
        game.dealer_hand = game._deserialize_hand(db_game.dealer_hand) if db_game.dealer_hand else None

        return game

    def _deserialize_hand(self, hand_data: Dict) -> Hand:
        """Restore a Hand object from dict"""
        hand = Hand()
        for card_data in hand_data.get("cards", []):
            hand.cards.append(self._deserialize_card(card_data))
        hand.bet = hand_data.get("bet", 0)
        hand.is_standing = hand_data.get("is_standing", False)
        hand.is_busted = hand_data.get("is_busted", False)
        hand.is_blackjack = hand_data.get("is_blackjack", False)
        hand.is_doubled = hand_data.get("is_doubled", False)
        return hand

    @staticmethod
    def _deserialize_card(card_data: Dict) -> Card:
        """Restore a Card object from dict"""
        card = Card(card_data["rank"], Suit(card_data["suit"]))
        card.id = card_data.get("id", card.id)
        return card


# ═══════════════════════════════════════════════════════════════════════════════
# DATABASE HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def save_game_to_db(game: Game, db: Session):
    """Save game state to database"""
    db_data = game.to_db_model()

    db_game = db.query(GameModel).filter(GameModel.id == game.id).first()

    if db_game:
        # Update existing game
        for key, value in db_data.items():
            if key != "id":
                setattr(db_game, key, value)
        # Update stats
        if db_game.stats:
            db_game.stats.wins = game.wins
            db_game.stats.losses = game.losses
            db_game.stats.pushes = game.pushes
            db_game.stats.rounds = game.rounds
            db_game.stats.cheats_used = game.cheats_used
            db_game.stats.cheats_detected = game.cheats_detected
    else:
        # Create new game
        db_game = GameModel(**db_data)
        db.add(db_game)
        db.flush()
        # Create stats
        stats = StatsModel(
            game_id=game.id,
            wins=game.wins,
            losses=game.losses,
            pushes=game.pushes,
            rounds=game.rounds,
            cheats_used=game.cheats_used,
            cheats_detected=game.cheats_detected,
        )
        db.add(stats)

    db.commit()


def load_game_from_db(game_id: str, db: Session) -> Optional[Game]:
    """Load game state from database"""
    db_game = db.query(GameModel).filter(GameModel.id == game_id).first()
    if not db_game:
        return None

    stats = db.query(StatsModel).filter(StatsModel.game_id == game_id).first()
    return Game.from_db_model(db_game, stats)


def delete_game_from_db(game_id: str, db: Session) -> Optional[Dict]:
    """Delete game and return final stats for leaderboard"""
    db_game = db.query(GameModel).filter(GameModel.id == game_id).first()
    if not db_game:
        return None

    stats = db.query(StatsModel).filter(StatsModel.game_id == game_id).first()

    final_stats = {
        "player_name": db_game.player_name,
        "final_chips": db_game.player_chips,
        "profit": db_game.player_chips - CONFIG["starting_chips"],
        "rounds_played": stats.rounds if stats else 0,
        "wins": stats.wins if stats else 0,
        "losses": stats.losses if stats else 0,
        "pushes": stats.pushes if stats else 0,
        "cheats_used": stats.cheats_used if stats else 0,
        "cheats_detected": stats.cheats_detected if stats else 0,
        "highest_garito": db_game.current_garito,
        "win_rate": f"{(stats.wins / stats.rounds * 100):.1f}%" if stats and stats.rounds > 0 else "0%"
    }

    # Save to leaderboard
    leaderboard_entry = LeaderboardModel(
        player_name=db_game.player_name,
        final_chips=db_game.player_chips,
        profit=db_game.player_chips - CONFIG["starting_chips"],
        highest_garito=db_game.current_garito,
        rounds_played=stats.rounds if stats else 0,
        wins=stats.wins if stats else 0,
        losses=stats.losses if stats else 0,
        win_rate=(stats.wins / stats.rounds * 100) if stats and stats.rounds > 0 else 0,
        cheats_used=stats.cheats_used if stats else 0,
        cheats_detected=stats.cheats_detected if stats else 0,
    )
    db.add(leaderboard_entry)

    # Delete the game
    db.delete(db_game)
    db.commit()

    return final_stats


# ═══════════════════════════════════════════════════════════════════════════════
# API
# ═══════════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="Blackjack Roguelite API",
    version="2.1.0",
    description="Backend para el Blackjack Roguelite - Etapa 2.1: Fix Game Over + Peek Next Card"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir imágenes estáticas (crear carpeta images en el mismo directorio)
# app.mount("/images", StaticFiles(directory="images"), name="images")

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup"""
    try:
        init_db()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Warning: Could not initialize database: {e}")
        print("Running in memory-only mode")


# Request Models
class CreateGameRequest(BaseModel):
    player_name: str = "Forastero"
    difficulty: str = "normal"  # easy, normal, hard

class PlaceBetRequest(BaseModel):
    amount: int

class ActionRequest(BaseModel):
    action: PlayerAction

class CheatRequest(BaseModel):
    cheat_id: str

class ItemRequest(BaseModel):
    item_id: str


@app.get("/")
def root():
    return {
        "game": "Blackjack Roguelite",
        "version": "3.0.0 - Etapa 3.0",
        "features": [
            "Garitos", "Trampas", "Objetos", "Estres",
            "Peek Next Card", "Dealer Images",
            "Sistema de Dificultad", "Win Streak con Multiplicadores",
            "Items Multiplicadores de Bonus"
        ],
        "status": "online"
    }


@app.get("/meta/garitos")
def get_garitos():
    """Info de todos los garitos"""
    return GARITOS


@app.get("/meta/cheats")
def get_cheats():
    """Info de todas las trampas"""
    return TRAMPAS


@app.get("/meta/items")
def get_items():
    """Info de todos los objetos"""
    return ITEMS


@app.get("/meta/difficulties")
def get_difficulties():
    """Info de todos los niveles de dificultad"""
    return DIFFICULTY_SETTINGS


@app.post("/games")
def create_game(request: CreateGameRequest, db: Session = Depends(get_db)):
    # Validar dificultad
    difficulty = request.difficulty if request.difficulty in DIFFICULTY_SETTINGS else "normal"

    game_id = str(uuid.uuid4())[:8]
    game = Game(game_id, request.player_name, difficulty)

    # Save to database
    save_game_to_db(game, db)

    garito = game.get_garito()
    diff = game.get_difficulty_settings()

    return {
        "game_id": game_id,
        "message": f"Bienvenido a {garito['name']}, {request.player_name}",
        "starting_chips": game.player_chips,
        "starting_stress": game.stress,
        "difficulty": {
            "id": difficulty,
            "name": diff["name"],
            "icon": diff["icon"],
        },
        "garito": garito["name"],
        "dealer": garito["dealer_name"]
    }


@app.get("/games/{game_id}")
def get_game(game_id: str, db: Session = Depends(get_db)):
    game = load_game_from_db(game_id, db)
    if not game:
        raise HTTPException(status_code=404, detail="Partida no encontrada")
    return game.to_dict()


@app.post("/games/{game_id}/bet")
def place_bet(game_id: str, request: PlaceBetRequest, db: Session = Depends(get_db)):
    game = load_game_from_db(game_id, db)
    if not game:
        raise HTTPException(status_code=404, detail="Partida no encontrada")

    try:
        game.place_bet(request.amount)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    save_game_to_db(game, db)
    return game.to_dict()


@app.post("/games/{game_id}/action")
def player_action(game_id: str, request: ActionRequest, db: Session = Depends(get_db)):
    game = load_game_from_db(game_id, db)
    if not game:
        raise HTTPException(status_code=404, detail="Partida no encontrada")

    try:
        game.player_action(request.action)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    save_game_to_db(game, db)
    return game.to_dict()


@app.post("/games/{game_id}/cheat")
def use_cheat(game_id: str, request: CheatRequest, db: Session = Depends(get_db)):
    """Intenta hacer una trampa"""
    game = load_game_from_db(game_id, db)
    if not game:
        raise HTTPException(status_code=404, detail="Partida no encontrada")

    result = game.attempt_cheat(request.cheat_id)
    save_game_to_db(game, db)

    return {
        "cheat_result": result,
        "game_state": game.to_dict()
    }


@app.post("/games/{game_id}/use-item")
def use_item(game_id: str, request: ItemRequest, db: Session = Depends(get_db)):
    """Usa un objeto del inventario"""
    game = load_game_from_db(game_id, db)
    if not game:
        raise HTTPException(status_code=404, detail="Partida no encontrada")

    result = game.use_item(request.item_id)
    save_game_to_db(game, db)

    return {
        "item_result": result,
        "game_state": game.to_dict()
    }


@app.post("/games/{game_id}/buy-item")
def buy_item(game_id: str, request: ItemRequest, db: Session = Depends(get_db)):
    """Compra un objeto en la tienda"""
    game = load_game_from_db(game_id, db)
    if not game:
        raise HTTPException(status_code=404, detail="Partida no encontrada")

    result = game.buy_item(request.item_id)
    save_game_to_db(game, db)

    return {
        "purchase_result": result,
        "game_state": game.to_dict()
    }


@app.post("/games/{game_id}/advance-garito")
def advance_garito(game_id: str, db: Session = Depends(get_db)):
    """Avanza al siguiente garito"""
    game = load_game_from_db(game_id, db)
    if not game:
        raise HTTPException(status_code=404, detail="Partida no encontrada")

    result = game.advance_garito()
    save_game_to_db(game, db)

    return {
        "advance_result": result,
        "game_state": game.to_dict()
    }


@app.post("/games/{game_id}/leave-shop")
def leave_shop(game_id: str, db: Session = Depends(get_db)):
    """Sale de la tienda"""
    game = load_game_from_db(game_id, db)
    if not game:
        raise HTTPException(status_code=404, detail="Partida no encontrada")

    game.leave_shop()
    save_game_to_db(game, db)

    return game.to_dict()


@app.post("/games/{game_id}/new-round")
def new_round(game_id: str, db: Session = Depends(get_db)):
    game = load_game_from_db(game_id, db)
    if not game:
        raise HTTPException(status_code=404, detail="Partida no encontrada")

    try:
        result = game.new_round()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    save_game_to_db(game, db)

    return {
        **game.to_dict(),
        **result
    }


@app.delete("/games/{game_id}")
def leave_game(game_id: str, db: Session = Depends(get_db)):
    final_stats = delete_game_from_db(game_id, db)
    if not final_stats:
        raise HTTPException(status_code=404, detail="Partida no encontrada")

    return {
        "message": "Hasta la proxima, forastero",
        "final_stats": final_stats
    }


@app.get("/leaderboard")
def get_leaderboard(limit: int = 10, db: Session = Depends(get_db)):
    """Get top players from leaderboard"""
    entries = db.query(LeaderboardModel).order_by(
        LeaderboardModel.final_chips.desc()
    ).limit(limit).all()

    return [
        {
            "player_name": e.player_name,
            "final_chips": e.final_chips,
            "profit": e.profit,
            "highest_garito": e.highest_garito,
            "rounds_played": e.rounds_played,
            "wins": e.wins,
            "losses": e.losses,
            "win_rate": f"{e.win_rate:.1f}%",
            "date": e.created_at.isoformat() if e.created_at else None
        }
        for e in entries
    ]


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    from sqlalchemy import text
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    return {
        "status": "healthy",
        "database": db_status
    }


if __name__ == "__main__":
    import uvicorn
    print("""
    ╔═══════════════════════════════════════════════════════════════════════╗
    ║              BLACKJACK ROGUELITE - ETAPA 2.1                          ║
    ║         Sistema de Garitos + Trampas + Objetos                        ║
    ║         + FIX: Game Over si saldo < apuesta mínima                    ║
    ║         + NEW: Trampa "Espiar Próxima Carta"                          ║
    ║         + NEW: Imágenes de croupier por nivel                         ║
    ╠═══════════════════════════════════════════════════════════════════════╣
    ║  Servidor: http://localhost:8000                                      ║
    ║  Docs:     http://localhost:8000/docs                                 ║
    ╠═══════════════════════════════════════════════════════════════════════╣
    ║  GARITOS:                                                             ║
    ║  1. El Callejón de los Desahuciados (Inicio)                          ║
    ║  2. La Taberna del Tuerto                                             ║
    ║  3. El Salón Dorado                                                   ║
    ║  4. La Casa de la Viuda Negra                                         ║
    ║  5. El Infierno de Dante (Final)                                      ║
    ╠═══════════════════════════════════════════════════════════════════════╣
    ║  TRAMPAS:                                                             ║
    ║  👁️ Espiar Carta Oculta - Ver carta del crupier (10% riesgo)          ║
    ║  🔮 Espiar Próxima Carta - Ver próxima del mazo (35% riesgo!)         ║
    ║  🔄 Cambiar Carta - Swap tu peor carta (20% riesgo)                   ║
    ║  🃏 Carta Extra - Hit gratis (25% riesgo)                             ║
    ║  ✒️ Marcar Mazo - Ver 3 cartas siguientes (15% riesgo)                ║
    ║  💰 Sobornar - El dealer se equivoca (30% riesgo + $50)               ║
    ╚═══════════════════════════════════════════════════════════════════════╝
    """)
    uvicorn.run(app, host="0.0.0.0", port=8000)
