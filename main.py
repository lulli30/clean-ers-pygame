import pygame
import random
import os
import cv2
import time
import sys

class Particle:
    def __init__(self, x, y, color, lifetime=500):
        self.x = x
        self.y = y
        self.radius = random.randint(4, 8)
        self.color = color
        self.lifetime = lifetime
        self.spawn_time = pygame.time.get_ticks()
        self.vel_x = random.uniform(-2, 2)
        self.vel_y = random.uniform(-2, 2)

    def update(self):
        self.x += self.vel_x
        self.y += self.vel_y
        self.radius = max(0, self.radius - 0.2)

    def draw(self, screen, scale_factor):
        if self.radius > 0:
            pygame.draw.circle(screen, self.color, 
                               (int(self.x * scale_factor[0]), int(self.y * scale_factor[1])), 
                               int(self.radius * min(scale_factor)))

    def is_alive(self):
        return pygame.time.get_ticks() - self.spawn_time < self.lifetime

class Game:
    BASE_WIDTH, BASE_HEIGHT = 1600, 900
    PLAYER_SIZE = 180
    PICKUP_SIZE = 130
    FLASH_DURATION = 100
    ANIMATION_DELAY = 100
    BOOST_DURATION = 3000
    DEFAULT_SPEED = 4
    BOOSTED_SPEED = 8
    
    def __init__(self):
        pygame.init()
        pygame.mixer.init()

        self.WIDTH, self.HEIGHT = self.BASE_WIDTH, self.BASE_HEIGHT
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("CLEAN Ers")
        self.clock = pygame.time.Clock()

        self.scale_x = 1.0
        self.scale_y = 1.0

        self.game_running = False
        self.score = 0
        self.start_time = None
        self.end_time = None
        self.elapsed_time = 0

        self.player_pos = pygame.Rect(100, 100, self.PLAYER_SIZE, self.PLAYER_SIZE)
        self.player_speed = self.DEFAULT_SPEED
        self.animation_index = 1
        self.animation_timer = 0

        self.power_up_active = False
        self.power_up_timer = 0

        self.particles = []
        self.flash_alpha = 0
        self.flash_start_time = None

        self.exit_button_rect = pygame.Rect(600, 677, 390, 80)
        self.start_button_rect = pygame.Rect(590, 520, 400, 100)
        self.default_cursor = pygame.SYSTEM_CURSOR_ARROW
        self.hand_cursor = pygame.SYSTEM_CURSOR_HAND

        self.try_again_offsets = {
            'x1': 176,
            'y1': 555,
            'x2': 484,
            'y2': 635 
        }

        self.load_assets()
        self.init_game_elements()
    
    def load_assets(self):
        self.ASSETS_PATH = "assets"

        self.original_menu_img = pygame.image.load(os.path.join(self.ASSETS_PATH, "menu.png"))
        self.original_map_img = pygame.image.load(os.path.join(self.ASSETS_PATH, "map.png"))
        self.original_score_board_img = pygame.image.load(os.path.join(self.ASSETS_PATH, "score_board.png"))

        self.menu_img = pygame.transform.scale(self.original_menu_img, (self.WIDTH, self.HEIGHT))
        self.map_img = pygame.transform.scale(self.original_map_img, (self.WIDTH, self.HEIGHT))

        orig_sb_width = self.original_score_board_img.get_width()
        orig_sb_height = self.original_score_board_img.get_height()
        sb_aspect_ratio = orig_sb_width / orig_sb_height

        scaled_sb_height = int(self.HEIGHT * 0.7) 
        scaled_sb_width = int(scaled_sb_height * sb_aspect_ratio)
        
        self.score_board_img = pygame.transform.scale(
            self.original_score_board_img, 
            (scaled_sb_width, scaled_sb_height)
        )

        font_path = os.path.join('assets', 'fonts', 'PressStart2P-Regular.ttf')
        self.font = pygame.font.Font(font_path, 50)
        self.small_font = pygame.font.Font(font_path, 24)

        self.broom_sweep_sound = pygame.mixer.Sound(os.path.join(self.ASSETS_PATH, "sound effects", "broom_sweep.mp3"))
        self.pickup_sound = pygame.mixer.Sound(os.path.join(self.ASSETS_PATH, "sound effects", "pick-up.mp3"))

        self.original_student_walk_frames = [
            pygame.image.load(os.path.join(self.ASSETS_PATH, "student", f"walk{i}.png"))
            for i in range(1, 4)
        ]

        self.student_walk_frames = [
            pygame.transform.scale(frame, (int(self.PLAYER_SIZE * self.scale_x), int(self.PLAYER_SIZE * self.scale_y)))
            for frame in self.original_student_walk_frames
        ]

        self.original_shawarma_img = pygame.image.load(os.path.join(self.ASSETS_PATH, "powerups", "shawarma.png"))
        self.original_lemon_img = pygame.image.load(os.path.join(self.ASSETS_PATH, "powerups", "lemon.png"))

        self.shawarma_img = pygame.transform.scale(
            self.original_shawarma_img, 
            (int(self.PICKUP_SIZE * self.scale_x), int(self.PICKUP_SIZE * self.scale_y))
        )
        self.lemon_img = pygame.transform.scale(
            self.original_lemon_img, 
            (int(self.PICKUP_SIZE * self.scale_x), int(self.PICKUP_SIZE * self.scale_y))
        )

        self.original_trash_imgs = [
            pygame.image.load(os.path.join(self.ASSETS_PATH, "trash", f"trash{i}.png"))
            for i in range(1, 5)
        ]

        self.trash_imgs = [
            pygame.transform.scale(img, (int(self.PICKUP_SIZE * self.scale_x), int(self.PICKUP_SIZE * self.scale_y)))
            for img in self.original_trash_imgs
        ]
    
    def rescale_assets(self):
        self.scale_x = self.WIDTH / self.BASE_WIDTH
        self.scale_y = self.HEIGHT / self.BASE_HEIGHT

        self.menu_img = pygame.transform.scale(self.original_menu_img, (self.WIDTH, self.HEIGHT))
        self.map_img = pygame.transform.scale(self.original_map_img, (self.WIDTH, self.HEIGHT))

        orig_sb_width = self.original_score_board_img.get_width()
        orig_sb_height = self.original_score_board_img.get_height()
        sb_aspect_ratio = orig_sb_width / orig_sb_height

        scaled_sb_height = int(self.HEIGHT * 0.7)
        scaled_sb_width = int(scaled_sb_height * sb_aspect_ratio)
        
        self.score_board_img = pygame.transform.scale(
            self.original_score_board_img, 
            (scaled_sb_width, scaled_sb_height)
        )

        font_size_factor = self.scale_y
        font_path = os.path.join('assets', 'fonts', 'PressStart2P-Regular.ttf')
        self.font = pygame.font.Font(font_path, int(50 * font_size_factor))
        self.small_font = pygame.font.Font(font_path, int(24 * font_size_factor))

        self.student_walk_frames = [
            pygame.transform.scale(frame, (int(self.PLAYER_SIZE * self.scale_x), int(self.PLAYER_SIZE * self.scale_y)))
            for frame in self.original_student_walk_frames
        ]

        self.shawarma_img = pygame.transform.scale(
            self.original_shawarma_img, 
            (int(self.PICKUP_SIZE * self.scale_x), int(self.PICKUP_SIZE * self.scale_y))
        )
        self.lemon_img = pygame.transform.scale(
            self.original_lemon_img, 
            (int(self.PICKUP_SIZE * self.scale_x), int(self.PICKUP_SIZE * self.scale_y))
        )

        self.trash_imgs = [
            pygame.transform.scale(img, (int(self.PICKUP_SIZE * self.scale_x), int(self.PICKUP_SIZE * self.scale_y)))
            for img in self.original_trash_imgs
        ]

        self.exit_button_rect = pygame.Rect(
            int(600 * self.scale_x), int(677 * self.scale_y),
            int(390 * self.scale_x), int(80 * self.scale_y)
        )
        self.start_button_rect = pygame.Rect(
            int(590 * self.scale_x), int(520 * self.scale_y),
            int(400 * self.scale_x), int(100 * self.scale_y)
        )

        self.create_obstacles()

        self.update_game_elements_positions()
    
    def update_game_elements_positions(self):
        self.player_pos.x = int(self.player_pos.x * self.scale_x)
        self.player_pos.y = int(self.player_pos.y * self.scale_y)
        self.player_pos.width = int(self.PLAYER_SIZE * self.scale_x)
        self.player_pos.height = int(self.PLAYER_SIZE * self.scale_y)

        speed_scale = min(self.scale_x, self.scale_y)
        self.DEFAULT_SPEED = int(4 * speed_scale)
        self.BOOSTED_SPEED = int(8 * speed_scale)
        self.player_speed = self.BOOSTED_SPEED if self.power_up_active else self.DEFAULT_SPEED

        for trash in self.trash_items:
            trash["rect"].x = int(trash["rect"].x * self.scale_x)
            trash["rect"].y = int(trash["rect"].y * self.scale_y)
            trash["rect"].width = int(self.PICKUP_SIZE * self.scale_x)
            trash["rect"].height = int(self.PICKUP_SIZE * self.scale_y)

        for power_up in self.power_ups:
            power_up["rect"].x = int(power_up["rect"].x * self.scale_x)
            power_up["rect"].y = int(power_up["rect"].y * self.scale_y)
            power_up["rect"].width = int(self.PICKUP_SIZE * self.scale_x)
            power_up["rect"].height = int(self.PICKUP_SIZE * self.scale_y)
    
    def init_game_elements(self):
        self.create_obstacles()
        self.spawn_trash_items()
        self.spawn_power_ups()
    
    def create_obstacles(self):
        obstacle_data = [
            (730, 90, 170, 20),
            (135, 0, 165, 20),
            (1366, 0, 129, 20),
            (260, 370, 40, 70),
            (565, 380, 45, 40),
            (260, 680, 50, 40),
            (560, 680, 50, 35),
            (1300, 390, 55, 30),
            (1320, 680, 40, 40)
        ]
        
        self.obstacles = [
            pygame.Rect(
                int(x * self.scale_x), int(y * self.scale_y), 
                int(w * self.scale_x), int(h * self.scale_y)
            ) for x, y, w, h in obstacle_data
        ]
    
    def spawn_trash_items(self):
        self.trash_items = []
        for _ in range(16):
            x = random.randint(50, self.WIDTH - 100)
            y = random.randint(50, self.HEIGHT - 100)
            img_index = random.randint(0, len(self.trash_imgs) - 1)
            self.trash_items.append({
                "rect": pygame.Rect(x, y, int(self.PICKUP_SIZE * self.scale_x), int(self.PICKUP_SIZE * self.scale_y)),
                "img": self.trash_imgs[img_index]
            })
    
    def spawn_power_ups(self):
        self.power_ups = []
        for _ in range(3):
            x = random.randint(50, self.WIDTH - 100)
            y = random.randint(50, self.HEIGHT - 100)
            img = random.choice([self.shawarma_img, self.lemon_img])
            self.power_ups.append({
                "rect": pygame.Rect(x, y, int(self.PICKUP_SIZE * self.scale_x), int(self.PICKUP_SIZE * self.scale_y)),
                "img": img
            })
    
    def spawn_particles(self, x, y, color=(255, 255, 0)):
        for _ in range(15):
            self.particles.append(Particle(x / self.scale_x, y / self.scale_y, color))
    
    def update_particles(self):
        for particle in self.particles[:]:
            particle.update()
            if not particle.is_alive():
                self.particles.remove(particle)
    
    def start_flash(self):
        self.flash_alpha = 255
        self.flash_start_time = pygame.time.get_ticks()
    
    def fade_out_menu(self, duration=500):
        fade_surface = pygame.Surface((self.WIDTH, self.HEIGHT))
        fade_surface.fill((0, 0, 0))
        
        steps = int(duration / 16)
        for i in range(steps):
            alpha = int((i / steps) * 255)
            self.screen.blit(self.menu_img, (0, 0))
            fade_surface.set_alpha(alpha)
            self.screen.blit(fade_surface, (0, 0))
            pygame.display.update()
            pygame.time.delay(16)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
    
    def fade_in_from_black(self, duration=500):
        fade_surface = pygame.Surface((self.WIDTH, self.HEIGHT))
        fade_surface.fill((0, 0, 0))
        
        steps = int(duration / 16)
        for i in range(steps):
            alpha = 255 - int((i / steps) * 255)
            self.screen.blit(self.map_img, (0, 0))
            fade_surface.set_alpha(alpha)
            self.screen.blit(fade_surface, (0, 0))
            pygame.display.update()
            pygame.time.delay(16)
    
    def play_intro_video(self, video_path, audio_path):
        pygame.mixer.music.load(audio_path)
        pygame.mixer.music.play()
        
        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        video_duration = total_frames / fps
        start_time = time.time()
        
        skip = False
        
        while cap.isOpened() and not skip:
            elapsed_time = time.time() - start_time
            if elapsed_time >= video_duration:
                break
            
            ret, frame = cap.read()
            if not ret:
                break
            
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (self.WIDTH, self.HEIGHT))
            frame_surface = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
            
            self.screen.blit(frame_surface, (0, 0))
            skip_text = self.small_font.render("Press ESC to skip...", True, (255, 165, 0))
            self.screen.blit(skip_text, (20, 20))
            pygame.display.update()
            pygame.time.delay(int(1000 / fps))
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    cap.release()
                    pygame.mixer.music.stop()
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        skip = True
                elif event.type == pygame.VIDEORESIZE:
                    self.handle_resize(event.size)
        
        cap.release()
        pygame.mixer.music.stop()
    
    def handle_resize(self, size):
        old_width, old_height = self.WIDTH, self.HEIGHT
        self.WIDTH, self.HEIGHT = size

        self.scale_x = self.WIDTH / self.BASE_WIDTH
        self.scale_y = self.HEIGHT / self.BASE_HEIGHT

        self.rescale_assets()

        if self.game_running:
            ratio_x = self.WIDTH / old_width
            ratio_y = self.HEIGHT / old_height
            self.player_pos.x = int(self.player_pos.x * ratio_x)
            self.player_pos.y = int(self.player_pos.y * ratio_y)
    
    def play_background_music(self):
        pygame.mixer.music.load(os.path.join(self.ASSETS_PATH, "background_music.mp3"))
        pygame.mixer.music.set_volume(0.5)
        pygame.mixer.music.play(loops=-1)
    
    def reset_game(self):
        self.score = 0
        self.game_running = True
        self.start_time = time.time()
        self.end_time = None
        self.elapsed_time = 0
        self.spawn_trash_items()
        self.spawn_power_ups()
        self.power_up_active = False
        self.player_speed = int(self.DEFAULT_SPEED * min(self.scale_x, self.scale_y))
        self.player_pos = pygame.Rect(
            int(100 * self.scale_x), int(100 * self.scale_y), 
            int(self.PLAYER_SIZE * self.scale_x), int(self.PLAYER_SIZE * self.scale_y)
        )
        pygame.time.delay(200)
    
    def handle_player_movement(self):
        if self.score >= 16:
            return False
            
        keys = pygame.key.get_pressed()
        moving = False
        old_pos = self.player_pos.copy()
        
        if keys[pygame.K_LEFT]:
            self.player_pos.x -= self.player_speed
            moving = True
        if keys[pygame.K_RIGHT]:
            self.player_pos.x += self.player_speed
            moving = True
        if keys[pygame.K_UP]:
            self.player_pos.y -= self.player_speed
            moving = True
        if keys[pygame.K_DOWN]:
            self.player_pos.y += self.player_speed
            moving = True
        
        self.player_pos.clamp_ip(pygame.Rect(0, 0, self.WIDTH, self.HEIGHT))

        for obstacle in self.obstacles:
            if self.player_pos.colliderect(obstacle):
                self.player_pos = old_pos
                break
        
        return moving
    
    def update_animation(self, moving, dt):
        if moving:
            self.animation_timer += dt
            if self.animation_timer >= self.ANIMATION_DELAY:
                self.animation_index = (self.animation_index + 1) % len(self.student_walk_frames)
                self.animation_timer = 0
        else:
            self.animation_index = 1
    
    def handle_collisions(self):
        for trash in self.trash_items[:]:
            if self.player_pos.colliderect(trash["rect"]):
                self.spawn_particles(trash["rect"].centerx, trash["rect"].centery, (255, 255, 0))
                self.trash_items.remove(trash)
                self.score += 1
                self.broom_sweep_sound.play()

        for power_up in self.power_ups[:]:
            if self.player_pos.colliderect(power_up["rect"]):
                color = (144, 238, 144) if power_up["img"] == self.shawarma_img else (255, 165, 0)
                self.spawn_particles(power_up["rect"].centerx, power_up["rect"].centery, color)
                self.power_ups.remove(power_up)
                self.power_up_active = True
                self.start_flash()
                self.power_up_timer = pygame.time.get_ticks()
                self.player_speed = int(self.BOOSTED_SPEED * min(self.scale_x, self.scale_y))
                self.pickup_sound.play()

        if self.score == 16 and self.end_time is None:
            self.end_time = time.time()
            self.elapsed_time = self.end_time - self.start_time
    
    def update_power_up_status(self):
        if self.power_up_active and pygame.time.get_ticks() - self.power_up_timer > self.BOOST_DURATION:
            self.power_up_active = False
            self.player_speed = int(self.DEFAULT_SPEED * min(self.scale_x, self.scale_y))
    
    def draw_menu_screen(self):
        self.screen.blit(self.menu_img, (0, 0))
    
    def draw_game_screen(self):
        self.screen.blit(self.map_img, (0, 0))

        self.screen.blit(self.student_walk_frames[self.animation_index], 
                        (self.player_pos.x, self.player_pos.y))

        for trash in self.trash_items:
            self.screen.blit(trash["img"], (trash["rect"].x, trash["rect"].y))

        for power_up in self.power_ups:
            self.screen.blit(power_up["img"], (power_up["rect"].x, power_up["rect"].y))

        if self.start_time and self.end_time is None:
            self.elapsed_time = time.time() - self.start_time
        
        time_display = self.font.render(f"Time: {self.elapsed_time:.2f}s", True, (255, 165, 0))
        self.screen.blit(time_display, (30, 30))

        self.draw_flash_effect()

        if self.score == 16:
            self.draw_score_board()
    
    def draw_flash_effect(self):
        if self.flash_alpha > 0:
            flash_surface = pygame.Surface((self.WIDTH, self.HEIGHT))
            flash_surface.fill((255, 255, 255))
            flash_surface.set_alpha(self.flash_alpha)
            self.screen.blit(flash_surface, (0, 0))

            if pygame.time.get_ticks() - self.flash_start_time > self.FLASH_DURATION:
                self.flash_alpha = max(0, self.flash_alpha - 25)
    
    def draw_score_board(self):
        score_board_rect = self.score_board_img.get_rect()

        vertical_offset = 40
        score_board_rect.center = (self.WIDTH // 2, self.HEIGHT // 2 + vertical_offset)

        self.screen.blit(self.score_board_img, score_board_rect)

        trash_collected_text = self.font.render(f"{self.score}/16", True, (255, 165, 0))
        vertical_text_offset = 40
        text_rect = trash_collected_text.get_rect(center=(score_board_rect.centerx, score_board_rect.centery + vertical_text_offset))
        self.screen.blit(trash_collected_text, text_rect)

        sb_width_scale = score_board_rect.width / self.original_score_board_img.get_width()
        sb_height_scale = score_board_rect.height / self.original_score_board_img.get_height()
        
        try_again_x = score_board_rect.left + int(self.try_again_offsets['x1'] * sb_width_scale)
        try_again_y = score_board_rect.top + int(self.try_again_offsets['y1'] * sb_height_scale)
        try_again_width = int((self.try_again_offsets['x2'] - self.try_again_offsets['x1']) * sb_width_scale)
        try_again_height = int((self.try_again_offsets['y2'] - self.try_again_offsets['y1']) * sb_height_scale)
        
        try_again_button_rect = pygame.Rect(try_again_x, try_again_y, try_again_width, try_again_height)

        mouse_pos = pygame.mouse.get_pos()
        if try_again_button_rect.collidepoint(mouse_pos):
            pygame.mouse.set_cursor(self.hand_cursor)
            if pygame.mouse.get_pressed()[0]:
                self.reset_game()
        else:
            if not self.exit_button_rect.collidepoint(mouse_pos) and not self.start_button_rect.collidepoint(mouse_pos):
                pygame.mouse.set_cursor(self.default_cursor)
    
    def handle_cursor(self):
        mouse_pos = pygame.mouse.get_pos()
        if self.exit_button_rect.collidepoint(mouse_pos) or self.start_button_rect.collidepoint(mouse_pos):
            pygame.mouse.set_cursor(self.hand_cursor)
        else:
            pygame.mouse.set_cursor(self.default_cursor)
    
    def start_game(self):
        self.fade_out_menu()
        video_path = os.path.join(self.ASSETS_PATH, "intro.mp4")
        audio_path = os.path.join(self.ASSETS_PATH, "intro_audio.mp3")
        self.play_intro_video(video_path, audio_path)
        self.fade_in_from_black()
        self.play_background_music()
        self.reset_game()
    
    def process_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.VIDEORESIZE:
                self.handle_resize(event.size)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if not self.game_running:
                    mouse_pos = pygame.mouse.get_pos()
                    if self.exit_button_rect.collidepoint(mouse_pos):
                        pygame.quit()
                        sys.exit()
                    if self.start_button_rect.collidepoint(mouse_pos):
                        self.start_game()
        return True
    
    def update(self, dt):
        if self.game_running:
            moving = self.handle_player_movement()
            self.update_animation(moving, dt)
            self.handle_collisions()
            self.update_power_up_status()
    
    def render(self):
        self.screen.fill((0, 0, 0))
        
        if not self.game_running:
            self.draw_menu_screen()
        else:
            self.draw_game_screen()

            for particle in self.particles:
                particle.draw(self.screen, (self.scale_x, self.scale_y))
        
        pygame.display.flip()
    
    def run(self):
        running = True
        while running:
            dt = self.clock.tick(60)
            self.update_particles()
            
            running = self.process_events()

            if not self.game_running or self.score < 16:
                self.handle_cursor()

            self.update(dt)

            self.render()
        
        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()