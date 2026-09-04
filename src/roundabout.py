"""
Roundabout simulation logic for the Autonomous Vehicle Fleet Simulation.

This module contains the Roundabout class which manages a group of vehicles
and implements the core simulation logic including vehicle coordination,
collision avoidance, and metrics calculation.
"""

import math
import random
from typing import List, Tuple, Dict, Optional

from .config import roundabout as rb_config, vehicle as v_config, metrics as m_config
from .models import Vehicle, VehicleType


class Roundabout:
    """
    Manages a circular roundabout with multiple vehicles.

    Each roundabout represents one fleet type (autonomous, mixed, or manual)
    and handles all vehicle updates, interactions, and metrics collection.

    The key difference between fleet types:
    - Autonomous: Vehicles communicate to maintain optimal spacing and speed
    - Manual: Vehicles react with delays and cannot coordinate
    - Mixed: Combination of both types, demonstrating partial benefits

    Attributes:
        center: Screen coordinates of the roundabout center.
        fleet_type: Type of fleet ("autonomous", "mixed", or "manual").
        label: Display label for the roundabout.
        radius: Radius of the vehicle path.
        vehicles: List of vehicles on this roundabout.
        total_slowdowns: Counter for brake events.
        current_time: Internal simulation time tracker.
    """

    def __init__(self, center: Tuple[int, int], fleet_type: str, label: str, num_vehicles: int = None):
        """
        Initialize a new roundabout.

        Args:
            center: Screen coordinates (x, y) for the roundabout center.
            fleet_type: One of "autonomous", "mixed", or "manual".
            label: Display label shown above the roundabout.
            num_vehicles: Number of vehicles (defaults to config value).
        """
        self.center = center
        self.fleet_type = fleet_type
        self.label = label
        self.radius = rb_config.RADIUS
        self.num_vehicles = num_vehicles if num_vehicles is not None else rb_config.NUM_VEHICLES
        self.vehicles: List[Vehicle] = []
        self.total_slowdowns = 0
        self.current_time = 0.0
        self._init_vehicles()

    def set_stop(self, stopped: bool) -> None:
        """
        Force the first vehicle to stop or resume.

        Used to demonstrate how each fleet type recovers from a sudden stop.

        Args:
            stopped: True to stop the vehicle, False to let it resume.
        """
        self.vehicles[0].stopped_until = float('inf') if stopped else 0

    def _init_vehicles(self) -> None:
        """Initialize vehicles with even spacing around the roundabout."""
        for i in range(self.num_vehicles):
            angle = (2 * math.pi * i) / self.num_vehicles
            base_speed = v_config.BASE_SPEED + random.uniform(
                -v_config.SPEED_VARIATION, v_config.SPEED_VARIATION
            )

            # Assign vehicle type based on fleet type
            if self.fleet_type == "autonomous":
                v_type = VehicleType.AUTONOMOUS
            elif self.fleet_type == "manual":
                v_type = VehicleType.MANUAL
            else:  # mixed - alternate between types
                v_type = VehicleType.AUTONOMOUS if i % 2 == 0 else VehicleType.MANUAL

            vehicle = Vehicle(
                angle=angle,
                speed=base_speed * random.uniform(0.7, 1.0),
                base_speed=base_speed,
                vehicle_type=v_type,
                roundabout_center=self.center,
                radius=self.radius,
                target_speed=base_speed
            )
            self.vehicles.append(vehicle)

    def _get_vehicle_ahead(self, vehicle: Vehicle) -> Tuple[Optional[Vehicle], float]:
        """
        Find the vehicle immediately ahead of the given vehicle.

        Args:
            vehicle: The vehicle to find the leader for.

        Returns:
            Tuple of (vehicle_ahead, arc_distance) or (None, inf) if no vehicle ahead.
        """
        min_dist = float('inf')
        ahead_vehicle = None

        for other in self.vehicles:
            if other is vehicle:
                continue
            dist = vehicle.get_angle_distance_to(other)
            if 0 < dist < min_dist:
                min_dist = dist
                ahead_vehicle = other

        arc_distance = min_dist * self.radius
        return ahead_vehicle, arc_distance

    def _fleet_coordination(self) -> None:
        """
        Global fleet coordination through centralized V2V communication.

        This is the TRUE advantage of autonomous vehicles - they can:
        1. Share state information with ALL vehicles instantly (not just the one ahead)
        2. Coordinate as a unified system to optimize global traffic flow
        3. Anticipate and distribute slowdowns across the entire fleet
        4. Maintain optimal spacing through collective decision-making

        The algorithm works in three phases:
        1. Gather global fleet state (all speeds, positions, gaps)
        2. Identify bottlenecks and compute optimal fleet speed
        3. Distribute target speeds to achieve uniform flow
        """
        autonomous_vehicles = [v for v in self.vehicles if v.is_autonomous]

        if len(autonomous_vehicles) < 1:
            return

        # === PHASE 1: Gather global fleet state ===
        circumference = 2 * math.pi * self.radius
        optimal_spacing = circumference / self.num_vehicles

        # Collect all gaps and speeds across the entire fleet
        fleet_state = []
        min_gap_in_fleet = float('inf')
        bottleneck_speed = float('inf')

        for vehicle in self.vehicles:
            ahead, dist = self._get_vehicle_ahead(vehicle)
            fleet_state.append({
                'vehicle': vehicle,
                'ahead': ahead,
                'gap': dist,
                'speed': vehicle.speed
            })

            # Track the tightest gap and slowest vehicle (bottleneck detection)
            if dist < min_gap_in_fleet:
                min_gap_in_fleet = dist
            if vehicle.speed < bottleneck_speed and vehicle.speed > 0:
                bottleneck_speed = vehicle.speed

        # === PHASE 2: Compute optimal fleet speed ===
        # The key insight: instead of each vehicle reacting to the one ahead,
        # ALL autonomous vehicles adjust based on the global bottleneck

        # Detect if there's a significant bottleneck (stopped vehicle, manual slowdown)
        critical_gap = v_config.MIN_DISTANCE * 1.5
        has_bottleneck = min_gap_in_fleet < critical_gap or bottleneck_speed < v_config.BASE_SPEED * 0.5

        if has_bottleneck:
            # Global slowdown: ALL autonomous vehicles reduce speed proportionally
            # This prevents the "accordion effect" where braking propagates backward
            slowdown_factor = min(1.0, min_gap_in_fleet / optimal_spacing)
            global_target_speed = v_config.BASE_SPEED * max(0.3, slowdown_factor)
        else:
            # No bottleneck: optimize for smooth, uniform flow
            global_target_speed = v_config.BASE_SPEED

        # === PHASE 3: Distribute coordinated target speeds ===
        for state in fleet_state:
            vehicle = state['vehicle']

            if not vehicle.is_autonomous:
                continue

            ahead = state['ahead']
            gap = state['gap']

            # Base target from global coordination
            vehicle.target_speed = global_target_speed

            # Local adjustments for immediate safety and spacing optimization
            if ahead:
                gap_ratio = gap / optimal_spacing

                if gap < v_config.MIN_DISTANCE:
                    # Emergency: too close, match leader speed
                    vehicle.target_speed = min(vehicle.target_speed, ahead.speed * 0.95)
                elif gap_ratio < 0.7:
                    # Below optimal spacing: slow down slightly to increase gap
                    vehicle.target_speed = min(vehicle.target_speed, global_target_speed * (0.85 + gap_ratio * 0.2))
                elif gap_ratio > 1.3:
                    # Above optimal spacing: speed up slightly to close gap
                    vehicle.target_speed = min(v_config.BASE_SPEED * 1.1, global_target_speed * 1.1)

                # If following a manual vehicle, anticipate their inconsistency
                if not ahead.is_autonomous:
                    # Maintain slightly larger buffer when following manual vehicles
                    if gap < optimal_spacing * 0.8:
                        vehicle.target_speed = min(vehicle.target_speed, ahead.speed)

            # Ensure we never exceed safe limits
            vehicle.target_speed = max(0, min(vehicle.target_speed, v_config.BASE_SPEED * 1.15))

    def _update_manual_vehicle(self, vehicle: Vehicle, ahead: Optional[Vehicle],
                               dist: float, dt: float) -> None:
        """
        Update a manual vehicle's behavior with realistic reaction delays.

        Manual vehicles have several disadvantages:
        1. Reaction delay before braking or accelerating
        2. Cannot anticipate traffic flow
        3. Inconsistent speed maintenance

        Args:
            vehicle: The manual vehicle to update.
            ahead: The vehicle ahead (if any).
            dist: Distance to the vehicle ahead.
            dt: Time delta.
        """
        # Random speed variations (human inconsistency)
        if random.random() < 0.02:
            vehicle.base_speed = v_config.BASE_SPEED + random.uniform(
                -v_config.SPEED_VARIATION * 2, v_config.SPEED_VARIATION * 2
            )

        if ahead:
            if dist < v_config.MIN_DISTANCE:
                # Emergency braking zone
                new_target = max(0.5, ahead.speed * 0.7)
                vehicle.reaction_timer += dt
                if vehicle.reaction_timer > v_config.MANUAL_BRAKE_REACTION:
                    vehicle.target_speed = new_target
                    vehicle.reaction_timer = 0
                    self.total_slowdowns += 1
            elif dist < v_config.SLOW_DOWN_DISTANCE:
                # Gradual slowdown zone
                vehicle.reaction_timer += dt
                if vehicle.reaction_timer > v_config.MANUAL_ADJUST_REACTION:
                    slow_factor = (dist - v_config.MIN_DISTANCE) / (
                            v_config.SLOW_DOWN_DISTANCE - v_config.MIN_DISTANCE
                    )
                    vehicle.target_speed = vehicle.base_speed * (0.5 + slow_factor * 0.5)
                    vehicle.reaction_timer = 0
                    self.total_slowdowns += 1
            else:
                # Clear road - accelerate back to base speed
                vehicle.reaction_timer += dt
                if vehicle.reaction_timer > v_config.MANUAL_ADJUST_REACTION:
                    vehicle.target_speed = vehicle.base_speed
                    vehicle.reaction_timer = 0
        else:
            vehicle.target_speed = vehicle.base_speed
            vehicle.reaction_timer = 0

    def update(self, dt: float) -> None:
        """
        Update all vehicles for one simulation step.

        Args:
            dt: Time delta since last update.
        """
        self.current_time += dt

        # Autonomous vehicles coordinate through global fleet communication
        if self.fleet_type in ("autonomous", "mixed"):
            self._fleet_coordination()

        for vehicle in self.vehicles:
            ahead, dist = self._get_vehicle_ahead(vehicle)

            # Check if vehicle is forced to stop
            if vehicle.stopped_until > self.current_time:
                vehicle.speed = 0
                vehicle.target_speed = 0
                continue

            # Collision prevention - full stop if too close
            if ahead and dist < v_config.COLLISION_DISTANCE:
                vehicle.speed = 0
                vehicle.target_speed = 0
                continue

            # Update behavior based on vehicle type
            if not vehicle.is_autonomous:
                self._update_manual_vehicle(vehicle, ahead, dist, dt)

            # Apply acceleration/deceleration
            if vehicle.is_autonomous:
                accel_rate = v_config.AUTONOMOUS_ACCEL
                if vehicle.target_speed < vehicle.speed:
                    accel_rate = v_config.AUTONOMOUS_DECEL
            else:
                accel_rate = v_config.MANUAL_ACCEL
                if vehicle.target_speed < vehicle.speed:
                    accel_rate = v_config.MANUAL_DECEL

            vehicle.speed += (vehicle.target_speed - vehicle.speed) * accel_rate
            vehicle.speed = max(0, min(vehicle.speed, v_config.BASE_SPEED * 1.5))

            # Update position
            angular_speed = vehicle.speed / self.radius
            vehicle.angle = (vehicle.angle + angular_speed * dt) % (2 * math.pi)

            # Update energy consumption
            vehicle.update_energy(dt)

    def get_metrics(self) -> Dict[str, float]:
        """
        Calculate current performance metrics for this roundabout.

        Returns:
            Dictionary containing:
            - avg_speed_kmh: Average speed in km/h
            - total_energy_kwh: Total energy consumed in kWh
            - flow_smoothness: Higher = more even vehicle spacing (better)
            - congestion_pct: Percentage of vehicles significantly slowed
            - total_slowdowns: Count of brake events
        """
        avg_speed = sum(v.speed for v in self.vehicles) / len(self.vehicles)
        total_energy = sum(v.energy_consumed for v in self.vehicles)

        # Congestion: how many vehicles are significantly below their target speed
        congestion_score = 0
        for v in self.vehicles:
            speed_diff = abs(v.speed - v.base_speed) / v.base_speed
            if speed_diff > 0.2:
                congestion_score += speed_diff

        # Flow smoothness: inverse of gap variance (even spacing = smooth flow)
        gaps = []
        for v in self.vehicles:
            _, dist = self._get_vehicle_ahead(v)
            gaps.append(dist * m_config.PIXEL_TO_METERS)
        avg_gap = sum(gaps) / len(gaps)
        gap_variance = sum((g - avg_gap) ** 2 for g in gaps) / len(gaps)

        return {
            "avg_speed_kmh": avg_speed * m_config.SPEED_TO_KMH,
            "total_energy_kwh": total_energy * m_config.ENERGY_TO_KWH,
            "flow_smoothness": 100 / (1 + gap_variance),
            "congestion_pct": (congestion_score / len(self.vehicles)) * 100,
            "total_slowdowns": self.total_slowdowns
        }