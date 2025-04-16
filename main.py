import pygame
import random
import os
import cv2
import time

class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()

        self.WIDTH, self.HEIGHT = 1600, 900
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("CLEAN Ers")

        self.clock = pygame.time.Clock()
        self.game_running = False
        self.score = 0
        self.start_time = None
        self.end_time = None
        self.elapsed_time = 0

        self.player_pos = pygame.Rect(100, 100, 180, 180)
        self.player_speed = 4
        self.boosted_speed = 8
        
        self.power_up_active = False
        self.power_up_timer = 0
        self.boost_duration = 3000
        self.particles = []

        self.animation_index = 1
        self.animation_timer = 0
        self.animation_delay = 100
        
        self.load_assets()

        self.create_obstacles()
        self.spawn_trash_items()
        self.spawn_power_ups()

        self.exit_button_rect = pygame.Rect(600, 677, 390, 80)
        self.start_button_rect = pygame.Rect(590, 520, 400, 100)

        self.default_cursor = pygame.SYSTEM_CURSOR_ARROW
        self.hand_cursor = pygame.SYSTEM_CURSOR_HAND
    
    def load_assets(self):
        self.ASSETS_PATH = "assets"

        self.menu_img = pygame.image.load(os.path.join(self.ASSETS_PATH, "menu.png"))
        self.map_img = pygame.image.load(os.path.join(self.ASSETS_PATH, "map.png"))
        self.score_board_img = pygame.image.load(os.path.join(self.ASSETS_PATH, "score_board.png"))

        font_path = os.path.join('assets', 'fonts', 'PressStart2P-Regular.ttf')
        self.font = pygame.font.Font(font_path, 50)

        self.broom_sweep_sound = pygame.mixer.Sound(os.path.join(self.ASSETS_PATH, "sound effects", "broom_sweep.mp3"))
        self.pickup_sound = pygame.mixer.Sound(os.path.join(self.ASSETS_PATH, "sound effects", "pick-up.mp3"))
        
        self.student_walk_frames = [
            pygame.transform.scale(pygame.image.load(os.path.join(self.ASSETS_PATH, "student", f"walk{i}.png")), (180, 180))
            for i in range(1, 4)
        ]
        
        self.shawarma_img = pygame.transform.scale(pygame.image.load(os.path.join(self.ASSETS_PATH, "powerups", "shawarma.png")), (130, 130))
        self.lemon_img = pygame.transform.scale(pygame.image.load(os.path.join(self.ASSETS_PATH, "powerups", "lemon.png")), (130, 130))
        
        # Trash images
        self.trash_imgs = [
            pygame.transform.scale(pygame.image.load(os.path.join(self.ASSETS_PATH, "trash", f"trash{i}.png")), (130, 130))
            for i in range(1, 5)
        ]
    
    def create_obstacles(self):
        self.obstacles = [
            pygame.Rect(730, 90, 170, 20),
            pygame.Rect(135, 0, 165, 20),
            pygame.Rect(1366, 0, 129, 20),
            pygame.Rect(260, 370, 40, 70),
            pygame.Rect(565, 380, 45, 40),
            pygame.Rect(260, 680, 50, 40),
            pygame.Rect(560, 680, 50, 35),
            pygame.Rect(1300, 390, 55, 30),
            pygame.Rect(1320, 680, 40, 40)
        ]
    
    def spawn_trash_items(self):
        self.trash_items = []
        for _ in range(8):
            x = random.randint(50, self.WIDTH - 100)
            y = random.randint(50, self.HEIGHT - 100)
            self.trash_items.append({
                "rect": pygame.Rect(x, y, 130, 130),
                "img": random.choice(self.trash_imgs)
            })
    
    def spawn_power_ups(self):
        self.power_ups = []
        for _ in range(2):
            x = random.randint(50, self.WIDTH - 100)
            y = random.randint(50, self.HEIGHT - 100)
            img = random.choice([self.shawarma_img, self.lemon_img])
            self.power_ups.append({
                "rect": pygame.Rect(x, y, 130, 130),
                "img": img
            })

    def spawn_particles(self, x, y, color=(255, 255, 0)):
        for _ in range(15):  # Number of particles
            self.particles.append(Particle(x, y, color))

    def update_particles(self):
        for particle in self.particles[:]:
            particle.update()
            if not particle.is_alive():
                self.particles.remove(particle)
    
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
                    exit()
    
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
            skip_text = self.font.render("Press ESC to skip...", True, (255, 165, 0))
            self.screen.blit(skip_text, (20, 20))
            pygame.display.update()
            pygame.time.delay(int(1000 / fps))
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    cap.release()
                    pygame.mixer.music.stop()
                    pygame.quit()
                    exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        skip = True
        
        cap.release()
        pygame.mixer.music.stop()
    
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
        self.player_speed = 4
        pygame.time.delay(200)  # Simple debounce to avoid instant re-click
    
    def handle_player_movement(self):
        moving = False
        if self.score < 8:
            keys = pygame.key.get_pressed()
            
            old_pos = self.player_pos.copy()  # Save current position
            
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
            
            # Clamp to screen
            self.player_pos.clamp_ip(pygame.Rect(0, 0, self.WIDTH, self.HEIGHT))
            
            # Check collision with obstacles
            for obstacle in self.obstacles:
                if self.player_pos.colliderect(obstacle):
                    self.player_pos = old_pos  # Revert position if collided
                    break
        
        self.player_pos.clamp_ip(pygame.Rect(0, 0, self.WIDTH, self.HEIGHT))
        return moving
    
    def update_animation(self, moving, dt):
        if moving:
            self.animation_timer += dt
            if self.animation_timer >= self.animation_delay:
                self.animation_index = (self.animation_index + 1) % len(self.student_walk_frames)
                self.animation_timer = 0
        else:
            self.animation_index = 1
    
    def handle_collisions(self):
        # Check trash collisions
        for trash in self.trash_items[:]:
            if self.player_pos.colliderect(trash["rect"]):
                self.spawn_particles(trash["rect"].centerx, trash["rect"].centery, (255, 255, 0))
                self.trash_items.remove(trash)
                self.score += 1
                self.broom_sweep_sound.play()
        
        # Check power-up collisions
        for power_up in self.power_ups[:]:
            if self.player_pos.colliderect(power_up["rect"]):
                color = (144, 238, 144) if power_up["img"] == self.shawarma_img else (255, 165, 0)
                self.spawn_particles(power_up["rect"].centerx, power_up["rect"].centery, color)
                self.power_ups.remove(power_up)
                self.power_up_active = True
                self.power_up_timer = pygame.time.get_ticks()
                self.player_speed = self.boosted_speed
                self.pickup_sound.play()
        
        # Check if game completed
        if self.score == 8 and self.end_time is None:
            self.end_time = time.time()
            self.elapsed_time = self.end_time - self.start_time
    
    def update_power_up_status(self):
        if self.power_up_active and pygame.time.get_ticks() - self.power_up_timer > self.boost_duration:
            self.power_up_active = False
            self.player_speed = 4
    
    def draw_menu_screen(self):
        self.screen.blit(self.menu_img, (0, 0))
    
    def draw_game_screen(self):
        # Draw map
        self.screen.blit(self.map_img, (0, 0))
        
        # Draw player
        self.screen.blit(self.student_walk_frames[self.animation_index], (self.player_pos.x, self.player_pos.y))
        
        # Draw trash items
        for trash in self.trash_items:
            self.screen.blit(trash["img"], (trash["rect"].x, trash["rect"].y))
        
        # Draw power-ups
        for power_up in self.power_ups:
            self.screen.blit(power_up["img"], (power_up["rect"].x, power_up["rect"].y))
        
        # Update and draw time
        if self.start_time and self.end_time is None:
            self.elapsed_time = time.time() - self.start_time
        
        time_display = self.font.render(f"Time: {self.elapsed_time:.2f}s", True, (255, 165, 0))
        self.screen.blit(time_display, (30, 30))
        
        # Draw score board if game completed
        if self.score == 8:
            self.draw_score_board()
    
    def draw_score_board(self):
        score_board_rect = self.score_board_img.get_rect(center=(self.WIDTH // 2, self.HEIGHT // 2))
        
        # Render the number of trash collected
        trash_collected_text = self.font.render(f"{self.score}/8", True, (255, 165, 0))
        text_rect = trash_collected_text.get_rect(center=(score_board_rect.centerx, score_board_rect.centery + 80))
        
        # Draw score board
        self.screen.blit(self.score_board_img, score_board_rect)
        self.screen.blit(trash_collected_text, text_rect)
        
        # Define Try Again button rect
        try_again_x = score_board_rect.left + 176
        try_again_y = score_board_rect.top + 555
        try_again_width = 484 - 176
        try_again_height = 635 - 555
        try_again_button_rect = pygame.Rect(try_again_x, try_again_y, try_again_width, try_again_height)
        
        # Check for click on Try Again
        if pygame.mouse.get_pressed()[0]:
            if try_again_button_rect.collidepoint(pygame.mouse.get_pos()):
                self.reset_game()
    
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
    
    def run(self):
        running = True
        while running:
            self.screen.fill((0, 0, 0))
            dt = self.clock.tick(60)
            self.update_particles()
            
            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if not self.game_running and event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    if self.exit_button_rect.collidepoint(mouse_pos):
                        pygame.quit()
                        exit()
                    if self.start_button_rect.collidepoint(mouse_pos):
                        self.start_game()
            
            # Update cursor
            self.handle_cursor()
            
            # Draw appropriate screen
            if not self.game_running:
                self.draw_menu_screen()
            else:
                # Handle game mechanics
                moving = self.handle_player_movement()
                self.update_animation(moving, dt)
                self.handle_collisions()
                self.update_power_up_status()
                
                # Draw game elements
                self.draw_game_screen()

                for particle in self.particles:
                    particle.draw(self.screen)
            
            pygame.display.flip()
        
        pygame.quit()

class Particle:
    def __init__(self, x, y, color, lifetime=500):
        self.x = x
        self.y = y
        self.radius = random.randint(4, 8)
        self.color = color
        self.lifetime = lifetime  # in milliseconds
        self.spawn_time = pygame.time.get_ticks()
        self.vel_x = random.uniform(-2, 2)
        self.vel_y = random.uniform(-2, 2)

    def update(self):
        self.x += self.vel_x
        self.y += self.vel_y
        self.radius = max(0, self.radius - 0.2)  # shrink over time

    def draw(self, screen):
        if self.radius > 0:
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), int(self.radius))

    def is_alive(self):
        return pygame.time.get_ticks() - self.spawn_time < self.lifetime

if __name__ == "__main__":
    game = Game()
    game.run()