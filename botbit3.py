import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import hashlib
import hmac
import json
import time
import requests
import threading
from datetime import datetime, timedelta
import os
import numpy as np
from collections import deque

# Try to import matplotlib, but make it optional
try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    import matplotlib.dates as mdates
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("📊 Matplotlib not found. Chart features will be disabled.")
    print("   Install with: pip install matplotlib")

class BitkubAPIClient:
    """
    คลาส API Client ที่แก้ไขแล้วสำหรับ Bitkub
    รองรับ API V3 และ V4 พร้อม Rate Limiting และ Error Handling
    """
    
    def __init__(self, api_key="", api_secret=""):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://api.bitkub.com"
        
        # Rate limiting
        self.request_times = deque(maxlen=250)
        self.rate_limit_lock = threading.Lock()
        
        # Logging
        print("🚀 Bitkub API Client initialized")
    
    def _wait_for_rate_limit(self):
        """จัดการ Rate Limiting ตาม API documentation"""
        with self.rate_limit_lock:
            now = time.time()
            
            # ลบ request ที่เก่ากว่า 10 วินาที
            while self.request_times and (now - self.request_times[0]) > 10:
                self.request_times.popleft()
            
            # ตรวจสอบ rate limit (250 req / 10 secs)
            if len(self.request_times) >= 250:
                sleep_time = 10 - (now - self.request_times[0]) + 0.1
                if sleep_time > 0:
                    print(f"⏳ Rate limit reached, waiting {sleep_time:.1f} seconds...")
                    time.sleep(sleep_time)
                    self.request_times.clear()
            
            self.request_times.append(now)
    
    def _generate_signature(self, payload_string):
        """สร้าง HMAC SHA-256 signature ตาม Bitkub spec"""
        if not self.api_secret:
            raise ValueError("API Secret not configured")
        
        return hmac.new(
            self.api_secret.encode('utf-8'),
            payload_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _build_query_string(self, params):
        """สร้าง query string สำหรับ GET request"""
        if not params:
            return ""
        
        # กรอง None values และแปลงเป็น string
        filtered_params = {k: str(v) for k, v in params.items() if v is not None}
        
        # สร้าง query string
        query_parts = []
        for key, value in filtered_params.items():
            query_parts.append(f"{key}={value}")
        
        return "?" + "&".join(query_parts) if query_parts else ""
    
    def get_server_time(self):
        """ดึงเวลาเซิร์ฟเวอร์"""
        return self.make_public_request('/api/v3/servertime')
    
    def get_ticker(self, symbol=None):
        """ดึงข้อมูล ticker"""
        params = {'sym': symbol} if symbol else None
        return self.make_public_request('/api/v3/market/ticker', params)
    
    def get_depth(self, symbol, limit=10):
        """ดึงข้อมูล order book"""
        params = {'sym': symbol, 'lmt': limit}
        return self.make_public_request('/api/v3/market/depth', params)
    
    def get_wallet(self):
        """ดึงยอดเงินในกระเป๋า"""
        return self.make_private_request('POST', '/api/v3/market/wallet')
    
    def get_balances(self):
        """ดึงยอดเงินแบบละเอียด"""
        return self.make_private_request('POST', '/api/v3/market/balances')
    
    def place_buy_order(self, symbol, amount, rate=0, order_type='market', client_id=None):
        """วางคำสั่งซื้อ"""
        body = {
            'sym': symbol,
            'amt': amount,
            'rat': rate,
            'typ': order_type
        }
        
        if client_id:
            body['client_id'] = client_id
        
        return self.make_private_request('POST', '/api/v3/market/place-bid', body=body)
    
    def place_sell_order(self, symbol, amount, rate=0, order_type='market', client_id=None):
        """วางคำสั่งขาย"""
        body = {
            'sym': symbol,
            'amt': amount,
            'rat': rate,
            'typ': order_type
        }
        
        if client_id:
            body['client_id'] = client_id
        
        return self.make_private_request('POST', '/api/v3/market/place-ask', body=body)
    
    def cancel_order(self, symbol, order_id, side):
        """ยกเลิกคำสั่ง"""
        body = {
            'sym': symbol,
            'id': order_id,
            'sd': side
        }
        return self.make_private_request('POST', '/api/v3/market/cancel-order', body=body)
    
    def get_open_orders(self, symbol):
        """ดึงรายการคำสั่งที่ยังเปิดอยู่"""
        params = {'sym': symbol}
        return self.make_private_request('GET', '/api/v3/market/my-open-orders', params=params)
    
    def make_public_request(self, endpoint, params=None):
        """ส่งคำขอ Public API"""
        try:
            self._wait_for_rate_limit()
            
            url = f"{self.base_url}{endpoint}"
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            print(f"✅ Public API: {endpoint} - Success")
            return result
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Public API Error ({endpoint}): {e}")
            return None
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return None
    
    def make_private_request(self, method, endpoint, params=None, body=None, debug=False):
        """ส่งคำขอ Private API พร้อม authentication และ debug"""
        try:
            if not self.api_key or not self.api_secret:
                raise ValueError("API credentials not configured")
            
            self._wait_for_rate_limit()
            
            # ดึงเวลาจากเซิร์ฟเวอร์ Bitkub
            try:
                server_time_response = requests.get(f"{self.base_url}/api/v3/servertime", timeout=5)
                ts = str(server_time_response.json())
            except:
                # ถ้าไม่ได้ ใช้เวลาเครื่อง
                ts = str(round(time.time() * 1000))
            
            url = f"{self.base_url}{endpoint}"
            
            # สร้าง payload สำหรับ signature
            payload_parts = [ts, method.upper(), endpoint]
            
            if method.upper() == 'GET' and params:
                query_string = self._build_query_string(params)
                if query_string:
                    payload_parts.append(query_string)
                    url += query_string
            elif method.upper() == 'POST' and body:
                json_body = json.dumps(body, separators=(',', ':'))
                payload_parts.append(json_body)
            elif method.upper() == 'POST':
                # สำหรับ POST ที่ไม่มี body ต้องใส่ {} 
                payload_parts.append('{}')
            
            # สร้าง signature
            payload_string = ''.join(payload_parts)
            signature = self._generate_signature(payload_string)
            
            # Headers
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'X-BTK-TIMESTAMP': ts,
                'X-BTK-SIGN': signature,
                'X-BTK-APIKEY': self.api_key
            }
            
            # Debug output
            if debug or endpoint == '/api/v3/market/wallet':
                print(f"\n🔧 === DEBUG API REQUEST ===")
                print(f"Method: {method}")
                print(f"Endpoint: {endpoint}")
                print(f"URL: {url}")
                print(f"Timestamp: {ts}")
                print(f"Payload String: {payload_string}")
                print(f"Signature: {signature}")
                print(f"API Key: {self.api_key[:16]}...")
                print(f"API Secret: {self.api_secret[:16]}...")
                print(f"===========================\n")
            
            # ส่งคำขอ
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            else:
                response = requests.post(url, headers=headers, json=body or {}, timeout=10)
            
            # Debug response
            if debug or endpoint == '/api/v3/market/wallet':
                print(f"📡 Response Status: {response.status_code}")
                print(f"📤 Response Headers: {dict(response.headers)}")
                if response.status_code != 200:
                    print(f"📝 Response Text: {response.text}")
            
            response.raise_for_status()
            result = response.json()
            
            # ตรวจสอบ error code
            if isinstance(result, dict) and result.get('error') != 0:
                error_code = result.get('error')
                print(f"⚠️ API Error Code: {error_code}")
                print(f"📋 Error Message: {self.get_error_description(error_code)}")
            else:
                print(f"✅ Private API: {endpoint} - Success")
            
            return result
            
        except ValueError as e:
            print(f"❌ Configuration Error: {e}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"❌ Private API Error ({endpoint}): {e}")
            if "401" in str(e):
                print("🔍 Possible causes:")
                print("   1. ตรวจสอบ API Key และ Secret")
                print("   2. ตรวจสอบ API Permissions (ต้องมี 'trade' permission)")
                print("   3. ตรวจสอบ IP Whitelist ใน Bitkub")
                print("   4. ตรวจสอบว่า API ยังไม่หมดอายุ")
            return None
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return None
    
    def get_error_description(self, error_code):
        """แปลง error code เป็นคำอธิบาย"""
        error_descriptions = {
            0: "สำเร็จ - ไม่มีข้อผิดพลาด",
            1: "JSON payload ไม่ถูกต้อง",
            2: "ไม่พบ X-BTK-APIKEY",
            3: "API key ไม่ถูกต้อง",
            4: "API รอการอนุมัติ",
            5: "IP address ไม่ได้รับอนุญาต",
            6: "Signature หายไปหรือไม่ถูกต้อง",
            7: "ไม่พบ timestamp",
            8: "Timestamp ไม่ถูกต้อง",
            9: "ผู้ใช้ไม่ถูกต้องหรือถูกระงับ",
            10: "Parameter ไม่ถูกต้อง",
            11: "Symbol ไม่ถูกต้อง",
            12: "จำนวนเงินไม่ถูกต้องหรือต่ำเกินไป",
            13: "ราคาไม่ถูกต้อง",
            14: "ราคาไม่เหมาะสม",
            15: "จำนวนเงินต่ำเกินไป",
            16: "ไม่สามารถดึงยอดเงินได้",
            17: "กระเป๋าเงินว่าง",
            18: "ยอดเงินไม่เพียงพอ",
            21: "คำสั่งไม่ถูกต้องสำหรับการยกเลิก",
            22: "ฝั่งการเทรดไม่ถูกต้อง (buy/sell)",
            25: "ต้องผ่าน KYC ระดับ 1",
            30: "เกินขีดจำกัด",
            90: "ข้อผิดพลาดเซิร์ฟเวอร์"
        }
        
        return error_descriptions.get(error_code, f"ข้อผิดพลาดไม่ทราบ (Code: {error_code})")
    
    def test_connection(self):
        """ทดสอบการเชื่อมต่อ API"""
        print("🔍 Testing API connection...")
        
        # ทดสอบ Public API
        server_time = self.get_server_time()
        if not server_time:
            print("❌ Public API connection failed")
            return False
        
        print("✅ Public API working")
        
        # ทดสอบ Private API (ถ้ามี credentials)
        if self.api_key and self.api_secret:
            wallet = self.get_wallet()
            if wallet and wallet.get('error') == 0:
                print("✅ Private API working")
                
                # แสดงยอดเงิน
                balance_data = wallet.get('result', {})
                thb_balance = balance_data.get('THB', 0)
                print(f"💰 THB Balance: {thb_balance:,.2f}")
                
                return True
            else:
                print("❌ Private API authentication failed")
                return False
        else:
            print("⚠️ No API credentials for Private API testing")
            return True

class BitkubAIGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🚀 Bitkub AI Trading Bot - Professional Edition")
        self.root.geometry("1400x900")
        self.root.configure(bg='#1e1e1e')
        
        # Configure modern style
        self.setup_styles()
        
        # API Client
        self.api_client = None
        
        # AI Trading Variables
        self.ai_enabled = False
        self.price_history = deque(maxlen=100)
        self.trade_signals = deque(maxlen=50)
        self.auto_trading_thread = None
        self.stop_trading = False
        
        # Portfolio tracking
        self.portfolio = {"THB": 0, "BTC": 0, "ETH": 0}
        self.initial_balance = 0
        self.total_trades = 0
        self.profitable_trades = 0
        
        self.setup_gui()
        
    def setup_styles(self):
        """Setup modern dark theme styles"""
        style = ttk.Style()
        
        # Use a compatible theme
        try:
            style.theme_use('clam')
        except:
            style.theme_use('default')
        
        # Configure colors
        bg_color = '#2b2b2b'
        fg_color = '#ffffff'
        select_color = '#404040'
        accent_color = '#00d4aa'
        
        # Configure standard ttk styles
        style.configure('TLabel', 
                       background=bg_color, foreground=fg_color, 
                       font=('Segoe UI', 10))
        
        style.configure('TLabelFrame', 
                       background=bg_color, foreground=fg_color,
                       borderwidth=1, relief='solid')
        
        style.configure('TFrame', background=bg_color)
        
        style.configure('TButton', 
                       background=select_color, foreground=fg_color,
                       borderwidth=1, focuscolor='none')
        
        style.configure('TEntry', 
                       insertcolor=fg_color, fieldbackground='#404040',
                       borderwidth=1, foreground=fg_color)
        
        style.configure('TCombobox', 
                       fieldbackground='#404040', background=select_color,
                       foreground=fg_color, borderwidth=1)
        
        # Map styles for hover effects
        style.map('TButton',
                 background=[('active', accent_color), ('pressed', accent_color)],
                 foreground=[('active', '#000000'), ('pressed', '#000000')])
        
        # Configure Notebook
        style.configure('TNotebook', background=bg_color, borderwidth=1)
        style.configure('TNotebook.Tab', 
                       background=select_color, foreground=fg_color,
                       padding=[12, 8])
        style.map('TNotebook.Tab',
                 background=[('selected', accent_color), ('active', '#505050')],
                 foreground=[('selected', '#000000'), ('active', fg_color)])
        
    def setup_gui(self):
        # Configure root window
        self.root.configure(bg='#2b2b2b')
        
        # Main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Header
        self.setup_header(main_container)
        
        # Create main notebook for tabs
        notebook = ttk.Notebook(main_container)
        notebook.pack(fill='both', expand=True, pady=(10, 0))
        
        # Setup all tabs
        self.setup_dashboard_tab(notebook)
        self.setup_api_tab(notebook)
        self.setup_manual_trading_tab(notebook)
        self.setup_market_tab(notebook)
        self.setup_portfolio_tab(notebook)
        self.setup_orders_tab(notebook)
        
        # Status bar with modern styling
        self.setup_status_bar(main_container)
        
    def setup_header(self, parent):
        """Setup modern header with logo and stats"""
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill='x', pady=(0, 10))
        
        # Logo and title
        title_frame = ttk.Frame(header_frame)
        title_frame.pack(side='left')
        
        ttk.Label(title_frame, text="🚀", font=('Segoe UI', 24)).pack(side='left')
        title_label = ttk.Label(title_frame, text="Bitkub AI Trading Bot", 
                               font=('Segoe UI', 16, 'bold'), foreground='#00d4aa')
        title_label.pack(side='left', padx=(10, 0))
        
        # Stats panel
        stats_frame = ttk.Frame(header_frame)
        stats_frame.pack(side='right')
        
        self.stats_labels = {}
        stats = [
            ("💰 Balance", "0 THB"),
            ("📈 P&L", "0.00%"),
            ("🤖 Connection", "Offline"),
            ("📊 Trades", "0")
        ]
        
        for i, (label, value) in enumerate(stats):
            frame = ttk.Frame(stats_frame)
            frame.grid(row=0, column=i, padx=10)
            
            ttk.Label(frame, text=label, font=('Segoe UI', 9)).pack()
            self.stats_labels[label] = ttk.Label(frame, text=value, 
                                               font=('Segoe UI', 12, 'bold'))
            self.stats_labels[label].pack()
    
    def setup_dashboard_tab(self, notebook):
        """Dashboard with live charts and overview"""
        dash_frame = ttk.Frame(notebook)
        notebook.add(dash_frame, text="📊 Dashboard")
        
        # Top metrics
        metrics_frame = ttk.LabelFrame(dash_frame, text="📈 Live Metrics", padding=10)
        metrics_frame.pack(fill='x', padx=10, pady=10)
        
        metrics_inner = ttk.Frame(metrics_frame)
        metrics_inner.pack(fill='x')
        
        # Create metric cards
        self.metric_cards = {}
        metrics = ["BTC Price", "ETH Price", "Portfolio Value", "24h Change"]
        
        for i, metric in enumerate(metrics):
            card = ttk.Frame(metrics_inner, relief='solid')
            card.grid(row=0, column=i, padx=10, pady=5, sticky='ew')
            metrics_inner.grid_columnconfigure(i, weight=1)
            
            ttk.Label(card, text=metric, font=('Segoe UI', 10)).pack(pady=2)
            self.metric_cards[metric] = ttk.Label(card, text="Loading...", 
                                                font=('Segoe UI', 12, 'bold'))
            self.metric_cards[metric].pack(pady=2)
        
        # Chart area
        chart_frame = ttk.LabelFrame(dash_frame, text="📈 Price Chart", padding=10)
        chart_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create chart
        if MATPLOTLIB_AVAILABLE:
            self.setup_chart(chart_frame)
        else:
            ttk.Label(chart_frame, text="📊 Chart not available\nInstall matplotlib for chart features", 
                     font=('Segoe UI', 12), foreground='orange').pack(expand=True)
        
        # Quick actions
        actions_frame = ttk.LabelFrame(dash_frame, text="⚡ Quick Actions", padding=10)
        actions_frame.pack(fill='x', padx=10, pady=10)
        
        actions_inner = ttk.Frame(actions_frame)
        actions_inner.pack(fill='x')
        
        ttk.Button(actions_inner, text="💰 Get Balance",
                  command=self.quick_balance_check).pack(side='left', padx=5)
        ttk.Button(actions_inner, text="📊 Refresh Data",
                  command=self.refresh_dashboard).pack(side='left', padx=5)
    
    def setup_chart(self, parent):
        """Setup matplotlib chart for price data"""
        if not MATPLOTLIB_AVAILABLE:
            return
            
        self.fig, self.ax = plt.subplots(figsize=(10, 4), facecolor='#2b2b2b')
        self.ax.set_facecolor('#2b2b2b')
        self.ax.tick_params(colors='white')
        self.ax.spines['bottom'].set_color('white')
        self.ax.spines['top'].set_color('white')
        self.ax.spines['right'].set_color('white')
        self.ax.spines['left'].set_color('white')
        
        self.canvas = FigureCanvasTkAgg(self.fig, parent)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
        
        # Initialize empty plot
        self.ax.plot([], [], color='#00d4aa', linewidth=2)
        self.ax.set_title('BTC/THB Price', color='white', fontsize=14)
        self.ax.set_ylabel('Price (THB)', color='white')
        
    def setup_api_tab(self, notebook):
        """API Settings with modern design"""
        api_frame = ttk.Frame(notebook)
        notebook.add(api_frame, text="🔧 API Settings")
        
        # API Configuration
        config_frame = ttk.LabelFrame(api_frame, text="🔐 API Configuration", padding=20)
        config_frame.pack(fill='x', padx=10, pady=10)
        
        # Instructions
        instruction_text = """
📝 How to create API Key in Bitkub:

1. Login to Bitkub.com
2. Go to Settings > API Management
3. Create new API Key with permissions:
   ✅ View Portfolio (for balance viewing)
   ✅ Trade (for trading)
   ❌ Withdraw (not recommended for security)
4. Copy API Key and Secret below

⚠️ Warning: Never share your API Secret and keep it secure!
        """
        
        instruction_label = ttk.Label(config_frame, text=instruction_text, 
                                    font=('Segoe UI', 9), justify='left')
        instruction_label.pack(fill='x', pady=(0, 20))
        
        # API Key input frame
        api_key_frame = ttk.Frame(config_frame)
        api_key_frame.pack(fill='x', pady=5)
        
        ttk.Label(api_key_frame, text="API Key:", font=('Segoe UI', 12, 'bold')).pack(anchor='w')
        self.api_key_entry = ttk.Entry(api_key_frame, width=80, show="*", font=('Consolas', 10))
        self.api_key_entry.pack(fill='x', pady=(5, 0))
        
        # API Secret input frame
        api_secret_frame = ttk.Frame(config_frame)
        api_secret_frame.pack(fill='x', pady=5)
        
        ttk.Label(api_secret_frame, text="API Secret:", font=('Segoe UI', 12, 'bold')).pack(anchor='w')
        self.api_secret_entry = ttk.Entry(api_secret_frame, width=80, show="*", font=('Consolas', 10))
        self.api_secret_entry.pack(fill='x', pady=(5, 0))
        
        # Buttons
        btn_frame = ttk.Frame(config_frame)
        btn_frame.pack(fill='x', pady=20)
        
        ttk.Button(btn_frame, text="💾 Save Configuration",
                  command=self.save_api_config).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="🔍 Test Connection",
                  command=self.test_api_connection).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="👁️ Show/Hide",
                  command=self.toggle_api_visibility).pack(side='left', padx=5)
        
        # Connection Status
        status_frame = ttk.LabelFrame(api_frame, text="🌐 Connection Status", padding=20)
        status_frame.pack(fill='x', padx=10, pady=10)
        
        self.connection_status = ttk.Label(status_frame, text="⚫ Not Connected", 
                                         font=('Segoe UI', 12))
        self.connection_status.pack()
        
        # API Logs
        log_frame = ttk.LabelFrame(api_frame, text="📝 API Logs", padding=10)
        log_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, bg='#1e1e1e', fg='#ffffff',
                                                font=('Consolas', 10))
        self.log_text.pack(fill='both', expand=True)
        
    def setup_manual_trading_tab(self, notebook):
        """Manual trading with advanced features"""
        trading_frame = ttk.Frame(notebook)
        notebook.add(trading_frame, text="💰 Manual Trading")
        
        # Trading interface with modern cards
        main_trading = ttk.Frame(trading_frame)
        main_trading.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Buy side
        buy_frame = ttk.LabelFrame(main_trading, text="🟢 BUY ORDER", padding=15)
        buy_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
        
        self.setup_trading_form(buy_frame, "buy")
        
        # Sell side
        sell_frame = ttk.LabelFrame(main_trading, text="🔴 SELL ORDER", padding=15)
        sell_frame.pack(side='right', fill='both', expand=True, padx=(5, 0))
        
        self.setup_trading_form(sell_frame, "sell")
        
        # Trading results
        result_frame = ttk.LabelFrame(trading_frame, text="📊 Trading Results", padding=10)
        result_frame.pack(fill='x', padx=10, pady=10)
        
        self.trading_text = scrolledtext.ScrolledText(result_frame, height=8, 
                                                    bg='#1e1e1e', fg='#ffffff',
                                                    font=('Consolas', 10))
        self.trading_text.pack(fill='both', expand=True)
        
    def setup_trading_form(self, parent, side):
        """Setup trading form for buy/sell"""
        # Symbol
        ttk.Label(parent, text="Symbol:", font=('Segoe UI', 12, 'bold')).grid(row=0, column=0, sticky='w', pady=5)
        symbol_var = tk.StringVar(value="btc_thb")
        setattr(self, f"{side}_symbol_var", symbol_var)
        ttk.Combobox(parent, textvariable=symbol_var, 
                    values=["btc_thb", "eth_thb", "ada_thb"]).grid(row=0, column=1, sticky='ew', padx=5)
        
        # Amount
        amount_label = "Amount (THB):" if side == "buy" else "Amount (Crypto):"
        ttk.Label(parent, text=amount_label, font=('Segoe UI', 12, 'bold')).grid(row=1, column=0, sticky='w', pady=5)
        amount_var = tk.StringVar()
        setattr(self, f"{side}_amount_var", amount_var)
        ttk.Entry(parent, textvariable=amount_var, font=('Segoe UI', 11)).grid(row=1, column=1, sticky='ew', padx=5)
        
        # Rate
        ttk.Label(parent, text="Rate:", font=('Segoe UI', 12, 'bold')).grid(row=2, column=0, sticky='w', pady=5)
        rate_var = tk.StringVar()
        setattr(self, f"{side}_rate_var", rate_var)
        ttk.Entry(parent, textvariable=rate_var, font=('Segoe UI', 11)).grid(row=2, column=1, sticky='ew', padx=5)
        
        # Type
        ttk.Label(parent, text="Type:", font=('Segoe UI', 12, 'bold')).grid(row=3, column=0, sticky='w', pady=5)
        type_var = tk.StringVar(value="limit")
        setattr(self, f"{side}_type_var", type_var)
        ttk.Combobox(parent, textvariable=type_var, 
                    values=["limit", "market"]).grid(row=3, column=1, sticky='ew', padx=5)
        
        parent.grid_columnconfigure(1, weight=1)
        
        # Submit button
        btn_text = f"🟢 PLACE BUY ORDER" if side == 'buy' else "🔴 PLACE SELL ORDER"
        command = self.place_buy_order if side == 'buy' else self.place_sell_order
        
        ttk.Button(parent, text=btn_text, 
                  command=command).grid(row=4, column=0, columnspan=2, pady=20, sticky='ew')
        
    def setup_market_tab(self, notebook):
        """Market data with real-time updates"""
        market_frame = ttk.Frame(notebook)
        notebook.add(market_frame, text="📈 Market Data")
        
        # Symbol selection and controls
        control_frame = ttk.LabelFrame(market_frame, text="🎯 Market Controls", padding=10)
        control_frame.pack(fill='x', padx=10, pady=10)
        
        control_inner = ttk.Frame(control_frame)
        control_inner.pack(fill='x')
        
        ttk.Label(control_inner, text="Symbol:", font=('Segoe UI', 12, 'bold')).pack(side='left')
        self.market_symbol_var = tk.StringVar(value="btc_thb")
        symbol_combo = ttk.Combobox(control_inner, textvariable=self.market_symbol_var, 
                                   values=["btc_thb", "eth_thb", "ada_thb", "dot_thb", "xrp_thb"])
        symbol_combo.pack(side='left', padx=10)
        
        ttk.Button(control_inner, text="📊 Get Ticker",
                  command=self.get_ticker).pack(side='left', padx=5)
        ttk.Button(control_inner, text="📋 Orderbook",
                  command=self.get_orderbook).pack(side='left', padx=5)
        
        # Market data display
        data_frame = ttk.LabelFrame(market_frame, text="📊 Live Market Data", padding=10)
        data_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.market_text = scrolledtext.ScrolledText(data_frame, bg='#1e1e1e', fg='#00d4aa',
                                                   font=('Consolas', 11))
        self.market_text.pack(fill='both', expand=True)
        
    def setup_portfolio_tab(self, notebook):
        """Portfolio management and tracking"""
        portfolio_frame = ttk.Frame(notebook)
        notebook.add(portfolio_frame, text="💼 Portfolio")
        
        # Portfolio overview
        overview_frame = ttk.LabelFrame(portfolio_frame, text="💰 Portfolio Overview", padding=10)
        overview_frame.pack(fill='x', padx=10, pady=10)
        
        # Balance cards
        balance_frame = ttk.Frame(overview_frame)
        balance_frame.pack(fill='x')
        
        self.balance_cards = {}
        currencies = ["THB", "BTC", "ETH", "Total Value"]
        
        for i, currency in enumerate(currencies):
            card = ttk.Frame(balance_frame, relief='solid')
            card.grid(row=0, column=i, padx=10, pady=5, sticky='ew')
            balance_frame.grid_columnconfigure(i, weight=1)
            
            ttk.Label(card, text=f"💰 {currency}", font=('Segoe UI', 12, 'bold')).pack(pady=2)
            self.balance_cards[currency] = ttk.Label(card, text="Loading...", 
                                                   font=('Segoe UI', 16, 'bold'))
            self.balance_cards[currency].pack(pady=2)
        
        # Portfolio actions
        actions_frame = ttk.Frame(overview_frame)
        actions_frame.pack(fill='x', pady=(10, 0))
        
        ttk.Button(actions_frame, text="🔄 Refresh Portfolio",
                  command=self.refresh_portfolio).pack(side='left', padx=5)
        ttk.Button(actions_frame, text="📊 Get Full Balances",
                  command=self.get_balances).pack(side='left', padx=5)
        
        # Portfolio details
        details_frame = ttk.LabelFrame(portfolio_frame, text="📊 Detailed Information", padding=10)
        details_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.portfolio_text = scrolledtext.ScrolledText(details_frame, bg='#1e1e1e', fg='#ffffff',
                                                      font=('Consolas', 10))
        self.portfolio_text.pack(fill='both', expand=True)
        
    def setup_orders_tab(self, notebook):
        """Order management with advanced features"""
        orders_frame = ttk.Frame(notebook)
        notebook.add(orders_frame, text="📋 Order Management")
        
        # Order controls
        control_frame = ttk.LabelFrame(orders_frame, text="🎛️ Order Controls", padding=10)
        control_frame.pack(fill='x', padx=10, pady=10)
        
        control_inner = ttk.Frame(control_frame)
        control_inner.pack(fill='x')
        
        ttk.Label(control_inner, text="Symbol:", font=('Segoe UI', 12, 'bold')).pack(side='left')
        self.order_symbol_var = tk.StringVar(value="btc_thb")
        ttk.Combobox(control_inner, textvariable=self.order_symbol_var, 
                    values=["btc_thb", "eth_thb", "ada_thb"]).pack(side='left', padx=10)
        
        ttk.Button(control_inner, text="📋 Open Orders",
                  command=self.get_open_orders).pack(side='left', padx=5)
        
        # Order information display
        info_frame = ttk.LabelFrame(orders_frame, text="📊 Order Information", padding=10)
        info_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.order_text = scrolledtext.ScrolledText(info_frame, bg='#1e1e1e', fg='#ffffff',
                                                  font=('Consolas', 10))
        self.order_text.pack(fill='both', expand=True)
        
    def setup_status_bar(self, parent):
        """Modern status bar"""
        status_frame = ttk.Frame(parent)
        status_frame.pack(side='bottom', fill='x', pady=(10, 0))
        
        self.status_var = tk.StringVar()
        self.status_var.set("🟢 Ready - Bitkub AI Trading Bot")
        status_label = ttk.Label(status_frame, textvariable=self.status_var, relief='sunken')
        status_label.pack(side='left', fill='x', expand=True)
        
        # Connection indicator
        self.connection_indicator = ttk.Label(status_frame, text="⚫ Disconnected")
        self.connection_indicator.pack(side='right', padx=10)
        
    # === API และ Trading Functions ===
    
    def log_message(self, message):
        """Enhanced logging with colors and formatting"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        
        # Also update status bar
        self.update_status(f"Last action: {message[:50]}...")
        
    def update_status(self, message):
        """Update status bar with icon"""
        self.status_var.set(f"🟢 {message}")
        self.root.update_idletasks()
    
    def toggle_api_visibility(self):
        """Toggle API credentials visibility"""
        if self.api_key_entry.cget('show') == '*':
            self.api_key_entry.configure(show='')
            self.api_secret_entry.configure(show='')
        else:
            self.api_key_entry.configure(show='*')
            self.api_secret_entry.configure(show='*')
        
    def save_api_config(self):
        """Save API configuration with validation"""
        api_key = self.api_key_entry.get().strip()
        api_secret = self.api_secret_entry.get().strip()
        
        if api_key and api_secret:
            # สร้าง API Client ใหม่
            self.api_client = BitkubAPIClient(api_key, api_secret)
            
            self.log_message("✅ API configuration saved successfully")
            self.connection_status.configure(text="🟡 Configured - Testing...")
            self.connection_indicator.configure(text="🟡 Testing")
            
            # Test connection automatically
            threading.Thread(target=self.test_api_connection, daemon=True).start()
        else:
            messagebox.showwarning("Warning", "Please enter both API Key and Secret")
    
    def test_api_connection(self):
        """Test API connection with comprehensive checks"""
        def test():
            if not self.api_client:
                self.connection_status.configure(text="🔴 No API Configuration")
                self.connection_indicator.configure(text="🔴 No Config")
                return
            
            # Test API connection
            success = self.api_client.test_connection()
            
            if success:
                self.connection_status.configure(text="🟢 Connected & Authenticated")
                self.connection_indicator.configure(text="🟢 Connected")
                self.stats_labels["🤖 Connection"].configure(text="Online")
                self.log_message("✅ API connection test successful!")
                messagebox.showinfo("Success", "🎉 API connection successful!\nReady for trading.")
            else:
                self.connection_status.configure(text="🔴 Connection Failed")
                self.connection_indicator.configure(text="🔴 Failed")
                self.stats_labels["🤖 Connection"].configure(text="Offline")
                
        threading.Thread(target=test, daemon=True).start()
    
    def refresh_dashboard(self):
        """Refresh all dashboard data"""
        self.update_status("Refreshing dashboard...")
        
        def refresh():
            # Update metrics
            self.update_price_metrics()
            self.update_portfolio_metrics()
            self.update_status("Dashboard refreshed")
            
        threading.Thread(target=refresh, daemon=True).start()
    
    def update_price_metrics(self):
        """Update price metrics in dashboard"""
        if not self.api_client:
            return
            
        try:
            btc_data = self.api_client.get_ticker('btc_thb')
            eth_data = self.api_client.get_ticker('eth_thb')
            
            if btc_data and len(btc_data) > 0:
                btc_price = f"{float(btc_data[0]['last']):,.0f} THB"
                self.metric_cards["BTC Price"].configure(text=btc_price)
                
            if eth_data and len(eth_data) > 0:
                eth_price = f"{float(eth_data[0]['last']):,.0f} THB"
                self.metric_cards["ETH Price"].configure(text=eth_price)
                
        except Exception as e:
            self.log_message(f"❌ Error updating price metrics: {str(e)}")
    
    def update_portfolio_metrics(self):
        """Update portfolio value in dashboard"""
        if not self.api_client:
            return
            
        wallet = self.api_client.get_wallet()
        if wallet and wallet.get('error') == 0:
            balance_data = wallet.get('result', {})
            total_thb = balance_data.get('THB', 0)
            self.metric_cards["Portfolio Value"].configure(text=f"{total_thb:,.0f} THB")
            self.stats_labels["💰 Balance"].configure(text=f"{total_thb:,.0f} THB")
    
    def quick_balance_check(self):
        """Quick balance check for dashboard"""
        if not self.api_client:
            messagebox.showerror("Error", "Please configure API first!")
            return
            
        self.update_status("Checking balance...")
        
        def check():
            wallet = self.api_client.get_wallet()
            if wallet and wallet.get('error') == 0:
                self.update_portfolio_metrics()
                balance_data = wallet.get('result', {})
                
                balance_text = "💰 Account Balances:\n\n"
                for currency, amount in balance_data.items():
                    if amount > 0:
                        if currency == 'THB':
                            balance_text += f"{currency}: {amount:,.2f}\n"
                        else:
                            balance_text += f"{currency}: {amount:.8f}\n"
                
                messagebox.showinfo("Balance", balance_text)
            self.update_status("Ready")
            
        threading.Thread(target=check, daemon=True).start()
    
    # Enhanced Trading Functions
    def place_buy_order(self):
        """Enhanced buy order placement with validation"""
        try:
            if not self.api_client:
                messagebox.showerror("Error", "Please configure API first!")
                return
                
            symbol = self.buy_symbol_var.get()
            amount = float(self.buy_amount_var.get()) if self.buy_amount_var.get() else 0
            rate = float(self.buy_rate_var.get()) if self.buy_rate_var.get() else 0
            order_type = self.buy_type_var.get()
            
            if amount <= 0:
                messagebox.showerror("Error", "❌ Amount must be greater than 0")
                return
            
            # Confirmation dialog
            if not messagebox.askyesno("Confirm Order", 
                                     f"🟢 Place BUY order?\n\n"
                                     f"Symbol: {symbol.upper()}\n"
                                     f"Amount: {amount:,.2f} THB\n"
                                     f"Rate: {rate:,.2f}\n"
                                     f"Type: {order_type.upper()}"):
                return
            
            self.update_status("Placing buy order...")
            
            def place():
                result = self.api_client.place_buy_order(symbol, amount, rate, order_type)
                if result:
                    self.trading_text.insert(tk.END, f"\n🟢 === BUY ORDER RESULT ===\n")
                    self.trading_text.insert(tk.END, json.dumps(result, indent=2, ensure_ascii=False))
                    self.trading_text.insert(tk.END, f"\n{'='*60}\n")
                    self.trading_text.see(tk.END)
                    
                    if result.get('error') == 0:
                        messagebox.showinfo("Success", "🎉 Buy order placed successfully!")
                        self.buy_amount_var.set("")
                        self.buy_rate_var.set("")
                        self.total_trades += 1
                        self.stats_labels["📊 Trades"].configure(text=str(self.total_trades))
                
                self.update_status("Ready")
            
            threading.Thread(target=place, daemon=True).start()
            
        except ValueError:
            messagebox.showerror("Error", "❌ Please enter valid numeric values")
    
    def place_sell_order(self):
        """Enhanced sell order placement with validation"""
        try:
            if not self.api_client:
                messagebox.showerror("Error", "Please configure API first!")
                return
                
            symbol = self.sell_symbol_var.get()
            amount = float(self.sell_amount_var.get()) if self.sell_amount_var.get() else 0
            rate = float(self.sell_rate_var.get()) if self.sell_rate_var.get() else 0
            order_type = self.sell_type_var.get()
            
            if amount <= 0:
                messagebox.showerror("Error", "❌ Amount must be greater than 0")
                return
            
            # Confirmation dialog
            if not messagebox.askyesno("Confirm Order", 
                                     f"🔴 Place SELL order?\n\n"
                                     f"Symbol: {symbol.upper()}\n"
                                     f"Amount: {amount} {symbol.split('_')[0].upper()}\n"
                                     f"Rate: {rate:,.2f}\n"
                                     f"Type: {order_type.upper()}"):
                return
            
            self.update_status("Placing sell order...")
            
            def place():
                result = self.api_client.place_sell_order(symbol, amount, rate, order_type)
                if result:
                    self.trading_text.insert(tk.END, f"\n🔴 === SELL ORDER RESULT ===\n")
                    self.trading_text.insert(tk.END, json.dumps(result, indent=2, ensure_ascii=False))
                    self.trading_text.insert(tk.END, f"\n{'='*60}\n")
                    self.trading_text.see(tk.END)
                    
                    if result.get('error') == 0:
                        messagebox.showinfo("Success", "🎉 Sell order placed successfully!")
                        self.sell_amount_var.set("")
                        self.sell_rate_var.set("")
                        self.total_trades += 1
                        self.stats_labels["📊 Trades"].configure(text=str(self.total_trades))
                
                self.update_status("Ready")
            
            threading.Thread(target=place, daemon=True).start()
            
        except ValueError:
            messagebox.showerror("Error", "❌ Please enter valid numeric values")
    
    # Enhanced Market Data Functions
    def get_ticker(self):
        """Get ticker with enhanced formatting"""
        if not self.api_client:
            messagebox.showwarning("Warning", "Please configure API first!")
            return
            
        self.update_status("Getting ticker data...")
        
        def fetch():
            symbol = self.market_symbol_var.get()
            result = self.api_client.get_ticker(symbol)
            if result and len(result) > 0:
                self.market_text.delete(1.0, tk.END)
                self.market_text.insert(tk.END, f"📊 === TICKER DATA: {symbol.upper()} ===\n\n")
                
                ticker = result[0]
                formatted_data = f"""
🏷️  Symbol: {ticker.get('symbol', 'N/A')}
💰 Last Price: {float(ticker.get('last', 0)):,.2f} THB
📈 24h High: {float(ticker.get('high_24_hr', 0)):,.2f} THB
📉 24h Low: {float(ticker.get('low_24_hr', 0)):,.2f} THB
🔄 24h Change: {float(ticker.get('percent_change', 0)):+.2f}%
📊 Volume (Base): {float(ticker.get('base_volume', 0)):,.8f}
💵 Volume (Quote): {float(ticker.get('quote_volume', 0)):,.2f} THB
🟢 Highest Bid: {float(ticker.get('highest_bid', 0)):,.2f} THB
🔴 Lowest Ask: {float(ticker.get('lowest_ask', 0)):,.2f} THB
"""
                self.market_text.insert(tk.END, formatted_data)
            self.update_status("Ready")
        
        threading.Thread(target=fetch, daemon=True).start()
    
    def get_orderbook(self):
        """Get orderbook with enhanced formatting"""
        if not self.api_client:
            messagebox.showwarning("Warning", "Please configure API first!")
            return
            
        self.update_status("Getting orderbook...")
        
        def fetch():
            symbol = self.market_symbol_var.get()
            result = self.api_client.get_depth(symbol, limit=10)
            if result and 'result' in result:
                self.market_text.delete(1.0, tk.END)
                self.market_text.insert(tk.END, f"📋 === ORDERBOOK: {symbol.upper()} ===\n\n")
                
                asks = result['result'].get('asks', [])
                bids = result['result'].get('bids', [])
                
                self.market_text.insert(tk.END, "🔴 === SELL ORDERS (ASKS) ===\n")
                self.market_text.insert(tk.END, f"{'Price':>15} {'Amount':>15}\n")
                self.market_text.insert(tk.END, "-" * 35 + "\n")
                
                for ask in asks[:10]:
                    price, amount = ask[0], ask[1]
                    self.market_text.insert(tk.END, f"{price:>15,.2f} {amount:>15,.8f}\n")
                
                self.market_text.insert(tk.END, "\n🟢 === BUY ORDERS (BIDS) ===\n")
                self.market_text.insert(tk.END, f"{'Price':>15} {'Amount':>15}\n")
                self.market_text.insert(tk.END, "-" * 35 + "\n")
                
                for bid in bids[:10]:
                    price, amount = bid[0], bid[1]
                    self.market_text.insert(tk.END, f"{price:>15,.2f} {amount:>15,.8f}\n")
                        
            self.update_status("Ready")
        
        threading.Thread(target=fetch, daemon=True).start()
    
    # Portfolio Functions
    def refresh_portfolio(self):
        """Refresh portfolio with comprehensive data"""
        if not self.api_client:
            messagebox.showwarning("Warning", "Please configure API first!")
            return
            
        self.update_status("Refreshing portfolio...")
        
        def refresh():
            wallet = self.api_client.get_wallet()
            if wallet and wallet.get('error') == 0:
                balance_data = wallet.get('result', {})
                
                # Update balance cards
                for currency in ["THB", "BTC", "ETH"]:
                    balance = balance_data.get(currency, 0)
                    if currency == "THB":
                        self.balance_cards[currency].configure(text=f"{balance:,.2f}")
                    else:
                        self.balance_cards[currency].configure(text=f"{balance:.8f}")
                
                # Calculate total value
                total_value = balance_data.get('THB', 0)
                self.balance_cards["Total Value"].configure(text=f"{total_value:,.2f} THB")
                
                self.log_message("✅ Portfolio refreshed successfully")
            self.update_status("Ready")
        
        threading.Thread(target=refresh, daemon=True).start()
    
    def get_balances(self):
        """Get detailed balances"""
        if not self.api_client:
            messagebox.showwarning("Warning", "Please configure API first!")
            return
            
        self.update_status("Getting full balances...")
        
        def fetch():
            result = self.api_client.get_balances()
            if result:
                self.portfolio_text.delete(1.0, tk.END)
                self.portfolio_text.insert(tk.END, "💰 === FULL ACCOUNT BALANCES ===\n\n")
                
                if result.get('error') == 0:
                    balances = result.get('result', {})
                    self.portfolio_text.insert(tk.END, f"{'Currency':>12} {'Available':>18} {'Reserved':>18} {'Total':>18}\n")
                    self.portfolio_text.insert(tk.END, "-" * 70 + "\n")
                    
                    total_value_thb = 0
                    for currency, data in balances.items():
                        available = float(data.get('available', 0))
                        reserved = float(data.get('reserved', 0))
                        total = available + reserved
                        
                        if currency == 'THB':
                            total_value_thb += total
                        
                        if total > 0:  # Only show non-zero balances
                            self.portfolio_text.insert(tk.END, 
                                f"{currency:>12} {available:>18,.8f} {reserved:>18,.8f} {total:>18,.8f}\n")
                    
                    self.portfolio_text.insert(tk.END, f"\n💵 Total Portfolio Value: {total_value_thb:,.2f} THB\n")
                else:
                    self.portfolio_text.insert(tk.END, f"❌ Error: {result}")
                    
            self.update_status("Ready")
        
        threading.Thread(target=fetch, daemon=True).start()
    
    # Order Management Functions
    def get_open_orders(self):
        """Get open orders with enhanced formatting"""
        if not self.api_client:
            messagebox.showwarning("Warning", "Please configure API first!")
            return
            
        self.update_status("Getting open orders...")
        
        def fetch():
            symbol = self.order_symbol_var.get()
            result = self.api_client.get_open_orders(symbol)
            if result:
                self.order_text.delete(1.0, tk.END)
                self.order_text.insert(tk.END, f"📋 === OPEN ORDERS: {symbol.upper()} ===\n\n")
                
                if result.get('error') == 0:
                    orders = result.get('result', [])
                    
                    if orders:
                        self.order_text.insert(tk.END, f"{'ID':>12} {'Side':>6} {'Type':>8} {'Amount':>15} {'Rate':>15} {'Status':>10}\n")
                        self.order_text.insert(tk.END, "-" * 75 + "\n")
                        
                        for order in orders:
                            order_id = order.get('id', 'N/A')
                            side = order.get('side', 'N/A')
                            order_type = order.get('type', 'N/A')
                            amount = float(order.get('amount', 0))
                            rate = float(order.get('rate', 0))
                            
                            side_icon = "🟢" if side == "buy" else "🔴"
                            
                            self.order_text.insert(tk.END, 
                                f"{order_id:>12} {side_icon}{side:>5} {order_type:>8} {amount:>15,.8f} {rate:>15,.2f} {'Active':>10}\n")
                    else:
                        self.order_text.insert(tk.END, "✅ No open orders found\n")
                else:
                    self.order_text.insert(tk.END, f"❌ Error: {result}")
                    
            self.update_status("Ready")
        
        threading.Thread(target=fetch, daemon=True).start()


def main():
    """Main application entry point"""
    root = tk.Tk()
    
    # Set application properties
    root.configure(bg='#1e1e1e')
    
    # Try to set window icon
    try:
        # You can add an icon file here
        # root.iconbitmap('icon.ico')
        pass
    except:
        pass
    
    # Initialize the application
    app = BitkubAIGUI(root)
    
    # Center window on screen
    root.update_idletasks()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width // 2) - (1400 // 2)
    y = (screen_height // 2) - (900 // 2)
    root.geometry(f"1400x900+{x}+{y}")
    
    # Make window resizable
    root.minsize(1200, 800)
    
    # Add welcome message
    app.log_message("🚀 Welcome to Bitkub AI Trading Bot!")
    app.log_message("💡 Please configure your API credentials in the API Settings tab")
    app.log_message("📈 Ready for trading!")
    app.log_message("⚠️ Trading involves risk - please use with caution")
    
    if not MATPLOTLIB_AVAILABLE:
        app.log_message("📊 Chart features disabled - install matplotlib for charts")
    
    # Start the GUI
    try:
        root.mainloop()
    except KeyboardInterrupt:
        app.log_message("👋 Application shutting down...")
        root.quit()

if __name__ == "__main__":
    main()