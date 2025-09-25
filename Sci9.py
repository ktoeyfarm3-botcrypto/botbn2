"""
🚀 Sci6 Enhanced Trading Bot - Complete Version with Improved UI
รวมโค้ดทั้งหมดจาก Sci6.py และ Enhanced UI System
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
import threading
import json
import time
import math
import random
import requests
import hashlib
import hmac
import urllib.parse
from datetime import datetime, timedelta
import logging
import os
from collections import deque
import uuid

# Optional imports with fallbacks
try:
    import pandas as pd
    import numpy as np
except ImportError:
    pd = None
    np = None
    print("Warning: pandas/numpy not installed - some features may be limited")

from typing import Dict, List, Optional, Tuple

# Set appearance mode and theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


# ============================================================================
# 🎬 Sci-Fi Visual System
# ============================================================================

class SciFiVisualSystem:
    """🎬 Advanced Sci-Fi Visual System for Trading Bot"""

    def __init__(self, parent_frame, width=300, height=250):
        self.parent_frame = parent_frame
        self.width = width
        self.height = height
        self.center_x = width // 2
        self.center_y = height // 2

        # Animation state
        self.is_animating = False
        self.animation_thread = None
        self.frame_count = 0
        self.rotation_angle = 0
        self.pulse_phase = 0
        self.wave_phase = 0
        self.current_state = "idle"

        # Create canvas
        self.canvas = tk.Canvas(
            parent_frame,
            width=width,
            height=height,
            bg="#000011",
            highlightthickness=0
        )

        # State themes
        self.state_themes = {
            "idle": {
                "primary": "#4a9eff",
                "secondary": "#2d5aa0",
                "accent": "#87ceeb",
                "glow": "#6ab7ff"
            },
            "connecting": {
                "primary": "#ffaa00",
                "secondary": "#cc8800",
                "accent": "#ffcc66",
                "glow": "#ffbb33"
            },
            "analyzing": {
                "primary": "#ff6600",
                "secondary": "#cc5200",
                "accent": "#ff9966",
                "glow": "#ff7733"
            },
            "coin_analysis": {
                "primary": "#9966ff",
                "secondary": "#7744cc",
                "accent": "#bb88ff",
                "glow": "#aa77ff"
            },
            "buy_signal": {
                "primary": "#00ff44",
                "secondary": "#00cc33",
                "accent": "#66ff88",
                "glow": "#33ff66"
            },
            "sell_signal": {
                "primary": "#ff4400",
                "secondary": "#cc3300",
                "accent": "#ff7766",
                "glow": "#ff5533"
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
                elif self.current_state == "coin_analysis":
                    self._draw_coin_analysis()
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
            particle['phase'] += 0.1

            # Bounce off edges
            if particle['x'] <= 0 or particle['x'] >= self.width:
                particle['dx'] *= -1
            if particle['y'] <= 0 or particle['y'] >= self.height:
                particle['dy'] *= -1

    def draw_particles(self, theme):
        """Draw floating particles"""
        for particle in self.particles:
            alpha_mod = 0.5 + 0.5 * math.sin(particle['phase'])
            size = particle['size'] * (1 + 0.3 * alpha_mod)

            self.canvas.create_oval(
                particle['x'] - size, particle['y'] - size,
                particle['x'] + size, particle['y'] + size,
                fill=theme["accent"], outline="",
                tags="particle"
            )

    def draw_hud_rings(self, theme, rotation_offset=0):
        """Draw HUD-style rotating rings"""
        ring_radius = [60, 80, 100]

        for i, radius in enumerate(ring_radius):
            angle_offset = (self.rotation_angle + rotation_offset + i * 30) % 360
            segments = 8 + i * 4

            for j in range(segments):
                angle = (360 / segments) * j + angle_offset
                start_angle = angle
                extent_angle = 360 / segments * 0.7

                self.canvas.create_arc(
                    self.center_x - radius, self.center_y - radius,
                    self.center_x + radius, self.center_y + radius,
                    start=start_angle, extent=extent_angle,
                    outline=theme["primary"] if j % 2 == 0 else theme["secondary"],
                    width=2, style="arc",
                    tags=f"ring_{i}"
                )

    def draw_energy_core(self, theme):
        """Draw central energy core"""
        pulse = 1 + 0.3 * math.sin(self.pulse_phase)
        core_size = 20 * pulse

        # Outer glow
        for i in range(5, 0, -1):
            glow_size = core_size + i * 3
            alpha_color = theme["glow"]

            self.canvas.create_oval(
                self.center_x - glow_size, self.center_y - glow_size,
                self.center_x + glow_size, self.center_y + glow_size,
                fill=alpha_color, outline="",
                tags="core_glow"
            )

        # Core
        self.canvas.create_oval(
            self.center_x - core_size, self.center_y - core_size,
            self.center_x + core_size, self.center_y + core_size,
            fill=theme["primary"], outline=theme["accent"], width=2,
            tags="energy_core"
        )

    def _draw_idle(self):
        """Draw idle state"""
        self.canvas.delete("all")
        theme = self.state_themes["idle"]

        self.draw_particles(theme)
        self.draw_hud_rings(theme, 0)
        self.draw_energy_core(theme)

        self.canvas.create_text(
            self.center_x, self.height - 30,
            text="SYSTEM READY", fill=theme["primary"],
            font=("Orbitron", 12, "bold"),
            tags="status_text"
        )

    def _draw_connecting(self):
        """Draw connecting state"""
        self.canvas.delete("all")
        theme = self.state_themes["connecting"]

        self.draw_particles(theme)
        self.draw_hud_rings(theme, 45)
        self.draw_energy_core(theme)

        self.canvas.create_text(
            self.center_x, self.height - 30,
            text="CONNECTING...", fill=theme["primary"],
            font=("Orbitron", 12, "bold"),
            tags="status_text"
        )

    def _draw_analyzing(self):
        """Draw analyzing state"""
        self.canvas.delete("all")
        theme = self.state_themes["analyzing"]

        self.draw_particles(theme)
        self.draw_hud_rings(theme, 90)
        self.draw_energy_core(theme)

        # Analysis waves
        wave_y = self.center_y + 30 * math.sin(self.wave_phase)
        for i in range(3):
            y_offset = wave_y + i * 5
            self.canvas.create_line(
                self.center_x - 50, y_offset,
                self.center_x + 50, y_offset,
                fill=theme["accent"], width=2,
                tags="analysis_wave"
            )

        self.canvas.create_text(
            self.center_x, self.height - 30,
            text="ANALYZING...", fill=theme["primary"],
            font=("Orbitron", 12, "bold"),
            tags="status_text"
        )

    def _draw_coin_analysis(self):
        """Draw coin analysis state"""
        self.canvas.delete("all")
        theme = self.state_themes["coin_analysis"]

        self.draw_particles(theme)
        self.draw_hud_rings(theme, 135)
        self.draw_energy_core(theme)

        self.canvas.create_text(
            self.center_x, self.height - 30,
            text="COIN ANALYSIS", fill=theme["primary"],
            font=("Orbitron", 12, "bold"),
            tags="status_text"
        )

    def _draw_buy_signal(self):
        """Draw buy signal state"""
        self.canvas.delete("all")
        theme = self.state_themes["buy_signal"]

        self.draw_particles(theme)
        self.draw_hud_rings(theme, 180)
        self.draw_energy_core(theme)

        self.canvas.create_text(
            self.center_x, self.height - 30,
            text="BUY SIGNAL", fill=theme["primary"],
            font=("Orbitron", 12, "bold"),
            tags="status_text"
        )

    def _draw_sell_signal(self):
        """Draw sell signal state"""
        self.canvas.delete("all")
        theme = self.state_themes["sell_signal"]

        self.draw_particles(theme)
        self.draw_hud_rings(theme, 95)
        self.draw_energy_core(theme)

        self.canvas.create_text(
            self.center_x, self.height - 30,
            text="SELL SIGNAL", fill=theme["primary"],
            font=("Orbitron", 12, "bold"),
            tags="status_text"
        )

    def _draw_trading(self):
        """Draw trading state"""
        self.canvas.delete("all")
        theme = self.state_themes["trading"]

        self.draw_particles(theme)
        self.draw_hud_rings(theme, 110)
        self.draw_energy_core(theme)

        self.canvas.create_text(
            self.center_x, self.height - 30,
            text="TRADING...", fill=theme["primary"],
            font=("Orbitron", 12, "bold"),
            tags="status_text"
        )

    def _draw_success(self):
        """Draw success state"""
        self.canvas.delete("all")
        theme = self.state_themes["success"]

        self.draw_particles(theme)
        self.draw_hud_rings(theme, 75)
        self.draw_energy_core(theme)

        self.canvas.create_text(
            self.center_x, self.height - 30,
            text="SUCCESS", fill=theme["primary"],
            font=("Orbitron", 12, "bold"),
            tags="status_text"
        )

    def _draw_error(self):
        """Draw error state"""
        self.canvas.delete("all")
        theme = self.state_themes["error"]

        self.draw_particles(theme)
        self.draw_hud_rings(theme, 65)
        self.draw_energy_core(theme)

        self.canvas.create_text(
            self.center_x, self.height - 30,
            text="ERROR", fill=theme["primary"],
            font=("Orbitron", 12, "bold"),
            tags="status_text"
        )

    def draw_idle_state(self):
        """Draw static idle state"""
        self.canvas.delete("all")
        theme = self.state_themes["idle"]

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


# ============================================================================
# 🔌 Enhanced Bitkub API Client
# ============================================================================

class ImprovedBitkubAPI:
    """Enhanced Bitkub API Client with REAL TRADING capabilities"""

    def __init__(self, api_key="", api_secret=""):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://api.bitkub.com"
        self.request_times = deque(maxlen=250)
        self.rate_limit_lock = threading.Lock()

        # Bitkub fee structure
        self.trading_fees = {
            'maker_fee': 0.0025,  # 0.25%
            'taker_fee': 0.0025,  # 0.25%
            'withdrawal_fee': 0.001  # 0.1%
        }

        # Complete list of Bitkub supported coins
        self.all_bitkub_symbols = [
            "btc_thb", "eth_thb", "ada_thb", "xrp_thb", "bnb_thb", "doge_thb",
            "dot_thb", "matic_thb", "atom_thb", "near_thb", "sol_thb", "sand_thb",
            "mana_thb", "avax_thb", "shib_thb", "ltc_thb", "bch_thb", "etc_thb",
            "link_thb", "uni_thb", "usdt_thb", "usdc_thb", "usds_thb", "alpha_thb",
            "chz_thb", "bat_thb", "comp_thb", "knc_thb", "cvc_thb", "pow_thb",
            "iotx_thb", "zil_thb", "six_thb", "jfin_thb", "kub_thb", "1inch_thb",
            "aave_thb", "grt_thb", "enj_thb", "gala_thb", "snx_thb", "lrc_thb",
            "mkr_thb", "aero_thb", "aevo_thb", "algo_thb", "alt_thb", "ankr_thb",
            "ape_thb", "api3_thb", "apt_thb", "arb_thb", "arkm_thb", "asp_thb"
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
            22: "Invalid side", 23: "Failed to cancel order", 30: "Unrecognized request",
            40: "Rate limit exceeded", 50: "Server error"
        }

    def wait_for_rate_limit(self):
        """Enhanced rate limiting"""
        with self.rate_limit_lock:
            now = time.time()
            self.request_times.append(now)

            if len(self.request_times) >= 250:
                oldest_time = self.request_times[0]
                if now - oldest_time < 60:
                    sleep_time = 60 - (now - oldest_time) + 0.1
                    time.sleep(sleep_time)

    def create_signature(self, timestamp, method, path, query_string="", payload=""):
        """Create API signature"""
        if method.upper() == "GET":
            string_to_sign = timestamp + method.upper() + path + query_string
        else:
            string_to_sign = timestamp + method.upper() + path + payload

        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        return signature

    def make_request(self, method, endpoint, params=None, signed=False):
        """Make API request - using exact working method from Scci5.py"""
        self.wait_for_rate_limit()

        url = f"{self.base_url}{endpoint}"
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

        # Only add API key if available
        if self.api_key:
            headers['X-BTK-APIKEY'] = self.api_key

        try:
            if signed and self.api_key and self.api_secret:
                timestamp = str(int(time.time() * 1000))
                headers['X-BTK-TIMESTAMP'] = timestamp

                # Create payload for signature (like Scci5.py)
                if params:
                    payload = json.dumps(params, separators=(',', ':'))
                else:
                    payload = "{}"

                # Create signature string (like Scci5.py)
                string_to_sign = timestamp + method.upper() + endpoint + payload
                signature = hmac.new(
                    self.api_secret.encode('utf-8'),
                    string_to_sign.encode('utf-8'),
                    hashlib.sha256
                ).hexdigest()

                headers['X-BTK-SIGN'] = signature

                if method.upper() == "GET":
                    response = requests.get(url, headers=headers, params=params, timeout=10)
                else:
                    response = requests.post(url, headers=headers, data=payload, timeout=10)
            else:
                # Public API calls (like Scci5.py)
                if method.upper() == "GET":
                    response = requests.get(url, params=params, timeout=10)
                else:
                    response = requests.post(url, json=params, timeout=10)

            # Check HTTP status
            response.raise_for_status()

            # Parse JSON response
            try:
                json_response = response.json()

                # Ensure response is a dictionary (like Scci5.py validation)
                if isinstance(json_response, dict):
                    return json_response
                else:
                    return {"error": 995, "message": f"Unexpected response type: {type(json_response)}"}

            except json.JSONDecodeError as e:
                return {"error": 997, "message": f"Invalid JSON response: {str(e)}"}

        except requests.exceptions.Timeout:
            return {"error": 999, "message": "Request timeout - please check your internet connection"}
        except requests.exceptions.ConnectionError:
            return {"error": 998, "message": "Connection failed - please check your internet connection"}
        except requests.exceptions.HTTPError as e:
            return {"error": 994, "message": f"HTTP error {e.response.status_code}: {str(e)}"}
        except requests.exceptions.RequestException as e:
            return {"error": 993, "message": f"Request failed: {str(e)}"}
        except Exception as e:
            return {"error": 996, "message": f"Unexpected error: {str(e)}"}

    # Public API methods
    def get_server_time(self):
        """Get server timestamp"""
        try:
            response = requests.get(f"{self.base_url}/api/servertime", timeout=10)
            response.raise_for_status()

            # Parse response
            result = response.json()

            # Handle different response formats from Bitkub
            if isinstance(result, dict):
                if 'result' in result:
                    timestamp = result['result']
                elif 'servertime' in result:
                    timestamp = result['servertime']
                elif len(result) == 1:
                    # Sometimes it's just a single key-value pair
                    timestamp = list(result.values())[0]
                else:
                    return {"error": 999, "message": f"Unexpected response structure: {result}"}
            elif isinstance(result, (int, float)):
                timestamp = int(result)
            else:
                return {"error": 999, "message": f"Unexpected response type: {type(result)}"}

            # Bitkub server time is in seconds, we need milliseconds for consistency
            if timestamp < 2000000000:  # If timestamp is in seconds (before year 2033)
                timestamp = timestamp * 1000  # Convert to milliseconds

            return {"error": 0, "result": int(timestamp)}

        except requests.exceptions.Timeout:
            return {"error": 999, "message": "Server connection timeout"}
        except requests.exceptions.ConnectionError:
            return {"error": 998, "message": "Cannot connect to server - check internet connection"}
        except requests.exceptions.HTTPError as e:
            return {"error": 997, "message": f"Server error: HTTP {e.response.status_code}"}
        except json.JSONDecodeError:
            return {"error": 996, "message": "Invalid response from server"}
        except Exception as e:
            return {"error": 995, "message": f"Connection error: {str(e)}"}

    def get_market_data(self, symbol=None):
        """Get market data"""
        try:
            endpoint = f"{self.base_url}/api/market/ticker"

            # Don't use sym parameter, get all symbols
            response = requests.get(endpoint, timeout=10)
            response.raise_for_status()

            result = response.json()

            # Debug logging
            print(f"Market data response type: {type(result)}")

            # Handle different response formats
            if isinstance(result, dict):
                # If specific symbol requested
                if symbol:
                    symbol_upper = symbol.upper()

                    # Try different key formats
                    possible_keys = [
                        symbol_upper,  # BTC_THB
                        symbol.lower(),  # btc_thb
                        f"THB_{symbol_upper.split('_')[0]}" if '_' in symbol_upper else symbol_upper,
                        symbol_upper.replace('_', ''),  # BTCTHB
                    ]

                    symbol_data = None
                    for key in possible_keys:
                        if key in result:
                            symbol_data = {key: result[key]}
                            break

                    if symbol_data:
                        return {"error": 0, "result": symbol_data}
                    else:
                        # Debug: show available symbols
                        available_symbols = list(result.keys())[:10]  # Show first 10
                        print(f"Symbol {symbol_upper} not found. Available symbols: {available_symbols}")
                        return {"error": 11,
                                "message": f"Symbol {symbol_upper} not found. Available: {', '.join(available_symbols)}"}
                else:
                    # Return all data
                    return {"error": 0, "result": result}
            else:
                return {"error": 999, "message": f"Unexpected response format: {type(result)}"}

        except requests.exceptions.Timeout:
            return {"error": 999, "message": "Market data request timeout"}
        except requests.exceptions.ConnectionError:
            return {"error": 998, "message": "Cannot connect to market data server"}
        except requests.exceptions.HTTPError as e:
            return {"error": 997, "message": f"Market data error: HTTP {e.response.status_code}"}
        except json.JSONDecodeError:
            return {"error": 996, "message": "Invalid market data response"}
        except Exception as e:
            return {"error": 995, "message": f"Market data error: {str(e)}"}

    def get_market_depth(self, symbol, limit=5):
        """Get market depth"""
        return self.make_request("GET", "/api/market/depth", {
            "sym": symbol,
            "lmt": limit
        })

    def get_recent_trades(self, symbol, limit=10):
        """Get recent trades"""
        return self.make_request("GET", "/api/market/trades", {
            "sym": symbol,
            "lmt": limit
        })

    # Private API methods
    def get_wallet_balance(self):
        """Get wallet balance - REAL MONEY"""
        return self.make_request("POST", "/api/market/wallet", signed=True)

    def get_wallet_balance(self):
        """Get wallet balance - REAL MONEY (using working method from Scci5.py)"""
        if not self.api_key or not self.api_secret:
            return {"error": 3, "message": "API credentials not provided"}

        # Use the exact method from Scci5.py that works
        return self.make_request("POST", "/api/v3/market/wallet", {}, signed=True)

    def check_balance(self):
        """Check balance using Scci5.py working method"""
        try:
            result = self.make_request("POST", "/api/v3/market/wallet", {}, signed=True)
            return result
        except Exception as e:
            return {"error": 999, "message": f"Balance check error: {str(e)}"}

    def get_balances_safe(self):
        """Safely get balances with Scci5.py working method"""
        try:
            # Use check_balance method like in Scci5.py
            result = self.check_balance()

            # Check if result is valid
            if not result or not isinstance(result, dict):
                return {'error': 999, 'message': 'Invalid API response'}

            if result.get('error') == 0:
                balances = result.get('result', {})
                formatted = {}

                # Handle different response formats (like Scci5.py)
                if isinstance(balances, dict):
                    for currency, data in balances.items():
                        if isinstance(data, dict):
                            available = float(data.get('available', 0))
                            reserved = float(data.get('reserved', 0))
                            formatted[currency.upper()] = {
                                'available': available,
                                'reserved': reserved,
                                'total': available + reserved
                            }
                        elif isinstance(data, (int, float)):
                            # Sometimes balance is just a number (Scci5.py handles this)
                            formatted[currency.upper()] = {
                                'available': float(data),
                                'reserved': 0,
                                'total': float(data)
                            }

                return {'error': 0, 'result': formatted}
            else:
                error_code = result.get('error', 999)

                # Map common Bitkub error codes (from working Scci5.py)
                error_messages = {
                    0: "Success",
                    1: "Invalid JSON payload",
                    2: "Missing X-BTK-APIKEY",
                    3: "Invalid API key - please check your credentials",
                    4: "API pending for activation - please activate in Bitkub settings",
                    5: "IP not allowed - please add your IP address to whitelist",
                    6: "Missing / invalid signature",
                    7: "Missing timestamp",
                    8: "Invalid timestamp",
                    9: "Invalid user",
                    10: "Invalid parameter",
                    40: "Rate limit exceeded",
                    994: "HTTP error - server may be temporarily unavailable"
                }

                error_msg = error_messages.get(error_code, result.get('message', f"Error code {error_code}"))
                return {'error': error_code, 'message': error_msg}

        except Exception as e:
            return {'error': 999, 'message': f'Balance fetch error: {str(e)}'}

    def place_order(self, symbol, side, amount, rate, order_type="limit"):
        """Place order - REAL TRADING"""
        params = {
            "sym": symbol,
            "amt": amount,
            "rat": rate,
            "typ": order_type,
            "side": side
        }

        return self.make_request("POST", "/api/market/place-order", params, signed=True)

    def cancel_order(self, symbol, order_id, side):
        """Cancel order"""
        params = {
            "sym": symbol,
            "id": order_id,
            "sd": side
        }

        return self.make_request("POST", "/api/market/cancel-order", params, signed=True)

    def get_my_open_orders(self, symbol):
        """Get open orders"""
        params = {"sym": symbol}
        return self.make_request("POST", "/api/market/my-open-orders", params, signed=True)

    def get_my_open_orders_safe(self, symbol):
        """Safely get open orders"""
        try:
            result = self.get_my_open_orders(symbol)
            if result and result.get('error') == 0:
                return result
            else:
                error_code = result.get('error', 999)
                error_msg = self.error_codes.get(error_code, f"Unknown error {error_code}")
                return {'error': error_code, 'message': error_msg}

        except Exception as e:
            return {'error': 999, 'message': f'Open orders fetch error: {str(e)}'}

    def get_order_history(self, symbol, limit=10):
        """Get order history"""
        params = {
            "sym": symbol,
            "lmt": limit
        }
        return self.make_request("POST", "/api/market/my-order-history", params, signed=True)


# ============================================================================
# 🧠 Enhanced Trading Strategy
# ============================================================================

class EnhancedTradingStrategy:
    """Enhanced Trading Strategy with Fee Awareness"""

    def __init__(self, api_client):
        self.api_client = api_client
        self.min_profit_threshold = 0.006  # 0.6% minimum profit (after fees)

    def calculate_break_even_price(self, buy_price, fees):
        """Calculate break-even price after fees"""
        total_fee_rate = fees['maker_fee'] + fees['taker_fee']
        break_even_price = buy_price * (1 + total_fee_rate + 0.001)  # +0.1% safety margin
        return break_even_price

    def analyze_market_condition(self, symbol):
        """Analyze current market condition"""
        try:
            # Get market data
            ticker_data = self.api_client.get_market_data(symbol)
            depth_data = self.api_client.get_market_depth(symbol, 10)

            if not ticker_data or ticker_data.get('error') != 0:
                return 'UNKNOWN'

            if not depth_data or depth_data.get('error') != 0:
                return 'UNKNOWN'

            ticker = ticker_data.get('result', {}).get(symbol.upper(), {})
            depth = depth_data.get('result', {})

            # Calculate indicators
            last_price = float(ticker.get('last', 0))
            volume_24h = float(ticker.get('baseVolume', 0))
            price_change_24h = float(ticker.get('percentChange', 0))

            # Get order book data
            bids = depth.get('bids', [])
            asks = depth.get('asks', [])

            if not bids or not asks:
                return 'UNKNOWN'

            best_bid = float(bids[0][0]) if bids else 0
            best_ask = float(asks[0][0]) if asks else 0
            spread = ((best_ask - best_bid) / best_bid) * 100 if best_bid > 0 else 0

            # Simple condition logic
            condition = 'SIDEWAYS'

            if price_change_24h > 2 and volume_24h > 1000000 and spread < 0.5:
                condition = 'BULLISH'
            elif price_change_24h < -2 and volume_24h > 1000000:
                condition = 'BEARISH'
            elif spread > 1.0 or volume_24h < 100000:
                condition = 'LOW_LIQUIDITY'

            time.sleep(0.5)  # Rate limiting

            return condition

        except Exception as e:
            print(f"Market analysis error: {e}")
            return 'UNKNOWN'

    def should_buy(self, symbol, balance_thb):
        """Determine if should buy"""
        try:
            condition = self.analyze_market_condition(symbol)

            # Only buy in favorable conditions
            if condition in ['BULLISH', 'SIDEWAYS'] and balance_thb > 1000:
                return True, f"Market condition: {condition}"
            else:
                return False, f"Unfavorable condition: {condition}"

        except Exception as e:
            return False, f"Analysis error: {str(e)}"

    def should_sell(self, symbol, buy_price, current_price, hold_time_minutes=0):
        """Determine if should sell with fee consideration"""
        try:
            fees = self.api_client.trading_fees
            break_even_price = self.calculate_break_even_price(buy_price, fees)

            # Calculate profit percentage
            if current_price > break_even_price:
                profit_percent = ((current_price - buy_price) / buy_price) * 100

                # Sell if profit > threshold or holding too long with small profit
                if profit_percent >= (self.min_profit_threshold * 100):
                    return True, f"Profit target reached: {profit_percent:.2f}%"
                elif hold_time_minutes > 60 and profit_percent > 0.2:
                    return True, f"Time-based sell: {profit_percent:.2f}% profit"

            # Stop-loss: sell if loss > 2%
            loss_percent = ((buy_price - current_price) / buy_price) * 100
            if loss_percent > 2.0:
                return True, f"Stop-loss triggered: -{loss_percent:.2f}%"

            return False, f"Hold position (P&L: {((current_price - buy_price) / buy_price) * 100:.2f}%)"

        except Exception as e:
            return False, f"Sell analysis error: {str(e)}"


# ============================================================================
# 🪙 Coin Recommendation System
# ============================================================================

class CoinRecommendationSystem:
    """AI-powered coin recommendation system"""

    def __init__(self, api_client):
        self.api_client = api_client
        self.analysis_cache = {}
        self.cache_duration = 300  # 5 minutes

    def get_all_active_symbols(self):
        """Get all active trading symbols"""
        try:
            ticker_data = self.api_client.get_market_data()
            if ticker_data and ticker_data.get('error') == 0:
                symbols = []
                result = ticker_data.get('result', {})

                for symbol, data in result.items():
                    # Check if it's a THB pair and has volume
                    if ('THB' in symbol.upper() and
                            isinstance(data, dict) and
                            float(data.get('baseVolume', 0)) > 1000):  # Minimum volume threshold
                        symbols.append(symbol.lower())

                # Sort by volume
                def get_volume(symbol):
                    symbol_upper = symbol.upper()
                    return float(result.get(symbol_upper, {}).get('baseVolume', 0))

                symbols.sort(key=get_volume, reverse=True)
                return symbols[:20]  # Top 20 by volume

            return ['btc_thb', 'eth_thb', 'ada_thb', 'xrp_thb']  # Fallback

        except Exception as e:
            print(f"Symbol fetch error: {e}")
            return ['btc_thb', 'eth_thb', 'ada_thb', 'xrp_thb']

    def analyze_coin(self, symbol):
        """Analyze individual coin"""
        try:
            # Check cache
            cache_key = f"{symbol}_{int(time.time() // self.cache_duration)}"
            if cache_key in self.analysis_cache:
                return self.analysis_cache[cache_key]

            # Get all market data first
            ticker_data = self.api_client.get_market_data()

            if not ticker_data or ticker_data.get('error') != 0:
                return {'score': 0, 'reason': f'API Error: {ticker_data.get("message", "Unknown error")}'}

            all_data = ticker_data.get('result', {})

            # Try to find the symbol in different formats
            symbol_upper = symbol.upper()
            possible_keys = [
                symbol_upper,  # BTC_THB
                symbol.lower(),  # btc_thb
                symbol_upper.replace('_', ''),  # BTCTHB
                f"THB_{symbol_upper.split('_')[0]}" if '_' in symbol_upper else symbol_upper
            ]

            ticker = None
            found_key = None
            for key in possible_keys:
                if key in all_data:
                    ticker = all_data[key]
                    found_key = key
                    break

            if not ticker or not isinstance(ticker, dict):
                available_symbols = [k for k in all_data.keys() if 'THB' in k.upper()][:10]
                return {
                    'score': 0,
                    'reason': f'Symbol {symbol_upper} not found. Available: {", ".join(available_symbols)}'
                }

            # Extract metrics with fallbacks
            try:
                price_change_24h = float(ticker.get('percentChange', 0))
            except (ValueError, TypeError):
                price_change_24h = 0

            try:
                volume_24h = float(ticker.get('baseVolume', 0))
            except (ValueError, TypeError):
                volume_24h = 0

            try:
                last_price = float(ticker.get('last', 0))
            except (ValueError, TypeError):
                last_price = 0

            try:
                high_24h = float(ticker.get('high24hr', 0))
            except (ValueError, TypeError):
                high_24h = 0

            try:
                low_24h = float(ticker.get('low24hr', 0))
            except (ValueError, TypeError):
                low_24h = 0

            # Calculate score
            score = 5.0  # Base score
            reasons = []

            # Volume factor (higher volume = better)
            if volume_24h > 5000000:
                score += 2.0
                reasons.append("High volume")
            elif volume_24h > 1000000:
                score += 1.0
                reasons.append("Good volume")
            elif volume_24h > 100000:
                score += 0.5
                reasons.append("Moderate volume")
            elif volume_24h < 10000:
                score -= 1.5
                reasons.append("Low volume")

            # Price change factor
            if 0.5 <= price_change_24h <= 5.0:
                score += 1.5
                reasons.append("Positive momentum")
            elif price_change_24h > 5.0:
                score += 0.5
                reasons.append("Strong momentum (risky)")
            elif price_change_24h < -3.0:
                score -= 1.0
                reasons.append("Negative momentum")
            elif price_change_24h < -10.0:
                score -= 2.0
                reasons.append("Strong downtrend")

            # Volatility factor
            if high_24h > 0 and low_24h > 0:
                volatility = ((high_24h - low_24h) / low_24h) * 100
                if 2 <= volatility <= 8:
                    score += 1.0
                    reasons.append("Good volatility")
                elif volatility > 15:
                    score -= 0.5
                    reasons.append("High volatility")

            # Price level check
            if last_price > 0:
                reasons.append(f"Current price: ฿{last_price:,.2f}")

            score = max(0, min(10, score))  # Clamp between 0-10

            result = {
                'score': round(score, 2),
                'reason': '; '.join(reasons) if reasons else 'Basic analysis completed',
                'metrics': {
                    'price_change_24h': price_change_24h,
                    'volume_24h': volume_24h,
                    'last_price': last_price,
                    'high_24h': high_24h,
                    'low_24h': low_24h,
                    'symbol_found': found_key
                }
            }

            # Cache result
            self.analysis_cache[cache_key] = result
            time.sleep(0.2)  # Rate limiting

            return result

        except Exception as e:
            return {'score': 0, 'reason': f'Analysis error: {str(e)}'}

    def get_best_recommendation(self, exclude_symbols=None):
        """Get best coin recommendation"""
        if exclude_symbols is None:
            exclude_symbols = []

        try:
            symbols = self.get_all_active_symbols()
            recommendations = []

            for symbol in symbols:
                if symbol not in exclude_symbols:
                    analysis = self.analyze_coin(symbol)
                    if analysis['score'] > 0:
                        recommendations.append({
                            'symbol': symbol,
                            'score': analysis['score'],
                            'reason': analysis['reason'],
                            'metrics': analysis.get('metrics', {})
                        })

            # Sort by score
            recommendations.sort(key=lambda x: x['score'], reverse=True)

            if recommendations:
                best = recommendations[0]
                return {
                    'success': True,
                    'symbol': best['symbol'],
                    'score': best['score'],
                    'reason': best['reason'],
                    'all_recommendations': recommendations[:5]
                }
            else:
                return {
                    'success': False,
                    'message': 'No suitable coins found',
                    'fallback_symbol': 'btc_thb'
                }

        except Exception as e:
            return {
                'success': False,
                'message': f'Recommendation error: {str(e)}',
                'fallback_symbol': 'btc_thb'
            }


# ============================================================================
# 🤖 Full Auto Trading System (from original Sci6.py)
# ============================================================================

class FullAutoTradingEngine:
    """🤖 ระบบ Full Auto Trading แบบครบครัน"""

    def __init__(self, api_client, initial_balance=1000):
        self.api_client = api_client
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.target_balance = initial_balance * 2  # เป้าหมายกำไร 100%

        # Trading state
        self.is_auto_trading = False
        self.trading_start_time = None
        self.current_positions = {}
        self.session_id = str(uuid.uuid4())[:8]

        # Performance tracking
        self.total_trades = 0
        self.winning_trades = 0
        self.max_drawdown = 0
        self.decisions_made = 0
        self.total_confidence = 0

        # Decision logger
        self.decision_logger = DecisionLogger()

    def start_auto_trading(self, target_hours=24):
        """เริ่มระบบ Auto Trading"""
        self.is_auto_trading = True
        self.trading_start_time = datetime.now()
        self.target_hours = target_hours

        self.log_decision("TRADING_START", {
            "initial_balance": self.initial_balance,
            "target_balance": self.target_balance,
            "target_hours": target_hours,
            "session_id": self.session_id
        })

        return True

    def stop_auto_trading(self):
        """หยุดระบบ Auto Trading"""
        self.is_auto_trading = False

        self.log_decision("TRADING_STOP", {
            "final_balance": self.current_balance,
            "total_pnl": self.current_balance - self.initial_balance,
            "total_trades": self.total_trades,
            "win_rate": (self.winning_trades / max(self.total_trades, 1)) * 100,
            "session_id": self.session_id
        })

    def make_trading_decision(self, market_data):
        """🧠 AI Decision Making Engine"""
        try:
            # Select coin for analysis
            selected_coin = self.select_best_coin()

            decision_data = {
                "timestamp": datetime.now().isoformat(),
                "selected_coin": selected_coin,
                "market_analysis": self.analyze_market_comprehensive(market_data),
                "risk_assessment": self.assess_risk_factors(),
                "technical_indicators": self.calculate_technical_indicators(market_data),
                "sentiment_score": self.analyze_market_sentiment(),
                "confidence": 0,
                "action": "HOLD",
                "symbol": selected_coin,
                "amount": 0
            }

            # คำนวณ confidence score
            total_score = (
                                  decision_data["market_analysis"]["score"] +
                                  decision_data["risk_assessment"]["score"] +
                                  decision_data["technical_indicators"]["score"] +
                                  decision_data["sentiment_score"]
                          ) / 4

            decision_data["confidence"] = min(max(total_score, 0), 10)
            self.decisions_made += 1

            # ตัดสินใจ Action based on coin analysis
            if total_score >= 7.5 and self.current_balance >= 500:
                decision_data["action"] = "BUY"
                decision_data["symbol"] = selected_coin
                decision_data["amount"] = min(self.current_balance * 0.3, 1000)

            elif total_score <= 3.5 and self.current_positions:
                decision_data["action"] = "SELL"
                # เลือก position ที่จะขาย
                if selected_coin in self.current_positions:
                    decision_data["symbol"] = selected_coin

            # บันทึก decision
            self.log_decision("TRADING_DECISION", {"decision": decision_data})

            return decision_data

        except Exception as e:
            error_decision = {
                "action": "ERROR",
                "symbol": "UNKNOWN",
                "error": str(e),
                "confidence": 0,
                "timestamp": datetime.now().isoformat()
            }

            self.log_decision("DECISION_ERROR", {"error": error_decision})
            return error_decision

    def analyze_market_comprehensive(self, market_data):
        """วิเคราะห์ตลาดแบบครบครัน พร้อมชื่อเหรียญ"""
        try:
            score = 5.0  # Base score

            # Technical Analysis
            technical_score = self.analyze_technical_factors()

            # Time Analysis
            time_score = self.analyze_time_factor()

            # Volume Analysis
            volume_score = self.analyze_volume_factor()

            # Volatility Analysis
            volatility_score = self.analyze_volatility_factor()

            # คำนวณคะแนนรวม
            total_score = (technical_score + time_score + volume_score + volatility_score) / 4

            return {
                "score": round(total_score, 2),
                "technical": technical_score,
                "time": time_score,
                "volume": volume_score,
                "volatility": volatility_score,
                "analysis_time": datetime.now().isoformat(),
                "market_condition": self.get_market_condition_text(total_score)
            }

        except Exception as e:
            return {"score": 5.0, "error": str(e), "market_condition": "Unknown"}

    def get_market_condition_text(self, score):
        """แปลงคะแนนเป็นข้อความสภาวะตลาด"""
        if score >= 8.0:
            return "Bullish Strong"
        elif score >= 6.5:
            return "Bullish Moderate"
        elif score >= 5.5:
            return "Neutral-Bullish"
        elif score >= 4.5:
            return "Neutral"
        elif score >= 3.5:
            return "Neutral-Bearish"
        elif score >= 2.0:
            return "Bearish Moderate"
        else:
            return "Bearish Strong"

    def assess_risk_factors(self):
        """ประเมินปัจจัยความเสี่ยง"""
        risk_score = 7.0  # Base risk score (7/10 = moderate risk)

        try:
            # Portfolio risk
            if len(self.current_positions) > 3:
                risk_score -= 1.0  # มี position เยอะเกินไป

            # Balance risk
            if self.current_balance < self.initial_balance * 0.8:
                risk_score -= 1.5  # เสียเงินมากเกินไป

            # Time risk
            elapsed_hours = self.get_elapsed_hours()
            if elapsed_hours > self.target_hours * 0.8:
                risk_score -= 0.5  # ใกล้หมดเวลา

            # Win rate risk
            win_rate = (self.winning_trades / max(self.total_trades, 1)) * 100
            if win_rate < 40:
                risk_score -= 1.0  # Win rate ต่ำ

            return {
                "score": max(0, min(10, risk_score)),
                "factors": {
                    "position_count": len(self.current_positions),
                    "balance_ratio": self.current_balance / self.initial_balance,
                    "elapsed_ratio": elapsed_hours / self.target_hours if self.target_hours > 0 else 0,
                    "win_rate": win_rate
                }
            }

        except Exception as e:
            return {"score": 5.0, "error": str(e)}

    def calculate_technical_indicators(self, market_data):
        """คำนวณ Technical Indicators"""
        try:
            # Mock implementation - ในระบบจริงจะใช้ข้อมูลจริง
            indicators = {
                "rsi": random.uniform(30, 70),
                "macd": random.uniform(-1, 1),
                "bollinger_position": random.uniform(0, 1),
                "volume_trend": random.uniform(0.5, 1.5)
            }

            # คำนวณคะแนนจาก indicators
            score = 5.0

            # RSI analysis
            if 40 <= indicators["rsi"] <= 60:
                score += 1.0
            elif indicators["rsi"] < 30:
                score += 1.5  # Oversold - good buy opportunity
            elif indicators["rsi"] > 70:
                score -= 1.0  # Overbought

            # MACD analysis
            if indicators["macd"] > 0:
                score += 0.5

            # Volume analysis
            if indicators["volume_trend"] > 1.2:
                score += 1.0

            return {
                "score": max(0, min(10, score)),
                "indicators": indicators
            }

        except Exception as e:
            return {"score": 5.0, "error": str(e)}

    def analyze_market_sentiment(self):
        """วิเคราะห์ Market Sentiment"""
        # Mock implementation - ในระบบจริงจะวิเคราะห์จาก news, social media
        sentiment_factors = [
            random.uniform(0, 10),  # News sentiment
            random.uniform(0, 10),  # Social media sentiment
            random.uniform(0, 10),  # Market momentum
            random.uniform(0, 10)  # Fear & Greed index
        ]

        return sum(sentiment_factors) / len(sentiment_factors)

    def select_best_coin(self):
        """เลือก Coin ที่ดีที่สุดสำหรับการซื้อ"""
        try:
            # Get top performing coins from current market data
            top_coins = [
                "thb_gala",  # Score: 9.5/10 from previous analysis
                "thb_doge",  # Score: 9.5/10
                "thb_alpha",  # High volume
                "thb_btc",  # Most stable
                "thb_eth",  # Second most stable
                "thb_ada",  # Good alternative
                "thb_xrp",  # Popular choice
                "thb_six",  # We have holdings
                "thb_kub"  # We have holdings
            ]

            # Prefer coins we already have some balance in for better tracking
            # But also consider high-performance new coins

            # Simple rotation to test different coins
            coin_index = (self.decisions_made % len(top_coins))
            selected = top_coins[coin_index]

            return selected

        except Exception as e:
            print(f"Coin selection error: {e}")
            return "thb_btc"  # Safe fallback

    def analyze_technical_factors(self):
        """วิเคราะห์ปัจจัยทางเทคนิค"""
        # Mock implementation - ในระบบจริงจะวิเคราะห์จากข้อมูลจริง
        factors = []

        # Price trend analysis
        factors.append(random.uniform(0, 10))

        # Volume analysis
        factors.append(random.uniform(0, 10))

        # Support/Resistance analysis
        factors.append(random.uniform(0, 10))

        # Moving averages
        factors.append(random.uniform(0, 10))

        return sum(factors) / len(factors)

    def analyze_time_factor(self):
        """วิเคราะห์ปัจจัยเวลา"""
        current_hour = datetime.now().hour
        current_day = datetime.now().weekday()  # 0=Monday, 6=Sunday

        score = 5.0  # Base score

        # เวลาในวัน
        if 9 <= current_hour <= 17:  # Business hours
            score += 1.5
        elif 19 <= current_hour <= 23:  # Evening active time
            score += 1.0
        elif 0 <= current_hour <= 6:  # Night time
            score -= 1.0

        # วันในสัปดาห์
        if current_day < 5:  # Weekday
            score += 0.5
        else:  # Weekend
            score -= 0.5

        return max(0, min(10, score))

    def analyze_volume_factor(self):
        """วิเคราะห์ปัจจัยปริมาณการเทรด"""
        # Mock implementation - ในระบบจริงจะดึงข้อมูล volume จริง
        random_volume_trend = random.uniform(0, 10)
        return random_volume_trend

    def analyze_volatility_factor(self):
        """วิเคราะห์ปัจจัยความผันผวน"""
        # Mock implementation - ในระบบจริงจะวิเคราะห์ volatility จริง
        random_volatility = random.uniform(0, 10)
        return random_volatility

    def log_decision(self, decision_type, data):
        """บันทึก Decision Log"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": decision_type,
            "data": data,
            "balance": self.current_balance,
            "positions": len(self.current_positions),
            "elapsed_hours": self.get_elapsed_hours()
        }

        # บันทึกผ่าน DecisionLogger
        self.decision_logger.save_decision(log_entry, self.session_id)

        # เก็บข้อมูล confidence สำหรับ tracking
        if decision_type == "TRADING_DECISION" and 'decision' in data:
            confidence = data['decision'].get('confidence', 0)
            self.total_confidence += confidence

    def get_elapsed_hours(self):
        """คำนวณเวลาที่เทรดผ่านไป"""
        if not self.trading_start_time:
            return 0
        return (datetime.now() - self.trading_start_time).total_seconds() / 3600

    def get_session_summary(self):
        """ดึงสรุปผล session ปัจจุบัน"""
        elapsed_hours = self.get_elapsed_hours()
        final_pnl = self.current_balance - self.initial_balance
        roi = (final_pnl / self.initial_balance) * 100 if self.initial_balance > 0 else 0
        win_rate = (self.winning_trades / max(self.total_trades, 1)) * 100

        return {
            "session_id": self.session_id,
            "status": "RUNNING" if self.is_auto_trading else "STOPPED",
            "elapsed_hours": elapsed_hours,
            "initial_balance": self.initial_balance,
            "current_balance": self.current_balance,
            "total_pnl": final_pnl,
            "roi_percentage": roi,
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "win_rate": win_rate,
            "active_positions": len(self.current_positions),
            "max_drawdown": self.max_drawdown,
            "decisions_made": self.decisions_made
        }


class DecisionLogger:
    """📝 ระบบบันทึก Decision Log แบบครบครัน"""

    def __init__(self):
        self.db_path = "full_auto_trading_decisions.db"
        self.log_file = f"full_auto_decisions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.init_database()

    def init_database(self):
        """สร้าง Database สำหรับเก็บ Decision Log"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS full_auto_decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    session_id TEXT,
                    decision_type TEXT NOT NULL,
                    coin_symbol TEXT,
                    action TEXT,
                    confidence REAL,
                    technical_score REAL,
                    volume_score REAL,
                    sentiment_score REAL,
                    risk_score REAL,
                    stability_score REAL,
                    total_score REAL,
                    balance REAL,
                    position_size REAL,
                    market_condition TEXT,
                    raw_data TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            conn.commit()
            conn.close()

        except Exception as e:
            print(f"Database initialization error: {e}")

    def save_decision(self, decision_data, session_id):
        """บันทึก Decision ลงฐานข้อมูล"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # แยกข้อมูลสำหรับบันทึก
            decision_info = decision_data.get('data', {})
            decision_detail = decision_info.get('decision', {}) if 'decision' in decision_info else {}

            cursor.execute('''
                INSERT INTO full_auto_decisions (
                    timestamp, session_id, decision_type, coin_symbol, action,
                    confidence, technical_score, volume_score, sentiment_score,
                    risk_score, total_score, balance, position_size,
                    market_condition, raw_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                decision_data.get('timestamp', datetime.now().isoformat()),
                session_id,
                decision_data.get('type', 'UNKNOWN'),
                decision_detail.get('symbol', ''),
                decision_detail.get('action', ''),
                decision_detail.get('confidence', 0),
                decision_detail.get('technical_indicators', {}).get('score', 0),
                decision_detail.get('market_analysis', {}).get('volume', 0),
                decision_detail.get('sentiment_score', 0),
                decision_detail.get('risk_assessment', {}).get('score', 0),
                decision_detail.get('confidence', 0),
                decision_data.get('balance', 0),
                decision_detail.get('amount', 0),
                decision_detail.get('market_analysis', {}).get('condition', ''),
                json.dumps(decision_data, ensure_ascii=False, indent=2)
            ))

            conn.commit()
            conn.close()

            # บันทึกลงไฟล์ JSON ด้วย
            self.save_to_json_file(decision_data, session_id)

        except Exception as e:
            print(f"Decision logging error: {e}")

    def save_to_json_file(self, decision_data, session_id):
        """บันทึกลงไฟล์ JSON"""
        try:
            log_entry = {
                "session_id": session_id,
                "logged_at": datetime.now().isoformat(),
                **decision_data
            }

            # อ่านไฟล์เดิม (ถ้ามี)
            logs = []
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)

            # เพิ่มข้อมูลใหม่
            logs.append(log_entry)

            # เขียนกลับลงไฟล์
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"JSON file logging error: {e}")

    def get_session_decisions(self, session_id, limit=50):
        """ดึงข้อมูล Decision ของ session"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT * FROM full_auto_decisions 
                WHERE session_id = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (session_id, limit))

            columns = [description[0] for description in cursor.description]
            results = []

            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))

            conn.close()
            return results

        except Exception as e:
            print(f"Session decisions fetch error: {e}")
            return []


class PerformanceAnalyzer:
    """📊 ระบบวิเคราะห์ผลการเทรด"""

    def __init__(self):
        self.decision_logger = DecisionLogger()

    def analyze_session_performance(self, session_id):
        """วิเคราะห์ผลการเทรดของ session"""
        try:
            decisions = self.decision_logger.get_session_decisions(session_id)

            if not decisions:
                return {
                    "error": "No decisions found for this session",
                    "session_id": session_id
                }

            # คำนวณสถิติต่างๆ
            analysis = {
                "session_id": session_id,
                "total_decisions": len(decisions),
                "decision_types": {},
                "confidence_stats": {},
                "time_analysis": {},
                "performance_summary": {},
                "recommendations": []
            }

            # นับประเภทการตัดสินใจ
            for decision in decisions:
                decision_type = decision.get('decision_type', 'UNKNOWN')
                analysis["decision_types"][decision_type] = analysis["decision_types"].get(decision_type, 0) + 1

            # วิเคราะห์ confidence
            confidences = [d.get('confidence', 0) for d in decisions if d.get('confidence', 0) > 0]
            if confidences:
                analysis["confidence_stats"] = {
                    "average": sum(confidences) / len(confidences),
                    "max": max(confidences),
                    "min": min(confidences),
                    "count": len(confidences)
                }

            # สร้างคำแนะนำ
            analysis["recommendations"] = self.generate_recommendations(decisions)

            return analysis

        except Exception as e:
            return {"error": f"Performance analysis error: {str(e)}"}

    def generate_recommendations(self, decisions):
        """สร้างคำแนะนำจากการวิเคราะห์"""
        recommendations = []

        try:
            # วิเคราะห์ confidence level
            confidences = [d.get('confidence', 0) for d in decisions if d.get('confidence', 0) > 0]
            if confidences:
                avg_confidence = sum(confidences) / len(confidences)
                if avg_confidence < 5:
                    recommendations.append({
                        "type": "CONFIDENCE",
                        "message": "Average confidence is low. Consider more conservative trading.",
                        "suggestion": "Increase minimum confidence threshold for trading decisions."
                    })
                elif avg_confidence > 8:
                    recommendations.append({
                        "type": "CONFIDENCE",
                        "message": "High confidence levels detected. Good decision making.",
                        "suggestion": "Continue current analysis methodology."
                    })

            # วิเคราะห์ประเภทการตัดสินใจ
            decision_counts = {}
            for decision in decisions:
                dtype = decision.get('decision_type', 'UNKNOWN')
                decision_counts[dtype] = decision_counts.get(dtype, 0) + 1

            if decision_counts.get('TRADING_DECISION', 0) < 5:
                recommendations.append({
                    "type": "ACTIVITY",
                    "message": "Low trading activity detected.",
                    "suggestion": "Consider adjusting market analysis parameters for more opportunities."
                })

        except Exception as e:
            recommendations.append({
                "type": "ERROR",
                "message": f"Error generating recommendations: {str(e)}",
                "suggestion": "Check system logs for details."
            })

        return recommendations


# ============================================================================
# 🎯 Complete Enhanced Trading Bot with Integrated UI
# ============================================================================

class EnhancedTradingBot:
    """🚀 Complete Enhanced Trading Bot with Integrated UI System"""

    def __init__(self):
        # License check (commented out for demo)
        # self.check_license()

        # Initialize main window
        self.root = ctk.CTk()
        self.root.title("🚀 Sci6 Enhanced Trading Bot - Complete System")
        self.root.geometry("1600x1000")

        # Core components
        self.api_client = None
        self.strategy = None
        self.coin_recommender = None
        self.scifi_visual = None
        self.full_auto_engine = None
        self.performance_analyzer = PerformanceAnalyzer()

        # Trading state
        self.is_trading = False
        self.is_paper_trading = True
        self.emergency_stop = False
        self.daily_trades = 0
        self.daily_pnl = 0.0
        self.total_fees_paid = 0.0
        self.last_trade_time = None

        # Database
        self.db_path = "sci6_enhanced_trading_bot.db"

        # Configuration
        self.config = {
            'symbol': 'btc_thb',
            'trade_amount_thb': 1000,
            'max_daily_trades': 3,
            'max_daily_loss': 500,
            'use_coin_recommendation': False,
            'auto_trading': False
        }

        # UI Variables
        self.setup_variables()

        # Initialize database and UI
        self.init_database()
        self.setup_enhanced_ui()

    def setup_variables(self):
        """Initialize all UI control variables"""
        self.paper_trading_var = ctk.BooleanVar(value=True)
        self.real_trading_var = ctk.BooleanVar(value=False)
        self.coin_rec_var = ctk.BooleanVar(value=False)
        self.auto_trading_var = ctk.BooleanVar(value=False)
        self.emergency_stop_var = ctk.BooleanVar(value=False)

        # Full auto variables
        self.auto_balance_var = ctk.StringVar(value="1000")
        self.auto_hours_var = ctk.StringVar(value="24")
        self.auto_profit_var = ctk.StringVar(value="100")

    def init_database(self):
        """Initialize enhanced database structure"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
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
                api_response TEXT,
                ai_score REAL DEFAULT 0,
                recommendation TEXT DEFAULT ""
            )
        ''')

        conn.commit()
        conn.close()

    def setup_enhanced_ui(self):
        """Setup the complete enhanced UI system"""

        # Warning banner
        self.setup_warning_banner()

        # Main container with sidebar navigation
        self.main_container = ctk.CTkFrame(self.root)
        self.main_container.pack(fill="both", expand=True, padx=10, pady=5)

        # Create tabbed interface
        self.setup_tabbed_interface()

        # Initialize with main tab
        self.setup_main_tab()
        self.setup_configuration_tab()
        self.setup_trading_tab()
        self.setup_coin_analysis_tab()
        self.setup_full_auto_tab()
        self.setup_testing_tab()
        self.setup_history_tab()

    def setup_warning_banner(self):
        """Setup danger warning banner"""
        warning_frame = ctk.CTkFrame(self.root, fg_color="red", height=50)
        warning_frame.pack(fill="x", padx=10, pady=5)
        warning_frame.pack_propagate(False)

        warning_text = "🔥 REAL TRADING CAPABLE BOT - CAN USE ACTUAL MONEY! USE WITH EXTREME CAUTION! 🔥"
        ctk.CTkLabel(
            warning_frame,
            text=warning_text,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="white"
        ).pack(pady=10)

    def setup_tabbed_interface(self):
        """Setup tabbed interface"""
        self.notebook = ctk.CTkTabview(self.main_container)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Create tabs
        self.tab_main = self.notebook.add("📊 Dashboard")
        self.tab_config = self.notebook.add("🔧 Configuration")
        self.tab_trading = self.notebook.add("📈 Trading Control")
        self.tab_coin_analysis = self.notebook.add("🪙 Coin Analysis")
        self.tab_full_auto = self.notebook.add("🤖 Full Auto")
        self.tab_testing = self.notebook.add("⚙️ API Testing")
        self.tab_history = self.notebook.add("📜 History")

    def setup_main_tab(self):
        """Setup main dashboard tab"""
        main_frame = ctk.CTkFrame(self.tab_main)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Title
        ctk.CTkLabel(
            main_frame,
            text="🚀 Sci6 Enhanced Trading Bot Dashboard",
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(pady=20)

        # Create main layout with left panel and sci-fi visual
        content_frame = ctk.CTkFrame(main_frame)
        content_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Left side - Controls and stats
        left_frame = ctk.CTkFrame(content_frame)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

        # Quick stats
        stats_frame = ctk.CTkFrame(left_frame)
        stats_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(stats_frame, text="📊 Quick Statistics", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)

        # Stats grid
        stats_grid = ctk.CTkFrame(stats_frame)
        stats_grid.pack(fill="x", padx=10, pady=10)

        # Balance
        balance_frame = ctk.CTkFrame(stats_grid)
        balance_frame.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        ctk.CTkLabel(balance_frame, text="💰 Balance", font=ctk.CTkFont(weight="bold")).pack()
        self.balance_label = ctk.CTkLabel(balance_frame, text="฿0.00", font=ctk.CTkFont(size=18))
        self.balance_label.pack()

        # Daily P&L
        pnl_frame = ctk.CTkFrame(stats_grid)
        pnl_frame.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkLabel(pnl_frame, text="📈 Daily P&L", font=ctk.CTkFont(weight="bold")).pack()
        self.pnl_label = ctk.CTkLabel(pnl_frame, text="฿0.00", font=ctk.CTkFont(size=18))
        self.pnl_label.pack()

        # Trades
        trades_frame = ctk.CTkFrame(stats_grid)
        trades_frame.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        ctk.CTkLabel(trades_frame, text="🔄 Trades Today", font=ctk.CTkFont(weight="bold")).pack()
        self.trades_label = ctk.CTkLabel(trades_frame, text="0/3", font=ctk.CTkFont(size=18))
        self.trades_label.pack()

        # Status
        status_frame = ctk.CTkFrame(stats_grid)
        status_frame.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkLabel(status_frame, text="⚡ Status", font=ctk.CTkFont(weight="bold")).pack()
        self.status_label = ctk.CTkLabel(status_frame, text="Ready", font=ctk.CTkFont(size=18))
        self.status_label.pack()

        stats_grid.grid_columnconfigure(0, weight=1)
        stats_grid.grid_columnconfigure(1, weight=1)

        # Quick action buttons
        actions_frame = ctk.CTkFrame(left_frame)
        actions_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(actions_frame, text="⚡ Quick Actions", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)

        buttons_frame = ctk.CTkFrame(actions_frame)
        buttons_frame.pack(fill="x", padx=10, pady=10)

        quick_buttons = [
            ("🔌 Connect API", self.quick_connect_api, "blue"),
            ("▶️ Start Trading", self.quick_start_trading, "green"),
            ("⏹️ Stop Trading", self.quick_stop_trading, "red"),
            ("📊 Refresh Data", self.quick_refresh_data, "orange")
        ]

        for i, (text, command, color) in enumerate(quick_buttons):
            btn = ctk.CTkButton(
                buttons_frame,
                text=text,
                command=command,
                fg_color=color,
                width=120
            )
            btn.grid(row=i // 2, column=i % 2, padx=5, pady=5, sticky="ew")

        buttons_frame.grid_columnconfigure(0, weight=1)
        buttons_frame.grid_columnconfigure(1, weight=1)

        # Activity log
        log_frame = ctk.CTkFrame(left_frame)
        log_frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(log_frame, text="📋 Activity Log", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)

        self.main_log_display = ctk.CTkTextbox(log_frame, height=250)
        self.main_log_display.pack(fill="both", expand=True, padx=10, pady=10)

        # Right side - Sci-Fi Visual System
        right_frame = ctk.CTkFrame(content_frame, width=320)
        right_frame.pack(side="right", fill="y", padx=(10, 0))
        right_frame.pack_propagate(False)

        ctk.CTkLabel(
            right_frame,
            text="🎬 Sci-Fi Visual System",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=10)

        # Initialize Sci-Fi Visual System
        visual_frame = ctk.CTkFrame(right_frame)
        visual_frame.pack(padx=10, pady=10)

        self.scifi_visual = SciFiVisualSystem(visual_frame)

        # Visual controls
        visual_controls_frame = ctk.CTkFrame(right_frame)
        visual_controls_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(visual_controls_frame, text="🎮 Visual Controls", font=ctk.CTkFont(weight="bold")).pack(pady=5)

        visual_states = [
            ("🔘 Idle", "idle"),
            ("🔌 Connecting", "connecting"),
            ("🔍 Analyzing", "analyzing"),
            ("📈 Buy Signal", "buy_signal"),
            ("📉 Sell Signal", "sell_signal"),
            ("⚡ Trading", "trading")
        ]

        for text, state in visual_states:
            btn = ctk.CTkButton(
                visual_controls_frame,
                text=text,
                command=lambda s=state: self.test_visual_state(s),
                width=100,
                height=25
            )
            btn.pack(pady=2)

    def setup_configuration_tab(self):
        """Setup configuration tab"""
        config_frame = ctk.CTkFrame(self.tab_config)
        config_frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(
            config_frame,
            text="🔧 Bot Configuration",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=20)

        # Scrollable configuration area
        config_scroll = ctk.CTkScrollableFrame(config_frame)
        config_scroll.pack(fill="both", expand=True, padx=20, pady=10)

        # API Configuration Section
        api_section = ctk.CTkFrame(config_scroll)
        api_section.pack(fill="x", pady=10)

        ctk.CTkLabel(api_section, text="🔑 API Configuration", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)

        api_grid = ctk.CTkFrame(api_section)
        api_grid.pack(fill="x", padx=20, pady=10)

        # API Key
        ctk.CTkLabel(api_grid, text="API Key:").grid(row=0, column=0, sticky="w", padx=10, pady=10)
        self.api_key_entry = ctk.CTkEntry(api_grid, width=350, show="*", placeholder_text="Enter your Bitkub API Key")
        self.api_key_entry.grid(row=0, column=1, padx=10, pady=10)

        # Secret Key
        ctk.CTkLabel(api_grid, text="Secret Key:").grid(row=1, column=0, sticky="w", padx=10, pady=10)
        self.secret_key_entry = ctk.CTkEntry(api_grid, width=350, show="*",
                                             placeholder_text="Enter your Bitkub Secret Key")
        self.secret_key_entry.grid(row=1, column=1, padx=10, pady=10)

        # Connect button
        ctk.CTkButton(
            api_grid,
            text="🔌 Connect to API",
            command=self.connect_api,
            width=150,
            height=40
        ).grid(row=2, column=0, columnspan=2, pady=20)

        # Trading Configuration Section
        trading_section = ctk.CTkFrame(config_scroll)
        trading_section.pack(fill="x", pady=10)

        ctk.CTkLabel(trading_section, text="💰 Trading Configuration", font=ctk.CTkFont(size=18, weight="bold")).pack(
            pady=10)

        trading_grid = ctk.CTkFrame(trading_section)
        trading_grid.pack(fill="x", padx=20, pady=10)

        # Symbol
        ctk.CTkLabel(trading_grid, text="Trading Symbol:").grid(row=0, column=0, sticky="w", padx=10, pady=10)
        self.symbol_combo = ctk.CTkComboBox(
            trading_grid,
            values=["BTC_THB", "ETH_THB", "ADA_THB", "XRP_THB", "BNB_THB", "DOGE_THB"],
            width=200
        )
        self.symbol_combo.grid(row=0, column=1, padx=10, pady=10)
        self.symbol_combo.set("BTC_THB")

        # Trade amount
        ctk.CTkLabel(trading_grid, text="Trade Amount (THB):").grid(row=1, column=0, sticky="w", padx=10, pady=10)
        self.trade_amount_entry = ctk.CTkEntry(trading_grid, width=200, placeholder_text="1000")
        self.trade_amount_entry.grid(row=1, column=1, padx=10, pady=10)
        self.trade_amount_entry.insert(0, "1000")

        # Max daily trades
        ctk.CTkLabel(trading_grid, text="Max Daily Trades:").grid(row=2, column=0, sticky="w", padx=10, pady=10)
        self.max_trades_entry = ctk.CTkEntry(trading_grid, width=200, placeholder_text="3")
        self.max_trades_entry.grid(row=2, column=1, padx=10, pady=10)
        self.max_trades_entry.insert(0, "3")

        # Max daily loss
        ctk.CTkLabel(trading_grid, text="Max Daily Loss (THB):").grid(row=3, column=0, sticky="w", padx=10, pady=10)
        self.max_loss_entry = ctk.CTkEntry(trading_grid, width=200, placeholder_text="500")
        self.max_loss_entry.grid(row=3, column=1, padx=10, pady=10)
        self.max_loss_entry.insert(0, "500")

        # Save button
        ctk.CTkButton(
            trading_grid,
            text="💾 Save Configuration",
            command=self.save_configuration,
            width=200,
            height=40
        ).grid(row=4, column=0, columnspan=2, pady=20)

    def setup_trading_tab(self):
        """Setup trading control tab"""
        trading_frame = ctk.CTkFrame(self.tab_trading)
        trading_frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(
            trading_frame,
            text="📈 Trading Control Center",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=20)

        # Trading mode section
        mode_section = ctk.CTkFrame(trading_frame)
        mode_section.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(mode_section, text="🎮 Trading Mode Selection", font=ctk.CTkFont(size=16, weight="bold")).pack(
            pady=10)

        mode_buttons_frame = ctk.CTkFrame(mode_section)
        mode_buttons_frame.pack(pady=20)

        # Paper trading switch
        self.paper_switch = ctk.CTkSwitch(
            mode_buttons_frame,
            text="📝 Paper Trading Mode (SAFE)",
            variable=self.paper_trading_var,
            command=self.toggle_paper_trading,
            font=ctk.CTkFont(size=14)
        )
        self.paper_switch.pack(pady=10)

        # Real trading switch with warning
        self.real_switch = ctk.CTkSwitch(
            mode_buttons_frame,
            text="🔥 REAL TRADING MODE (DANGER!)",
            variable=self.real_trading_var,
            command=self.toggle_real_trading,
            button_color="red",
            progress_color="darkred",
            font=ctk.CTkFont(size=14)
        )
        self.real_switch.pack(pady=10)

        # Trading controls section
        controls_section = ctk.CTkFrame(trading_frame)
        controls_section.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(controls_section, text="🎯 Trading Controls", font=ctk.CTkFont(size=16, weight="bold")).pack(
            pady=10)

        controls_grid = ctk.CTkFrame(controls_section)
        controls_grid.pack(pady=20)

        control_buttons = [
            ("▶️ Start Trading", self.start_manual_trading, "green"),
            ("⏸️ Pause Trading", self.pause_trading, "orange"),
            ("⏹️ Stop Trading", self.stop_trading, "red"),
            ("🔄 Reset Stats", self.reset_daily_stats, "blue")
        ]

        for i, (text, command, color) in enumerate(control_buttons):
            btn = ctk.CTkButton(
                controls_grid,
                text=text,
                command=command,
                fg_color=color,
                width=150,
                height=40
            )
            btn.grid(row=i // 2, column=i % 2, padx=10, pady=10)

        controls_grid.grid_columnconfigure(0, weight=1)
        controls_grid.grid_columnconfigure(1, weight=1)

        # Emergency controls
        emergency_section = ctk.CTkFrame(trading_frame)
        emergency_section.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(emergency_section, text="🚨 Emergency Controls", font=ctk.CTkFont(size=16, weight="bold")).pack(
            pady=10)

        emergency_btn = ctk.CTkButton(
            emergency_section,
            text="🚨 EMERGENCY STOP ALL TRADING 🚨",
            command=self.emergency_stop_trading,
            fg_color="darkred",
            hover_color="red",
            width=400,
            height=50,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        emergency_btn.pack(pady=20)

        # Trading log
        log_section = ctk.CTkFrame(trading_frame)
        log_section.pack(fill="both", expand=True, padx=20, pady=10)

        ctk.CTkLabel(log_section, text="📋 Trading Log", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)

        self.trading_log_display = ctk.CTkTextbox(log_section, height=200)
        self.trading_log_display.pack(fill="both", expand=True, padx=10, pady=10)

    def setup_coin_analysis_tab(self):
        """Setup coin analysis tab"""
        coin_frame = ctk.CTkFrame(self.tab_coin_analysis)
        coin_frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(
            coin_frame,
            text="🪙 Coin Analysis Center",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=20)

        # Auto recommendation toggle
        auto_section = ctk.CTkFrame(coin_frame)
        auto_section.pack(fill="x", padx=20, pady=10)

        self.coin_rec_switch = ctk.CTkSwitch(
            auto_section,
            text="🤖 Enable Auto Coin Recommendation",
            variable=self.coin_rec_var,
            command=self.toggle_coin_recommendation,
            font=ctk.CTkFont(size=14)
        )
        self.coin_rec_switch.pack(pady=20)

        # Manual analysis section
        manual_section = ctk.CTkFrame(coin_frame)
        manual_section.pack(fill="both", expand=True, padx=20, pady=10)

        ctk.CTkLabel(manual_section, text="📊 Manual Coin Analysis", font=ctk.CTkFont(size=16, weight="bold")).pack(
            pady=10)

        # Analysis controls
        analysis_controls = ctk.CTkFrame(manual_section)
        analysis_controls.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(analysis_controls, text="Select Coin to Analyze:").pack(side="left", padx=10)

        self.analysis_coin_combo = ctk.CTkComboBox(
            analysis_controls,
            values=["BTC_THB", "ETH_THB", "ADA_THB", "XRP_THB", "BNB_THB", "DOGE_THB", "SOL_THB"],
            width=150
        )
        self.analysis_coin_combo.pack(side="left", padx=10)

        ctk.CTkButton(
            analysis_controls,
            text="📈 Analyze Coin",
            command=self.analyze_selected_coin,
            width=120
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            analysis_controls,
            text="🔍 Get Best Recommendation",
            command=self.get_coin_recommendation,
            width=180
        ).pack(side="left", padx=10)

        # Results display
        results_frame = ctk.CTkFrame(manual_section)
        results_frame.pack(fill="both", expand=True, padx=20, pady=10)

        ctk.CTkLabel(results_frame, text="📊 Analysis Results", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)

        self.coin_analysis_results = ctk.CTkTextbox(results_frame, height=300)
        self.coin_analysis_results.pack(fill="both", expand=True, padx=10, pady=10)

    def setup_full_auto_tab(self):
        """Setup full auto trading tab"""
        auto_frame = ctk.CTkFrame(self.tab_full_auto)
        auto_frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(
            auto_frame,
            text="🤖 Full Auto Trading System",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=20)

        # Configuration section
        config_section = ctk.CTkFrame(auto_frame)
        config_section.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(config_section, text="⚙️ Auto Trading Configuration",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)

        config_grid = ctk.CTkFrame(config_section)
        config_grid.pack(pady=20)

        # Initial balance
        ctk.CTkLabel(config_grid, text="Initial Balance (THB):").grid(row=0, column=0, sticky="w", padx=10, pady=10)
        self.auto_balance_entry = ctk.CTkEntry(config_grid, textvariable=self.auto_balance_var, width=150)
        self.auto_balance_entry.grid(row=0, column=1, padx=10, pady=10)

        # Trading hours
        ctk.CTkLabel(config_grid, text="Trading Hours:").grid(row=0, column=2, sticky="w", padx=10, pady=10)
        self.auto_hours_entry = ctk.CTkEntry(config_grid, textvariable=self.auto_hours_var, width=100)
        self.auto_hours_entry.grid(row=0, column=3, padx=10, pady=10)

        # Target profit
        ctk.CTkLabel(config_grid, text="Target Profit (%):").grid(row=1, column=0, sticky="w", padx=10, pady=10)
        self.auto_profit_entry = ctk.CTkEntry(config_grid, textvariable=self.auto_profit_var, width=150)
        self.auto_profit_entry.grid(row=1, column=1, padx=10, pady=10)

        # Auto trading toggle
        self.auto_trading_switch = ctk.CTkSwitch(
            config_grid,
            text="🤖 Enable Full Auto Trading",
            variable=self.auto_trading_var,
            command=self.toggle_auto_trading,
            font=ctk.CTkFont(size=14)
        )
        self.auto_trading_switch.grid(row=1, column=2, columnspan=2, pady=10)

        # Control buttons
        controls_section = ctk.CTkFrame(auto_frame)
        controls_section.pack(fill="x", padx=20, pady=10)

        controls_grid = ctk.CTkFrame(controls_section)
        controls_grid.pack(pady=20)

        auto_buttons = [
            ("🚀 Start Full Auto", self.start_full_auto_trading, "green"),
            ("⏹️ Stop Full Auto", self.stop_full_auto_trading, "red"),
            ("📊 Show Performance", self.show_full_auto_performance, "blue"),
            ("🔄 Reset Session", self.reset_full_auto_session, "orange")
        ]

        for i, (text, command, color) in enumerate(auto_buttons):
            btn = ctk.CTkButton(
                controls_grid,
                text=text,
                command=command,
                fg_color=color,
                width=150,
                height=40
            )
            btn.grid(row=i // 2, column=i % 2, padx=10, pady=10)

        controls_grid.grid_columnconfigure(0, weight=1)
        controls_grid.grid_columnconfigure(1, weight=1)

        # Status display
        status_section = ctk.CTkFrame(auto_frame)
        status_section.pack(fill="both", expand=True, padx=20, pady=10)

        ctk.CTkLabel(status_section, text="📊 Auto Trading Status", font=ctk.CTkFont(size=16, weight="bold")).pack(
            pady=10)

        self.full_auto_status_display = ctk.CTkTextbox(status_section, height=250)
        self.full_auto_status_display.pack(fill="both", expand=True, padx=10, pady=10)

    def setup_testing_tab(self):
        """Setup API testing tab"""
        test_frame = ctk.CTkFrame(self.tab_testing)
        test_frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(
            test_frame,
            text="⚙️ API Testing Center",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=20)

        # Test buttons grid
        buttons_section = ctk.CTkFrame(test_frame)
        buttons_section.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(buttons_section, text="🧪 Available Tests", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)

        test_grid = ctk.CTkFrame(buttons_section)
        test_grid.pack(pady=20)

        test_buttons = [
            ("🔌 Test Connection", self.test_connection),
            ("💰 Test Balance", self.test_balance),
            ("📊 Test Market Data", self.test_market_data),
            ("📈 Test Order Book", self.test_order_book),
            ("📋 Test Open Orders", self.test_open_orders),
            ("🎬 Test Sci-Fi Visuals", self.test_scifi_cycle)
        ]

        for i, (text, command) in enumerate(test_buttons):
            btn = ctk.CTkButton(
                test_grid,
                text=text,
                command=command,
                width=180,
                height=40
            )
            btn.grid(row=i // 3, column=i % 3, padx=10, pady=10)

        # Results display
        results_section = ctk.CTkFrame(test_frame)
        results_section.pack(fill="both", expand=True, padx=20, pady=10)

        ctk.CTkLabel(results_section, text="📊 Test Results", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)

        self.test_results_display = ctk.CTkTextbox(results_section, height=300)
        self.test_results_display.pack(fill="both", expand=True, padx=10, pady=10)

    def setup_history_tab(self):
        """Setup trading history tab"""
        history_frame = ctk.CTkFrame(self.tab_history)
        history_frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(
            history_frame,
            text="📜 Trading History & Analytics",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=20)

        # Filter controls
        filter_section = ctk.CTkFrame(history_frame)
        filter_section.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(filter_section, text="🔍 Filters", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)

        filter_controls = ctk.CTkFrame(filter_section)
        filter_controls.pack(pady=10)

        # Date filters
        ctk.CTkLabel(filter_controls, text="Date Range:").grid(row=0, column=0, padx=10, pady=5)
        self.date_from_entry = ctk.CTkEntry(filter_controls, placeholder_text="YYYY-MM-DD", width=120)
        self.date_from_entry.grid(row=0, column=1, padx=5, pady=5)
        ctk.CTkLabel(filter_controls, text="to").grid(row=0, column=2, padx=5, pady=5)
        self.date_to_entry = ctk.CTkEntry(filter_controls, placeholder_text="YYYY-MM-DD", width=120)
        self.date_to_entry.grid(row=0, column=3, padx=5, pady=5)

        # Symbol filter
        ctk.CTkLabel(filter_controls, text="Symbol:").grid(row=1, column=0, padx=10, pady=5)
        self.history_symbol_combo = ctk.CTkComboBox(
            filter_controls,
            values=["All", "BTC_THB", "ETH_THB", "ADA_THB", "XRP_THB"],
            width=120
        )
        self.history_symbol_combo.grid(row=1, column=1, padx=5, pady=5)

        # Filter buttons
        ctk.CTkButton(
            filter_controls,
            text="🔍 Apply Filter",
            command=self.apply_history_filter,
            width=100
        ).grid(row=1, column=2, padx=10, pady=5)

        ctk.CTkButton(
            filter_controls,
            text="🔄 Refresh",
            command=self.refresh_trade_history,
            width=100
        ).grid(row=1, column=3, padx=10, pady=5)

        # History display
        history_section = ctk.CTkFrame(history_frame)
        history_section.pack(fill="both", expand=True, padx=20, pady=10)

        # Create treeview for history
        columns = ("Time", "Symbol", "Side", "Amount", "Price", "Total", "P&L", "Status")

        self.history_tree = ttk.Treeview(history_section, columns=columns, show="headings", height=15)

        for col in columns:
            self.history_tree.heading(col, text=col)
            self.history_tree.column(col, width=100)

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(history_section, orient="vertical", command=self.history_tree.yview)
        h_scrollbar = ttk.Scrollbar(history_section, orient="horizontal", command=self.history_tree.xview)

        self.history_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # Pack elements
        self.history_tree.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        v_scrollbar.grid(row=0, column=1, sticky="ns", pady=10)
        h_scrollbar.grid(row=1, column=0, sticky="ew", padx=10)

        history_section.grid_rowconfigure(0, weight=1)
        history_section.grid_columnconfigure(0, weight=1)

    # ========================================================================
    # 🎯 Core Functionality Methods
    # ========================================================================

    def log_message(self, message, log_type="main"):
        """Add message to appropriate log display"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"

        try:
            if log_type == "main" and hasattr(self, 'main_log_display'):
                self.main_log_display.insert("end", log_entry)
                self.main_log_display.see("end")
            elif log_type == "trading" and hasattr(self, 'trading_log_display'):
                self.trading_log_display.insert("end", log_entry)
                self.trading_log_display.see("end")
            elif log_type == "auto" and hasattr(self, 'full_auto_status_display'):
                self.full_auto_status_display.insert("end", log_entry)
                self.full_auto_status_display.see("end")

            # Also log to main if not main
            if log_type != "main" and hasattr(self, 'main_log_display'):
                self.main_log_display.insert("end", log_entry)
                self.main_log_display.see("end")

        except Exception as e:
            print(f"Logging error: {e}")

    def update_status_displays(self):
        """Update all status displays"""
        try:
            # Update balance label
            if hasattr(self, 'balance_label'):
                balance_text = "฿0.00"
                if self.api_client:
                    # Get real balance from API
                    try:
                        balance_result = self.api_client.get_balances_safe()
                        if balance_result and balance_result.get('error') == 0:
                            balances = balance_result.get('result', {})
                            thb_balance = balances.get('THB', {})
                            if thb_balance and thb_balance.get('total', 0) > 0:
                                balance_text = f"฿{thb_balance['total']:,.2f}"

                            # Also update portfolio value
                            total_portfolio_thb = thb_balance.get('total', 0)

                            # Add other crypto values (simplified - could enhance with price conversion)
                            other_coins = 0
                            for currency, data in balances.items():
                                if currency != 'THB' and data.get('total', 0) > 0:
                                    other_coins += 1

                            if other_coins > 0:
                                balance_text += f" (+{other_coins} coins)"

                    except Exception as e:
                        print(f"Balance update error: {e}")
                        balance_text = "฿---.--"

                self.balance_label.configure(text=balance_text)

            # Update P&L label
            if hasattr(self, 'pnl_label'):
                pnl_color = "green" if self.daily_pnl >= 0 else "red"
                self.pnl_label.configure(text=f"฿{self.daily_pnl:.2f}", text_color=pnl_color)

            # Update trades label
            if hasattr(self, 'trades_label'):
                max_trades = self.config.get('max_daily_trades', 3)
                self.trades_label.configure(text=f"{self.daily_trades}/{max_trades}")

            # Update status
            if hasattr(self, 'status_label'):
                if self.emergency_stop:
                    status_text = "🔴 Emergency Stop"
                    status_color = "red"
                elif self.is_trading:
                    status_text = "🟢 Trading Active"
                    status_color = "green"
                elif self.api_client:
                    # Check if we have private API access
                    try:
                        balance_check = self.api_client.get_balances_safe()
                        if balance_check and balance_check.get('error') == 0:
                            status_text = "🟢 Connected (Full API)"
                            status_color = "green"
                        else:
                            status_text = "🟡 Connected (Public API)"
                            status_color = "orange"
                    except:
                        status_text = "🟡 Connected (Limited)"
                        status_color = "orange"
                else:
                    status_text = "⚪ Disconnected"
                    status_color = "gray"

                self.status_label.configure(text=status_text, text_color=status_color)

            # Force UI update
            if hasattr(self, 'root'):
                self.root.update_idletasks()

        except Exception as e:
            print(f"Status update error: {e}")

    # ========================================================================
    # 🔌 API Connection Methods
    # ========================================================================

    def connect_api(self):
        """Connect to Bitkub API"""
        try:
            api_key = self.api_key_entry.get().strip()
            secret_key = self.secret_key_entry.get().strip()

            if not api_key or not secret_key:
                messagebox.showwarning("Warning", "Please enter both API Key and Secret Key")
                return

            self.log_message("🔌 Connecting to Bitkub API...")

            # Update visual state
            if self.scifi_visual:
                self.scifi_visual.set_state("connecting")

            def connect_thread():
                try:
                    self.log_message("🔍 Creating API client...")

                    # Create API client
                    self.api_client = ImprovedBitkubAPI(api_key, secret_key)

                    self.log_message("🌐 Testing internet connection...")

                    # Test basic connectivity first
                    try:
                        test_response = requests.get("https://www.google.com", timeout=5)
                        self.log_message("✅ Internet connection OK")
                    except:
                        raise Exception("No internet connection - please check your network")

                    # Test Bitkub server connectivity
                    self.log_message("🔍 Testing Bitkub server connectivity...")
                    try:
                        test_bitkub = requests.get("https://api.bitkub.com/api/servertime", timeout=10)
                        if test_bitkub.status_code == 200:
                            self.log_message("✅ Bitkub server reachable")
                        else:
                            raise Exception(f"Bitkub server returned status {test_bitkub.status_code}")
                    except requests.exceptions.Timeout:
                        raise Exception("Bitkub server timeout - please try again later")
                    except requests.exceptions.ConnectionError:
                        raise Exception("Cannot reach Bitkub server - please check your connection")

                    # Test server time API
                    self.log_message("🕒 Testing server time API...")
                    server_time = self.api_client.get_server_time()

                    if not server_time:
                        raise Exception("No response from server time API")

                    if not isinstance(server_time, dict):
                        raise Exception(f"Invalid server time response type: {type(server_time)}")

                    # Check if server time request was successful
                    if server_time.get('error') == 0 and 'result' in server_time:
                        server_timestamp = server_time['result']
                        server_datetime = datetime.fromtimestamp(server_timestamp / 1000)

                        self.log_message("✅ Server time API working!")
                        self.log_message(f"🕒 Server Time: {server_datetime}")

                        # Test private API only if we have credentials
                        if api_key and secret_key:
                            self.log_message("🔐 Testing private API using Scci5.py method...")
                            balance_result = self.api_client.get_balances_safe()

                            if balance_result and isinstance(balance_result, dict):
                                if balance_result.get('error') == 0:
                                    # Private API works - show balance like Scci5.py
                                    self.log_message("✅ Private API authentication successful!")

                                    balances = balance_result.get('result', {})
                                    total_value_thb = 0
                                    non_zero_balances = 0

                                    for currency, data in balances.items():
                                        if data['total'] > 0:
                                            non_zero_balances += 1
                                            if currency == 'THB':
                                                total_value_thb += data['total']
                                                self.log_message(
                                                    f"💰 {currency}: {data['total']:,.2f} (Available: {data['available']:,.2f})")
                                            else:
                                                self.log_message(
                                                    f"🪙 {currency}: {data['total']:,.8f} (Available: {data['available']:,.8f})")

                                    if non_zero_balances > 0:
                                        self.log_message(f"📊 Found {non_zero_balances} currencies with balance")
                                        if total_value_thb > 0:
                                            self.log_message(f"💎 THB Balance: ฿{total_value_thb:,.2f}")
                                    else:
                                        self.log_message("ℹ️ All balances are zero (normal for new accounts)")

                                    # Initialize trading components
                                    self.strategy = EnhancedTradingStrategy(self.api_client)
                                    self.coin_recommender = CoinRecommendationSystem(self.api_client)

                                    self.log_message("✅ All trading systems initialized!")

                                    # Update visual state
                                    if self.scifi_visual:
                                        self.root.after(0, lambda: self.scifi_visual.set_state("success"))

                                else:
                                    error_code = balance_result.get('error', 999)
                                    error_msg = balance_result.get('message', 'Unknown error')

                                    # Still initialize systems for public API usage
                                    self.strategy = EnhancedTradingStrategy(self.api_client)
                                    self.coin_recommender = CoinRecommendationSystem(self.api_client)

                                    if error_code == 3:
                                        self.log_message("⚠️ Private API: Invalid API credentials")
                                        self.log_message("💡 Please check your API Key and Secret in Bitkub settings")
                                    elif error_code == 5:
                                        self.log_message("⚠️ Private API: IP address not allowed")
                                        self.log_message("💡 Please add your IP to Bitkub API settings")
                                    elif error_code == 994:
                                        self.log_message("⚠️ Private API: Server temporarily busy")
                                        self.log_message("💡 This may resolve itself - try again in a few minutes")
                                    else:
                                        self.log_message(f"⚠️ Private API limited: {error_msg}")

                                    self.log_message("✅ Connected with public API only (market data)")

                                    if self.scifi_visual:
                                        self.root.after(0, lambda: self.scifi_visual.set_state("success"))
                            else:
                                raise Exception("Invalid private API response format")
                        else:
                            raise Exception("API credentials are empty")

                        # Update status in UI thread
                        self.root.after(0, self.update_status_displays)

                        # Also update dashboard immediately after connection
                        self.root.after(1000, self.update_dashboard_with_balance)

                    else:
                        # Handle server time error
                        error_code = server_time.get('error', 999)
                        error_msg = server_time.get('message', f"Server time error {error_code}")
                        raise Exception(f"Server time API failed: {error_msg}")

                except Exception as e:
                    error_msg = str(e)
                    self.log_message(f"❌ Connection failed: {error_msg}")

                    # Show error in UI thread
                    self.root.after(0, lambda: messagebox.showerror(
                        "Connection Error",
                        f"Failed to connect to Bitkub API:\n\n{error_msg}\n\nPlease check:\n" +
                        "• Your internet connection\n" +
                        "• API credentials are correct\n" +
                        "• Your IP is allowed in Bitkub settings"
                    ))

                    if self.scifi_visual:
                        self.root.after(0, lambda: self.scifi_visual.set_state("error"))

            threading.Thread(target=connect_thread, daemon=True).start()

        except Exception as e:
            error_msg = f"Connection setup error: {str(e)}"
            self.log_message(f"❌ {error_msg}")
            messagebox.showerror("Error", error_msg)

    def quick_connect_api(self):
        """Quick connect using saved credentials"""
        if self.api_key_entry.get() and self.secret_key_entry.get():
            self.connect_api()
        else:
            self.log_message("⚠️ Please configure API credentials first")
            self.notebook.set("🔧 Configuration")

    # ========================================================================
    # 💰 Trading Control Methods
    # ========================================================================

    def toggle_paper_trading(self):
        """Toggle paper trading mode"""
        if self.paper_trading_var.get():
            self.real_trading_var.set(False)
            self.is_paper_trading = True
            self.log_message("📝 Switched to Paper Trading mode (SAFE)")
        else:
            self.paper_trading_var.set(True)  # Force paper trading on

    def toggle_real_trading(self):
        """Toggle real trading mode with warning"""
        if self.real_trading_var.get():
            result = messagebox.askyesno(
                "⚠️ EXTREME DANGER WARNING",
                "🔥 YOU ARE ABOUT TO ENABLE REAL TRADING MODE!\n\n" +
                "This will use your ACTUAL MONEY for trades.\n" +
                "You could lose significant amounts of money.\n\n" +
                "Are you absolutely sure you want to continue?\n\n" +
                "⚠️ ONLY PROCEED IF YOU UNDERSTAND THE RISKS!"
            )

            if result:
                # Double confirmation
                confirm = messagebox.askyesno(
                    "🚨 FINAL CONFIRMATION",
                    "This is your FINAL WARNING!\n\n" +
                    "Real trading mode will be activated.\n" +
                    "You may lose real money.\n\n" +
                    "Type 'YES' in the next dialog to confirm."
                )

                if confirm:
                    user_input = simpledialog.askstring(
                        "Final Confirmation",
                        "Type 'YES' to activate real trading:"
                    )

                    if user_input and user_input.upper() == "YES":
                        self.paper_trading_var.set(False)
                        self.is_paper_trading = False
                        self.log_message("🔥 REAL TRADING MODE ACTIVATED! USE EXTREME CAUTION!")

                        if self.scifi_visual:
                            self.scifi_visual.flash_effect("#ff0000", 1.0)
                    else:
                        self.real_trading_var.set(False)
                        self.log_message("❌ Real trading activation cancelled")
                else:
                    self.real_trading_var.set(False)
            else:
                self.real_trading_var.set(False)
        else:
            self.is_paper_trading = True
            self.paper_trading_var.set(True)

    def start_manual_trading(self):
        """Start manual trading"""
        if not self.api_client:
            messagebox.showwarning("Warning", "Please connect to API first")
            return

        self.is_trading = True
        self.emergency_stop = False

        mode = "PAPER" if self.is_paper_trading else "REAL"
        self.log_message(f"▶️ Manual Trading Started ({mode} mode)", "trading")

        if self.scifi_visual:
            self.scifi_visual.set_state("analyzing")

        self.update_status_displays()

    def pause_trading(self):
        """Pause trading"""
        self.is_trading = False
        self.log_message("⏸️ Trading Paused", "trading")

        if self.scifi_visual:
            self.scifi_visual.set_state("idle")

        self.update_status_displays()

    def stop_trading(self):
        """Stop all trading"""
        self.is_trading = False
        self.emergency_stop = False

        self.log_message("⏹️ Trading Stopped", "trading")

        if self.scifi_visual:
            self.scifi_visual.set_state("idle")

        self.update_status_displays()

    def emergency_stop_trading(self):
        """Emergency stop all trading activities"""
        result = messagebox.askyesno(
            "🚨 EMERGENCY STOP",
            "This will immediately stop all trading activities.\n\n" +
            "Are you sure you want to proceed?"
        )

        if result:
            self.emergency_stop = True
            self.is_trading = False

            # Stop auto trading if active
            if hasattr(self, 'full_auto_engine') and self.full_auto_engine:
                self.full_auto_engine.stop_auto_trading()

            self.log_message("🚨 EMERGENCY STOP ACTIVATED!")

            if self.scifi_visual:
                self.scifi_visual.set_state("error")
                self.scifi_visual.flash_effect("#ff0000", 2.0)

            self.update_status_displays()

    def reset_daily_stats(self):
        """Reset daily statistics"""
        self.daily_trades = 0
        self.daily_pnl = 0.0
        self.total_fees_paid = 0.0
        self.last_trade_time = None

        self.log_message("🔄 Daily statistics reset")
        self.update_status_displays()

    # ========================================================================
    # 🪙 Coin Analysis Methods
    # ========================================================================

    def toggle_coin_recommendation(self):
        """Toggle coin recommendation system"""
        status = "enabled" if self.coin_rec_var.get() else "disabled"
        self.config['use_coin_recommendation'] = self.coin_rec_var.get()
        self.log_message(f"🪙 Coin recommendation system {status}")

    def analyze_selected_coin(self):
        """Analyze the selected coin"""
        if not self.coin_recommender:
            self.coin_analysis_results.insert("end", "❌ Please connect to API first\n\n")
            return

        symbol = self.analysis_coin_combo.get().lower()

        self.coin_analysis_results.insert("end", f"🔍 Analyzing {symbol.upper()}...\n")

        if self.scifi_visual:
            self.scifi_visual.set_state("coin_analysis")

        def analyze_thread():
            try:
                result = self.coin_recommender.analyze_coin(symbol)

                analysis_text = f"""
📊 Analysis Results for {symbol.upper()}:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 Overall Score: {result['score']}/10
📝 Reason: {result['reason']}

"""
                if 'metrics' in result:
                    metrics = result['metrics']
                    analysis_text += f"""📈 Key Metrics:
• Price Change (24h): {metrics.get('price_change_24h', 'N/A')}%
• Volume (24h): ฿{metrics.get('volume_24h', 0):,.2f}
• Last Price: ฿{metrics.get('last_price', 0):,.2f}

"""

                # Add recommendation
                if result['score'] >= 7:
                    analysis_text += "✅ Recommendation: STRONG BUY\n"
                elif result['score'] >= 5:
                    analysis_text += "🟡 Recommendation: MODERATE BUY\n"
                else:
                    analysis_text += "❌ Recommendation: AVOID\n"

                analysis_text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

                self.coin_analysis_results.insert("end", analysis_text)
                self.coin_analysis_results.see("end")

                if self.scifi_visual:
                    if result['score'] >= 7:
                        self.scifi_visual.set_state("buy_signal")
                    elif result['score'] <= 3:
                        self.scifi_visual.set_state("sell_signal")
                    else:
                        self.scifi_visual.set_state("analyzing")

            except Exception as e:
                error_text = f"❌ Analysis error: {str(e)}\n\n"
                self.coin_analysis_results.insert("end", error_text)

                if self.scifi_visual:
                    self.scifi_visual.set_state("error")

        threading.Thread(target=analyze_thread, daemon=True).start()

    def get_coin_recommendation(self):
        """Get best coin recommendation"""
        if not self.coin_recommender:
            self.coin_analysis_results.insert("end", "❌ Please connect to API first\n\n")
            return

        self.coin_analysis_results.insert("end", "🤖 Getting AI recommendation...\n")

        if self.scifi_visual:
            self.scifi_visual.set_state("analyzing")

        def recommend_thread():
            try:
                result = self.coin_recommender.get_best_recommendation()

                if result['success']:
                    rec_text = f"""
🤖 AI Coin Recommendation:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏆 Best Coin: {result['symbol'].upper()}
🎯 Score: {result['score']}/10
📝 Reason: {result['reason']}

📊 Top 5 Recommendations:
"""

                    for i, rec in enumerate(result['all_recommendations'][:5], 1):
                        rec_text += f"{i}. {rec['symbol'].upper()} - Score: {rec['score']}/10\n"
                        rec_text += f"   Reason: {rec['reason']}\n\n"

                    rec_text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

                    if self.scifi_visual:
                        self.scifi_visual.set_state("success")

                else:
                    rec_text = f"""
❌ Recommendation Failed:
{result['message']}

Using fallback: {result['fallback_symbol'].upper()}

"""
                    if self.scifi_visual:
                        self.scifi_visual.set_state("error")

                self.coin_analysis_results.insert("end", rec_text)
                self.coin_analysis_results.see("end")

            except Exception as e:
                error_text = f"❌ Recommendation error: {str(e)}\n\n"
                self.coin_analysis_results.insert("end", error_text)

                if self.scifi_visual:
                    self.scifi_visual.set_state("error")

        threading.Thread(target=recommend_thread, daemon=True).start()

    # ========================================================================
    # 🤖 Full Auto Trading Methods
    # ========================================================================

    def toggle_auto_trading(self):
        """Toggle auto trading system"""
        if self.auto_trading_var.get():
            if not self.api_client:
                messagebox.showwarning("Warning", "Please connect to API first")
                self.auto_trading_var.set(False)
                return

            self.config['auto_trading'] = True
            self.log_message("🤖 Auto trading system enabled", "auto")
        else:
            self.config['auto_trading'] = False
            self.log_message("🤖 Auto trading system disabled", "auto")

    def start_full_auto_trading(self):
        """Start full auto trading system"""
        if not self.api_client:
            messagebox.showwarning("Warning", "Please connect to API first")
            return

        try:
            initial_balance = float(self.auto_balance_var.get())
            target_hours = float(self.auto_hours_var.get())
            target_profit = float(self.auto_profit_var.get())

            if initial_balance <= 0 or target_hours <= 0:
                messagebox.showerror("Error", "Please enter valid configuration values")
                return

            # Create full auto engine
            self.full_auto_engine = FullAutoTradingEngine(self.api_client, initial_balance)

            # Start auto trading
            success = self.full_auto_engine.start_auto_trading(target_hours)

            if success:
                self.auto_trading_var.set(True)
                self.log_message(f"🚀 Full Auto Trading Started!", "auto")
                self.log_message(f"💰 Initial Balance: ฿{initial_balance:,.2f}", "auto")
                self.log_message(f"⏰ Target Hours: {target_hours}", "auto")
                self.log_message(f"🎯 Target Profit: {target_profit}%", "auto")

                if self.scifi_visual:
                    self.scifi_visual.set_state("trading")

                # Start monitoring thread
                self.start_auto_monitoring()

            else:
                messagebox.showerror("Error", "Failed to start auto trading")

        except ValueError:
            messagebox.showerror("Error", "Please enter valid numeric values")
        except Exception as e:
            messagebox.showerror("Error", f"Auto trading start error: {str(e)}")

    def stop_full_auto_trading(self):
        """Stop full auto trading"""
        if self.full_auto_engine and self.full_auto_engine.is_auto_trading:
            self.full_auto_engine.stop_auto_trading()
            self.auto_trading_var.set(False)

            self.log_message("🛑 Full Auto Trading Stopped", "auto")

            if self.scifi_visual:
                self.scifi_visual.set_state("idle")

            # Show final summary
            self.show_auto_trading_summary()

    def start_auto_monitoring(self):
        """Start auto trading monitoring thread"""

        def monitoring_thread():
            while (self.full_auto_engine and
                   self.full_auto_engine.is_auto_trading and
                   not self.emergency_stop):
                try:
                    # Make trading decision
                    decision = self.full_auto_engine.make_trading_decision({})

                    # Log decision
                    coin_symbol = decision.get('symbol', 'UNKNOWN').upper()
                    action = decision.get('action', 'UNKNOWN')
                    confidence = decision.get('confidence', 0)

                    decision_text = f"""
🧠 AI Decision: {action}
🪙 Analyzing: {coin_symbol}
🎯 Confidence: {confidence:.1f}/10
"""
                    if decision.get('amount'):
                        decision_text += f"💰 Amount: ฿{decision['amount']:.2f}\n"

                    self.log_message(decision_text.strip(), "auto")

                    # Update visual based on decision
                    if self.scifi_visual:
                        if decision['action'] == 'BUY':
                            self.scifi_visual.set_state("buy_signal")
                        elif decision['action'] == 'SELL':
                            self.scifi_visual.set_state("sell_signal")
                        elif decision['action'] == 'ERROR':
                            self.scifi_visual.set_state("error")
                        else:
                            self.scifi_visual.set_state("analyzing")

                    time.sleep(30)  # Wait 30 seconds between decisions

                except Exception as e:
                    self.log_message(f"❌ Auto monitoring error: {str(e)}", "auto")
                    time.sleep(60)  # Wait longer on error

        threading.Thread(target=monitoring_thread, daemon=True).start()

    def show_full_auto_performance(self):
        """Show full auto trading performance"""
        if not self.full_auto_engine:
            messagebox.showinfo("Info", "No auto trading session active")
            return

        try:
            summary = self.full_auto_engine.get_session_summary()
            analysis = self.performance_analyzer.analyze_session_performance(summary['session_id'])

            # Create performance report
            report = f"""
🤖 Full Auto Trading Performance Report
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Session Information:
• Session ID: {summary['session_id']}
• Status: {summary['status']}
• Elapsed Time: {summary['elapsed_hours']:.2f} hours

💰 Financial Summary:
• Initial Balance: ฿{summary['initial_balance']:,.2f}
• Current Balance: ฿{summary['current_balance']:,.2f}
• Total P&L: ฿{summary['total_pnl']:,.2f}
• ROI: {summary['roi_percentage']:.2f}%

📈 Trading Statistics:
• Total Trades: {summary['total_trades']}
• Winning Trades: {summary['winning_trades']}
• Win Rate: {summary['win_rate']:.1f}%
• Active Positions: {summary['active_positions']}
• Max Drawdown: {summary['max_drawdown']:.2f}%
• Decisions Made: {summary['decisions_made']}

🧠 AI Analysis:
"""

            if 'error' not in analysis:
                report += f"• Total Decisions: {analysis['total_decisions']}\n"

                if analysis['confidence_stats']:
                    conf = analysis['confidence_stats']
                    report += f"• Average Confidence: {conf['average']:.1f}/10\n"
                    report += f"• Max Confidence: {conf['max']:.1f}/10\n"
                    report += f"• Min Confidence: {conf['min']:.1f}/10\n"

                report += "\n🎯 Recommendations:\n"
                for rec in analysis['recommendations']:
                    report += f"• {rec['message']}\n"
                    report += f"  Suggestion: {rec['suggestion']}\n\n"
            else:
                report += f"• Analysis Error: {analysis['error']}\n"

            report += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

            # Show in popup window
            self.show_performance_window(report)

        except Exception as e:
            messagebox.showerror("Error", f"Performance analysis failed: {str(e)}")

    def show_performance_window(self, report):
        """Show performance report in popup window"""
        perf_window = ctk.CTkToplevel(self.root)
        perf_window.title("📊 Auto Trading Performance Report")
        perf_window.geometry("900x700")
        perf_window.grab_set()

        # Title
        ctk.CTkLabel(
            perf_window,
            text="📊 Full Auto Trading Performance Report",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=20)

        # Report display
        report_display = ctk.CTkTextbox(perf_window, height=500, width=850)
        report_display.pack(fill="both", expand=True, padx=20, pady=10)
        report_display.insert("1.0", report)

        # Close button
        ctk.CTkButton(
            perf_window,
            text="✅ Close Report",
            command=perf_window.destroy,
            height=40,
            width=150
        ).pack(pady=20)

    def reset_full_auto_session(self):
        """Reset full auto trading session"""
        result = messagebox.askyesno(
            "Reset Session",
            "This will reset the current auto trading session.\nAll progress will be lost.\n\nContinue?"
        )

        if result:
            if self.full_auto_engine:
                self.full_auto_engine.stop_auto_trading()

            self.full_auto_engine = None
            self.auto_trading_var.set(False)

            if hasattr(self, 'full_auto_status_display'):
                self.full_auto_status_display.delete("1.0", "end")

            self.log_message("🔄 Auto trading session reset", "auto")

            if self.scifi_visual:
                self.scifi_visual.set_state("idle")

    def show_auto_trading_summary(self):
        """Show auto trading session summary"""
        if not self.full_auto_engine:
            return

        summary = self.full_auto_engine.get_session_summary()

        summary_text = f"""
🏁 Auto Trading Session Completed!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⏰ Duration: {summary['elapsed_hours']:.2f} hours
💰 Final P&L: ฿{summary['total_pnl']:,.2f}
📊 ROI: {summary['roi_percentage']:.2f}%
🔄 Total Trades: {summary['total_trades']}
✅ Win Rate: {summary['win_rate']:.1f}%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
        self.log_message(summary_text, "auto")

    # ========================================================================
    # 🧪 Testing Methods
    # ========================================================================

    def test_connection(self):
        """Test API connection"""
        if not self.api_client:
            self.test_results_display.insert("end", "❌ No API client connected\n\n")
            return

        self.test_results_display.insert("end", "🔌 Testing API connection...\n")

        def test_thread():
            try:
                # Test server time first
                result = self.api_client.get_server_time()

                if result and isinstance(result, dict) and result.get('error') == 0:
                    server_time = datetime.fromtimestamp(result['result'] / 1000)
                    self.test_results_display.insert("end", f"✅ Public API connection successful!\n")
                    self.test_results_display.insert("end", f"🕒 Server time: {server_time}\n")

                    # Test private API
                    balance_result = self.api_client.get_balances_safe()

                    if balance_result and isinstance(balance_result, dict):
                        if balance_result.get('error') == 0:
                            self.test_results_display.insert("end", f"✅ Private API connection successful!\n")
                            balances = balance_result.get('result', {})

                            # Show some balance info
                            thb_balance = balances.get('THB', {})
                            if thb_balance and thb_balance.get('total', 0) > 0:
                                self.test_results_display.insert("end",
                                                                 f"💰 THB Balance: {thb_balance['total']:.2f} THB\n"
                                                                 )
                        else:
                            error_code = balance_result.get('error', 999)
                            error_msg = balance_result.get('message', f"Error {error_code}")
                            self.test_results_display.insert("end", f"⚠️ Private API limited: {error_msg}\n")
                    else:
                        self.test_results_display.insert("end", f"⚠️ Private API test inconclusive\n")

                else:
                    error_msg = "Connection failed"
                    if result and isinstance(result, dict):
                        error_msg = result.get('message', 'Unknown error')
                    elif result:
                        error_msg = f"Invalid response type: {type(result)}"

                    self.test_results_display.insert("end", f"❌ Connection failed: {error_msg}\n")

                self.test_results_display.insert("end", "\n")

            except Exception as e:
                self.test_results_display.insert("end", f"❌ Test error: {str(e)}\n\n")

        threading.Thread(target=test_thread, daemon=True).start()

    def test_balance(self):
        """Test balance retrieval with proper display"""
        if not self.api_client:
            self.test_results_display.insert("end", "❌ No API client connected\n\n")
            return

        self.test_results_display.insert("end", "💰 Testing balance retrieval...\n")

        def test_thread():
            try:
                self.test_results_display.insert("end", "🔍 Using working Scci5.py method...\n")
                result = self.api_client.get_balances_safe()

                if result and isinstance(result, dict) and result.get('error') == 0:
                    balances = result.get('result', {})
                    self.test_results_display.insert("end", f"✅ Balance retrieved successfully!\n\n")

                    # Show balances like successful connection log
                    total_value_thb = 0
                    non_zero_balances = 0

                    for currency, data in balances.items():
                        if data['total'] > 0:
                            non_zero_balances += 1
                            if currency == 'THB':
                                total_value_thb += data['total']
                                self.test_results_display.insert("end",
                                                                 f"💰 {currency}: {data['total']:,.2f} (Available: {data['available']:,.2f})\n"
                                                                 )
                            else:
                                self.test_results_display.insert("end",
                                                                 f"🪙 {currency}: {data['total']:,.8f} (Available: {data['available']:,.8f})\n"
                                                                 )

                    if non_zero_balances > 0:
                        self.test_results_display.insert("end",
                                                         f"\n📊 Found {non_zero_balances} currencies with balance\n")
                        if total_value_thb > 0:
                            self.test_results_display.insert("end", f"💎 Total THB: ฿{total_value_thb:,.2f}\n")
                    else:
                        self.test_results_display.insert("end", "ℹ️ All balances are zero (normal for new accounts)\n")

                    self.test_results_display.insert("end", "\n")
                else:
                    error_code = result.get('error', 999)
                    error_msg = result.get('message', 'Unknown error')

                    self.test_results_display.insert("end", f"❌ Balance test failed: {error_msg}\n")

                    # Handle different error types
                    if error_code == 994:
                        self.test_results_display.insert("end", f"🔍 HTTP 994 detected - server busy/maintenance\n")
                        self.test_results_display.insert("end", f"💡 This is a Bitkub server issue, try again later\n")
                    elif error_code == 3:
                        self.test_results_display.insert("end", f"🔑 Check your API credentials\n")
                    elif error_code == 5:
                        self.test_results_display.insert("end", f"🌐 Add your IP to Bitkub API whitelist\n")

                    self.test_results_display.insert("end", "\n")

            except Exception as e:
                self.test_results_display.insert("end", f"❌ Test error: {str(e)}\n\n")

        threading.Thread(target=test_thread, daemon=True).start()

    def test_market_data(self):
        """Test market data retrieval"""
        if not self.api_client:
            self.test_results_display.insert("end", "❌ No API client connected\n\n")
            return

        self.test_results_display.insert("end", "📊 Testing market data...\n")

        def test_thread():
            try:
                # Get all market data first to see available symbols
                result = self.api_client.get_market_data()

                if result and isinstance(result, dict) and result.get('error') == 0:
                    all_data = result.get('result', {})

                    # Find BTC related symbols
                    btc_symbols = [k for k in all_data.keys() if 'BTC' in k.upper() and 'THB' in k.upper()]

                    if btc_symbols:
                        # Use the first BTC symbol found
                        btc_symbol = btc_symbols[0]
                        btc_data = all_data[btc_symbol]

                        self.test_results_display.insert("end", f"✅ Market data retrieved!\n")
                        self.test_results_display.insert("end", f"📊 Found symbol: {btc_symbol}\n")

                        if isinstance(btc_data, dict):
                            # Safe value extraction
                            last_price = btc_data.get('last', 'N/A')
                            if last_price != 'N/A':
                                try:
                                    last_price = float(last_price)
                                    self.test_results_display.insert("end",
                                                                     f"📈 {btc_symbol} Last Price: ฿{last_price:,.2f}\n")
                                except (ValueError, TypeError):
                                    self.test_results_display.insert("end",
                                                                     f"📈 {btc_symbol} Last Price: {last_price}\n")

                            percent_change = btc_data.get('percentChange', 'N/A')
                            if percent_change != 'N/A':
                                self.test_results_display.insert("end", f"📊 24h Change: {percent_change}%\n")

                            high_24h = btc_data.get('high24hr', 'N/A')
                            if high_24h != 'N/A':
                                try:
                                    high_24h = float(high_24h)
                                    self.test_results_display.insert("end", f"📈 24h High: ฿{high_24h:,.2f}\n")
                                except (ValueError, TypeError):
                                    pass

                            low_24h = btc_data.get('low24hr', 'N/A')
                            if low_24h != 'N/A':
                                try:
                                    low_24h = float(low_24h)
                                    self.test_results_display.insert("end", f"📉 24h Low: ฿{low_24h:,.2f}\n")
                                except (ValueError, TypeError):
                                    pass

                            volume = btc_data.get('baseVolume', 'N/A')
                            if volume != 'N/A':
                                try:
                                    volume = float(volume)
                                    self.test_results_display.insert("end", f"💹 24h Volume: ฿{volume:,.2f}\n")
                                except (ValueError, TypeError):
                                    pass

                        self.test_results_display.insert("end",
                                                         f"\n📋 Available THB pairs: {len([k for k in all_data.keys() if 'THB' in k.upper()])}\n")

                        # Show top 5 symbols by volume
                        thb_pairs = [(k, v) for k, v in all_data.items() if 'THB' in k.upper() and isinstance(v, dict)]
                        thb_pairs.sort(key=lambda x: float(x[1].get('baseVolume', 0)), reverse=True)

                        if thb_pairs:
                            self.test_results_display.insert("end", f"\n🏆 Top 5 by Volume:\n")
                            for i, (symbol, data) in enumerate(thb_pairs[:5]):
                                volume = float(data.get('baseVolume', 0))
                                price = data.get('last', 'N/A')
                                self.test_results_display.insert("end", f"  {i + 1}. {symbol}: ฿{volume:,.0f} volume")
                                if price != 'N/A':
                                    try:
                                        price = float(price)
                                        self.test_results_display.insert("end", f" @ ฿{price:,.2f}")
                                    except:
                                        pass
                                self.test_results_display.insert("end", f"\n")

                        self.test_results_display.insert("end", "\n")
                    else:
                        # No BTC found, show what's available
                        thb_symbols = [k for k in all_data.keys() if 'THB' in k.upper()][:10]
                        self.test_results_display.insert("end", f"⚠️ No BTC_THB found\n")
                        self.test_results_display.insert("end", f"📋 Available THB pairs: {', '.join(thb_symbols)}\n\n")

                else:
                    error_msg = "Market data test failed"
                    if result and isinstance(result, dict):
                        error_msg = result.get('message', error_msg)
                    self.test_results_display.insert("end", f"❌ {error_msg}\n\n")

            except Exception as e:
                self.test_results_display.insert("end", f"❌ Test error: {str(e)}\n\n")

        threading.Thread(target=test_thread, daemon=True).start()

    def test_order_book(self):
        """Test order book data"""
        if not self.api_client:
            self.test_results_display.insert("end", "❌ No API client connected\n\n")
            return

        self.test_results_display.insert("end", "📖 Testing order book data...\n")

        def test_thread():
            try:
                result = self.api_client.get_market_depth('btc_thb', 5)

                if result and result.get('error') == 0:
                    depth = result.get('result', {})
                    bids = depth.get('bids', [])
                    asks = depth.get('asks', [])

                    self.test_results_display.insert("end", f"✅ Order book retrieved!\n\n")

                    self.test_results_display.insert("end", f"📊 Top 5 Bids (Buy Orders):\n")
                    for i, bid in enumerate(bids[:5]):
                        price, volume = bid
                        self.test_results_display.insert("end",
                                                         f"  {i + 1}. Price: ฿{float(price):,.2f}, Volume: {float(volume):.8f}\n")

                    self.test_results_display.insert("end", f"\n📊 Top 5 Asks (Sell Orders):\n")
                    for i, ask in enumerate(asks[:5]):
                        price, volume = ask
                        self.test_results_display.insert("end",
                                                         f"  {i + 1}. Price: ฿{float(price):,.2f}, Volume: {float(volume):.8f}\n")

                    # Calculate spread
                    if bids and asks:
                        best_bid = float(bids[0][0])
                        best_ask = float(asks[0][0])
                        spread = ((best_ask - best_bid) / best_bid) * 100
                        self.test_results_display.insert("end", f"\n💰 Spread: {spread:.4f}%\n\n")

                else:
                    self.test_results_display.insert("end", f"❌ Order book test failed\n\n")

            except Exception as e:
                self.test_results_display.insert("end", f"❌ Test error: {str(e)}\n\n")

        threading.Thread(target=test_thread, daemon=True).start()

    def test_open_orders(self):
        """Test open orders retrieval"""
        if not self.api_client:
            self.test_results_display.insert("end", "❌ No API client connected\n\n")
            return

        self.test_results_display.insert("end", "📋 Testing open orders...\n")

        def test_thread():
            try:
                result = self.api_client.get_my_open_orders_safe('btc_thb')

                if result and result.get('error') == 0:
                    orders = result.get('result', [])

                    if orders:
                        self.test_results_display.insert("end", f"✅ Found {len(orders)} open orders:\n\n")

                        for order in orders:
                            side = order.get('side', 'unknown').upper()
                            order_id = order.get('id', 'N/A')
                            rate = float(order.get('rate', 0))
                            amount = float(order.get('amount', 0))

                            self.test_results_display.insert("end",
                                                             f"🔸 {side} Order ID: {order_id}\n" +
                                                             f"   Price: ฿{rate:,.2f}, Amount: {amount:.8f} BTC\n\n"
                                                             )
                    else:
                        self.test_results_display.insert("end", f"✅ No open orders found\n\n")

                else:
                    error_msg = result.get('message', 'Unknown error')
                    self.test_results_display.insert("end", f"❌ Open orders test failed: {error_msg}\n\n")

            except Exception as e:
                self.test_results_display.insert("end", f"❌ Test error: {str(e)}\n\n")

        threading.Thread(target=test_thread, daemon=True).start()

    def test_scifi_cycle(self):
        """Test sci-fi visual state cycling"""
        if not self.scifi_visual:
            self.test_results_display.insert("end", "❌ Sci-fi visual system not initialized\n\n")
            return

        states = ["connecting", "analyzing", "coin_analysis", "buy_signal", "sell_signal", "trading", "success",
                  "error", "idle"]

        self.test_results_display.insert("end", "🎬 Testing sci-fi visual states...\n")

        def cycle_states():
            for i, state in enumerate(states):
                self.test_results_display.insert("end", f"🎯 Testing state: {state}\n")
                self.scifi_visual.set_state(state)
                time.sleep(2)

            self.test_results_display.insert("end", "✅ Visual state test completed!\n\n")

        threading.Thread(target=cycle_states, daemon=True).start()

    def test_visual_state(self, state):
        """Test specific visual state"""
        if self.scifi_visual:
            self.scifi_visual.set_state(state)
            self.log_message(f"🎬 Visual state changed to: {state}")

    # ========================================================================
    # 📜 History and Analytics Methods
    # ========================================================================

    def apply_history_filter(self):
        """Apply filters to trade history"""
        self.log_message("🔍 Applying history filters...")
        self.refresh_trade_history()

    def refresh_trade_history(self):
        """Refresh trade history display"""
        try:
            # Clear existing items
            for item in self.history_tree.get_children():
                self.history_tree.delete(item)

            # Load trades from database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Build query based on filters
            query = "SELECT * FROM trades ORDER BY timestamp DESC LIMIT 100"
            params = []

            # Add date filters if specified
            date_from = self.date_from_entry.get().strip()
            date_to = self.date_to_entry.get().strip()
            symbol_filter = self.history_symbol_combo.get()

            conditions = []

            if date_from:
                conditions.append("DATE(timestamp) >= ?")
                params.append(date_from)

            if date_to:
                conditions.append("DATE(timestamp) <= ?")
                params.append(date_to)

            if symbol_filter and symbol_filter != "All":
                conditions.append("symbol = ?")
                params.append(symbol_filter.lower())

            if conditions:
                query = f"SELECT * FROM trades WHERE {' AND '.join(conditions)} ORDER BY timestamp DESC LIMIT 100"

            cursor.execute(query, params)
            trades = cursor.fetchall()

            # Get column names
            columns = [description[0] for description in cursor.description]

            # Populate treeview
            for trade in trades:
                trade_dict = dict(zip(columns, trade))

                # Format display values
                timestamp = datetime.fromisoformat(trade_dict['timestamp']).strftime("%m/%d %H:%M")
                symbol = trade_dict['symbol'].upper()
                side = trade_dict['side'].upper()
                amount = f"{trade_dict['amount']:.6f}"
                price = f"฿{trade_dict['price']:,.2f}"
                total = f"฿{trade_dict['total_thb']:,.2f}"
                pnl = f"฿{trade_dict['net_pnl']:.2f}" if trade_dict['net_pnl'] else "N/A"
                status = trade_dict['status'] or "Unknown"

                # Color coding for P&L
                if trade_dict['net_pnl']:
                    pnl_value = trade_dict['net_pnl']
                    if pnl_value > 0:
                        pnl = f"+฿{pnl_value:.2f}"
                    else:
                        pnl = f"-฿{abs(pnl_value):.2f}"

                self.history_tree.insert("", "end", values=(
                    timestamp, symbol, side, amount, price, total, pnl, status
                ))

            conn.close()

            self.log_message(f"📊 Loaded {len(trades)} trade records")

        except Exception as e:
            self.log_message(f"❌ History refresh error: {str(e)}")
            messagebox.showerror("Error", f"Failed to refresh history: {str(e)}")

    # ========================================================================
    # ⚙️ Configuration Methods
    # ========================================================================

    def save_configuration(self):
        """Save bot configuration"""
        try:
            # Update config from UI
            self.config['symbol'] = self.symbol_combo.get().lower()
            self.config['trade_amount_thb'] = float(self.trade_amount_entry.get())
            self.config['max_daily_trades'] = int(self.max_trades_entry.get())
            self.config['max_daily_loss'] = float(self.max_loss_entry.get())

            # Save to file
            config_file = "sci6_config.json"
            with open(config_file, 'w') as f:
                json.dump(self.config, f, indent=2)

            self.log_message("💾 Configuration saved successfully!")
            messagebox.showinfo("Success", "Configuration saved!")

        except ValueError:
            messagebox.showerror("Error", "Please enter valid numeric values")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {str(e)}")

    def load_configuration(self):
        """Load bot configuration"""
        try:
            config_file = "sci6_config.json"
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    saved_config = json.load(f)
                    self.config.update(saved_config)

                # Update UI elements
                if hasattr(self, 'symbol_combo'):
                    self.symbol_combo.set(self.config['symbol'].upper())
                if hasattr(self, 'trade_amount_entry'):
                    self.trade_amount_entry.delete(0, "end")
                    self.trade_amount_entry.insert(0, str(self.config['trade_amount_thb']))
                if hasattr(self, 'max_trades_entry'):
                    self.max_trades_entry.delete(0, "end")
                    self.max_trades_entry.insert(0, str(self.config['max_daily_trades']))
                if hasattr(self, 'max_loss_entry'):
                    self.max_loss_entry.delete(0, "end")
                    self.max_loss_entry.insert(0, str(self.config['max_daily_loss']))

                self.log_message("📁 Configuration loaded successfully!")

        except Exception as e:
            self.log_message(f"⚠️ Failed to load configuration: {str(e)}")

    # ========================================================================
    # 🚀 Quick Action Methods
    # ========================================================================

    def quick_start_trading(self):
        """Quick start trading"""
        if not self.api_client:
            messagebox.showwarning("Warning", "Please connect to API first")
            self.notebook.set("🔧 Configuration")
            return

        self.start_manual_trading()
        self.notebook.set("📈 Trading Control")

    def quick_stop_trading(self):
        """Quick stop trading"""
        self.stop_trading()

    def quick_refresh_data(self):
        """Quick refresh all data"""
        self.log_message("🔄 Refreshing all data...")

        # Refresh history
        if hasattr(self, 'history_tree'):
            self.refresh_trade_history()

        # Update status displays
        self.update_status_displays()

        # Clear and update test results
        if hasattr(self, 'test_results_display'):
            self.test_results_display.delete("1.0", "end")
            self.test_results_display.insert("end", "🔄 Data refreshed successfully!\n\n")

        self.log_message("✅ Data refresh completed!")

    def update_dashboard_with_balance(self):
        """Update dashboard with real balance data"""
        try:
            if not self.api_client:
                return

            # Get fresh balance data
            balance_result = self.api_client.get_balances_safe()
            if balance_result and balance_result.get('error') == 0:
                balances = balance_result.get('result', {})

                # Update balance display
                thb_balance = balances.get('THB', {})
                if thb_balance and thb_balance.get('total', 0) > 0:
                    balance_amount = thb_balance['total']
                    if hasattr(self, 'balance_label'):
                        self.balance_label.configure(text=f"฿{balance_amount:,.2f}")

                    # Log the update
                    self.log_message(f"💰 Dashboard updated: Balance ฿{balance_amount:,.2f}")

                # Count other assets
                other_assets = 0
                for currency, data in balances.items():
                    if currency != 'THB' and data.get('total', 0) > 0:
                        other_assets += 1

                if other_assets > 0:
                    self.log_message(f"🪙 Portfolio: {other_assets + 1} currencies")

                # Update connection status to show full API access
                if hasattr(self, 'status_label'):
                    self.status_label.configure(
                        text="🟢 Connected (Full API)",
                        text_color="green"
                    )

        except Exception as e:
            print(f"Dashboard balance update error: {e}")

    def refresh_balance_display(self):
        """Manually refresh balance display"""
        if self.api_client:
            self.update_dashboard_with_balance()
            self.log_message("🔄 Balance display refreshed")

    def start_periodic_updates(self):
        """Start periodic status updates"""

        def update_loop():
            while True:
                try:
                    if hasattr(self, 'root') and self.root.winfo_exists():
                        # Update status every 30 seconds
                        self.update_status_displays()

                        # Update balance every 2 minutes if connected
                        if self.api_client and hasattr(self, '_last_balance_update'):
                            if time.time() - self._last_balance_update > 120:  # 2 minutes
                                self.update_dashboard_with_balance()
                                self._last_balance_update = time.time()
                        elif self.api_client:
                            # First time setup
                            self._last_balance_update = time.time()
                            self.update_dashboard_with_balance()

                        time.sleep(30)  # Update every 30 seconds
                    else:
                        break
                except Exception as e:
                    print(f"Periodic update error: {e}")
                    time.sleep(60)  # Wait longer on error

        threading.Thread(target=update_loop, daemon=True).start()

    # ========================================================================
    # 🎯 Main Application Methods
    # ========================================================================

    def run(self):
        """Run the complete trading bot application"""
        try:
            # Load saved configuration
            self.load_configuration()

            # Start periodic updates
            self.start_periodic_updates()

            # Log startup
            self.log_message("🚀 Sci6 Enhanced Trading Bot Started!")
            self.log_message("📊 All systems initialized successfully")
            self.log_message("⚡ Ready for trading operations!")

            # Initialize visual system
            if self.scifi_visual:
                self.scifi_visual.set_state("idle")

            # Start main loop
            self.root.mainloop()

        except Exception as e:
            print(f"Application error: {str(e)}")
            messagebox.showerror("Application Error", f"Failed to start application: {str(e)}")
        finally:
            # Cleanup
            try:
                if self.scifi_visual:
                    self.scifi_visual.cleanup()

                if self.full_auto_engine and self.full_auto_engine.is_auto_trading:
                    self.full_auto_engine.stop_auto_trading()

            except:
                pass


# ============================================================================
# 🚀 Application Entry Point
# ============================================================================

def main():
    """Main application entry point"""
    try:
        # Check if license system exists (commented out for demo)
        # from license_simple import check_license
        #
        # print("=== 🔐 License Verification ===")
        # user_name = input("Username: ")
        # license_key = input("License Key: ")
        #
        # if not check_license(license_key, user_name):
        #     print("🚫 License verification failed!")
        #     return
        #
        # print(f"🎉 Welcome {user_name}!")

        # Create and run the trading bot
        app = EnhancedTradingBot()
        app.run()

    except KeyboardInterrupt:
        print("\n⚡ Application interrupted by user")
    except Exception as e:
        print(f"❌ Application startup error: {str(e)}")


if __name__ == "__main__":
    main()
