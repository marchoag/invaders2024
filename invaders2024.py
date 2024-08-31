import pygame
import random
import time
import math
import json
import os

# Initialize Pygame
pygame.init()

# Set up the display
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Invaders Deluxe")

# Colors
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
BRIGHT_YELLOW = (255, 255, 100)
BRIGHT_ORANGE = (255, 200, 0)
BRIGHT_RED = (255, 100, 100)
NEON_PINK = (255, 20, 147)
NEON_CYAN = (0, 255, 255)

# Player
player_width, player_height = 40, 30
player_x = WIDTH // 2 - player_width // 2
player_y = HEIGHT - player_height - 10
player_speed = 5
lives = 3
respawn_time = 2
respawn_delay = 1
respawn_start = 0
is_respawning = False

# Bullets
bullets = []
bullet_speed = 10
bullet_width, bullet_height = 4, 18
bullet_trail_length = 25
last_shot_time = 0
shot_delay = 0.25

# Enemies
enemies = []
base_enemy_types = [
    {"width": 40, "height": 30, "shape": "invader_1"},
    {"width": 45, "height": 35, "shape": "invader_2"},
    {"width": 42, "height": 32, "shape": "invader_3"},
    {"width": 38, "height": 28, "shape": "invader_4"},
    {"width": 44, "height": 34, "shape": "invader_5"}
]

# Function to generate random colors
def random_color():
    return (random.randint(100, 255), random.randint(100, 255), random.randint(100, 255))

# Function to randomize enemy types
def randomize_enemy_types():
    return [{"width": et["width"], "height": et["height"], "color": random_color(), "shape": et["shape"]} 
            for et in base_enemy_types]

# Initialize enemy_types
enemy_types = randomize_enemy_types()

# Explosions
explosions = []
explosion_duration = 1.5
max_particles = 500

# Starfield
stars = []
for _ in range(200):
    stars.append([random.randint(0, WIDTH), random.randint(0, HEIGHT), random.random() * 3 + 1, random.choice([WHITE, (200, 200, 255), (255, 200, 200)])])

# Game state
running = True
clock = pygame.time.Clock()
game_over = False

# Screen flash
screen_flash = 0
screen_flash_duration = 10

# Progress bar
progress = 0
progress_bar_width = 200
progress_bar_height = 20
progress_speed = 0.5  # 5x faster for testing

# Muzzle flash
muzzle_flash_duration = 5
muzzle_flash_timer = 0

# Add new colors for ships
DARK_RED = (139, 0, 0)
DARK_BLUE = (0, 0, 139)
DARK_PURPLE = (75, 0, 130)

# Add variables for victory celebration
victory = False
victory_time = 0
fireworks = []

# Add timer
start_time = time.time()

# Add these variables for exploding ship fragments
ship_fragments = []

# Add these variables at the top of your script
victory_delay = 3  # 3 seconds delay before showing initials entry
victory_delay_start = 0

# Modify these variables at the top of your script
progress = 0
progress_per_enemy = 2  # Adjust this value to control how much progress is gained per enemy destroyed

# Add this to the top of your script
FRAGMENT_LIFETIME = 1.0  # 1 second lifetime for fragments

# Add this variable at the top of your script
game_state = "playing"  # Can be "playing", "victory", "game_over", or "restart"

def draw_ship(x, y, width, height, color, shape):
    if shape == "invader_1":
        points = [(x, y + height // 2), (x + width // 2, y), (x + width, y + height // 2),
                  (x + width * 3 // 4, y + height), (x + width // 4, y + height)]
    elif shape == "invader_2":
        points = [(x, y), (x + width, y), (x + width * 3 // 4, y + height // 2),
                  (x + width, y + height), (x, y + height), (x + width // 4, y + height // 2)]
    elif shape == "invader_3":
        points = [(x + width // 2, y), (x + width, y + height // 3), (x + width * 3 // 4, y + height),
                  (x + width // 4, y + height), (x, y + height // 3)]
    elif shape == "invader_4":
        points = [(x, y + height // 2), (x + width // 2, y), (x + width, y + height // 2),
                  (x + width, y + height), (x, y + height)]
    elif shape == "invader_5":
        points = [(x, y), (x + width, y), (x + width, y + height), (x, y + height)]
    
    pygame.draw.polygon(screen, color, points)
    return points  # Return the points

def draw_player(x, y, show_muzzle_flash=False):
    pygame.draw.rect(screen, GREEN, (x, y + player_height // 2, player_width, player_height // 2))
    pygame.draw.rect(screen, GREEN, (x + player_width // 2 - 5, y, 10, player_height))
    
    if show_muzzle_flash and muzzle_flash_timer > 0:
        flash_radius = 10 + 5 * math.sin(time.time() * 10)  # Pulsating effect
        pygame.draw.circle(screen, BRIGHT_YELLOW, (x + player_width // 2, y), int(flash_radius))

def create_enemy():
    enemy_type = random.choice(enemy_types)
    return {
        "x": random.randint(0, WIDTH - enemy_type["width"]),
        "y": random.randint(-50, -10),
        "type": enemy_type,
        "speed": random.uniform(0.5, 2)
    }

def create_explosion(x, y):
    return {
        "x": x, "y": y,
        "particles": [(random.uniform(-3, 3), random.uniform(-3, 3), random.uniform(1, 3)) for _ in range(150)],
        "start_time": time.time(),
        "color": random.choice([BRIGHT_RED, BRIGHT_ORANGE, BRIGHT_YELLOW, NEON_PINK, NEON_CYAN])
    }

def draw_bullet(x, y, bullet_type):
    if bullet_type == "player":
        core_color = WHITE
        glow_color = GREEN
    else:  # enemy bullet
        core_color = WHITE
        glow_color = RED

    # Draw motion blur
    for i in range(bullet_trail_length):
        alpha = 150 - i * (150 // bullet_trail_length)
        width = bullet_width + i // 3
        height = bullet_height - i // 3
        s = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.rect(s, (*glow_color, alpha), (0, 0, width, height))
        screen.blit(s, (x - i // 6, y + i * 2))

    # Draw bullet core
    pygame.draw.rect(screen, core_color, (x, y, bullet_width, bullet_height))
    
    # Draw neon glow
    glow_surf = pygame.Surface((bullet_width + 4, bullet_height + 4), pygame.SRCALPHA)
    pygame.draw.rect(glow_surf, (*glow_color, 150), (0, 0, bullet_width + 4, bullet_height + 4))
    screen.blit(glow_surf, (x - 2, y - 2))

def draw_explosion(explosion):
    progress = (time.time() - explosion["start_time"]) / explosion_duration
    if progress > 1:
        return True
    
    for dx, dy, size in explosion["particles"]:
        x = explosion["x"] + dx * progress * 100
        y = explosion["y"] + dy * progress * 100
        current_size = size * (1 - progress)
        alpha = int(255 * (1 - progress))
        color = (*explosion["color"], alpha)
        
        pygame.draw.circle(screen, color, (int(x), int(y)), int(current_size))
    
    return False

def create_firework(x, y):
    return {
        "x": x,
        "y": y,
        "particles": [(random.uniform(-1, 1), random.uniform(-1, 1)) for _ in range(100)],
        "color": random.choice([RED, GREEN, BLUE, YELLOW, ORANGE, NEON_PINK, NEON_CYAN]),
        "start_time": time.time()
    }

def draw_firework(firework):
    progress = (time.time() - firework["start_time"]) / 1.5
    if progress > 1:
        return True
    for dx, dy in firework["particles"]:
        x = firework["x"] + dx * progress * 100
        y = firework["y"] + dy * progress * 100 + 50 * progress ** 2  # Add gravity effect
        size = 3 * (1 - progress)
        pygame.draw.circle(screen, firework["color"], (int(x), int(y)), int(size))
    return False

def create_ship_fragments(x, y, width, height, color, shape):
    fragments = []
    points = draw_ship(x, y, width, height, color, shape)
    for i in range(len(points) - 2):
        fragment = {
            "points": [points[0], points[i+1], points[i+2]],
            "velocity": [random.uniform(-2, 2), random.uniform(-2, 2)],
            "rotation": random.uniform(-0.1, 0.1),
            "color": color,
            "start_time": time.time()
        }
        fragments.append(fragment)
    return fragments

def update_and_draw_fragments():
    current_time = time.time()
    for fragment in ship_fragments[:]:
        age = current_time - fragment["start_time"]
        if age > FRAGMENT_LIFETIME:
            ship_fragments.remove(fragment)
            continue
        
        alpha = int(255 * (1 - age / FRAGMENT_LIFETIME))
        color = (*fragment["color"][:3], alpha)
        
        for i, point in enumerate(fragment["points"]):
            fragment["points"][i] = (point[0] + fragment["velocity"][0], point[1] + fragment["velocity"][1])
        
        center = sum([p[0] for p in fragment["points"]]) / 3, sum([p[1] for p in fragment["points"]]) / 3
        rotated_points = []
        for point in fragment["points"]:
            x, y = point[0] - center[0], point[1] - center[1]
            x_rot = x * math.cos(fragment["rotation"]) - y * math.sin(fragment["rotation"])
            y_rot = x * math.sin(fragment["rotation"]) + y * math.cos(fragment["rotation"])
            rotated_points.append((x_rot + center[0], y_rot + center[1]))
        
        pygame.draw.polygon(screen, color, rotated_points)

# Create initial enemies
for _ in range(10):
    enemies.append(create_enemy())

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if game_state == "playing":
                # ... (rest of the key handling for playing state)
                pass  # Add this line if there's no code here yet
            elif game_state in ["game_over", "victory"]:
                if event.key == pygame.K_RETURN:
                    # Reset game state
                    enemies = [create_enemy() for _ in range(10)]
                    bullets = []
                    explosions = []
                    ship_fragments = []
                    lives = 3
                    game_over = False
                    victory = False
                    player_x = WIDTH // 2 - player_width // 2
                    player_y = HEIGHT - player_height - 10
                    progress = 0
                    start_time = time.time()
                    enemy_types = randomize_enemy_types()
                    game_state = "playing"
                    victory_time = 0

    if game_state == "playing":
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and player_x > 0:
            player_x -= player_speed
        if keys[pygame.K_RIGHT] and player_x < WIDTH - player_width:
            player_x += player_speed

        current_time = time.time()
        if keys[pygame.K_SPACE] and current_time - last_shot_time > shot_delay:
            bullets.append([player_x + player_width // 2 - bullet_width // 2, player_y, "player"])
            last_shot_time = current_time
            screen_flash = screen_flash_duration
            muzzle_flash_timer = muzzle_flash_duration

        # Increase enemy speed based on progress
        enemy_speed_multiplier = 1 + (progress / 100)

        for enemy in enemies[:]:
            enemy["y"] += enemy["speed"] * enemy_speed_multiplier
            if enemy["y"] > HEIGHT:
                enemies.remove(enemy)
                enemies.append(create_enemy())

            # Enemy shooting (in the last 25% of progress)
            if progress > 75 and random.random() < 0.02:
                enemy_bullet = [enemy["x"] + enemy["type"]["width"] // 2, enemy["y"] + enemy["type"]["height"], "enemy"]
                bullets.append(enemy_bullet)

        for bullet in bullets[:]:
            if bullet[2] == "player":
                bullet[1] -= bullet_speed
            else:
                bullet[1] += bullet_speed
            if bullet[1] < 0 or bullet[1] > HEIGHT:
                bullets.remove(bullet)

        for enemy in enemies[:]:
            enemy_rect = pygame.Rect(enemy["x"], enemy["y"], enemy["type"]["width"], enemy["type"]["height"])
            
            for bullet in bullets[:]:
                if bullet[2] == "player" and enemy_rect.collidepoint(bullet[0], bullet[1]):
                    enemies.remove(enemy)
                    bullets.remove(bullet)
                    explosions.append(create_explosion(enemy["x"] + enemy["type"]["width"] // 2, enemy["y"] + enemy["type"]["height"] // 2))
                    ship_fragments.extend(create_ship_fragments(enemy["x"], enemy["y"], enemy["type"]["width"], enemy["type"]["height"], enemy["type"]["color"], enemy["type"]["shape"]))
                    enemies.append(create_enemy())
                    # Update progress when an enemy is destroyed
                    progress += progress_per_enemy * (1 + progress / 100)  # Increase faster as progress grows
                    progress = min(progress, 100)
                    break
            
            if not is_respawning:
                player_rect = pygame.Rect(player_x, player_y, player_width, player_height)
                if enemy_rect.colliderect(player_rect) or any(b[2] == "enemy" and player_rect.collidepoint(b[0], b[1]) for b in bullets):
                    lives -= 1
                    explosions.append(create_explosion(player_x + player_width // 2, player_y + player_height // 2))
                    if lives <= 0:
                        game_over = True
                        game_state = "game_over"
                    else:
                        is_respawning = True
                        respawn_start = time.time()
                    if enemy_rect.colliderect(player_rect):
                        enemies.remove(enemy)

        if is_respawning and time.time() - respawn_start > respawn_time + respawn_delay:
            is_respawning = False

        # Check for victory
        if progress >= 100:
            victory = True
            victory_time = time.time() - start_time
            victory_delay_start = time.time()
            game_state = "victory"

    screen.fill((0, 0, 0))

    # Draw screen flash
    if screen_flash > 0:
        flash_surface = pygame.Surface((WIDTH, HEIGHT))
        flash_surface.fill((50, 255, 50))
        flash_surface.set_alpha(screen_flash * 5)
        screen.blit(flash_surface, (0, 0))
        screen_flash -= 1

    for star in stars:
        pygame.draw.circle(screen, star[3], (int(star[0]), int(star[1])), int(star[2]))
        star[1] += star[2] * 0.2
        if star[1] > HEIGHT:
            star[1] = 0
            star[0] = random.randint(0, WIDTH)

    if not game_over and not is_respawning:
        draw_player(player_x, player_y, True)  # Show muzzle flash for main player
    
    for bullet in bullets:
        draw_bullet(bullet[0], bullet[1], bullet[2])
    
    for enemy in enemies:
        draw_ship(enemy["x"], enemy["y"], enemy["type"]["width"], enemy["type"]["height"], enemy["type"]["color"], enemy["type"]["shape"])

    for explosion in explosions[:]:
        if draw_explosion(explosion):
            explosions.remove(explosion)

    update_and_draw_fragments()

    # Draw progress bar and timer
    pygame.draw.rect(screen, WHITE, (WIDTH - progress_bar_width - 10, 10, progress_bar_width, progress_bar_height), 2)
    pygame.draw.rect(screen, GREEN, (WIDTH - progress_bar_width - 10, 10, progress_bar_width * progress / 100, progress_bar_height))
    
    font = pygame.font.Font(None, 24)
    time_text = font.render(f"Time: {time.time() - start_time:.2f}" if game_state == "playing" else f"Final Time: {victory_time:.2f}", True, WHITE)
    screen.blit(time_text, (WIDTH - progress_bar_width - 10, 40))
    
    victory_text = font.render("Victory!", True, WHITE)
    screen.blit(victory_text, (WIDTH - victory_text.get_width() - 10, 10))

    for i in range(lives):
        draw_player(10 + i * (player_width + 5), 10, False)  # Don't show muzzle flash for life indicators

    if game_state == "victory":
        for fw in fireworks[:]:
            if draw_firework(fw):
                fireworks.remove(fw)

        font = pygame.font.Font(None, 74)
        text = font.render("YOU WON!", True, WHITE)
        screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - text.get_height() // 2))

        font = pygame.font.Font(None, 36)
        text = font.render(f"Time: {victory_time:.2f} seconds", True, WHITE)
        screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 + 50))

        font = pygame.font.Font(None, 36)
        text = font.render("Press ENTER to play again", True, WHITE)
        screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 + 100))

    if game_state == "game_over":
        font = pygame.font.Font(None, 74)
        text = font.render("Game Over", True, WHITE)
        screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - text.get_height() // 2))
        
        font = pygame.font.Font(None, 36)
        text = font.render("Press ENTER to restart", True, WHITE)
        screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 + 50))

    if muzzle_flash_timer > 0:
        muzzle_flash_timer -= 1

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
