import math
from utils import lerp_angle, smoothstep
from config import SPRINT
import pygame

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.rotation = 0.0
        self.target_rotation = 0.0

        self.speed = 1
        self.backward_speed = 0.08
        self.rotation_speed = 5
        self.rotation_smoothing = 0.15

        self.current_velocity = 0.0
        self.target_velocity = 0.0
        self.acceleration = 3.0
        self.deceleration = 4.0

        self.velocity_x = 0.0
        self.velocity_y = 0.0
        self.wake_fade = 0.0

        self.camera_x = x
        self.camera_y = y
        self.camera_smoothing = 0.12

        self.previous_x = x
        self.previous_y = y

        self.sprint = SPRINT
        self.sprinting = False
        # Option to invert right-stick rotation direction if a controller's axis is reversed
        self.invert_right_stick = False
        # Left trigger rest value (detected on first controller sample) for robust LT detection
        self._lt_rest = None

        self.L_Can_fire = True
        self.R_Can_fire = True
        self.L_fire_time = 0
        self.R_fire_time = 0
        self.cooldown = 3000


        self.engine_sound = pygame.mixer.Sound('../Assets/Sounds/Game Sounds/boat.mp3')
        self.engine_sound.set_volume(1.0)
        self.engine_channel = None
        self.engine_fade_ms = 150  # quick fade in/out in milliseconds


    def update(self, dt, keys, controller=None):
        from config import WORLD_WIDTH, WORLD_HEIGHT
        current_time = pygame.time.get_ticks()

        # Regenerate sprint when not currently sprinting (time-based)
        if self.sprint < 100 and not self.sprinting:
            # regen rate: 10 units per second
            self.sprint = min(100, self.sprint + dt * 10.0)

        # Keyboard input for rotation
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.target_rotation += self.rotation_speed * dt
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.target_rotation -= self.rotation_speed * dt

        # Cannon fire with Q and E
        if keys[pygame.K_q] and self.L_Can_fire:
            print("Left cannon fired")
            self.L_Can_fire = False
            self.L_fire_time = current_time
        if keys[pygame.K_e] and self.R_Can_fire:
            print("Right cannon fired")
            self.R_Can_fire = False
            self.R_fire_time = current_time

        # Cooldown thing, waits 3 seconds to reset
        if not self.L_Can_fire and current_time - self.L_fire_time >= self.cooldown:
            self.L_Can_fire = True
        if not self.R_Can_fire and current_time - self.R_fire_time >= self.cooldown:
            self.R_Can_fire = True

        # Controller input for rotation (right stick or d-pad)
        # ... existing code ...

        self.rotation = lerp_angle(self.rotation, self.target_rotation, self.rotation_smoothing)
        self.rotation %= (2 * math.pi)
        self.target_rotation %= (2 * math.pi)

        self.previous_x, self.previous_y = self.x, self.y

        # Initialize movement input
        movement_input = 0.0
        if not (keys[pygame.K_w] or keys[pygame.K_UP]):
            self.sprinting = False
        if not keys[pygame.K_LSHIFT]:
            self.sprinting = False

        # --- Keyboard controls (no direct sound here) ---
        forward_pressed = keys[pygame.K_w] or keys[pygame.K_UP]
        if forward_pressed:
            movement_input = 1.0
            if keys[pygame.K_LSHIFT] and self.sprint > 0 and forward_pressed:
                self.sprint -= 0.5
                self.sprinting = True
                movement_input = 2
        elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
            movement_input = -3.0

        # Controller input for movement (if controller is connected)
        # ... existing code that modifies movement_input ...

        # Apply the movement input
        prev_velocity = self.current_velocity
        self.target_velocity = movement_input

        if self.target_velocity > self.current_velocity:
            self.current_velocity = min(self.current_velocity + self.acceleration * dt, self.target_velocity)
        else:
            self.current_velocity = max(self.current_velocity - self.deceleration * dt, self.target_velocity)

        # --- Start/stop sound based on actual movement ---
        moving_now = abs(self.current_velocity) > 1e-3
        moving_before = abs(prev_velocity) > 1e-3

        # Started moving this frame
        if moving_now and not moving_before:
            if self.engine_channel is None or not self.engine_channel.get_busy():
                self.engine_channel = self.engine_sound.play(-1)  # loop while moving

        # Stopped moving this frame
        if not moving_now and moving_before:
            if self.engine_channel is not None:
                self.engine_channel.stop()
                self.engine_channel = None

        target_wake_fade = smoothstep(0.0, 0.2, abs(self.current_velocity))
        if target_wake_fade > self.wake_fade:
            self.wake_fade = min(self.wake_fade + 3.5 * dt, target_wake_fade)
        else:
            self.wake_fade = max(self.wake_fade - 3.5 * dt, target_wake_fade)

        if self.current_velocity > 0:
            self.x += math.cos(self.rotation) * self.speed * self.current_velocity * dt
            self.y += math.sin(self.rotation) * self.speed * self.current_velocity * dt
        elif self.current_velocity < 0:
            self.x += math.cos(self.rotation) * self.backward_speed * self.current_velocity * dt
            self.y += math.sin(self.rotation) * self.backward_speed * self.current_velocity * dt

        self.velocity_x = (self.x - self.previous_x) / (dt + 1e-6)
        self.velocity_y = (self.y - self.previous_y) / (dt + 1e-6)

        self.x = max(0.5, min(WORLD_WIDTH - 0.5, self.x))
        self.y = max(0.5, min(WORLD_HEIGHT - 0.5, self.y))

        self.camera_x += (self.x - self.camera_x) * self.camera_smoothing
        self.camera_y += (self.y - self.camera_y) * self.camera_smoothing
