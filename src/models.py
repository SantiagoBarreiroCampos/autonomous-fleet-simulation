"""
Data models for the Autonomous Vehicle Fleet Simulation.

This module defines the core data structures used throughout the simulation,
including vehicle types and the Vehicle class.
"""

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Tuple


class VehicleType(Enum):
    """Enumeration of vehicle control types."""
    AUTONOMOUS = "autonomous"
    MANUAL = "manual"


@dataclass
class Vehicle:
    """
    Represents a single vehicle in the simulation.

    Vehicles move around a circular roundabout and interact with other vehicles
    based on their type (autonomous or manual). Autonomous vehicles can
    communicate and coordinate, while manual vehicles have reaction delays.

    Attributes:
        angle: Current angular position on the roundabout (radians).
        speed: Current speed in simulation units.
        base_speed: Desired cruising speed.
        vehicle_type: Whether the vehicle is autonomous or manual.
        roundabout_center: Center coordinates of the roundabout.
        radius: Radius of the vehicle's circular path.
        energy_consumed: Cumulative energy consumption.
        acceleration_changes: Count of significant speed changes.
        last_speed: Speed from previous frame (for energy calculation).
        reaction_timer: Timer for manual vehicle reaction delays.
        target_speed: Speed the vehicle is trying to reach.
        stopped_until: Timestamp until which vehicle is forced to stop.
    """
    angle: float
    speed: float
    base_speed: float
    vehicle_type: VehicleType
    roundabout_center: Tuple[int, int]
    radius: float
    energy_consumed: float = 0.0
    acceleration_changes: int = 0
    last_speed: float = 0.0
    reaction_timer: float = 0.0
    target_speed: float = 0.0
    stopped_until: float = 0.0

    def get_position(self) -> Tuple[float, float]:
        """
        Calculate the vehicle's current position in screen coordinates.

        Returns:
            Tuple of (x, y) coordinates.
        """
        x = self.roundabout_center[0] + self.radius * math.cos(self.angle)
        y = self.roundabout_center[1] + self.radius * math.sin(self.angle)
        return (x, y)

    def get_angle_distance_to(self, other: 'Vehicle') -> float:
        """
        Calculate the angular distance to another vehicle ahead.

        Args:
            other: The vehicle to measure distance to.

        Returns:
            Angular distance in radians (0 to 2π).
        """
        diff = (other.angle - self.angle) % (2 * math.pi)
        return diff

    def update_energy(self, dt: float) -> None:
        """
        Update energy consumption based on current driving behavior.

        Energy consumption is modeled with two components:
        1. Base consumption proportional to speed (rolling resistance, air drag)
        2. Additional consumption for speed changes (acceleration/braking)

        This model demonstrates that stop-and-go traffic (manual vehicles)
        consumes more energy than smooth, coordinated flow (autonomous).

        Args:
            dt: Time delta since last update.
        """
        speed_change = self.speed - self.last_speed

        # Base energy consumption (proportional to speed)
        self.energy_consumed += self.speed * dt * 0.05

        # Additional energy for acceleration/deceleration
        if speed_change > 0.01:
            self.energy_consumed += speed_change * 10 + (speed_change ** 2) * 5
            self.acceleration_changes += 1

        self.last_speed = self.speed

    @property
    def is_autonomous(self) -> bool:
        """Check if this vehicle is autonomous."""
        return self.vehicle_type == VehicleType.AUTONOMOUS