import pygame
import chess
import sys
import os
import random
import threading
import time

# --- Constants ---
# Screen dimensions
WIDTH = 800
HEIGHT = 800

# Board dimensions
BOARD_WIDTH = 720
BOARD_HEIGHT = 720
SQUARE_SIZE = BOARD_WIDTH // 8

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LIGHT_SQUARE = (240, 217, 181)
DARK_SQUARE = (181, 136, 99)
HIGHLIGHT_COLOR = (100, 255, 100, 100)
SELECTED_COLOR = (255, 255, 0, 150)

# --- NEW: AI Configuration ---
AI_PLAYER = chess.BLACK
AI_THINK_TIME = 0.5 # Seconds for the AI to "think" to feel more natural

# --- NEW: Piece values for AI evaluation ---
PIECE_VALUES = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 5,
    chess.QUEEN: 9,
    chess.KING: 0 # King value is infinite in reality, but 0 for material calculation
}

class ChessGUI:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Stanford CIP 2025 Chess Game - by Christopher Young")
        
        self.board_pos_x = (WIDTH - BOARD_WIDTH) // 2
        self.board_pos_y = (HEIGHT - BOARD_HEIGHT) // 2

        self.board = chess.Board()
        self.piece_images = self.load_piece_images()
        self.sounds = self.load_sounds()
        
        self.selected_square = None
        self.legal_moves = []
        self.ai_is_thinking = False # --- NEW --- Flag to prevent user moves while AI thinks

        self.font = pygame.font.SysFont("Arial", 48, bold=True)
        self.small_font = pygame.font.SysFont("Arial", 24)

    def load_sounds(self):
        sounds = {}
        sound_files = {"move": "move.wav", "capture": "capture.wav", "check": "check.wav"}
        for name, filename in sound_files.items():
            path = os.path.join("sounds", filename)
            try:
                sounds[name] = pygame.mixer.Sound(path)
            except pygame.error:
                print(f"Error: Could not load sound '{name}' at path '{path}'")
                return None
        return sounds

    def load_piece_images(self):
        images = {}
        pieces = ['P', 'R', 'N', 'B', 'Q', 'K', 'p', 'r', 'n', 'b', 'q', 'k']
        for piece in pieces:
            color = 'w' if piece.isupper() else 'b'
            filename = f"{color}{piece.upper()}.png"
            path = os.path.join("pieces", filename)
            
            try:
                img = pygame.image.load(path).convert_alpha()
                img = pygame.transform.smoothscale(img, (SQUARE_SIZE, SQUARE_SIZE))
                images[piece] = img
            except pygame.error:
                print(f"Error: Could not load image for piece '{piece}' at path '{path}'")
                return None
        return images

    # --- NEW: AI Logic ---
    def evaluate_board(self):
        """
        Evaluates the board based on material count.
        Positive score means White is ahead, negative means Black is ahead.
        """
        score = 0
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece:
                value = PIECE_VALUES[piece.piece_type]
                if piece.color == chess.WHITE:
                    score += value
                else:
                    score -= value
        return score

    def find_best_move(self):
        """
        Finds the best move for the AI player using a simple greedy algorithm.
        """
        best_move = None
        legal_moves = list(self.board.legal_moves)
        random.shuffle(legal_moves) # Introduce randomness for variety

        if self.board.turn == chess.WHITE: # AI is White (Maximizing player)
            max_eval = -float('inf')
            for move in legal_moves:
                self.board.push(move)
                evaluation = self.evaluate_board()
                self.board.pop()
                if evaluation > max_eval:
                    max_eval = evaluation
                    best_move = move
        else: # AI is Black (Minimizing player)
            min_eval = float('inf')
            for move in legal_moves:
                self.board.push(move)
                evaluation = self.evaluate_board()
                self.board.pop()
                if evaluation < min_eval:
                    min_eval = evaluation
                    best_move = move
        
        # If no move improves the situation, pick a random one
        return best_move if best_move is not None else random.choice(legal_moves)


    def make_ai_move(self):
        """
        Calculates and performs the AI's move in a separate thread.
        """
        self.ai_is_thinking = True
        time.sleep(AI_THINK_TIME) # A small delay to feel more natural
        
        move = self.find_best_move()

        if move:
            # Play sound based on the move's outcome
            is_capture = self.board.is_capture(move)
            self.board.push(move)
            if self.board.is_check():
                self.sounds['check'].play()
            elif is_capture:
                self.sounds['capture'].play()
            else:
                self.sounds['move'].play()
        
        self.ai_is_thinking = False

    def draw_board(self):
        for row in range(8):
            for col in range(8):
                color = LIGHT_SQUARE if (row + col) % 2 == 0 else DARK_SQUARE
                pygame.draw.rect(self.screen, color, 
                                 (self.board_pos_x + col * SQUARE_SIZE, 
                                  self.board_pos_y + row * SQUARE_SIZE, 
                                  SQUARE_SIZE, SQUARE_SIZE))

    def draw_pieces(self):
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece:
                row = 7 - (square // 8) 
                col = square % 8
                piece_img = self.piece_images[piece.symbol()]
                x = self.board_pos_x + col * SQUARE_SIZE
                y = self.board_pos_y + row * SQUARE_SIZE
                self.screen.blit(piece_img, (x, y))

    def draw_highlights(self):
        if self.selected_square is not None:
            row = 7 - (self.selected_square // 8)
            col = self.selected_square % 8
            s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            s.fill(SELECTED_COLOR)
            self.screen.blit(s, (self.board_pos_x + col * SQUARE_SIZE, 
                                 self.board_pos_y + row * SQUARE_SIZE))
        
        for move in self.legal_moves:
            dest_square = move.to_square
            row = 7 - (dest_square // 8)
            col = dest_square % 8
            s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            pygame.draw.circle(s, HIGHLIGHT_COLOR, (SQUARE_SIZE//2, SQUARE_SIZE//2), SQUARE_SIZE // 6)
            self.screen.blit(s, (self.board_pos_x + col * SQUARE_SIZE, 
                                 self.board_pos_y + row * SQUARE_SIZE))

    # --- MODIFIED: Handle clicks and trigger AI ---
    def handle_click(self, pos):
        # Do nothing if it's the AI's turn or the game is over
        if self.board.turn == AI_PLAYER or self.board.is_game_over() or self.ai_is_thinking:
            return

        col = (pos[0] - self.board_pos_x) // SQUARE_SIZE
        row = (pos[1] - self.board_pos_y) // SQUARE_SIZE
        
        if not (0 <= col < 8 and 0 <= row < 8):
            self.selected_square = None
            self.legal_moves = []
            return

        square_index = chess.square(col, 7 - row)

        if self.selected_square is not None:
            move = chess.Move(self.selected_square, square_index)
            if self.board.piece_at(self.selected_square).piece_type == chess.PAWN:
                if chess.square_rank(square_index) in [0, 7]:
                    move.promotion = chess.QUEEN

            if move in self.board.legal_moves:
                is_capture = self.board.is_capture(move)
                self.board.push(move)
                
                if self.board.is_check(): self.sounds['check'].play()
                elif is_capture: self.sounds['capture'].play()
                else: self.sounds['move'].play()
                
                self.selected_square = None
                self.legal_moves = []

                # --- NEW: Trigger AI move after human move ---
                if not self.board.is_game_over():
                    ai_thread = threading.Thread(target=self.make_ai_move)
                    ai_thread.start()
            
            elif self.board.piece_at(square_index) and self.board.piece_at(square_index).color == self.board.turn:
                self.selected_square = square_index
                self.legal_moves = [m for m in self.board.legal_moves if m.from_square == square_index]
            else:
                self.selected_square = None
                self.legal_moves = []
        else:
            piece = self.board.piece_at(square_index)
            if piece and piece.color == self.board.turn:
                self.selected_square = square_index
                self.legal_moves = [m for m in self.board.legal_moves if m.from_square == square_index]
    
    def draw_game_over_message(self):
        outcome = self.board.outcome()
        if outcome:
            overlay = pygame.Surface((BOARD_WIDTH, BOARD_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (self.board_pos_x, self.board_pos_y))
            
            winner_text = ""
            if outcome.winner is not None:
                winner = "White" if outcome.winner == chess.WHITE else "Black"
                winner_text = f"{winner} wins by {outcome.termination.name}!"
            else:
                winner_text = f"Draw by {outcome.termination.name}!"
            
            text_surface = self.font.render(winner_text, True, WHITE)
            text_rect = text_surface.get_rect(center=(WIDTH / 2, HEIGHT / 2 - 20))
            self.screen.blit(text_surface, text_rect)
            
            restart_text = "Press 'R' to play again."
            restart_surface = self.small_font.render(restart_text, True, WHITE)
            restart_rect = restart_surface.get_rect(center=(WIDTH / 2, HEIGHT / 2 + 30))
            self.screen.blit(restart_surface, restart_rect)

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_click(pygame.mouse.get_pos())
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r and self.board.is_game_over():
                        self.board.reset()
                        self.selected_square = None
                        self.legal_moves = []
                        self.ai_is_thinking = False

            self.screen.fill(BLACK)
            self.draw_board()
            self.draw_highlights()
            self.draw_pieces()
            
            if self.board.is_game_over():
                self.draw_game_over_message()

            pygame.display.flip()

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = ChessGUI()
    if game.piece_images is None or game.sounds is None:
        print("Failed to load assets. Exiting.")
        sys.exit(1)
    game.run()