import pygame
import sys
import math
import random

# --- הגדרות בסיסיות וצבעים ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# הגדרות צבעים
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
LASER_COLOR_PLAYER = (0, 255, 255)  # לייזר שחקן
LASER_COLOR_ENEMY = (255, 50, 50)  # לייזר אויב (אדום)
SKIN_COLOR = (255, 204, 153)
WALL_COLOR = (139, 69, 19)
BG_COLOR = (100, 100, 100)

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("The Binding Of Matthew - Final")
clock = pygame.time.Clock()

# --- הגדרת פונט להצגת ניקוד וחיים ---
pygame.font.init()
FONT = pygame.font.SysFont('Arial', 30)


def draw_text(surface, text, x, y, color=WHITE):
    """מצייר טקסט על המסך."""
    text_surface = FONT.render(text, True, color)
    text_rect = text_surface.get_rect(topleft=(x, y))
    surface.blit(text_surface, text_rect)


# מחלקת בסיס: דמויות (Character)

class Character(pygame.sprite.Sprite):
    def __init__(self, size, speed, color):
        super().__init__()
        self.size = size
        self.image = pygame.Surface([self.size + 4, self.size + 4], pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.speed = speed
        self.color = color

    def handle_movement(self, walls, dx, dy):
        """מטפל בתנועה ובדיקת התנגשות עם קירות."""
        new_x, new_y = self.rect.x + dx, self.rect.y + dy
        original_x, original_y = self.rect.x, self.rect.y

        self.rect.x = new_x
        hit_x = pygame.sprite.spritecollideany(self, walls)
        if hit_x:
            self.rect.x = original_x

        self.rect.y = new_y
        hit_y = pygame.sprite.spritecollideany(self, walls)
        if hit_y:
            self.rect.y = original_y

        self.rect.clamp_ip(screen.get_rect())
        return hit_x, hit_y


# מחלקה יורשת: שחקן (Player)

class Player(Character):
    def __init__(self):
        super().__init__(size=50, speed=5, color=SKIN_COLOR)
        self.max_health = 5
        self.health = 5
        self.invulnerable_timer = pygame.time.get_ticks()
        self.invulnerability_cooldown = 1000  # 1 שניה של חסינות

        self.aim_angle = 0
        self.last_shot_time = pygame.time.get_ticks()
        self.shoot_cooldown = 400
        self.draw_head()

    def draw_head(self):
        """מצייר את ראש השחקן (מטפל בהבהוב חסינות)."""
        self.image.fill((0, 0, 0, 0))
        center_x = self.size // 2 + 2
        center_y = self.size // 2 + 2
        radius = self.size // 2

        now = pygame.time.get_ticks()
        is_invulnerable = now - self.invulnerable_timer < self.invulnerability_cooldown

        if not is_invulnerable or (is_invulnerable and now % 200 < 100):
            pygame.draw.circle(self.image, BLACK, (center_x, center_y), radius + 2, 0)
            pygame.draw.circle(self.image, SKIN_COLOR, (center_x, center_y), radius, 0)
            eye_offset = 12
            eye_radius = 8
            pupil_radius = 4
            eye_left_pos = (center_x - eye_offset, center_y - eye_offset)
            pygame.draw.circle(self.image, WHITE, eye_left_pos, eye_radius, 0)
            pygame.draw.circle(self.image, BLACK, eye_left_pos, pupil_radius, 0)
            eye_right_pos = (center_x + eye_offset, center_y - eye_offset)
            pygame.draw.circle(self.image, WHITE, eye_right_pos, eye_radius, 0)
            pygame.draw.circle(self.image, BLACK, eye_right_pos, pupil_radius, 0)
        else:
            self.image.fill((0, 0, 0, 0))

    def update(self, walls):
        self.draw_head()
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        if keys[pygame.K_w]: dy -= self.speed
        if keys[pygame.K_s]: dy += self.speed
        if keys[pygame.K_a]: dx -= self.speed
        if keys[pygame.K_d]: dx += self.speed

        self.handle_movement(walls, dx, dy)

    def shoot(self, all_sprites, lasers, shoot_angle):
        """השחקן יורה לייזר."""
        now = pygame.time.get_ticks()
        if now - self.last_shot_time > self.shoot_cooldown:
            self.last_shot_time = now
            # לייזר של שחקן (player_laser=True)
            laser = Laser(self.rect.centerx, self.rect.centery, shoot_angle, True)
            all_sprites.add(laser)
            lasers.add(laser)

    def take_damage(self):
        """מפחית חיים רק אם השחקן אינו חסין."""
        now = pygame.time.get_ticks()
        if now - self.invulnerable_timer > self.invulnerability_cooldown:
            self.health -= 1
            self.invulnerable_timer = now
            return True  # נפגע
        return False  # חסין


# ----------------------------------------------------
# מחלקה יורשת: אויב (Enemy)
# ----------------------------------------------------

class Enemy(Character):
    def __init__(self, x, y, size, walls):
        super().__init__(size=size, speed=2, color=BLACK)
        self.rect.topleft = (x, y)
        self.walls = walls
        self.direction_timer = pygame.time.get_ticks()
        self.change_interval = 2000
        self.vx = 0
        self.vy = 0

        self.max_health = 3
        self.health = self.max_health

        # תזמון ירי של האויב
        self.last_shot_time = pygame.time.get_ticks()
        self.shoot_interval = random.randint(1500, 3000)

        self.draw_enemy()
        self.change_direction()

    def draw_enemy(self):
        """מצייר את האויב (ריבוע שחור עם עיניים אדומות)."""
        self.image.fill((0, 0, 0, 0))
        pygame.draw.rect(self.image, BLACK, (0, 0, self.size, self.size))
        pygame.draw.rect(self.image, BLACK, (0, 0, self.size, self.size), 2)

        eye_radius = 4
        eye_offset = self.size // 4
        center_x = self.size // 2
        center_y = self.size // 2

        pygame.draw.circle(self.image, RED, (center_x - eye_offset, center_y - eye_offset), eye_radius, 0)
        pygame.draw.circle(self.image, RED, (center_x + eye_offset, center_y - eye_offset), eye_radius, 0)

    def change_direction(self):
        """בוחר כיוון תנועה אקראי חדש."""
        direction_options = [(-1, 0), (1, 0), (0, -1), (0, 1), (0, 0)]
        self.vx, self.vy = random.choice(direction_options)

    def update(self, player_rect, all_sprites, enemy_lasers):
        """מעדכן תנועה וירי לכיוון השחקן."""
        # עדכון תנועה אקראית
        now = pygame.time.get_ticks()
        if now - self.direction_timer > self.change_interval:
            self.direction_timer = now
            self.change_direction()

        dx = self.vx * self.speed
        dy = self.vy * self.speed
        self.handle_movement(self.walls, dx, dy)

        # הפעלת ירי
        self.shoot(player_rect, all_sprites, enemy_lasers)

    def shoot(self, target_rect, all_sprites, enemy_lasers):
        """יורה לייזר לכיוון השחקן."""
        now = pygame.time.get_ticks()

        if now - self.last_shot_time > self.shoot_interval:
            self.last_shot_time = now
            self.shoot_interval = random.randint(1500, 3000)

            # חישוב זווית הירי לכיוון השחקן
            dx = target_rect.centerx - self.rect.centerx
            dy = target_rect.centery - self.rect.centery
            angle_rad = math.atan2(-dy, dx)
            angle = math.degrees(angle_rad)

            # לייזר של אויב (player_laser=False)
            laser = Laser(self.rect.centerx, self.rect.centery, angle, False)
            all_sprites.add(laser)
            enemy_lasers.add(laser)

    def take_damage(self):
        """מפחית חיים ומחזיר True אם האויב הובס."""
        self.health -= 1
        return self.health <= 0


# ----------------------------------------------------
# מחלקת הלייזר (Laser)
# ----------------------------------------------------

class Laser(pygame.sprite.Sprite):
    def __init__(self, x, y, angle, player_laser):
        super().__init__()
        self.speed = 10
        self.player_laser = player_laser

        self.angle_rad = math.radians(angle)
        self.vx = self.speed * math.cos(self.angle_rad)
        self.vy = self.speed * math.sin(self.angle_rad)

        self.image = pygame.Surface([10, 3], pygame.SRCALPHA)
        color = LASER_COLOR_PLAYER if player_laser else LASER_COLOR_ENEMY
        self.image.fill(color)

        self.image = pygame.transform.rotate(self.image, -angle)
        self.rect = self.image.get_rect(center=(x, y))
        self.float_x = float(x)
        self.float_y = float(y)

    def update(self, walls):
        self.float_x += self.vx
        self.float_y -= self.vy
        self.rect.x = int(self.float_x)
        self.rect.y = int(self.float_y)
        if not screen.get_rect().colliderect(self.rect): self.kill()
        if pygame.sprite.spritecollideany(self, walls): self.kill()


# ----------------------------------------------------
# מחלקת בסיס: עצמי מפה (MapObject)
# ----------------------------------------------------

class MapObject(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, color):
        super().__init__()
        self.image = pygame.Surface([width, height])
        self.image.fill(color)
        self.rect = self.image.get_rect(topleft=(x, y))
        pygame.draw.rect(self.image, BLACK, self.image.get_rect(), 2)

    # ----------------------------------------------------


# מחלקה יורשת: קיר (Wall)
# ----------------------------------------------------

class Wall(MapObject):
    pass


# ----------------------------------------------------
# הגדרת המפה והמשחק (Setup Game)
# ----------------------------------------------------

def setup_game():
    all_sprites = pygame.sprite.Group()
    player_lasers = pygame.sprite.Group()
    enemy_lasers = pygame.sprite.Group()
    walls = pygame.sprite.Group()
    enemies = pygame.sprite.Group()

    player = Player()
    all_sprites.add(player)

    # הגדרת המכשולים
    wall_data = [
        (0, 0, SCREEN_WIDTH, 10, WALL_COLOR),
        (0, 0, 10, SCREEN_HEIGHT, WALL_COLOR),
        (SCREEN_WIDTH - 10, 0, 10, SCREEN_HEIGHT, WALL_COLOR),
        (0, SCREEN_HEIGHT - 10, SCREEN_WIDTH, 10, WALL_COLOR),
        (150, 150, 150, 20, WALL_COLOR),
        (500, 300, 20, 150, WALL_COLOR),
        (300, 450, 150, 40, WALL_COLOR),
        (600, 100, 50, 50, WALL_COLOR),
        (100, 400, 100, 20, WALL_COLOR),
    ]
    for x, y, w, h, color in wall_data:
        wall = Wall(x, y, w, h, color)
        walls.add(wall)
        all_sprites.add(wall)

    # הוספת אויבים
    enemy_positions = [(50, 50), (700, 500), (400, 100), (200, 500)]
    enemy_sizes = [30, 40, 25, 35]

    for (x, y), size in zip(enemy_positions, enemy_sizes):
        enemy = Enemy(x, y, size, walls)
        enemies.add(enemy)
        all_sprites.add(enemy)

    return all_sprites, player_lasers, enemy_lasers, walls, player, enemies


# ----------------------------------------------------
# לולאת המשחק הראשית (Game Loop)
# ----------------------------------------------------

def game_loop():
    all_sprites, player_lasers, enemy_lasers, walls, player, enemies = setup_game()
    running = True

    score = 0
    game_over = False

    while running:
        # --- 1. טיפול באירועים ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        if game_over:
            continue

            # --- 2. טיפול בקלט וירי (שחקן) ---
        keys = pygame.key.get_pressed()
        shoot_angle = None

        # לוגיקת ירי שחקן
        if keys[pygame.K_UP] and not keys[pygame.K_LEFT] and not keys[pygame.K_RIGHT]:
            shoot_angle = 90
        elif keys[pygame.K_DOWN] and not keys[pygame.K_LEFT] and not keys[pygame.K_RIGHT]:
            shoot_angle = -90
        elif keys[pygame.K_LEFT] and not keys[pygame.K_UP] and not keys[pygame.K_DOWN]:
            shoot_angle = 180
        elif keys[pygame.K_RIGHT] and not keys[pygame.K_UP] and not keys[pygame.K_DOWN]:
            shoot_angle = 0
        elif keys[pygame.K_UP] and keys[pygame.K_LEFT]:
            shoot_angle = 135
        elif keys[pygame.K_UP] and keys[pygame.K_RIGHT]:
            shoot_angle = 45
        elif keys[pygame.K_DOWN] and keys[pygame.K_LEFT]:
            shoot_angle = -135
        elif keys[pygame.K_DOWN] and keys[pygame.K_RIGHT]:
            shoot_angle = -45

        if shoot_angle is not None:
            player.shoot(all_sprites, player_lasers, shoot_angle)

        # --- 3. עדכון ---
        player.update(walls)
        player_lasers.update(walls)
        enemy_lasers.update(walls)

        # עדכון אויבים (כולל ירי לכיוון השחקן)
        for enemy in enemies:
            enemy.update(player.rect, all_sprites, enemy_lasers)

            # --- 4. בדיקת התנגשויות ---

        # 4.1. לייזר שחקן נגד אויב: (הורדת חיים והסרת האויב כשחיים מגיעים ל-0)
        laser_hits = pygame.sprite.groupcollide(player_lasers, enemies, True, False)
        for laser, hit_enemies in laser_hits.items():
            for enemy in hit_enemies:
                is_defeated = enemy.take_damage()
                if is_defeated:
                    score += 1
                    enemy.kill()

                    # 4.2. לייזר אויב נגד שחקן: (הורדת חיים לשחקן והסרת הלייזר האדום)
        enemy_laser_hits = pygame.sprite.spritecollide(player, enemy_lasers, True)
        if enemy_laser_hits:
            if player.take_damage():
                if player.health <= 0:
                    game_over = True

        # 4.3. התנגשות פיזית שחקן נגד אויב (הורדת חיים לשחקן)
        player_hits = pygame.sprite.spritecollide(player, enemies, False)
        if player_hits:
            if player.take_damage():
                if player.health <= 0:
                    game_over = True

        # --- 5. ציור ---
        screen.fill(BG_COLOR)
        all_sprites.draw(screen)

        # ציור סטטוס
        draw_text(screen, f"Score: {score}", 10, 10, WHITE)
        draw_text(screen, f"Health: {player.health}/{player.max_health}", 10, 40, WHITE)

        if game_over:
            draw_text(screen, "GAME OVER", SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 50, RED)

        pygame.display.flip()

        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    game_loop()