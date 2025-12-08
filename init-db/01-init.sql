-- Blackjack Roguelite Database Initialization

-- Games table
CREATE TABLE IF NOT EXISTS games (
    id VARCHAR(8) PRIMARY KEY,
    player_name VARCHAR(100) NOT NULL,
    player_chips INT DEFAULT 500,
    stress INT DEFAULT 0,
    status VARCHAR(50) DEFAULT 'waiting_for_bet',
    current_garito INT DEFAULT 1,
    garitos_completed JSON DEFAULT '[]',

    -- Inventory
    inventory_items JSON DEFAULT '{}',
    inventory_passive_effects JSON DEFAULT '{}',
    inventory_unlocked_cheats JSON DEFAULT '["peek_card", "peek_next_card"]',
    inventory_cheat_cooldowns JSON DEFAULT '{}',
    inventory_guaranteed_cheat BOOLEAN DEFAULT FALSE,
    inventory_rewind_available BOOLEAN DEFAULT FALSE,

    -- Current round state
    current_bet INT DEFAULT 0,
    player_hand JSON,
    dealer_hand JSON,
    deck_state JSON,
    round_result VARCHAR(50),
    round_message VARCHAR(500),

    -- Cheat state
    dealer_card_revealed BOOLEAN DEFAULT FALSE,
    peeked_cards JSON DEFAULT '[]',
    next_card_peeked JSON,
    cheat_used_this_round VARCHAR(50),

    -- Rewind state
    last_round_state JSON,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_player_name (player_name),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Game stats table
CREATE TABLE IF NOT EXISTS game_stats (
    id INT AUTO_INCREMENT PRIMARY KEY,
    game_id VARCHAR(8) UNIQUE,
    wins INT DEFAULT 0,
    losses INT DEFAULT 0,
    pushes INT DEFAULT 0,
    rounds INT DEFAULT 0,
    cheats_used INT DEFAULT 0,
    cheats_detected INT DEFAULT 0,

    FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Leaderboard table
CREATE TABLE IF NOT EXISTS leaderboard (
    id INT AUTO_INCREMENT PRIMARY KEY,
    player_name VARCHAR(100) NOT NULL,
    final_chips INT NOT NULL,
    profit INT NOT NULL,
    highest_garito INT DEFAULT 1,
    rounds_played INT DEFAULT 0,
    wins INT DEFAULT 0,
    losses INT DEFAULT 0,
    win_rate FLOAT DEFAULT 0.0,
    cheats_used INT DEFAULT 0,
    cheats_detected INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_final_chips (final_chips DESC),
    INDEX idx_profit (profit DESC),
    INDEX idx_highest_garito (highest_garito DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
