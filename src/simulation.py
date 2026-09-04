"""
Main simulation controller for the Autonomous Vehicle Fleet Simulation.

This module contains the Simulation class which orchestrates the entire
application including event handling, updates, and rendering.
"""

import pygame
from typing import List, Optional

from .config import display, colors, roundabout as rb_config
from .roundabout import Roundabout
from .ui import GraphWindow, draw_roundabout, draw_aa_circle


class Simulation:
    """
    Main simulation controller.

    Manages the simulation loop, user input, and coordinates between
    the three roundabouts (autonomous, mixed, manual fleets).

    Controls:
        SPACE: Pause/Resume simulation
        R: Reset simulation
        F: Cycle through speed multipliers (1x, 2x, 4x, 8x)
        S (hold): Trigger stop event to demonstrate recovery
        G: Toggle real-time graph window
        UP/DOWN: Increase/decrease vehicle count
        LEFT/RIGHT: Change graph metric (when graph is open)
        ESC: Quit
    """

    def __init__(self):
        """Initialize the simulation."""
        self.screen = pygame.display.set_mode(
            (display.WINDOW_WIDTH, display.WINDOW_HEIGHT)
        )
        pygame.display.set_caption(display.TITLE)
        self.clock = pygame.time.Clock()

        # Fonts
        self.font = pygame.font.Font(None, 28)
        self.small_font = pygame.font.Font(None, 22)
        self.title_font = pygame.font.Font(None, 36)

        # Simulation state
        self.running = True
        self.paused = False
        self.simulation_time = 0.0
        self.speed_multiplier = 1
        self.speed_options = [1, 2, 4, 8]
        self.num_vehicles = rb_config.NUM_VEHICLES

        # Create roundabouts
        spacing = display.WINDOW_WIDTH // 4
        y_center = display.WINDOW_HEIGHT // 2 - 30

        self.roundabouts: List[Roundabout] = [
            Roundabout((spacing, y_center), "autonomous", "AUTONOMOUS FLEET", self.num_vehicles),
            Roundabout((spacing * 2, y_center), "mixed", "MIXED FLEET", self.num_vehicles),
            Roundabout((spacing * 3, y_center), "manual", "MANUAL FLEET", self.num_vehicles),
        ]

        # Graph window
        self.graph_window: Optional[GraphWindow] = None
        self.graph_update_timer = 0.0
        self.graph_update_interval = 0.5

        # Metrics display caching (update every second for readability)
        self.metrics_update_timer = 0.0
        self.metrics_update_interval = 1.0
        self.cached_metrics = [rb.get_metrics() for rb in self.roundabouts]

    def handle_events(self) -> None:
        """Process user input events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                elif event.key == pygame.K_r:
                    self._reset()
                elif event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_f:
                    self._cycle_speed()
                elif event.key == pygame.K_g:
                    self._toggle_graph_window()
                elif event.key == pygame.K_s:
                    self._set_stop_event(True)
                elif event.key == pygame.K_LEFT and self.graph_window:
                    self.graph_window.prev_metric()
                elif event.key == pygame.K_RIGHT and self.graph_window:
                    self.graph_window.next_metric()
                elif event.key == pygame.K_UP:
                    self._change_vehicle_count(1)
                elif event.key == pygame.K_DOWN:
                    self._change_vehicle_count(-1)
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_s:
                    self._set_stop_event(False)

    def _reset(self) -> None:
        """Reset the simulation to initial state."""
        spacing = display.WINDOW_WIDTH // 4
        y_center = display.WINDOW_HEIGHT // 2 - 30

        self.roundabouts = [
            Roundabout((spacing, y_center), "autonomous", "AUTONOMOUS FLEET", self.num_vehicles),
            Roundabout((spacing * 2, y_center), "mixed", "MIXED FLEET", self.num_vehicles),
            Roundabout((spacing * 3, y_center), "manual", "MANUAL FLEET", self.num_vehicles),
        ]
        self.simulation_time = 0.0
        self.paused = False
        self.cached_metrics = [rb.get_metrics() for rb in self.roundabouts]

        if self.graph_window:
            self.graph_window._clear_history()

    def _cycle_speed(self) -> None:
        """Cycle through speed multiplier options."""
        idx = self.speed_options.index(self.speed_multiplier)
        self.speed_multiplier = self.speed_options[(idx + 1) % len(self.speed_options)]

    def _change_vehicle_count(self, delta: int) -> None:
        """Change the number of vehicles and reset simulation."""
        self.num_vehicles = max(1, min(30, self.num_vehicles + delta))
        self._reset()

    def _toggle_graph_window(self) -> None:
        """Toggle the real-time graph window."""
        if self.graph_window is None:
            self.graph_window = GraphWindow()
        else:
            self.graph_window = None
            self.screen = pygame.display.set_mode(
                (display.WINDOW_WIDTH, display.WINDOW_HEIGHT)
            )
            pygame.display.set_caption(display.TITLE)

    def _set_stop_event(self, stopped: bool) -> None:
        """Set stop state for all roundabouts."""
        for roundabout in self.roundabouts:
            roundabout.set_stop(stopped)

    def update(self, dt: float) -> None:
        """
        Update simulation state.

        Args:
            dt: Time delta since last update.
        """
        if self.paused:
            return

        self.simulation_time += dt

        for roundabout in self.roundabouts:
            roundabout.update(dt)

        # Update cached metrics for display
        self.metrics_update_timer += dt
        if self.metrics_update_timer >= self.metrics_update_interval:
            self.metrics_update_timer = 0
            self.cached_metrics = [rb.get_metrics() for rb in self.roundabouts]

        # Update graph data
        if self.graph_window:
            self.graph_update_timer += dt
            if self.graph_update_timer >= self.graph_update_interval:
                self.graph_update_timer = 0
                self.graph_window.add_data(
                    self.simulation_time, self.cached_metrics[0], self.cached_metrics[1], self.cached_metrics[2]
                )

    def _draw_metrics(self) -> None:
        """Draw the metrics panel at the bottom of the screen."""
        y_start = display.WINDOW_HEIGHT - 180
        spacing = display.WINDOW_WIDTH // 4

        # Background
        pygame.draw.rect(self.screen, colors.DARK_GRAY,
                         (0, y_start - 10, display.WINDOW_WIDTH, 200))
        pygame.draw.line(self.screen, colors.WHITE,
                         (0, y_start - 10), (display.WINDOW_WIDTH, y_start - 10), 2)

        # Headers
        headers = ["METRIC", "AUTONOMOUS", "MIXED", "MANUAL"]
        for i, header in enumerate(headers):
            x = 20 if i == 0 else spacing * i
            text = self.small_font.render(header, True, colors.WHITE)
            self.screen.blit(text, (x, y_start))

        # Metric values (use cached metrics for stable display)
        metrics_list = self.cached_metrics

        metric_names = [
            ("Avg Speed (km/h)", "avg_speed_kmh", "{:.1f}"),
            ("Energy (kWh)", "total_energy_kwh", "{:.2f}"),
            ("Flow Smoothness", "flow_smoothness", "{:.1f}"),
            ("Congestion (%)", "congestion_pct", "{:.1f}"),
            ("Brake Events", "total_slowdowns", "{:.0f}")
        ]

        for row, (name, key, fmt) in enumerate(metric_names):
            y = y_start + 25 + row * 25

            name_text = self.small_font.render(name, True, colors.LIGHT_GRAY)
            self.screen.blit(name_text, (20, y))

            for i, metrics in enumerate(metrics_list):
                value = metrics[key]
                value_text = self.small_font.render(fmt.format(value), True, colors.WHITE)
                self.screen.blit(value_text, (spacing * (i + 1), y))

    def _draw_legend(self) -> None:
        """Draw the vehicle type legend."""
        legend_y = 20
        legend_x = display.WINDOW_WIDTH - 200

        draw_aa_circle(self.screen, colors.WHITE, (legend_x, legend_y), 6)
        text = self.small_font.render("Autonomous", True, colors.WHITE)
        self.screen.blit(text, (legend_x + 15, legend_y - 8))

        draw_aa_circle(self.screen, colors.LIGHT_GRAY, (legend_x, legend_y + 25), 6)
        draw_aa_circle(self.screen, colors.BLACK, (legend_x, legend_y + 25), 6, 1)
        text = self.small_font.render("Manual", True, colors.WHITE)
        self.screen.blit(text, (legend_x + 15, legend_y + 17))

    def _draw_controls(self) -> None:
        """Draw the controls help text and status."""
        controls = "SPACE: Pause | R: Reset | F: Fast Fwd | S: Stop Event | G: Graph | UP/DOWN: Vehicles | ESC: Quit"
        text = self.small_font.render(controls, True, colors.GRAY)
        self.screen.blit(text, (20, 20))

        time_text = self.small_font.render(
            f"Time: {self.simulation_time:.1f}s", True, colors.WHITE
        )
        self.screen.blit(time_text, (20, 45))

        speed_text = self.small_font.render(
            f"Speed: {self.speed_multiplier}x", True, colors.WHITE
        )
        self.screen.blit(speed_text, (20, 70))

        vehicles_text = self.small_font.render(
            f"Vehicles: {self.num_vehicles}", True, colors.WHITE
        )
        self.screen.blit(vehicles_text, (120, 70))

        if self.paused:
            pause_text = self.title_font.render("PAUSED", True, colors.WHITE)
            rect = pause_text.get_rect(center=(display.WINDOW_WIDTH // 2, 30))
            self.screen.blit(pause_text, rect)

    def draw(self) -> None:
        """Render the main simulation view."""
        self.screen.fill(colors.BLACK)

        # Title
        title = self.title_font.render(
            "Autonomous Vehicle Fleet Comparison", True, colors.WHITE
        )
        title_rect = title.get_rect(center=(display.WINDOW_WIDTH // 2, 60))
        self.screen.blit(title, title_rect)

        # Roundabouts
        for roundabout in self.roundabouts:
            draw_roundabout(
                self.screen, roundabout.center, roundabout.radius,
                roundabout.label, roundabout.vehicles, self.font
            )

        # UI elements
        self._draw_metrics()
        self._draw_legend()
        self._draw_controls()

        pygame.display.flip()

    def run(self) -> None:
        """Main simulation loop."""
        while self.running:
            frame_dt = self.clock.tick(display.FPS) / 1000.0

            self.handle_events()

            # Subdivide updates at high speeds to maintain physics consistency
            for _ in range(self.speed_multiplier):
                self.update(frame_dt)

            if self.graph_window:
                self.graph_window.draw()
                pygame.display.flip()
            else:
                self.draw()

        pygame.quit()