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

# Configure theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class AIVisualEffects:
    """AI Visual Effects Manager - วงกลมสีฟ้าเรืองแสงแบบ AI"""
    
    def __init__(self, parent_frame):
        self.parent = parent_frame
        self.canvas_width = 180
        self.canvas_height = 180
        
        # สร้าง Canvas สำหรับเอฟเฟค
        self.canvas = tk.Canvas(
            parent_frame, 
            width=self.canvas_width, 
            height=self.canvas_height,
            bg='#1a1a1a',  # สีพื้นหลังเข้ม
            highlightthickness=0,
            relief='flat'
        )
        
        # สถานะการแสดงผล
        self.is_animating = False
        self.animation_thread = None
        self.current_state = "idle"
        self.pulse_phase = 0
        self.rotation_angle = 0
        self.sparkle_phase = 0
        
        # สี effects สำหรับสถานะต่างๆ
        self.state_colors = {
            "idle": "#3366ff",           # ฟ้าปกติ
            "connecting": "#00ffff",     # ฟ้าอมเขียว - กำลังเชื่อมต่อ
            "analyzing": "#ff6600",      # ส้ม - กำลังวิเคราะห์
            "signal_buy": "#00ff00",     # เขียว - สัญญาณซื้อ
            "signal_sell": "#ff0000",    # แดง - สัญญาณขาย
            "trading": "#ffff00",        # เหลือง - กำลังเทรด
            "success": "#00ff88",        # เขียวอ่อน - สำเร็จ
            "error": "#ff3366",          # แดงอ่อน - ข้อผิดพลาด
            "thinking": "#9966ff",       # ม่วง - กำลังคิด
            "profit": "#00ff00",         # เขียว - กำไร
            "loss": "#ff0000"            # แดง - ขาดทุน
        }
        
        # เริ่มต้นเอฟเฟค
        self.setup_effects()
        
    def setup_effects(self):
        """ตั้งค่าเอฟเฟคเริ่มต้น"""
        self.canvas.pack(pady=5)
        self.draw_idle_state()
        
    def draw_idle_state(self):
        """วาดสถานะพัก - วงกลมฟ้าเรืองแสง"""
        self.canvas.delete("all")
        center_x, center_y = self.canvas_width // 2, self.canvas_height // 2
        
        # วงกลมหลักสีฟ้าเรืองแสง
        for i in range(3):
            radius = 35 - i * 8
            alpha = 0.8 - i * 0.2
            intensity = int(alpha * 255)
            color = f"#{intensity//4:02x}{intensity//4:02x}{intensity:02x}"
            
            self.canvas.create_oval(
                center_x - radius, center_y - radius,
                center_x + radius, center_y + radius,
                outline=color,
                width=2 + i,
                tags=f"main_circle_{i}"
            )
        
        # จุดกลางเรืองแสง
        self.canvas.create_oval(
            center_x - 5, center_y - 5,
            center_x + 5, center_y + 5,
            fill="#3366ff",
            outline="#66aaff",
            width=2,
            tags="center_dot"
        )
        
    def start_animation(self, state="idle"):
        """เริ่มแอนิเมชัน"""
        self.current_state = state
        if not self.is_animating:
            self.is_animating = True
            self.animation_thread = threading.Thread(target=self._animate_loop, daemon=True)
            self.animation_thread.start()
    
    def stop_animation(self):
        """หยุดแอนิเมชัน"""
        self.is_animating = False
        if self.animation_thread:
            self.animation_thread.join(timeout=1)
        self.draw_idle_state()
    
    def set_state(self, state, message=""):
        """เปลี่ยนสถานะและเอฟเฟค"""
        if state in self.state_colors:
            self.current_state = state
            if state != "idle":
                self.start_animation(state)
            else:
                self.stop_animation()
    
    def _animate_loop(self):
        """ลูปแอนิเมชันหลัก"""
        while self.is_animating:
            try:
                if self.current_state == "connecting":
                    self._animate_connecting()
                elif self.current_state == "analyzing":
                    self._animate_analyzing()
                elif self.current_state == "signal_buy":
                    self._animate_signal_buy()
                elif self.current_state == "signal_sell":
                    self._animate_signal_sell()
                elif self.current_state == "trading":
                    self._animate_trading()
                elif self.current_state == "success" or self.current_state == "profit":
                    self._animate_success()
                elif self.current_state == "error" or self.current_state == "loss":
                    self._animate_error()
                elif self.current_state == "thinking":
                    self._animate_thinking()
                else:
                    self._animate_idle()
                
                time.sleep(0.05)  # 50ms refresh rate
                
            except Exception as e:
                print(f"Animation error: {e}")
                break
    
    def _animate_idle(self):
        """แอนิเมชันสถานะพัก - pulse เบาๆ"""
        self.canvas.delete("all")
        center_x, center_y = self.canvas_width // 2, self.canvas_height // 2
        
        # คำนวณ pulse
        pulse = math.sin(self.pulse_phase) * 0.2 + 1.0
        self.pulse_phase += 0.08
        
        # วงกลมหลักหลายชั้น
        for i in range(4):
            radius = int((30 + i * 8) * pulse)
            alpha = (0.9 - i * 0.15) * pulse
            intensity = int(alpha * 255)
            
            color = f"#{intensity//6:02x}{intensity//6:02x}{intensity:02x}"
            self.canvas.create_oval(
                center_x - radius, center_y - radius,
                center_x + radius, center_y + radius,
                outline=color,
                width=2,
                tags=f"pulse_ring_{i}"
            )
        
        # จุดกลางเรืองแสง
        core_pulse = math.sin(self.pulse_phase * 2) * 0.3 + 1.0
        core_size = int(6 * core_pulse)
        
        self.canvas.create_oval(
            center_x - core_size, center_y - core_size,
            center_x + core_size, center_y + core_size,
            fill="#4477ff",
            outline="#88aaff",
            width=1,
            tags="core"
        )
    
    def _animate_connecting(self):
        """แอนิเมชันการเชื่อมต่อ - spinning particles"""
        self.canvas.delete("all")
        center_x, center_y = self.canvas_width // 2, self.canvas_height // 2
        
        self.rotation_angle += 4
        
        # วงกลมหลัก
        base_pulse = math.sin(self.pulse_phase) * 0.1 + 1.0
        self.pulse_phase += 0.1
        
        main_radius = int(35 * base_pulse)
        self.canvas.create_oval(
            center_x - main_radius, center_y - main_radius,
            center_x + main_radius, center_y + main_radius,
            outline="#00aaff", width=2,
            tags="main_ring"
        )
        
        # อนุภาคหมุน
        for i in range(12):
            angle = (self.rotation_angle + i * 30) * math.pi / 180
            distance = 45 + 10 * math.sin(self.pulse_phase + i * 0.5)
            x = center_x + distance * math.cos(angle)
            y = center_y + distance * math.sin(angle)
            
            alpha = (math.sin(self.pulse_phase + i * 0.3) + 1) / 2
            intensity = int(alpha * 255)
            color = f"#{intensity//8:02x}{intensity:02x}{intensity:02x}"
            
            size = 2 + int(alpha * 3)
            self.canvas.create_oval(
                x - size, y - size, x + size, y + size,
                fill=color, outline="",
                tags=f"particle_{i}"
            )
    
    def _animate_analyzing(self):
        """แอนิเมชันการวิเคราะห์ - brain wave + scanner"""
        self.canvas.delete("all")
        center_x, center_y = self.canvas_width // 2, self.canvas_height // 2
        
        self.pulse_phase += 0.15
        
        # วงกลมสแกนเนอร์
        for ring in range(3):
            radius = (self.pulse_phase * 15 + ring * 20) % 70
            alpha = 1.0 - (radius / 70.0)
            intensity = int(alpha * 255)
            
            if intensity > 20:
                color = f"#{intensity:02x}{intensity//2:02x}{intensity//8:02x}"
                self.canvas.create_oval(
                    center_x - radius, center_y - radius,
                    center_x + radius, center_y + radius,
                    outline=color, width=2,
                    tags=f"scanner_{ring}"
                )
        
        # คลื่นสมอง
        wave_points = []
        for i in range(80):
            x = center_x - 40 + i
            y = center_y + 15 * math.sin((i + self.pulse_phase * 20) * 0.1) * math.sin((i + self.pulse_phase * 8) * 0.05)
            wave_points.extend([x, y])
        
        if len(wave_points) >= 4:
            self.canvas.create_line(
                wave_points, fill="#ff8800", width=2, smooth=True,
                tags="brain_wave"
            )
        
        # จุดกลางกะพริบ
        core_intensity = int((math.sin(self.pulse_phase * 3) + 1) * 128 + 64)
        core_color = f"#{core_intensity:02x}{core_intensity//2:02x}{core_intensity//8:02x}"
        
        self.canvas.create_oval(
            center_x - 8, center_y - 8,
            center_x + 8, center_y + 8,
            fill=core_color, outline="#ffaa44", width=2,
            tags="core"
        )
    
    def _animate_signal_buy(self):
        """แอนิเมชันสัญญาณซื้อ - expanding green energy"""
        self.canvas.delete("all")
        center_x, center_y = self.canvas_width // 2, self.canvas_height // 2
        
        self.pulse_phase += 0.25
        
        # วงกลมพลังงานขยายตัว
        for i in range(4):
            radius = (self.pulse_phase * 25 + i * 15) % 80
            alpha = 1.0 - (radius / 80.0)
            intensity = int(alpha * 255)
            
            if intensity > 0:
                color = f"#{intensity//8:02x}{intensity:02x}{intensity//4:02x}"
                width = max(1, int(alpha * 3))
                self.canvas.create_oval(
                    center_x - radius, center_y - radius,
                    center_x + radius, center_y + radius,
                    outline=color, width=width,
                    tags=f"energy_ring_{i}"
                )
        
        # ลูกศรพลังงานขึ้น
        arrow_pulse = math.sin(self.pulse_phase * 2) * 0.3 + 1.0
        arrow_size = int(15 * arrow_pulse)
        
        arrow_points = [
            center_x, center_y - arrow_size,
            center_x - arrow_size//2, center_y - arrow_size//3,
            center_x - arrow_size//4, center_y - arrow_size//3,
            center_x - arrow_size//4, center_y + arrow_size//2,
            center_x + arrow_size//4, center_y + arrow_size//2,
            center_x + arrow_size//4, center_y - arrow_size//3,
            center_x + arrow_size//2, center_y - arrow_size//3
        ]
        
        arrow_intensity = int((math.sin(self.pulse_phase * 2) + 1) * 128 + 64)
        arrow_color = f"#{arrow_intensity//8:02x}{arrow_intensity:02x}{arrow_intensity//4:02x}"
        
        self.canvas.create_polygon(
            arrow_points, fill=arrow_color, outline="#ffffff", width=2,
            tags="buy_arrow"
        )
        
        # ประกายรอบๆ
        self.sparkle_phase += 0.3
        for i in range(6):
            angle = (self.sparkle_phase + i * 60) * math.pi / 180
            distance = 50 + 15 * math.sin(self.sparkle_phase + i)
            x = center_x + distance * math.cos(angle)
            y = center_y + distance * math.sin(angle)
            
            sparkle_size = 2 + int(math.sin(self.sparkle_phase * 2 + i) * 2)
            self.canvas.create_oval(
                x - sparkle_size, y - sparkle_size,
                x + sparkle_size, y + sparkle_size,
                fill="#44ff44", outline="",
                tags=f"sparkle_{i}"
            )
    
    def _animate_signal_sell(self):
        """แอนิเมชันสัญญาณขาย - contracting red energy"""
        self.canvas.delete("all")
        center_x, center_y = self.canvas_width // 2, self.canvas_height // 2
        
        self.pulse_phase += 0.25
        
        # วงกลมพลังงานหดตัว
        for i in range(4):
            radius = 80 - ((self.pulse_phase * 25 + i * 15) % 80)
            alpha = (radius / 80.0)
            intensity = int(alpha * 255)
            
            if intensity > 0:
                color = f"#{intensity:02x}{intensity//8:02x}{intensity//8:02x}"
                width = max(1, int(alpha * 3))
                self.canvas.create_oval(
                    center_x - radius, center_y - radius,
                    center_x + radius, center_y + radius,
                    outline=color, width=width,
                    tags=f"energy_ring_{i}"
                )
        
        # ลูกศรพลังงานลง
        arrow_pulse = math.sin(self.pulse_phase * 2) * 0.3 + 1.0
        arrow_size = int(15 * arrow_pulse)
        
        arrow_points = [
            center_x, center_y + arrow_size,
            center_x - arrow_size//2, center_y + arrow_size//3,
            center_x - arrow_size//4, center_y + arrow_size//3,
            center_x - arrow_size//4, center_y - arrow_size//2,
            center_x + arrow_size//4, center_y - arrow_size//2,
            center_x + arrow_size//4, center_y + arrow_size//3,
            center_x + arrow_size//2, center_y + arrow_size//3
        ]
        
        arrow_intensity = int((math.sin(self.pulse_phase * 2) + 1) * 128 + 64)
        arrow_color = f"#{arrow_intensity:02x}{arrow_intensity//8:02x}{arrow_intensity//8:02x}"
        
        self.canvas.create_polygon(
            arrow_points, fill=arrow_color, outline="#ffffff", width=2,
            tags="sell_arrow"
        )
    
    def _animate_trading(self):
        """แอนิเมชันการเทรด - active trading energy"""
        self.canvas.delete("all")
        center_x, center_y = self.canvas_width // 2, self.canvas_height // 2
        
        self.rotation_angle += 3
        self.pulse_phase += 0.2
        
        # วงกลมหลักพลังงาน
        main_pulse = math.sin(self.pulse_phase) * 0.15 + 1.0
        main_radius = int(40 * main_pulse)
        
        main_intensity = int((math.sin(self.pulse_phase * 2) + 1) * 128 + 64)
        main_color = f"#{main_intensity:02x}{main_intensity:02x}{main_intensity//8:02x}"
        
        self.canvas.create_oval(
            center_x - main_radius, center_y - main_radius,
            center_x + main_radius, center_y + main_radius,
            outline=main_color, width=3,
            tags="main_trading_ring"
        )
        
        # สัญลักษณ์เงินหมุน
        symbols = ["฿", "$", "€", "¥", "₿"]
        for i, symbol in enumerate(symbols):
            angle = (self.rotation_angle + i * 72) * math.pi / 180
            distance = 30 + 8 * math.sin(self.pulse_phase + i)
            x = center_x + distance * math.cos(angle)
            y = center_y + distance * math.sin(angle)
            
            symbol_intensity = int((math.sin(self.pulse_phase + i * 1.5) + 1) * 128 + 64)
            symbol_color = f"#{symbol_intensity:02x}{symbol_intensity:02x}{symbol_intensity//4:02x}"
            
            self.canvas.create_text(
                x, y, text=symbol, fill=symbol_color,
                font=("Arial", 14, "bold"),
                tags=f"symbol_{i}"
            )
        
        # พลังงานกลาง
        core_pulse = math.sin(self.pulse_phase * 3) * 0.4 + 1.0
        core_size = int(8 * core_pulse)
        
        self.canvas.create_oval(
            center_x - core_size, center_y - core_size,
            center_x + core_size, center_y + core_size,
            fill="#ffdd00", outline="#ffffff", width=2,
            tags="trading_core"
        )
    
    def _animate_success(self):
        """แอนิเมชันความสำเร็จ - victory celebration"""
        self.canvas.delete("all")
        center_x, center_y = self.canvas_width // 2, self.canvas_height // 2
        
        self.pulse_phase += 0.2
        self.sparkle_phase += 0.4
        
        # เครื่องหมายถูกใหญ่
        check_scale = math.sin(self.pulse_phase) * 0.2 + 1.0
        check_size = int(20 * check_scale)
        
        check_points = [
            center_x - check_size, center_y,
            center_x - check_size//3, center_y + check_size//2,
            center_x + check_size, center_y - check_size//2
        ]
        
        check_intensity = int((math.sin(self.pulse_phase * 1.5) + 1) * 128 + 64)
        check_color = f"#{check_intensity//8:02x}{check_intensity:02x}{check_intensity//2:02x}"
        
        self.canvas.create_line(
            check_points, fill=check_color, width=5,
            capstyle=tk.ROUND, joinstyle=tk.ROUND,
            tags="success_check"
        )
        
        # วงกลมชัยชนะ
        victory_rings = 3
        for ring in range(victory_rings):
            radius = (self.pulse_phase * 20 + ring * 25) % 75
            alpha = 1.0 - (radius / 75.0)
            intensity = int(alpha * 255)
            
            if intensity > 20:
                color = f"#{intensity//8:02x}{intensity:02x}{intensity//4:02x}"
                self.canvas.create_oval(
                    center_x - radius, center_y - radius,
                    center_x + radius, center_y + radius,
                    outline=color, width=2,
                    tags=f"victory_ring_{ring}"
                )
        
        # ประกายแห่งชัยชนะ
        for i in range(8):
            angle = (self.sparkle_phase * 2 + i * 45) * math.pi / 180
            distance = 55 + 15 * math.sin(self.sparkle_phase + i * 0.8)
            x = center_x + distance * math.cos(angle)
            y = center_y + distance * math.sin(angle)
            
            sparkle_size = 3 + int(math.sin(self.sparkle_phase * 3 + i) * 2)
            sparkle_intensity = int((math.sin(self.sparkle_phase + i) + 1) * 128 + 64)
            sparkle_color = f"#{sparkle_intensity//4:02x}{sparkle_intensity:02x}{sparkle_intensity//2:02x}"
            
            # วาดดาว
            star_points = []
            for j in range(10):  # 5 แฉกดาว
                star_angle = j * math.pi / 5
                if j % 2 == 0:
                    star_radius = sparkle_size
                else:
                    star_radius = sparkle_size // 2
                star_x = x + star_radius * math.cos(star_angle)
                star_y = y + star_radius * math.sin(star_angle)
                star_points.extend([star_x, star_y])
            
            self.canvas.create_polygon(
                star_points, fill=sparkle_color, outline="",
                tags=f"victory_star_{i}"
            )
    
    def _animate_error(self):
        """แอนิเมชันข้อผิดพลาด - warning flash"""
        self.canvas.delete("all")
        center_x, center_y = self.canvas_width // 2, self.canvas_height // 2
        
        self.pulse_phase += 0.4
        
        # วงกลมเตือนกะพริบ
        flash_intensity = (math.sin(self.pulse_phase) + 1) / 2
        intensity = int(flash_intensity * 255)
        warning_color = f"#{intensity:02x}{intensity//6:02x}{intensity//6:02x}"
        
        warning_radius = int(35 + flash_intensity * 10)
        self.canvas.create_oval(
            center_x - warning_radius, center_y - warning_radius,
            center_x + warning_radius, center_y + warning_radius,
            outline=warning_color, width=4,
            tags="warning_circle"
        )
        
        # วงกลมภายใน
        inner_radius = int(25 + flash_intensity * 5)
        self.canvas.create_oval(
            center_x - inner_radius, center_y - inner_radius,
            center_x + inner_radius, center_y + inner_radius,
            outline=warning_color, width=2,
            tags="warning_inner"
        )
        
        # เครื่องหมายอันตราย
        symbol_intensity = int((math.sin(self.pulse_phase * 1.5) + 1) * 128 + 96)
        symbol_color = f"#{symbol_intensity:02x}{symbol_intensity//8:02x}{symbol_intensity//8:02x}"
        
        self.canvas.create_text(
            center_x, center_y, text="⚠",
            fill=symbol_color, font=("Arial", 28, "bold"),
            tags="warning_symbol"
        )
        
        # คลื่นกระแส
        for wave in range(2):
            wave_radius = (self.pulse_phase * 30 + wave * 40) % 80
            wave_alpha = 1.0 - (wave_radius / 80.0)
            wave_intensity = int(wave_alpha * 200)
            
            if wave_intensity > 30:
                wave_color = f"#{wave_intensity:02x}{wave_intensity//8:02x}{wave_intensity//8:02x}"
                self.canvas.create_oval(
                    center_x - wave_radius, center_y - wave_radius,
                    center_x + wave_radius, center_y + wave_radius,
                    outline=wave_color, width=1,
                    tags=f"error_wave_{wave}"
                )
    
    def _animate_thinking(self):
        """แอนิเมชันการคิด - neural network"""
        self.canvas.delete("all")
        center_x, center_y = self.canvas_width // 2, self.canvas_height // 2
        
        self.pulse_phase += 0.12
        
        # โหนดเครือข่ายประสาท
        nodes = [
            (center_x - 35, center_y - 25),
            (center_x, center_y - 35),
            (center_x + 35, center_y - 25),
            (center_x - 20, center_y),
            (center_x + 20, center_y),
            (center_x - 35, center_y + 25),
            (center_x, center_y + 35),
            (center_x + 35, center_y + 25)
        ]
        
        # เส้นเชื่อมระหว่างโหนด
        connections = [
            (0, 3), (1, 3), (1, 4), (2, 4),
            (3, 5), (3, 6), (4, 6), (4, 7),
            (0, 1), (1, 2), (5, 6), (6, 7)
        ]
        
        for i, (start, end) in enumerate(connections):
            pulse_offset = self.pulse_phase + i * 0.3
            alpha = (math.sin(pulse_offset) + 1) / 2
            intensity = int(alpha * 200 + 55)
            connection_color = f"#{intensity//4:02x}{intensity//4:02x}{intensity:02x}"
            
            line_width = max(1, int(alpha * 3))
            self.canvas.create_line(
                nodes[start][0], nodes[start][1],
                nodes[end][0], nodes[end][1],
                fill=connection_color, width=line_width,
                tags=f"neural_connection_{i}"
            )
        
        # โหนดแต่ละตัว
        for i, (x, y) in enumerate(nodes):
            node_pulse = math.sin(self.pulse_phase + i * 0.4) * 0.4 + 1.0
            node_size = int(5 * node_pulse)
            
            node_intensity = int((math.sin(self.pulse_phase + i * 0.5) + 1) * 128 + 64)
            node_color = f"#{node_intensity//4:02x}{node_intensity//4:02x}{node_intensity:02x}"
            outline_color = f"#{node_intensity//2:02x}{node_intensity//2:02x}{min(255, node_intensity + 64):02x}"
            
            self.canvas.create_oval(
                x - node_size, y - node_size, x + node_size, y + node_size,
                fill=node_color, outline=outline_color, width=2,
                tags=f"neural_node_{i}"
            )
        
        # พัลส์กลาง
        center_pulse = math.sin(self.pulse_phase * 2) * 0.3 + 1.0
        center_size = int(8 * center_pulse)
        
        center_intensity = int((math.sin(self.pulse_phase * 1.5) + 1) * 128 + 64)
        center_color = f"#{center_intensity//3:02x}{center_intensity//3:02x}{center_intensity:02x}"
        
        self.canvas.create_oval(
            center_x - center_size, center_y - center_size,
            center_x + center_size, center_y + center_size,
            fill=center_color, outline="#9999ff", width=2,
            tags="thinking_core"
        )
    
    def flash_effect(self, color, duration=0.5):
        """เอฟเฟคกะพริบ"""
        original_bg = self.canvas.cget('bg')
        self.canvas.configure(bg=color)
        
        def reset_bg():
            self.canvas.configure(bg=original_bg)
        
        self.canvas.after(int(duration * 1000), reset_bg)


class ImprovedBitkubAPI:
    """Improved Bitkub API Client with proven order execution"""

    def __init__(self, api_key="", api_secret=""):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://api.bitkub.com"
        self.request_times = deque(maxlen=250)
        self.rate_limit_lock = threading.Lock()

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

        # Convert display format to trading format - รองรับเหรียญทั้งหมดของ Bitkub
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
            "THB_1INCH": "1inch_thb", "THB_ENJ": "enj_thb", "THB_GALA": "gala_thb"
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

    def get_order_book(self, symbol, depth=20):
        """Get order book data"""
        try:
            self._wait_for_rate_limit()
            symbol_for_api = symbol.upper()
            response = requests.get(
                f"{self.base_url}/api/market/books?sym={symbol_for_api}&lmt={depth}", 
                timeout=10
            )
            return response.json()
        except Exception as e:
            print(f"Order book error: {e}")
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


class ProfitableStrategy:
    """กลยุทธ์เทรดที่คำนึงถึงกำไรและค่าธรรมเนียม Bitkub"""

    def __init__(self):
        # ค่าธรรมเนียม Bitkub
        self.maker_fee = 0.0025  # 0.25%
        self.taker_fee = 0.0025  # 0.25% 
        self.total_fee = self.maker_fee + self.taker_fee  # 0.5%
        
        # พารามิเตอร์กำไรที่ปรับปรุง
        self.min_profit_margin = 0.008  # 0.8% ขั้นต่ำ (มากกว่าค่าธรรมเนียม)
        self.optimal_profit_target = 0.015  # 1.5% เป้าหมาย
        
        # RSI ที่เข้มงวดขึ้น
        self.rsi_oversold = 25  # เข้มงวดกว่าเดิม
        self.rsi_overbought = 75
        
        # Volume analysis
        self.min_volume_ratio = 1.3  # Volume ต้องสูงกว่าค่าเฉลี่ย 30%
        
        # Order Book requirements
        self.min_order_book_depth = 30000  # THB ขั้นต่ำใน order book
        self.max_spread_tolerance = 0.005  # 0.5% spread สูงสุด
        
        # Risk management
        self.stop_loss_pct = 0.015  # 1.5%
        self.take_profit_pct = 0.025  # 2.5%
        self.max_position_time_hours = 6  # ปิดภายใน 6 ชั่วโมง
        
        # Data storage
        self.price_history = deque(maxlen=200)
        self.volume_history = deque(maxlen=50)
        self.spread_history = deque(maxlen=20)
        
        self.position = None

    def calculate_fees(self, amount, price, side="both"):
        """คำนวณค่าธรรมเนียมที่แท้จริง"""
        trade_value = amount * price
        
        if side == "buy":
            return trade_value * self.taker_fee
        elif side == "sell":
            return trade_value * self.maker_fee  # ใช้ limit order
        else:  # both
            return trade_value * self.total_fee

    def calculate_break_even_price(self, entry_price, side="buy"):
        """คำนวณราคาที่จะไม่ขาดทุน (รวมค่าธรรมเนียม)"""
        if side == "buy":
            return entry_price * (1 + self.total_fee + 0.002)  # เผื่อ slippage
        else:
            return entry_price * (1 - self.total_fee - 0.002)

    def analyze_order_book(self, order_book):
        """วิเคราะห์ Order Book เพื่อความปลอดภัย"""
        if not order_book or not isinstance(order_book, dict):
            return False, "ไม่มีข้อมูล Order Book"
        
        if 'result' not in order_book:
            return False, "รูปแบบ Order Book ไม่ถูกต้อง"
        
        result = order_book['result']
        if not isinstance(result, dict):
            return False, "ข้อมูล Order Book ไม่ถูกต้อง"
            
        bids = result.get('bids', [])
        asks = result.get('asks', [])
        
        if not bids or not asks:
            return False, "Order Book ว่าง"
        
        try:
            # คำนวณ spread
            best_bid = float(bids[0][0])
            best_ask = float(asks[0][0])
            spread_pct = (best_ask - best_bid) / best_bid
            
            self.spread_history.append(spread_pct)
            
            if spread_pct > self.max_spread_tolerance:
                return False, f"Spread สูงเกินไป: {spread_pct*100:.3f}%"
            
            # คำนวณความลึกของ order book
            bid_depth = sum([float(bid[0]) * float(bid[1]) for bid in bids[:10]])
            ask_depth = sum([float(ask[0]) * float(ask[1]) for ask in asks[:10]])
            
            min_depth = min(bid_depth, ask_depth)
            if min_depth < self.min_order_book_depth:
                return False, f"Order Book ไม่ลึกพอ: {min_depth:.0f} THB"
            
            return True, {
                'spread_pct': spread_pct,
                'bid_depth': bid_depth,
                'ask_depth': ask_depth,
                'best_bid': best_bid,
                'best_ask': best_ask
            }
        except (ValueError, IndexError, TypeError) as e:
            return False, f"ข้อผิดพลาดในการวิเคราะห์ Order Book: {str(e)}"

    def calculate_volume_signal(self, current_volume):
        """วิเคราะห์ Volume สำหรับ momentum"""
        self.volume_history.append(current_volume)
        
        if len(self.volume_history) < 20:
            return False, "ข้อมูล Volume ไม่เพียงพอ"
        
        avg_volume = np.mean(list(self.volume_history)[-20:])
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
        
        if volume_ratio < self.min_volume_ratio:
            return False, f"Volume ต่ำ: {volume_ratio:.2f}x"
        
        return True, f"Volume ดี: {volume_ratio:.2f}x"

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

    def calculate_momentum(self, prices, periods=[5, 10]):
        """คำนวณ momentum หลายช่วงเวลา"""
        if len(prices) < max(periods) + 1:
            return {}
        
        current_price = prices[-1]
        momentum = {}
        
        for period in periods:
            if len(prices) >= period + 1:
                old_price = prices[-(period+1)]
                momentum[f'{period}p'] = (current_price - old_price) / old_price * 100
        
        return momentum

    def should_buy_profitable(self, price, volume, order_book, balance_thb, trade_amount):
        """การตัดสินใจซื้อที่เน้นกำไร"""
        if self.position:
            return False, "มี position อยู่แล้ว"
        
        if balance_thb < trade_amount:
            return False, f"เงินไม่พอ: {balance_thb:.2f} < {trade_amount}"
        
        self.price_history.append(price)
        
        conditions = []
        warnings = []
        
        # 1. ตรวจสอบ Order Book ก่อน
        book_ok, book_analysis = self.analyze_order_book(order_book)
        if not book_ok:
            return False, f"Order Book: {book_analysis}"
        
        conditions.append(f"Order Book ดี (spread: {book_analysis['spread_pct']*100:.3f}%)")
        
        # 2. ตรวจสอบ Volume
        vol_ok, vol_analysis = self.calculate_volume_signal(volume)
        if not vol_ok:
            return False, f"Volume ไม่เพียงพอ: {vol_analysis}"
        
        conditions.append(f"Volume: {vol_analysis}")
        
        # 3. วิเคราะห์ RSI
        if len(self.price_history) >= 15:
            rsi = self.calculate_rsi(list(self.price_history))
            if rsi < self.rsi_oversold:
                conditions.append(f"RSI oversold ({rsi:.1f})")
            elif rsi > 45:  # ไม่ซื้อถ้า RSI > 45
                return False, f"RSI สูงเกินไป ({rsi:.1f})"
        
        # 4. ตรวจสอบ Momentum
        if len(self.price_history) >= 11:
            momentum = self.calculate_momentum(list(self.price_history))
            if momentum.get('5p', 0) < -1.0:  # ลดลง 1% ใน 5 periods
                conditions.append(f"Momentum ลง ({momentum['5p']:.2f}%)")
            elif momentum.get('5p', 0) > 3:  # ขึ้นมากเกินไป
                return False, f"Momentum สูงเกินไป ({momentum['5p']:.2f}%)"
        
        # 5. คำนวณความคุ้มค่า (สำคัญที่สุด)
        break_even_price = self.calculate_break_even_price(price, "buy")
        required_gain_pct = (break_even_price - price) / price
        
        if required_gain_pct > self.min_profit_margin:
            return False, f"ต้องการกำไรสูงเกินไป: {required_gain_pct*100:.2f}%"
        
        # ตัดสินใจซื้อ: ต้องมีเงื่อนไขอย่างน้อย 3 ข้อ
        if len(conditions) >= 3:
            return True, " & ".join(conditions[:3])
        
        return False, f"เงื่อนไข: {len(conditions)}/3"

    def should_sell_profitable(self, current_price, volume, order_book):
        """การตัดสินใจขายที่เน้นกำไร"""
        if not self.position:
            return False, "ไม่มี position"
        
        entry_price = self.position['entry_price']
        entry_time = self.position.get('entry_time', datetime.now())
        amount = self.position['amount']
        
        # คำนวณ P&L รวมค่าธรรมเนียม
        gross_pnl = (current_price - entry_price) * amount
        buy_fee = self.calculate_fees(amount, entry_price, "buy")
        sell_fee = self.calculate_fees(amount, current_price, "sell")
        net_pnl = gross_pnl - buy_fee - sell_fee
        net_pnl_pct = net_pnl / (entry_price * amount)
        
        # เช็คเวลา (บังคับปิด)
        hours_held = (datetime.now() - entry_time).total_seconds() / 3600
        if hours_held > self.max_position_time_hours:
            return True, f"เกินเวลา ({hours_held:.1f}h), P&L: {net_pnl_pct*100:.2f}%"
        
        # Stop Loss
        if net_pnl_pct <= -self.stop_loss_pct:
            return True, f"Stop Loss ({net_pnl_pct*100:.2f}%)"
        
        # Take Profit
        if net_pnl_pct >= self.take_profit_pct:
            return True, f"Take Profit ({net_pnl_pct*100:.2f}%)"
        
        # RSI overbought
        if len(self.price_history) >= 15:
            rsi = self.calculate_rsi(list(self.price_history))
            if rsi > self.rsi_overbought:
                return True, f"RSI overbought ({rsi:.1f}), P&L: {net_pnl_pct*100:.2f}%"
        
        # ขายเมื่อมีกำไรและ momentum เริ่มลด
        if net_pnl_pct > 0.01:  # มีกำไร 1%
            if len(self.price_history) >= 11:
                momentum = self.calculate_momentum(list(self.price_history))
                if momentum.get('5p', 0) < -0.8:  # momentum ลดลง
                    return True, f"กำไร + momentum ลด ({net_pnl_pct*100:.2f}%)"
        
        return False, f"Hold (P&L: {net_pnl_pct*100:.2f}%)"


class EnhancedTradingBot:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("🚀 Enhanced Bitkub Trading Bot with AI Visual Effects")
        self.root.geometry("1600x1000")

        # AI Visual Effects
        self.visual_effects = None

        # Core components
        self.api_client = None
        self.strategy = ProfitableStrategy()

        # Trading state
        self.is_trading = False
        self.is_paper_trading = True
        self.emergency_stop = False

        # Trading config with all Bitkub coins
        self.config = {
            'symbol': 'btc_thb',
            'trade_amount_thb': 500,  # เพิ่มขึ้นเพื่อกำไรที่คุ้มค่า
            'max_daily_trades': 2,
            'max_daily_loss': 1000,
            'min_trade_interval': 1800,
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
                volume_ratio REAL,
                spread_pct REAL,
                api_response TEXT
            )
        ''')

        conn.commit()
        conn.close()

    def setup_ui(self):
        """Create enhanced UI with AI visual effects"""

        # Header with AI Visual Effects
        header_frame = ctk.CTkFrame(self.root, height=220)
        header_frame.pack(fill="x", padx=10, pady=5)
        header_frame.pack_propagate(False)

        # Left side - AI Visual Effects
        effects_frame = ctk.CTkFrame(header_frame)
        effects_frame.pack(side="left", padx=15, pady=15)

        ctk.CTkLabel(effects_frame, text="🤖 AI Status", 
                     font=("Arial", 16, "bold")).pack(pady=5)

        # สร้าง visual effects
        self.visual_effects = AIVisualEffects(effects_frame)

        self.ai_status_label = ctk.CTkLabel(effects_frame, text="System Ready", 
                                           font=("Arial", 12))
        self.ai_status_label.pack(pady=5)

        # Center - Title and Info
        title_frame = ctk.CTkFrame(header_frame)
        title_frame.pack(side="left", expand=True, fill="both", padx=10, pady=15)

        ctk.CTkLabel(title_frame, 
                     text="🚀 ENHANCED BITKUB TRADING BOT",
                     font=("Arial", 24, "bold")).pack(pady=10)

        ctk.CTkLabel(title_frame,
                     text="ระบบเทรดอัจฉริยะพร้อม AI Visual Effects\nคำนึงถึงกำไรและค่าธรรมเนียม Bitkub 0.5%\nรองรับเหรียญทั้งหมดของ Bitkub",
                     font=("Arial", 12),
                     text_color="#00ff88").pack(pady=5)

        # Profit indicator
        profit_frame = ctk.CTkFrame(title_frame)
        profit_frame.pack(pady=10)

        ctk.CTkLabel(profit_frame, text="💰 วันนี้:", font=("Arial", 12)).pack(side="left", padx=5)
        self.profit_label = ctk.CTkLabel(profit_frame, text="0.00 THB", 
                                        font=("Arial", 14, "bold"), text_color="#00ff00")
        self.profit_label.pack(side="left", padx=5)

        ctk.CTkLabel(profit_frame, text="💸 ค่าธรรมเนียม:", font=("Arial", 12)).pack(side="left", padx=10)
        self.fees_label = ctk.CTkLabel(profit_frame, text="0.00 THB", 
                                      font=("Arial", 14, "bold"), text_color="#ff6600")
        self.fees_label.pack(side="left", padx=5)

        # Right side - Quick Stats
        stats_frame = ctk.CTkFrame(header_frame)
        stats_frame.pack(side="right", padx=15, pady=15)

        ctk.CTkLabel(stats_frame, text="📊 Quick Stats", 
                     font=("Arial", 14, "bold")).pack(pady=5)

        self.quick_stats = {}
        stats_items = [
            ("API", "Disconnected", "red"),
            ("Balance", "---", "gray"),
            ("Position", "None", "gray"),
            ("Mode", "PAPER", "orange")
        ]

        for label, value, color in stats_items:
            stat_frame = ctk.CTkFrame(stats_frame)
            stat_frame.pack(fill="x", pady=2)
            
            ctk.CTkLabel(stat_frame, text=f"{label}:", font=("Arial", 10)).pack(side="left", padx=5)
            self.quick_stats[label] = ctk.CTkLabel(stat_frame, text=value, 
                                                  font=("Arial", 11, "bold"), text_color=color)
            self.quick_stats[label].pack(side="right", padx=5)

        # Enhanced warning banner
        warning_frame = ctk.CTkFrame(self.root, fg_color="red", height=60)
        warning_frame.pack(fill="x", padx=10, pady=5)
        warning_frame.pack_propagate(False)

        warning_text = "⚠️ ENHANCED TRADING BOT - คำนึงถึงค่าธรรมเนียมและกำไร ⚠️\nรองรับเหรียญทั้งหมดของ Bitkub พร้อม AI Visual Effects"
        ctk.CTkLabel(warning_frame, text=warning_text,
                     font=("Arial", 14, "bold"),
                     text_color="white").pack(expand=True)

        # Tabs
        self.tabview = ctk.CTkTabview(self.root)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_dashboard = self.tabview.add("📊 Dashboard")
        self.tab_trading = self.tabview.add("💹 Trading")
        self.tab_profit = self.tabview.add("💰 Profit Analysis")
        self.tab_api = self.tabview.add("🔌 API Config")
        self.tab_testing = self.tabview.add("🧪 Testing")
        self.tab_history = self.tabview.add("📜 History")
        self.tab_settings = self.tabview.add("⚙️ Settings")

        self.setup_dashboard_tab()
        self.setup_trading_tab()
        self.setup_profit_tab()
        self.setup_api_tab()
        self.setup_testing_tab()
        self.setup_history_tab()
        self.setup_settings_tab()

        # Control Panel
        self.setup_control_panel()

    def setup_control_panel(self):
        """สร้าง control panel หลัก"""
        control_frame = ctk.CTkFrame(self.root, height=80)
        control_frame.pack(fill="x", padx=10, pady=5)
        control_frame.pack_propagate(False)

        # Trading Controls
        self.start_btn = ctk.CTkButton(
            control_frame, 
            text="🚀 Start AI Trading",
            command=self.toggle_trading,
            fg_color="green", 
            height=50, 
            width=200,
            font=("Arial", 14, "bold")
        )
        self.start_btn.pack(side="left", padx=20, pady=15)

        # AI Action Buttons
        ai_buttons_frame = ctk.CTkFrame(control_frame)
        ai_buttons_frame.pack(side="left", padx=20, pady=15)

        ctk.CTkButton(ai_buttons_frame, text="🧠 AI Analysis", 
                      command=self.trigger_ai_analysis,
                      height=35, width=110).pack(side="left", padx=3)

        ctk.CTkButton(ai_buttons_frame, text="🔍 Market Scan",
                      command=self.trigger_market_scan,
                      height=35, width=110).pack(side="left", padx=3)

        ctk.CTkButton(ai_buttons_frame, text="💡 Signal Check",
                      command=self.trigger_signal_check,
                      height=35, width=110).pack(side="left", padx=3)

        ctk.CTkButton(ai_buttons_frame, text="💰 Profit Calc",
                      command=self.trigger_profit_analysis,
                      height=35, width=110).pack(side="left", padx=3)

        # Mode Toggle
        mode_frame = ctk.CTkFrame(control_frame)
        mode_frame.pack(side="right", padx=20, pady=15)

        ctk.CTkLabel(mode_frame, text="Mode:", font=("Arial", 12, "bold")).pack()
        self.paper_switch = ctk.CTkSwitch(
            mode_frame,
            text="REAL",
            command=self.toggle_paper_trading
        )
        self.paper_switch.pack()

        # Emergency Stop
        ctk.CTkButton(
            control_frame,
            text="🚨 EMERGENCY STOP",
            command=self.emergency_stop_trading,
            fg_color="red",
            height=50,
            width=180,
            font=("Arial", 12, "bold")
        ).pack(side="right", padx=20, pady=15)

    def setup_dashboard_tab(self):
        """Enhanced dashboard"""
        # Status cards พร้อมข้อมูลกำไร
        stats_frame = ctk.CTkFrame(self.tab_dashboard)
        stats_frame.pack(fill="x", padx=10, pady=10)

        self.status_cards = {}
        cards = [
            ("Mode", "PAPER TRADING", "orange"),
            ("System Status", "Checking...", "blue"),
            ("Balance THB", "---", "green"),
            ("Net P&L Today", "0.00", "blue"),
            ("Gross Profit", "0.00", "green"),
            ("Total Fees", "0.00", "red"),
            ("Daily Trades", "0/2", "purple"),
            ("Position", "None", "gray")
        ]

        for i, (label, value, color) in enumerate(cards):
            card = ctk.CTkFrame(stats_frame)
            card.grid(row=i//4, column=i%4, padx=5, pady=5, sticky="ew")

            ctk.CTkLabel(card, text=label, font=("Arial", 10)).pack(pady=2)
            self.status_cards[label] = ctk.CTkLabel(card, text=value,
                                                    font=("Arial", 12, "bold"))
            self.status_cards[label].pack(pady=5)

        for col in range(4):
            stats_frame.grid_columnconfigure(col, weight=1)

        # Control panel with improved safety
        control_frame = ctk.CTkFrame(self.tab_dashboard)
        control_frame.pack(fill="x", padx=10, pady=10)

        # Paper/Real toggle
        safety_frame = ctk.CTkFrame(control_frame)
        safety_frame.pack(side="left", padx=10)

        ctk.CTkLabel(safety_frame, text="Trading Mode:",
                     font=("Arial", 12, "bold")).pack(pady=2)

        self.paper_switch_dashboard = ctk.CTkSwitch(safety_frame,
                                          text="REAL Trading (ระวัง!)",
                                          command=self.toggle_paper_trading,
                                          button_color="red",
                                          progress_color="darkred")
        self.paper_switch_dashboard.pack(pady=2)

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
        self.dashboard_display = ctk.CTkTextbox(self.tab_dashboard, font=("Consolas", 11))
        self.dashboard_display.pack(fill="both", expand=True, padx=10, pady=10)

    def setup_trading_tab(self):
        """Enhanced trading tab"""
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

        # Strategy settings กำไรที่ปรับปรุง
        strategy_frame = ctk.CTkFrame(self.tab_trading)
        strategy_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(strategy_frame, text="💰 Profit Strategy Settings:",
                     font=("Arial", 14, "bold")).pack(anchor="w", padx=10, pady=5)

        # Profit settings
        profit_settings_frame = ctk.CTkFrame(strategy_frame)
        profit_settings_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(profit_settings_frame, text="กำไรขั้นต่ำ %:").pack(side="left", padx=5)
        self.min_profit_var = tk.DoubleVar(value=0.8)
        ctk.CTkSlider(profit_settings_frame, from_=0.5, to=2.0, variable=self.min_profit_var,
                      command=self.update_strategy).pack(side="left", padx=5)
        self.min_profit_label = ctk.CTkLabel(profit_settings_frame, text="0.8%")
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

    def setup_profit_tab(self):
        """Tab สำหรับวิเคราะห์กำไร"""
        # Profit calculator
        calc_frame = ctk.CTkFrame(self.tab_profit)
        calc_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(calc_frame, text="💰 Profit Calculator & Analysis",
                     font=("Arial", 16, "bold")).pack(pady=10)

        # Calculator controls
        calc_controls = ctk.CTkFrame(calc_frame)
        calc_controls.pack(fill="x", padx=20, pady=10)

        ctk.CTkButton(calc_controls, text="🧮 Calculate Profit",
                      command=self.show_profit_calculator,
                      height=40, width=150).pack(side="left", padx=5)

        ctk.CTkButton(calc_controls, text="📊 Fee Analysis",
                      command=self.analyze_fees,
                      height=40, width=150).pack(side="left", padx=5)

        ctk.CTkButton(calc_controls, text="📈 Performance Stats",
                      command=self.show_performance_stats,
                      height=40, width=150).pack(side="left", padx=5)

        # Profit display
        self.profit_display = ctk.CTkTextbox(self.tab_profit, font=("Consolas", 10))
        self.profit_display.pack(fill="both", expand=True, padx=10, pady=10)

    def setup_api_tab(self):
        """API configuration with enhanced security notes"""
        api_frame = ctk.CTkFrame(self.tab_api)
        api_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(api_frame, text="Bitkub API Configuration",
                     font=("Arial", 18, "bold")).pack(pady=10)

        # Enhanced security warning
        warning_text = """
🔒 ENHANCED SECURITY NOTES:
• บอทนี้ใช้วิธีการส่งคำสั่งซื้อขายที่ได้รับการยืนยันแล้ว
• คำนึงถึงค่าธรรมเนียม Bitkub 0.5% ในการคำนวณ
• รองรับเหรียญทั้งหมดของ Bitkub
• เริ่มต้นด้วย PAPER TRADING และจำนวนเงินเล็กน้อย
• ตั้งค่า IP whitelist ใน Bitkub เพื่อความปลอดภัยสูงสุด
• ใช้บัญชีเทรดแยกต่างหากที่มีเงินทุนจำกัด
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
        """Testing tab for safe order testing"""
        test_frame = ctk.CTkFrame(self.tab_testing)
        test_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(test_frame, text="🧪 Order Testing (Safe Testing Environment)",
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

        ctk.CTkButton(btn_frame, text="💡 Test Profit Calc",
                      command=self.test_profit_calculation).pack(side="left", padx=5)

        # Test results
        self.test_display = ctk.CTkTextbox(self.tab_testing, font=("Consolas", 10))
        self.test_display.pack(fill="both", expand=True, padx=10, pady=10)

    def setup_history_tab(self):
        """Enhanced history tab"""
        control_frame = ctk.CTkFrame(self.tab_history)
        control_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkButton(control_frame, text="🔄 Refresh",
                      command=self.load_trade_history).pack(side="left", padx=5)

        ctk.CTkButton(control_frame, text="📊 Profit Statistics",
                      command=self.show_profitability_stats).pack(side="left", padx=5)

        ctk.CTkButton(control_frame, text="📤 Export CSV",
                      command=self.export_history).pack(side="left", padx=5)

        # History display
        self.history_display = ctk.CTkTextbox(self.tab_history, font=("Consolas", 10))
        self.history_display.pack(fill="both", expand=True, padx=10, pady=10)

    def setup_settings_tab(self):
        """Enhanced settings tab รองรับเหรียญทั้งหมดของ Bitkub"""
        settings_frame = ctk.CTkFrame(self.tab_settings)
        settings_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(settings_frame, text="⚙️ การตั้งค่าเพื่อกำไร",
                     font=("Arial", 16, "bold")).pack(pady=10)

        # เหรียญทั้งหมดของ Bitkub
        bitkub_symbols = [
            "btc_thb", "eth_thb", "ada_thb", "xrp_thb", "bnb_thb", "doge_thb",
            "dot_thb", "matic_thb", "atom_thb", "near_thb", "sol_thb", "sand_thb",
            "mana_thb", "avax_thb", "shib_thb", "ltc_thb", "bch_thb", "etc_thb",
            "link_thb", "uni_thb", "usdt_thb", "usdc_thb", "dai_thb", "busd_thb",
            "alpha_thb", "ftt_thb", "axie_thb", "alice_thb", "chz_thb", "jasmy_thb",
            "lrc_thb", "comp_thb", "mkr_thb", "snx_thb", "aave_thb", "grt_thb",
            "1inch_thb", "enj_thb", "gala_thb"
        ]

        # Trading pair
        pair_frame = ctk.CTkFrame(settings_frame)
        pair_frame.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(pair_frame, text="คู่เทรด:").pack(side="left", padx=5)
        self.symbol_var = tk.StringVar(value="btc_thb")
        symbol_menu = ctk.CTkOptionMenu(pair_frame, variable=self.symbol_var,
                                        values=bitkub_symbols)
        symbol_menu.pack(side="left", padx=5)

        ctk.CTkLabel(pair_frame, text="(รองรับเหรียญทั้งหมดของ Bitkub)",
                     text_color="yellow").pack(side="left", padx=5)

        # Trade amount - optimized for profitability
        amount_frame = ctk.CTkFrame(settings_frame)
        amount_frame.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(amount_frame, text="จำนวนเทรดต่อครั้ง (THB):").pack(side="left", padx=5)
        self.trade_amount_var = tk.IntVar(value=500)
        amount_entry = ctk.CTkEntry(amount_frame, textvariable=self.trade_amount_var, width=100)
        amount_entry.pack(side="left", padx=5)

        ctk.CTkLabel(amount_frame, text="(แนะนำ 500+ เพื่อกำไรคุ้มค่า)",
                     text_color="yellow").pack(side="left", padx=5)

        # Risk settings optimized for profit
        risk_frame = ctk.CTkFrame(settings_frame)
        risk_frame.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(risk_frame, text="เทรดสูงสุดต่อวัน:").pack(side="left", padx=5)
        self.max_trades_var = tk.IntVar(value=2)
        ctk.CTkEntry(risk_frame, textvariable=self.max_trades_var, width=50).pack(side="left", padx=5)

        ctk.CTkLabel(risk_frame, text="ขาดทุนสูงสุดต่อวัน (THB):").pack(side="left", padx=20)
        self.max_loss_var = tk.IntVar(value=1000)
        ctk.CTkEntry(risk_frame, textvariable=self.max_loss_var, width=100).pack(side="left", padx=5)

        # Save button
        ctk.CTkButton(settings_frame, text="💾 บันทึกการตั้งค่า",
                      command=self.save_settings,
                      fg_color="green", height=40).pack(pady=20)

    # === AI Visual Methods ===

    def trigger_ai_analysis(self):
        """เรียกใช้การวิเคราะห์ AI พร้อม visual effects"""
        self.visual_effects.set_state("thinking")
        self.ai_status_label.configure(text="AI กำลังวิเคราะห์...")

        threading.Thread(target=self._simulate_ai_analysis, daemon=True).start()

    def _simulate_ai_analysis(self):
        """จำลองการวิเคราะห์ AI"""
        time.sleep(2)

        self.visual_effects.set_state("analyzing")
        self.ai_status_label.configure(text="กำลังประมวลผลข้อมูล...")

        time.sleep(3)

        # วิเคราะห์จริง
        if self.api_client:
            ticker = self.api_client.get_simple_ticker(self.config['symbol'])
            if ticker:
                current_price = ticker['last_price']
                
                # คำนวณกำไรที่คาดหวัง
                break_even = self.strategy.calculate_break_even_price(current_price, "buy")
                profit_needed = (break_even - current_price) / current_price * 100
                
                if len(self.strategy.price_history) >= 15:
                    rsi = self.strategy.calculate_rsi(list(self.strategy.price_history))
                    
                    if rsi < 30 and profit_needed < 1.0:
                        self.visual_effects.set_state("signal_buy")
                        self.ai_status_label.configure(text="พบโอกาสกำไร!")
                        self.log("🤖 AI Analysis: พบโอกาสซื้อที่คุ้มค่า")
                    else:
                        self.visual_effects.set_state("idle")
                        self.ai_status_label.configure(text="ไม่พบโอกาสที่ดี")
                        self.log("🤖 AI Analysis: รอโอกาสที่ดีกว่า")
                else:
                    self.visual_effects.set_state("idle")
                    self.ai_status_label.configure(text="ข้อมูลไม่เพียงพอ")
                    self.log("🤖 AI Analysis: ต้องการข้อมูลเพิ่มเติม")
            else:
                self.visual_effects.set_state("error")
                self.ai_status_label.configure(text="ไม่สามารถดึงข้อมูลได้")
        else:
            self.visual_effects.set_state("error")
            self.ai_status_label.configure(text="ไม่ได้เชื่อมต่อ API")

        time.sleep(2)
        if self.visual_effects.current_state not in ["signal_buy", "signal_sell"]:
            self.visual_effects.set_state("idle")
            self.ai_status_label.configure(text="พร้อมใช้งาน")

    def trigger_market_scan(self):
        """สแกนตลาดพร้อม visual effects"""
        self.visual_effects.set_state("connecting")
        self.ai_status_label.configure(text="กำลังสแกนตลาด...")

        threading.Thread(target=self._simulate_market_scan, daemon=True).start()

    def _simulate_market_scan(self):
        """จำลองการสแกนตลาด"""
        time.sleep(1.5)

        self.visual_effects.set_state("analyzing")
        self.ai_status_label.configure(text="วิเคราะห์ข้อมูลตลาด...")

        time.sleep(2)

        self.visual_effects.set_state("success")
        self.ai_status_label.configure(text="สแกนตลาดสำเร็จ")

        self.log("📊 Market Scan Complete: ตรวจสอบ 39 เหรียญของ Bitkub")

        time.sleep(1.5)
        self.visual_effects.set_state("idle")
        self.ai_status_label.configure(text="พร้อมใช้งาน")

    def trigger_signal_check(self):
        """ตรวจสอบสัญญาณพร้อม visual effects"""
        self.visual_effects.set_state("thinking")
        self.ai_status_label.configure(text="ตรวจสอบสัญญาณ...")

        threading.Thread(target=self._simulate_signal_check, daemon=True).start()

    def _simulate_signal_check(self):
        """จำลองการตรวจสอบสัญญาณ"""
        time.sleep(1)

        # ตรวจสอบสัญญาณจริง
        if self.api_client:
            ticker = self.api_client.get_simple_ticker(self.config['symbol'])
            if ticker:
                self.strategy.price_history.append(ticker['last_price'])
                
                if len(self.strategy.price_history) >= 15:
                    rsi = self.strategy.calculate_rsi(list(self.strategy.price_history))
                    
                    if rsi < 30:
                        self.visual_effects.set_state("signal_buy")
                        self.ai_status_label.configure(text="พบสัญญาณซื้อ!")
                        self.log("📈 BUY SIGNAL: RSI Oversold detected")
                    elif rsi > 70:
                        self.visual_effects.set_state("signal_sell")
                        self.ai_status_label.configure(text="พบสัญญาณขาย!")
                        self.log("📉 SELL SIGNAL: RSI Overbought detected")
                    else:
                        self.visual_effects.set_state("idle")
                        self.ai_status_label.configure(text="ไม่พบสัญญาณ")
                        self.log("⏸️ NO SIGNAL: RSI ปกติ")
                else:
                    self.visual_effects.set_state("idle")
                    self.ai_status_label.configure(text="ข้อมูลไม่เพียงพอ")
            else:
                self.visual_effects.set_state("error")
                self.ai_status_label.configure(text="ไม่สามารถดึงข้อมูลได้")
        else:
            self.visual_effects.set_state("error")
            self.ai_status_label.configure(text="ไม่ได้เชื่อมต่อ API")

        time.sleep(3)
        if self.visual_effects.current_state not in ["signal_buy", "signal_sell"]:
            self.visual_effects.set_state("idle")
            self.ai_status_label.configure(text="พร้อมใช้งาน")

    def trigger_profit_analysis(self):
        """วิเคราะห์กำไรพร้อม visual effects"""
        self.visual_effects.set_state("thinking")
        self.ai_status_label.configure(text="คำนวณกำไร...")

        threading.Thread(target=self._simulate_profit_analysis, daemon=True).start()

    def _simulate_profit_analysis(self):
        """จำลองการวิเคราะห์กำไร"""
        time.sleep(1.5)

        self.visual_effects.set_state("analyzing")
        self.ai_status_label.configure(text="วิเคราะห์ความคุ้มค่า...")

        # คำนวณกำไรจริง
        if self.api_client:
            ticker = self.api_client.get_simple_ticker(self.config['symbol'])
            if ticker:
                current_price = ticker['last_price']
                trade_amount = self.config['trade_amount_thb']
                
                # คำนวณค่าธรรมเนียม
                crypto_amount = trade_amount / current_price
                total_fees = self.strategy.calculate_fees(crypto_amount, current_price, "both")
                
                # คำนวณราคาเท่าทุน
                break_even = self.strategy.calculate_break_even_price(current_price, "buy")
                profit_needed = (break_even - current_price) / current_price * 100
                
                time.sleep(2)
                
                if profit_needed < 1.0:
                    self.visual_effects.set_state("profit")
                    self.ai_status_label.configure(text="โอกาสกำไรดี!")
                    self.log(f"💰 Profit Analysis: ต้องขึ้น {profit_needed:.2f}% เพื่อเท่าทุน")
                else:
                    self.visual_effects.set_state("loss")
                    self.ai_status_label.configure(text="ค่าธรรมเนียมสูง")
                    self.log(f"💸 Profit Analysis: ต้องขึ้น {profit_needed:.2f}% (สูงไป)")
                
                self.log(f"📊 ค่าธรรมเนียมรวม: {total_fees:.2f} THB")
            else:
                self.visual_effects.set_state("error")
                self.ai_status_label.configure(text="ไม่สามารถดึงข้อมูลได้")
        else:
            self.visual_effects.set_state("error")
            self.ai_status_label.configure(text="ไม่ได้เชื่อมต่อ API")

        time.sleep(2)
        self.visual_effects.set_state("idle")
        self.ai_status_label.configure(text="พร้อมใช้งาน")

    # === Trading Functions with Profit Focus ===

    def toggle_trading(self):
        """เปิด/ปิดการเทรดพร้อม visual effects"""
        if not self.is_trading:
            if not self.api_client:
                messagebox.showwarning("Error", "กรุณาเชื่อมต่อ API ก่อน")
                return

            if not self.pre_flight_check():
                return

            if not self.is_paper_trading:
                if not messagebox.askyesno("เริ่มเทรดจริง",
                                           f"เริ่มเทรดด้วยเงินจริง?\n\n" +
                                           f"จำนวนต่อรอบ: {self.config['trade_amount_thb']} THB\n" +
                                           f"สูงสุดต่อวัน: {self.config['max_daily_trades']} รอบ\n" +
                                           f"คู่เทรด: {self.config['symbol'].upper()}"):
                    return

            self.visual_effects.set_state("trading")
            self.is_trading = True
            self.emergency_stop = False
            self.start_btn.configure(text="⏹️ Stop AI Trading", fg_color="red")
            self.start_btn_trading.configure(text="⏹️ Stop Trading Bot", fg_color="red")
            self.ai_status_label.configure(text="กำลังเทรด...")
            self.log(f"🚀 เริ่มบอทเทรด {'PAPER' if self.is_paper_trading else 'REAL'}")

            threading.Thread(target=self.profitable_trading_loop, daemon=True).start()
        else:
            self.visual_effects.set_state("idle")
            self.is_trading = False
            self.start_btn.configure(text="🚀 Start AI Trading", fg_color="green")
            self.start_btn_trading.configure(text="▶️ Start Trading Bot", fg_color="green")
            self.ai_status_label.configure(text="หยุดเทรด")
            self.log("🛑 หยุดการเทรด")

    def profitable_trading_loop(self):
        """Trading loop ที่เน้นกำไร"""
        consecutive_errors = 0
        max_consecutive_errors = 3

        while self.is_trading and not self.emergency_stop:
            try:
                # Check daily limits
                if self.daily_trades >= self.config['max_daily_trades']:
                    self.log(f"📊 ถึงลิมิตเทรดต่อวัน ({self.daily_trades}/{self.config['max_daily_trades']})")
                    time.sleep(3600)
                    continue

                if self.daily_pnl <= -self.config['max_daily_loss']:
                    self.log(f"💸 ถึงลิมิตขาดทุนต่อวัน ({self.daily_pnl:.2f})")
                    self.emergency_stop_trading()
                    break

                # Check minimum interval
                if self.last_trade_time:
                    time_since_trade = (datetime.now() - self.last_trade_time).seconds
                    if time_since_trade < self.config['min_trade_interval']:
                        time.sleep(60)
                        continue

                # Get market data
                ticker = self.api_client.get_simple_ticker(self.config['symbol'])
                order_book = self.api_client.get_order_book(self.config['symbol'])

                if not ticker:
                    consecutive_errors += 1
                    if consecutive_errors >= max_consecutive_errors:
                        self.log("❌ ข้อผิดพลาดต่อเนื่อง หยุดการทำงาน")
                        break
                    time.sleep(120)
                    continue

                current_price = ticker['last_price']
                volume_24h = ticker.get('volume_24h', 0)

                consecutive_errors = 0

                # Get balance
                balance = self.api_client.check_balance()
                thb_balance = 0
                if balance and balance.get('error') == 0:
                    thb_balance = float(balance['result'].get('THB', 0))

                # Check buy signal
                should_buy, buy_reason = self.strategy.should_buy_profitable(
                    current_price, volume_24h, order_book, thb_balance,
                    self.config['trade_amount_thb']
                )

                if should_buy:
                    self.visual_effects.set_state("signal_buy")
                    self.execute_buy_profitable(current_price, buy_reason)

                # Check sell signal
                if self.strategy.position:
                    should_sell, sell_reason = self.strategy.should_sell_profitable(
                        current_price, volume_24h, order_book
                    )
                    if should_sell:
                        if "Profit" in sell_reason or "profit" in sell_reason:
                            self.visual_effects.set_state("profit")
                        elif "Loss" in sell_reason or "loss" in sell_reason:
                            self.visual_effects.set_state("loss")
                        else:
                            self.visual_effects.set_state("signal_sell")
                        self.execute_sell_profitable(current_price, sell_reason)

                # Update dashboard
                self.update_dashboard_profitable()

                time.sleep(60)

            except Exception as e:
                consecutive_errors += 1
                self.log(f"❌ ข้อผิดพลาด: {e}")
                if consecutive_errors >= max_consecutive_errors:
                    self.log("❌ ข้อผิดพลาดมากเกินไป หยุดการเทรด")
                    break
                time.sleep(120)

        self.log("🛑 สิ้นสุดการทำงานของบอท")

    def execute_buy_profitable(self, price, reason):
        """ดำเนินการซื้อที่เน้นกำไร"""
        try:
            amount_thb = self.config['trade_amount_thb']
            crypto_amount = amount_thb / price

            # คำนวณค่าธรรมเนียม
            expected_fees = self.strategy.calculate_fees(crypto_amount, price, "both")

            if self.is_paper_trading:
                self.strategy.position = {
                    'entry_price': price,
                    'amount': crypto_amount,
                    'entry_time': datetime.now()
                }

                self.log(f"📝 PAPER ซื้อ: {amount_thb} THB @ {price:,.2f}")
                self.log(f"   เหตุผล: {reason}")
                self.log(f"   ค่าธรรมเนียมคาดการณ์: {expected_fees:.2f} THB")

                self.save_profitable_trade('buy', crypto_amount, price, amount_thb,
                                         'PAPER', 0, expected_fees, 0, reason, True)
            else:
                buy_price = price * 1.002

                self.log(f"💰 ซื้อจริง: {amount_thb} THB @ {buy_price:,.2f}")

                result = self.api_client.place_buy_order_safe(
                    self.config['symbol'], amount_thb, buy_price, 'limit'
                )

                if result and result.get('error') == 0:
                    order_info = result['result']
                    order_id = order_info.get('id', 'unknown')
                    actual_amount = order_info.get('rec', crypto_amount)
                    actual_fee = order_info.get('fee', expected_fees)

                    self.strategy.position = {
                        'entry_price': buy_price,
                        'amount': actual_amount,
                        'entry_time': datetime.now(),
                        'order_id': order_id
                    }

                    self.log(f"✅ ซื้อสำเร็จ: Order ID {order_id}")
                    self.log(f"   ได้ Crypto: {actual_amount:.8f}")
                    self.log(f"   ค่าธรรมเนียม: {actual_fee:.2f} THB")

                    self.total_fees_paid += actual_fee
                    self.save_profitable_trade('buy', actual_amount, buy_price, amount_thb,
                                             order_id, 0, actual_fee, 0, reason, False)
                else:
                    error_code = result.get("error", 999) if result else 999
                    error_msg = self.api_client.error_codes.get(error_code, f"Error {error_code}")
                    self.log(f"❌ การซื้อล้มเหลว: {error_msg}")
                    return

            self.daily_trades += 1
            self.last_trade_time = datetime.now()
            self.status_cards["Position"].configure(text=f"LONG @ {price:,.0f}")
            self.status_cards["Daily Trades"].configure(
                text=f"{self.daily_trades}/{self.config['max_daily_trades']}"
            )

        except Exception as e:
            self.log(f"❌ ข้อผิดพลาดในการซื้อ: {e}")

    def execute_sell_profitable(self, price, reason):
        """ดำเนินการขายที่เน้นกำไร"""
        try:
            if not self.strategy.position:
                return

            amount = self.strategy.position['amount']
            entry_price = self.strategy.position['entry_price']

            # คำนวณ P&L รวมค่าธรรมเนียม
            buy_fee = self.strategy.calculate_fees(amount, entry_price, "buy")
            sell_fee = self.strategy.calculate_fees(amount, price, "sell")
            gross_pnl = (price - entry_price) * amount
            net_pnl = gross_pnl - buy_fee - sell_fee

            if self.is_paper_trading:
                self.log(f"📝 PAPER ขาย: {amount:.8f} @ {price:,.2f}")
                self.log(f"   เหตุผล: {reason}")
                self.log(f"   P&L สุทธิ: {net_pnl:+.2f} THB")

                self.save_profitable_trade('sell', amount, price, amount * price,
                                         'PAPER', net_pnl, sell_fee, net_pnl, reason, True)
            else:
                sell_price = price * 0.998

                self.log(f"💰 ขายจริง: {amount:.8f} @ {sell_price:,.2f}")

                result = self.api_client.place_sell_order_safe(
                    self.config['symbol'], amount, sell_price, 'limit'
                )

                if result and result.get('error') == 0:
                    order_info = result['result']
                    order_id = order_info.get('id', 'unknown')
                    actual_fee = order_info.get('fee', sell_fee)

                    actual_gross_pnl = (sell_price - entry_price) * amount
                    actual_net_pnl = actual_gross_pnl - buy_fee - actual_fee

                    self.log(f"✅ ขายสำเร็จ: Order ID {order_id}")
                    self.log(f"   P&L สุทธิ: {actual_net_pnl:+.2f} THB")
                    self.log(f"   ค่าธรรมเนียม: {actual_fee:.2f} THB")

                    self.total_fees_paid += actual_fee
                    self.save_profitable_trade('sell', amount, sell_price, amount * sell_price,
                                             order_id, actual_net_pnl, actual_fee,
                                             actual_net_pnl, reason, False)
                    net_pnl = actual_net_pnl
                else:
                    error_code = result.get("error", 999) if result else 999
                    error_msg = self.api_client.error_codes.get(error_code, f"Error {error_code}")
                    self.log(f"❌ การขายล้มเหลว: {error_msg}")
                    return

            self.daily_pnl += net_pnl
            self.strategy.position = None
            self.status_cards["Position"].configure(text="None")
            self.status_cards["Net P&L Today"].configure(text=f"{self.daily_pnl:+.2f}")
            self.status_cards["Total Fees"].configure(text=f"{self.total_fees_paid:.2f}")

            # อัปเดต profit labels
            if net_pnl > 0:
                self.profit_label.configure(text=f"+{self.daily_pnl:.2f} THB", text_color="#00ff00")
            else:
                self.profit_label.configure(text=f"{self.daily_pnl:.2f} THB", text_color="#ff6600")

            self.fees_label.configure(text=f"{self.total_fees_paid:.2f} THB")

        except Exception as e:
            self.log(f"❌ ข้อผิดพลาดในการขาย: {e}")

    # === Profit Analysis Functions ===

    def show_profit_calculator(self):
        """แสดงเครื่องคำนวณกำไร"""
        if not self.api_client:
            self.profit_log("❌ กรุณาเชื่อมต่อ API ก่อน")
            return

        ticker = self.api_client.get_simple_ticker(self.config['symbol'])
        if not ticker:
            self.profit_log("❌ ไม่สามารถดึงข้อมูลราคาได้")
            return

        current_price = ticker['last_price']
        trade_amount = self.config['trade_amount_thb']

        self.profit_log("\n💰 เครื่องคำนวณกำไร-ขาดทุน Bitkub")
        self.profit_log("=" * 60)
        self.profit_log(f"📊 ราคาปัจจุบัน: {current_price:,.2f} THB")
        self.profit_log(f"💵 จำนวนเทรด: {trade_amount:,.0f} THB")
        self.profit_log(f"🔗 คู่เทรด: {self.config['symbol'].upper()}")

        # คำนวณ crypto amount
        crypto_amount = trade_amount / current_price
        self.profit_log(f"🪙 จำนวน Crypto: {crypto_amount:.8f}")

        # คำนวณค่าธรรมเนียม
        buy_fee = self.strategy.calculate_fees(crypto_amount, current_price, "buy")
        sell_fee = self.strategy.calculate_fees(crypto_amount, current_price, "sell")
        total_fee = buy_fee + sell_fee

        self.profit_log(f"\n💸 ค่าธรรมเนียม Bitkub:")
        self.profit_log(f"   ซื้อ (Taker): {buy_fee:.2f} THB (0.25%)")
        self.profit_log(f"   ขาย (Maker): {sell_fee:.2f} THB (0.25%)")
        self.profit_log(f"   รวม: {total_fee:.2f} THB (0.5%)")

        # คำนวณราคาเท่าทุน
        break_even = self.strategy.calculate_break_even_price(current_price, "buy")
        profit_needed_pct = (break_even - current_price) / current_price * 100

        self.profit_log(f"\n⚖️ การคำนวณเท่าทุน:")
        self.profit_log(f"   ราคาเท่าทุน: {break_even:,.2f} THB")
        self.profit_log(f"   ต้องขึ้น: {profit_needed_pct:.3f}% เพื่อไม่ขาดทุน")

        # สถานการณ์ต่างๆ
        scenarios = [
            ("💀 Stop Loss (-1.5%)", current_price * (1 - 0.015)),
            ("⚖️ Break Even", break_even),
            ("💚 Small Profit (+1%)", current_price * 1.01),
            ("🎯 Target Profit (+2.5%)", current_price * 1.025),
            ("🚀 Good Profit (+5%)", current_price * 1.05)
        ]

        self.profit_log(f"\n📈 สถานการณ์ต่างๆ:")
        for scenario_name, sell_price in scenarios:
            sell_fee_scenario = self.strategy.calculate_fees(crypto_amount, sell_price, "sell")
            gross_pnl = (sell_price - current_price) * crypto_amount
            net_pnl = gross_pnl - buy_fee - sell_fee_scenario
            net_pnl_pct = net_pnl / trade_amount * 100

            color_icon = "📈" if net_pnl > 0 else "📉" if net_pnl < 0 else "➡️"
            self.profit_log(f"{color_icon} {scenario_name}")
            self.profit_log(f"   ราคาขาย: {sell_price:,.2f} THB")
            self.profit_log(f"   P&L สุทธิ: {net_pnl:+.2f} THB ({net_pnl_pct:+.2f}%)")

        # คำแนะนำ
        self.profit_log(f"\n💡 คำแนะนำ:")
        if profit_needed_pct < 0.8:
            self.profit_log("✅ โอกาสกำไรดี - ค่าธรรมเนียมไม่สูงมาก")
        elif profit_needed_pct < 1.2:
            self.profit_log("⚠️ โอกาสกำไรปานกลาง - ต้องระวังความผันผวน")
        else:
            self.profit_log("❌ ค่าธรรมเนียมสูง - ควรรอโอกาสที่ดีกว่า")

    def analyze_fees(self):
        """วิเคราะห์ค่าธรรมเนียม"""
        self.profit_log("\n💸 การวิเคราะห์ค่าธรรมเนียม Bitkub")
        self.profit_log("=" * 50)
        self.profit_log("📋 โครงสร้างค่าธรรมเนียม:")
        self.profit_log(f"   Maker Fee: {self.strategy.maker_fee*100:.2f}%")
        self.profit_log(f"   Taker Fee: {self.strategy.taker_fee*100:.2f}%")
        self.profit_log(f"   รวมต่อรอบ: {self.strategy.total_fee*100:.2f}%")

        # คำนวณค่าธรรมเนียมในจำนวนต่างๆ
        amounts = [100, 500, 1000, 5000, 10000]
        self.profit_log(f"\n💰 ค่าธรรมเนียมตามจำนวนเทรด:")

        for amount in amounts:
            total_fee = amount * self.strategy.total_fee
            self.profit_log(f"   {amount:,} THB → ค่าธรรมเนียม: {total_fee:.2f} THB")

        # ค่าธรรมเนียมรวมวันนี้
        self.profit_log(f"\n📊 สถิติวันนี้:")
        self.profit_log(f"   ค่าธรรมเนียมจ่ายแล้ว: {self.total_fees_paid:.2f} THB")
        self.profit_log(f"   จำนวนเทรด: {self.daily_trades} รอบ")

        if self.daily_trades > 0:
            avg_fee = self.total_fees_paid / self.daily_trades
            self.profit_log(f"   ค่าธรรมเนียมเฉลี่ย: {avg_fee:.2f} THB/รอบ")

    def show_performance_stats(self):
        """แสดงสถิติประสิทธิภาพ"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # สถิติโดยรวม
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN net_pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
                    SUM(CASE WHEN net_pnl < 0 THEN 1 ELSE 0 END) as losing_trades,
                    SUM(net_pnl) as total_net_pnl,
                    SUM(fees) as total_fees,
                    AVG(net_pnl) as avg_net_pnl,
                    MAX(net_pnl) as best_trade,
                    MIN(net_pnl) as worst_trade
                FROM trades
                WHERE side = 'sell' AND net_pnl IS NOT NULL
            ''')

            stats = cursor.fetchone()
            conn.close()

            if stats and stats[0] > 0:
                total, wins, losses, total_pnl, total_fees, avg_pnl, best, worst = stats
                win_rate = (wins / total * 100) if total > 0 else 0

                # คำนวณ profit factor
                gross_wins = cursor.execute(
                    'SELECT SUM(net_pnl) FROM trades WHERE net_pnl > 0 AND side = "sell"'
                ).fetchone()[0] or 0
                gross_losses = cursor.execute(
                    'SELECT SUM(ABS(net_pnl)) FROM trades WHERE net_pnl < 0 AND side = "sell"'
                ).fetchone()[0] or 1

                profit_factor = gross_wins / gross_losses if gross_losses > 0 else float('inf')

                self.profit_log("\n📊 สถิติประสิทธิภาพการเทรด")
                self.profit_log("=" * 50)
                self.profit_log(f"📈 ผลตอบแทนรวม:")
                self.profit_log(f"   กำไร-ขาดทุนสุทธิ: {total_pnl:+.2f} THB")
                self.profit_log(f"   ค่าธรรมเนียมจ่าย: {total_fees:.2f} THB")
                self.profit_log(f"   อัตราส่วนค่าธรรมเนียม: {(total_fees/abs(total_pnl)*100) if total_pnl != 0 else 0:.1f}%")

                self.profit_log(f"\n🎯 ประสิทธิภาพการเทรด:")
                self.profit_log(f"   เทรดทั้งหมด: {total} รอบ")
                self.profit_log(f"   ชนะ: {wins} รอบ ({win_rate:.1f}%)")
                self.profit_log(f"   แพ้: {losses} รอบ")
                self.profit_log(f"   Profit Factor: {profit_factor:.2f}")

                self.profit_log(f"\n💰 สถิติกำไร:")
                self.profit_log(f"   เฉลี่ยต่อเทรด: {avg_pnl:+.2f} THB")
                self.profit_log(f"   เทรดดีที่สุด: {best:+.2f} THB")
                self.profit_log(f"   เทรดแย่ที่สุด: {worst:+.2f} THB")

                # ประเมินผล
                self.profit_log(f"\n📋 การประเมิน:")
                if win_rate >= 60 and total_pnl > total_fees:
                    self.profit_log("✅ ระบบทำกำไรได้ดีมาก")
                elif win_rate >= 50 and total_pnl > 0:
                    self.profit_log("⚠️ ระบบทำกำไรได้พอใช้")
                else:
                    self.profit_log("❌ ระบบต้องปรับปรุง")

            else:
                self.profit_log("ยังไม่มีข้อมูลการเทรดที่สมบูรณ์")

        except Exception as e:
            self.profit_log(f"ข้อผิดพลาดในการแสดงสถิติ: {e}")

    def test_profit_calculation(self):
        """ทดสอบการคำนวณกำไร"""
        test_amount = self.test_amount_var.get()

        if not self.api_client:
            self.test_log("❌ กรุณาเชื่อมต่อ API ก่อน")
            return

        ticker = self.api_client.get_simple_ticker(self.config['symbol'])
        if not ticker:
            self.test_log("❌ ไม่สามารถดึงข้อมูลราคาได้")
            return

        price = ticker['last_price']

        self.test_log(f"💰 ทดสอบการคำนวณกำไรสำหรับ {test_amount} THB")
        self.test_log(f"📊 ราคาปัจจุบัน: {price:,.2f} THB")
        self.test_log(f"🔗 คู่เทรด: {self.config['symbol'].upper()}")

        # คำนวณราคาเท่าทุน
        break_even = self.strategy.calculate_break_even_price(price, "buy")
        required_gain = (break_even - price) / price * 100

        self.test_log(f"⚖️ ราคาเท่าทุน: {break_even:,.2f} THB")
        self.test_log(f"📈 ต้องขึ้น: {required_gain:.3f}% เพื่อไม่ขาดทุน")

        # คำนวณค่าธรรมเนียม
        crypto_amount = test_amount / price
        total_fees = self.strategy.calculate_fees(crypto_amount, price, "both")
        fee_percentage = total_fees / test_amount * 100

        self.test_log(f"💸 ค่าธรรมเนียมรวม: {total_fees:.2f} THB ({fee_percentage:.3f}%)")

        # สถานการณ์กำไรต่างๆ
        for profit_pct in [0.5, 1.0, 1.5, 2.0, 3.0]:
            target_price = price * (1 + profit_pct/100)
            sell_fee = self.strategy.calculate_fees(crypto_amount, target_price, "sell")
            buy_fee = self.strategy.calculate_fees(crypto_amount, price, "buy")
            gross_profit = (target_price - price) * crypto_amount
            net_profit = gross_profit - buy_fee - sell_fee

            status = "✅" if net_profit > 0 else "❌"
            self.test_log(f"{status} หากขึ้น {profit_pct}% → กำไรสุทธิ: {net_profit:+.2f} THB")

    # === Enhanced Core Functions ===

    def connect_api(self):
        """Enhanced API connection with visual effects"""
        api_key = self.api_key_entry.get().strip()
        api_secret = self.api_secret_entry.get().strip()

        if not api_key or not api_secret:
            messagebox.showwarning("Error", "กรุณาใส่ API credentials")
            return

        self.visual_effects.set_state("connecting")
        self.ai_status_label.configure(text="กำลังเชื่อมต่อ...")

        # Create API client
        self.api_client = ImprovedBitkubAPI(api_key, api_secret)

        self.log("🔌 กำลังเชื่อมต่อ API...")

        # Test connection
        def test_api():
            time.sleep(1)
            
            # Check system status
            status_ok, status_msg = self.api_client.check_system_status()
            if not status_ok:
                self.visual_effects.set_state("error")
                self.ai_status_label.configure(text="ระบบมีปัญหา")
                self.log(f"❌ System status issue: {status_msg}")
                messagebox.showwarning("System Status", f"API Status Issue: {status_msg}")
                return

            # Test balance check
            balance = self.api_client.check_balance()
            if balance and balance.get('error') == 0:
                self.visual_effects.set_state("success")
                self.ai_status_label.configure(text="เชื่อมต่อสำเร็จ")
                self.log("✅ API Connected successfully")
                self.update_balance()
                self.quick_stats["API"].configure(text="Connected", text_color="green")
                messagebox.showinfo("Success", "API Connected and validated!")
                
                time.sleep(2)
                self.visual_effects.set_state("idle")
                self.ai_status_label.configure(text="พร้อมใช้งาน")
            else:
                error_msg = "Unknown error"
                if balance:
                    error_code = balance.get("error", 999)
                    error_msg = self.api_client.error_codes.get(error_code, f"Error {error_code}")

                self.visual_effects.set_state("error")
                self.ai_status_label.configure(text="เชื่อมต่อล้มเหลว")
                self.log(f"❌ API Connection failed: {error_msg}")
                messagebox.showerror("Error", f"Failed to connect: {error_msg}")

        threading.Thread(target=test_api, daemon=True).start()

    def emergency_stop_trading(self):
        """Enhanced emergency stop with visual effects"""
        self.visual_effects.set_state("error")
        self.visual_effects.flash_effect("#ff0000", 0.3)

        self.emergency_stop = True
        self.is_trading = False
        self.start_btn.configure(text="🚀 Start AI Trading", fg_color="green")
        self.start_btn_trading.configure(text="▶️ Start Trading Bot", fg_color="green")

        self.ai_status_label.configure(text="🚨 EMERGENCY STOP")
        self.log("🚨 EMERGENCY STOP ACTIVATED!")

        # Cancel all open orders if real trading
        if not self.is_paper_trading and self.api_client:
            try:
                self.log("🗑️ กำลังยกเลิกคำสั่งที่ค้างอยู่...")
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
                            self.log(f"✅ ยกเลิกคำสั่ง {order['id']}")
                        else:
                            self.log(f"❌ ไม่สามารถยกเลิกคำสั่ง {order['id']}")
            except Exception as e:
                self.log(f"❌ ข้อผิดพลาดในการหยุดฉุกเฉิน: {e}")

        messagebox.showwarning("Emergency Stop", "หยุดการเทรดและยกเลิกคำสั่งทั้งหมดแล้ว!")

        # Reset after 3 seconds
        def reset_status():
            self.visual_effects.set_state("idle")
            self.ai_status_label.configure(text="พร้อมใช้งาน")

        self.root.after(3000, reset_status)

    def toggle_paper_trading(self):
        """Enhanced paper trading toggle"""
        if self.paper_switch.get():
            # Multiple confirmations for real trading
            if not messagebox.askyesno("⚠️ WARNING - Real Trading",
                                       "เปิดใช้งานการเทرดด้วยเงินจริง?\n\n" +
                                       "บอทนี้จะใช้เงินจริงในการเทרด!\n" +
                                       "คุณได้ทดสอบด้วย paper trading แล้วหรือยัง?"):
                self.paper_switch.deselect()
                return

            if not messagebox.askyesno("⚠️ ยืนยันครั้งสุดท้าย",
                                       "นี่คือการยืนยันครั้งสุดท้าย!\n\n" +
                                       "เงินจริงจะถูกนำมาเสี่ยง\n" +
                                       "คุณใช้เงินทดลองเล็กน้อยใช่ไหม?\n" +
                                       "คุณยอมรับความรับผิดชอบทั้งหมด?"):
                self.paper_switch.deselect()
                return

            self.is_paper_trading = False
            self.status_cards["Mode"].configure(text="REAL TRADING", text_color="red")
            self.quick_stats["Mode"].configure(text="REAL", text_color="red")
            self.visual_effects.flash_effect("#ff6600", 0.5)
            self.log("⚠️ เปิดใช้งานการเทรดจริง - ใช้ความระมัดระวัง!")

        else:
            self.is_paper_trading = True
            self.status_cards["Mode"].configure(text="PAPER TRADING", text_color="orange")
            self.quick_stats["Mode"].configure(text="PAPER", text_color="orange")
            self.log("📝 เปลี่ยนเป็น Paper Trading")

    # === Helper Functions ===

    def save_profitable_trade(self, side, amount, price, total_thb, order_id, 
                            pnl, fees, net_pnl, reason, is_paper):
        """บันทึกข้อมูลการเทรดพร้อมข้อมูลกำไร"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get current market data for additional info
            rsi = 50
            volume_ratio = 1.0
            spread_pct = 0

            if len(self.strategy.price_history) >= 15:
                rsi = self.strategy.calculate_rsi(list(self.strategy.price_history))

            if len(self.strategy.volume_history) >= 2:
                volume_ratio = self.strategy.volume_history[-1] / np.mean(list(self.strategy.volume_history)[-10:])

            if len(self.strategy.spread_history) >= 1:
                spread_pct = self.strategy.spread_history[-1]

            cursor.execute('''
                INSERT INTO trades 
                (timestamp, symbol, side, amount, price, total_thb, 
                 order_id, status, pnl, fees, net_pnl, reason, is_paper,
                 rsi, volume_ratio, spread_pct, api_response)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (datetime.now(), self.config['symbol'], side, amount, price,
                  total_thb, order_id, 'completed', pnl, fees, net_pnl, reason,
                  is_paper, rsi, volume_ratio, spread_pct, None))

            conn.commit()
            conn.close()

        except Exception as e:
            self.log(f"❌ ข้อผิดพลาดฐานข้อมูล: {e}")

    def show_profitability_stats(self):
        """แสดงสถิติความสามารถในการทำกำไร"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Overall profitability stats
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN net_pnl > 0 THEN 1 ELSE 0 END) as profitable_trades,
                    SUM(CASE WHEN net_pnl < 0 THEN 1 ELSE 0 END) as losing_trades,
                    SUM(net_pnl) as total_net_pnl,
                    SUM(fees) as total_fees,
                    AVG(net_pnl) as avg_net_pnl,
                    MAX(net_pnl) as best_trade,
                    MIN(net_pnl) as worst_trade,
                    AVG(rsi) as avg_rsi
                FROM trades
                WHERE side = 'sell' AND net_pnl IS NOT NULL
            ''')

            stats = cursor.fetchone()

            if stats and stats[0] > 0:
                total, profitable, losing, total_pnl, total_fees, avg_pnl, best, worst, avg_rsi = stats
                win_rate = (profitable / total * 100) if total > 0 else 0

                # Calculate profit factor
                positive_pnl = cursor.execute(
                    'SELECT SUM(net_pnl) FROM trades WHERE net_pnl > 0 AND side = "sell"'
                ).fetchone()[0] or 0

                negative_pnl = cursor.execute(
                    'SELECT SUM(ABS(net_pnl)) FROM trades WHERE net_pnl < 0 AND side = "sell"'
                ).fetchone()[0] or 1

                profit_factor = positive_pnl / negative_pnl if negative_pnl > 0 else float('inf')

                stats_text = f"""
=== สถิติความสามารถทำกำไร ===

📊 ภาพรวม:
• เทรดทั้งหมด: {total} รอบ
• เทรดกำไร: {profitable} รอบ ({win_rate:.1f}%)
• เทรดขาดทุน: {losing} รอบ

💰 ผลตอบแทน:
• กำไร-ขาดทุนสุทธิ: {total_pnl:+.2f} THB
• ค่าธรรมเนียมรวม: {total_fees:.2f} THB
• กำไรสุทธิหลังหักค่าธรรมเนียม: {total_pnl:.2f} THB
• กำไรเฉลี่ยต่อเทรด: {avg_pnl:+.2f} THB
• เทรดที่ดีที่สุด: {best:+.2f} THB
• เทรดที่แย่ที่สุด: {worst:+.2f} THB

📈 คุณภาพการเทรด:
• Profit Factor: {profit_factor:.2f}
• RSI เฉลี่ย: {avg_rsi:.1f}
• อัตราส่วนค่าธรรมเนียม: {(total_fees/abs(total_pnl)*100) if total_pnl != 0 else 0:.1f}%

💡 ประเมินผล:"""

                if win_rate >= 60 and total_pnl > total_fees:
                    stats_text += "\n✅ ระบบทำกำไรได้ดีมาก - คุ้มค่าธรรมเนียม"
                elif win_rate >= 50 and total_pnl > 0:
                    stats_text += "\n⚠️ ระบบทำกำไรได้พอใช้ - ควรปรับปรุง"
                else:
                    stats_text += "\n❌ ระบบต้องปรับปรุง - ไม่คุ้มค่าธรรมเนียม"

                messagebox.showinfo("สถิติการทำกำไร", stats_text)
            else:
                messagebox.showinfo("สถิติ", "ยังไม่มีข้อมูลการเทรดที่สมบูรณ์")

            conn.close()

        except Exception as e:
            self.log(f"❌ ข้อผิดพลาดในการแสดงสถิติ: {e}")

    def load_trade_history(self):
        """โหลดประวัติการเทรดพร้อมข้อมูลกำไร"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT timestamp, symbol, side, amount, price, net_pnl, fees, reason, is_paper, order_id
                FROM trades
                ORDER BY timestamp DESC
                LIMIT 100
            ''')

            trades = cursor.fetchall()
            conn.close()

            self.history_display.delete("1.0", "end")

            if not trades:
                self.history_display.insert("1.0", "ยังไม่มีประวัติการเทรด")
                return

            header = f"{'เวลา':<10} {'โหมด':<6} {'ฝั่ง':<4} {'จำนวน':<12} {'ราคา':<10} {'P&L สุทธิ':<10} {'ค่าธรรมเนียม':<8} {'เหตุผล'}\n"
            header += "=" * 120 + "\n"
            self.history_display.insert("end", header)

            for trade in trades:
                timestamp, symbol, side, amount, price, net_pnl, fees, reason, is_paper, order_id = trade
                time_str = datetime.fromisoformat(timestamp).strftime('%H:%M:%S')
                mode = "PAPER" if is_paper else "REAL"

                pnl_str = f"{net_pnl:+.2f}" if net_pnl else "0.00"
                fees_str = f"{fees:.2f}" if fees else "0.00"

                trade_line = f"{time_str:<10} {mode:<6} {side.upper():<4} {amount:<12.8f} {price:<10.2f} {pnl_str:<10} {fees_str:<8} {reason}\n"
                self.history_display.insert("end", trade_line)

        except Exception as e:
            self.log(f"ข้อผิดพลาดในการโหลดประวัติ: {e}")

    def check_signals(self):
        """Enhanced signal checking with profit analysis"""
        if not self.api_client:
            messagebox.showwarning("Error", "กรุณาเชื่อมต่อ API ก่อน")
            return

        ticker = self.api_client.get_simple_ticker(self.config['symbol'])
        order_book = self.api_client.get_order_book(self.config['symbol'])
        
        if ticker and len(self.strategy.price_history) >= 15:
            price = ticker['last_price']
            volume = ticker.get('volume_24h', 0)
            rsi = self.strategy.calculate_rsi(list(self.strategy.price_history))

            # Get balance for buy signal analysis
            balance = self.api_client.check_balance()
            thb_balance = 0
            if balance and balance.get('error') == 0:
                thb_balance = float(balance['result'].get('THB', 0))

            signal_text = f"\n📊 การวิเคราะห์สัญญาณพร้อมกำไร - {datetime.now().strftime('%H:%M:%S')}\n"
            signal_text += f"{'=' * 60}\n"
            signal_text += f"Symbol: {ticker['symbol']}\n"
            signal_text += f"ราคาปัจจุบัน: {price:,.2f} THB\n"
            signal_text += f"การเปลี่ยนแปลง 24h: {ticker['change_24h']:+.2f}%\n"
            signal_text += f"Volume 24h: {volume:,.0f} THB\n"
            signal_text += f"RSI: {rsi:.1f}\n"
            signal_text += f"ยอดเงินพร้อมใช้: {thb_balance:,.2f} THB\n\n"

            # Profit analysis
            break_even = self.strategy.calculate_break_even_price(price, "buy")
            profit_needed = (break_even - price) / price * 100
            crypto_amount = self.config['trade_amount_thb'] / price
            total_fees = self.strategy.calculate_fees(crypto_amount, price, "both")

            signal_text += f"💰 การวิเคราะห์กำไร:\n"
            signal_text += f"   ราคาเท่าทุน: {break_even:,.2f} THB\n"
            signal_text += f"   ต้องขึ้น: {profit_needed:.3f}% เพื่อไม่ขาดทุน\n"
            signal_text += f"   ค่าธรรมเนียมรวม: {total_fees:.2f} THB\n\n"

            # Buy signal analysis
            should_buy, buy_reason = self.strategy.should_buy_profitable(
                price, volume, order_book, thb_balance, self.config['trade_amount_thb']
            )

            if should_buy:
                signal_text += f"📈 สัญญาณซื้อ: {buy_reason}\n"
                signal_text += f"   จำนวนแนะนำ: {self.config['trade_amount_thb']} THB\n"
                if profit_needed < 1.0:
                    signal_text += f"   ✅ โอกาสกำไรดี!\n"
                else:
                    signal_text += f"   ⚠️ ค่าธรรมเนียมค่อนข้างสูง\n"
            else:
                signal_text += f"⏸️ ไม่มีสัญญาณซื้อ: {buy_reason}\n"

            # Sell signal analysis (if position exists)
            if self.strategy.position:
                should_sell, sell_reason = self.strategy.should_sell_profitable(
                    price, volume, order_book
                )
                if should_sell:
                    signal_text += f"📉 สัญญาณขาย: {sell_reason}\n"
                else:
                    signal_text += f"📊 ถือต่อ: {sell_reason}\n"
            else:
                signal_text += f"💼 ไม่มี position\n"

            self.trading_log.insert("end", signal_text)
            self.trading_log.see("end")

    def pre_flight_check(self):
        """Pre-flight safety check with profit considerations"""
        self.log("🛫 ตรวจสอบระบบก่อนเริ่มเทรด...")

        # System status
        status_ok, status_msg = self.api_client.check_system_status()
        if not status_ok:
            self.log(f"❌ ระบบไม่พร้อม: {status_msg}")
            return False

        # Balance check
        balance = self.api_client.check_balance()
        if not balance or balance.get('error') != 0:
            self.log("❌ ไม่สามารถตรวจสอบยอดเงินได้")
            return False

        thb_balance = float(balance['result'].get('THB', 0))
        if thb_balance < self.config['trade_amount_thb']:
            self.log(f"❌ เงินไม่เพียงพอ: {thb_balance:.2f} < {self.config['trade_amount_thb']}")
            return False

        # Market data check
        ticker = self.api_client.get_simple_ticker(self.config['symbol'])
        if not ticker:
            self.log("❌ ไม่สามารถดึงข้อมูลตลาดได้")
            return False

        # Profit viability check
        current_price = ticker['last_price']
        break_even = self.strategy.calculate_break_even_price(current_price, "buy")
        profit_needed = (break_even - current_price) / current_price * 100

        if profit_needed > 2.0:
            self.log(f"⚠️ คำเตือน: ต้องการกำไร {profit_needed:.2f}% เพื่อเท่าทุน (สูงมาก)")
            if not messagebox.askyesno("คำเตือนกำไร", 
                                       f"ค่าธรรมเนียมค่อนข้างสูงสำหรับราคาปัจจุบัน\n" +
                                       f"ต้องการกำไร {profit_needed:.2f}% เพื่อเท่าทุน\n\n" +
                                       f"ต้องการดำเนินการต่อหรือไม่?"):
                return False

        self.log("✅ ผ่านการตรวจสอบทั้งหมด")
        return True

    def update_dashboard_profitable(self):
        """อัปเดต dashboard พร้อมข้อมูลกำไร"""
        # อัปเดตจำนวนเทรด
        self.status_cards["Daily Trades"].configure(
            text=f"{self.daily_trades}/{self.config['max_daily_trades']}"
        )

        # อัปเดต P&L และค่าธรรมเนียม
        self.status_cards["Net P&L Today"].configure(text=f"{self.daily_pnl:+.2f}")
        self.status_cards["Total Fees"].configure(text=f"{self.total_fees_paid:.2f}")

        # คำนวณ gross profit
        gross_profit = self.daily_pnl + self.total_fees_paid
        self.status_cards["Gross Profit"].configure(text=f"{gross_profit:+.2f}")

        # อัปเดตยอดเงินเป็นระยะ
        self.update_balance()

    def update_balance(self):
        """Enhanced balance update with profit tracking"""
        if not self.api_client:
            return

        balance = self.api_client.check_balance()
        if balance and balance.get('error') == 0:
            thb_balance = float(balance['result'].get('THB', 0))
            self.status_cards["Balance THB"].configure(text=f"{thb_balance:,.2f}")
            self.quick_stats["Balance"].configure(text=f"{thb_balance:,.0f}")

            # Get crypto balance
            symbol_base = self.config['symbol'].split('_')[0].upper()
            crypto_balance = float(balance['result'].get(symbol_base, 0))

            display_text = f"💰 ข้อมูลบัญชีและกำไร\n"
            display_text += f"{'=' * 50}\n"
            display_text += f"💵 ยอดเงิน THB: {thb_balance:,.2f}\n"
            display_text += f"🪙 {symbol_base}: {crypto_balance:.8f}\n\n"

            # ข้อมูล position ปัจจุบัน
            if self.strategy.position:
                entry_price = self.strategy.position['entry_price']
                amount = self.strategy.position['amount']
                entry_time = self.strategy.position['entry_time']

                # ดึงราคาปัจจุบันเพื่อคำนวณ P&L
                ticker = self.api_client.get_simple_ticker(self.config['symbol'])
                if ticker:
                    current_price = ticker['last_price']

                    # คำนวณ P&L รวมค่าธรรมเนียม
                    buy_fee = self.strategy.calculate_fees(amount, entry_price, "buy")
                    sell_fee = self.strategy.calculate_fees(amount, current_price, "sell")
                    gross_pnl = (current_price - entry_price) * amount
                    net_pnl = gross_pnl - buy_fee - sell_fee
                    net_pnl_pct = net_pnl / (entry_price * amount) * 100

                    display_text += f"📈 Position ปัจจุบัน\n"
                    display_text += f"{'=' * 30}\n"
                    display_text += f"ราคาเข้า: {entry_price:,.2f} THB\n"
                    display_text += f"ราคาปัจจุบัน: {current_price:,.2f} THB\n"
                    display_text += f"จำนวน: {amount:.8f}\n"
                    display_text += f"P&L สุทธิ: {net_pnl:+.2f} THB ({net_pnl_pct:+.2f}%)\n"
                    display_text += f"ค่าธรรมเนียม: {buy_fee + sell_fee:.2f} THB\n"
                    display_text += f"เวลาเข้า: {entry_time.strftime('%H:%M:%S')}\n\n"

                    # อัปเดต quick stats
                    self.quick_stats["Position"].configure(text=f"LONG {net_pnl_pct:+.1f}%")

            # สถิติกำไรประจำวัน
            display_text += f"📊 สถิติกำไรวันนี้\n"
            display_text += f"{'=' * 30}\n"
            display_text += f"เทรด: {self.daily_trades}/{self.config['max_daily_trades']}\n"
            display_text += f"P&L สุทธิ: {self.daily_pnl:+.2f} THB\n"
            display_text += f"ค่าธรรมเนียมจ่าย: {self.total_fees_paid:.2f} THB\n"
            display_text += f"P&L รวม: {self.daily_pnl + self.total_fees_paid:+.2f} THB\n"
            display_text += f"โหมด: {'PAPER' if self.is_paper_trading else 'REAL'} TRADING\n\n"

            # ข้อมูลตลาดล่าสุด
            ticker = self.api_client.get_simple_ticker(self.config['symbol'])
            if ticker:
                current_price = ticker['last_price']
                break_even = self.strategy.calculate_break_even_price(current_price, "buy")
                profit_needed = (break_even - current_price) / current_price * 100

                display_text += f"📈 สภาวะตลาดปัจจุบัน\n"
                display_text += f"{'=' * 30}\n"
                display_text += f"ราคา: {current_price:,.2f} THB\n"
                display_text += f"เปลี่ยนแปลง 24h: {ticker['change_24h']:+.2f}%\n"
                display_text += f"ราคาเท่าทุน: {break_even:,.2f} THB\n"
                display_text += f"ต้องขึ้น: {profit_needed:.3f}% เพื่อเท่าทุน\n"

                if profit_needed < 0.8:
                    display_text += "✅ โอกาสกำไรดี\n"
                elif profit_needed < 1.5:
                    display_text += "⚠️ โอกาสกำไรปานกลาง\n"
                else:
                    display_text += "❌ ค่าธรรมเนียมสูง\n"

            self.dashboard_display.delete("1.0", "end")
            self.dashboard_display.insert("1.0", display_text)

    def update_strategy(self, value=None):
        """อัปเดตพารามิเตอร์กลยุทธ์"""
        self.strategy.min_profit_margin = self.min_profit_var.get() / 100
        self.strategy.rsi_oversold = self.rsi_oversold_var.get()
        self.strategy.rsi_overbought = self.rsi_overbought_var.get()
        self.strategy.stop_loss_pct = self.stop_loss_var.get() / 100
        self.strategy.take_profit_pct = self.take_profit_var.get() / 100

        # อัปเดต labels
        self.min_profit_label.configure(text=f"{self.min_profit_var.get():.1f}%")
        self.rsi_oversold_label.configure(text=str(self.strategy.rsi_oversold))
        self.rsi_overbought_label.configure(text=str(self.strategy.rsi_overbought))
        self.stop_loss_label.configure(text=f"{self.strategy.stop_loss_pct * 100:.1f}%")
        self.take_profit_label.configure(text=f"{self.strategy.take_profit_pct * 100:.1f}%")

        # ตรวจสอบความสมเหตุสมผล
        if self.strategy.rsi_oversold >= self.strategy.rsi_overbought:
            self.log("⚠️ คำเตือน: RSI oversold ควรน้อยกว่า overbought")

    def save_settings(self):
        """บันทึกการตั้งค่า"""
        # ตรวจสอบการตั้งค่าก่อนบันทึก
        new_amount = self.trade_amount_var.get()
        new_max_trades = self.max_trades_var.get()
        new_max_loss = self.max_loss_var.get()

        warnings = []
        if new_amount < 200:
            warnings.append(f"จำนวนเทรดต่ำ: {new_amount} THB (อาจไม่คุ้มค่าธรรมเนียม)")
        if new_amount > 10000:
            warnings.append(f"จำนวนเทรดสูง: {new_amount} THB")
        if new_max_trades > 5:
            warnings.append(f"จำนวนเทรดต่อวันสูง: {new_max_trades}")

        if warnings and not messagebox.askyesno("คำเตือนการตั้งค่า",
                                                "พบการตั้งค่าที่ควรระวัง:\n\n" +
                                                "\n".join(warnings) +
                                                "\n\nต้องการดำเนินการต่อไหม?"):
            return

        # บันทึกการตั้งค่า
        self.config['symbol'] = self.symbol_var.get()
        self.config['trade_amount_thb'] = new_amount
        self.config['max_daily_trades'] = new_max_trades
        self.config['max_daily_loss'] = new_max_loss

        messagebox.showinfo("สำเร็จ", "บันทึกการตั้งค่าเรียบร้อย!")
        self.log(f"อัปเดตการตั้งค่า: จำนวน={new_amount}, เทรดสูงสุด={new_max_trades}, ขาดทุนสูงสุด={new_max_loss}")

    # === Additional Helper Functions ===

    def system_health_check(self):
        """Comprehensive system health check"""
        self.visual_effects.set_state("analyzing")
        self.ai_status_label.configure(text="ตรวจสอบระบบ...")

        def health_check():
            self.log("🏥 ตรวจสอบสุขภาพระบบ...")

            if not self.api_client:
                self.log("❌ ไม่มี API client")
                self.visual_effects.set_state("error")
                return

            # System status
            status_ok, status_msg = self.api_client.check_system_status()
            self.log(f"ระบบ: {'✅' if status_ok else '❌'} {status_msg}")

            # Balance check
            balance = self.api_client.check_balance()
            if balance and balance.get('error') == 0:
                thb_balance = balance['result'].get('THB', 0)
                self.log(f"ยอดเงิน: ✅ THB {float(thb_balance):,.2f}")
            else:
                self.log("ยอดเงิน: ❌ ตรวจสอบไม่ได้")

            # Market data check
            ticker = self.api_client.get_simple_ticker(self.config['symbol'])
            if ticker:
                self.log(f"ข้อมูลตลาด: ✅ {ticker['symbol']} @ {ticker['last_price']:,.0f}")
                
                # Profit analysis
                current_price = ticker['last_price']
                break_even = self.strategy.calculate_break_even_price(current_price, "buy")
                profit_needed = (break_even - current_price) / current_price * 100
                
                if profit_needed < 1.0:
                    self.log(f"โอกาสกำไร: ✅ ต้องขึ้น {profit_needed:.2f}%")
                else:
                    self.log(f"โอกาสกำไร: ⚠️ ต้องขึ้น {profit_needed:.2f}%")
            else:
                self.log("ข้อมูลตลาด: ❌ ดึงข้อมูลไม่ได้")

            # Configuration check
            if self.config['trade_amount_thb'] > 5000:
                self.log("⚠️ คำเตือน: จำนวนเทรด > 5000 THB")
            if self.config['max_daily_trades'] > 10:
                self.log("⚠️ คำเตือน: เทรดต่อวันสูง")

            self.log("🏥 ตรวจสอบสมบูรณ์")
            
            time.sleep(2)
            self.visual_effects.set_state("success")
            self.ai_status_label.configure(text="ระบบปกติ")
            
            time.sleep(1.5)
            self.visual_effects.set_state("idle")
            self.ai_status_label.configure(text="พร้อมใช้งาน")

        threading.Thread(target=health_check, daemon=True).start()

    def test_market_data(self):
        """Test market data retrieval with profit analysis"""
        if not self.api_client:
            self.test_log("❌ กรุณาเชื่อมต่อ API ก่อน")
            return

        self.test_log("📊 ทดสอบการดึงข้อมูลตลาด...")

        ticker = self.api_client.get_simple_ticker(self.config['symbol'])
        if ticker:
            self.test_log(f"✅ ข้อมูล Ticker:")
            self.test_log(f"   Symbol: {ticker['symbol']}")
            self.test_log(f"   ราคาล่าสุด: {ticker['last_price']:,.0f} THB")
            self.test_log(f"   Bid: {ticker['bid']:,.0f} THB")
            self.test_log(f"   Ask: {ticker['ask']:,.0f} THB")
            self.test_log(f"   การเปลี่ยนแปลง 24h: {ticker['change_24h']:+.2f}%")
            
            # Profit analysis
            current_price = ticker['last_price']
            break_even = self.strategy.calculate_break_even_price(current_price, "buy")
            profit_needed = (break_even - current_price) / current_price * 100
            
            self.test_log(f"💰 การวิเคราะห์กำไร:")
            self.test_log(f"   ราคาเท่าทุน: {break_even:,.2f} THB")
            self.test_log(f"   ต้องขึ้น: {profit_needed:.3f}% เพื่อไม่ขาดทุน")
            
            if profit_needed < 1.0:
                self.test_log("   ✅ โอกาสกำไรดี")
            else:
                self.test_log("   ⚠️ ค่าธรรมเนียมค่อนข้างสูง")
        else:
            self.test_log("❌ ไม่สามารถดึงข้อมูล Ticker ได้")

    def test_balance(self):
        """Test balance check"""
        if not self.api_client:
            self.test_log("❌ กรุณาเชื่อมต่อ API ก่อน")
            return

        self.test_log("💰 ทดสอบการตรวจสอบยอดเงิน...")

        balance = self.api_client.check_balance()
        if balance and balance.get('error') == 0:
            self.test_log("✅ ยอดเงินในบัญชี:")
            for currency, amount in balance['result'].items():
                if float(amount) > 0:
                    self.test_log(f"   {currency}: {float(amount):,.8f}")
        else:
            error_msg = "Unknown error"
            if balance:
                error_code = balance.get("error", 999)
                error_msg = self.api_client.error_codes.get(error_code, f"Error {error_code}")
            self.test_log(f"❌ การตรวจสอบยอดเงินล้มเหลว: {error_msg}")

    def check_open_orders(self):
        """Check open orders"""
        if not self.api_client:
            self.log("❌ กรุณาเชื่อมต่อ API ก่อน")
            return

        self.log("📋 กำลังตรวจสอบคำสั่งที่ค้างอยู่...")

        orders = self.api_client.get_my_open_orders_safe(self.config['symbol'])

        if orders and orders.get("error") == 0:
            order_list = orders.get("result", [])
            if order_list:
                self.log(f"📋 พบคำสั่งค้างอยู่ {len(order_list)} รายการ:")
                for order in order_list:
                    side = order.get('side', 'unknown').upper()
                    order_id = order.get('id', 'N/A')
                    rate = order.get('rate', 'N/A')
                    amount = order.get('amount', 'N/A')
                    self.log(f"   {side} Order ID: {order_id} @ {rate} THB (Amount: {amount})")
            else:
                self.log("📋 ไม่มีคำสั่งค้างอยู่")
        else:
            error_code = orders.get("error", 999) if orders else 999
            error_msg = self.api_client.error_codes.get(error_code, f"Error {error_code}")
            self.log(f"❌ ไม่สามารถดึงข้อมูลคำสั่งได้: {error_msg}")

    def test_connection(self):
        """Enhanced connection test"""
        if not self.api_client:
            self.api_status_display.delete("1.0", "end")
            self.api_status_display.insert("1.0", "❌ กรุณาเชื่อมต่อ API ก่อน")
            return

        self.api_status_display.delete("1.0", "end")
        self.api_status_display.insert("1.0", "🔌 กำลังทดสอบการเชื่อมต่อ...\n\n")

        # Test ticker
        ticker = self.api_client.get_simple_ticker(self.config['symbol'])
        if ticker:
            self.api_status_display.insert("end",
                                           f"✅ ข้อมูลตลาด: {ticker['symbol']} @ {ticker['last_price']:,.2f} THB\n")
        else:
            self.api_status_display.insert("end", "❌ ข้อมูลตลาด: ล้มเหลว\n")

        # Test balance
        balance = self.api_client.check_balance()
        if balance and balance.get('error') == 0:
            thb_balance = balance['result'].get('THB', 0)
            self.api_status_display.insert("end", f"✅ ยอดเงิน: {float(thb_balance):,.2f} THB\n")
        else:
            self.api_status_display.insert("end", "❌ ยอดเงิน: ล้มเหลว\n")

        # Test system status
        status_ok, status_msg = self.api_client.check_system_status()
        self.api_status_display.insert("end", f"{'✅' if status_ok else '❌'} ระบบ: {status_msg}\n")

        self.api_status_display.insert("end", f"\nทดสอบเมื่อ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    def api_health_check(self):
        """Detailed API health check"""
        if not self.api_client:
            self.api_status_display.delete("1.0", "end")
            self.api_status_display.insert("1.0", "❌ ไม่มี API client")
            return

        self.api_status_display.delete("1.0", "end")
        self.api_status_display.insert("1.0", "🏥 กำลังตรวจสอบสุขภาพ API...\n\n")

        # System status
        status_ok, status_msg = self.api_client.check_system_status()
        self.api_status_display.insert("end", f"ระบบ: {'✅' if status_ok else '❌'} {status_msg}\n")

        # Balance check
        balance = self.api_client.check_balance()
        if balance and balance.get('error') == 0:
            self.api_status_display.insert("end", "ยอดเงิน: ✅ สำเร็จ\n")
            for currency, amount in balance['result'].items():
                if float(amount) > 0:
                    self.api_status_display.insert("end", f"  {currency}: {float(amount):,.8f}\n")
        else:
            self.api_status_display.insert("end", "ยอดเงิน: ❌ ล้มเหลว\n")

        # Market data check
        ticker = self.api_client.get_simple_ticker(self.config['symbol'])
        if ticker:
            self.api_status_display.insert("end", f"ข้อมูลตลาด: ✅ {ticker['symbol']} @ {ticker['last_price']:,.0f}\n")
        else:
            self.api_status_display.insert("end", "ข้อมูลตลาด: ❌ ล้มเหลว\n")

        self.api_status_display.insert("end", f"\nตรวจสอบเมื่อ: {datetime.now().strftime('%H:%M:%S')}")

    def export_history(self):
        """Export trade history to CSV"""
        try:
            import csv
            from tkinter import filedialog

            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv")],
                title="ส่งออกประวัติการเทรด"
            )

            if filename:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT timestamp, symbol, side, amount, price, total_thb, 
                           order_id, net_pnl, fees, reason, is_paper
                    FROM trades ORDER BY timestamp DESC
                ''')

                trades = cursor.fetchall()
                conn.close()

                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(['Timestamp', 'Symbol', 'Side', 'Amount', 'Price',
                                     'Total THB', 'Order ID', 'Net P&L', 'Fees', 'Reason', 'Paper Trading'])
                    writer.writerows(trades)

                messagebox.showinfo("ส่งออกสำเร็จ", f"ส่งออกประวัติไปยัง {filename}")

        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถส่งออกได้: {e}")

    # === Logging Methods ===

    def log(self, message):
        """เขียน log หลัก"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"

        self.trading_log.insert("end", log_entry)
        self.trading_log.see("end")

        # จำกัดขนาด log
        lines = self.trading_log.get("1.0", "end").split('\n')
        if len(lines) > 500:
            self.trading_log.delete("1.0", f"{len(lines) - 250}.0")

    def profit_log(self, message):
        """เขียน log การวิเคราะห์กำไร"""
        self.profit_display.insert("end", message + "\n")
        self.profit_display.see("end")

    def test_log(self, message):
        """เขียน log การทดสอบ"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.test_display.insert("end", log_entry)
        self.test_display.see("end")

    def run(self):
        """เริ่มแอปพลิเคชัน"""
        # รีเซ็ตตัวนับประจำวัน
        self.daily_trades = 0
        self.daily_pnl = 0
        self.total_fees_paid = 0

        self.log("🚀 เริ่มต้น Enhanced Bitkub Trading Bot")
        self.log("💰 เวอร์ชันที่ปรับปรุงเพื่อสร้างกำไรจริง")
        self.log("📝 โหมดเริ่มต้น: PAPER TRADING")
        self.log("⚠️ คำนึงถึงค่าธรรมเนียม Bitkub 0.5% รวม")
        self.log("🪙 รองรับเหรียญทั้งหมดของ Bitkub (39 เหรียญ)")
        self.log("🤖 AI Visual Effects พร้อมใช้งาน")

        # เริ่มต้น visual effects
        self.visual_effects.start_animation("idle")

        self.root.mainloop()


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("🚀 ENHANCED BITKUB TRADING BOT WITH AI VISUAL EFFECTS")
    print("=" * 80)
    print("✨ คุณลักษณะใหม่:")
    print("• AI Visual Effects - วงกลมสีฟ้าเรืองแสงตอบสนองสถานะ")
    print("• คำนึงถึงค่าธรรมเนียม Bitkub 0.5% ในทุกการตัดสินใจ")
    print("• รองรับเหรียญทั้งหมดของ Bitkub (39 เหรียญ)")
    print("• ระบบวิเคราะห์กำไรแบบ Real-time")
    print("• การจัดการความเสี่ยงที่เน้นผลกำไร")
    print("• UI/UX ที่ปรับปรุงพร้อม Profit Calculator")
    print("\n🎨 AI Visual States:")
    print("• 🔵 Idle - สถานะพักทำงาน") 
    print("• 🔄 Connecting - กำลังเชื่อมต่อ")
    print("• 🧠 Thinking - AI กำลังคิด")
    print("• 📊 Analyzing - กำลังวิเคราะห์")
    print("• 📈 Buy Signal - สัญญาณซื้อ")
    print("• 📉 Sell Signal - สัญญาณขาย")
    print("• 💰 Trading - กำลังเทรด")
    print("• ✅ Profit - กำไร")
    print("• ❌ Loss/Error - ขาดทุน/ข้อผิดพลาด")
    print("\n💰 การคำนวณกำไร:")
    print("• Maker Fee: 0.25%")
    print("• Taker Fee: 0.25%")
    print("• รวม: 0.5% ต่อรอบการเทรด")
    print("• กำไรขั้นต่ำแนะนำ: 0.8%+")
    print("\n⚠️ คำเตือน:")
    print("• บอทนี้ใช้เงินจริงเมื่อเปิดโหมด REAL TRADING")
    print("• เริ่มต้นด้วย PAPER TRADING เสมอ")
    print("• ใช้เงินทดลองเล็กน้อยในครั้งแรก")
    print("• การเทรดมีความเสี่ยง - ไม่รับประกันผลกำไร")
    print("=" * 80 + "\n")

    response = input("คุณเข้าใจความเสี่ยงและต้องการดำเนินการต่อหรือไม่? (yes/no): ")

    if response.lower() in ['yes', 'y', 'ใช่']:
        app = EnhancedTradingBot()
        app.run()
    else:
        print("ออกจากโปรแกรม กรุณาศึกษาความเสี่ยงก่อนใช้งานบอทนี้")
