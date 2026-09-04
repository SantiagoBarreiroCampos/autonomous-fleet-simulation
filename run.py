#!/usr/bin/env python3
"""
Autonomous Vehicle Fleet Simulation

A visual demonstration comparing the efficiency of autonomous, mixed, and manual
vehicle fleets in traffic scenarios. This simulation shows how vehicle-to-vehicle
(V2V) communication in autonomous fleets leads to smoother traffic flow, lower
energy consumption, and faster recovery from disruptions.

Usage:
    python run.py

Controls:
    SPACE       Pause/Resume simulation
    R           Reset simulation
    F           Cycle speed (1x, 2x, 4x, 8x)
    S (hold)    Trigger stop event
    G           Toggle real-time graph
    LEFT/RIGHT  Change graph metric
    ESC         Quit

Author: Santiago Barreiro
License: MIT
"""

import pygame
from src.simulation import Simulation


def main():
    """Entry point for the simulation."""
    pygame.init()

    try:
        simulation = Simulation()
        simulation.run()
    except KeyboardInterrupt:
        pass
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()