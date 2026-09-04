"""
User interface components for the Autonomous Vehicle Fleet Simulation.

This module contains rendering functions and UI classes including the
GraphWindow for real-time metrics visualization.
"""

import pygame
import pygame.gfxdraw
from typing import List, Dict, Tuple

from .config import display, colors, roundabout as rb_config, vehicle as v_config
from .models import Vehicle, VehicleType


def get_vehicle_color(vehicle: Vehicle) -> Tuple[int, int, int]:
    """
    Calculate vehicle color based on its speed.

    Returns the base color (white for autonomous, light gray for manual)
    blended towards red as the vehicle slows down.

    Args:
        vehicle: The vehicle to get color for.

    Returns:
        RGB color tuple.
    """
    # Base colors
    if vehicle.is_autonomous:
        base_color = colors.WHITE  # (255, 255, 255)
    else:
        base_color = colors.LIGHT_GRAY  # (200, 200, 200)

    # Calculate speed ratio (0 = stopped, 1 = full speed)
    speed_ratio = min(1.0, vehicle.speed / v_config.BASE_SPEED)

    # Blend towards red as speed decreases
    # Red color target: (255, 80, 80) - soft red
    red_color = (255, 80, 80)

    # Interpolate: at full speed = base color, at zero speed = red
    r = int(base_color[0] + (red_color[0] - base_color[0]) * (1 - speed_ratio))
    g = int(base_color[1] + (red_color[1] - base_color[1]) * (1 - speed_ratio))
    b = int(base_color[2] + (red_color[2] - base_color[2]) * (1 - speed_ratio))

    return (r, g, b)


def draw_aa_circle(surface: pygame.Surface, color: Tuple[int, int, int],
                   center: Tuple[float, float], radius: int, width: int = 0) -> None:
    """
    Draw an anti-aliased circle for smoother graphics.

    Args:
        surface: Pygame surface to draw on.
        color: RGB color tuple.
        center: Center coordinates (x, y).
        radius: Circle radius in pixels.
        width: Border width (0 for filled circle).
    """
    x, y = int(center[0]), int(center[1])
    if width == 0:
        pygame.gfxdraw.aacircle(surface, x, y, radius, color)
        pygame.gfxdraw.filled_circle(surface, x, y, radius, color)
    else:
        pygame.gfxdraw.aacircle(surface, x, y, radius, color)
        if radius > width:
            pygame.gfxdraw.aacircle(surface, x, y, radius - width, color)


def draw_roundabout(surface: pygame.Surface, center: Tuple[int, int],
                    radius: int, label: str, vehicles: List[Vehicle],
                    font: pygame.font.Font) -> None:
    """
    Render a roundabout with its vehicles.

    Args:
        surface: Pygame surface to draw on.
        center: Center coordinates of the roundabout.
        radius: Radius of the vehicle path.
        label: Text label to display above the roundabout.
        vehicles: List of vehicles to render.
        font: Font for the label text.
    """
    outer_radius = radius + rb_config.ROAD_WIDTH // 2
    inner_radius = radius - rb_config.ROAD_WIDTH // 2

    # Draw road
    draw_aa_circle(surface, colors.DARK_GRAY, center, outer_radius)
    draw_aa_circle(surface, colors.BLACK, center, inner_radius)

    # Draw road edges
    draw_aa_circle(surface, colors.WHITE, center, outer_radius, 2)
    draw_aa_circle(surface, colors.WHITE, center, inner_radius, 2)

    # Draw center island
    draw_aa_circle(surface, colors.GRAY, center, inner_radius - 5)

    # Draw vehicles with speed-based color gradient
    for vehicle in vehicles:
        pos = vehicle.get_position()
        color = get_vehicle_color(vehicle)
        draw_aa_circle(surface, color, pos, rb_config.VEHICLE_SIZE // 2)
        draw_aa_circle(surface, colors.BLACK, pos, rb_config.VEHICLE_SIZE // 2, 1)

    # Draw label
    label_surface = font.render(label, True, colors.WHITE)
    label_rect = label_surface.get_rect(center=(center[0], center[1] - radius - 50))
    surface.blit(label_surface, label_rect)


class GraphWindow:
    """
    Real-time graph visualization for comparing fleet metrics.

    Displays a line graph showing how a selected metric changes over time
    for all three fleet types, allowing direct visual comparison.

    Attributes:
        GRAPH_WIDTH: Window width in pixels.
        GRAPH_HEIGHT: Window height in pixels.
        MARGIN: Left margin for Y-axis labels.
    """

    GRAPH_WIDTH = 600
    GRAPH_HEIGHT = 400
    MARGIN = 60

    # Available metrics to display
    METRICS = [
        ("avg_speed_kmh", "Average Speed (km/h)"),
        ("total_energy_kwh", "Energy Consumption (kWh)"),
        ("flow_smoothness", "Flow Smoothness"),
        ("congestion_pct", "Congestion (%)"),
    ]

    def __init__(self):
        """Initialize the graph window."""
        self.screen = pygame.display.set_mode((self.GRAPH_WIDTH, self.GRAPH_HEIGHT))
        pygame.display.set_caption("Real-Time Metrics Graph")
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 20)
        self.title_font = pygame.font.Font(None, 32)

        self.current_metric_idx = 0
        self.history_autonomous: List[float] = []
        self.history_mixed: List[float] = []
        self.history_manual: List[float] = []
        self.time_history: List[float] = []
        self.max_points = 200

    def get_current_metric(self) -> Tuple[str, str]:
        """Get the currently selected metric key and display name."""
        return self.METRICS[self.current_metric_idx]

    def next_metric(self) -> None:
        """Switch to the next metric and clear history."""
        self.current_metric_idx = (self.current_metric_idx + 1) % len(self.METRICS)
        self._clear_history()

    def prev_metric(self) -> None:
        """Switch to the previous metric and clear history."""
        self.current_metric_idx = (self.current_metric_idx - 1) % len(self.METRICS)
        self._clear_history()

    def _clear_history(self) -> None:
        """Clear all historical data."""
        self.history_autonomous.clear()
        self.history_mixed.clear()
        self.history_manual.clear()
        self.time_history.clear()

    def add_data(self, time: float, metrics_auto: Dict[str, float],
                 metrics_mixed: Dict[str, float], metrics_manual: Dict[str, float]) -> None:
        """
        Add a new data point for each fleet.

        Args:
            time: Current simulation time.
            metrics_auto: Metrics dictionary for autonomous fleet.
            metrics_mixed: Metrics dictionary for mixed fleet.
            metrics_manual: Metrics dictionary for manual fleet.
        """
        key, _ = self.get_current_metric()

        self.time_history.append(time)
        self.history_autonomous.append(metrics_auto.get(key, 0))
        self.history_mixed.append(metrics_mixed.get(key, 0))
        self.history_manual.append(metrics_manual.get(key, 0))

        # Keep only the most recent points
        if len(self.time_history) > self.max_points:
            self.time_history.pop(0)
            self.history_autonomous.pop(0)
            self.history_mixed.pop(0)
            self.history_manual.pop(0)

    def draw(self) -> None:
        """Render the graph window."""
        self.screen.fill(colors.BLACK)

        # Draw title
        _, metric_name = self.get_current_metric()
        title = self.title_font.render(metric_name, True, colors.WHITE)
        title_rect = title.get_rect(center=(self.GRAPH_WIDTH // 2, 25))
        self.screen.blit(title, title_rect)

        # Draw controls hint
        controls = self.small_font.render("LEFT/RIGHT: Change Metric", True, colors.GRAY)
        self.screen.blit(controls, (10, self.GRAPH_HEIGHT - 25))

        # Calculate graph area
        graph_left = self.MARGIN
        graph_right = self.GRAPH_WIDTH - 30
        graph_top = 50
        graph_bottom = self.GRAPH_HEIGHT - 50
        graph_w = graph_right - graph_left
        graph_h = graph_bottom - graph_top

        # Draw graph background
        pygame.draw.rect(self.screen, colors.DARK_GRAY,
                         (graph_left, graph_top, graph_w, graph_h))
        pygame.draw.rect(self.screen, colors.WHITE,
                         (graph_left, graph_top, graph_w, graph_h), 1)

        # Check if we have enough data
        if len(self.time_history) < 2:
            no_data = self.font.render("Collecting data...", True, colors.GRAY)
            self.screen.blit(no_data, (self.GRAPH_WIDTH // 2 - 60, self.GRAPH_HEIGHT // 2))
            return

        # Calculate value range
        all_values = self.history_autonomous + self.history_mixed + self.history_manual
        min_val = min(all_values) * 0.9 if all_values else 0
        max_val = max(all_values) * 1.1 if all_values else 1
        if max_val == min_val:
            max_val = min_val + 1

        # Draw grid lines and labels
        for i in range(5):
            y = graph_bottom - (i / 4) * graph_h
            val = min_val + (i / 4) * (max_val - min_val)
            pygame.draw.line(self.screen, colors.GRAY, (graph_left, y), (graph_right, y), 1)
            label = self.small_font.render(f"{val:.1f}", True, colors.LIGHT_GRAY)
            self.screen.blit(label, (5, y - 8))

        # Draw data lines
        def draw_line(history: List[float], color: Tuple[int, int, int]) -> None:
            if len(history) < 2:
                return
            points = []
            for i, val in enumerate(history):
                x = graph_left + (i / (len(history) - 1)) * graph_w
                y = graph_bottom - ((val - min_val) / (max_val - min_val)) * graph_h
                points.append((x, y))
            pygame.draw.lines(self.screen, color, False, points, 2)

        draw_line(self.history_autonomous, colors.WHITE)
        draw_line(self.history_mixed, colors.MIXED_GRAPH)
        draw_line(self.history_manual, colors.MANUAL_GRAPH)

        # Draw legend
        legend_y = graph_top + 10
        legend_x = graph_right - 100

        pygame.draw.line(self.screen, colors.WHITE,
                         (legend_x, legend_y), (legend_x + 20, legend_y), 2)
        self.screen.blit(self.small_font.render("Auto", True, colors.WHITE),
                         (legend_x + 25, legend_y - 6))

        pygame.draw.line(self.screen, colors.MIXED_GRAPH,
                         (legend_x, legend_y + 15), (legend_x + 20, legend_y + 15), 2)
        self.screen.blit(self.small_font.render("Mixed", True, colors.MIXED_GRAPH),
                         (legend_x + 25, legend_y + 9))

        pygame.draw.line(self.screen, colors.MANUAL_GRAPH,
                         (legend_x, legend_y + 30), (legend_x + 20, legend_y + 30), 2)
        self.screen.blit(self.small_font.render("Manual", True, colors.MANUAL_GRAPH),
                         (legend_x + 25, legend_y + 24))