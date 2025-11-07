import math
from utils import lerp_angle, smoothstep


class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.rotation = 0.0
        self.target_rotation = 0.0

        self.speed = 0.5
        self.backward_speed = 0.08
        self.rotation_speed = 2.5
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

    def update(self, dt, keys, controller=None):
        import pygame
        from config import WORLD_WIDTH, WORLD_HEIGHT

        # Keyboard input for rotation
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.target_rotation += self.rotation_speed * dt
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.target_rotation -= self.rotation_speed * dt

        # Controller input for rotation (if controller is connected)
        if controller:
            # Right stick for rotation
            rotation_value = -controller.get_axis(2)  # Right stick X-axis
            if abs(rotation_value) > 0.1:  # Dead zone
                self.target_rotation -= rotation_value * self.rotation_speed * dt
            
            # D-pad rotation
            dpad_x = controller.get_hat(0)[0]  # -1 for left, 1 for right
            if dpad_x != 0:
                self.target_rotation -= dpad_x * self.rotation_speed * dt

        self.rotation = lerp_angle(self.rotation, self.target_rotation, self.rotation_smoothing)
        self.rotation %= (2 * math.pi)
        self.target_rotation %= (2 * math.pi)

        self.previous_x, self.previous_y = self.x, self.y

        # Initialize movement input
        movement_input = 0.0

        # Keyboard controls
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            movement_input = 1.0
        elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
            movement_input = -3.0

        # Controller input for movement (if controller is connected)
        if controller:
            # Left stick for movement
            stick_value = -controller.get_axis(1)  # Left stick Y-axis
            if abs(stick_value) > 0.1:  # Dead zone
                # Map stick value to match keyboard speeds
                if stick_value > 0:  # Forward
                    movement_input = stick_value * 1.0  # Same as W key
                else:  # Backward
                    movement_input = stick_value * 3.0  # Same as S key
            
            # D-pad movement (if stick isn't being used)
            if abs(stick_value) <= 0.1:
                dpad_y = controller.get_hat(0)[1]  # -1 for down, 1 for up
                if dpad_y > 0:  # Up
                    movement_input = 1.0  # Same as W key
                elif dpad_y < 0:  # Down
                    movement_input = -3.0  # Same as S key
        
        # Apply the movement
        self.target_velocity = movement_input

        if self.target_velocity > self.current_velocity:
            self.current_velocity = min(self.current_velocity + self.acceleration * dt, self.target_velocity)
        else:
            self.current_velocity = max(self.current_velocity - self.deceleration * dt, self.target_velocity)

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
