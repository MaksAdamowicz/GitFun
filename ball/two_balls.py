import pygame
import math
import random

# --- Constants ---
WIDTH, HEIGHT = 400, 400
FPS = 60
BALL_RADIUS = 50 

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 100, 100)
BLUE = (100, 100, 255)
GREEN = (50, 200, 50)

class Ball:
    def __init__(self, x, y, color, strategy):
        self.x = x
        self.y = y
        self.color = color
        self.radius = BALL_RADIUS
        self.dx = random.choice([-3, -2, 2, 3])
        self.dy = random.choice([-3, -2, 2, 3])
        
        # --- Battle Stats ---
        self.hp = 100000
        self.damage = 1
        self.strategy = strategy # 'fib' or 'double'
        
        # Fibonacci trackers
        self.fib_prev = 0
        self.fib_curr = 1

    def increase_damage(self):
        if self.strategy == 'fib':
            # Sequence: 1, 1, 2, 3, 5, 8...
            new_fib = self.fib_prev + self.fib_curr
            self.fib_prev = self.fib_curr
            self.fib_curr = new_fib
            self.damage = self.fib_curr
        elif self.strategy == 'double':
            # Sequence: 1, 2, 4, 8, 16...
            self.damage *= 2

    def move(self):
        self.x += self.dx
        self.y += self.dy

    def draw(self, screen, font, small_font):
        # Draw Ball
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(screen, BLACK, (int(self.x), int(self.y)), self.radius, 3)

        # Draw Stats Text
        hp_text = font.render(f"{self.hp}", True, BLACK)
        dmg_text = small_font.render(f"Dmg: {self.damage}", True, BLACK)
        
        # Center the text
        screen.blit(hp_text, (self.x - hp_text.get_width() // 2, self.y - 15))
        screen.blit(dmg_text, (self.x - dmg_text.get_width() // 2, self.y + 10))

    def check_wall_collision(self):
        if self.x - self.radius < 0:
            self.x = self.radius 
            self.dx *= -1
        elif self.x + self.radius > WIDTH:
            self.x = WIDTH - self.radius
            self.dx *= -1

        if self.y - self.radius < 0:
            self.y = self.radius
            self.dy *= -1
        elif self.y + self.radius > HEIGHT:
            self.y = HEIGHT - self.radius
            self.dy *= -1

def check_ball_collision(b1, b2):
    dx = b2.x - b1.x
    dy = b2.y - b1.y
    distance = math.hypot(dx, dy)

    # Collision Detected
    if distance < (b1.radius + b2.radius):
        # 1. Resolve Overlap (Move them apart so they don't stick)
        overlap = (b1.radius + b2.radius - distance) / 2
        angle = math.atan2(dy, dx)
        
        b1.x -= overlap * math.cos(angle)
        b1.y -= overlap * math.sin(angle)
        b2.x += overlap * math.cos(angle)
        b2.y += overlap * math.sin(angle)

        # 2. Physics Bounce
        nx = dx / distance
        ny = dy / distance
        tx = -ny
        ty = nx

        dpTan1 = b1.dx * tx + b1.dy * ty
        dpNorm1 = b1.dx * nx + b1.dy * ny
        dpTan2 = b2.dx * tx + b2.dy * ty
        dpNorm2 = b2.dx * nx + b2.dy * ny

        # Assuming equal mass for movement physics
        m = 1 
        pNorm1 = (dpNorm1 * (m - m) + 2 * m * dpNorm2) / (m + m)
        pNorm2 = (dpNorm2 * (m - m) + 2 * m * dpNorm1) / (m + m)

        b1.dx = tx * dpTan1 + nx * pNorm1
        b1.dy = ty * dpTan1 + ny * pNorm1
        b2.dx = tx * dpTan2 + nx * pNorm2
        b2.dy = ty * dpTan2 + ny * pNorm2

        # 3. APPLY DAMAGE & INCREASE POWER
        b1.hp -= b2.damage
        b2.hp -= b1.damage
        
        b1.increase_damage()
        b2.increase_damage()

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Fibonacci vs Doubling Battle")
    clock = pygame.time.Clock()
    
    # Fonts
    font = pygame.font.SysFont("Arial", 24, bold=True)
    small_font = pygame.font.SysFont("Arial", 16)
    game_over_font = pygame.font.SysFont("Arial", 40, bold=True)

    # Create Balls
    # Ball 1 (Red) = Fibonacci
    # Ball 2 (Blue) = Doubling
    ball1 = Ball(100, 200, RED, 'fib')
    ball2 = Ball(300, 200, BLUE, 'double')

    running = True
    game_over = False
    winner_text = ""

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            # Restart on click if game over
            if event.type == pygame.MOUSEBUTTONDOWN and game_over:
                main() 
                return

        if not game_over:
            ball1.move()
            ball2.move()

            ball1.check_wall_collision()
            ball2.check_wall_collision()
            check_ball_collision(ball1, ball2)

            # Check for death
            if ball1.hp <= 0 or ball2.hp <= 0:
                game_over = True
                if ball1.hp > ball2.hp:
                    winner_text = "RED (Fibonacci) WINS!"
                elif ball2.hp > ball1.hp:
                    winner_text = "BLUE (Double) WINS!"
                else:
                    winner_text = "DRAW!"

        # Drawing
        screen.fill(WHITE)
        
        ball1.draw(screen, font, small_font)
        ball2.draw(screen, font, small_font)

        if game_over:
            text_surf = game_over_font.render(winner_text, True, BLACK)
            screen.blit(text_surf, (WIDTH//2 - text_surf.get_width()//2, HEIGHT//2))
            
            sub_text = small_font.render("Click to Restart", True, BLACK)
            screen.blit(sub_text, (WIDTH//2 - sub_text.get_width()//2, HEIGHT//2 + 40))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()