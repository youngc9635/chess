import pygame
import chess
import sys
import os

# --- Constants ---
# Screen dimensions
WIDTH = 800
HEIGHT = 800

# Board dimensions
BOARD_WIDTH = 640
BOARD_HEIGHT = 640
SQUARE_SIZE = BOARD_WIDTH // 8

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LIGHT_SQUARE = (240, 217, 181)
DARK_SQUARE = (181, 136, 99)
HIGHLIGHT_COLOR = (100, 255, 100, 100) # Green with transparency
SELECTED_COLOR = (255, 255, 0, 150) # Yellow with transparency

class ChessGUI:
    def __init__(self):
        """
        Initializes the Pygame window, loads assets, and sets up the game state.
        """
        pygame.init()
        pygame.mixer.init() # --- NEW --- Initialize the mixer for sound

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Code in Place 5 Chess Game")
        
        self.board_pos_x = (WIDTH - BOARD_WIDTH) // 2
        self.board_pos_y = (HEIGHT - BOARD_HEIGHT) // 2

        self.board = chess.Board()
        self.piece_images = self.load_piece_images()
        self.sounds = self.load_sounds() # --- NEW --- Load sound files
        
        self.selected_square = None
        self.legal_moves = []

        self.font = pygame.font.SysFont("Arial", 48, bold=True)
        self.small_font = pygame.font.SysFont("Arial", 24)

    # --- NEW --- Function to load sounds
    def load_sounds(self):
        """
        Loads sound effects from the 'sounds' directory.
        """
        sounds = {}
        sound_files = {"move": "move.wav", "capture": "capture.wav", "check": "check.wav"}
        for name, filename in sound_files.items():
            path = os.path.join("sounds", filename)
            try:
                sounds[name] = pygame.mixer.Sound(path)
            except pygame.error:
                print(f"Error: Could not load sound '{name}' at path '{path}'")
                print("Make sure you have a 'sounds' folder with correctly named .wav files.")
                sys.exit(1)
        return sounds

    def load_piece_images(self):
        """
        Loads chess piece images from the 'pieces' directory.
        """
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
                print("Make sure you have a 'pieces' folder with correctly named PNG files.")
                sys.exit(1)
        return images

    def draw_board(self):
        """
        Draws the checkerboard pattern.
        """
        for row in range(8):
            for col in range(8):
                color = LIGHT_SQUARE if (row + col) % 2 == 0 else DARK_SQUARE
                pygame.draw.rect(self.screen, color, 
                                 (self.board_pos_x + col * SQUARE_SIZE, 
                                  self.board_pos_y + row * SQUARE_SIZE, 
                                  SQUARE_SIZE, SQUARE_SIZE))

    def draw_pieces(self):
        """
        Draws the pieces on the board based on the current board state.
        """
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
        """
        Highlights the selected square and all legal move destinations.
        """
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
            center_x = self.board_pos_x + col * SQUARE_SIZE + SQUARE_SIZE // 2
            center_y = self.board_pos_y + row * SQUARE_SIZE + SQUARE_SIZE // 2
            s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            pygame.draw.circle(s, HIGHLIGHT_COLOR, (SQUARE_SIZE//2, SQUARE_SIZE//2), SQUARE_SIZE // 6)
            self.screen.blit(s, (self.board_pos_x + col * SQUARE_SIZE, 
                                 self.board_pos_y + row * SQUARE_SIZE))

    # --- MODIFIED --- This function now handles sound playback
    def handle_click(self, pos):
        """
        Handles a mouse click to select a piece, make a move, and play sounds.
        """
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
                if (chess.square_rank(square_index) == 7 and self.board.turn == chess.WHITE) or \
                   (chess.square_rank(square_index) == 0 and self.board.turn == chess.BLACK):
                    move.promotion = chess.QUEEN

            if move in self.board.legal_moves:
                # --- NEW: Sound logic ---
                # Check for capture before making the move
                is_capture = self.board.is_capture(move)
                
                # Make the move
                self.board.push(move)
                
                # Play sound based on the move's outcome
                if self.board.is_check():
                    self.sounds['check'].play()
                elif is_capture:
                    self.sounds['capture'].play()
                else:
                    self.sounds['move'].play()
                
                self.selected_square = None
                self.legal_moves = []
            elif self.board.piece_at(square_index) and \
                 self.board.piece_at(square_index).color == self.board.turn:
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
        """
        Displays a game over message when the game ends.
        """
        outcome = self.board.outcome()
        if outcome:
            overlay = pygame.Surface((BOARD_WIDTH, BOARD_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (self.board_pos_x, self.board_pos_y))
            
            if outcome.winner is not None:
                winner = "White" if outcome.winner == chess.WHITE else "Black"
                text = f"{winner} wins by {outcome.termination.name}!"
            else:
                text = f"Draw by {outcome.termination.name}!"
            
            text_surface = self.font.render(text, True, WHITE)
            text_rect = text_surface.get_rect(center=(WIDTH / 2, HEIGHT / 2 - 20))
            self.screen.blit(text_surface, text_rect)
            
            restart_text = "Press 'R' to play again."
            restart_surface = self.small_font.render(restart_text, True, WHITE)
            restart_rect = restart_surface.get_rect(center=(WIDTH / 2, HEIGHT / 2 + 30))
            self.screen.blit(restart_surface, restart_rect)

    def run(self):
        """
        The main game loop.
        """
        running = True
        game_over = False
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if not game_over:
                        self.handle_click(pygame.mouse.get_pos())
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r and game_over:
                        self.board.reset()
                        self.selected_square = None
                        self.legal_moves = []
                        game_over = False

            # Drawing
            self.screen.fill(BLACK)
            self.draw_board()
            self.draw_highlights()
            self.draw_pieces()
            
            if self.board.is_game_over():
                game_over = True
                self.draw_game_over_message()

            pygame.display.flip()

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = ChessGUI()
    game.run()