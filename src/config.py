"""
Configuration settings for the Autonomous Vehicle Fleet Simulation.

This module contains all configurable parameters including display settings,
vehicle behavior parameters, and simulation constants.
"""

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class DisplayConfig:
    """Display and window configuration."""
    WINDOW_WIDTH: int = 1400
    WINDOW_HEIGHT: int = 700
    FPS: int = 60
    TITLE: str = "Autonomous Vehicle Fleet Simulation"


@dataclass(frozen=True)
class Colors:
    """Color palette for the simulation (grayscale theme)."""
    BLACK: Tuple[int, int, int] = (0, 0, 0)
    WHITE: Tuple[int, int, int] = (255, 255, 255)
    GRAY: Tuple[int, int, int] = (128, 128, 128)
    LIGHT_GRAY: Tuple[int, int, int] = (200, 200, 200)
    DARK_GRAY: Tuple[int, int, int] = (60, 60, 60)

    # Graph colors for fleet comparison
    MIXED_GRAPH: Tuple[int, int, int] = (180, 180, 220)
    MANUAL_GRAPH: Tuple[int, int, int] = (220, 180, 180)


@dataclass(frozen=True)
class RoundaboutConfig:
    """Roundabout physical properties."""
    RADIUS: int = 80
    ROAD_WIDTH: int = 30
    VEHICLE_SIZE: int = 12
    NUM_VEHICLES: int = 14


@dataclass(frozen=True)
class VehicleConfig:
    """Vehicle behavior parameters."""

    # Speed rates
    BASE_SPEED: float = 35.0
    SPEED_VARIATION: float = 0.5

    # Distance rates
    MIN_DISTANCE: float = 20
    SLOW_DOWN_DISTANCE: float = 30
    COLLISION_DISTANCE: float = 15

    # Acceleration rates
    GLOBAL_ACCEL: float = 0.02
    GLOBAL_DECEL: float = 0.05
    AUTONOMOUS_ACCEL: float = GLOBAL_ACCEL
    AUTONOMOUS_DECEL: float = GLOBAL_DECEL
    MANUAL_ACCEL: float = GLOBAL_ACCEL
    MANUAL_DECEL: float = GLOBAL_DECEL

    # Reaction delays (seconds) - manual vehicles have delayed reactions
    MANUAL_BRAKE_REACTION: float = 0.3
    MANUAL_ADJUST_REACTION: float = 0.12


@dataclass(frozen=True)
class MetricsConfig:
    """Real-world unit conversion factors."""
    PIXEL_TO_METERS: float = 0.5
    SIM_TIME_SCALE: float = 1
    ENERGY_TO_KWH: float = 0.001

    @property
    def SPEED_TO_KMH(self) -> float:
        """Convert simulation speed to km/h."""
        return self.PIXEL_TO_METERS * 3.6 * self.SIM_TIME_SCALE


# Global configuration instances
display = DisplayConfig()
colors = Colors()
roundabout = RoundaboutConfig()
vehicle = VehicleConfig()
metrics = MetricsConfig()