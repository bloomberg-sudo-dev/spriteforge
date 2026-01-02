import pygame
import random
import sys
import os
import time

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 400
FPS = 60
BG_COLOR = (34, 139, 34)  # Forest Green (felt-like)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Set up the display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Dice Forge Simulator")
clock = pygame.time.Clock()

# Assets Path
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")

def load_dice_frames():
    frames = []
    # We rendered --frames which produces frame_00.png, frame_01.png, etc.
    # Frame 0-5 are sides 1-6
    # Frame 6-7 are animation frames
    for i in range(8):
        path = os.path.join(ASSETS_DIR, f"frame_{i:02d}.png")
        if os.path.exists(path):
            img = pygame.image.load(path).convert_alpha()
            frames.append(img)
        else:
            print(f"Warning: Could not find {path}")
    return frames

class Die:
    def __init__(self, x, y, frames):
        self.x = x
        self.y = y
        self.frames = frames
        self.current_side = 1
        self.is_rolling = False
        self.roll_start_time = 0
        self.roll_duration = 0.8  # seconds
        self.animation_index = 0
        self.target_side = 1
        self.image = self.frames[0]
        self.rect = self.image.get_rect(center=(x, y))

    def roll(self):
        if not self.is_rolling:
            self.is_rolling = True
            self.roll_start_time = time.time()
            self.target_side = random.randint(1, 6)

    def update(self):
        if self.is_rolling:
            elapsed = time.time() - self.roll_start_time
            if elapsed < self.roll_duration:
                # Play animation frames (6-7) and random sides
                # Speed up animation as it goes?
                self.animation_index = (self.animation_index + 1) % 10
                if self.animation_index < 2:
                    self.image = self.frames[6 + self.animation_index]
                else:
                    self.image = self.frames[random.randint(0, 5)]
                
                # Jitter position slightly for "rolling" effect
                jitter_x = random.randint(-5, 5)
                jitter_y = random.randint(-5, 5)
                self.rect.center = (self.x + jitter_x, self.y + jitter_y)
            else:
                self.is_rolling = False
                self.current_side = self.target_side
                self.image = self.frames[self.current_side - 1]
                self.rect.center = (self.x, self.y)

    def draw(self, surface):
        surface.blit(self.image, self.rect)

def main():
    dice_frames = load_dice_frames()
    if not dice_frames:
        print("Error: No dice frames found. Please ensure they were rendered correctly.")
        return

    die1 = Die(SCREEN_WIDTH // 3, SCREEN_HEIGHT // 2, dice_frames)
    die2 = Die(2 * SCREEN_WIDTH // 3, SCREEN_HEIGHT // 2, dice_frames)
    
    font = pygame.font.Font(None, 48)
    small_font = pygame.font.Font(None, 24)
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    die1.roll()
                    die2.roll()
            if event.type == pygame.MOUSEBUTTONDOWN:
                die1.roll()
                die2.roll()

        # Update
        die1.update()
        die2.update()

        # Draw
        screen.fill(BG_COLOR)
        
        # Draw some "felt" texture or table border?
        pygame.draw.rect(screen, (20, 100, 20), (10, 10, SCREEN_WIDTH-20, SCREEN_HEIGHT-20), 5)
        
        die1.draw(screen)
        die2.draw(screen)
        
        # Text
        title = font.render("Spriteforge Dice Simulator", True, WHITE)
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 30))
        
        instr = small_font.render("Press SPACE or Click to Roll", True, WHITE)
        screen.blit(instr, (SCREEN_WIDTH // 2 - instr.get_width() // 2, SCREEN_HEIGHT - 40))
        
        if not die1.is_rolling and not die2.is_rolling:
            total = die1.current_side + die2.current_side
            total_text = font.render(f"Total: {total}", True, WHITE)
            screen.blit(total_text, (SCREEN_WIDTH // 2 - total_text.get_width() // 2, SCREEN_HEIGHT // 2 + 80))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()

