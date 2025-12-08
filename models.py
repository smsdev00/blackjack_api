"""
SQLAlchemy models for Blackjack Roguelite persistence
"""
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class GameModel(Base):
    """Persistent game state"""
    __tablename__ = "games"

    id = Column(String(8), primary_key=True, index=True)
    player_name = Column(String(100), nullable=False)
    player_chips = Column(Integer, default=500)
    stress = Column(Integer, default=0)
    status = Column(String(50), default="waiting_for_bet")
    difficulty = Column(String(20), default="normal")
    current_garito = Column(Integer, default=1)
    garitos_completed = Column(JSON, default=list)

    # Win streak system
    win_streak = Column(Integer, default=0)
    max_win_streak = Column(Integer, default=0)
    last_streak_bonus = Column(Integer, default=0)

    # Inventory stored as JSON
    inventory_items = Column(JSON, default=dict)
    inventory_passive_effects = Column(JSON, default=dict)
    inventory_unlocked_cheats = Column(JSON, default=list)
    inventory_cheat_cooldowns = Column(JSON, default=dict)
    inventory_guaranteed_cheat = Column(Boolean, default=False)
    inventory_rewind_available = Column(Boolean, default=False)

    # Current round state (JSON for complex objects)
    current_bet = Column(Integer, default=0)
    player_hand = Column(JSON, nullable=True)
    dealer_hand = Column(JSON, nullable=True)
    deck_state = Column(JSON, nullable=True)
    round_result = Column(String(50), nullable=True)
    round_message = Column(String(500), nullable=True)

    # Cheat state for current round
    dealer_card_revealed = Column(Boolean, default=False)
    peeked_cards = Column(JSON, default=list)
    next_card_peeked = Column(JSON, nullable=True)
    cheat_used_this_round = Column(String(50), nullable=True)

    # Last round state for rewind
    last_round_state = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship to stats
    stats = relationship("StatsModel", back_populates="game", uselist=False, cascade="all, delete-orphan")


class StatsModel(Base):
    """Game statistics"""
    __tablename__ = "game_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    game_id = Column(String(8), ForeignKey("games.id", ondelete="CASCADE"), unique=True)

    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    pushes = Column(Integer, default=0)
    rounds = Column(Integer, default=0)
    cheats_used = Column(Integer, default=0)
    cheats_detected = Column(Integer, default=0)

    game = relationship("GameModel", back_populates="stats")


class LeaderboardModel(Base):
    """Historical leaderboard entries"""
    __tablename__ = "leaderboard"

    id = Column(Integer, primary_key=True, autoincrement=True)
    player_name = Column(String(100), nullable=False)
    final_chips = Column(Integer, nullable=False)
    profit = Column(Integer, nullable=False)
    highest_garito = Column(Integer, default=1)
    rounds_played = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    win_rate = Column(Float, default=0.0)
    cheats_used = Column(Integer, default=0)
    cheats_detected = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
