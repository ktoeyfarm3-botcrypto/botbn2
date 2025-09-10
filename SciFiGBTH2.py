import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
import hashlib
import hmac
import json
import time
import requests
import threading
from datetime import datetime, timedelta
from collections import deque
import numpy as np
import sqlite3
import os
import math
import random

# Configure theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class SciFiVisualSystem:
    """Futuristic Sci-Fi Visual Status System"""

    def __init__(self, parent_frame, width=280, height=280):
        self.parent = parent_frame
        self.width = width
        self.height = height
        self.center_x = width // 2
        self.center_y = height // 2

        # Create main canvas
        self.canvas = tk.Canvas(
            parent_frame,
            width=self.width,
            height=self.height,
            bg='#000008',  # Deep space black with blue tint
            highlightthickness=0,
            relief='flat'
        )

        # Animation state
        self.is_animating = False
        self.animation_thread = None
        self.current_state = "idle"
        self.frame_count = 0
        self.rotation_angle = 0
        self.pulse_phase = 0
        self.wave_phase = 0
        self.particle_systems = []

        # Sci-fi color schemes
        self.state_themes = {
            "idle": {
                "primary": "#00aaff",
                "secondary": "#0066cc",
                "accent": "#88ccff",
                "glow": "#44aaff"
            },
            "connecting": {
                "primary": "#ffaa00",
                "secondary": "#cc8800",
                "accent": "#ffdd88",
                "glow": "#ffcc44"
            },
            "analyzing": {
                "primary": "#ff0066",
                "secondary": "#cc0044",
                "accent": "#ff88bb",
                "glow": "#ff4488"
            },
            "buy_signal": {
                "primary": "#00ff44",
                "secondary": "#00cc22",
                "accent": "#88ff99",
                "glow": "#44ff66"
            },
            "sell_signal": {
                "primary": "#ff4400",
                "secondary": "#cc2200",
                "accent": "#ff9966",
                "glow": "#ff6644"
            },
            "trading": {
                "primary": "#ffff00",
                "secondary": "#cccc00",
                "accent": "#ffff88",
                "glow": "#ffff44"
            },
            "success": {
                "primary": "#00ff88",
                "secondary": "#00cc66",
                "accent": "#88ffbb",
                "glow": "#44ff99"
            },
            "error": {
                "primary": "#ff0000",
                "secondary": "#cc0000",
                "accent": "#ff8888",
                "glow": "#ff4444"
            }
        }

        # Initialize particles
        self.init_particle_system()
        self.canvas.pack(pady=10)

    def init_particle_system(self):
        """Initialize floating particles"""
        self.particles = []
        for _ in range(15):
            particle = {
                'x': random.uniform(50, self.width - 50),
                'y': random.uniform(50, self.height - 50),
                'dx': random.uniform(-0.5, 0.5),
                'dy': random.uniform(-0.5, 0.5),
                'size': random.uniform(1, 3),
                'alpha': random.uniform(0.3, 0.8),
                'phase': random.uniform(0, 2 * math.pi)
            }
            self.particles.append(particle)

    def start_animation(self, state="idle"):
        """Start the sci-fi animation"""
        self.current_state = state
        if not self.is_animating:
            self.is_animating = True
            self.animation_thread = threading.Thread(target=self._animation_loop, daemon=True)
            self.animation_thread.start()

    def stop_animation(self):
        """Stop animation"""
        self.is_animating = False
        if self.animation_thread:
            self.animation_thread.join(timeout=1)
        self.draw_idle_state()

    def set_state(self, state):
        """Change visual state"""
        if state in self.state_themes:
            self.current_state = state
            if state != "idle":
                self.start_animation(state)
            else:
                self.stop_animation()

    def _animation_loop(self):
        """Main animation loop"""
        while self.is_animating:
            try:
                self.frame_count += 1
                self.rotation_angle += 2
                self.pulse_phase += 0.1
                self.wave_phase += 0.15

                # Update particles
                self.update_particles()

                # Draw based on current state
                if self.current_state == "idle":
                    self._draw_idle()
                elif self.current_state == "connecting":
                    self._draw_connecting()
                elif self.current_state == "analyzing":
                    self._draw_analyzing()
                elif self.current_state == "buy_signal":
                    self._draw_buy_signal()
                elif self.current_state == "sell_signal":
                    self._draw_sell_signal()
                elif self.current_state == "trading":
                    self._draw_trading()
                elif self.current_state == "success":
                    self._draw_success()
                elif self.current_state == "error":
                    self._draw_error()

                time.sleep(0.05)  # 20 FPS

            except Exception as e:
                print(f"Animation error: {e}")
                break

    def update_particles(self):
        """Update particle positions"""
        for particle in self.particles:
            particle['x'] += particle['dx']
            particle['y'] += particle['dy']
            particle['phase'] += 0.05

            # Bounce off edges
            if particle['x'] <= 10 or particle['x'] >= self.width - 10:
                particle['dx'] *= -1
            if particle['y'] <= 10 or particle['y'] >= self.height - 10:
                particle['dy'] *= -1

    def draw_particles(self, theme):
        """Draw floating particles"""
        for particle in self.particles:
            alpha_mod = (math.sin(particle['phase']) + 1) / 2
            alpha = particle['alpha'] * alpha_mod
            intensity = int(alpha * 255)

            # Create color with alpha
            if intensity > 20:
                color = f"#{intensity // 4:02x}{intensity // 4:02x}{intensity:02x}"
                size = particle['size'] * (alpha + 0.5)

                self.canvas.create_oval(
                    particle['x'] - size, particle['y'] - size,
                    particle['x'] + size, particle['y'] + size,
                    fill=color, outline="",
                    tags="particle"
                )

    def draw_hud_rings(self, theme, base_radius=80):
        """Draw sci-fi HUD rings"""
        for i in range(4):
            radius = base_radius + i * 15
            pulse = math.sin(self.pulse_phase + i * 0.5) * 0.2 + 1.0
            actual_radius = int(radius * pulse)

            alpha = 0.8 - i * 0.15
            intensity = int(alpha * 255)

            if i == 0:
                color = theme["primary"]
                width = 3
            else:
                color = f"#{intensity // 8:02x}{intensity // 8:02x}{intensity:02x}"
                width = 2

            # Draw ring segments (broken circle effect)
            for segment in range(8):
                start_angle = segment * 45 + self.rotation_angle
                extent = 30  # 30 degree segments

                self.canvas.create_arc(
                    self.center_x - actual_radius, self.center_y - actual_radius,
                    self.center_x + actual_radius, self.center_y + actual_radius,
                    start=start_angle, extent=extent,
                    outline=color, width=width, style="arc",
                    tags="hud_ring"
                )

    def draw_energy_core(self, theme, state_specific=False):
        """Draw central energy core"""
        core_pulse = math.sin(self.pulse_phase * 2) * 0.3 + 1.0
        core_size = int(25 * core_pulse)

        # Outer glow
        for i in range(5):
            glow_size = core_size + i * 4
            alpha = (0.8 - i * 0.15) * core_pulse
            intensity = int(alpha * 200)

            if intensity > 20:
                color = f"#{intensity // 4:02x}{intensity // 4:02x}{intensity:02x}"
                self.canvas.create_oval(
                    self.center_x - glow_size, self.center_y - glow_size,
                    self.center_x + glow_size, self.center_y + glow_size,
                    fill="", outline=color, width=2,
                    tags="core_glow"
                )

        # Central core
        self.canvas.create_oval(
            self.center_x - core_size, self.center_y - core_size,
            self.center_x + core_size, self.center_y + core_size,
            fill=theme["primary"], outline=theme["accent"], width=3,
            tags="core"
        )

        # Core inner details
        inner_size = core_size // 2
        self.canvas.create_oval(
            self.center_x - inner_size, self.center_y - inner_size,
            self.center_x + inner_size, self.center_y + inner_size,
            fill=theme["glow"], outline="",
            tags="core_inner"
        )

    def _draw_idle(self):
        """Draw idle state - peaceful monitoring"""
        self.canvas.delete("all")
        theme = self.state_themes["idle"]

        self.draw_particles(theme)
        self.draw_hud_rings(theme)
        self.draw_energy_core(theme)

        # Status text
        self.canvas.create_text(
            self.center_x, self.height - 30,
            text="SYSTEM READY", fill=theme["primary"],
            font=("Orbitron", 12, "bold"),
            tags="status_text"
        )

    def _draw_connecting(self):
        """Draw connecting state - scanning animation"""
        self.canvas.delete("all")
        theme = self.state_themes["connecting"]

        self.draw_particles(theme)

        # Rotating scanner
        scanner_angle = self.rotation_angle * 3
        scanner_length = 60

        end_x = self.center_x + scanner_length * math.cos(math.radians(scanner_angle))
        end_y = self.center_y + scanner_length * math.sin(math.radians(scanner_angle))

        self.canvas.create_line(
            self.center_x, self.center_y, end_x, end_y,
            fill=theme["primary"], width=4,
            tags="scanner"
        )

        # Scanner trail effect
        for i in range(8):
            trail_angle = scanner_angle - i * 5
            trail_alpha = 1.0 - i * 0.1
            trail_length = scanner_length * trail_alpha

            trail_x = self.center_x + trail_length * math.cos(math.radians(trail_angle))
            trail_y = self.center_y + trail_length * math.sin(math.radians(trail_angle))

            intensity = int(trail_alpha * 255)
            trail_color = f"#{intensity:02x}{intensity // 2:02x}{intensity // 8:02x}"

            self.canvas.create_line(
                self.center_x, self.center_y, trail_x, trail_y,
                fill=trail_color, width=max(1, int(3 * trail_alpha)),
                tags="scanner_trail"
            )

        self.draw_hud_rings(theme, 70)
        self.draw_energy_core(theme)

        self.canvas.create_text(
            self.center_x, self.height - 30,
            text="CONNECTING...", fill=theme["primary"],
            font=("Orbitron", 12, "bold"),
            tags="status_text"
        )

    def _draw_analyzing(self):
        """Draw analyzing state - brain wave analysis"""
        self.canvas.delete("all")
        theme = self.state_themes["analyzing"]

        self.draw_particles(theme)

        # Brain wave pattern
        wave_points = []
        for i in range(100):
            x = i * (self.width / 100)
            # Complex waveform
            y1 = math.sin((i + self.wave_phase * 5) * 0.1) * 20
            y2 = math.sin((i + self.wave_phase * 3) * 0.05) * 10
            y3 = math.sin((i + self.wave_phase * 7) * 0.15) * 5
            y = self.center_y + y1 + y2 + y3
            wave_points.extend([x, y])

        if len(wave_points) >= 4:
            self.canvas.create_line(
                wave_points, fill=theme["primary"], width=3, smooth=True,
                tags="brainwave"
            )

        # Neural network nodes
        for i in range(6):
            angle = i * 60 + self.rotation_angle
            radius = 50 + 20 * math.sin(self.pulse_phase + i)

            node_x = self.center_x + radius * math.cos(math.radians(angle))
            node_y = self.center_y + radius * math.sin(math.radians(angle))

            node_pulse = math.sin(self.pulse_phase * 2 + i * 0.5) * 0.3 + 1.0
            node_size = int(8 * node_pulse)

            self.canvas.create_oval(
                node_x - node_size, node_y - node_size,
                node_x + node_size, node_y + node_size,
                fill=theme["primary"], outline=theme["accent"], width=2,
                tags="neural_node"
            )

        self.draw_energy_core(theme)

        self.canvas.create_text(
            self.center_x, self.height - 30,
            text="ANALYZING MARKET", fill=theme["primary"],
            font=("Orbitron", 12, "bold"),
            tags="status_text"
        )

    def _draw_buy_signal(self):
        """Draw buy signal - energy surge upward"""
        self.canvas.delete("all")
        theme = self.state_themes["buy_signal"]

        self.draw_particles(theme)

        # Energy surge effect
        surge_height = 80 + 30 * math.sin(self.pulse_phase * 2)
        for i in range(5):
            surge_y = self.center_y - surge_height + i * 10
            surge_width = 40 - i * 6
            alpha = 1.0 - i * 0.15
            intensity = int(alpha * 255)

            color = f"#{intensity // 8:02x}{intensity:02x}{intensity // 4:02x}"

            self.canvas.create_oval(
                self.center_x - surge_width, surge_y - 5,
                self.center_x + surge_width, surge_y + 5,
                fill=color, outline="",
                tags="energy_surge"
            )

        # Buy arrow
        arrow_size = 30 + 10 * math.sin(self.pulse_phase * 2)
        arrow_points = [
            self.center_x, self.center_y - arrow_size,
                           self.center_x - arrow_size // 2, self.center_y - arrow_size // 3,
                           self.center_x - arrow_size // 4, self.center_y - arrow_size // 3,
                           self.center_x - arrow_size // 4, self.center_y + arrow_size // 2,
                           self.center_x + arrow_size // 4, self.center_y + arrow_size // 2,
                           self.center_x + arrow_size // 4, self.center_y - arrow_size // 3,
                           self.center_x + arrow_size // 2, self.center_y - arrow_size // 3
        ]

        self.canvas.create_polygon(
            arrow_points, fill=theme["primary"], outline=theme["accent"], width=3,
            tags="buy_arrow"
        )

        self.draw_hud_rings(theme, 90)

        self.canvas.create_text(
            self.center_x, self.height - 30,
            text="BUY SIGNAL DETECTED", fill=theme["primary"],
            font=("Orbitron", 12, "bold"),
            tags="status_text"
        )

    def _draw_sell_signal(self):
        """Draw sell signal - energy contraction downward"""
        self.canvas.delete("all")
        theme = self.state_themes["sell_signal"]

        self.draw_particles(theme)

        # Energy contraction effect
        contraction_height = 80 + 30 * math.sin(self.pulse_phase * 2)
        for i in range(5):
            contract_y = self.center_y + contraction_height - i * 10
            contract_width = 40 - i * 6
            alpha = 1.0 - i * 0.15
            intensity = int(alpha * 255)

            color = f"#{intensity:02x}{intensity // 8:02x}{intensity // 8:02x}"

            self.canvas.create_oval(
                self.center_x - contract_width, contract_y - 5,
                self.center_x + contract_width, contract_y + 5,
                fill=color, outline="",
                tags="energy_contract"
            )

        # Sell arrow
        arrow_size = 30 + 10 * math.sin(self.pulse_phase * 2)
        arrow_points = [
            self.center_x, self.center_y + arrow_size,
                           self.center_x - arrow_size // 2, self.center_y + arrow_size // 3,
                           self.center_x - arrow_size // 4, self.center_y + arrow_size // 3,
                           self.center_x - arrow_size // 4, self.center_y - arrow_size // 2,
                           self.center_x + arrow_size // 4, self.center_y - arrow_size // 2,
                           self.center_x + arrow_size // 4, self.center_y + arrow_size // 3,
                           self.center_x + arrow_size // 2, self.center_y + arrow_size // 3
        ]

        self.canvas.create_polygon(
            arrow_points, fill=theme["primary"], outline=theme["accent"], width=3,
            tags="sell_arrow"
        )

        self.draw_hud_rings(theme, 90)

        self.canvas.create_text(
            self.center_x, self.height - 30,
            text="SELL SIGNAL DETECTED", fill=theme["primary"],
            font=("Orbitron", 12, "bold"),
            tags="status_text"
        )

    def _draw_trading(self):
        """Draw active trading - lightning and currency symbols"""
        self.canvas.delete("all")
        theme = self.state_themes["trading"]

        self.draw_particles(theme)

        # Lightning bolts
        for i in range(3):
            bolt_angle = i * 120 + self.rotation_angle
            bolt_radius = 60

            bolt_start_x = self.center_x + bolt_radius * math.cos(math.radians(bolt_angle))
            bolt_start_y = self.center_y + bolt_radius * math.sin(math.radians(bolt_angle))

            bolt_end_x = self.center_x + (bolt_radius + 40) * math.cos(math.radians(bolt_angle))
            bolt_end_y = self.center_y + (bolt_radius + 40) * math.sin(math.radians(bolt_angle))

            # Zigzag lightning effect
            bolt_points = [bolt_start_x, bolt_start_y]
            for j in range(4):
                progress = (j + 1) / 4
                mid_x = bolt_start_x + (bolt_end_x - bolt_start_x) * progress
                mid_y = bolt_start_y + (bolt_end_y - bolt_start_y) * progress

                # Add zigzag
                offset = 10 * math.sin(self.pulse_phase + j) * (1 - progress)
                perp_angle = bolt_angle + 90
                mid_x += offset * math.cos(math.radians(perp_angle))
                mid_y += offset * math.sin(math.radians(perp_angle))

                bolt_points.extend([mid_x, mid_y])

            if len(bolt_points) >= 4:
                self.canvas.create_line(
                    bolt_points, fill=theme["primary"], width=3,
                    tags="lightning"
                )

        # Currency symbols rotation
        symbols = ["฿", "$", "€", "¥"]
        for i, symbol in enumerate(symbols):
            symbol_angle = i * 90 + self.rotation_angle * 2
            symbol_radius = 45

            symbol_x = self.center_x + symbol_radius * math.cos(math.radians(symbol_angle))
            symbol_y = self.center_y + symbol_radius * math.sin(math.radians(symbol_angle))

            symbol_pulse = math.sin(self.pulse_phase + i * 0.5) * 0.3 + 1.0
            font_size = int(16 * symbol_pulse)

            self.canvas.create_text(
                symbol_x, symbol_y, text=symbol,
                fill=theme["primary"], font=("Arial", font_size, "bold"),
                tags="currency_symbol"
            )

        self.draw_energy_core(theme, True)

        self.canvas.create_text(
            self.center_x, self.height - 30,
            text="ACTIVE TRADING", fill=theme["primary"],
            font=("Orbitron", 12, "bold"),
            tags="status_text"
        )

    def _draw_success(self):
        """Draw success state - victory explosion"""
        self.canvas.delete("all")
        theme = self.state_themes["success"]

        self.draw_particles(theme)

        # Success explosion
        explosion_radius = 20 + 60 * math.sin(self.pulse_phase)
        for i in range(12):
            ray_angle = i * 30
            ray_length = explosion_radius

            ray_end_x = self.center_x + ray_length * math.cos(math.radians(ray_angle))
            ray_end_y = self.center_y + ray_length * math.sin(math.radians(ray_angle))

            alpha = math.sin(self.pulse_phase) * 0.5 + 0.5
            intensity = int(alpha * 255)
            color = f"#{intensity // 8:02x}{intensity:02x}{intensity // 2:02x}"

            self.canvas.create_line(
                self.center_x, self.center_y, ray_end_x, ray_end_y,
                fill=color, width=4,
                tags="success_ray"
            )

        # Checkmark
        check_size = 20 + 10 * math.sin(self.pulse_phase)
        check_points = [
            self.center_x - check_size, self.center_y,
            self.center_x - check_size // 3, self.center_y + check_size // 2,
            self.center_x + check_size, self.center_y - check_size // 2
        ]

        self.canvas.create_line(
            check_points, fill=theme["primary"], width=6,
            capstyle=tk.ROUND, joinstyle=tk.ROUND,
            tags="checkmark"
        )

        self.draw_hud_rings(theme, 100)

        self.canvas.create_text(
            self.center_x, self.height - 30,
            text="OPERATION SUCCESS", fill=theme["primary"],
            font=("Orbitron", 12, "bold"),
            tags="status_text"
        )

    def _draw_error(self):
        """Draw error state - warning system"""
        self.canvas.delete("all")
        theme = self.state_themes["error"]

        self.draw_particles(theme)

        # Error pulse
        error_intensity = math.sin(self.pulse_phase * 4) * 0.5 + 0.5

        # Warning triangles
        for i in range(6):
            triangle_angle = i * 60 + self.rotation_angle
            triangle_radius = 70
            triangle_size = 15

            tri_x = self.center_x + triangle_radius * math.cos(math.radians(triangle_angle))
            tri_y = self.center_y + triangle_radius * math.sin(math.radians(triangle_angle))

            # Triangle points
            tri_points = []
            for j in range(3):
                point_angle = triangle_angle + j * 120
                point_x = tri_x + triangle_size * math.cos(math.radians(point_angle))
                point_y = tri_y + triangle_size * math.sin(math.radians(point_angle))
                tri_points.extend([point_x, point_y])

            alpha = error_intensity
            intensity = int(alpha * 255)
            color = f"#{intensity:02x}{intensity // 8:02x}{intensity // 8:02x}"

            self.canvas.create_polygon(
                tri_points, fill=color, outline=theme["accent"], width=2,
                tags="warning_triangle"
            )

        # Central warning symbol
        warning_size = 25 + 10 * error_intensity
        self.canvas.create_text(
            self.center_x, self.center_y,
            text="⚠", fill=theme["primary"],
            font=("Arial", int(warning_size), "bold"),
            tags="warning_symbol"
        )

        # Error rings
        for i in range(3):
            ring_radius = 50 + i * 20 + 10 * error_intensity
            ring_alpha = error_intensity * (1 - i * 0.2)
            ring_intensity = int(ring_alpha * 255)
            ring_color = f"#{ring_intensity:02x}{ring_intensity // 8:02x}{ring_intensity // 8:02x}"

            self.canvas.create_oval(
                self.center_x - ring_radius, self.center_y - ring_radius,
                self.center_x + ring_radius, self.center_y + ring_radius,
                outline=ring_color, width=3,
                tags="error_ring"
            )

        self.canvas.create_text(
            self.center_x, self.height - 30,
            text="SYSTEM ERROR", fill=theme["primary"],
            font=("Orbitron", 12, "bold"),
            tags="status_text"
        )

    def draw_idle_state(self):
        """Draw static idle state"""
        self.canvas.delete("all")
        theme = self.state_themes["idle"]

        # Simple idle display
        self.canvas.create_oval(
            self.center_x - 50, self.center_y - 50,
            self.center_x + 50, self.center_y + 50,
            outline=theme["primary"], width=3,
            tags="idle_ring"
        )

        self.canvas.create_oval(
            self.center_x - 15, self.center_y - 15,
            self.center_x + 15, self.center_y + 15,
            fill=theme["primary"], outline=theme["accent"], width=2,
            tags="idle_core"
        )

        self.canvas.create_text(
            self.center_x, self.height - 30,
            text="SYSTEM READY", fill=theme["primary"],
            font=("Orbitron", 12, "bold"),
            tags="status_text"
        )

    def flash_effect(self, color="#ff0000", duration=0.3):
        """Flash effect for alerts"""
        original_bg = self.canvas.cget('bg')
        self.canvas.configure(bg=color)

        def reset_bg():
            self.canvas.configure(bg=original_bg)

        threading.Timer(duration, reset_bg).start()

    def cleanup(self):
        """Cleanup resources"""
        self.stop_animation()
        if hasattr(self, 'canvas'):
            self.canvas.destroy()


class ImprovedBitkubAPI:
    """Enhanced Bitkub API Client with all coins and fee calculation"""

    def __init__(self, api_key="", api_secret=""):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://api.bitkub.com"
        self.request_times = deque(maxlen=250)
        self.rate_limit_lock = threading.Lock()

        # Bitkub fee structure (actual fees as of 2024)
        self.trading_fees = {
            'maker_fee': 0.0025,  # 0.25%
            'taker_fee': 0.0025,  # 0.25%
            'withdrawal_fee': 0.001  # 0.1% (varies by coin)
        }

        # Complete list of all Bitkub supported coins
        self.all_bitkub_symbols = [
            "btc_thb", "eth_thb", "ada_thb", "xrp_thb", "bnb_thb", "doge_thb",
            "dot_thb", "matic_thb", "atom_thb", "near_thb", "sol_thb", "sand_thb",
            "mana_thb", "avax_thb", "shib_thb", "ltc_thb", "bch_thb", "etc_thb",
            "link_thb", "uni_thb", "usdt_thb", "usdc_thb", "dai_thb", "busd_thb",
            "alpha_thb", "ftt_thb", "axie_thb", "alice_thb", "chz_thb", "jasmy_thb",
            "lrc_thb", "comp_thb", "mkr_thb", "snx_thb", "aave_thb", "grt_thb",
            "1inch_thb", "enj_thb", "gala_thb", "chr_thb", "bat_thb", "omg_thb",
            "knc_thb", "cvc_thb", "pow_thb", "iotx_thb", "wxt_thb", "zil_thb",
            "srk_thb", "six_thb", "jfin_thb", "arpa_thb", "troy_thb", "ong_thb",
            "zrx_thb", "kub_thb", "ctxc_thb", "infra_thb", "bitkub_thb"
        ]

        # Error code mapping
        self.error_codes = {
            0: "Success", 1: "Invalid JSON payload", 2: "Missing X-BTK-APIKEY",
            3: "Invalid API key", 4: "API pending for activation", 5: "IP not allowed",
            6: "Missing / invalid signature", 7: "Missing timestamp", 8: "Invalid timestamp",
            9: "Invalid user / User not found", 10: "Invalid parameter", 11: "Invalid symbol",
            12: "Invalid amount / Amount too low", 13: "Invalid rate", 14: "Improper rate",
            15: "Amount too low", 16: "Failed to get balance", 17: "Wallet is empty",
            18: "Insufficient balance", 19: "Failed to insert order into db",
            20: "Failed to deduct balance", 21: "Invalid order for cancellation",
            22: "Invalid side", 23: "Failed to update order status", 24: "Invalid order for lookup",
            25: "KYC level 1 is required", 30: "Limit exceeds", 55: "Cancel only mode",
            56: "User suspended from purchasing", 57: "User suspended from selling",
            90: "Server error (contact support)"
        }

    def calculate_trading_fees(self, amount, price, side="both"):
        """Calculate Bitkub trading fees"""
        trade_value = amount * price

        if side == "buy":
            return trade_value * self.trading_fees['taker_fee']
        elif side == "sell":
            return trade_value * self.trading_fees['maker_fee']
        else:  # both sides
            return trade_value * (self.trading_fees['maker_fee'] + self.trading_fees['taker_fee'])

    def calculate_break_even_price(self, entry_price, side="buy"):
        """Calculate break-even price including fees"""
        total_fee_pct = self.trading_fees['maker_fee'] + self.trading_fees['taker_fee']

        if side == "buy":
            # Price needs to rise to cover both buy and sell fees
            return entry_price * (1 + total_fee_pct + 0.002)  # +0.2% buffer for slippage
        else:
            return entry_price * (1 - total_fee_pct - 0.002)

    def _wait_for_rate_limit(self):
        """Rate limiting management"""
        with self.rate_limit_lock:
            now = time.time()
            while self.request_times and (now - self.request_times[0]) > 10:
                self.request_times.popleft()
            if len(self.request_times) >= 190:  # Conservative limit
                time.sleep(1)
                self.request_times.clear()
            self.request_times.append(now)

    def get_server_time(self):
        """Get server timestamp"""
        try:
            response = requests.get(f"{self.base_url}/api/v3/servertime", timeout=10)
            return response.json()
        except:
            return int(time.time() * 1000)

    def create_signature(self, timestamp, method, path, body=""):
        """Create HMAC SHA256 signature"""
        signature_string = f"{timestamp}{method}{path}{body}"
        return hmac.new(
            self.api_secret.encode('utf-8'),
            signature_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

    def normalize_symbol_for_trading(self, symbol):
        """Convert symbol to correct format for trading API"""
        symbol = symbol.upper()

        # Convert display format to trading format for all Bitkub coins
        symbol_map = {
            "THB_BTC": "btc_thb", "THB_ETH": "eth_thb", "THB_ADA": "ada_thb",
            "THB_XRP": "xrp_thb", "THB_BNB": "bnb_thb", "THB_DOGE": "doge_thb",
            "THB_DOT": "dot_thb", "THB_MATIC": "matic_thb", "THB_ATOM": "atom_thb",
            "THB_NEAR": "near_thb", "THB_SOL": "sol_thb", "THB_SAND": "sand_thb",
            "THB_MANA": "mana_thb", "THB_AVAX": "avax_thb", "THB_SHIB": "shib_thb",
            "THB_LTC": "ltc_thb", "THB_BCH": "bch_thb", "THB_ETC": "etc_thb",
            "THB_LINK": "link_thb", "THB_UNI": "uni_thb", "THB_USDT": "usdt_thb",
            "THB_USDC": "usdc_thb", "THB_DAI": "dai_thb", "THB_BUSD": "busd_thb",
            "THB_ALPHA": "alpha_thb", "THB_FTT": "ftt_thb", "THB_AXIE": "axie_thb",
            "THB_ALICE": "alice_thb", "THB_CHZ": "chz_thb", "THB_JASMY": "jasmy_thb",
            "THB_LRC": "lrc_thb", "THB_COMP": "comp_thb", "THB_MKR": "mkr_thb",
            "THB_SNX": "snx_thb", "THB_AAVE": "aave_thb", "THB_GRT": "grt_thb",
            "THB_1INCH": "1inch_thb", "THB_ENJ": "enj_thb", "THB_GALA": "gala_thb",
            "THB_CHR": "chr_thb", "THB_BAT": "bat_thb", "THB_OMG": "omg_thb",
            "THB_KNC": "knc_thb", "THB_CVC": "cvc_thb", "THB_POW": "pow_thb",
            "THB_IOTX": "iotx_thb", "THB_WXT": "wxt_thb", "THB_ZIL": "zil_thb",
            "THB_SRK": "srk_thb", "THB_SIX": "six_thb", "THB_JFIN": "jfin_thb",
            "THB_ARPA": "arpa_thb", "THB_TROY": "troy_thb", "THB_ONG": "ong_thb",
            "THB_ZRX": "zrx_thb", "THB_KUB": "kub_thb", "THB_CTXC": "ctxc_thb",
            "THB_INFRA": "infra_thb", "THB_BITKUB": "bitkub_thb"
        }

        if symbol in symbol_map:
            return symbol_map[symbol]

        # If already in base_quote format, keep it
        parts = symbol.lower().split('_')
        if len(parts) == 2 and parts[1] == 'thb':
            return symbol.lower()
        elif len(parts) == 2 and parts[0] == 'thb':
            return f"{parts[1]}_thb"
        else:
            return symbol.lower()

    def get_simple_ticker(self, symbol):
        """Get ticker data using proven method"""
        try:
            self._wait_for_rate_limit()
            response = requests.get(f"{self.base_url}/api/market/ticker", timeout=10)
            data = response.json()

            if isinstance(data, dict):
                # Look for symbol in different formats
                symbol_variations = [
                    symbol.upper(), symbol.lower(),
                    f"THB_{symbol.split('_')[0].upper()}",
                    f"{symbol.split('_')[0].upper()}_THB"
                ]

                for variant in symbol_variations:
                    if variant in data:
                        ticker_data = data[variant]
                        return {
                            'symbol': variant,
                            'last_price': float(ticker_data.get('last', 0)),
                            'bid': float(ticker_data.get('highestBid', 0)),
                            'ask': float(ticker_data.get('lowestAsk', 0)),
                            'change_24h': float(ticker_data.get('percentChange', 0)),
                            'volume_24h': float(ticker_data.get('quoteVolume', 0))
                        }

                # Try to find BTC related symbols as fallback
                for key in data.keys():
                    if 'BTC' in key.upper():
                        ticker_data = data[key]
                        return {
                            'symbol': key,
                            'last_price': float(ticker_data.get('last', 0)),
                            'bid': float(ticker_data.get('highestBid', 0)),
                            'ask': float(ticker_data.get('lowestAsk', 0)),
                            'change_24h': float(ticker_data.get('percentChange', 0)),
                            'volume_24h': float(ticker_data.get('quoteVolume', 0))
                        }

            return None
        except Exception as e:
            print(f"Ticker error: {e}")
            return None

    def check_balance(self):
        """Check wallet balance"""
        try:
            self._wait_for_rate_limit()
            timestamp = self.get_server_time()
            path = "/api/v3/market/wallet"
            signature = self.create_signature(timestamp, "POST", path)

            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "X-BTK-APIKEY": self.api_key,
                "X-BTK-TIMESTAMP": str(timestamp),
                "X-BTK-SIGN": signature
            }

            response = requests.post(f"{self.base_url}{path}", headers=headers, timeout=10)
            return response.json()
        except Exception as e:
            print(f"Balance check error: {e}")
            return None

    def place_buy_order_safe(self, symbol, amount_thb, buy_price, order_type="limit"):
        """Place buy order using proven method"""
        try:
            # Convert to trading API format
            trading_symbol = self.normalize_symbol_for_trading(symbol)

            self._wait_for_rate_limit()

            order_data = {
                "sym": trading_symbol,
                "amt": amount_thb,
                "rat": buy_price if order_type == "limit" else 0,
                "typ": order_type
            }

            timestamp = self.get_server_time()
            path = "/api/v3/market/place-bid"
            body = json.dumps(order_data, separators=(',', ':'))
            signature = self.create_signature(timestamp, "POST", path, body)

            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "X-BTK-APIKEY": self.api_key,
                "X-BTK-TIMESTAMP": str(timestamp),
                "X-BTK-SIGN": signature
            }

            response = requests.post(f"{self.base_url}{path}", headers=headers, data=body, timeout=10)
            result = response.json()

            # Log for debugging
            print(f"Buy order - Symbol: {trading_symbol}, Amount: {amount_thb}, Price: {buy_price}")
            print(f"API Response: {result}")

            return result

        except Exception as e:
            return {"error": 999, "message": f"Request failed: {e}"}

    def place_sell_order_safe(self, symbol, amount_crypto, sell_price, order_type="limit"):
        """Place sell order using proven method"""
        try:
            # Convert to trading API format
            trading_symbol = self.normalize_symbol_for_trading(symbol)

            self._wait_for_rate_limit()

            order_data = {
                "sym": trading_symbol,
                "amt": amount_crypto,
                "rat": sell_price if order_type == "limit" else 0,
                "typ": order_type
            }

            timestamp = self.get_server_time()
            path = "/api/v3/market/place-ask"
            body = json.dumps(order_data, separators=(',', ':'))
            signature = self.create_signature(timestamp, "POST", path, body)

            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "X-BTK-APIKEY": self.api_key,
                "X-BTK-TIMESTAMP": str(timestamp),
                "X-BTK-SIGN": signature
            }

            response = requests.post(f"{self.base_url}{path}", headers=headers, data=body, timeout=10)
            result = response.json()

            print(f"Sell order - Symbol: {trading_symbol}, Amount: {amount_crypto}, Price: {sell_price}")
            print(f"API Response: {result}")

            return result

        except Exception as e:
            return {"error": 999, "message": f"Request failed: {e}"}

    def cancel_order_safe(self, symbol, order_id, side):
        """Cancel order safely"""
        try:
            trading_symbol = self.normalize_symbol_for_trading(symbol)

            self._wait_for_rate_limit()

            order_data = {
                "sym": trading_symbol,
                "id": str(order_id),
                "sd": side
            }

            timestamp = self.get_server_time()
            path = "/api/v3/market/cancel-order"
            body = json.dumps(order_data, separators=(',', ':'))
            signature = self.create_signature(timestamp, "POST", path, body)

            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "X-BTK-APIKEY": self.api_key,
                "X-BTK-TIMESTAMP": str(timestamp),
                "X-BTK-SIGN": signature
            }

            response = requests.post(f"{self.base_url}{path}", headers=headers, data=body, timeout=10)
            return response.json()

        except Exception as e:
            return {"error": 999, "message": f"Request failed: {e}"}

    def get_my_open_orders_safe(self, symbol):
        """Get open orders safely"""
        try:
            # Use GET method for open orders
            trading_symbol = self.normalize_symbol_for_trading(symbol)

            self._wait_for_rate_limit()

            timestamp = self.get_server_time()
            path = f"/api/v3/market/my-open-orders"
            query_string = f"?sym={trading_symbol.upper()}"

            signature = self.create_signature(timestamp, "GET", path + query_string)

            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "X-BTK-APIKEY": self.api_key,
                "X-BTK-TIMESTAMP": str(timestamp),
                "X-BTK-SIGN": signature
            }

            response = requests.get(f"{self.base_url}{path}{query_string}", headers=headers, timeout=10)
            return response.json()

        except Exception as e:
            return {"error": 999, "message": f"Request failed: {e}"}

    def check_system_status(self):
        """Check API system status"""
        try:
            response = requests.get(f"{self.base_url}/api/status", timeout=10)
            status_data = response.json()
            for service in status_data:
                if service["status"] != "ok":
                    return False, f"Service '{service['name']}' is not OK"
            return True, "All systems operational"
        except Exception as e:
            return False, f"Could not check system status: {e}"


class ProfitableTradingStrategy:
    """Enhanced trading strategy with Bitkub fee calculation"""

    def __init__(self, api_client):
        self.api_client = api_client

        # Fee-aware parameters
        self.min_profit_margin = 0.008  # 0.8% minimum profit above fees
        self.optimal_profit_target = 0.015  # 1.5% target profit

        # RSI settings optimized for fee structure
        self.rsi_oversold = 25  # More conservative
        self.rsi_overbought = 75

        # Risk management
        self.stop_loss_pct = 0.015  # 1.5%
        self.take_profit_pct = 0.025  # 2.5%
        self.max_position_age_hours = 6  # Close position within 6 hours

        # Position tracking
        self.position = None

        # Market data storage
        self.price_history = deque(maxlen=200)
        self.volume_history = deque(maxlen=50)

    def calculate_rsi(self, prices, period=14):
        """Calculate RSI with improved accuracy"""
        if len(prices) < period + 1:
            return 50

        deltas = np.diff(prices[-period - 1:])
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gain = np.mean(gains)
        avg_loss = np.mean(losses)

        if avg_loss == 0:
            return 100

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def calculate_volume_momentum(self, current_volume):
        """Calculate volume momentum"""
        self.volume_history.append(current_volume)

        if len(self.volume_history) < 10:
            return 1.0

        recent_avg = np.mean(list(self.volume_history)[-5:])
        longer_avg = np.mean(list(self.volume_history)[-10:])

        return recent_avg / longer_avg if longer_avg > 0 else 1.0

    def should_buy_profitable(self, price, volume, balance_thb, trade_amount):
        """Enhanced buy signal with fee consideration"""
        if self.position:
            return False, "Already have position"

        if balance_thb < trade_amount:
            return False, f"Insufficient balance: {balance_thb:.2f} < {trade_amount}"

        self.price_history.append(price)

        # Calculate break-even price including fees
        break_even_price = self.api_client.calculate_break_even_price(price, "buy")
        required_gain_pct = (break_even_price - price) / price

        # Only proceed if profit potential is realistic
        if required_gain_pct > self.min_profit_margin:
            return False, f"Required gain too high: {required_gain_pct * 100:.2f}%"

        conditions = []

        # RSI check
        if len(self.price_history) >= 15:
            rsi = self.calculate_rsi(list(self.price_history))
            if rsi < self.rsi_oversold:
                conditions.append(f"RSI oversold ({rsi:.1f})")
            elif rsi > 50:  # Don't buy if RSI > 50
                return False, f"RSI too high ({rsi:.1f})"

        # Volume momentum check
        volume_momentum = self.calculate_volume_momentum(volume)
        if volume_momentum > 1.2:  # Volume 20% above average
            conditions.append(f"Volume surge ({volume_momentum:.2f}x)")

        # Price momentum check
        if len(self.price_history) >= 10:
            recent_prices = list(self.price_history)[-5:]
            older_prices = list(self.price_history)[-10:-5]

            recent_avg = np.mean(recent_prices)
            older_avg = np.mean(older_prices)

            price_momentum = (recent_avg - older_avg) / older_avg
            if price_momentum < -0.01:  # Price declining 1%
                conditions.append(f"Price dip ({price_momentum * 100:.2f}%)")

        # Need at least 2 conditions for buy signal
        if len(conditions) >= 2:
            return True, " & ".join(conditions)

        return False, f"Conditions: {len(conditions)}/2 ({', '.join(conditions) if conditions else 'None'})"

    def should_sell_profitable(self, current_price, volume):
        """Enhanced sell signal with fee consideration"""
        if not self.position:
            return False, "No position"

        entry_price = self.position['entry_price']
        entry_time = self.position.get('entry_time', datetime.now())
        amount = self.position['amount']

        # Calculate real P&L including fees
        buy_fee = self.api_client.calculate_trading_fees(amount, entry_price, "buy")
        sell_fee = self.api_client.calculate_trading_fees(amount, current_price, "sell")
        gross_pnl = (current_price - entry_price) * amount
        net_pnl = gross_pnl - buy_fee - sell_fee
        net_pnl_pct = net_pnl / (entry_price * amount)

        # Time-based exit (forced)
        hours_held = (datetime.now() - entry_time).total_seconds() / 3600
        if hours_held > self.max_position_age_hours:
            return True, f"Max holding time ({hours_held:.1f}h), P&L: {net_pnl_pct * 100:.2f}%"

        # Stop loss (net loss)
        if net_pnl_pct <= -self.stop_loss_pct:
            return True, f"Stop Loss ({net_pnl_pct * 100:.2f}%)"

        # Take profit (net gain)
        if net_pnl_pct >= self.take_profit_pct:
            return True, f"Take Profit ({net_pnl_pct * 100:.2f}%)"

        # RSI overbought
        if len(self.price_history) >= 15:
            rsi = self.calculate_rsi(list(self.price_history))
            if rsi > self.rsi_overbought and net_pnl_pct > 0.005:  # Only if some profit
                return True, f"RSI overbought ({rsi:.1f}), P&L: {net_pnl_pct * 100:.2f}%"

        # Volume momentum decline (with profit)
        if net_pnl_pct > 0.01:  # At least 1% profit
            volume_momentum = self.calculate_volume_momentum(volume)
            if volume_momentum < 0.8:  # Volume declined 20%
                return True, f"Volume decline with profit ({net_pnl_pct * 100:.2f}%)"

        return False, f"Hold (Net P&L: {net_pnl_pct * 100:.2f}%)"


class ImprovedTradingBot:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("🚀 Enhanced Bitkub Trading Bot with Sci-Fi Graphics")
        self.root.geometry("1600x1000")

        # Core components
        self.api_client = None
        self.strategy = None
        self.scifi_visual = None

        # Trading state
        self.is_trading = False
        self.is_paper_trading = True
        self.emergency_stop = False

        # Trading config with all Bitkub coins
        self.config = {
            'symbol': 'btc_thb',
            'trade_amount_thb': 500,  # Higher for profitable trading
            'max_daily_trades': 3,
            'max_daily_loss': 1000,
            'min_trade_interval': 1800,  # 30 minutes
        }

        # Statistics
        self.daily_trades = 0
        self.daily_pnl = 0
        self.last_trade_time = None
        self.total_fees_paid = 0

        # Database
        self.init_database()

        # Setup UI
        self.setup_ui()

    def init_database(self):
        """Initialize database for trade history"""
        self.db_path = "enhanced_trading_bot.db"
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                symbol TEXT,
                side TEXT,
                amount REAL,
                price REAL,
                total_thb REAL,
                order_id TEXT,
                status TEXT,
                pnl REAL,
                fees REAL,
                net_pnl REAL,
                reason TEXT,
                is_paper BOOLEAN,
                rsi REAL,
                volume_momentum REAL,
                break_even_price REAL,
                api_response TEXT
            )
        ''')

        conn.commit()
        conn.close()

    def setup_ui(self):
        """Create enhanced UI with Sci-Fi graphics"""

        # Enhanced warning banner
        warning_frame = ctk.CTkFrame(self.root, fg_color="red", height=60)
        warning_frame.pack(fill="x", padx=10, pady=5)
        warning_frame.pack_propagate(False)

        warning_text = "⚠️ ENHANCED BITKUB TRADING BOT - WITH FEE CALCULATION & SCI-FI GRAPHICS ⚠️\nAll Bitkub coins supported with accurate fee calculation!"
        ctk.CTkLabel(warning_frame, text=warning_text,
                     font=("Arial", 14, "bold"),
                     text_color="white").pack(expand=True)

        # Tabs
        self.tabview = ctk.CTkTabview(self.root)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_dashboard = self.tabview.add("📊 Dashboard")
        self.tab_trading = self.tabview.add("💹 Trading")
        self.tab_api = self.tabview.add("🔌 API Config")
        self.tab_testing = self.tabview.add("🧪 Testing")
        self.tab_history = self.tabview.add("📜 History")
        self.tab_settings = self.tabview.add("⚙️ Settings")

        self.setup_dashboard_tab()
        self.setup_trading_tab()
        self.setup_api_tab()
        self.setup_testing_tab()
        self.setup_history_tab()
        self.setup_settings_tab()

    def setup_dashboard_tab(self):
        """Enhanced dashboard with Sci-Fi visual system"""
        # Main content frame
        content_frame = ctk.CTkFrame(self.tab_dashboard)
        content_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Left side - Status cards and controls
        left_frame = ctk.CTkFrame(content_frame)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

        # Status cards
        stats_frame = ctk.CTkFrame(left_frame)
        stats_frame.pack(fill="x", padx=10, pady=10)

        self.status_cards = {}
        cards = [
            ("Mode", "PAPER TRADING", "orange"),
            ("System Status", "Checking...", "blue"),
            ("Balance THB", "---", "green"),
            ("Daily P&L", "0.00", "blue"),
            ("Total Fees", "0.00", "red"),
            ("Daily Trades", "0/3", "purple"),
            ("Position", "None", "gray"),
            ("Net Profit", "0.00", "yellow")
        ]

        for i, (label, value, color) in enumerate(cards):
            row = i // 4
            col = i % 4

            card = ctk.CTkFrame(stats_frame)
            card.grid(row=row, column=col, padx=5, pady=5, sticky="ew")

            ctk.CTkLabel(card, text=label, font=("Arial", 10)).pack(pady=2)
            self.status_cards[label] = ctk.CTkLabel(card, text=value,
                                                    font=("Arial", 12, "bold"))
            self.status_cards[label].pack(pady=5)

        for col in range(4):
            stats_frame.grid_columnconfigure(col, weight=1)

        # Control panel
        control_frame = ctk.CTkFrame(left_frame)
        control_frame.pack(fill="x", padx=10, pady=10)

        # Trading controls
        trading_controls = ctk.CTkFrame(control_frame)
        trading_controls.pack(side="left", padx=10)

        self.start_btn = ctk.CTkButton(trading_controls, text="▶️ Start Trading Bot",
                                       command=self.toggle_trading,
                                       fg_color="green", height=40, width=200)
        self.start_btn.pack(pady=5)

        # Paper/Real toggle
        self.paper_switch = ctk.CTkSwitch(trading_controls,
                                          text="REAL Trading (Dangerous!)",
                                          command=self.toggle_paper_trading,
                                          button_color="red",
                                          progress_color="darkred")
        self.paper_switch.pack(pady=5)

        # Emergency controls
        emergency_frame = ctk.CTkFrame(control_frame)
        emergency_frame.pack(side="right", padx=10)

        ctk.CTkButton(emergency_frame, text="🚨 EMERGENCY STOP",
                      command=self.emergency_stop_trading,
                      fg_color="red", height=50, width=150,
                      font=("Arial", 12, "bold")).pack(pady=2)

        ctk.CTkButton(emergency_frame, text="🔄 System Check",
                      command=self.system_health_check,
                      height=30, width=150).pack(pady=2)

        # Enhanced display
        self.dashboard_display = ctk.CTkTextbox(left_frame, font=("Consolas", 11))
        self.dashboard_display.pack(fill="both", expand=True, padx=10, pady=10)

        # Right side - Sci-Fi Visual System
        self.add_scifi_visual_to_dashboard(content_frame)

    def add_scifi_visual_to_dashboard(self, parent_frame):
        """Add Sci-Fi Visual System to dashboard"""

        # Visual system frame
        visual_frame = ctk.CTkFrame(parent_frame)
        visual_frame.pack(side="right", padx=(10, 0), pady=10)

        # Title
        ctk.CTkLabel(visual_frame, text="🚀 AI SYSTEM STATUS",
                     font=("Orbitron", 16, "bold")).pack(pady=5)

        # Create visual system
        self.scifi_visual = SciFiVisualSystem(visual_frame)

        # Status message
        self.ai_status_label = ctk.CTkLabel(visual_frame, text="System Ready",
                                            font=("Orbitron", 12))
        self.ai_status_label.pack(pady=5)

        # Control buttons for testing
        control_frame = ctk.CTkFrame(visual_frame)
        control_frame.pack(pady=10)

        # AI action buttons
        ai_buttons = [
            ("🧠 Analyze", "analyzing"),
            ("🔍 Connect", "connecting"),
            ("📈 Buy Signal", "buy_signal"),
            ("📉 Sell Signal", "sell_signal"),
            ("⚡ Trading", "trading"),
            ("✅ Success", "success"),
            ("❌ Error", "error"),
            ("🔵 Idle", "idle")
        ]

        for i, (label, state) in enumerate(ai_buttons):
            row = i // 2
            col = i % 2

            btn = ctk.CTkButton(
                control_frame,
                text=label,
                command=lambda s=state: self.update_scifi_visual_state(s),
                width=120, height=30,
                font=("Arial", 10)
            )
            btn.grid(row=row, column=col, padx=2, pady=2)

        # Initialize with idle state
        self.scifi_visual.set_state("idle")

    def setup_trading_tab(self):
        """Enhanced trading tab with fee display"""
        # Trading controls
        control_frame = ctk.CTkFrame(self.tab_trading)
        control_frame.pack(fill="x", padx=10, pady=10)

        self.start_btn_trading = ctk.CTkButton(control_frame, text="▶️ Start Trading Bot",
                                               command=self.toggle_trading,
                                               fg_color="green", height=40, width=200)
        self.start_btn_trading.pack(side="left", padx=10)

        ctk.CTkButton(control_frame, text="📊 Check Signals",
                      command=self.check_signals,
                      height=40).pack(side="left", padx=5)

        ctk.CTkButton(control_frame, text="📋 Open Orders",
                      command=self.check_open_orders,
                      height=40).pack(side="left", padx=5)

        ctk.CTkButton(control_frame, text="💰 Fee Calculator",
                      command=self.show_fee_calculator,
                      height=40).pack(side="left", padx=5)

        # Fee information display
        fee_frame = ctk.CTkFrame(self.tab_trading)
        fee_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(fee_frame, text="💸 Bitkub Fee Structure:",
                     font=("Arial", 14, "bold")).pack(anchor="w", padx=10, pady=5)

        fee_info = ctk.CTkFrame(fee_frame)
        fee_info.pack(fill="x", padx=10, pady=5)

        fee_text = "• Maker Fee: 0.25% • Taker Fee: 0.25% • Total per round trip: 0.5%"
        ctk.CTkLabel(fee_info, text=fee_text, font=("Arial", 12),
                     text_color="yellow").pack(padx=10, pady=5)

        # Strategy settings
        strategy_frame = ctk.CTkFrame(self.tab_trading)
        strategy_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(strategy_frame, text="🎯 Profitable Strategy Settings:",
                     font=("Arial", 14, "bold")).pack(anchor="w", padx=10, pady=5)

        # Profit settings
        profit_settings = ctk.CTkFrame(strategy_frame)
        profit_settings.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(profit_settings, text="Min Profit Margin %:").pack(side="left", padx=5)
        self.min_profit_var = tk.DoubleVar(value=0.8)
        ctk.CTkSlider(profit_settings, from_=0.5, to=2.0, variable=self.min_profit_var,
                      command=self.update_strategy).pack(side="left", padx=5)
        self.min_profit_label = ctk.CTkLabel(profit_settings, text="0.8%")
        self.min_profit_label.pack(side="left", padx=5)

        # RSI settings
        rsi_frame = ctk.CTkFrame(strategy_frame)
        rsi_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(rsi_frame, text="RSI Oversold:").pack(side="left", padx=5)
        self.rsi_oversold_var = tk.IntVar(value=25)
        ctk.CTkSlider(rsi_frame, from_=15, to=35, variable=self.rsi_oversold_var,
                      command=self.update_strategy).pack(side="left", padx=5)
        self.rsi_oversold_label = ctk.CTkLabel(rsi_frame, text="25")
        self.rsi_oversold_label.pack(side="left", padx=5)

        ctk.CTkLabel(rsi_frame, text="RSI Overbought:").pack(side="left", padx=20)
        self.rsi_overbought_var = tk.IntVar(value=75)
        ctk.CTkSlider(rsi_frame, from_=65, to=85, variable=self.rsi_overbought_var,
                      command=self.update_strategy).pack(side="left", padx=5)
        self.rsi_overbought_label = ctk.CTkLabel(rsi_frame, text="75")
        self.rsi_overbought_label.pack(side="left", padx=5)

        # Risk settings
        risk_frame = ctk.CTkFrame(strategy_frame)
        risk_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(risk_frame, text="Stop Loss %:").pack(side="left", padx=5)
        self.stop_loss_var = tk.DoubleVar(value=1.5)
        ctk.CTkSlider(risk_frame, from_=0.5, to=3.0, variable=self.stop_loss_var,
                      command=self.update_strategy).pack(side="left", padx=5)
        self.stop_loss_label = ctk.CTkLabel(risk_frame, text="1.5%")
        self.stop_loss_label.pack(side="left", padx=5)

        ctk.CTkLabel(risk_frame, text="Take Profit %:").pack(side="left", padx=20)
        self.take_profit_var = tk.DoubleVar(value=2.5)
        ctk.CTkSlider(risk_frame, from_=1.0, to=5.0, variable=self.take_profit_var,
                      command=self.update_strategy).pack(side="left", padx=5)
        self.take_profit_label = ctk.CTkLabel(risk_frame, text="2.5%")
        self.take_profit_label.pack(side="left", padx=5)

        # Trading log
        self.trading_log = ctk.CTkTextbox(self.tab_trading, font=("Consolas", 10))
        self.trading_log.pack(fill="both", expand=True, padx=10, pady=10)

    def setup_api_tab(self):
        """API configuration with enhanced security notes"""
        api_frame = ctk.CTkFrame(self.tab_api)
        api_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(api_frame, text="Bitkub API Configuration",
                     font=("Arial", 18, "bold")).pack(pady=10)

        # Enhanced security warning
        warning_text = """
🔒 ENHANCED SECURITY NOTES:
• This bot supports ALL Bitkub coins with accurate fee calculation
• Fee-aware trading strategy for profitable operations
• Start with PAPER TRADING and small amounts
• Set IP whitelist in Bitkub for maximum security
• Use a dedicated trading account with limited funds
• Monitor trades closely during first runs
        """
        ctk.CTkLabel(api_frame, text=warning_text,
                     font=("Arial", 10), justify="left",
                     text_color="yellow").pack(pady=10)

        # API inputs
        ctk.CTkLabel(api_frame, text="API Key:").pack(anchor="w", padx=20, pady=5)
        self.api_key_entry = ctk.CTkEntry(api_frame, show="*", width=400)
        self.api_key_entry.pack(padx=20, pady=5)

        ctk.CTkLabel(api_frame, text="API Secret:").pack(anchor="w", padx=20, pady=5)
        self.api_secret_entry = ctk.CTkEntry(api_frame, show="*", width=400)
        self.api_secret_entry.pack(padx=20, pady=5)

        # Enhanced buttons
        btn_frame = ctk.CTkFrame(api_frame)
        btn_frame.pack(pady=20)

        ctk.CTkButton(btn_frame, text="🔐 Save & Connect",
                      command=self.connect_api,
                      fg_color="green", height=40).pack(side="left", padx=5)

        ctk.CTkButton(btn_frame, text="🔌 Test Connection",
                      command=self.test_connection,
                      height=40).pack(side="left", padx=5)

        ctk.CTkButton(btn_frame, text="🏥 Health Check",
                      command=self.api_health_check,
                      height=40).pack(side="left", padx=5)

        # Status display
        self.api_status_display = ctk.CTkTextbox(self.tab_api, font=("Consolas", 11))
        self.api_status_display.pack(fill="both", expand=True, padx=10, pady=10)

    def setup_testing_tab(self):
        """Testing tab with fee calculation testing"""
        test_frame = ctk.CTkFrame(self.tab_testing)
        test_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(test_frame, text="🧪 Enhanced Testing with Fee Calculation",
                     font=("Arial", 16, "bold")).pack(pady=10)

        # Test controls
        test_controls = ctk.CTkFrame(test_frame)
        test_controls.pack(fill="x", padx=10, pady=10)

        # Test amount
        amount_frame = ctk.CTkFrame(test_controls)
        amount_frame.pack(side="left", padx=5)

        ctk.CTkLabel(amount_frame, text="Test Amount (THB):").pack()
        self.test_amount_var = tk.IntVar(value=100)
        ctk.CTkEntry(amount_frame, textvariable=self.test_amount_var, width=80).pack()

        # Test buttons
        btn_frame = ctk.CTkFrame(test_controls)
        btn_frame.pack(side="left", padx=20)

        ctk.CTkButton(btn_frame, text="📊 Check Market Data",
                      command=self.test_market_data).pack(side="left", padx=5)

        ctk.CTkButton(btn_frame, text="💰 Check Balance",
                      command=self.test_balance).pack(side="left", padx=5)

        ctk.CTkButton(btn_frame, text="💸 Test Fee Calc",
                      command=self.test_fee_calculation).pack(side="left", padx=5)

        ctk.CTkButton(btn_frame, text="🧪 Test Buy Order",
                      command=self.test_buy_order,
                      fg_color="orange").pack(side="left", padx=5)

        # Test results
        self.test_display = ctk.CTkTextbox(self.tab_testing, font=("Consolas", 10))
        self.test_display.pack(fill="both", expand=True, padx=10, pady=10)

    def setup_history_tab(self):
        """Enhanced history tab with profit analysis"""
        control_frame = ctk.CTkFrame(self.tab_history)
        control_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkButton(control_frame, text="🔄 Refresh",
                      command=self.load_trade_history).pack(side="left", padx=5)

        ctk.CTkButton(control_frame, text="📊 Profit Statistics",
                      command=self.show_profit_statistics).pack(side="left", padx=5)

        ctk.CTkButton(control_frame, text="💸 Fee Analysis",
                      command=self.show_fee_analysis).pack(side="left", padx=5)

        ctk.CTkButton(control_frame, text="📤 Export CSV",
                      command=self.export_history).pack(side="left", padx=5)

        # History display
        self.history_display = ctk.CTkTextbox(self.tab_history, font=("Consolas", 10))
        self.history_display.pack(fill="both", expand=True, padx=10, pady=10)

    def setup_settings_tab(self):
        """Enhanced settings tab with all Bitkub coins"""
        settings_frame = ctk.CTkFrame(self.tab_settings)
        settings_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(settings_frame, text="⚙️ Enhanced Trading Configuration",
                     font=("Arial", 16, "bold")).pack(pady=10)

        # Symbol selection with all Bitkub coins
        symbol_frame = ctk.CTkFrame(settings_frame)
        symbol_frame.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(symbol_frame, text="Trading Pair:").pack(side="left", padx=5)
        self.symbol_var = tk.StringVar(value="btc_thb")

        # All Bitkub symbols for dropdown
        bitkub_symbols = [
            "btc_thb", "eth_thb", "ada_thb", "xrp_thb", "bnb_thb", "doge_thb",
            "dot_thb", "matic_thb", "atom_thb", "near_thb", "sol_thb", "sand_thb",
            "mana_thb", "avax_thb", "shib_thb", "ltc_thb", "bch_thb", "etc_thb",
            "link_thb", "uni_thb", "usdt_thb", "usdc_thb", "dai_thb", "busd_thb",
            "alpha_thb", "ftt_thb", "axie_thb", "alice_thb", "chz_thb", "jasmy_thb",
            "lrc_thb", "comp_thb", "mkr_thb", "snx_thb", "aave_thb", "grt_thb",
            "1inch_thb", "enj_thb", "gala_thb", "chr_thb", "bat_thb", "omg_thb",
            "knc_thb", "cvc_thb", "pow_thb", "iotx_thb", "wxt_thb", "zil_thb",
            "srk_thb", "six_thb", "jfin_thb", "arpa_thb", "troy_thb", "ong_thb",
            "zrx_thb", "kub_thb", "ctxc_thb", "infra_thb", "bitkub_thb"
        ]

        symbol_menu = ctk.CTkOptionMenu(symbol_frame, variable=self.symbol_var,
                                        values=bitkub_symbols)
        symbol_menu.pack(side="left", padx=5)

        ctk.CTkLabel(symbol_frame, text="(All 57 Bitkub coins supported)",
                     text_color="green").pack(side="left", padx=5)

        # Trade amount optimized for fees
        amount_frame = ctk.CTkFrame(settings_frame)
        amount_frame.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(amount_frame, text="Trade Amount (THB):").pack(side="left", padx=5)
        self.trade_amount_var = tk.IntVar(value=500)
        amount_entry = ctk.CTkEntry(amount_frame, textvariable=self.trade_amount_var, width=100)
        amount_entry.pack(side="left", padx=5)

        ctk.CTkLabel(amount_frame, text="(Minimum 500 THB recommended for profitable trading)",
                     text_color="yellow").pack(side="left", padx=5)

        # Risk limits
        risk_frame = ctk.CTkFrame(settings_frame)
        risk_frame.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(risk_frame, text="Max Daily Trades:").pack(side="left", padx=5)
        self.max_trades_var = tk.IntVar(value=3)
        ctk.CTkEntry(risk_frame, textvariable=self.max_trades_var, width=50).pack(side="left", padx=5)

        ctk.CTkLabel(risk_frame, text="Max Daily Loss (THB):").pack(side="left", padx=20)
        self.max_loss_var = tk.IntVar(value=1000)
        ctk.CTkEntry(risk_frame, textvariable=self.max_loss_var, width=100).pack(side="left", padx=5)

        # Fee impact display
        fee_impact_frame = ctk.CTkFrame(settings_frame)
        fee_impact_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(fee_impact_frame, text="💸 Fee Impact Analysis:",
                     font=("Arial", 12, "bold")).pack(anchor="w", padx=10)

        self.fee_impact_label = ctk.CTkLabel(fee_impact_frame,
                                             text="Configure amount to see fee impact",
                                             font=("Arial", 10))
        self.fee_impact_label.pack(anchor="w", padx=20, pady=5)

        # Update fee impact when amount changes
        self.trade_amount_var.trace('w', self.update_fee_impact)

        # Save button
        ctk.CTkButton(settings_frame, text="💾 Save Settings",
                      command=self.save_settings,
                      fg_color="green", height=40).pack(pady=20)

    # === Enhanced Core Functions ===

    def update_scifi_visual_state(self, state, message=""):
        """Update Sci-Fi visual system state"""
        if hasattr(self, 'scifi_visual'):
            self.scifi_visual.set_state(state)

        # Update status label
        if hasattr(self, 'ai_status_label'):
            status_messages = {
                "idle": "System Ready",
                "connecting": "Connecting to API...",
                "analyzing": "Analyzing Market...",
                "buy_signal": "Buy Signal Detected!",
                "sell_signal": "Sell Signal Detected!",
                "trading": "Active Trading...",
                "success": "Operation Successful!",
                "error": "System Error!"
            }
            self.ai_status_label.configure(text=status_messages.get(state, "Unknown State"))

        # Log the visual state change
        if message:
            self.log(f"🎬 Visual State: {state.upper()} - {message}")

    def connect_api(self):
        """Enhanced API connection with visual feedback"""
        api_key = self.api_key_entry.get().strip()
        api_secret = self.api_secret_entry.get().strip()

        if not api_key or not api_secret:
            messagebox.showwarning("Error", "Please enter API credentials")
            return

        # Visual feedback
        self.update_scifi_visual_state("connecting", "Establishing API connection")

        # Create enhanced API client
        self.api_client = ImprovedBitkubAPI(api_key, api_secret)

        # Create strategy with API client
        self.strategy = ProfitableTradingStrategy(self.api_client)

        self.log("🔌 Connecting to Enhanced API...")

        def test_connection():
            time.sleep(1)

            # Check system status first
            status_ok, status_msg = self.api_client.check_system_status()
            if not status_ok:
                self.update_scifi_visual_state("error", f"System status issue: {status_msg}")
                self.log(f"❌ System status issue: {status_msg}")
                messagebox.showwarning("System Status", f"API Status Issue: {status_msg}")
                return

            # Test balance check
            balance = self.api_client.check_balance()
            if balance and balance.get('error') == 0:
                self.update_scifi_visual_state("success", "API connected successfully")
                self.log("✅ Enhanced API Connected successfully")
                self.update_balance()
                self.status_cards["System Status"].configure(text="Connected", text_color="green")
                messagebox.showinfo("Success", "Enhanced API Connected and validated!")

                # Auto return to idle after 2 seconds
                threading.Timer(2.0, lambda: self.update_scifi_visual_state("idle")).start()
            else:
                error_msg = "Unknown error"
                if balance:
                    error_code = balance.get("error", 999)
                    error_msg = self.api_client.error_codes.get(error_code, f"Error {error_code}")

                self.update_scifi_visual_state("error", f"Connection failed: {error_msg}")
                self.log(f"❌ API Connection failed: {error_msg}")
                messagebox.showerror("Error", f"Failed to connect: {error_msg}")
                self.status_cards["System Status"].configure(text="Failed", text_color="red")

        threading.Thread(target=test_connection, daemon=True).start()

    def toggle_trading(self):
        """Enhanced trading toggle with visual feedback"""
        if not self.is_trading:
            if not self.api_client or not self.strategy:
                messagebox.showwarning("Error", "Please connect API first")
                return

            # Pre-flight checks
            if not self.pre_flight_check():
                return

            if not self.is_paper_trading:
                if not messagebox.askyesno("Start Real Trading",
                                           f"Start trading with REAL money?\n\n" +
                                           f"Amount per trade: {self.config['trade_amount_thb']} THB\n" +
                                           f"Max daily trades: {self.config['max_daily_trades']}\n" +
                                           f"Symbol: {self.config['symbol'].upper()}\n" +
                                           f"Fee per round trip: {self.api_client.trading_fees['maker_fee'] + self.api_client.trading_fees['taker_fee']:.2%}"):
                    return

            self.is_trading = True
            self.emergency_stop = False
            self.start_btn.configure(text="⏹️ Stop Trading Bot", fg_color="red")
            self.start_btn_trading.configure(text="⏹️ Stop Trading Bot", fg_color="red")

            self.update_scifi_visual_state("analyzing", "Starting trading analysis")
            self.log(f"🚀 Started Enhanced {'PAPER' if self.is_paper_trading else 'REAL'} trading")

            # Start enhanced trading thread
            threading.Thread(target=self.enhanced_trading_loop, daemon=True).start()
        else:
            self.is_trading = False
            self.start_btn.configure(text="▶️ Start Trading Bot", fg_color="green")
            self.start_btn_trading.configure(text="▶️ Start Trading Bot", fg_color="green")

            self.update_scifi_visual_state("idle", "Trading stopped")
            self.log("🛑 Stopped trading")

    def enhanced_trading_loop(self):
        """Enhanced trading loop with fee-aware strategy"""
        consecutive_errors = 0
        max_consecutive_errors = 5

        while self.is_trading and not self.emergency_stop:
            try:
                # Check daily limits
                if self.daily_trades >= self.config['max_daily_trades']:
                    self.log(f"📊 Daily trade limit reached ({self.daily_trades}/{self.config['max_daily_trades']})")
                    time.sleep(3600)  # Wait 1 hour
                    continue

                if self.daily_pnl <= -self.config['max_daily_loss']:
                    self.log(f"💸 Daily loss limit reached ({self.daily_pnl:.2f}/{-self.config['max_daily_loss']})")
                    self.emergency_stop_trading()
                    break

                # Check minimum trade interval
                if self.last_trade_time:
                    time_since_trade = (datetime.now() - self.last_trade_time).seconds
                    if time_since_trade < self.config['min_trade_interval']:
                        time.sleep(30)
                        continue

                # Visual feedback for analysis
                self.update_scifi_visual_state("analyzing", "Analyzing market conditions")

                # Get market data
                ticker = self.api_client.get_simple_ticker(self.config['symbol'])
                if not ticker:
                    consecutive_errors += 1
                    if consecutive_errors >= max_consecutive_errors:
                        self.log("❌ Too many consecutive errors, stopping")
                        self.update_scifi_visual_state("error", "Too many API errors")
                        break
                    time.sleep(60)
                    continue

                current_price = ticker['last_price']
                volume_24h = ticker.get('volume_24h', 0)

                # Reset error counter on success
                consecutive_errors = 0

                # Get balance for buy decisions
                balance = self.api_client.check_balance()
                thb_balance = 0
                if balance and balance.get('error') == 0:
                    thb_balance = float(balance['result'].get('THB', 0))

                # Check for buy signal with fee consideration
                should_buy, buy_reason = self.strategy.should_buy_profitable(
                    current_price, volume_24h, thb_balance, self.config['trade_amount_thb']
                )

                if should_buy:
                    self.update_scifi_visual_state("buy_signal", f"Buy signal: {buy_reason}")
                    self.execute_enhanced_buy(current_price, buy_reason)

                # Check for sell signal
                if self.strategy.position:
                    should_sell, sell_reason = self.strategy.should_sell_profitable(current_price, volume_24h)
                    if should_sell:
                        if "Profit" in sell_reason or "profit" in sell_reason:
                            self.update_scifi_visual_state("success", f"Profitable sell: {sell_reason}")
                        else:
                            self.update_scifi_visual_state("sell_signal", f"Sell signal: {sell_reason}")
                        self.execute_enhanced_sell(current_price, sell_reason)

                # Update display
                self.update_enhanced_dashboard()

                # Return to idle if no active trading
                if not self.strategy.position:
                    self.update_scifi_visual_state("idle", "Monitoring market")

                # Wait before next check
                time.sleep(30)

            except Exception as e:
                consecutive_errors += 1
                self.log(f"❌ Trading loop error: {e}")
                self.update_scifi_visual_state("error", f"Trading error: {str(e)[:50]}")
                if consecutive_errors >= max_consecutive_errors:
                    self.log("❌ Too many errors, stopping trading")
                    break
                time.sleep(60)

        self.log("🛑 Enhanced trading loop ended")
        self.update_scifi_visual_state("idle", "Trading ended")

    def execute_enhanced_buy(self, price, reason):
        """Enhanced buy execution with fee calculation"""
        try:
            amount_thb = self.config['trade_amount_thb']
            crypto_amount = amount_thb / price

            # Calculate expected fees
            expected_buy_fee = self.api_client.calculate_trading_fees(crypto_amount, price, "buy")
            break_even_price = self.api_client.calculate_break_even_price(price, "buy")

            self.update_scifi_visual_state("trading", f"Executing buy order: {amount_thb} THB")

            if self.is_paper_trading:
                # Paper trading
                self.strategy.position = {
                    'entry_price': price,
                    'amount': crypto_amount,
                    'entry_time': datetime.now()
                }

                self.log(f"📝 PAPER BUY: {amount_thb} THB @ {price:.2f}")
                self.log(f"   Reason: {reason}")
                self.log(f"   Expected fee: {expected_buy_fee:.2f} THB")
                self.log(f"   Break-even price: {break_even_price:.2f} THB")

                self.save_enhanced_trade('buy', crypto_amount, price, amount_thb,
                                         'PAPER', 0, expected_buy_fee, 0, reason, True)
            else:
                # Real trading with fee-optimized pricing
                buy_price = price * 1.002  # Small buffer for execution

                self.log(f"💰 REAL BUY: {amount_thb} THB @ {buy_price:.2f}")

                result = self.api_client.place_buy_order_safe(
                    self.config['symbol'], amount_thb, buy_price, 'limit'
                )

                if result and result.get('error') == 0:
                    order_info = result['result']
                    order_id = order_info.get('id', 'unknown')
                    actual_amount = order_info.get('rec', crypto_amount)
                    actual_fee = order_info.get('fee', expected_buy_fee)

                    self.strategy.position = {
                        'entry_price': buy_price,
                        'amount': actual_amount,
                        'entry_time': datetime.now(),
                        'order_id': order_id
                    }

                    self.log(f"✅ REAL BUY SUCCESS: Order ID {order_id}")
                    self.log(f"   Amount: {actual_amount:.8f} crypto")
                    self.log(f"   Fee: {actual_fee:.2f} THB")

                    self.total_fees_paid += actual_fee
                    self.save_enhanced_trade('buy', actual_amount, buy_price, amount_thb,
                                             order_id, 0, actual_fee, 0, reason, False)

                    self.update_scifi_visual_state("success", "Buy order executed successfully")
                else:
                    error_code = result.get("error", 999) if result else 999
                    error_msg = self.api_client.error_codes.get(error_code, f"Error {error_code}")
                    self.log(f"❌ Buy order failed: {error_msg}")
                    self.update_scifi_visual_state("error", f"Buy failed: {error_msg}")
                    return

            self.daily_trades += 1
            self.last_trade_time = datetime.now()
            self.status_cards["Position"].configure(text=f"LONG @ {price:.2f}")
            self.status_cards["Daily Trades"].configure(
                text=f"{self.daily_trades}/{self.config['max_daily_trades']}"
            )

        except Exception as e:
            self.log(f"❌ Buy execution error: {e}")
            self.update_scifi_visual_state("error", f"Buy error: {str(e)[:50]}")

    def execute_enhanced_sell(self, price, reason):
        """Enhanced sell execution with fee calculation"""
        try:
            if not self.strategy.position:
                return

            amount = self.strategy.position['amount']
            entry_price = self.strategy.position['entry_price']

            # Calculate comprehensive P&L including fees
            buy_fee = self.api_client.calculate_trading_fees(amount, entry_price, "buy")
            sell_fee = self.api_client.calculate_trading_fees(amount, price, "sell")
            gross_pnl = (price - entry_price) * amount
            net_pnl = gross_pnl - buy_fee - sell_fee

            self.update_scifi_visual_state("trading", f"Executing sell order: {amount:.6f}")

            if self.is_paper_trading:
                # Paper trading
                self.log(f"📝 PAPER SELL: {amount:.8f} @ {price:.2f}")
                self.log(f"   Reason: {reason}")
                self.log(f"   Gross P&L: {gross_pnl:.2f} THB")
                self.log(f"   Fees: {buy_fee + sell_fee:.2f} THB")
                self.log(f"   Net P&L: {net_pnl:.2f} THB")

                self.save_enhanced_trade('sell', amount, price, amount * price,
                                         'PAPER', net_pnl, sell_fee, net_pnl, reason, True)
            else:
                # Real trading
                sell_price = price * 0.998  # Small buffer for execution

                self.log(f"💰 REAL SELL: {amount:.8f} @ {sell_price:.2f}")

                result = self.api_client.place_sell_order_safe(
                    self.config['symbol'], amount, sell_price, 'limit'
                )

                if result and result.get('error') == 0:
                    order_info = result['result']
                    order_id = order_info.get('id', 'unknown')
                    actual_fee = order_info.get('fee', sell_fee)

                    # Recalculate with actual sell price and fee
                    actual_gross_pnl = (sell_price - entry_price) * amount
                    actual_net_pnl = actual_gross_pnl - buy_fee - actual_fee

                    self.log(f"✅ REAL SELL SUCCESS: Order ID {order_id}")
                    self.log(f"   Net P&L: {actual_net_pnl:.2f} THB")
                    self.log(f"   Total fees: {buy_fee + actual_fee:.2f} THB")

                    self.total_fees_paid += actual_fee
                    self.save_enhanced_trade('sell', amount, sell_price, amount * sell_price,
                                             order_id, actual_net_pnl, actual_fee,
                                             actual_net_pnl, reason, False)
                    net_pnl = actual_net_pnl

                    if net_pnl > 0:
                        self.update_scifi_visual_state("success", f"Profitable sell: +{net_pnl:.2f} THB")
                    else:
                        self.update_scifi_visual_state("error", f"Loss sell: {net_pnl:.2f} THB")
                else:
                    error_code = result.get("error", 999) if result else 999
                    error_msg = self.api_client.error_codes.get(error_code, f"Error {error_code}")
                    self.log(f"❌ Sell order failed: {error_msg}")
                    self.update_scifi_visual_state("error", f"Sell failed: {error_msg}")
                    return

            self.daily_pnl += net_pnl
            self.strategy.position = None
            self.status_cards["Position"].configure(text="None")
            self.status_cards["Daily P&L"].configure(text=f"{self.daily_pnl:.2f}")
            self.status_cards["Total Fees"].configure(text=f"{self.total_fees_paid:.2f}")

            # Calculate net profit
            net_profit = self.daily_pnl - self.total_fees_paid
            self.status_cards["Net Profit"].configure(text=f"{net_profit:.2f}")

        except Exception as e:
            self.log(f"❌ Sell execution error: {e}")
            self.update_scifi_visual_state("error", f"Sell error: {str(e)[:50]}")

    def save_enhanced_trade(self, side, amount, price, total_thb, order_id, pnl, fees, net_pnl, reason, is_paper):
        """Save trade with enhanced fee tracking"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Calculate additional metrics
            rsi = 50
            volume_momentum = 1.0
            break_even_price = 0

            if self.strategy and len(self.strategy.price_history) >= 15:
                rsi = self.strategy.calculate_rsi(list(self.strategy.price_history))

            if self.strategy and len(self.strategy.volume_history) >= 2:
                volume_momentum = self.strategy.calculate_volume_momentum(
                    self.strategy.volume_history[-1]
                )

            if self.api_client and side == "buy":
                break_even_price = self.api_client.calculate_break_even_price(price, "buy")

            cursor.execute('''
                INSERT INTO trades 
                (timestamp, symbol, side, amount, price, total_thb, 
                 order_id, status, pnl, fees, net_pnl, reason, is_paper,
                 rsi, volume_momentum, break_even_price, api_response)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (datetime.now(), self.config['symbol'], side, amount, price,
                  total_thb, order_id, 'completed', pnl, fees, net_pnl, reason,
                  is_paper, rsi, volume_momentum, break_even_price, None))

            conn.commit()
            conn.close()

        except Exception as e:
            self.log(f"❌ Database error: {e}")

    # === Additional Enhanced Functions ===

    def show_fee_calculator(self):
        """Show comprehensive fee calculator"""
        if not self.api_client:
            messagebox.showwarning("Error", "Please connect API first")
            return

        ticker = self.api_client.get_simple_ticker(self.config['symbol'])
        if not ticker:
            messagebox.showwarning("Error", "Cannot get current price")
            return

        current_price = ticker['last_price']
        trade_amount = self.config['trade_amount_thb']
        crypto_amount = trade_amount / current_price

        # Calculate all fees
        buy_fee = self.api_client.calculate_trading_fees(crypto_amount, current_price, "buy")
        sell_fee = self.api_client.calculate_trading_fees(crypto_amount, current_price, "sell")
        total_fees = buy_fee + sell_fee
        break_even_price = self.api_client.calculate_break_even_price(current_price, "buy")

        fee_info = f"""
💸 BITKUB FEE CALCULATOR

📊 Current Market:
• Symbol: {self.config['symbol'].upper()}
• Current Price: {current_price:,.2f} THB
• Trade Amount: {trade_amount:,.0f} THB
• Crypto Amount: {crypto_amount:.8f}

💰 Fee Breakdown:
• Buy Fee (0.25%): {buy_fee:.2f} THB
• Sell Fee (0.25%): {sell_fee:.2f} THB
• Total Fees: {total_fees:.2f} THB
• Fee Percentage: {(total_fees / trade_amount) * 100:.3f}%

⚖️ Break-Even Analysis:
• Break-Even Price: {break_even_price:,.2f} THB
• Required Gain: {((break_even_price - current_price) / current_price) * 100:.3f}%
• Minimum Profit Target: {break_even_price * 1.005:,.2f} THB (+0.5%)

📈 Profit Scenarios:
• +1% price = {current_price * 1.01 * crypto_amount - trade_amount - total_fees:.2f} THB net
• +2% price = {current_price * 1.02 * crypto_amount - trade_amount - total_fees:.2f} THB net
• +3% price = {current_price * 1.03 * crypto_amount - trade_amount - total_fees:.2f} THB net
• +5% price = {current_price * 1.05 * crypto_amount - trade_amount - total_fees:.2f} THB net
        """

        messagebox.showinfo("Fee Calculator", fee_info)

    def test_fee_calculation(self):
        """Test fee calculation system"""
        if not self.api_client:
            self.test_log("❌ Please connect API first")
            return

        try:
            test_amount = self.test_amount_var.get()
        except:
            test_amount = 100
            self.test_amount_var.set(test_amount)

        self.test_log(f"💸 Testing fee calculation for {test_amount} THB")

        ticker = self.api_client.get_simple_ticker(self.config['symbol'])
        if ticker:
            price = ticker['last_price']
            crypto_amount = test_amount / price

            # Test all fee calculations
            buy_fee = self.api_client.calculate_trading_fees(crypto_amount, price, "buy")
            sell_fee = self.api_client.calculate_trading_fees(crypto_amount, price, "sell")
            total_fees = self.api_client.calculate_trading_fees(crypto_amount, price, "both")
            break_even = self.api_client.calculate_break_even_price(price, "buy")

            self.test_log(f"✅ Fee calculation results:")
            self.test_log(f"   Current price: {price:,.2f} THB")
            self.test_log(f"   Crypto amount: {crypto_amount:.8f}")
            self.test_log(f"   Buy fee: {buy_fee:.2f} THB ({(buy_fee / test_amount) * 100:.3f}%)")
            self.test_log(f"   Sell fee: {sell_fee:.2f} THB ({(sell_fee / (crypto_amount * price)) * 100:.3f}%)")
            self.test_log(f"   Total fees: {total_fees:.2f} THB")
            self.test_log(f"   Break-even price: {break_even:,.2f} THB")
            self.test_log(f"   Required gain: {((break_even - price) / price) * 100:.3f}%")

            # Test profitability scenarios
            self.test_log(f"📊 Profitability scenarios:")
            for pct in [0.5, 1.0, 1.5, 2.0, 3.0]:
                sell_price = price * (1 + pct / 100)
                gross_profit = (sell_price - price) * crypto_amount
                net_profit = gross_profit - buy_fee - sell_fee
                self.test_log(f"   +{pct}% → Net profit: {net_profit:+.2f} THB")
        else:
            self.test_log("❌ Failed to get price data")

    def update_fee_impact(self, *args):
        """Update fee impact display when trade amount changes"""
        try:
            amount = self.trade_amount_var.get()
            if amount > 0 and self.api_client:
                # Get current price for calculation
                ticker = self.api_client.get_simple_ticker(self.config['symbol'])
                if ticker:
                    price = ticker['last_price']
                    crypto_amount = amount / price
                    total_fees = self.api_client.calculate_trading_fees(crypto_amount, price, "both")
                    fee_pct = (total_fees / amount) * 100
                    break_even = self.api_client.calculate_break_even_price(price, "buy")
                    required_gain = ((break_even - price) / price) * 100

                    impact_text = f"Amount: {amount} THB → Fees: {total_fees:.2f} THB ({fee_pct:.3f}%) → Need: +{required_gain:.3f}% to break even"

                    if required_gain < 1.0:
                        color = "green"
                    elif required_gain < 1.5:
                        color = "yellow"
                    else:
                        color = "red"

                    self.fee_impact_label.configure(text=impact_text, text_color=color)
                else:
                    self.fee_impact_label.configure(text="Cannot get current price for calculation")
            else:
                self.fee_impact_label.configure(text="Enter valid amount and connect API")
        except:
            self.fee_impact_label.configure(text="Error calculating fee impact")

    def show_profit_statistics(self):
        """Show enhanced profit statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Comprehensive profit analysis
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN net_pnl > 0 THEN 1 ELSE 0 END) as profitable_trades,
                    SUM(CASE WHEN net_pnl < 0 THEN 1 ELSE 0 END) as losing_trades,
                    SUM(net_pnl) as total_net_pnl,
                    SUM(fees) as total_fees_paid,
                    AVG(net_pnl) as avg_net_pnl,
                    MAX(net_pnl) as best_trade,
                    MIN(net_pnl) as worst_trade,
                    AVG(rsi) as avg_rsi,
                    AVG(volume_momentum) as avg_volume_momentum
                FROM trades
                WHERE side = 'sell' AND net_pnl IS NOT NULL
            ''')

            stats = cursor.fetchone()
            conn.close()

            if stats and stats[0] > 0:
                total, profitable, losing, total_pnl, total_fees, avg_pnl, best, worst, avg_rsi, avg_vol = stats
                win_rate = (profitable / total * 100) if total > 0 else 0

                # Calculate profit factor
                positive_trades = cursor.execute(
                    'SELECT SUM(net_pnl) FROM trades WHERE net_pnl > 0 AND side = "sell"'
                ).fetchone()[0] or 0
                negative_trades = cursor.execute(
                    'SELECT SUM(ABS(net_pnl)) FROM trades WHERE net_pnl < 0 AND side = "sell"'
                ).fetchone()[0] or 1

                profit_factor = positive_trades / negative_trades if negative_trades > 0 else float('inf')
                net_after_fees = total_pnl

                stats_text = f"""
=== ENHANCED PROFIT ANALYSIS ===

💰 Financial Performance:
• Total Net P&L: {total_pnl:+.2f} THB
• Total Fees Paid: {total_fees:.2f} THB
• Net After All Costs: {net_after_fees:+.2f} THB
• Average per Trade: {avg_pnl:+.2f} THB
• Best Trade: {best:+.2f} THB
• Worst Trade: {worst:+.2f} THB

📊 Trading Statistics:
• Total Completed Trades: {total}
• Profitable Trades: {profitable} ({win_rate:.1f}%)
• Losing Trades: {losing}
• Profit Factor: {profit_factor:.2f}

📈 Strategy Metrics:
• Average RSI at Entry: {avg_rsi:.1f}
• Average Volume Momentum: {avg_vol:.2f}x
• Fee Efficiency: {(total_fees / abs(total_pnl) * 100) if total_pnl != 0 else 0:.1f}%

🎯 Performance Rating:"""

                if win_rate >= 60 and net_after_fees > total_fees:
                    stats_text += "\n✅ EXCELLENT - Highly profitable strategy"
                elif win_rate >= 50 and net_after_fees > 0:
                    stats_text += "\n⚠️ GOOD - Profitable but can improve"
                elif net_after_fees > -total_fees:
                    stats_text += "\n⚠️ FAIR - Near break-even, needs optimization"
                else:
                    stats_text += "\n❌ POOR - Strategy needs major revision"

                messagebox.showinfo("Enhanced Profit Statistics", stats_text)
            else:
                messagebox.showinfo("Statistics", "No completed trades found.")

        except Exception as e:
            self.log(f"❌ Error showing profit statistics: {e}")

    def show_fee_analysis(self):
        """Show comprehensive fee analysis"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT 
                    SUM(fees) as total_fees,
                    COUNT(*) as total_trades,
                    AVG(fees) as avg_fee_per_trade,
                    SUM(total_thb) as total_volume,
                    SUM(net_pnl) as total_net_pnl
                FROM trades
                WHERE fees IS NOT NULL
            ''')

            fee_stats = cursor.fetchone()
            conn.close()

            if fee_stats and fee_stats[0]:
                total_fees, trades, avg_fee, total_volume, net_pnl = fee_stats
                fee_rate = (total_fees / total_volume * 100) if total_volume > 0 else 0
                fee_impact = (total_fees / abs(net_pnl) * 100) if net_pnl != 0 else 0

                fee_analysis = f"""
💸 COMPREHENSIVE FEE ANALYSIS

📊 Fee Overview:
• Total Fees Paid: {total_fees:.2f} THB
• Total Trades: {trades}
• Average Fee per Trade: {avg_fee:.2f} THB
• Total Trading Volume: {total_volume:.2f} THB
• Effective Fee Rate: {fee_rate:.3f}%

💰 Impact Analysis:
• Total Net P&L: {net_pnl:+.2f} THB
• Fees as % of P&L: {fee_impact:.1f}%
• Net Profit After Fees: {net_pnl - total_fees:+.2f} THB

🎯 Fee Efficiency:
• Bitkub Standard Rate: 0.5% per round trip
• Your Effective Rate: {fee_rate:.3f}%
• Fee Optimization: {'✅ Good' if fee_rate <= 0.55 else '⚠️ Check execution'}

💡 Recommendations:"""

                if fee_impact < 20:
                    fee_analysis += "\n✅ Fee impact is reasonable for your strategy"
                elif fee_impact < 50:
                    fee_analysis += "\n⚠️ Fees are significant, consider larger trades"
                else:
                    fee_analysis += "\n❌ Fees are eating profits, increase trade size"

                messagebox.showinfo("Fee Analysis", fee_analysis)
            else:
                messagebox.showinfo("Fee Analysis", "No fee data available yet.")

        except Exception as e:
            self.log(f"❌ Error in fee analysis: {e}")

    # === Rest of the enhanced functions ===

    def emergency_stop_trading(self):
        """Enhanced emergency stop with visual feedback"""
        self.update_scifi_visual_state("error", "EMERGENCY STOP ACTIVATED")
        if hasattr(self, 'scifi_visual'):
            self.scifi_visual.flash_effect("#ff0000", 0.5)

        self.emergency_stop = True
        self.is_trading = False
        self.start_btn.configure(text="▶️ Start Trading Bot", fg_color="green")
        self.start_btn_trading.configure(text="▶️ Start Trading Bot", fg_color="green")

        self.log("🚨 EMERGENCY STOP ACTIVATED!")

        # Cancel all open orders if real trading
        if not self.is_paper_trading and self.api_client:
            try:
                self.log("🗑️ Cancelling all open orders...")
                orders = self.api_client.get_my_open_orders_safe(self.config['symbol'])
                if orders and orders.get('error') == 0:
                    order_list = orders.get('result', [])
                    for order in order_list:
                        result = self.api_client.cancel_order_safe(
                            self.config['symbol'],
                            order['id'],
                            order['side']
                        )
                        if result.get('error') == 0:
                            self.log(f"✅ Cancelled order {order['id']}")
                        else:
                            self.log(f"❌ Failed to cancel order {order['id']}")
            except Exception as e:
                self.log(f"❌ Error during emergency stop: {e}")

        messagebox.showwarning("Emergency Stop", "All trading stopped and orders cancelled!")

    def toggle_paper_trading(self):
        """Enhanced paper trading toggle with visual feedback"""
        if self.paper_switch.get():
            # Multiple confirmations for real trading
            if not messagebox.askyesno("⚠️ WARNING - Real Trading",
                                       "Enable REAL MONEY trading?\n\n" +
                                       f"• Trading amount: {self.config['trade_amount_thb']} THB per trade\n" +
                                       f"• Fee per round trip: 0.5%\n" +
                                       f"• All {len(self.api_client.all_bitkub_symbols) if self.api_client else 57} Bitkub coins supported\n\n" +
                                       "Have you tested thoroughly with paper trading?"):
                self.paper_switch.deselect()
                return

            if not messagebox.askyesno("⚠️ FINAL CONFIRMATION",
                                       "This is your FINAL warning!\n\n" +
                                       "Real money will be at risk.\n" +
                                       "Are you using a small test amount?\n" +
                                       "Do you accept full responsibility?"):
                self.paper_switch.deselect()
                return

            self.is_paper_trading = False
            self.status_cards["Mode"].configure(text="REAL TRADING", text_color="red")
            self.update_scifi_visual_state("error", "REAL TRADING MODE ACTIVATED")
            self.log("⚠️ REAL TRADING ENABLED - USE EXTREME CAUTION!")

        else:
            self.is_paper_trading = True
            self.status_cards["Mode"].configure(text="PAPER TRADING", text_color="orange")
            self.update_scifi_visual_state("idle", "Paper trading mode")
            self.log("📝 Switched to Paper Trading")

    def update_enhanced_dashboard(self):
        """Enhanced dashboard update with comprehensive info"""
        # Update all status cards
        self.status_cards["Daily Trades"].configure(
            text=f"{self.daily_trades}/{self.config['max_daily_trades']}"
        )
        self.status_cards["Daily P&L"].configure(text=f"{self.daily_pnl:.2f}")
        self.status_cards["Total Fees"].configure(text=f"{self.total_fees_paid:.2f}")

        net_profit = self.daily_pnl - self.total_fees_paid
        self.status_cards["Net Profit"].configure(text=f"{net_profit:.2f}")

        # Update balance and display
        self.update_balance()

    def update_balance(self):
        """Enhanced balance update with fee tracking"""
        if not self.api_client:
            return

        balance = self.api_client.check_balance()
        if balance and balance.get('error') == 0:
            thb_balance = float(balance['result'].get('THB', 0))
            self.status_cards["Balance THB"].configure(text=f"{thb_balance:,.2f}")

            # Get crypto balance
            symbol_base = self.config['symbol'].split('_')[0].upper()
            crypto_balance = float(balance['result'].get(symbol_base, 0))

            display_text = f"💰 ENHANCED ACCOUNT OVERVIEW\n"
            display_text += f"{'=' * 50}\n"
            display_text += f"THB Balance: {thb_balance:,.2f}\n"
            display_text += f"{symbol_base} Balance: {crypto_balance:.8f}\n\n"

            # Position information with fee analysis
            if self.strategy and self.strategy.position:
                entry_price = self.strategy.position['entry_price']
                amount = self.strategy.position['amount']
                entry_time = self.strategy.position['entry_time']

                # Get current price for live P&L
                ticker = self.api_client.get_simple_ticker(self.config['symbol'])
                if ticker:
                    current_price = ticker['last_price']

                    # Calculate live P&L with fees
                    buy_fee = self.api_client.calculate_trading_fees(amount, entry_price, "buy")
                    sell_fee = self.api_client.calculate_trading_fees(amount, current_price, "sell")
                    gross_pnl = (current_price - entry_price) * amount
                    net_pnl = gross_pnl - buy_fee - sell_fee
                    net_pnl_pct = net_pnl / (entry_price * amount) * 100

                    break_even_price = self.api_client.calculate_break_even_price(entry_price, "buy")

                    display_text += f"📈 CURRENT POSITION\n"
                    display_text += f"{'=' * 30}\n"
                    display_text += f"Entry Price: {entry_price:,.2f} THB\n"
                    display_text += f"Current Price: {current_price:,.2f} THB\n"
                    display_text += f"Amount: {amount:.8f} {symbol_base}\n"
                    display_text += f"Break-Even: {break_even_price:,.2f} THB\n"
                    display_text += f"Gross P&L: {gross_pnl:+.2f} THB\n"
                    display_text += f"Est. Fees: {buy_fee + sell_fee:.2f} THB\n"
                    display_text += f"Net P&L: {net_pnl:+.2f} THB ({net_pnl_pct:+.2f}%)\n"
                    display_text += f"Hold Time: {(datetime.now() - entry_time).seconds // 60} min\n\n"

            # Enhanced daily statistics
            display_text += f"📊 TODAY'S PERFORMANCE\n"
            display_text += f"{'=' * 30}\n"
            display_text += f"Trades: {self.daily_trades}/{self.config['max_daily_trades']}\n"
            display_text += f"Daily P&L: {self.daily_pnl:+.2f} THB\n"
            display_text += f"Fees Paid: {self.total_fees_paid:.2f} THB\n"
            display_text += f"Net Profit: {self.daily_pnl - self.total_fees_paid:+.2f} THB\n"
            display_text += f"Mode: {'PAPER' if self.is_paper_trading else 'REAL'} TRADING\n\n"

            # Market overview
            ticker = self.api_client.get_simple_ticker(self.config['symbol'])
            if ticker:
                current_price = ticker['last_price']
                change_24h = ticker.get('change_24h', 0)
                volume_24h = ticker.get('volume_24h', 0)

                break_even = self.api_client.calculate_break_even_price(current_price, "buy")
                required_gain = ((break_even - current_price) / current_price) * 100

                display_text += f"📈 MARKET STATUS\n"
                display_text += f"{'=' * 30}\n"
                display_text += f"Symbol: {self.config['symbol'].upper()}\n"
                display_text += f"Current Price: {current_price:,.2f} THB\n"
                display_text += f"24h Change: {change_24h:+.2f}%\n"
                display_text += f"24h Volume: {volume_24h:,.0f} THB\n"
                display_text += f"Break-Even: {break_even:,.2f} THB\n"
                display_text += f"Required Gain: {required_gain:.3f}%\n"

                if required_gain < 0.8:
                    display_text += "✅ Low fee impact - Good for trading\n"
                elif required_gain < 1.2:
                    display_text += "⚠️ Moderate fee impact\n"
                else:
                    display_text += "❌ High fee impact - Wait for better opportunity\n"

            self.dashboard_display.delete("1.0", "end")
            self.dashboard_display.insert("1.0", display_text)

    def check_signals(self):
        """Enhanced signal checking with fee consideration"""
        if not self.api_client or not self.strategy:
            messagebox.showwarning("Error", "Please connect API first")
            return

        self.update_scifi_visual_state("analyzing", "Analyzing market signals")

        ticker = self.api_client.get_simple_ticker(self.config['symbol'])
        if ticker and len(self.strategy.price_history) >= 15:
            price = ticker['last_price']
            volume = ticker.get('volume_24h', 0)

            # Get balance for buy signal analysis
            balance = self.api_client.check_balance()
            thb_balance = 0
            if balance and balance.get('error') == 0:
                thb_balance = float(balance['result'].get('THB', 0))

            signal_text = f"\n📊 ENHANCED SIGNAL ANALYSIS - {datetime.now().strftime('%H:%M:%S')}\n"
            signal_text += f"{'=' * 60}\n"
            signal_text += f"Symbol: {ticker['symbol']}\n"
            signal_text += f"Current Price: {price:,.2f} THB\n"
            signal_text += f"24h Change: {ticker['change_24h']:+.2f}%\n"
            signal_text += f"24h Volume: {volume:,.0f} THB\n"
            signal_text += f"Available Balance: {thb_balance:,.2f} THB\n\n"

            # Fee analysis
            trade_amount = self.config['trade_amount_thb']
            crypto_amount = trade_amount / price
            total_fees = self.api_client.calculate_trading_fees(crypto_amount, price, "both")
            break_even_price = self.api_client.calculate_break_even_price(price, "buy")
            required_gain = ((break_even_price - price) / price) * 100

            signal_text += f"💸 FEE ANALYSIS:\n"
            signal_text += f"   Trade Amount: {trade_amount:,.0f} THB\n"
            signal_text += f"   Total Fees: {total_fees:.2f} THB ({(total_fees / trade_amount) * 100:.3f}%)\n"
            signal_text += f"   Break-Even Price: {break_even_price:,.2f} THB\n"
            signal_text += f"   Required Gain: {required_gain:.3f}%\n"

            if required_gain < 1.0:
                signal_text += f"   ✅ Fee impact acceptable\n\n"
            else:
                signal_text += f"   ⚠️ High fee impact - consider larger trades\n\n"

            # Technical analysis
            rsi = self.strategy.calculate_rsi(list(self.strategy.price_history))
            volume_momentum = self.strategy.calculate_volume_momentum(volume)

            signal_text += f"📈 TECHNICAL INDICATORS:\n"
            signal_text += f"   RSI: {rsi:.1f} "
            if rsi < 30:
                signal_text += "(Oversold - Bullish)\n"
            elif rsi > 70:
                signal_text += "(Overbought - Bearish)\n"
            else:
                signal_text += "(Neutral)\n"

            signal_text += f"   Volume Momentum: {volume_momentum:.2f}x "
            if volume_momentum > 1.2:
                signal_text += "(High - Bullish)\n"
            elif volume_momentum < 0.8:
                signal_text += "(Low - Bearish)\n"
            else:
                signal_text += "(Normal)\n\n"

            # Buy signal analysis
            should_buy, buy_reason = self.strategy.should_buy_profitable(
                price, volume, thb_balance, trade_amount
            )

            if should_buy:
                signal_text += f"📈 🟢 BUY SIGNAL DETECTED\n"
                signal_text += f"   Reason: {buy_reason}\n"
                signal_text += f"   Entry Price: {price:,.2f} THB\n"
                signal_text += f"   Target: {break_even_price * 1.015:,.2f} THB (+1.5%)\n"
                self.update_scifi_visual_state("buy_signal", "Buy signal detected")
            else:
                signal_text += f"⏸️ NO BUY SIGNAL\n"
                signal_text += f"   Reason: {buy_reason}\n"

            # Sell signal analysis (if position exists)
            if self.strategy.position:
                should_sell, sell_reason = self.strategy.should_sell_profitable(price, volume)
                entry_price = self.strategy.position['entry_price']
                amount = self.strategy.position['amount']

                # Calculate current P&L
                buy_fee = self.api_client.calculate_trading_fees(amount, entry_price, "buy")
                sell_fee = self.api_client.calculate_trading_fees(amount, price, "sell")
                net_pnl = (price - entry_price) * amount - buy_fee - sell_fee

                signal_text += f"\n📊 CURRENT POSITION:\n"
                signal_text += f"   Entry: {entry_price:,.2f} THB\n"
                signal_text += f"   Current: {price:,.2f} THB\n"
                signal_text += f"   Unrealized P&L: {net_pnl:+.2f} THB\n"

                if should_sell:
                    signal_text += f"📉 🔴 SELL SIGNAL DETECTED\n"
                    signal_text += f"   Reason: {sell_reason}\n"
                    self.update_scifi_visual_state("sell_signal", "Sell signal detected")
                else:
                    signal_text += f"📊 HOLD POSITION\n"
                    signal_text += f"   Reason: {sell_reason}\n"
            else:
                signal_text += f"\n💼 NO POSITION\n"

            self.trading_log.insert("end", signal_text)
            self.trading_log.see("end")

        # Return to idle after analysis
        threading.Timer(3.0, lambda: self.update_scifi_visual_state("idle")).start()

    def update_strategy(self, value=None):
        """Enhanced strategy update with fee consideration"""
        if not self.strategy:
            return

        self.strategy.min_profit_margin = self.min_profit_var.get() / 100
        self.strategy.rsi_oversold = self.rsi_oversold_var.get()
        self.strategy.rsi_overbought = self.rsi_overbought_var.get()
        self.strategy.stop_loss_pct = self.stop_loss_var.get() / 100
        self.strategy.take_profit_pct = self.take_profit_var.get() / 100

        # Update labels
        self.min_profit_label.configure(text=f"{self.min_profit_var.get():.1f}%")
        self.rsi_oversold_label.configure(text=str(self.strategy.rsi_oversold))
        self.rsi_overbought_label.configure(text=str(self.strategy.rsi_overbought))
        self.stop_loss_label.configure(text=f"{self.strategy.stop_loss_pct * 100:.1f}%")
        self.take_profit_label.configure(text=f"{self.strategy.take_profit_pct * 100:.1f}%")

        # Validate settings
        if self.strategy.rsi_oversold >= self.strategy.rsi_overbought:
            self.log("⚠️ Warning: RSI oversold should be less than overbought")

        # Check if profit margins are realistic with fees
        if self.api_client:
            ticker = self.api_client.get_simple_ticker(self.config['symbol'])
            if ticker:
                price = ticker['last_price']
                break_even = self.api_client.calculate_break_even_price(price, "buy")
                required_gain = ((break_even - price) / price) * 100

                if self.strategy.min_profit_margin * 100 < required_gain:
                    self.log(
                        f"⚠️ Warning: Min profit {self.strategy.min_profit_margin * 100:.1f}% < Required {required_gain:.1f}%")

    def save_settings(self):
        """Enhanced settings save with fee validation"""
        # Validate settings before saving
        new_amount = self.trade_amount_var.get()
        new_max_trades = self.max_trades_var.get()
        new_max_loss = self.max_loss_var.get()

        warnings = []

        # Fee-based validation
        if new_amount < 300:
            warnings.append(f"Low trade amount: {new_amount} THB (may not be profitable with 0.5% fees)")
        if new_amount > 10000:
            warnings.append(f"High trade amount: {new_amount} THB")
        if new_max_trades > 10:
            warnings.append(f"High daily trade limit: {new_max_trades}")

        # Calculate fee impact for current settings
        if self.api_client:
            ticker = self.api_client.get_simple_ticker(self.symbol_var.get())
            if ticker:
                price = ticker['last_price']
                crypto_amount = new_amount / price
                total_fees = self.api_client.calculate_trading_fees(crypto_amount, price, "both")
                fee_pct = (total_fees / new_amount) * 100

                if fee_pct > 0.6:
                    warnings.append(f"High fee impact: {fee_pct:.3f}% (consider larger trades)")

        if warnings and not messagebox.askyesno("Settings Warning",
                                                "Potential issues detected:\n\n" +
                                                "\n".join(warnings) +
                                                "\n\nContinue anyway?"):
            return

        # Save settings
        self.config['symbol'] = self.symbol_var.get()
        self.config['trade_amount_thb'] = new_amount
        self.config['max_daily_trades'] = new_max_trades
        self.config['max_daily_loss'] = new_max_loss

        messagebox.showinfo("Success", "Enhanced settings saved!")
        self.log(
            f"Settings updated: Symbol={self.config['symbol']}, Amount={new_amount}, MaxTrades={new_max_trades}, MaxLoss={new_max_loss}")

        # Update fee impact display
        self.update_fee_impact()

    def pre_flight_check(self):
        """Enhanced pre-flight safety check"""
        self.update_scifi_visual_state("analyzing", "Running pre-flight check")
        self.log("🛫 Running enhanced pre-flight check...")

        # System status
        status_ok, status_msg = self.api_client.check_system_status()
        if not status_ok:
            self.log(f"❌ System not ready: {status_msg}")
            self.update_scifi_visual_state("error", f"System check failed")
            return False

        # Balance check
        balance = self.api_client.check_balance()
        if not balance or balance.get('error') != 0:
            self.log("❌ Cannot verify balance")
            self.update_scifi_visual_state("error", "Balance check failed")
            return False

        thb_balance = float(balance['result'].get('THB', 0))
        if thb_balance < self.config['trade_amount_thb']:
            self.log(f"❌ Insufficient balance: {thb_balance:.2f} < {self.config['trade_amount_thb']}")
            self.update_scifi_visual_state("error", "Insufficient balance")
            return False

        # Market data check
        ticker = self.api_client.get_simple_ticker(self.config['symbol'])
        if not ticker:
            self.log("❌ Cannot get market data")
            self.update_scifi_visual_state("error", "Market data unavailable")
            return False

        # Fee viability check
        current_price = ticker['last_price']
        crypto_amount = self.config['trade_amount_thb'] / current_price
        total_fees = self.api_client.calculate_trading_fees(crypto_amount, current_price, "both")
        break_even = self.api_client.calculate_break_even_price(current_price, "buy")
        required_gain = ((break_even - current_price) / current_price) * 100

        if required_gain > 1.5:
            self.log(f"⚠️ Warning: High fee impact - need {required_gain:.2f}% gain to break even")
            if not messagebox.askyesno("Fee Warning",
                                       f"High fee impact detected!\n\n" +
                                       f"Trade amount: {self.config['trade_amount_thb']} THB\n" +
                                       f"Total fees: {total_fees:.2f} THB\n" +
                                       f"Required gain: {required_gain:.2f}%\n\n" +
                                       f"Consider using larger trade amounts.\n" +
                                       f"Continue anyway?"):
                self.update_scifi_visual_state("error", "Fee check failed")
                return False

        self.log("✅ Enhanced pre-flight check passed")
        self.update_scifi_visual_state("success", "Pre-flight check passed")
        threading.Timer(1.0, lambda: self.update_scifi_visual_state("idle")).start()
        return True

    def system_health_check(self):
        """Comprehensive enhanced system health check"""
        self.update_scifi_visual_state("analyzing", "Running system health check")
        self.log("🏥 Running enhanced system health check...")

        if not self.api_client:
            self.log("❌ No API client configured")
            self.update_scifi_visual_state("error", "No API client")
            return

        # 1. System status
        status_ok, status_msg = self.api_client.check_system_status()
        self.log(f"System Status: {'✅' if status_ok else '❌'} {status_msg}")

        # 2. Balance check
        balance = self.api_client.check_balance()
        if balance and balance.get('error') == 0:
            thb_balance = balance['result'].get('THB', 0)
            self.log(f"Balance Check: ✅ THB {thb_balance:,.2f}")
        else:
            self.log("Balance Check: ❌ Failed")

        # 3. Market data check for all configured symbols
        ticker = self.api_client.get_simple_ticker(self.config['symbol'])
        if ticker:
            self.log(f"Market Data: ✅ {ticker['symbol']} @ {ticker['last_price']:,.2f}")

            # Fee analysis
            price = ticker['last_price']
            crypto_amount = self.config['trade_amount_thb'] / price
            total_fees = self.api_client.calculate_trading_fees(crypto_amount, price, "both")
            fee_pct = (total_fees / self.config['trade_amount_thb']) * 100

            self.log(f"Fee Analysis: 💸 {total_fees:.2f} THB ({fee_pct:.3f}%)")

            if fee_pct < 0.6:
                self.log("Fee Impact: ✅ Acceptable")
            else:
                self.log("Fee Impact: ⚠️ Consider larger trades")
        else:
            self.log("Market Data: ❌ Failed")

        # 4. Configuration check
        if self.config['trade_amount_thb'] < 500:
            self.log("⚠️ Warning: Small trade amount may not be profitable")
        if self.config['max_daily_trades'] > 10:
            self.log("⚠️ Warning: High daily trade limit")

        # 5. Strategy check
        if self.strategy:
            self.log(f"Strategy: ✅ Loaded (Min profit: {self.strategy.min_profit_margin * 100:.1f}%)")
        else:
            self.log("Strategy: ❌ Not loaded")

        # 6. Visual system check
        if hasattr(self, 'scifi_visual'):
            self.log("Visual System: ✅ Sci-Fi graphics active")
        else:
            self.log("Visual System: ❌ Not initialized")

        self.log("🏥 Enhanced health check completed")
        self.update_scifi_visual_state("success", "Health check completed")
        threading.Timer(2.0, lambda: self.update_scifi_visual_state("idle")).start()

    # === Additional testing and utility functions ===

    def test_market_data(self):
        """Enhanced market data testing"""
        if not self.api_client:
            self.test_log("❌ Please connect API first")
            return

        self.test_log("📊 Testing enhanced market data...")

        ticker = self.api_client.get_simple_ticker(self.config['symbol'])
        if ticker:
            self.test_log(f"✅ Market data retrieved:")
            self.test_log(f"   Symbol: {ticker['symbol']}")
            self.test_log(f"   Last Price: {ticker['last_price']:,.2f} THB")
            self.test_log(f"   Bid: {ticker['bid']:,.2f} THB")
            self.test_log(f"   Ask: {ticker['ask']:,.2f} THB")
            self.test_log(f"   24h Change: {ticker['change_24h']:+.2f}%")
            self.test_log(f"   24h Volume: {ticker.get('volume_24h', 0):,.0f} THB")

            # Test fee calculations
            price = ticker['last_price']
            test_amount = self.test_amount_var.get()
            crypto_amount = test_amount / price

            buy_fee = self.api_client.calculate_trading_fees(crypto_amount, price, "buy")
            sell_fee = self.api_client.calculate_trading_fees(crypto_amount, price, "sell")
            break_even = self.api_client.calculate_break_even_price(price, "buy")

            self.test_log(f"💸 Fee calculations for {test_amount} THB:")
            self.test_log(f"   Buy fee: {buy_fee:.2f} THB")
            self.test_log(f"   Sell fee: {sell_fee:.2f} THB")
            self.test_log(f"   Break-even: {break_even:.2f} THB")
            self.test_log(f"   Required gain: {((break_even - price) / price) * 100:.3f}%")
        else:
            self.test_log("❌ Failed to get market data")

    def test_balance(self):
        """Enhanced balance testing"""
        if not self.api_client:
            self.test_log("❌ Please connect API first")
            return

        self.test_log("💰 Testing enhanced balance check...")

        balance = self.api_client.check_balance()
        if balance and balance.get('error') == 0:
            self.test_log("✅ Balance retrieved:")

            total_value_thb = 0
            for currency, amount in balance['result'].items():
                amount_float = float(amount)
                if amount_float > 0:
                    self.test_log(f"   {currency}: {amount_float:,.8f}")

                    # Calculate THB value for crypto currencies
                    if currency != 'THB':
                        try:
                            symbol = f"{currency.lower()}_thb"
                            ticker = self.api_client.get_simple_ticker(symbol)
                            if ticker:
                                thb_value = amount_float * ticker['last_price']
                                total_value_thb += thb_value
                                self.test_log(f"      ≈ {thb_value:,.2f} THB")
                        except:
                            pass
                    else:
                        total_value_thb += amount_float

            self.test_log(f"📊 Total portfolio value: ≈ {total_value_thb:,.2f} THB")
        else:
            error_msg = "Unknown error"
            if balance:
                error_code = balance.get("error", 999)
                error_msg = self.api_client.error_codes.get(error_code, f"Error {error_code}")
            self.test_log(f"❌ Balance check failed: {error_msg}")

    def test_buy_order(self):
        """Enhanced buy order testing with fee calculation"""
        if not self.api_client:
            self.test_log("❌ Please connect API first")
            return

        # Enhanced confirmation for test order
        test_amount = self.test_amount_var.get()

        ticker = self.api_client.get_simple_ticker(self.config['symbol'])
        if not ticker:
            self.test_log("❌ Cannot get current price")
            return

        current_price = ticker['last_price']
        crypto_amount = test_amount / current_price
        total_fees = self.api_client.calculate_trading_fees(crypto_amount, current_price, "both")

        if not messagebox.askyesno("Confirm Enhanced Test Order",
                                   f"Place a REAL test buy order?\n\n" +
                                   f"Amount: {test_amount} THB\n" +
                                   f"Current Price: {current_price:,.2f} THB\n" +
                                   f"Expected Crypto: {crypto_amount:.8f}\n" +
                                   f"Estimated Fees: {total_fees:.2f} THB\n\n" +
                                   f"This will use real money!"):
            return

        self.test_log(f"🧪 Testing enhanced buy order for {test_amount} THB...")
        self.test_log(f"   Current price: {current_price:,.2f} THB")
        self.test_log(f"   Expected crypto: {crypto_amount:.8f}")
        self.test_log(f"   Estimated total fees: {total_fees:.2f} THB")

        buy_price = current_price * 1.01  # 1% above market for quick execution

        # Check balance first
        balance = self.api_client.check_balance()
        if not balance or balance.get('error') != 0:
            self.test_log("❌ Cannot check balance")
            return

        thb_balance = float(balance['result'].get('THB', 0))
        if thb_balance < test_amount:
            self.test_log(f"❌ Insufficient balance: {thb_balance:.2f} < {test_amount}")
            return

        # Place test order
        result = self.api_client.place_buy_order_safe(
            self.config['symbol'], test_amount, buy_price, "limit"
        )

        if result.get("error") == 0:
            order_info = result["result"]
            actual_fee = order_info.get('fee', 0)

            self.test_log("✅ Enhanced test buy order placed successfully!")
            self.test_log(f"   Order ID: {order_info['id']}")
            self.test_log(f"   Amount: {order_info['amt']} THB")
            self.test_log(f"   Rate: {order_info['rat']} THB")
            self.test_log(f"   Actual Fee: {actual_fee} THB")
            self.test_log(f"   Expected Crypto: {order_info['rec']:.8f}")

            # Ask if user wants to cancel the order
            if messagebox.askyesno("Cancel Test Order?",
                                   f"Enhanced test order placed successfully!\n\n" +
                                   f"Order ID: {order_info['id']}\n" +
                                   f"Actual Fee: {actual_fee} THB\n" +
                                   f"Do you want to cancel it now?"):
                self.cancel_test_order(order_info['id'])
        else:
            error_code = result.get("error", 999)
            error_msg = self.api_client.error_codes.get(error_code, f"Error {error_code}")
            self.test_log(f"❌ Enhanced test buy order failed: {error_msg}")

    def cancel_test_order(self, order_id):
        """Enhanced order cancellation"""
        self.test_log(f"🗑️ Cancelling enhanced test order {order_id}...")

        result = self.api_client.cancel_order_safe(self.config['symbol'], order_id, "buy")

        if result.get("error") == 0:
            self.test_log("✅ Enhanced test order cancelled successfully")
        else:
            error_code = result.get("error", 999)
            error_msg = self.api_client.error_codes.get(error_code, f"Error {error_code}")
            self.test_log(f"❌ Cancel failed: {error_msg}")

    def check_open_orders(self):
        """Enhanced open orders check"""
        if not self.api_client:
            self.log("❌ Please connect API first")
            return

        self.update_scifi_visual_state("analyzing", "Checking open orders")
        self.log("📋 Checking enhanced open orders...")

        orders = self.api_client.get_my_open_orders_safe(self.config['symbol'])

        if orders and orders.get("error") == 0:
            order_list = orders.get("result", [])
            if order_list:
                self.log(f"📋 Found {len(order_list)} open orders:")
                total_value = 0
                for order in order_list:
                    side = order.get('side', 'unknown').upper()
                    order_id = order.get('id', 'N/A')
                    rate = float(order.get('rate', 0))
                    amount = float(order.get('amount', 0))

                    if side == "BUY":
                        value = amount  # THB amount for buy orders
                    else:
                        value = amount * rate  # Crypto amount * price for sell orders

                    total_value += value

                    self.log(f"   {side} Order ID: {order_id}")
                    self.log(f"   Price: {rate:,.2f} THB, Amount: {amount:.8f}")
                    self.log(f"   Value: {value:,.2f} THB")

                self.log(f"📊 Total open order value: {total_value:,.2f} THB")
                self.update_scifi_visual_state("success", f"Found {len(order_list)} open orders")
            else:
                self.log("📋 No open orders")
                self.update_scifi_visual_state("idle", "No open orders")
        else:
            error_code = orders.get("error", 999) if orders else 999
            error_msg = self.api_client.error_codes.get(error_code, f"Error {error_code}")
            self.log(f"❌ Failed to get open orders: {error_msg}")
            self.update_scifi_visual_state("error", "Failed to get orders")

        threading.Timer(2.0, lambda: self.update_scifi_visual_state("idle")).start()

    def load_trade_history(self):
        """Enhanced trade history loading with profit analysis"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT timestamp, symbol, side, amount, price, net_pnl, fees, reason, is_paper, order_id, break_even_price
                FROM trades
                ORDER BY timestamp DESC
                LIMIT 100
            ''')

            trades = cursor.fetchall()
            conn.close()

            self.history_display.delete("1.0", "end")

            if not trades:
                self.history_display.insert("1.0", "No trade history found.")
                return

            header = f"{'Time':<10} {'Mode':<6} {'Side':<4} {'Amount':<12} {'Price':<10} {'Net P&L':<10} {'Fees':<8} {'Break-Even':<10} {'Reason'}\n"
            header += "=" * 120 + "\n"
            self.history_display.insert("end", header)

            total_pnl = 0
            total_fees = 0

            for trade in trades:
                timestamp, symbol, side, amount, price, net_pnl, fees, reason, is_paper, order_id, break_even = trade
                time_str = datetime.fromisoformat(timestamp).strftime('%H:%M:%S')
                mode = "PAPER" if is_paper else "REAL"

                pnl_str = f"{net_pnl:+.2f}" if net_pnl else "0.00"
                fees_str = f"{fees:.2f}" if fees else "0.00"
                break_even_str = f"{break_even:.0f}" if break_even else "N/A"

                if net_pnl:
                    total_pnl += net_pnl
                if fees:
                    total_fees += fees

                trade_line = f"{time_str:<10} {mode:<6} {side.upper():<4} {amount:<12.8f} {price:<10.2f} {pnl_str:<10} {fees_str:<8} {break_even_str:<10} {reason}\n"
                self.history_display.insert("end", trade_line)

            # Add summary
            summary = f"\n{'=' * 120}\n"
            summary += f"SUMMARY: Total Net P&L: {total_pnl:+.2f} THB | Total Fees: {total_fees:.2f} THB | Net After Fees: {total_pnl:.2f} THB\n"
            self.history_display.insert("end", summary)

        except Exception as e:
            self.log(f"Error loading enhanced history: {e}")

    def export_history(self):
        """Enhanced history export with profit analysis"""
        try:
            import csv
            from tkinter import filedialog

            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv")],
                title="Export Enhanced Trade History"
            )

            if filename:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT timestamp, symbol, side, amount, price, total_thb, 
                           order_id, net_pnl, fees, reason, is_paper, rsi, volume_momentum, break_even_price
                    FROM trades ORDER BY timestamp DESC
                ''')

                trades = cursor.fetchall()
                conn.close()

                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(['Timestamp', 'Symbol', 'Side', 'Amount', 'Price',
                                     'Total THB', 'Order ID', 'Net P&L', 'Fees', 'Reason',
                                     'Paper Trading', 'RSI', 'Volume Momentum', 'Break Even Price'])
                    writer.writerows(trades)

                messagebox.showinfo("Export Complete", f"Enhanced trade history exported to {filename}")

        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export: {e}")

    # === Enhanced utility functions ===

    def test_connection(self):
        """Enhanced connection test with visual feedback"""
        if not self.api_client:
            self.api_status_display.delete("1.0", "end")
            self.api_status_display.insert("1.0", "❌ Please connect API first")
            return

        self.update_scifi_visual_state("connecting", "Testing API connection")

        self.api_status_display.delete("1.0", "end")
        self.api_status_display.insert("1.0", "🔌 Testing Enhanced API Connection...\n\n")

        # Test ticker
        ticker = self.api_client.get_simple_ticker(self.config['symbol'])
        if ticker:
            self.api_status_display.insert("end",
                                           f"✅ Market Data: {ticker['symbol']} @ {ticker['last_price']:,.2f} THB\n")
        else:
            self.api_status_display.insert("end", "❌ Market Data: Failed\n")

        # Test balance
        balance = self.api_client.check_balance()
        if balance and balance.get('error') == 0:
            thb_balance = balance['result'].get('THB', 0)
            self.api_status_display.insert("end", f"✅ Balance: {float(thb_balance):,.2f} THB\n")
        else:
            self.api_status_display.insert("end", "❌ Balance: Failed\n")

        # Test system status
        status_ok, status_msg = self.api_client.check_system_status()
        self.api_status_display.insert("end", f"{'✅' if status_ok else '❌'} System: {status_msg}\n")

        # Test fee calculation
        if ticker:
            price = ticker['last_price']
            crypto_amount = 1000 / price  # Test with 1000 THB
            total_fees = self.api_client.calculate_trading_fees(crypto_amount, price, "both")
            self.api_status_display.insert("end", f"✅ Fee Calculation: {total_fees:.2f} THB for 1000 THB trade\n")

        # Test symbol support
        supported_symbols = len(self.api_client.all_bitkub_symbols)
        self.api_status_display.insert("end", f"✅ Supported Symbols: {supported_symbols} Bitkub coins\n")

        self.api_status_display.insert("end",
                                       f"\nEnhanced Connection Test: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        self.update_scifi_visual_state("success", "Connection test completed")
        threading.Timer(2.0, lambda: self.update_scifi_visual_state("idle")).start()

    def api_health_check(self):
        """Enhanced API health check with comprehensive testing"""
        if not self.api_client:
            self.api_status_display.delete("1.0", "end")
            self.api_status_display.insert("1.0", "❌ No API client configured")
            return

        self.update_scifi_visual_state("analyzing", "Running API health check")

        self.api_status_display.delete("1.0", "end")
        self.api_status_display.insert("1.0", "🏥 Running Enhanced API Health Check...\n\n")

        # System status
        status_ok, status_msg = self.api_client.check_system_status()
        self.api_status_display.insert("end", f"System Status: {'✅' if status_ok else '❌'} {status_msg}\n")

        # Balance check
        balance = self.api_client.check_balance()
        if balance and balance.get('error') == 0:
            self.api_status_display.insert("end", "Balance Check: ✅ Success\n")
            for currency, amount in balance['result'].items():
                amount_float = float(amount)
                if amount_float > 0:
                    self.api_status_display.insert("end", f"  {currency}: {amount_float:,.8f}\n")
        else:
            self.api_status_display.insert("end", "Balance Check: ❌ Failed\n")

        # Market data check for multiple symbols
        test_symbols = ["btc_thb", "eth_thb", "ada_thb"]
        working_symbols = 0
        for symbol in test_symbols:
            ticker = self.api_client.get_simple_ticker(symbol)
            if ticker:
                working_symbols += 1

        self.api_status_display.insert("end", f"Market Data: ✅ {working_symbols}/{len(test_symbols)} symbols working\n")

        # Fee calculation test
        try:
            test_amount = 1000
            test_price = 1000000  # 1M THB per BTC
            test_crypto = test_amount / test_price
            total_fees = self.api_client.calculate_trading_fees(test_crypto, test_price, "both")
            expected_fee_pct = (self.api_client.trading_fees['maker_fee'] + self.api_client.trading_fees[
                'taker_fee']) * 100

            self.api_status_display.insert("end",
                                           f"Fee Calculation: ✅ {total_fees:.2f} THB ({expected_fee_pct:.2f}%)\n")
        except Exception as e:
            self.api_status_display.insert("end", f"Fee Calculation: ❌ Error: {e}\n")

        # Strategy integration test
        if self.strategy:
            try:
                # Test strategy with sample data
                sample_prices = [100000, 101000, 102000, 99000, 98000]
                self.strategy.price_history.extend(sample_prices)
                rsi = self.strategy.calculate_rsi(list(self.strategy.price_history))
                self.api_status_display.insert("end", f"Strategy Test: ✅ RSI calculation working ({rsi:.1f})\n")
            except Exception as e:
                self.api_status_display.insert("end", f"Strategy Test: ❌ Error: {e}\n")
        else:
            self.api_status_display.insert("end", "Strategy Test: ⚠️ No strategy loaded\n")

        # Visual system test
        if hasattr(self, 'scifi_visual'):
            self.api_status_display.insert("end", "Visual System: ✅ Sci-Fi graphics active\n")
        else:
            self.api_status_display.insert("end", "Visual System: ❌ Not initialized\n")

        self.api_status_display.insert("end",
                                       f"\nEnhanced Health Check Completed: {datetime.now().strftime('%H:%M:%S')}")

        self.update_scifi_visual_state("success", "Health check completed")
        threading.Timer(3.0, lambda: self.update_scifi_visual_state("idle")).start()

    def test_log(self, message):
        """Enhanced test logging"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.test_display.insert("end", log_entry)
        self.test_display.see("end")

    def log(self, message):
        """Enhanced logging with visual state integration"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"

        # Add to trading log
        self.trading_log.insert("end", log_entry)
        self.trading_log.see("end")

        # Keep log size manageable
        lines = self.trading_log.get("1.0", "end").split('\n')
        if len(lines) > 1000:
            # Keep last 500 lines
            self.trading_log.delete("1.0", f"{len(lines) - 500}.0")

    def run(self):
        """Start the enhanced application with sci-fi graphics"""
        # Reset daily counters at startup
        self.daily_trades = 0
        self.daily_pnl = 0
        self.total_fees_paid = 0

        self.log("🚀 Enhanced Bitkub Trading Bot with Sci-Fi Graphics Started")
        self.log("🎬 Sci-Fi Visual System Initialized")
        self.log("💸 Fee-aware strategy loaded")
        self.log(f"🪙 Supporting all {len(ImprovedBitkubAPI('', '').all_bitkub_symbols)} Bitkub coins")
        self.log("📝 Default: PAPER TRADING mode")
        self.log("⚠️ Always test thoroughly before enabling real trading")

        # Initialize visual system
        if hasattr(self, 'scifi_visual'):
            self.update_scifi_visual_state("idle", "System ready")

        # Initialize system status
        self.status_cards["System Status"].configure(text="Not Connected", text_color="gray")

        # Set up cleanup on window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        try:
            self.root.mainloop()
        except Exception as e:
            print(f"Main loop error: {e}")
        finally:
            self.cleanup_resources()

    def on_closing(self):
        """Handle window closing properly"""
        try:
            # Stop trading first
            if self.is_trading:
                self.emergency_stop = True
                self.is_trading = False

            # Cleanup resources
            self.cleanup_resources()

            # Destroy window
            self.root.quit()
            self.root.destroy()
        except Exception as e:
            print(f"Cleanup error: {e}")
            # Force exit if cleanup fails
            import sys
            sys.exit(0)

    def cleanup_resources(self):
        """Enhanced cleanup resources on exit with safe threading"""
        try:
            # Stop trading
            self.is_trading = False
            self.emergency_stop = True

            # Cleanup visual system
            if hasattr(self, 'scifi_visual') and self.scifi_visual:
                self.scifi_visual.cleanup()

            # Wait for threads to finish
            time.sleep(0.5)

        except Exception as e:
            print(f"Resource cleanup error: {e}")

    def execute_enhanced_buy(self, price, reason):
        """Enhanced buy execution with thread safety"""
        try:
            amount_thb = self.config['trade_amount_thb']
            crypto_amount = amount_thb / price

            # Calculate expected fees
            expected_buy_fee = self.api_client.calculate_trading_fees(crypto_amount, price, "buy")
            break_even_price = self.api_client.calculate_break_even_price(price, "buy")

            # Safe visual update
            try:
                if threading.current_thread() == threading.main_thread():
                    self.update_scifi_visual_state("trading", f"Executing buy order: {amount_thb} THB")
                else:
                    self.root.after(0, lambda: self.update_scifi_visual_state("trading",
                                                                              f"Executing buy order: {amount_thb} THB"))
            except:
                pass

            if self.is_paper_trading:
                # Paper trading
                self.strategy.position = {
                    'entry_price': price,
                    'amount': crypto_amount,
                    'entry_time': datetime.now()
                }

                self.log(f"📝 PAPER BUY: {amount_thb} THB @ {price:.2f}")
                self.log(f"   Reason: {reason}")
                self.log(f"   Expected fee: {expected_buy_fee:.2f} THB")
                self.log(f"   Break-even price: {break_even_price:.2f} THB")

                self.save_enhanced_trade('buy', crypto_amount, price, amount_thb,
                                         'PAPER', 0, expected_buy_fee, 0, reason, True)
            else:
                # Real trading with fee-optimized pricing
                buy_price = price * 1.002  # Small buffer for execution

                self.log(f"💰 REAL BUY: {amount_thb} THB @ {buy_price:.2f}")

                result = self.api_client.place_buy_order_safe(
                    self.config['symbol'], amount_thb, buy_price, 'limit'
                )

                if result and result.get('error') == 0:
                    order_info = result['result']
                    order_id = order_info.get('id', 'unknown')
                    actual_amount = order_info.get('rec', crypto_amount)
                    actual_fee = order_info.get('fee', expected_buy_fee)

                    self.strategy.position = {
                        'entry_price': buy_price,
                        'amount': actual_amount,
                        'entry_time': datetime.now(),
                        'order_id': order_id
                    }

                    self.log(f"✅ REAL BUY SUCCESS: Order ID {order_id}")
                    self.log(f"   Amount: {actual_amount:.8f} crypto")
                    self.log(f"   Fee: {actual_fee:.2f} THB")

                    self.total_fees_paid += actual_fee
                    self.save_enhanced_trade('buy', actual_amount, buy_price, amount_thb,
                                             order_id, 0, actual_fee, 0, reason, False)

                    # Safe visual update
                    try:
                        if threading.current_thread() == threading.main_thread():
                            self.update_scifi_visual_state("success", "Buy order executed successfully")
                        else:
                            self.root.after(0, lambda: self.update_scifi_visual_state("success",
                                                                                      "Buy order executed successfully"))
                    except:
                        pass
                else:
                    error_code = result.get("error", 999) if result else 999
                    error_msg = self.api_client.error_codes.get(error_code, f"Error {error_code}")
                    self.log(f"❌ Buy order failed: {error_msg}")
                    try:
                        if threading.current_thread() == threading.main_thread():
                            self.update_scifi_visual_state("error", f"Buy failed: {error_msg}")
                        else:
                            self.root.after(0,
                                            lambda: self.update_scifi_visual_state("error", f"Buy failed: {error_msg}"))
                    except:
                        pass
                    return

            self.daily_trades += 1
            self.last_trade_time = datetime.now()

            # Safe UI updates
            try:
                if threading.current_thread() == threading.main_thread():
                    self.status_cards["Position"].configure(text=f"LONG @ {price:.2f}")
                    self.status_cards["Daily Trades"].configure(
                        text=f"{self.daily_trades}/{self.config['max_daily_trades']}"
                    )
                else:
                    self.root.after(0, lambda: self._update_position_cards(price))
            except:
                pass

        except Exception as e:
            self.log(f"❌ Buy execution error: {e}")
            try:
                if threading.current_thread() == threading.main_thread():
                    self.update_scifi_visual_state("error", f"Buy error: {str(e)[:50]}")
                else:
                    self.root.after(0, lambda: self.update_scifi_visual_state("error", f"Buy error: {str(e)[:50]}"))
            except:
                pass

    def _update_position_cards(self, price):
        """Helper to update position cards on main thread"""
        try:
            self.status_cards["Position"].configure(text=f"LONG @ {price:.2f}")
            self.status_cards["Daily Trades"].configure(
                text=f"{self.daily_trades}/{self.config['max_daily_trades']}"
            )
        except:
            pass


if __name__ == "__main__":
    # Enhanced startup warning
    print("\n" + "=" * 80)
    print("🚀 ENHANCED BITKUB TRADING BOT WITH SCI-FI GRAPHICS")
    print("=" * 80)
    print("✨ NEW FEATURES:")
    print("• Futuristic Sci-Fi visual status system with 8 different states")
    print("• Complete Bitkub fee integration (0.25% maker + 0.25% taker)")
    print("• Support for ALL 57+ Bitkub coins")
    print("• Fee-aware trading strategy for profitable operations")
    print("• Real-time profit calculation including all fees")
    print("• Enhanced market analysis with volume momentum")
    print("• Comprehensive break-even price calculation")
    print("• Advanced testing and debugging features")
    print("\n🎬 SCI-FI VISUAL STATES:")
    print("• 🔵 Idle - System monitoring")
    print("• 🟡 Connecting - API connection")
    print("• 🔴 Analyzing - Market analysis")
    print("• 🟢 Buy Signal - Buy opportunity detected")
    print("• 🔴 Sell Signal - Sell opportunity detected")
    print("• ⚡ Trading - Active order execution")
    print("• ✅ Success - Operation completed successfully")
    print("• ❌ Error - System error or warning")
    print("\n💰 FEE OPTIMIZATION:")
    print("• Automatic break-even price calculation")
    print("• Minimum profit margin enforcement")
    print("• Real-time fee impact analysis")
    print("• Trade size optimization recommendations")
    print("\n⚠️ WARNINGS:")
    print("• This bot trades with REAL MONEY when enabled")
    print("• Always start with PAPER TRADING")
    print("• Use minimum 500 THB per trade for profitability")
    print("• Monitor fee impact on smaller trades")
    print("• Test thoroughly with small amounts first")
    print("=" * 80 + "\n")

    response = input("Do you understand the risks and enhanced features? (yes/no): ")

    if response.lower() == 'yes':
        app = ImprovedTradingBot()
        try:
            app.run()
        finally:
            app.cleanup_resources()
    else:
        print("Exiting. Please understand all features and risks before using this enhanced bot.")