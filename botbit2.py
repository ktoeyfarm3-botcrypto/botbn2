import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import hashlib
import hmac
import json
import time
import requests
import threading
from datetime import datetime, timedelta
import numpy as np
from collections import deque
import logging
import os
from urllib.parse import urlencode
import configparser

# ตรวจสอบ matplotlib
try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.animation import FuncAnimation
    import matplotlib.dates as mdates
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("📊 Matplotlib ไม่พบ - จะปิดการใช้งานกราฟ")

class BitkubAPIClient:
    """คลาสสำหรับเชื่อมต่อ Bitkub API ที่ปรับปรุงแล้ว"""
    
    def __init__(self, api_key="", api_secret=""):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://api.bitkub.com"
        
        # Rate limiting
        self.request_times = deque(maxlen=250)
        self.rate_limit_lock = threading.Lock()
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
    def _wait_for_rate_limit(self):
        """ตรวจสอบ Rate Limit"""
        with self.rate_limit_lock:
            now = time.time()
            
            # ลบ request ที่เก่ากว่า 10 วินาที
            while self.request_times and (now - self.request_times[0]) > 10:
                self.request_times.popleft()
            
            # ถ้าถึงขีดจำกัด ให้รอ
            if len(self.request_times) >= 250:
                sleep_time = 10 - (now - self.request_times[0]) + 0.1
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    self.request_times.clear()
            
            self.request_times.append(now)
    
    def _generate_signature(self, payload_string):
        """สร้าง HMAC Signature"""
        if not self.api_secret:
            raise ValueError("API Secret ไม่ได้ตั้งค่า")
        
        return hmac.new(
            self.api_secret.encode('utf-8'),
            payload_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _build_query_string(self, params):
        """สร้าง Query String ที่ถูกต้อง"""
        if not params:
            return ""
        
        filtered_params = {k: str(v) for k, v in params.items() if v is not None}
        return urlencode(filtered_params)
    
    def make_public_request(self, endpoint, params=None):
        """เรียก Public API"""
        try:
            self._wait_for_rate_limit()
            
            url = f"{self.base_url}{endpoint}"
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            self.logger.error(f"Public API Error: {e}")
            return None
    
    def make_private_request(self, method, endpoint, params=None, body=None):
        """เรียก Private API"""
        try:
            if not self.api_key or not self.api_secret:
                raise ValueError("API Credentials ไม่ได้ตั้งค่า")
            
            self._wait_for_rate_limit()
            
            ts = str(round(time.time() * 1000))
            url = f"{self.base_url}{endpoint}"
            payload_parts = [ts, method.upper(), endpoint]
            
            if method.upper() == 'GET' and params:
                query_string = self._build_query_string(params)
                if query_string:
                    payload_parts.append(f"?{query_string}")
                    url += f"?{query_string}"
            elif method.upper() == 'POST' and body:
                json_body = json.dumps(body, separators=(',', ':'))
                payload_parts.append(json_body)
            
            payload_string = ''.join(payload_parts)
            signature = self._generate_signature(payload_string)
            
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'X-BTK-TIMESTAMP': ts,
                'X-BTK-SIGN': signature,
                'X-BTK-APIKEY': self.api_key
            }
            
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            else:
                response = requests.post(url, headers=headers, json=body or {}, timeout=10)
            
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            self.logger.error(f"Private API Error: {e}")
            return None

class TradingStrategy:
    """คลาสกลยุทธ์การเทรด"""
    
    @staticmethod
    def momentum_strategy(prices, current_price, period=10):
        """กลยุทธ์ Momentum ที่ปรับปรุงแล้ว"""
        if len(prices) < period:
            return {'action': 'hold', 'confidence': 0, 'reason': 'ข้อมูลไม่เพียงพอ'}
        
        short_ma = np.mean(prices[-5:])
        long_ma = np.mean(prices[-period:])
        
        # คำนวณ RSI เพื่อช่วยตัดสินใจ
        rsi = TradingStrategy.calculate_rsi(prices)
        
        momentum_ratio = (short_ma - long_ma) / long_ma
        
        if momentum_ratio > 0.002 and rsi < 70:  # ป้องกันการซื้อเมื่อ overbought
            confidence = min(0.8, abs(momentum_ratio) * 100)
            return {
                'action': 'buy', 
                'confidence': confidence,
                'reason': f'Momentum เพิ่มขึ้น: {momentum_ratio:.4f}, RSI: {rsi:.1f}'
            }
        elif momentum_ratio < -0.002 and rsi > 30:  # ป้องกันการขายเมื่อ oversold
            confidence = min(0.8, abs(momentum_ratio) * 100)
            return {
                'action': 'sell', 
                'confidence': confidence,
                'reason': f'Momentum ลดลง: {momentum_ratio:.4f}, RSI: {rsi:.1f}'
            }
        
        return {
            'action': 'hold', 
            'confidence': 0.3,
            'reason': f'Momentum กลาง ๆ: {momentum_ratio:.4f}, RSI: {rsi:.1f}'
        }
    
    @staticmethod
    def calculate_rsi(prices, period=14):
        """คำนวณ RSI"""
        if len(prices) < period + 1:
            return 50  # ค่ากลางถ้าข้อมูลไม่พอ
        
        prices_array = np.array(prices)
        deltas = np.diff(prices_array)
        
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    @staticmethod
    def bollinger_bands_strategy(prices, current_price, period=20, std_mult=2):
        """กลยุทธ์ Bollinger Bands"""
        if len(prices) < period:
            return {'action': 'hold', 'confidence': 0, 'reason': 'ข้อมูลไม่เพียงพอ'}
        
        prices_array = np.array(prices[-period:])
        middle = np.mean(prices_array)
        std = np.std(prices_array)
        
        upper_band = middle + (std_mult * std)
        lower_band = middle - (std_mult * std)
        
        if current_price <= lower_band:
            return {
                'action': 'buy',
                'confidence': 0.8,
                'reason': f'ราคาต่ำกว่า Lower Band: {current_price:.2f} <= {lower_band:.2f}'
            }
        elif current_price >= upper_band:
            return {
                'action': 'sell',
                'confidence': 0.8,
                'reason': f'ราคาสูงกว่า Upper Band: {current_price:.2f} >= {upper_band:.2f}'
            }
        
        return {
            'action': 'hold',
            'confidence': 0.2,
            'reason': f'ราคาอยู่ในแถบ: {lower_band:.2f} < {current_price:.2f} < {upper_band:.2f}'
        }

class BitkubTradingBot:
    def __init__(self, root):
        self.root = root
        self.root.title("🚀 Bitkub AI Trading Bot - Professional Edition")
        self.root.geometry("1400x900")
        self.root.configure(bg='#1a1a1a')
        
        # Setup logging
        self.setup_logging()
        
        # API Client
        self.api_client = None
        
        # Trading state
        self.ai_enabled = False
        self.price_history = deque(maxlen=200)  # เพิ่มขนาด buffer
        self.stop_trading = False
        self.total_trades = 0
        self.successful_trades = 0
        self.failed_trades = 0
        self.total_profit_loss = 0.0
        
        # Chart variables
        self.fig = None
        self.ax = None
        self.canvas = None
        self.animation = None
        
        # Configuration
        self.config = configparser.ConfigParser()
        self.config_file = 'bot_config.ini'
        self.load_configuration()
        
        # ตั้งค่า Style และสร้าง GUI
        self.setup_styles()
        self.create_widgets()
        
        # เริ่มต้นการติดตามราคา
        self.start_price_monitoring()
        
        # โหลดการตั้งค่าที่บันทึกไว้
        self.load_saved_settings()
        
    def setup_logging(self):
        """ตั้งค่า Logging"""
        # สร้างโฟลเดอร์ logs ถ้าไม่มี
        if not os.path.exists('logs'):
            os.makedirs('logs')
            
        log_filename = f"logs/trading_bot_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_filename, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('BitkubBot')
    
    def load_configuration(self):
        """โหลดการตั้งค่าจากไฟล์"""
        if os.path.exists(self.config_file):
            self.config.read(self.config_file, encoding='utf-8')
    
    def save_configuration(self):
        """บันทึกการตั้งค่าลงไฟล์"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            self.config.write(f)
    
    def setup_styles(self):
        """ตั้งค่า Style ที่ปรับปรุงแล้ว"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # สีที่ปรับปรุงแล้ว
        bg_dark = '#1a1a1a'
        bg_medium = '#2d2d2d'
        bg_light = '#404040'
        fg_color = '#ffffff'
        accent_color = '#00d4aa'
        error_color = '#ff6b6b'
        success_color = '#51cf66'
        
        # กำหนด style ต่าง ๆ
        style.configure('Dark.TFrame', background=bg_dark)
        style.configure('Dark.TLabel', background=bg_dark, foreground=fg_color)
        style.configure('Dark.TLabelFrame', background=bg_dark, foreground=fg_color)
        style.configure('Dark.TButton', background=bg_light, foreground=fg_color)
        style.configure('Dark.TEntry', fieldbackground=bg_light, foreground=fg_color)
        style.configure('Dark.TCombobox', fieldbackground=bg_light, foreground=fg_color)
        
        # Style พิเศษ
        style.configure('Title.TLabel', background=bg_dark, foreground=accent_color, 
                       font=('Segoe UI', 16, 'bold'))
        style.configure('Header.TLabel', background=bg_dark, foreground=fg_color, 
                       font=('Segoe UI', 12, 'bold'))
        style.configure('Success.TLabel', background=bg_dark, foreground=success_color, 
                       font=('Segoe UI', 11, 'bold'))
        style.configure('Error.TLabel', background=bg_dark, foreground=error_color, 
                       font=('Segoe UI', 11, 'bold'))
        
    def create_widgets(self):
        """สร้าง GUI ที่ปรับปรุงแล้ว"""
        
        # Main container
        main_frame = ttk.Frame(self.root, style='Dark.TFrame')
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Header ที่ปรับปรุงแล้ว
        self.create_enhanced_header(main_frame)
        
        # Notebook
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill='both', expand=True, pady=(10, 0))
        
        # สร้างแท็บต่าง ๆ
        self.create_dashboard_tab(notebook)
        self.create_api_config_tab(notebook)
        self.create_ai_trading_tab(notebook)
        self.create_manual_trading_tab(notebook)
        self.create_portfolio_tab(notebook)
        self.create_market_data_tab(notebook)
        self.create_settings_tab(notebook)
        
        # Status bar ที่ปรับปรุงแล้ว
        self.create_enhanced_status_bar(main_frame)
        
    def create_enhanced_header(self, parent):
        """สร้าง Header ที่ปรับปรุงแล้ว"""
        header_frame = ttk.Frame(parent, style='Dark.TFrame')
        header_frame.pack(fill='x', pady=(0, 10))
        
        # ส่วนซ้าย - Logo และ Title
        left_frame = ttk.Frame(header_frame, style='Dark.TFrame')
        left_frame.pack(side='left')
        
        ttk.Label(left_frame, text="🚀 Bitkub AI Trading Bot", 
                 style='Title.TLabel').pack(side='left')
        
        version_label = ttk.Label(left_frame, text="v2.0 Pro", 
                                 style='Dark.TLabel', font=('Segoe UI', 8))
        version_label.pack(side='left', padx=(10, 0))
        
        # ส่วนกลาง - สถิติด่วน
        center_frame = ttk.Frame(header_frame, style='Dark.TFrame')
        center_frame.pack(side='left', expand=True, padx=50)
        
        stats_container = ttk.Frame(center_frame, style='Dark.TFrame')
        stats_container.pack()
        
        self.header_stats = {}
        quick_stats = [
            ("การเชื่อมต่อ", "🔴 ไม่ได้เชื่อมต่อ"),
            ("AI Trading", "🔴 ปิด"),
            ("จำนวนเทรด", "0"),
            ("กำไร/ขาดทุน", "0.00%")
        ]
        
        for i, (label, value) in enumerate(quick_stats):
            stat_frame = ttk.Frame(stats_container, style='Dark.TFrame')
            stat_frame.grid(row=0, column=i, padx=10)
            
            ttk.Label(stat_frame, text=label, style='Dark.TLabel', 
                     font=('Segoe UI', 9)).pack()
            self.header_stats[label] = ttk.Label(stat_frame, text=value, 
                                               style='Header.TLabel', font=('Segoe UI', 10, 'bold'))
            self.header_stats[label].pack()
        
        # ส่วนขวา - ปุ่มควบคุมด่วน
        right_frame = ttk.Frame(header_frame, style='Dark.TFrame')
        right_frame.pack(side='right')
        
        self.quick_start_btn = ttk.Button(right_frame, text="🚀 เริ่ม AI",
                                         command=self.quick_start_ai, style='Dark.TButton')
        self.quick_start_btn.pack(side='right', padx=5)
        
        ttk.Button(right_frame, text="⚙️ ตั้งค่าด่วน",
                  command=self.quick_settings, style='Dark.TButton').pack(side='right', padx=5)
        
    def create_dashboard_tab(self, notebook):
        """แท็บ Dashboard ที่ปรับปรุงแล้ว"""
        frame = ttk.Frame(notebook, style='Dark.TFrame')
        notebook.add(frame, text="📊 Dashboard")
        
        # สถิติการเทรด
        stats_frame = ttk.LabelFrame(frame, text="📈 สถิติการเทรด", style='Dark.LabelFrame')
        stats_frame.pack(fill='x', padx=10, pady=10)
        
        stats_container = ttk.Frame(stats_frame, style='Dark.TFrame')
        stats_container.pack(fill='x', padx=10, pady=10)
        
        self.stats_cards = {}
        detailed_stats = [
            ("💰 ยอดเงิน (THB)", "0.00", "Success.TLabel"),
            ("📈 กำไร/ขาดทุน", "0.00%", "Dark.TLabel"),
            ("🎯 อัตราความสำเร็จ", "0%", "Dark.TLabel"),
            ("📊 จำนวนเทรดสำเร็จ", "0", "Success.TLabel"),
            ("❌ จำนวนเทรดล้มเหลว", "0", "Error.TLabel"),
            ("⏱️ เวลาเทรดล่าสุด", "ยังไม่มี", "Dark.TLabel")
        ]
        
        for i, (label, value, style) in enumerate(detailed_stats):
            row, col = i // 3, i % 3
            card_frame = ttk.Frame(stats_container, style='Dark.TFrame')
            card_frame.grid(row=row, column=col, padx=10, pady=5, sticky='ew')
            
            ttk.Label(card_frame, text=label, style='Header.TLabel').pack()
            self.stats_cards[label] = ttk.Label(card_frame, text=value, style=style)
            self.stats_cards[label].pack()
        
        # กำหนดให้ columns ขยายได้เท่า ๆ กัน
        for i in range(3):
            stats_container.grid_columnconfigure(i, weight=1)
        
        # กราฟราคา (ถ้ามี matplotlib)
        if MATPLOTLIB_AVAILABLE:
            self.create_price_chart(frame)
        
        # การกระทำด่วน
        self.create_quick_actions(frame)
        
    def create_price_chart(self, parent):
        """สร้างกราฟราคา"""
        chart_frame = ttk.LabelFrame(parent, text="📈 กราฟราคา", style='Dark.LabelFrame')
        chart_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # สร้าง matplotlib figure
        self.fig, self.ax = plt.subplots(figsize=(12, 4), facecolor='#1a1a1a')
        self.ax.set_facecolor('#1a1a1a')
        
        # ตั้งค่าสีของแกน
        self.ax.tick_params(colors='white')
        self.ax.spines['bottom'].set_color('white')
        self.ax.spines['top'].set_color('white')
        self.ax.spines['right'].set_color('white')
        self.ax.spines['left'].set_color('white')
        self.ax.set_title('BTC/THB Price Movement', color='white', fontsize=14)
        self.ax.set_ylabel('Price (THB)', color='white')
        
        # สร้าง canvas
        self.canvas = FigureCanvasTkAgg(self.fig, chart_frame)
        self.canvas.get_tk_widget().pack(fill='both', expand=True, padx=10, pady=10)
        
        # เริ่ม animation
        self.start_chart_animation()
    
    def start_chart_animation(self):
        """เริ่ม animation สำหรับกราฟ"""
        def update_chart(frame):
            if len(self.price_history) > 1:
                self.ax.clear()
                
                # ตั้งค่าสีและ style ใหม่
                self.ax.set_facecolor('#1a1a1a')
                self.ax.tick_params(colors='white')
                for spine in self.ax.spines.values():
                    spine.set_color('white')
                
                # พล็อตข้อมูล
                prices = list(self.price_history)
                times = range(len(prices))
                
                self.ax.plot(times, prices, color='#00d4aa', linewidth=2, alpha=0.8)
                
                # เพิ่ม moving average
                if len(prices) >= 20:
                    ma20 = [np.mean(prices[max(0, i-19):i+1]) for i in range(len(prices))]
                    self.ax.plot(times, ma20, color='#ff6b6b', linewidth=1, alpha=0.7, label='MA20')
                
                self.ax.set_title('BTC/THB Price Movement', color='white')
                self.ax.set_ylabel('Price (THB)', color='white')
                
                if len(prices) >= 2:
                    self.ax.legend(facecolor='#2d2d2d', edgecolor='white', labelcolor='white')
                
                # จำกัดจำนวนจุดที่แสดง
                if len(times) > 100:
                    self.ax.set_xlim(len(times) - 100, len(times))
            
            return []
        
        # เริ่ม animation (อัพเดททุก 5 วินาที)
        self.animation = FuncAnimation(self.fig, update_chart, interval=5000, blit=False)
    
    def create_quick_actions(self, parent):
        """สร้างส่วนการกระทำด่วน"""
        actions_frame = ttk.LabelFrame(parent, text="⚡ การกระทำด่วน", style='Dark.LabelFrame')
        actions_frame.pack(fill='x', padx=10, pady=10)
        
        button_container = ttk.Frame(actions_frame, style='Dark.TFrame')
        button_container.pack(padx=10, pady=10)
        
        # ปุ่มต่าง ๆ
        buttons = [
            ("🔄 รีเฟรชข้อมูล", self.refresh_dashboard, "รีเฟรชข้อมูลทั้งหมด"),
            ("💰 ตรวจสอบยอดเงิน", self.quick_balance_check, "ตรวจสอบยอดเงินปัจจุบัน"),
            ("📊 ดูสถิติ", self.show_detailed_stats, "แสดงสถิติโดยละเอียด"),
            ("💾 บันทึกการตั้งค่า", self.save_all_settings, "บันทึกการตั้งค่าทั้งหมด"),
            ("📤 ส่งออกข้อมูล", self.export_data, "ส่งออกข้อมูลการเทรด"),
        ]
        
        for i, (text, command, tooltip) in enumerate(buttons):
            btn = ttk.Button(button_container, text=text, command=command, style='Dark.TButton')
            btn.pack(side='left', padx=5)
            
            # เพิ่ม tooltip (อาจต้องติดตั้ง library เพิ่มเติม)
            self.create_tooltip(btn, tooltip)
    
    def create_tooltip(self, widget, text):
        """สร้าง tooltip แบบง่าย ๆ"""
        def on_enter(event):
            widget.configure(text=f"{widget['text']} - {text}")
        
        def on_leave(event):
            original_text = widget['text'].split(' - ')[0]
            widget.configure(text=original_text)
        
        # ใช้วิธีแสดง tooltip ใน status bar แทน
        def show_tooltip(event):
            if hasattr(self, 'status_var'):
                self.status_var.set(f"💡 {text}")
        
        def hide_tooltip(event):
            if hasattr(self, 'status_var'):
                self.status_var.set("🟢 พร้อมใช้งาน")
        
        widget.bind("<Enter>", show_tooltip)
        widget.bind("<Leave>", hide_tooltip)
    
    def create_api_config_tab(self, notebook):
        """แท็บ API Configuration ที่ปรับปรุงแล้ว"""
        frame = ttk.Frame(notebook, style='Dark.TFrame')
        notebook.add(frame, text="🔧 ตั้งค่า API")
        
        # การตั้งค่า API
        config_frame = ttk.LabelFrame(frame, text="🔐 การตั้งค่า API", style='Dark.LabelFrame')
        config_frame.pack(fill='x', padx=20, pady=20)
        
        config_container = ttk.Frame(config_frame, style='Dark.TFrame')
        config_container.pack(fill='x', padx=10, pady=10)
        
        # API Key
        ttk.Label(config_container, text="API Key:", style='Header.TLabel').grid(row=0, column=0, 
                                                                               sticky='w', padx=10, pady=10)
        self.api_key_entry = ttk.Entry(config_container, width=60, show="*", style='Dark.TEntry')
        self.api_key_entry.grid(row=0, column=1, padx=10, pady=10, sticky='ew')
        
        # API Secret
        ttk.Label(config_container, text="API Secret:", style='Header.TLabel').grid(row=1, column=0, 
                                                                                  sticky='w', padx=10, pady=10)
        self.api_secret_entry = ttk.Entry(config_container, width=60, show="*", style='Dark.TEntry')
        self.api_secret_entry.grid(row=1, column=1, padx=10, pady=10, sticky='ew')
        
        config_container.grid_columnconfigure(1, weight=1)
        
        # ปุ่มควบคุม
        button_frame = ttk.Frame(config_frame, style='Dark.TFrame')
        button_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Button(button_frame, text="💾 บันทึก", 
                  command=self.save_api_config, style='Dark.TButton').pack(side='left', padx=5)
        ttk.Button(button_frame, text="🔍 ทดสอบการเชื่อมต่อ", 
                  command=self.test_api_connection, style='Dark.TButton').pack(side='left', padx=5)
        ttk.Button(button_frame, text="📁 โหลดจากไฟล์", 
                  command=self.load_api_from_file, style='Dark.TButton').pack(side='left', padx=5)
        ttk.Button(button_frame, text="💾 บันทึกเป็นไฟล์", 
                  command=self.save_api_to_file, style='Dark.TButton').pack(side='left', padx=5)
        
        # สถานะการเชื่อมต่อ
        status_frame = ttk.LabelFrame(frame, text="🌐 สถานะการเชื่อมต่อ", style='Dark.LabelFrame')
        status_frame.pack(fill='x', padx=20, pady=20)
        
        self.connection_status = ttk.Label(status_frame, text="⚫ ไม่ได้เชื่อมต่อ", 
                                         style='Error.TLabel', font=('Segoe UI', 12, 'bold'))
        self.connection_status.pack(pady=10)
        
        # ข้อมูลการเชื่อมต่อ
        self.connection_info = ttk.Label(status_frame, text="", style='Dark.TLabel')
        self.connection_info.pack(pady=5)
        
        # Log
        log_frame = ttk.LabelFrame(frame, text="📝 Log การทำงาน", style='Dark.LabelFrame')
        log_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # สร้าง frame สำหรับ log และ scrollbar
        log_container = ttk.Frame(log_frame, style='Dark.TFrame')
        log_container.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.log_text = scrolledtext.ScrolledText(log_container, height=15, 
                                                bg='#1e1e1e', fg='#00d4aa', 
                                                font=('Consolas', 10),
                                                insertbackground='white')
        self.log_text.pack(fill='both', expand=True)
        
        # ปุ่มจัดการ log
        log_buttons = ttk.Frame(log_frame, style='Dark.TFrame')
        log_buttons.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(log_buttons, text="🗑️ ล้าง Log", 
                  command=self.clear_logs, style='Dark.TButton').pack(side='left', padx=5)
        ttk.Button(log_buttons, text="💾 บันทึก Log", 
                  command=self.save_logs, style='Dark.TButton').pack(side='left', padx=5)
        ttk.Button(log_buttons, text="📂 เปิดโฟลเดอร์ Log", 
                  command=self.open_log_folder, style='Dark.TButton').pack(side='left', padx=5)
    
    def create_ai_trading_tab(self, notebook):
        """แท็บ AI Trading ที่ปรับปรุงแล้ว"""
        frame = ttk.Frame(notebook, style='Dark.TFrame')
        notebook.add(frame, text="🤖 AI Trading")
        
        # การตั้งค่า AI
        ai_config_frame = ttk.LabelFrame(frame, text="🧠 การตั้งค่า AI Trading", style='Dark.LabelFrame')
        ai_config_frame.pack(fill='x', padx=20, pady=20)
        
        config_grid = ttk.Frame(ai_config_frame, style='Dark.TFrame')
        config_grid.pack(fill='x', padx=10, pady=10)
        
        # การตั้งค่าพื้นฐาน
        basic_settings = [
            ("Symbol:", "ai_symbol_var", ["btc_thb", "eth_thb", "ada_thb", "dot_thb", "xrp_thb"]),
            ("กลยุทธ์:", "ai_strategy_var", ["momentum", "bollinger_bands", "hybrid"]),
            ("ระดับความเสี่ยง:", "ai_risk_var", ["low", "medium", "high", "aggressive"])
        ]
        
        self.ai_vars = {}
        for i, (label, var_name, values) in enumerate(basic_settings):
            ttk.Label(config_grid, text=label, style='Header.TLabel').grid(row=i, column=0, 
                                                                         sticky='w', padx=5, pady=5)
            var = tk.StringVar(value=values[0])
            self.ai_vars[var_name] = var
            combo = ttk.Combobox(config_grid, textvariable=var, values=values, 
                               state='readonly', style='Dark.TCombobox')
            combo.grid(row=i, column=1, padx=5, pady=5, sticky='ew')
        
        # การตั้งค่าขั้นสูง
        advanced_settings = [
            ("จำนวนเงินต่อเทรด (THB):", "ai_amount_var", "1000"),
            ("จำนวนเทรดสูงสุดต่อชั่วโมง:", "ai_max_trades_var", "5"),
            ("Stop Loss (%):", "ai_stop_loss_var", "2.0"),
            ("Take Profit (%):", "ai_take_profit_var", "4.0")
        ]
        
        for i, (label, var_name, default) in enumerate(advanced_settings, len(basic_settings)):
            ttk.Label(config_grid, text=label, style='Header.TLabel').grid(row=i, column=0, 
                                                                         sticky='w', padx=5, pady=5)
            var = tk.StringVar(value=default)
            self.ai_vars[var_name] = var
            entry = ttk.Entry(config_grid, textvariable=var, style='Dark.TEntry')
            entry.grid(row=i, column=1, padx=5, pady=5, sticky='ew')
        
        config_grid.grid_columnconfigure(1, weight=1)
        
        # ปุ่มควบคุม AI
        ai_control_frame = ttk.Frame(ai_config_frame, style='Dark.TFrame')
        ai_control_frame.pack(fill='x', padx=10, pady=10)
        
        self.ai_start_button = ttk.Button(ai_control_frame, text="🚀 เริ่ม AI Trading", 
                                        command=self.toggle_ai_trading, style='Dark.TButton')
        self.ai_start_button.pack(side='left', padx=5)
        
        ttk.Button(ai_control_frame, text="⚙️ ปรับแต่งกลยุทธ์", 
                  command=self.customize_strategy, style='Dark.TButton').pack(side='left', padx=5)
        
        ttk.Button(ai_control_frame, text="📊 ทดสอบกลยุทธ์", 
                  command=self.backtest_strategy, style='Dark.TButton').pack(side='left', padx=5)
        
        # สถิติ AI
        ai_stats_frame = ttk.LabelFrame(frame, text="📊 สถิติ AI Trading", style='Dark.LabelFrame')
        ai_stats_frame.pack(fill='x', padx=20, pady=20)
        
        self.ai_stats_container = ttk.Frame(ai_stats_frame, style='Dark.TFrame')
        self.ai_stats_container.pack(fill='x', padx=10, pady=10)
        
        self.ai_stats = {}
        ai_stat_items = [
            ("🎯 อัตราความแม่นยำ", "0%"),
            ("💰 กำไรรวม", "0 THB"),
            ("📈 เทรดสำเร็จ", "0"),
            ("📉 เทรดล้มเหลว", "0"),
            ("⏱️ เวลาเทรดเฉลี่ย", "0 นาที"),
            ("🔄 สถานะปัจจุบัน", "ปิด")
        ]
        
        for i, (label, value) in enumerate(ai_stat_items):
            row, col = i // 3, i % 3
            stat_frame = ttk.Frame(self.ai_stats_container, style='Dark.TFrame')
            stat_frame.grid(row=row, column=col, padx=10, pady=5, sticky='ew')
            
            ttk.Label(stat_frame, text=label, style='Dark.TLabel').pack()
            self.ai_stats[label] = ttk.Label(stat_frame, text=value, style='Header.TLabel')
            self.ai_stats[label].pack()
        
        for i in range(3):
            self.ai_stats_container.grid_columnconfigure(i, weight=1)
        
        # AI Log
        ai_log_frame = ttk.LabelFrame(frame, text="🤖 AI Trading Log", style='Dark.LabelFrame')
        ai_log_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        self.ai_log = scrolledtext.ScrolledText(ai_log_frame, height=12, 
                                              bg='#1e1e1e', fg='#00d4aa', 
                                              font=('Consolas', 10),
                                              insertbackground='white')
        self.ai_log.pack(fill='both', expand=True, padx=10, pady=10)
        
    def create_manual_trading_tab(self, notebook):
        """แท็บ Manual Trading ที่ปรับปรุงแล้ว"""
        frame = ttk.Frame(notebook, style='Dark.TFrame')
        notebook.add(frame, text="💰 Manual Trading")
        
        # ส่วนบน - ข้อมูลตลาดสด
        market_info_frame = ttk.LabelFrame(frame, text="📊 ข้อมูลตลาดสด", style='Dark.LabelFrame')
        market_info_frame.pack(fill='x', padx=10, pady=10)
        
        self.create_live_market_info(market_info_frame)
        
        # ส่วนกลาง - ฟอร์มการซื้อขาย
        trading_container = ttk.Frame(frame, style='Dark.TFrame')
        trading_container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # ฟอร์มซื้อ
        buy_frame = ttk.LabelFrame(trading_container, text="🟢 คำสั่งซื้อ", style='Dark.LabelFrame')
        buy_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        self.create_enhanced_trading_form(buy_frame, "buy")
        
        # ฟอร์มขาย
        sell_frame = ttk.LabelFrame(trading_container, text="🔴 คำสั่งขาย", style='Dark.LabelFrame')
        sell_frame.pack(side='right', fill='both', expand=True, padx=(10, 0))
        
        self.create_enhanced_trading_form(sell_frame, "sell")
        
        # ส่วนล่าง - ผลลัพธ์และ Order Book
        bottom_container = ttk.Frame(frame, style='Dark.TFrame')
        bottom_container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # ผลลัพธ์การเทรด
        result_frame = ttk.LabelFrame(bottom_container, text="📊 ผลลัพธ์การเทรด", style='Dark.LabelFrame')
        result_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        self.trading_result = scrolledtext.ScrolledText(result_frame, height=10, 
                                                      bg='#1e1e1e', fg='#ffffff', 
                                                      font=('Consolas', 10),
                                                      insertbackground='white')
        self.trading_result.pack(fill='both', expand=True, padx=10, pady=10)
        
        # คำสั่งซื้อขายที่เปิด
        orders_frame = ttk.LabelFrame(bottom_container, text="📋 คำสั่งที่เปิด", style='Dark.LabelFrame')
        orders_frame.pack(side='right', fill='both', expand=True, padx=(10, 0))
        
        self.open_orders_text = scrolledtext.ScrolledText(orders_frame, height=10, 
                                                        bg='#1e1e1e', fg='#ffffff', 
                                                        font=('Consolas', 9),
                                                        insertbackground='white')
        self.open_orders_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        # ปุ่มรีเฟรชคำสั่งที่เปิด
        ttk.Button(orders_frame, text="🔄 รีเฟรชคำสั่ง", 
                  command=self.refresh_open_orders, style='Dark.TButton').pack(pady=5)
    
    def create_live_market_info(self, parent):
        """สร้างข้อมูลตลาดสด"""
        info_container = ttk.Frame(parent, style='Dark.TFrame')
        info_container.pack(fill='x', padx=10, pady=10)
        
        # Symbol selector
        symbol_frame = ttk.Frame(info_container, style='Dark.TFrame')
        symbol_frame.pack(side='left')
        
        ttk.Label(symbol_frame, text="Symbol:", style='Header.TLabel').pack(side='left')
        self.market_symbol_var = tk.StringVar(value="btc_thb")
        symbol_combo = ttk.Combobox(symbol_frame, textvariable=self.market_symbol_var, 
                                   values=["btc_thb", "eth_thb", "ada_thb", "dot_thb"], 
                                   state='readonly', style='Dark.TCombobox', width=15)
        symbol_combo.pack(side='left', padx=10)
        symbol_combo.bind('<<ComboboxSelected>>', self.on_symbol_change)
        
        # Market data display
        self.market_info_labels = {}
        market_data = [
            ("💰 ราคาปัจจุบัน", "0.00 THB"),
            ("📈 เปลี่ยนแปลง 24h", "0.00%"),
            ("📊 ปริมาณ 24h", "0.00"),
            ("🔄 อัพเดทล่าสุด", "ไม่มี")
        ]
        
        info_grid = ttk.Frame(info_container, style='Dark.TFrame')
        info_grid.pack(side='right', expand=True, fill='x', padx=20)
        
        for i, (label, value) in enumerate(market_data):
            info_frame = ttk.Frame(info_grid, style='Dark.TFrame')
            info_frame.grid(row=0, column=i, padx=10, sticky='ew')
            info_grid.grid_columnconfigure(i, weight=1)
            
            ttk.Label(info_frame, text=label, style='Dark.TLabel', font=('Segoe UI', 9)).pack()
            self.market_info_labels[label] = ttk.Label(info_frame, text=value, 
                                                     style='Header.TLabel', font=('Segoe UI', 10, 'bold'))
            self.market_info_labels[label].pack()
    
    def create_enhanced_trading_form(self, parent, side):
        """สร้างฟอร์มการเทรดที่ปรับปรุงแล้ว"""
        form_frame = ttk.Frame(parent, style='Dark.TFrame')
        form_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # การตั้งค่าฟอร์ม
        fields = [
            ("Symbol:", f"{side}_symbol_var", "btc_thb", "combo"),
            ("จำนวน:", f"{side}_amount_var", "", "entry"),
            ("ราคา:", f"{side}_rate_var", "", "entry"),
            ("ประเภท:", f"{side}_type_var", "limit", "combo")
        ]
        
        vars_dict = {}
        for i, (label, var_name, default, widget_type) in enumerate(fields):
            ttk.Label(form_frame, text=label, style='Header.TLabel').grid(row=i, column=0, 
                                                                        sticky='w', pady=5)
            
            var = tk.StringVar(value=default)
            vars_dict[var_name] = var
            
            if widget_type == "combo":
                if "symbol" in var_name:
                    values = ["btc_thb", "eth_thb", "ada_thb", "dot_thb"]
                else:  # type
                    values = ["limit", "market"]
                widget = ttk.Combobox(form_frame, textvariable=var, values=values, 
                                    state='readonly', style='Dark.TCombobox')
            else:  # entry
                widget = ttk.Entry(form_frame, textvariable=var, style='Dark.TEntry')
                
                # เพิ่ม validation สำหรับ number fields
                if "amount" in var_name or "rate" in var_name:
                    widget.bind('<KeyRelease>', lambda e, v=var: self.validate_number(v))
            
            widget.grid(row=i, column=1, padx=10, pady=5, sticky='ew')
        
        form_frame.grid_columnconfigure(1, weight=1)
        
        # เก็บตัวแปรไว้ใช้
        setattr(self, f'{side}_vars', vars_dict)
        
        # ปุ่มช่วยเหลือ
        help_frame = ttk.Frame(form_frame, style='Dark.TFrame')
        help_frame.grid(row=len(fields), column=0, columnspan=2, pady=10, sticky='ew')
        
        if side == 'buy':
            ttk.Button(help_frame, text="💰 ใช้ยอดเงินทั้งหมด", 
                      command=lambda: self.use_max_balance(side), style='Dark.TButton').pack(side='left', padx=2)
            ttk.Button(help_frame, text="📊 ราคาตลาด", 
                      command=lambda: self.use_market_price(side), style='Dark.TButton').pack(side='left', padx=2)
        else:
            ttk.Button(help_frame, text="🪙 ขายทั้งหมด", 
                      command=lambda: self.use_max_crypto(side), style='Dark.TButton').pack(side='left', padx=2)
            ttk.Button(help_frame, text="📊 ราคาตลาด", 
                      command=lambda: self.use_market_price(side), style='Dark.TButton').pack(side='left', padx=2)
        
        # ปุ่มส่งคำสั่ง
        btn_text = "🟢 สั่งซื้อ" if side == 'buy' else "🔴 สั่งขาย"
        command = lambda: self.place_order(side)
        
        submit_btn = ttk.Button(form_frame, text=btn_text, command=command, style='Dark.TButton')
        submit_btn.grid(row=len(fields)+1, column=0, columnspan=2, pady=20, sticky='ew')
        
        # เพิ่มข้อมูลการคำนวณ
        calc_frame = ttk.Frame(form_frame, style='Dark.TFrame')
        calc_frame.grid(row=len(fields)+2, column=0, columnspan=2, sticky='ew')
        
        setattr(self, f'{side}_calc_label', ttk.Label(calc_frame, text="", style='Dark.TLabel'))
        getattr(self, f'{side}_calc_label').pack()
        
        # Bind เพื่อคำนวณแบบ real-time
        for var_name, var in vars_dict.items():
            if "amount" in var_name or "rate" in var_name:
                var.trace('w', lambda *args, s=side: self.update_calculation(s))
    
    def create_portfolio_tab(self, notebook):
        """แท็บ Portfolio ที่ปรับปรุงแล้ว"""
        frame = ttk.Frame(notebook, style='Dark.TFrame')
        notebook.add(frame, text="💼 Portfolio")
        
        # ภาพรวม Portfolio
        overview_frame = ttk.LabelFrame(frame, text="💰 ภาพรวม Portfolio", style='Dark.LabelFrame')
        overview_frame.pack(fill='x', padx=20, pady=20)
        
        # Summary stats
        summary_container = ttk.Frame(overview_frame, style='Dark.TFrame')
        summary_container.pack(fill='x', padx=10, pady=10)
        
        self.portfolio_summary = {}
        summary_items = [
            ("💵 มูลค่ารวม (THB)", "0.00"),
            ("📈 กำไร/ขาดทุนวันนี้", "0.00%"),
            ("🎯 จำนวนสกุลเงิน", "0"),
            ("⏱️ อัพเดทล่าสุด", "ไม่มี")
        ]
        
        for i, (label, value) in enumerate(summary_items):
            summary_frame = ttk.Frame(summary_container, style='Dark.TFrame')
            summary_frame.grid(row=0, column=i, padx=10, pady=5, sticky='ew')
            summary_container.grid_columnconfigure(i, weight=1)
            
            ttk.Label(summary_frame, text=label, style='Header.TLabel').pack()
            self.portfolio_summary[label] = ttk.Label(summary_frame, text=value, style='Header.TLabel')
            self.portfolio_summary[label].pack()
        
        # Balance cards
        balance_frame = ttk.LabelFrame(overview_frame, text="💰 ยอดคงเหลือ", style='Dark.LabelFrame')
        balance_frame.pack(fill='x', padx=10, pady=10)
        
        balance_container = ttk.Frame(balance_frame, style='Dark.TFrame')
        balance_container.pack(fill='x', padx=10, pady=10)
        
        self.balance_cards = {}
        currencies = ["THB", "BTC", "ETH", "ADA", "DOT"]
        
        for i, currency in enumerate(currencies):
            card_frame = ttk.Frame(balance_container, style='Dark.TFrame', relief='solid', borderwidth=1)
            card_frame.grid(row=0, column=i, padx=5, pady=5, sticky='ew')
            balance_container.grid_columnconfigure(i, weight=1)
            
            # Currency icon/name
            ttk.Label(card_frame, text=f"💰 {currency}", style='Header.TLabel', 
                     font=('Segoe UI', 11, 'bold')).pack(pady=2)
            
            # Available balance
            self.balance_cards[f"{currency}_available"] = ttk.Label(card_frame, text="0.00000000", 
                                                                   style='Success.TLabel')
            self.balance_cards[f"{currency}_available"].pack()
            
            # Reserved balance (if any)
            self.balance_cards[f"{currency}_reserved"] = ttk.Label(card_frame, text="(จอง: 0.00)", 
                                                                  style='Dark.TLabel', font=('Segoe UI', 8))
            self.balance_cards[f"{currency}_reserved"].pack()
        
        # ปุ่มควบคุม Portfolio
        control_frame = ttk.Frame(overview_frame, style='Dark.TFrame')
        control_frame.pack(fill='x', padx=10, pady=10)
        
        portfolio_buttons = [
            ("🔄 รีเฟรช Portfolio", self.refresh_portfolio),
            ("📊 ข้อมูลครบถ้วน", self.get_full_balances),
            ("📈 ประวัติการเทรด", self.show_trade_history),
            ("💾 ส่งออกข้อมูล", self.export_portfolio_data)
        ]
        
        for text, command in portfolio_buttons:
            ttk.Button(control_frame, text=text, command=command, style='Dark.TButton').pack(side='left', padx=5)
        
        # รายละเอียด Portfolio
        detail_frame = ttk.LabelFrame(frame, text="📊 รายละเอียด Portfolio", style='Dark.LabelFrame')
        detail_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # สร้าง Treeview สำหรับแสดงข้อมูล
        self.create_portfolio_treeview(detail_frame)
    
    def create_portfolio_treeview(self, parent):
        """สร้าง Treeview สำหรับแสดง Portfolio"""
        tree_frame = ttk.Frame(parent, style='Dark.TFrame')
        tree_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # สร้าง Treeview
        columns = ('Currency', 'Available', 'Reserved', 'Total', 'THB_Value', 'Percentage')
        self.portfolio_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=10)
        
        # กำหนด headings
        headings = {
            'Currency': 'สกุลเงิน',
            'Available': 'ใช้ได้',
            'Reserved': 'จอง',
            'Total': 'รวม',
            'THB_Value': 'มูลค่า (THB)',
            'Percentage': '% ของ Portfolio'
        }
        
        for col, heading in headings.items():
            self.portfolio_tree.heading(col, text=heading)
            self.portfolio_tree.column(col, width=100, anchor='center')
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=self.portfolio_tree.yview)
        self.portfolio_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack
        self.portfolio_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
    
    def create_market_data_tab(self, notebook):
        """แท็บ Market Data ที่ปรับปรุงแล้ว"""
        frame = ttk.Frame(notebook, style='Dark.TFrame')
        notebook.add(frame, text="📈 Market Data")
        
        # ส่วนควบคุม
        control_frame = ttk.LabelFrame(frame, text="🎯 ควบคุม Market Data", style='Dark.LabelFrame')
        control_frame.pack(fill='x', padx=20, pady=20)
        
        control_container = ttk.Frame(control_frame, style='Dark.TFrame')
        control_container.pack(fill='x', padx=10, pady=10)
        
        # Symbol selection
        ttk.Label(control_container, text="Symbol:", style='Header.TLabel').pack(side='left')
        self.market_data_symbol_var = tk.StringVar(value="btc_thb")
        symbol_combo = ttk.Combobox(control_container, textvariable=self.market_data_symbol_var, 
                                   values=["btc_thb", "eth_thb", "ada_thb", "dot_thb"], 
                                   style='Dark.TCombobox')
        symbol_combo.pack(side='left', padx=10)
        
        # Data type buttons
        data_buttons = [
            ("📊 Ticker", self.get_ticker_data),
            ("📋 Order Book", self.get_orderbook_data),
            ("💹 Recent Trades", self.get_trades_data),
            ("📈 24h Stats", self.get_24h_stats)
        ]
        
        for text, command in data_buttons:
            ttk.Button(control_container, text=text, command=command, style='Dark.TButton').pack(side='left', padx=5)
        
        # Auto refresh
        auto_frame = ttk.Frame(control_container, style='Dark.TFrame')
        auto_frame.pack(side='right')
        
        self.auto_refresh_var = tk.BooleanVar()
        ttk.Checkbutton(auto_frame, text="Auto Refresh (30s)", variable=self.auto_refresh_var,
                       command=self.toggle_auto_refresh).pack(side='right')
        
        # แสดงข้อมูล Market
        data_frame = ttk.LabelFrame(frame, text="📊 ข้อมูล Market", style='Dark.LabelFrame')
        data_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # สร้าง Notebook สำหรับแยกประเภทข้อมูล
        data_notebook = ttk.Notebook(data_frame)
        data_notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Tabs สำหรับข้อมูลต่างๆ
        self.market_data_tabs = {}
        tab_names = ["Ticker", "Order Book", "Trades", "Statistics"]
        
        for tab_name in tab_names:
            tab_frame = ttk.Frame(data_notebook, style='Dark.TFrame')
            data_notebook.add(tab_frame, text=tab_name)
            
            text_widget = scrolledtext.ScrolledText(tab_frame, bg='#1e1e1e', fg='#00d4aa', 
                                                  font=('Consolas', 10), insertbackground='white')
            text_widget.pack(fill='both', expand=True, padx=10, pady=10)
            self.market_data_tabs[tab_name] = text_widget
    
    def create_settings_tab(self, notebook):
        """แท็บการตั้งค่าทั่วไป"""
        frame = ttk.Frame(notebook, style='Dark.TFrame')
        notebook.add(frame, text="⚙️ ตั้งค่า")
        
        # การตั้งค่าทั่วไป
        general_frame = ttk.LabelFrame(frame, text="🔧 การตั้งค่าทั่วไป", style='Dark.LabelFrame')
        general_frame.pack(fill='x', padx=20, pady=20)
        
        general_container = ttk.Frame(general_frame, style='Dark.TFrame')
        general_container.pack(fill='x', padx=10, pady=10)
        
        # การตั้งค่าต่างๆ
        self.setting_vars = {}
        settings = [
            ("🔔 แจ้งเตือนเสียง", "sound_notifications", True, "checkbox"),
            ("📧 แจ้งเตือน Email", "email_notifications", False, "checkbox"),
            ("💾 บันทึกอัตโนมัติ", "auto_save", True, "checkbox"),
            ("🔄 อัพเดทราคาทุก (วินาที)", "price_update_interval", "30", "entry"),
            ("📊 จำนวนข้อมูลราคาที่เก็บ", "price_history_size", "200", "entry"),
            ("⚠️ เปอร์เซ็นต์แจ้งเตือนกำไร/ขาดทุน", "alert_percentage", "5.0", "entry")
        ]
        
        for i, (label, var_name, default, widget_type) in enumerate(settings):
            ttk.Label(general_container, text=label, style='Header.TLabel').grid(row=i, column=0, 
                                                                               sticky='w', padx=10, pady=5)
            
            if widget_type == "checkbox":
                var = tk.BooleanVar(value=default)
                widget = ttk.Checkbutton(general_container, variable=var)
            else:  # entry
                var = tk.StringVar(value=str(default))
                widget = ttk.Entry(general_container, textvariable=var, style='Dark.TEntry', width=20)
            
            self.setting_vars[var_name] = var
            widget.grid(row=i, column=1, padx=10, pady=5, sticky='w')
        
        # การตั้งค่าความปลอดภัย
        security_frame = ttk.LabelFrame(frame, text="🔐 ความปลอดภัย", style='Dark.LabelFrame')
        security_frame.pack(fill='x', padx=20, pady=20)
        
        security_container = ttk.Frame(security_frame, style='Dark.TFrame')
        security_container.pack(fill='x', padx=10, pady=10)
        
        security_settings = [
            ("🔒 ล็อคหลังไม่ใช้งาน (นาที)", "auto_lock_minutes", "30"),
            ("💰 จำกัดจำนวนเงินต่อเทรด (THB)", "max_trade_amount", "10000"),
            ("📊 จำกัดเทรดต่อวัน", "max_trades_per_day", "50"),
            ("⚠️ ยืนยันก่อนเทรดที่มากกว่า (THB)", "confirm_threshold", "5000")
        ]
        
        for i, (label, var_name, default) in enumerate(security_settings):
            ttk.Label(security_container, text=label, style='Header.TLabel').grid(row=i, column=0, 
                                                                                sticky='w', padx=10, pady=5)
            var = tk.StringVar(value=default)
            self.setting_vars[var_name] = var
            entry = ttk.Entry(security_container, textvariable=var, style='Dark.TEntry', width=20)
            entry.grid(row=i, column=1, padx=10, pady=5, sticky='w')
        
        # ปุ่มจัดการการตั้งค่า
        settings_buttons_frame = ttk.Frame(frame, style='Dark.TFrame')
        settings_buttons_frame.pack(fill='x', padx=20, pady=20)
        
        settings_buttons = [
            ("💾 บันทึกการตั้งค่า", self.save_all_settings),
            ("🔄 โหลดการตั้งค่าเริ่มต้น", self.load_default_settings),
            ("📁 นำเข้าการตั้งค่า", self.import_settings),
            ("📤 ส่งออกการตั้งค่า", self.export_settings),
            ("🗑️ รีเซ็ตทั้งหมด", self.reset_all_settings)
        ]
        
        for text, command in settings_buttons:
            ttk.Button(settings_buttons_frame, text=text, command=command, 
                      style='Dark.TButton').pack(side='left', padx=5)
    
    def create_enhanced_status_bar(self, parent):
        """สร้าง Status Bar ที่ปรับปรุงแล้ว"""
        status_frame = ttk.Frame(parent, style='Dark.TFrame')
        status_frame.pack(side='bottom', fill='x', pady=(10, 0))
        
        # สถานะหลัก
        self.status_var = tk.StringVar()
        self.status_var.set("🟢 พร้อมใช้งาน")
        status_label = ttk.Label(status_frame, textvariable=self.status_var, 
                               relief='sunken', style='Dark.TLabel')
        status_label.pack(side='left', fill='x', expand=True)
        
        # แสดงเวลา
        self.time_var = tk.StringVar()
        time_label = ttk.Label(status_frame, textvariable=self.time_var, 
                             relief='sunken', style='Dark.TLabel')
        time_label.pack(side='right', padx=5)
        
        # อัพเดทเวลา
        self.update_time()
        
        # Progress bar สำหรับ loading
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(status_frame, variable=self.progress_var, 
                                          maximum=100, length=200)
        # ซ่อนไว้ก่อน
        
    def update_time(self):
        """อัพเดทเวลาใน Status Bar"""
        current_time = datetime.now().strftime("%H:%M:%S")
        self.time_var.set(f"🕐 {current_time}")
        
        # เรียกใช้ตัวเองทุก 1 วินาที
        self.root.after(1000, self.update_time)
    
    # === ฟังก์ชันการทำงานหลัก ===
    
    def log_message(self, message, log_type="INFO"):
        """บันทึก Log ที่ปรับปรุงแล้ว"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        icons = {
            "INFO": "ℹ️", "SUCCESS": "✅", "WARNING": "⚠️", 
            "ERROR": "❌", "TRADE": "📈", "API": "🔗"
        }
        icon = icons.get(log_type, "ℹ️")
        
        log_entry = f"[{timestamp}] {icon} {message}\n"
        
        # บันทึกใน GUI
        if hasattr(self, 'log_text'):
            self.log_text.insert(tk.END, log_entry)
            self.log_text.see(tk.END)
            
            # จำกัดจำนวนบรรทัดใน log
            lines = self.log_text.get('1.0', tk.END).split('\n')
            if len(lines) > 1000:  # เก็บเฉพาะ 1000 บรรทัดล่าสุด
                self.log_text.delete('1.0', f'{len(lines)-1000}.0')
        
        # บันทึกใน file
        self.logger.info(f"{log_type}: {message}")
        
        # อัพเดท Status
        if hasattr(self, 'status_var'):
            self.status_var.set(f"🟢 {message[:60]}...")
    
    def log_ai_message(self, message):
        """บันทึก AI Log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        if hasattr(self, 'ai_log'):
            self.ai_log.insert(tk.END, log_entry)
            self.ai_log.see(tk.END)
            
            # จำกัดจำนวนบรรทัด
            lines = self.ai_log.get('1.0', tk.END).split('\n')
            if len(lines) > 500:
                self.ai_log.delete('1.0', f'{len(lines)-500}.0')
    
    def save_api_config(self):
        """บันทึกการตั้งค่า API ที่ปรับปรุงแล้ว"""
        api_key = self.api_key_entry.get().strip()
        api_secret = self.api_secret_entry.get().strip()
        
        if not api_key or not api_secret:
            messagebox.showerror("ข้อผิดพลาด", "กรุณากรอก API Key และ Secret")
            return
        
        # ตรวจสอบรูปแบบ API Key (ต้องเป็น hex และมีความยาวที่เหมาะสม)
        if len(api_key) < 32 or len(api_secret) < 32:
            if not messagebox.askyesno("คำเตือน", 
                                     "API Key หรือ Secret ดูเหมือนจะสั้นเกินไป\nต้องการดำเนินการต่อหรือไม่?"):
                return
        
        # สร้าง API Client
        self.api_client = BitkubAPIClient(api_key, api_secret)
        
        # บันทึกในไฟล์ config (เข้ารหัส)
        self.config['API'] = {
            'key_hash': hashlib.sha256(api_key.encode()).hexdigest()[:16],  # เก็บเฉพาะ hash
            'configured': 'True'
        }
        self.save_configuration()
        
        self.log_message("บันทึกการตั้งค่า API สำเร็จ", "SUCCESS")
        self.header_stats["การเชื่อมต่อ"].configure(text="🟡 กำลังทดสอบ...")
        
        # ทดสอบการเชื่อมต่อใน background
        threading.Thread(target=self.test_api_connection, daemon=True).start()
    
    def test_api_connection(self):
        """ทดสอบการเชื่อมต่อ API ที่ปรับปรุงแล้ว"""
        if not self.api_client:
            self.update_connection_status("🔴 ไม่มี API Config", "ไม่ได้ตั้งค่า API")
            return
        
        try:
            self.log_message("🔍 เริ่มทดสอบการเชื่อมต่อ API...", "API")
            
            # แสดง progress bar
            if hasattr(self, 'progress_bar'):
                self.progress_bar.pack(side='right', padx=5)
                self.progress_var.set(10)
            
            # ทดสอบ Public API
            self.log_message("📡 ทดสอบ Public API...", "API")
            public_result = self.api_client.make_public_request('/api/v3/servertime')
            
            if hasattr(self, 'progress_var'):
                self.progress_var.set(50)
            
            if not public_result:
                self.update_connection_status("🔴 Public API ล้มเหลว", "ไม่สามารถเชื่อมต่อ Public API")
                return
            
            self.log_message("✅ Public API ทำงานปกติ", "SUCCESS")
            
            # ทดสอบ Private API
            self.log_message("🔐 ทดสอบ Private API...", "API")
            private_result = self.api_client.make_private_request('POST', '/api/v3/market/wallet')
            
            if hasattr(self, 'progress_var'):
                self.progress_var.set(90)
            
            if private_result and private_result.get('error') == 0:
                wallet_data = private_result.get('result', {})
                thb_balance = wallet_data.get('THB', 0)
                
                self.update_connection_status("🟢 เชื่อมต่อสำเร็จ", f"ยอดเงิน: {thb_balance:,.2f} THB")
                self.log_message("✅ ทดสอบการเชื่อมต่อ API สำเร็จ!", "SUCCESS")
                self.log_message(f"💰 ยอดเงิน THB: {thb_balance:,.2f}", "SUCCESS")
                
                # อัพเดทข้อมูลใน header
                self.stats_cards["💰 ยอดเงิน (THB)"].configure(text=f"{thb_balance:,.2f}")
                
                messagebox.showinfo("สำเร็จ", "🎉 เชื่อมต่อ API สำเร็จ!")
                
            else:
                error_code = private_result.get('error', 'ไม่ทราบ') if private_result else 'ไม่มีการตอบกลับ'
                self.update_connection_status("🔴 Authentication ล้มเหลว", f"Error: {error_code}")
                self.log_message(f"❌ API Error Code: {error_code}", "ERROR")
                
                self.show_api_error_help(error_code)
            
            if hasattr(self, 'progress_var'):
                self.progress_var.set(100)
                
        except Exception as e:
            self.update_connection_status("🔴 ข้อผิดพลาด", str(e))
            self.log_message(f"❌ ข้อผิดพลาดในการทดสอบ: {str(e)}", "ERROR")
        
        finally:
            # ซ่อน progress bar
            if hasattr(self, 'progress_bar'):
                self.root.after(2000, lambda: self.progress_bar.pack_forget())
                self.progress_var.set(0)
    
    def update_connection_status(self, status_text, info_text=""):
        """อัพเดทสถานะการเชื่อมต่อ"""
        if hasattr(self, 'header_stats'):
            self.header_stats["การเชื่อมต่อ"].configure(text=status_text)
        
        if hasattr(self, 'connection_status'):
            self.connection_status.configure(text=status_text)
        
        if hasattr(self, 'connection_info') and info_text:
            self.connection_info.configure(text=info_text)
    
    def show_api_error_help(self, error_code):
        """แสดงความช่วยเหลือสำหรับข้อผิดพลาด API"""
        error_help = {
            3: "API Key ไม่ถูกต้อง - กรุณาตรวจสอบ API Key",
            5: "IP Address ไม่ได้รับอนุญาต - กรุณาเพิ่ม IP ในการตั้งค่า Bitkub",
            6: "Signature ไม่ถูกต้อง - กรุณาตรวจสอบ API Secret",
            52: "Permission ไม่เพียงพอ - กรุณาตรวจสอบสิทธิ์ API"
        }
        
        help_text = error_help.get(error_code, "ข้อผิดพลาดไม่ทราบสาเหตุ")
        
        messagebox.showerror("ข้อผิดพลาด API", 
                           f"❌ การเชื่อมต่อ API ล้มเหลว!\n\n"
                           f"Error Code: {error_code}\n"
                           f"คำแนะนำ: {help_text}\n\n"
                           f"วิธีแก้ไข:\n"
                           f"1. ตรวจสอบ API Key และ Secret\n"
                           f"2. ตรวจสอบการตั้งค่า IP Whitelist\n"
                           f"3. ตรวจสอบสิทธิ์ API\n"
                           f"4. ลองสร้าง API Key ใหม่")
    
    def start_price_monitoring(self):
        """เริ่มต้นการติดตามราคาที่ปรับปรุงแล้ว"""
        def monitor():
            while True:
                try:
                    if not self.api_client:
                        time.sleep(60)
                        continue
                    
                    # ดึงราคาของหลายสกุลเงิน
                    symbols = ["btc_thb", "eth_thb", "ada_thb"]
                    
                    for symbol in symbols:
                        ticker = self.api_client.make_public_request('/api/v3/market/ticker', {'sym': symbol})
                        if ticker and len(ticker) > 0:
                            price_data = ticker[0]
                            current_price = float(price_data['last'])
                            
                            # เก็บข้อมูลราคา
                            if symbol == "btc_thb":  # เก็บเฉพาะ BTC สำหรับกราฟ
                                self.price_history.append(current_price)
                            
                            # อัพเดท GUI
                            self.update_market_display(symbol, price_data)
                    
                    # ตรวจสอบการแจ้งเตือน
                    self.check_price_alerts()
                    
                    # ใช้ interval ที่ตั้งค่าไว้
                    interval = int(self.setting_vars.get("price_update_interval", tk.StringVar(value="30")).get())
                    time.sleep(interval)
                    
                except Exception as e:
                    self.log_message(f"ข้อผิดพลาดในการติดตามราคา: {str(e)}", "ERROR")
                    time.sleep(60)
        
        # เริ่ม thread
        monitoring_thread = threading.Thread(target=monitor, daemon=True)
        monitoring_thread.start()
        self.log_message("เริ่มการติดตามราคาแล้ว", "SUCCESS")
    
    def update_market_display(self, symbol, price_data):
        """อัพเดทการแสดงผลข้อมูลตลาด"""
        try:
            current_price = float(price_data['last'])
            change_24h = float(price_data.get('percent_change', 0))
            
            # อัพเดทข้อมูลหลัก (สำหรับ BTC)
            if symbol == "btc_thb":
                if hasattr(self, 'market_info_labels'):
                    self.market_info_labels["💰 ราคาปัจจุบัน"].configure(text=f"{current_price:,.2f} THB")
                    
                    change_color = "Success.TLabel" if change_24h >= 0 else "Error.TLabel"
                    self.market_info_labels["📈 เปลี่ยนแปลง 24h"].configure(text=f"{change_24h:+.2f}%")
                    
                    volume = float(price_data.get('base_volume', 0))
                    self.market_info_labels["📊 ปริมาณ 24h"].configure(text=f"{volume:,.2f} BTC")
                    
                    self.market_info_labels["🔄 อัพเดทล่าสุด"].configure(
                        text=datetime.now().strftime("%H:%M:%S")
                    )
        
        except Exception as e:
            self.log_message(f"ข้อผิดพลาดในการอัพเดทการแสดงผล: {str(e)}", "ERROR")
    
    def check_price_alerts(self):
        """ตรวจสอบการแจ้งเตือนราคา"""
        try:
            # ตรวจสอบการเปลี่ยนแปลงราคาอย่างมาก
            if len(self.price_history) >= 2:
                current_price = self.price_history[-1]
                previous_price = self.price_history[-2]
                
                change_percent = ((current_price - previous_price) / previous_price) * 100
                alert_threshold = float(self.setting_vars.get("alert_percentage", tk.StringVar(value="5.0")).get())
                
                if abs(change_percent) >= alert_threshold:
                    direction = "เพิ่มขึ้น" if change_percent > 0 else "ลดลง"
                    message = f"🚨 ราคา BTC {direction} {abs(change_percent):.2f}% !"
                    
                    self.log_message(message, "WARNING")
                    
                    # แจ้งเตือนเสียง (ถ้าเปิดไว้)
                    if self.setting_vars.get("sound_notifications", tk.BooleanVar(value=True)).get():
                        self.play_alert_sound()
        
        except Exception as e:
            self.log_message(f"ข้อผิดพลาดในการตรวจสอบแจ้งเตือน: {str(e)}", "ERROR")
    
    def play_alert_sound(self):
        """เล่นเสียงแจ้งเตือน"""
        try:
            # ใช้เสียงแจ้งเตือนของระบบ
            import winsound
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        except:
            # ถ้าไม่สามารถเล่นเสียงได้
            pass
    
    def toggle_ai_trading(self):
        """เปิด/ปิด AI Trading ที่ปรับปรุงแล้ว"""
        if not self.ai_enabled:
            # ตรวจสอบข้อกำหนดก่อนเริ่ม
            if not self.api_client:
                messagebox.showerror("ข้อผิดพลาด", "กรุณาตั้งค่าและทดสอบ API ก่อน!")
                return
            
            # ตรวจสอบการตั้งค่า
            try:
                amount = float(self.ai_vars["ai_amount_var"].get())
                max_trades = int(self.ai_vars["ai_max_trades_var"].get())
                
                if amount <= 0 or max_trades <= 0:
                    raise ValueError("ค่าต้องมากกว่า 0")
                    
            except ValueError as e:
                messagebox.showerror("ข้อผิดพลาด", f"การตั้งค่าไม่ถูกต้อง: {str(e)}")
                return
            
            # ยืนยันการเริ่ม AI Trading
            if not messagebox.askyesno("ยืนยันการเริ่ม AI Trading", 
                                     f"🤖 เริ่ม AI Trading?\n\n"
                                     f"Symbol: {self.ai_vars['ai_symbol_var'].get().upper()}\n"
                                     f"กลยุทธ์: {self.ai_vars['ai_strategy_var'].get()}\n"
                                     f"จำนวนเงิน: {amount:,.2f} THB ต่อเทรด\n"
                                     f"ความเสี่ยง: {self.ai_vars['ai_risk_var'].get()}\n\n"
                                     f"⚠️ การเทรดมีความเสี่ยง คุณอาจสูญเสียเงินได้"):
                return
            
            self.start_ai_trading()
        else:
            self.stop_ai_trading()
    
    def start_ai_trading(self):
        """เริ่ม AI Trading"""
        self.ai_enabled = True
        self.stop_trading = False
        
        # อัพเดท UI
        self.ai_start_button.configure(text="🛑 หยุด AI Trading")
        self.quick_start_btn.configure(text="🛑 หยุด AI")
        self.header_stats["AI Trading"].configure(text="🟢 เปิด")
        self.ai_stats["🔄 สถานะปัจจุบัน"].configure(text="🟢 ทำงาน")
        
        # เริ่ม AI Trading Thread
        self.ai_trading_thread = threading.Thread(target=self.ai_trading_loop, daemon=True)
        self.ai_trading_thread.start()
        
        self.log_ai_message("🚀 เริ่ม AI Trading!")
        self.log_message("AI Trading เริ่มทำงานแล้ว", "SUCCESS")
    
    def stop_ai_trading(self):
        """หยุด AI Trading"""
        self.ai_enabled = False
        self.stop_trading = True
        
        # อัพเดท UI
        self.ai_start_button.configure(text="🚀 เริ่ม AI Trading")
        self.quick_start_btn.configure(text="🚀 เริ่ม AI")
        self.header_stats["AI Trading"].configure(text="🔴 ปิด")
        self.ai_stats["🔄 สถานะปัจจุบัน"].configure(text="🔴 หยุด")
        
        self.log_ai_message("🛑 หยุด AI Trading!")
        self.log_message("AI Trading หยุดทำงานแล้ว", "SUCCESS")
    
    def ai_trading_loop(self):
        """ลูปการทำงานของ AI Trading ที่ปรับปรุงแล้ว"""
        trades_this_hour = 0
        hour_start = time.time()
        last_trade_time = 0
        min_trade_interval = 300  # 5 นาที
        
        while self.ai_enabled and not self.stop_trading:
            try:
                current_time = time.time()
                
                # รีเซ็ตนับเทรดต่อชั่วโมง
                if current_time - hour_start > 3600:
                    trades_this_hour = 0
                    hour_start = current_time
                
                # ตรวจสอบข้อจำกัดการเทรด
                max_trades = int(self.ai_vars["ai_max_trades_var"].get())
                if trades_this_hour >= max_trades:
                    self.log_ai_message(f"⏳ ถึงขีดจำกัดการเทรดต่อชั่วโมง ({max_trades})")
                    time.sleep(300)  # รอ 5 นาที
                    continue
                
                # ตรวจสอบระยะห่างระหว่างเทรด
                if current_time - last_trade_time < min_trade_interval:
                    time.sleep(60)
                    continue
                
                # ตรวจสอบข้อมูลราคา
                if len(self.price_history) < 20:
                    self.log_ai_message("⏳ รอข้อมูลราคาเพิ่มเติม...")
                    time.sleep(30)
                    continue
                
                # สร้างสัญญาณการเทรด
                signal = self.generate_advanced_trading_signal()
                
                if signal and signal['action'] != 'hold' and signal['confidence'] > 0.6:
                    if self.execute_ai_trade(signal):
                        trades_this_hour += 1
                        last_trade_time = current_time
                        self.total_trades += 1
                        
                        # อัพเดทสถิติ
                        self.update_ai_statistics()
                
                # รอก่อนตรวจสอบครั้งต่อไป
                time.sleep(60)
                
            except Exception as e:
                self.log_ai_message(f"❌ ข้อผิดพลาดใน AI: {str(e)}")
                self.log_message(f"AI Trading Error: {str(e)}", "ERROR")
                time.sleep(120)
    
    def generate_advanced_trading_signal(self):
        """สร้างสัญญาณการเทรดขั้นสูง"""
        try:
            strategy = self.ai_vars["ai_strategy_var"].get()
            current_price = self.price_history[-1]
            prices = list(self.price_history)
            
            if strategy == "momentum":
                signal = TradingStrategy.momentum_strategy(prices, current_price)
            elif strategy == "bollinger_bands":
                signal = TradingStrategy.bollinger_bands_strategy(prices, current_price)
            elif strategy == "hybrid":
                # รวมหลายกลยุทธ์
                momentum_signal = TradingStrategy.momentum_strategy(prices, current_price)
                bb_signal = TradingStrategy.bollinger_bands_strategy(prices, current_price)
                
                # คำนวณคะแนนรวม
                total_confidence = (momentum_signal['confidence'] + bb_signal['confidence']) / 2
                
                if momentum_signal['action'] == bb_signal['action'] and momentum_signal['action'] != 'hold':
                    signal = {
                        'action': momentum_signal['action'],
                        'confidence': min(0.9, total_confidence * 1.2),  # เพิ่มความมั่นใจเมื่อสัญญาณตรงกัน
                        'reason': f"Hybrid: {momentum_signal['reason']} + {bb_signal['reason']}"
                    }
                else:
                    signal = {
                        'action': 'hold',
                        'confidence': 0.3,
                        'reason': "สัญญาณขัดแย้งกัน"
                    }
            else:
                signal = {'action': 'hold', 'confidence': 0, 'reason': 'ไม่ทราบกลยุทธ์'}
            
            # ปรับคะแนนตามระดับความเสี่ยง
            risk_level = self.ai_vars["ai_risk_var"].get()
            risk_adjustments = {"low": 0.7, "medium": 1.0, "high": 1.3, "aggressive": 1.5}
            signal['confidence'] *= risk_adjustments.get(risk_level, 1.0)
            signal['confidence'] = min(0.95, signal['confidence'])  # จำกัดไม่เกิน 95%
            
            self.log_ai_message(f"📊 สัญญาณ: {signal['action']} (มั่นใจ: {signal['confidence']:.2f}) - {signal['reason']}")
            
            return signal
            
        except Exception as e:
            self.log_ai_message(f"❌ ข้อผิดพลาดในการสร้างสัญญาณ: {str(e)}")
            return None
    
    def execute_ai_trade(self, signal):
        """ดำเนินการเทรดโดย AI ที่ปรับปรุงแล้ว"""
        try:
            symbol = self.ai_vars["ai_symbol_var"].get()
            base_amount = float(self.ai_vars["ai_amount_var"].get())
            
            # ปรับจำนวนตามความมั่นใจ
            adjusted_amount = base_amount * signal['confidence']
            
            # ตรวจสอบจำนวนเงินสูงสุดต่อเทรด
            max_trade = float(self.setting_vars.get("max_trade_amount", tk.StringVar(value="10000")).get())
            if adjusted_amount > max_trade:
                self.log_ai_message(f"⚠️ จำกัดจำนวนเทรดที่ {max_trade:,.2f} THB")
                adjusted_amount = max_trade
            
            if signal['action'] == 'buy':
                return self.ai_place_buy_order(symbol, adjusted_amount, signal)
            elif signal['action'] == 'sell':
                return self.ai_place_sell_order(symbol, adjusted_amount, signal)
            
            return False
            
        except Exception as e:
            self.log_ai_message(f"❌ ข้อผิดพลาดในการดำเนินการเทรด: {str(e)}")
            return False
    
    def ai_place_buy_order(self, symbol, amount, signal):
        """สั่งซื้อโดย AI ที่ปรับปรุงแล้ว"""
        try:
            # ตรวจสอบยอดเงิน
            wallet = self.api_client.make_private_request('POST', '/api/v3/market/wallet')
            if not wallet or wallet.get('error') != 0:
                self.log_ai_message("❌ ไม่สามารถตรวจสอบยอดเงินได้")
                return False
            
            thb_balance = wallet.get('result', {}).get('THB', 0)
            if thb_balance < amount:
                self.log_ai_message(f"❌ ยอดเงินไม่เพียงพอ: มี {thb_balance:,.2f} ต้องการ {amount:,.2f}")
                return False
            
            # สั่งซื้อแบบ market order
            body = {
                'sym': symbol,
                'amt': amount,
                'rat': 0,  # Market order
                'typ': 'market'
            }
            
            result = self.api_client.make_private_request('POST', '/api/v3/market/place-bid', body=body)
            
            if result and result.get('error') == 0:
                self.successful_trades += 1
                order_id = result.get('result', {}).get('id', 'N/A')
                
                self.log_ai_message(f"✅ AI ซื้อสำเร็จ: {amount:,.2f} THB ของ {symbol.upper()}")
                self.log_ai_message(f"📋 Order ID: {order_id}")
                self.log_message(f"AI Trade: BUY {amount:,.2f} THB of {symbol.upper()}", "TRADE")
                
                return True
            else:
                self.failed_trades += 1
                error = result.get('error', 'Unknown') if result else 'No response'
                self.log_ai_message(f"❌ AI ซื้อล้มเหลว: Error {error}")
                return False
                
        except Exception as e:
            self.failed_trades += 1
            self.log_ai_message(f"❌ ข้อผิดพลาดในการซื้อ: {str(e)}")
            return False
    
    def ai_place_sell_order(self, symbol, amount, signal):
        """สั่งขายโดย AI ที่ปรับปรุงแล้ว"""
        try:
            # ตรวจสอบยอดคริปโต
            wallet = self.api_client.make_private_request('POST', '/api/v3/market/wallet')
            if not wallet or wallet.get('error') != 0:
                self.log_ai_message("❌ ไม่สามารถตรวจสอบยอดเงินได้")
                return False
            
            crypto_symbol = symbol.split('_')[0].upper()
            crypto_balance = wallet.get('result', {}).get(crypto_symbol, 0)
            
            if crypto_balance <= 0:
                self.log_ai_message(f"❌ ไม่มี {crypto_symbol} ให้ขาย")
                return False
            
            # คำนวณจำนวนที่จะขาย (ไม่เกิน 20% ของที่มี)
            current_price = self.price_history[-1]
            max_sell_amount = crypto_balance * 0.2
            target_sell_amount = amount / current_price
            
            sell_amount = min(max_sell_amount, target_sell_amount, crypto_balance)
            
            if sell_amount < 0.00001:  # จำนวนน้อยเกินไป
                self.log_ai_message(f"❌ จำนวนขายน้อยเกินไป: {sell_amount:.8f}")
                return False
            
            # สั่งขายแบบ market order
            body = {
                'sym': symbol,
                'amt': sell_amount,
                'rat': 0,  # Market order
                'typ': 'market'
            }
            
            result = self.api_client.make_private_request('POST', '/api/v3/market/place-ask', body=body)
            
            if result and result.get('error') == 0:
                self.successful_trades += 1
                order_id = result.get('result', {}).get('id', 'N/A')
                
                self.log_ai_message(f"✅ AI ขายสำเร็จ: {sell_amount:.8f} {crypto_symbol}")
                self.log_ai_message(f"📋 Order ID: {order_id}")
                self.log_message(f"AI Trade: SELL {sell_amount:.8f} {crypto_symbol}", "TRADE")
                
                return True
            else:
                self.failed_trades += 1
                error = result.get('error', 'Unknown') if result else 'No response'
                self.log_ai_message(f"❌ AI ขายล้มเหลว: Error {error}")
                return False
                
        except Exception as e:
            self.failed_trades += 1
            self.log_ai_message(f"❌ ข้อผิดพลาดในการขาย: {str(e)}")
            return False
    
    def update_ai_statistics(self):
        """อัพเดทสถิติ AI Trading"""
        try:
            total_trades = self.successful_trades + self.failed_trades
            success_rate = (self.successful_trades / max(total_trades, 1)) * 100
            
            # อัพเดท GUI
            self.ai_stats["🎯 อัตราความแม่นยำ"].configure(text=f"{success_rate:.1f}%")
            self.ai_stats["📈 เทรดสำเร็จ"].configure(text=str(self.successful_trades))
            self.ai_stats["📉 เทรดล้มเหลว"].configure(text=str(self.failed_trades))
            
            # อัพเดท header stats
            self.header_stats["จำนวนเทรด"].configure(text=str(total_trades))
            
            self.log_message(f"สถิติ AI: สำเร็จ {self.successful_trades}/{total_trades} ({success_rate:.1f}%)", "INFO")
            
        except Exception as e:
            self.log_message(f"ข้อผิดพลาดในการอัพเดทสถิติ: {str(e)}", "ERROR")
    
    # === ฟังก์ชันสำหรับ Manual Trading ===
    
    def place_order(self, side):
        """วางคำสั่งซื้อ/ขาย (Manual)"""
        try:
            if not self.api_client:
                messagebox.showerror("ข้อผิดพลาด", "กรุณาตั้งค่า API ก่อน")
                return
            
            vars_dict = getattr(self, f'{side}_vars')
            
            symbol = vars_dict[f'{side}_symbol_var'].get()
            amount = float(vars_dict[f'{side}_amount_var'].get())
            rate = float(vars_dict[f'{side}_rate_var'].get()) if vars_dict[f'{side}_rate_var'].get() else 0
            order_type = vars_dict[f'{side}_type_var'].get()
            
            if amount <= 0:
                messagebox.showerror("ข้อผิดพลาด", "จำนวนต้องมากกว่า 0")
                return
            
            # ตรวจสอบจำนวนเงินสูงสุด
            max_amount = float(self.setting_vars.get("max_trade_amount", tk.StringVar(value="10000")).get())
            confirm_threshold = float(self.setting_vars.get("confirm_threshold", tk.StringVar(value="5000")).get())
            
            if side == 'buy' and amount > max_amount:
                messagebox.showerror("ข้อผิดพลาด", f"จำนวนเงินเกินขีดจำกัด: {max_amount:,.2f} THB")
                return
            
            # ยืนยันการสั่งซื้อ/ขาย
            if side == 'buy' and amount > confirm_threshold:
                if not messagebox.askyesno("ยืนยันการสั่งซื้อ", 
                                         f"⚠️ จำนวนเงินมาก!\n\n"
                                         f"🟢 สั่งซื้อ {symbol.upper()}\n"
                                         f"จำนวน: {amount:,.2f} THB\n"
                                         f"ราคา: {rate:,.2f}\n"
                                         f"ประเภท: {order_type.upper()}\n\n"
                                         f"ยืนยันการดำเนินการ?"):
                    return
            
            # ดำเนินการสั่งซื้อ/ขาย
            threading.Thread(target=self._execute_manual_order, 
                           args=(side, symbol, amount, rate, order_type), daemon=True).start()
            
        except ValueError:
            messagebox.showerror("ข้อผิดพลาด", "กรุณากรอกตัวเลขที่ถูกต้อง")
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"เกิดข้อผิดพลาด: {str(e)}")
    
    def _execute_manual_order(self, side, symbol, amount, rate, order_type):
        """ดำเนินการสั่งซื้อ/ขายใน background"""
        try:
            body = {
                'sym': symbol,
                'amt': amount,
                'rat': rate,
                'typ': order_type
            }
            
            if side == 'buy':
                result = self.api_client.make_private_request('POST', '/api/v3/market/place-bid', body=body)
                action = "ซื้อ"
                emoji = "🟢"
            else:
                result = self.api_client.make_private_request('POST', '/api/v3/market/place-ask', body=body)
                action = "ขาย"
                emoji = "🔴"
            
            if result:
                # แสดงผลลัพธ์
                timestamp = datetime.now().strftime("%H:%M:%S")
                self.trading_result.insert(tk.END, f"\n{emoji} === ผลการ{action} [{timestamp}] ===\n")
                self.trading_result.insert(tk.END, json.dumps(result, indent=2, ensure_ascii=False))
                self.trading_result.insert(tk.END, f"\n{'='*60}\n")
                self.trading_result.see(tk.END)
                
                if result.get('error') == 0:
                    order_data = result.get('result', {})
                    order_id = order_data.get('id', 'N/A')
                    
                    self.log_message(f"Manual Trade: {action} {amount:,.2f} {symbol.upper()} - Order ID: {order_id}", "TRADE")
                    messagebox.showinfo("สำเร็จ", f"🎉 {action}สำเร็จ!\nOrder ID: {order_id}")
                    
                    # ล้างฟอร์ม
                    vars_dict = getattr(self, f'{side}_vars')
                    vars_dict[f'{side}_amount_var'].set("")
                    vars_dict[f'{side}_rate_var'].set("")
                    
                    # รีเฟรชข้อมูล
                    self.refresh_open_orders()
                    
                else:
                    error_code = result.get('error')
                    self.log_message(f"Manual Trade Failed: {action} - Error {error_code}", "ERROR")
                    messagebox.showerror("ล้มเหลว", f"❌ {action}ล้มเหลว!\nError: {error_code}")
            
        except Exception as e:
            self.log_message(f"Manual Trade Error: {str(e)}", "ERROR")
            messagebox.showerror("ข้อผิดพลาด", f"เกิดข้อผิดพลาด: {str(e)}")
    
    # === ฟังก์ชันอื่นๆ ===
    
    def quick_start_ai(self):
        """เริ่ม AI แบบด่วน"""
        if not self.ai_enabled:
            self.toggle_ai_trading()
        else:
            self.stop_ai_trading()
    
    def quick_settings(self):
        """การตั้งค่าด่วน"""
        # สร้างหน้าต่างการตั้งค่าด่วน
        settings_window = tk.Toplevel(self.root)
        settings_window.title("⚙️ การตั้งค่าด่วน")
        settings_window.geometry("400x300")
        settings_window.configure(bg='#1a1a1a')
        
        # เนื้อหาการตั้งค่าด่วน
        ttk.Label(settings_window, text="การตั้งค่าด่วนจะอยู่ที่นี่", 
                 style='Header.TLabel').pack(expand=True)
    
    def load_saved_settings(self):
        """โหลดการตั้งค่าที่บันทึกไว้"""
        try:
            if 'API' in self.config and self.config['API'].get('configured') == 'True':
                # แสดงว่าเคยตั้งค่า API แล้ว
                self.log_message("พบการตั้งค่า API ที่บันทึกไว้", "INFO")
                
        except Exception as e:
            self.log_message(f"ข้อผิดพลาดในการโหลดการตั้งค่า: {str(e)}", "ERROR")
    
    def save_all_settings(self):
        """บันทึกการตั้งค่าทั้งหมด"""
        try:
            # บันทึกการตั้งค่าต่างๆ ลงไฟล์
            settings_to_save = {}
            
            for var_name, var in self.setting_vars.items():
                if isinstance(var, tk.BooleanVar):
                    settings_to_save[var_name] = var.get()
                else:
                    settings_to_save[var_name] = var.get()
            
            self.config['SETTINGS'] = settings_to_save
            self.save_configuration()
            
            self.log_message("บันทึกการตั้งค่าทั้งหมดสำเร็จ", "SUCCESS")
            messagebox.showinfo("สำเร็จ", "💾 บันทึกการตั้งค่าสำเร็จ!")
            
        except Exception as e:
            self.log_message(f"ข้อผิดพลาดในการบันทึกการตั้งค่า: {str(e)}", "ERROR")
            messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถบันทึกการตั้งค่าได้: {str(e)}")


# === ฟังก์ชันหลักของโปรแกรม ===
def main():
    """ฟังก์ชันหลัก"""
    print("🚀 เริ่มต้น Bitkub AI Trading Bot Professional Edition...")
    
    # สร้างหน้าต่างหลัก
    root = tk.Tk()
    
    # ตั้งค่าหน้าต่าง
    root.configure(bg='#1a1a1a')
    
    # สร้าง Application
    app = BitkubTradingBot(root)
    
    # จัดตำแหน่งหน้าต่างตรงกลางจอ
    root.update_idletasks()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width // 2) - (1400 // 2)
    y = (screen_height // 2) - (900 // 2)
    root.geometry(f"1400x900+{x}+{y}")
    
    # ตั้งค่าขนาดขั้นต่ำ
    root.minsize(1200, 700)
    
    # ข้อความต้อนรับ
    app.log_message("🚀 ยินดีต้อนรับสู่ Bitkub AI Trading Bot Professional Edition!")
    app.log_message("💡 กรุณาตั้งค่า API ในแท็บ 'ตั้งค่า API' ก่อนใช้งาน")
    app.log_message("🤖 ฟีเจอร์ AI Trading ขั้นสูงพร้อมใช้งาน")
    app.log_message("⚠️ การเทรดมีความเสี่ยง กรุณาใช้งานด้วยความระมัดระวัง")
    
    if not MATPLOTLIB_AVAILABLE:
        app.log_message("📊 กราฟไม่พร้อมใช้งาน - ติดตั้ง matplotlib สำหรับกราฟ", "WARNING")
    
    # เริ่มต้นโปรแกรม
    try:
        print("✅ GUI พร้อมใช้งาน")
        root.mainloop()
    except KeyboardInterrupt:
        app.log_message("👋 กำลังปิดโปรแกรม...")
        if app.ai_enabled:
            app.stop_trading = True
        root.quit()
    except Exception as e:
        print(f"❌ ข้อผิดพลาด: {e}")
        messagebox.showerror("ข้อผิดพลาด", f"เกิดข้อผิดพลาด: {e}")


if __name__ == "__main__":
    main()