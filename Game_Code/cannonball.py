import pygame
import math
import time
from datetime import datetime
import os
import sys


class CannonBall:
    #cache a single base image to avoid disk I/O on every shot
    _base_image = None
    _enemy_image = None
    _logged_enemy_image = False

    @staticmethod
    def _resolve_asset_path(rel_path: str) -> str:
        """Resolve assets reliably in dev and packaged builds."""
        try:
            if sys.platform == 'darwin' and 'Contents/MacOS' in sys.argv[0]:
                base_dir = os.path.join(os.path.dirname(sys.argv[0]), '..', 'Resources')
            else:
                base_dir = os.path.dirname(sys.argv[0])
            return os.path.normpath(os.path.join(base_dir, rel_path))
        except Exception:
            # Fallback to relative path as-is
            return rel_path

    @classmethod
    def _safe_load_image(cls, rel_path: str):
        """Load an image without requiring a display mode (avoid convert_alpha before init)."""
        path = cls._resolve_asset_path(rel_path)
        img = pygame.image.load(path)
        try:
            # Only convert if a display surface exists to avoid failures in background threads
            if pygame.display.get_init() and pygame.display.get_surface() is not None:
                img = img.convert_alpha()
        except Exception:
            # keep unconverted surface
            pass
        return img

    @classmethod
    def _get_base_image(cls):
        #load and cache the base cannonball image ONCE
        #returns a Surface that callers should .copy() before mutating (alpha, etc.).
        if cls._base_image is None:
            try:
                img = cls._safe_load_image('../Graphics/Sprites/Cannonballs/cannonball.png')
                cls._base_image = pygame.transform.scale(img, (32, 32))
            except Exception:
                #fallback simple circle if asset not found
                surf = pygame.Surface((32, 32), pygame.SRCALPHA)
                pygame.draw.circle(surf, (200, 200, 200), (16, 16), 16)
                cls._base_image = surf
        return cls._base_image

    @classmethod
    def _get_enemy_image(cls):
        #load and cache the red (enemy) cannonball image ONCE
        if cls._enemy_image is None:
            try:
                img = cls._safe_load_image('../Graphics/Sprites/Cannonballs/cannonball-enemy.png')
                cls._enemy_image = pygame.transform.scale(img, (32, 32))
                if not cls._logged_enemy_image:
                    try:
                        print("✅ Loaded enemy cannonball sprite")
                    except Exception:
                        pass
                    cls._logged_enemy_image = True
            except Exception:
                #fallback to base image colorized red-ish
                base = cls._get_base_image().copy()
                try:
                    tint = pygame.Surface(base.get_size(), pygame.SRCALPHA)
                    tint.fill((255, 60, 60, 120))
                    base.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
                    cls._enemy_image = base
                except Exception:
                    cls._enemy_image = base
                if not cls._logged_enemy_image:
                    try:
                        print("⚠️  Enemy cannonball sprite missing; using red-tinted base")
                    except Exception:
                        pass
                    cls._logged_enemy_image = True
        return cls._enemy_image

    def __init__(self, x, y, rotation, side, velocity_x=None, velocity_y=None, server_id=None, created_at=None,
                 is_remote=False):
        self.x = x
        self.y = y
        self.rotation = rotation
        self.side = side
        self.speed = 1.2
        self.lifetime = 5.0
        self.server_id = server_id
        self.is_remote = is_remote

        # Handle created_at timestamp
        if created_at:
            if isinstance(created_at, str):
                # Parse ISO format string
                try:
                    dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    self.created_at = dt.timestamp()
                except:
                    self.created_at = time.time()
            else:
                self.created_at = float(created_at)
        else:
            self.created_at = time.time()

        # Calculate initial age
        self.age = time.time() - self.created_at

        # use cached image and keep a per-instance copy for alpha adjustments
        # remote (enemy) cannonballs use the red enemy image
        if is_remote:
            self.image = self._get_enemy_image().copy()
        else:
            self.image = self._get_base_image().copy()

        offset_distance = 0.18
        angle_offset = 1.5 if side == "left" else -1.5
        spawn_angle = rotation + angle_offset

        # Initial position offset
        init_x = x + math.cos(spawn_angle) * offset_distance
        init_y = y + math.sin(spawn_angle) * offset_distance

        # Use provided velocities for remote cannonballs, calculate for local
        if velocity_x is not None and velocity_y is not None:
            self.velocity_x = velocity_x
            self.velocity_y = velocity_y
            # For remote cannonballs, update position based on age
            if is_remote and self.age > 0:
                self.x += self.velocity_x * self.age
                self.y += self.velocity_y * self.age
        else:
            self.velocity_x = math.cos(spawn_angle) * self.speed
            self.velocity_y = math.sin(spawn_angle) * self.speed
            self.x = init_x
            self.y = init_y

    def update(self, dt):
        self.x += self.velocity_x * dt
        self.y += self.velocity_y * dt
        self.age += dt

        # Fade out effect when expiring
        if self.lifetime - self.age < 1.0:
            if hasattr(self, 'image'):
                alpha = int(255 * (self.lifetime - self.age))
                self.image.set_alpha(alpha)

        return self.age < self.lifetime

    def to_dict(self):
        """Convert to dictionary for Supabase"""
        return {
            "player_id": None,  # Will be set by NetworkManager
            "x": float(self.x),
            "y": float(self.y),
            "rotation": float(self.rotation),
            "velocity_x": float(self.velocity_x),
            "velocity_y": float(self.velocity_y),
            "side": self.side
        }

    @classmethod
    def from_dict(cls, data):
        """Create cannonball from Supabase data"""
        return cls(
            x=float(data["x"]),
            y=float(data["y"]),
            rotation=float(data["rotation"]),
            side=data["side"],
            velocity_x=float(data["velocity_x"]),
            velocity_y=float(data["velocity_y"]),
            server_id=data["id"],
            created_at=data.get("created_at"),
            is_remote=True
        )


