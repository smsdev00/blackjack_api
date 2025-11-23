from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional, Set
from enum import Enum
import random
import uuid
import json
import redis
from datetime import datetime

# Configuration
CONFIG = {
    "deck_count": 6,
    "dealer_stand_value": 17,
    "blackjack_payout": 1.5,
    "starting_chips": 1000,
    "minimum_bet": 10,
    "maximum_bet": 500,
    "insurance_payout": 2.0,
    "repeat_last_bet": True,
    "allow_surrender": True,
    "perfect_pairs_payout": {
        "perfect_pair": 25,
        "colored_pair": 12,
        "mixed_pair": 6
    },
    "redis_host": "localhost",
    "redis_port": 6379,
    "redis_db": 0
}

# Redis connection
redis_client = redis.Redis(
    host=CONFIG["redis_host"],
    port=CONFIG["redis_port"],
    db=CONFIG["redis_db"],
    decode_responses=True
)

# Mysql connection would go here if needed
mysql_config = {
    "host": "localhost",
    "port": 3306,
    "user": "test"
    "password": "test",
    "database": "blackjack_db"
}

# Enums
class Suit(str, Enum):
    HEARTS = "hearts"
    DIAMONDS = "diamonds"
    CLUBS = "clubs"
    SPADES = "spades"

class GameStatus(str, Enum):
    WAITING_FOR_BET = "waiting_for_bet"
    DEALING = "dealing"
    PLAYER_TURN = "player_turn"
    DEALER_TURN = "dealer_turn"
    ROUND_COMPLETE = "round_complete"
    GAME_OVER = "game_over"

class PlayerAction(str, Enum):
    HIT = "hit"
    STAND = "stand"
    DOUBLE = "double"
    SPLIT = "split"
    INSURANCE = "insurance"

class HandResult(str, Enum):
    WIN = "win"
    LOSS = "loss"
    PUSH = "push"
    BLACKJACK = "blackjack"
    INSURANCE_WIN = "insurance_win"
    PERFECT_PAIR = "perfect_pair"
    COLORED_PAIR = "colored_pair"
    MIXED_PAIR = "mixed_pair"

# Models
class Card:
    def __init__(self, rank: str, suit: Suit):
        self.rank = rank
        self.suit = suit
    
    def value(self) -> int:
        if self.rank in ['J', 'Q', 'K']:
            return 10
        elif self.rank == 'A':
            return 11
        else:
            return int(self.rank)
    
    def to_dict(self) -> Dict:
        return {"rank": self.rank, "suit": self.suit}
    
    @staticmethod
    def from_dict(data: Dict) -> 'Card':
        return Card(data["rank"], Suit(data["suit"]))
    
    def get_color(self) -> str:
        return "red" if self.suit in [Suit.HEARTS, Suit.DIAMONDS] else "black"

class Deck:
    def __init__(self, deck_count: int = 1):
        self.cards: List[Card] = []
        self.reset(deck_count)
    
    def reset(self, deck_count: int):
        self.cards = []
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        suits = list(Suit)
        
        for _ in range(deck_count):
            for suit in suits:
                for rank in ranks:
                    self.cards.append(Card(rank, suit))
        
        random.shuffle(self.cards)
    
    def deal(self) -> Card:
        if len(self.cards) < 20:  # Reshuffle if running low
            self.reset(CONFIG["deck_count"])
        return self.cards.pop()
    
    def to_dict(self) -> List[Dict]:
        return [card.to_dict() for card in self.cards]
    
    @staticmethod
    def from_dict(data: List[Dict]) -> 'Deck':
        deck = Deck(0)
        deck.cards = [Card.from_dict(card_data) for card_data in data]
        return deck

class Hand:
    def __init__(self, hand_id: str = None):
        self.id = hand_id or str(uuid.uuid4())
        self.cards: List[Card] = []
        self.bet: int = 0
        self.insurance_bet: int = 0
        self.perfect_pairs_bet: int = 0
        self.is_standing: bool = False
        self.is_busted: bool = False
        self.is_blackjack: bool = False
        self.is_split_hand: bool = False
        self.is_doubled: bool = False
        self.parent_hand_id: Optional[str] = None
    
    def add_card(self, card: Card):
        self.cards.append(card)
        self._check_status()
    
    def calculate_value(self) -> int:
        value = sum(card.value() for card in self.cards)
        aces = sum(1 for card in self.cards if card.rank == 'A')
        
        while value > 21 and aces > 0:
            value -= 10
            aces -= 1
        
        return value
    
    def _check_status(self):
        value = self.calculate_value()
        
        if value > 21:
            self.is_busted = True
            self.is_standing = True
        
        if len(self.cards) == 2 and value == 21 and not self.is_split_hand:
            self.is_blackjack = True
            self.is_standing = True
    
    def can_split(self) -> bool:
        return len(self.cards) == 2 and self.cards[0].value() == self.cards[1].value()
    
    def can_double(self) -> bool:
        return len(self.cards) == 2 and not self.is_doubled
    
    def check_perfect_pairs(self) -> Optional[str]:
        if len(self.cards) != 2:
            return None
        
        card1, card2 = self.cards[0], self.cards[1]
        
        if card1.rank != card2.rank:
            return None
        
        if card1.suit == card2.suit:
            return "perfect_pair"
        
        if card1.get_color() == card2.get_color():
            return "colored_pair"
        
        return "mixed_pair"
    
    def split(self) -> 'Hand':
        if not self.can_split():
            raise ValueError("Cannot split this hand")
        
        new_hand = Hand()
        new_hand.cards = [self.cards.pop()]
        new_hand.bet = self.bet
        new_hand.is_split_hand = True
        new_hand.parent_hand_id = self.id
        self.is_split_hand = True
        
        return new_hand
    
    def to_dict(self, hide_second: bool = False) -> Dict:
        cards = [card.to_dict() for card in self.cards]
        
        if hide_second and len(cards) > 1:
            return {
                "id": self.id,
                "cards": [cards[0], {"rank": "hidden", "suit": "hidden"}],
                "value": self.cards[0].value(),
                "is_standing": self.is_standing,
                "is_busted": self.is_busted,
                "is_blackjack": False,
                "bet": self.bet,
                "insurance_bet": self.insurance_bet,
                "perfect_pairs_bet": self.perfect_pairs_bet,
                "is_doubled": self.is_doubled
            }
        
        return {
            "id": self.id,
            "cards": cards,
            "value": self.calculate_value(),
            "is_standing": self.is_standing,
            "is_busted": self.is_busted,
            "is_blackjack": self.is_blackjack,
            "bet": self.bet,
            "insurance_bet": self.insurance_bet,
            "perfect_pairs_bet": self.perfect_pairs_bet,
            "is_split_hand": self.is_split_hand,
            "is_doubled": self.is_doubled
        }
    
    @staticmethod
    def from_dict(data: Dict) -> 'Hand':
        hand = Hand(data["id"])
        hand.cards = [Card.from_dict(c) for c in data["cards"] if c.get("rank") != "hidden"]
        hand.bet = data["bet"]
        hand.insurance_bet = data["insurance_bet"]
        hand.perfect_pairs_bet = data["perfect_pairs_bet"]
        hand.is_standing = data["is_standing"]
        hand.is_busted = data["is_busted"]
        hand.is_blackjack = data["is_blackjack"]
        hand.is_split_hand = data.get("is_split_hand", False)
        hand.is_doubled = data.get("is_doubled", False)
        return hand

class Game:
    def __init__(self, game_id: str, player_name: str):
        self.id = game_id
        self.player_id = str(uuid.uuid4())
        self.player_name = player_name
        self.player_chips = CONFIG["starting_chips"]
        self.house_pot = 10000  # House starting pot
        self.deck = Deck(CONFIG["deck_count"])
        self.player_hands: List[Hand] = []
        self.dealer_hand: Optional[Hand] = None
        self.current_hand_index = 0
        self.status = GameStatus.WAITING_FOR_BET
        self.round_number = 0
        self.total_rounds_played = 0
        self.player_wins = 0
        self.player_losses = 0
        self.player_pushes = 0
    
    def can_place_bet(self, amount: int) -> bool:
        return (amount >= CONFIG["minimum_bet"] and 
                amount <= CONFIG["maximum_bet"] and
                amount <= self.player_chips)
    
    def place_bet(self, main_bet: int, perfect_pairs_bet: int = 0):
        if self.status != GameStatus.WAITING_FOR_BET:
            raise HTTPException(status_code=400, detail="Not in betting phase")
        
        if not self.can_place_bet(main_bet):
            raise HTTPException(status_code=400, detail=f"Invalid bet. Min: {CONFIG['minimum_bet']}, Max: {CONFIG['maximum_bet']}, Your chips: {self.player_chips}")
        
        total_bet = main_bet + perfect_pairs_bet
        if total_bet > self.player_chips:
            raise HTTPException(status_code=400, detail="Not enough chips")
        
        # Create new hand for player
        hand = Hand()
        hand.bet = main_bet
        hand.perfect_pairs_bet = perfect_pairs_bet
        self.player_hands = [hand]
        self.current_hand_index = 0
        
        # Deduct bet from player chips
        self.player_chips -= total_bet
        
        # Start dealing
        self._deal_initial_cards()
    
    def _deal_initial_cards(self):
        self.status = GameStatus.DEALING
        self.round_number += 1
        self.total_rounds_played += 1
        
        # Create dealer hand
        self.dealer_hand = Hand()
        
        # Deal cards: player, dealer, player, dealer
        self.player_hands[0].add_card(self.deck.deal())
        self.dealer_hand.add_card(self.deck.deal())
        self.player_hands[0].add_card(self.deck.deal())
        self.dealer_hand.add_card(self.deck.deal())
        
        # Check for perfect pairs
        if self.player_hands[0].perfect_pairs_bet > 0:
            pair_type = self.player_hands[0].check_perfect_pairs()
            if pair_type:
                payout_multiplier = CONFIG["perfect_pairs_payout"][pair_type]
                winnings = self.player_hands[0].perfect_pairs_bet * (payout_multiplier + 1)
                self.player_chips += winnings
                self.house_pot -= winnings
                self._save_hand_result(pair_type, self.player_hands[0].perfect_pairs_bet, winnings)
        
        # Check for dealer blackjack
        if self.dealer_hand.is_blackjack:
            self._finish_round()
        # Check for player blackjack
        elif self.player_hands[0].is_blackjack:
            self._finish_round()
        else:
            self.status = GameStatus.PLAYER_TURN
    
    def get_current_hand(self) -> Optional[Hand]:
        if self.current_hand_index < len(self.player_hands):
            return self.player_hands[self.current_hand_index]
        return None
    
    def can_take_insurance(self) -> bool:
        if not self.dealer_hand or len(self.dealer_hand.cards) < 1:
            return False
        
        dealer_up_card = self.dealer_hand.cards[0]
        current_hand = self.get_current_hand()
        
        return (dealer_up_card.rank == 'A' and 
                current_hand and 
                len(current_hand.cards) == 2 and
                current_hand.insurance_bet == 0 and
                self.player_chips >= current_hand.bet // 2)
    
    def player_action(self, action: PlayerAction) -> Dict:
        if self.status != GameStatus.PLAYER_TURN:
            raise HTTPException(status_code=400, detail="Not player's turn")
        
        hand = self.get_current_hand()
        if not hand or hand.is_standing:
            raise HTTPException(status_code=400, detail="No active hand")
        
        if action == PlayerAction.HIT:
            hand.add_card(self.deck.deal())
            if hand.is_busted or hand.is_standing:
                self._next_hand()
            return {"message": "Card dealt"}
        
        elif action == PlayerAction.STAND:
            hand.is_standing = True
            self._next_hand()
            return {"message": "Standing"}
        
        elif action == PlayerAction.DOUBLE:
            if not hand.can_double():
                raise HTTPException(status_code=400, detail="Cannot double down")
            
            if self.player_chips < hand.bet:
                raise HTTPException(status_code=400, detail="Not enough chips to double")
            
            self.player_chips -= hand.bet
            hand.bet *= 2
            hand.is_doubled = True
            hand.add_card(self.deck.deal())
            hand.is_standing = True
            self._next_hand()
            return {"message": "Doubled down"}
        
        elif action == PlayerAction.SPLIT:
            if not hand.can_split():
                raise HTTPException(status_code=400, detail="Cannot split")
            
            if self.player_chips < hand.bet:
                raise HTTPException(status_code=400, detail="Not enough chips to split")
            
            # Deduct bet for second hand
            self.player_chips -= hand.bet
            
            # Split the hand
            new_hand = hand.split()
            self.player_hands.append(new_hand)
            
            # Deal one card to each split hand
            hand.add_card(self.deck.deal())
            new_hand.add_card(self.deck.deal())
            
            return {"message": "Hand split"}
        
        elif action == PlayerAction.INSURANCE:
            if not self.can_take_insurance():
                raise HTTPException(status_code=400, detail="Cannot take insurance")
            
            insurance_amount = hand.bet // 2
            hand.insurance_bet = insurance_amount
            self.player_chips -= insurance_amount
            
            return {"message": "Insurance taken"}
        
        raise HTTPException(status_code=400, detail="Invalid action")
    
    def _next_hand(self):
        self.current_hand_index += 1
        
        # Check if there are more hands to play
        if self.current_hand_index < len(self.player_hands):
            current = self.get_current_hand()
            if current and not current.is_standing:
                return  # Continue with next hand
        
        # All hands played, dealer's turn
        self._dealer_turn()
    
    def _dealer_turn(self):
        self.status = GameStatus.DEALER_TURN
        
        # Check if all player hands are busted
        all_busted = all(hand.is_busted for hand in self.player_hands)
        
        if not all_busted:
            # Dealer must play
            while self.dealer_hand.calculate_value() < CONFIG["dealer_stand_value"]:
                self.dealer_hand.add_card(self.deck.deal())
        
        self._finish_round()
    
    def _finish_round(self):
        self.status = GameStatus.ROUND_COMPLETE
        dealer_value = self.dealer_hand.calculate_value()
        dealer_busted = self.dealer_hand.is_busted
        dealer_blackjack = self.dealer_hand.is_blackjack
        
        round_result = {
            "hands": [],
            "net_change": 0
        }
        
        for hand in self.player_hands:
            hand_value = hand.calculate_value()
            result = None
            payout = 0
            
            # Process insurance bet
            if hand.insurance_bet > 0:
                if dealer_blackjack:
                    insurance_payout = int(hand.insurance_bet * CONFIG["insurance_payout"])
                    payout += insurance_payout + hand.insurance_bet
                    self.house_pot -= insurance_payout
                    self._save_hand_result(HandResult.INSURANCE_WIN, hand.insurance_bet, insurance_payout)
                else:
                    # Insurance lost (already deducted)
                    self.house_pot += hand.insurance_bet
            
            # Player busted
            if hand.is_busted:
                result = HandResult.LOSS
                self.house_pot += hand.bet
                self.player_losses += 1
            
            # Player blackjack
            elif hand.is_blackjack:
                if dealer_blackjack:
                    result = HandResult.PUSH
                    payout += hand.bet
                    self.player_pushes += 1
                else:
                    result = HandResult.BLACKJACK
                    blackjack_payout = int(hand.bet * CONFIG["blackjack_payout"])
                    payout += hand.bet + blackjack_payout
                    self.house_pot -= blackjack_payout
                    self.player_wins += 1
            
            # Dealer busted or player has higher value
            elif dealer_busted or hand_value > dealer_value:
                result = HandResult.WIN
                payout += hand.bet * 2
                self.house_pot -= hand.bet
                self.player_wins += 1
            
            # Push
            elif hand_value == dealer_value:
                result = HandResult.PUSH
                payout += hand.bet
                self.player_pushes += 1
            
            # Player lost
            else:
                result = HandResult.LOSS
                self.house_pot += hand.bet
                self.player_losses += 1
            
            self.player_chips += payout
            round_result["net_change"] += payout - hand.bet - hand.insurance_bet
            
            hand_result = {
                "hand_value": hand_value,
                "result": result,
                "bet": hand.bet,
                "payout": payout,
                "is_blackjack": hand.is_blackjack,
                "is_split": hand.is_split_hand,
                "is_doubled": hand.is_doubled
            }
            round_result["hands"].append(hand_result)
            
            self._save_hand_result(result, hand.bet, payout)
        
        # Check if player is broke
        if self.player_chips < CONFIG["minimum_bet"]:
            self.status = GameStatus.GAME_OVER
        else:
            self.status = GameStatus.WAITING_FOR_BET
        
        return round_result
    
    def _save_hand_result(self, result: str, bet: int, payout: int):
        result_id = str(uuid.uuid4())
        redis_client.hset(f"hand_result:{result_id}", mapping={
            "game_id": self.id,
            "player_id": self.player_id,
            "result": result,
            "bet": bet,
            "payout": payout,
            "round": self.round_number,
            "timestamp": datetime.now().isoformat()
        })
        redis_client.lpush(f"history:game:{self.id}", result_id)
        redis_client.lpush(f"history:player:{self.player_id}", result_id)
    
    def to_dict(self) -> Dict:
        hide_dealer_card = self.status in [GameStatus.DEALING, GameStatus.PLAYER_TURN]
        
        return {
            "game_id": self.id,
            "player_id": self.player_id,
            "player_name": self.player_name,
            "player_chips": self.player_chips,
            "house_pot": self.house_pot,
            "status": self.status,
            "round_number": self.round_number,
            "total_rounds": self.total_rounds_played,
            "wins": self.player_wins,
            "losses": self.player_losses,
            "pushes": self.player_pushes,
            "dealer_hand": self.dealer_hand.to_dict(hide_second=hide_dealer_card) if self.dealer_hand else None,
            "player_hands": [hand.to_dict() for hand in self.player_hands],
            "current_hand_index": self.current_hand_index,
            "can_take_insurance": self.can_take_insurance(),
            "minimum_bet": CONFIG["minimum_bet"],
            "maximum_bet": CONFIG["maximum_bet"]
        }
    
    def save_to_redis(self):
        game_data = {
            "id": self.id,
            "player_id": self.player_id,
            "player_name": self.player_name,
            "player_chips": self.player_chips,
            "house_pot": self.house_pot,
            "status": self.status.value,
            "round_number": self.round_number,
            "total_rounds": self.total_rounds_played,
            "wins": self.player_wins,
            "losses": self.player_losses,
            "pushes": self.player_pushes,
            "deck": json.dumps(self.deck.to_dict()),
            "player_hands": json.dumps([h.to_dict() for h in self.player_hands]),
            "dealer_hand": json.dumps(self.dealer_hand.to_dict()) if self.dealer_hand else "",
            "current_hand_index": self.current_hand_index
        }
        redis_client.hset(f"game:{self.id}", mapping=game_data)
        redis_client.expire(f"game:{self.id}", 86400)  # Expire after 24 hours
    
    @staticmethod
    def load_from_redis(game_id: str) -> Optional['Game']:
        data = redis_client.hgetall(f"game:{game_id}")
        if not data:
            return None
        
        game = Game.__new__(Game)
        game.id = data["id"]
        game.player_id = data["player_id"]
        game.player_name = data["player_name"]
        game.player_chips = int(data["player_chips"])
        game.house_pot = int(data["house_pot"])
        game.status = GameStatus(data["status"])
        game.round_number = int(data["round_number"])
        game.total_rounds_played = int(data["total_rounds"])
        game.player_wins = int(data["wins"])
        game.player_losses = int(data["losses"])
        game.player_pushes = int(data["pushes"])
        game.deck = Deck.from_dict(json.loads(data["deck"]))
        game.player_hands = [Hand.from_dict(h) for h in json.loads(data["player_hands"])]
        game.dealer_hand = Hand.from_dict(json.loads(data["dealer_hand"])) if data["dealer_hand"] else None
        game.current_hand_index = int(data["current_hand_index"])
        
        return game

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, game_id: str):
        await websocket.accept()
        if game_id not in self.active_connections:
            self.active_connections[game_id] = set()
        self.active_connections[game_id].add(websocket)
    
    def disconnect(self, websocket: WebSocket, game_id: str):
        if game_id in self.active_connections:
            self.active_connections[game_id].discard(websocket)
    
    async def broadcast(self, message: dict, game_id: str):
        if game_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[game_id]:
                try:
                    await connection.send_json(message)
                except:
                    disconnected.add(connection)
            
            for conn in disconnected:
                self.active_connections[game_id].discard(conn)

manager = ConnectionManager()

# In-memory cache
games: Dict[str, Game] = {}

# API Models
class CreateGameRequest(BaseModel):
    player_name: str

class PlaceBetRequest(BaseModel):
    main_bet: int
    perfect_pairs_bet: int = 0

class ActionRequest(BaseModel):
    action: PlayerAction

# FastAPI App
app = FastAPI(title="Blackjack API", version="3.0.0")

@app.on_event("startup")
async def startup_event():
    try:
        redis_client.ping()
        print("Redis connection successful")
    except redis.ConnectionError:
        print("WARNING: Redis not available")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "status": "Blackjack API is running",
        "version": "3.0.0",
        "mode": "1v1 Player vs House",
        "features": [
            "Persistent sessions",
            "Multiple rounds per game",
            "Player and house pots",
            "Split, Double, Insurance",
            "Perfect Pairs side bet"
        ]
    }

@app.post("/games")
def create_game(request: CreateGameRequest):
    game_id = str(uuid.uuid4())
    game = Game(game_id, request.player_name)
    games[game_id] = game
    game.save_to_redis()
    
    return {
        "game_id": game_id,
        "player_id": game.player_id,
        "starting_chips": game.player_chips,
        "message": "Game created. Place your bet to start."
    }

@app.get("/games/{game_id}")
def get_game_state(game_id: str):
    if game_id not in games:
        game = Game.load_from_redis(game_id)
        if game:
            games[game_id] = game
        else:
            raise HTTPException(status_code=404, detail="Game not found")
    
    game = games[game_id]
    return game.to_dict()

@app.post("/games/{game_id}/bet")
async def place_bet(game_id: str, request: PlaceBetRequest):
    if game_id not in games:
        game = Game.load_from_redis(game_id)
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")
        games[game_id] = game
    
    game = games[game_id]
    game.place_bet(request.main_bet, request.perfect_pairs_bet)
    game.save_to_redis()
    
    await manager.broadcast({
        "type": "bet_placed",
        "game_state": game.to_dict()
    }, game_id)
    
    return game.to_dict()

@app.post("/games/{game_id}/action")
async def player_action(game_id: str, request: ActionRequest):
    if game_id not in games:
        game = Game.load_from_redis(game_id)
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")
        games[game_id] = game
    
    game = games[game_id]
    result = game.player_action(request.action)
    game.save_to_redis()
    
    await manager.broadcast({
        "type": "action_performed",
        "action": request.action,
        "game_state": game.to_dict()
    }, game_id)
    
    return game.to_dict()

@app.post("/games/{game_id}/leave")
async def leave_game(game_id: str):
    if game_id in games:
        game = games[game_id]
        
        # Save final stats
        redis_client.hset(f"player_final:{game.player_id}", mapping={
            "name": game.player_name,
            "final_chips": game.player_chips,
            "rounds_played": game.total_rounds_played,
            "wins": game.player_wins,
            "losses": game.player_losses,
            "pushes": game.player_pushes,
            "ended_at": datetime.now().isoformat()
        })
        
        del games[game_id]
        
        await manager.broadcast({
            "type": "game_ended"
        }, game_id)
    
    return {"message": "Left game successfully"}

@app.get("/games/{game_id}/history")
def get_game_history(game_id: str):
    result_ids = redis_client.lrange(f"history:game:{game_id}", 0, 49)  # Last 50 results
    results = []
    
    for result_id in result_ids:
        result_data = redis_client.hgetall(f"hand_result:{result_id}")
        if result_data:
            results.append(result_data)
    
    return {"history": results}

@app.get("/players/{player_id}/stats")
def get_player_stats(player_id: str):
    # Get current or final stats
    current_game = None
    for game in games.values():
        if game.player_id == player_id:
            current_game = game
            break
    
    if current_game:
        return {
            "player_id": player_id,
            "name": current_game.player_name,
            "current_chips": current_game.player_chips,
            "rounds_played": current_game.total_rounds_played,
            "wins": current_game.player_wins,
            "losses": current_game.player_losses,
            "pushes": current_game.player_pushes,
            "status": "active"
        }
    
    # Check final stats
    final_data = redis_client.hgetall(f"player_final:{player_id}")
    if final_data:
        return {
            "player_id": player_id,
            "name": final_data["name"],
            "final_chips": int(final_data["final_chips"]),
            "rounds_played": int(final_data["rounds_played"]),
            "wins": int(final_data["wins"]),
            "losses": int(final_data["losses"]),
            "pushes": int(final_data["pushes"]),
            "ended_at": final_data["ended_at"],
            "status": "completed"
        }
    
    raise HTTPException(status_code=404, detail="Player not found")

@app.websocket("/ws/{game_id}")
async def websocket_endpoint(websocket: WebSocket, game_id: str):
    await manager.connect(websocket, game_id)
    
    try:
        if game_id in games:
            await websocket.send_json({
                "type": "connected",
                "game_state": games[game_id].to_dict()
            })
        
        while True:
            data = await websocket.receive_text()
            await websocket.send_json({
                "type": "message",
                "data": data
            })
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, game_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket, game_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)