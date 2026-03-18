-- 1. Setup the Database
CREATE DATABASE IF NOT EXISTS green_db;
USE green_db;

-- 2. Disable Foreign Key Checks
SET FOREIGN_KEY_CHECKS = 0;

-- 3. Drop all tables to start fresh
DROP TABLE IF EXISTS game_players;
DROP TABLE IF EXISTS games;
DROP TABLE IF EXISTS lobby_players;
DROP TABLE IF EXISTS lobbies;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS cards;

-- 4. Re-enable Foreign Key Checks
SET FOREIGN_KEY_CHECKS = 1;

-- USERS TABLE
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    total_games_played INT DEFAULT 0,
    total_wins INT DEFAULT 0,
    total_losses INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- GAMES TABLE
CREATE TABLE IF NOT EXISTS games (
    game_id INT AUTO_INCREMENT PRIMARY KEY,
    game_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('active', 'completed', 'cancelled') DEFAULT 'completed'
);

-- LOBBIES TABLE
CREATE TABLE IF NOT EXISTS lobbies (
    lobby_id INT AUTO_INCREMENT PRIMARY KEY,
    lobby_code CHAR(6) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- LOBBY PLAYERS TABLE
CREATE TABLE IF NOT EXISTS lobby_players (
    lobby_player_id INT AUTO_INCREMENT PRIMARY KEY,
    lobby_id INT NOT NULL,
    username VARCHAR(50) NOT NULL,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_lobby_player_lobby
        FOREIGN KEY (lobby_id) REFERENCES lobbies(lobby_id)
        ON DELETE CASCADE,
    UNIQUE (lobby_id, username)
);

-- GAME PLAYERS TABLE
CREATE TABLE IF NOT EXISTS game_players (
    game_player_id INT AUTO_INCREMENT PRIMARY KEY,
    game_id INT NOT NULL,
    user_id INT NOT NULL,
    rounds INT NOT NULL,
    score INT DEFAULT 0,
    is_winner BOOLEAN DEFAULT FALSE,
    CONSTRAINT fk_game_link
        FOREIGN KEY (game_id) REFERENCES games(game_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_user_link
        FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE CASCADE,
    UNIQUE (game_id, user_id)
);

-- CARDS TABLE
CREATE TABLE IF NOT EXISTS cards (
    card_id INT AUTO_INCREMENT PRIMARY KEY,
    card_name VARCHAR(50) NOT NULL,
    card_type VARCHAR(50) NOT NULL,
    card_detail TEXT
);
