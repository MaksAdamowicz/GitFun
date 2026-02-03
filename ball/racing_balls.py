import pygame
import math
import random
import sys

# --- Constants & Configuration ---
WIDTH, HEIGHT = 1000, 700
FPS = 60
TRACK_CENTER = (WIDTH // 2, HEIGHT // 2)
TRACK_RADIUS_X = 400
TRACK_RADIUS_Y = 280
LANE_WIDTH = 30

# Colors
GRASS_COLOR = (30, 160, 30)
TRACK_COLOR = (60, 60, 60)       # Dark Asphalt
CURB_RED = (200, 0, 0)
CURB_WHITE = (255, 255, 255)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BUTTON_COLOR = (100, 100, 200)
BUTTON_HOVER_COLOR = (150, 150, 250)

RACER_CONFIG = [
    {"color": (255, 0, 0), "name": "Red"},
    {"color": (255, 140, 0), "name": "Orange"},
    {"color": (255, 255, 0), "name": "Yellow"},
    {"color": (0, 255, 255), "name": "Cyan"},
    {"color": (0, 0, 255), "name": "Blue"},
    {"color": (160, 32, 240), "name": "Purple"},
]

# --- Classes ---

class Button:
    def __init__(self, x, y, w, h, color, text, text_color=BLACK):
        self.rect = pygame.Rect(x, y, w, h)
        self.base_color = color
        self.text = text
        self.text_color = text_color
        self.font = pygame.font.SysFont("Arial", 20, bold=True)
        self.clicked = False

    def draw(self, screen):
        # Check hover for visual effect
        mouse_pos = pygame.mouse.get_pos()
        draw_color = self.base_color
        
        if self.rect.collidepoint(mouse_pos):
            # Lighten the color slightly if hovered
            r = min(self.base_color[0] + 30, 255)
            g = min(self.base_color[1] + 30, 255)
            b = min(self.base_color[2] + 30, 255)
            draw_color = (r, g, b)

        pygame.draw.rect(screen, draw_color, self.rect, border_radius=8)
        pygame.draw.rect(screen, WHITE, self.rect, 2, border_radius=8) # Border

        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    def is_clicked(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False

class Racer:
    def __init__(self, config, lane_index, total_laps):
        self.color = config["color"]
        self.name = config["name"]
        self.lane_index = lane_index
        self.total_laps = total_laps
        
        # Physics
        self.angle = 90  # Start at bottom (90 degrees)
        self.speed = 0
        self.laps_completed = 0
        self.finished = False
        
        # Determine Radius based on lane
        base_offset = 20 
        self.radius_x = TRACK_RADIUS_X - base_offset - (lane_index * LANE_WIDTH)
        self.radius_y = TRACK_RADIUS_Y - base_offset - (lane_index * LANE_WIDTH)

    def update(self):
        if self.finished:
            return

        # Physics: Acceleration and max speed
        acceleration = random.uniform(-0.05, 0.08)
        self.speed += acceleration
        self.speed = max(0.5, min(self.speed, 2.5)) # Speed limits
        
        self.angle += self.speed

        # Check for lap completion (360 degrees)
        # We start at 90, so a lap is 90 + 360
        if self.angle >= 90 + 360:
            self.angle -= 360
            self.laps_completed += 1
            if self.laps_completed >= self.total_laps:
                self.finished = True

    def draw(self, screen):
        rad = math.radians(self.angle)
        
        # Ellipse parametric equation
        x = TRACK_CENTER[0] + self.radius_x * math.cos(rad)
        y = TRACK_CENTER[1] + self.radius_y * math.sin(rad)
        
        # Draw Ball
        pygame.draw.circle(screen, self.color, (int(x), int(y)), 12)
        pygame.draw.circle(screen, WHITE, (int(x - 3), int(y - 3)), 4) # Shine
        pygame.draw.circle(screen, BLACK, (int(x), int(y)), 12, 1) # Outline

# --- Helper Functions ---

def draw_track_background(screen):
    screen.fill(GRASS_COLOR)
    
    # 1. Outer Curb (Red/White)
    outer_rect = (TRACK_CENTER[0] - TRACK_RADIUS_X, TRACK_CENTER[1] - TRACK_RADIUS_Y, 
                  TRACK_RADIUS_X * 2, TRACK_RADIUS_Y * 2)
    pygame.draw.ellipse(screen, CURB_RED, outer_rect)
    pygame.draw.ellipse(screen, WHITE, outer_rect, 5)

    # 2. Asphalt
    asphalt_rx = TRACK_RADIUS_X - 10
    asphalt_ry = TRACK_RADIUS_Y - 10
    pygame.draw.ellipse(screen, TRACK_COLOR, 
                        (TRACK_CENTER[0] - asphalt_rx, TRACK_CENTER[1] - asphalt_ry,
                         asphalt_rx * 2, asphalt_ry * 2))

    # 3. Inner Grass (The hole in the donut)
    inner_rx = TRACK_RADIUS_X - (len(RACER_CONFIG) * LANE_WIDTH) - 40
    inner_ry = TRACK_RADIUS_Y - (len(RACER_CONFIG) * LANE_WIDTH) - 40
    
    pygame.draw.ellipse(screen, CURB_RED, 
                        (TRACK_CENTER[0] - inner_rx - 10, TRACK_CENTER[1] - inner_ry - 10,
                         (inner_rx + 10) * 2, (inner_ry + 10) * 2))
    
    pygame.draw.ellipse(screen, GRASS_COLOR, 
                        (TRACK_CENTER[0] - inner_rx, TRACK_CENTER[1] - inner_ry,
                         inner_rx * 2, inner_ry * 2))

    # 4. Finish Line (Checkered Pattern at bottom)
    start_y = TRACK_CENTER[1] + inner_ry
    end_y = TRACK_CENTER[1] + asphalt_ry
    check_size = 10
    for y in range(int(start_y), int(end_y), check_size):
        for i, x_off in enumerate([-check_size, 0]):
            color = WHITE if (y // check_size) % 2 == i else BLACK
            pygame.draw.rect(screen, color, (TRACK_CENTER[0] + x_off, y, check_size, check_size))

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Ultimate Python Racing")
    clock = pygame.time.Clock()
    
    # Fonts
    title_font = pygame.font.SysFont("Impact", 50)
    msg_font = pygame.font.SysFont("Arial", 30, bold=True)
    lap_font = pygame.font.SysFont("Arial", 40, bold=True)

    # --- Setup UI Elements ---
    
    # Racer Buttons
    racer_buttons = []
    btn_w, btn_h = 100, 50
    start_x = (WIDTH - (len(RACER_CONFIG) * (btn_w + 10))) // 2
    for i, data in enumerate(RACER_CONFIG):
        btn = Button(start_x + i * (btn_w + 10), HEIGHT - 100, btn_w, btn_h, data["color"], data["name"])
        racer_buttons.append(btn)

    # Lap Control Buttons
    btn_minus = Button(WIDTH//2 - 100, HEIGHT//2 + 20, 50, 50, BUTTON_COLOR, "-", WHITE)
    btn_plus = Button(WIDTH//2 + 50, HEIGHT//2 + 20, 50, 50, BUTTON_COLOR, "+", WHITE)

    # Game Loop Variables
    state = "BETTING"
    user_bet = None
    winner = None
    racers = []
    
    # Default Laps
    current_laps_setting = 3 

    running = True
    while running:
        # Event Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if state == "BETTING":
                # Handle Lap Changer
                if btn_minus.is_clicked(event):
                    if current_laps_setting > 1:
                        current_laps_setting -= 1
                if btn_plus.is_clicked(event):
                    if current_laps_setting < 20: # Max 20 laps
                        current_laps_setting += 1

                # Handle Racer Selection
                for btn in racer_buttons:
                    if btn.is_clicked(event):
                        user_bet = btn.text
                        # Start Race with selected laps
                        racers = [Racer(data, i, current_laps_setting) for i, data in enumerate(RACER_CONFIG)]
                        state = "RACING"
            
            if state == "GAMEOVER":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    state = "BETTING"
                    user_bet = None
                    winner = None

        # --- Drawing ---
        draw_track_background(screen)

        if state == "BETTING":
            # Semi-transparent overlay
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0, 0))

            # Title
            title = title_font.render("RACE SETTINGS", True, WHITE)
            screen.blit(title, title.get_rect(center=(WIDTH//2, HEIGHT//2 - 120)))

            # Lap Counter UI
            lap_text = lap_font.render(f"LAPS: {current_laps_setting}", True, WHITE)
            screen.blit(lap_text, lap_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 45)))
            
            btn_minus.draw(screen)
            btn_plus.draw(screen)

            # "Choose your racer" text
            sub = msg_font.render("Choose a racer to start:", True, (200, 200, 200))
            screen.blit(sub, sub.get_rect(center=(WIDTH//2, HEIGHT - 160)))

            # Racer Buttons
            for btn in racer_buttons:
                btn.draw(screen)

        elif state == "RACING":
            finished_count = 0
            leader_laps = 0
            
            for r in racers:
                r.update()
                r.draw(screen)
                if r.finished:
                    finished_count += 1
                    if winner is None:
                        winner = r.name
                
                # Track the leader's lap for UI
                if r.laps_completed > leader_laps:
                    leader_laps = r.laps_completed

            # HUD (Heads Up Display)
            bet_text = msg_font.render(f"Bet: {user_bet}", True, WHITE)
            screen.blit(bet_text, (20, 20))
            
            # Show Lap Progress (capped at max laps)
            display_lap = min(leader_laps + 1, current_laps_setting)
            lap_info = msg_font.render(f"Lap: {display_lap} / {current_laps_setting}", True, WHITE)
            screen.blit(lap_info, (WIDTH - 200, 20))

            if finished_count == len(racers):
                state = "GAMEOVER"

        elif state == "GAMEOVER":
            for r in racers:
                r.draw(screen)

            # Results Box
            panel_rect = pygame.Rect(WIDTH//2 - 200, HEIGHT//2 - 100, 400, 200)
            pygame.draw.rect(screen, BLACK, panel_rect, border_radius=15)
            pygame.draw.rect(screen, WHITE, panel_rect, 4, border_radius=15)

            if user_bet == winner:
                res_color = (0, 255, 0)
                res_msg = "YOU WON!"
            else:
                res_color = (255, 50, 50)
                res_msg = "YOU LOST..."

            win_text = title_font.render(f"Winner: {winner}", True, WHITE)
            res_text = title_font.render(res_msg, True, res_color)
            retry_text = msg_font.render("Click to Race Again", True, (200, 200, 200))

            screen.blit(win_text, win_text.get_rect(center=(WIDTH//2, HEIGHT//2 - 40)))
            screen.blit(res_text, res_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 20)))
            screen.blit(retry_text, retry_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 70)))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()