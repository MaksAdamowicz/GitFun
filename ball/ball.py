import pygame
import math
import random

# --- Constants ---
WIDTH, HEIGHT = 900, 600
CENTER = (WIDTH // 2, HEIGHT // 2)
FPS = 60
GAME_DURATION = 60  
SPAWN_DISTANCE = 25  
MAX_RADIUS = 500     

# Colors
BLACK = (10, 10, 10)
WHITE = (255, 255, 255)
GRAY = (100, 100, 100)
RED = (255, 50, 50)
GREEN = (50, 255, 50)
NEON_BLUE = (50, 200, 255)

# --- SLIDER CLASS ---
class Slider:
    def __init__(self, x, y, width, min_val, max_val, initial_val, name):
        self.rect = pygame.Rect(x, y, width, 10)
        self.handle_rect = pygame.Rect(x, y - 5, 12, 20)
        self.min_val = min_val
        self.max_val = max_val
        self.val = initial_val
        self.name = name
        self.dragging = False
        self.update_handle_from_val()

    def update_handle_from_val(self):
        ratio = (self.val - self.min_val) / (self.max_val - self.min_val)
        self.handle_rect.centerx = self.rect.x + (self.rect.width * ratio)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.handle_rect.collidepoint(event.pos) or self.rect.collidepoint(event.pos):
                self.dragging = True
                self.update_val_from_mouse(event.pos[0])
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                self.update_val_from_mouse(event.pos[0])

    def update_val_from_mouse(self, mouse_x):
        x = max(self.rect.left, min(mouse_x, self.rect.right))
        self.handle_rect.centerx = x
        ratio = (x - self.rect.left) / self.rect.width
        self.val = self.min_val + (self.max_val - self.min_val) * ratio

    def draw(self, screen, font):
        text_surf = font.render(f"{self.name}: {self.val:.2f}", True, WHITE)
        screen.blit(text_surf, (self.rect.x, self.rect.y - 25))
        pygame.draw.rect(screen, GRAY, self.rect)
        pygame.draw.rect(screen, NEON_BLUE, self.handle_rect)

# --- GAME CLASSES ---
class Ball:
    def __init__(self):
        self.x = CENTER[0]
        self.y = CENTER[1]
        self.vx = 2
        self.vy = 0
        self.radius = 8
        self.color = NEON_BLUE

    def update(self, gravity):
        self.vy += gravity
        self.x += self.vx
        self.y += self.vy

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)

class Ring:
    def __init__(self, radius):
        self.radius = radius
        self.angle = random.uniform(0, math.pi * 2)
        self.gap_width = 1.2 
        self.direction = random.choice([-1, 1])
        self.color = (random.randint(50, 255), random.randint(50, 255), random.randint(200, 255))
        self.thickness = 4

    def update(self, rot_speed, shrink_speed):
        self.angle += self.direction * rot_speed
        self.radius -= shrink_speed
        self.angle = self.angle % (2 * math.pi)

    def draw(self, screen):
        if self.radius > 0:
            rect = pygame.Rect(CENTER[0] - self.radius, CENTER[1] - self.radius, 
                               self.radius * 2, self.radius * 2)
            start_angle = self.angle + (self.gap_width / 2)
            end_angle = self.angle - (self.gap_width / 2) + (2 * math.pi)
            pygame.draw.arc(screen, self.color, rect, start_angle, end_angle, self.thickness)

def run_game():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Tunnel Escape - Smooth Motion")
    clock = pygame.time.Clock()
    
    font = pygame.font.SysFont("Arial", 16)
    ui_font = pygame.font.SysFont("Arial", 20, bold=True)
    large_font = pygame.font.SysFont("Arial", 50, bold=True)

    # --- Sliders ---
    slider_gravity = Slider(20, 50, 150, 0.0, 0.5, 0.15, "Gravity")
    slider_rot = Slider(20, 120, 150, 0.0, 0.1, 0.02, "Spin Speed")
    slider_shrink = Slider(20, 190, 150, 0.0, 2.0, 0.60, "Shrink Speed")
    slider_bounce = Slider(20, 260, 150, 0.5, 1.5, 1.05, "Bounciness") 
    
    sliders = [slider_gravity, slider_rot, slider_shrink, slider_bounce]

    def reset_game():
        b = Ball()
        r = []
        current_r = 200
        while current_r < MAX_RADIUS:
            r.append(Ring(current_r))
            current_r += SPAWN_DISTANCE
        return b, r, pygame.time.get_ticks(), 0

    ball, rings, start_ticks, score = reset_game()
    
    running = True
    game_over = False
    message = ""
    sub_message = ""

    while running:
        screen.fill(BLACK)
        
        current_gravity = slider_gravity.val
        current_rot_speed = slider_rot.val
        current_shrink_speed = slider_shrink.val
        current_bounce = slider_bounce.val 

        seconds_passed = (pygame.time.get_ticks() - start_ticks) / 1000
        time_left = GAME_DURATION - seconds_passed
        
        if time_left <= 0 and not game_over:
            game_over = True
            message = "TIME'S UP!"
            sub_message = f"Final Score: {score}"
            time_left = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            for s in sliders:
                s.handle_event(event)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and game_over:
                    ball, rings, start_ticks, score = reset_game()
                    game_over = False

        if not game_over:
            ball.update(current_gravity)

            for ring in rings:
                ring.update(current_rot_speed, current_shrink_speed)

            # Spawn new rings
            if rings and rings[-1].radius < MAX_RADIUS - SPAWN_DISTANCE:
                rings.append(Ring(MAX_RADIUS))

            if rings:
                current_ring = rings[0]
                
                # --- AUTO POP LOGIC ---
                if current_ring.radius < ball.radius + 5:
                    rings.pop(0)
                    score += 1
                
                elif rings: 
                    current_ring = rings[0] 
                    dist_x = ball.x - CENTER[0]
                    dist_y = ball.y - CENTER[1]
                    distance = math.sqrt(dist_x**2 + dist_y**2)

                    if distance + ball.radius >= current_ring.radius - (current_ring.thickness / 2):
                        ball_angle = math.atan2(-dist_y, dist_x)
                        if ball_angle < 0: ball_angle += 2 * math.pi
                        
                        angle_diff = abs(ball_angle - current_ring.angle)
                        if angle_diff > math.pi: angle_diff = (2 * math.pi) - angle_diff

                        if angle_diff < (current_ring.gap_width / 2):
                            # --- SUCCESS: Escaped through hole ---
                            rings.pop(0) 
                            score += 1
                            # CHANGED: No position or velocity boost here.
                            # The ball simply continues its current path.
                        else:
                            # --- BOUNCE ---
                            overlap = distance + ball.radius - (current_ring.radius - current_ring.thickness/2)
                            ball.x -= (dist_x / distance) * overlap
                            ball.y -= (dist_y / distance) * overlap
                            
                            nx = dist_x / distance
                            ny = dist_y / distance
                            dot = ball.vx * nx + ball.vy * ny
                            
                            ball.vx = (ball.vx - 2 * dot * nx) * current_bounce
                            ball.vy = (ball.vy - 2 * dot * ny) * current_bounce

        for ring in reversed(rings):
            ring.draw(screen)
        
        ball.draw(screen)
        
        for s in sliders:
            s.draw(screen, font)

        timer_text = ui_font.render(f"Time: {int(time_left)}", True, WHITE)
        score_text = ui_font.render(f"Score: {score}", True, GREEN)
        screen.blit(timer_text, (WIDTH - 120, 20))
        screen.blit(score_text, (WIDTH - 120, 50))

        if game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(150)
            overlay.fill(BLACK)
            screen.blit(overlay, (0,0))
            msg_surf = large_font.render(message, True, GREEN)
            sub_surf = ui_font.render(sub_message, True, WHITE)
            restart_surf = ui_font.render("Press SPACE to Restart", True, WHITE)
            screen.blit(msg_surf, msg_surf.get_rect(center=(WIDTH//2, HEIGHT//2 - 30)))
            screen.blit(sub_surf, sub_surf.get_rect(center=(WIDTH//2, HEIGHT//2 + 20)))
            screen.blit(restart_surf, restart_surf.get_rect(center=(WIDTH//2, HEIGHT//2 + 60)))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    run_game()