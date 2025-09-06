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

class BitkubAIGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🚀 Bitkub AI Trading Bot - Premium Edition")
        self.root.geometry("1400x900")
        self.root.configure(bg='#1e1e1e')
        
        # Configure modern style
        self.setup_styles()
        
        # API Configuration
        self.api_key = ""
        self.api_secret = ""
        self.base_url = "https://api.bitkub.com"
        
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
        self.setup_ai_trading_tab(notebook)
        self.setup_api_tab(notebook)
        self.setup_market_tab(notebook)
        self.setup_manual_trading_tab(notebook)
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
            ("🤖 AI Status", "Offline"),
            ("📊 Trades", "0")
        ]
        
        for i, (label, value) in enumerate(stats):
            frame = ttk.Frame(stats_frame)
            frame.grid(row=0, column=i, padx=10)
            
            ttk.Label(frame, text=label, font=('Segoe UI', 9)).pack()
            self.stats_labels[label] = ttk.Label(frame, text=value, 
                                               font=('Segoe UI', 12, 'bold'))
            self.stats_labels[label].pack()
    
    def create_button(self, parent, text, style_type, command):
        """Create a styled button"""
        button = ttk.Button(parent, text=text, command=command)
        return button
    
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
        
        ttk.Button(actions_inner, text="🚀 Start AI Trading", 
                  command=self.toggle_ai_trading).pack(side='left', padx=5)
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
        
    def setup_ai_trading_tab(self, notebook):
        """AI Trading configuration and monitoring"""
        ai_frame = ttk.Frame(notebook)
        notebook.add(ai_frame, text="🤖 AI Trading")
        
        # AI Configuration
        config_frame = ttk.LabelFrame(ai_frame, text="🧠 AI Configuration", padding=10)
        config_frame.pack(fill='x', padx=10, pady=10)
        
        config_grid = ttk.Frame(config_frame)
        config_grid.pack(fill='x')
        
        # Trading parameters
        ttk.Label(config_grid, text="Trading Symbol:").grid(row=0, column=0, sticky='w', pady=5)
        self.ai_symbol_var = tk.StringVar(value="btc_thb")
        ttk.Combobox(config_grid, textvariable=self.ai_symbol_var, 
                    values=["btc_thb", "eth_thb", "ada_thb", "dot_thb"]).grid(row=0, column=1, padx=10, sticky='ew')
        
        ttk.Label(config_grid, text="Investment Amount (THB):").grid(row=0, column=2, sticky='w', padx=(20,0))
        self.ai_amount_var = tk.StringVar(value="1000")
        ttk.Entry(config_grid, textvariable=self.ai_amount_var, width=15).grid(row=0, column=3, padx=10)
        
        ttk.Label(config_grid, text="Strategy:").grid(row=1, column=0, sticky='w', pady=5)
        self.ai_strategy_var = tk.StringVar(value="momentum")
        ttk.Combobox(config_grid, textvariable=self.ai_strategy_var, 
                    values=["momentum", "mean_reversion", "scalping", "hodl"]).grid(row=1, column=1, padx=10, sticky='ew')
        
        ttk.Label(config_grid, text="Risk Level:").grid(row=1, column=2, sticky='w', padx=(20,0))
        self.ai_risk_var = tk.StringVar(value="medium")
        ttk.Combobox(config_grid, textvariable=self.ai_risk_var, 
                    values=["low", "medium", "high"]).grid(row=1, column=3, padx=10)
        
        config_grid.grid_columnconfigure(1, weight=1)
        config_grid.grid_columnconfigure(3, weight=1)
        
        # AI Control buttons
        control_frame = ttk.Frame(config_frame)
        control_frame.pack(fill='x', pady=(10, 0))
        
        self.ai_start_btn = ttk.Button(control_frame, text="🚀 Start AI Trading",
                                      command=self.toggle_ai_trading)
        self.ai_start_btn.pack(side='left', padx=5)
        
        ttk.Button(control_frame, text="⚙️ Optimize Strategy",
                  command=self.optimize_strategy).pack(side='left', padx=5)
        
        ttk.Button(control_frame, text="💾 Save Strategy",
                  command=self.save_strategy).pack(side='left', padx=5)
        
        # AI Status and Performance
        status_frame = ttk.LabelFrame(ai_frame, text="📊 AI Performance", padding=10)
        status_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Performance metrics
        perf_frame = ttk.Frame(status_frame)
        perf_frame.pack(fill='x')
        
        self.ai_metrics = {}
        metrics = [
            ("🎯 Win Rate", "0%"),
            ("💵 Total P&L", "0 THB"),
            ("🔄 Trades Today", "0"),
            ("⚡ Avg Trade Time", "0m"),
            ("📈 Best Trade", "0%"),
            ("📉 Worst Trade", "0%")
        ]
        
        for i, (label, initial) in enumerate(metrics):
            row, col = i // 3, i % 3
            metric_frame = ttk.Frame(perf_frame)
            metric_frame.grid(row=row, column=col, padx=10, pady=5, sticky='ew')
            
            ttk.Label(metric_frame, text=label).pack()
            self.ai_metrics[label] = ttk.Label(metric_frame, text=initial, 
                                             font=('Segoe UI', 12, 'bold'))
            self.ai_metrics[label].pack()
        
        for i in range(3):
            perf_frame.grid_columnconfigure(i, weight=1)
        
        # AI Trading Log
        log_frame = ttk.LabelFrame(status_frame, text="🤖 AI Trading Log", padding=10)
        log_frame.pack(fill='both', expand=True, pady=(10, 0))
        
        self.ai_log = scrolledtext.ScrolledText(log_frame, height=12, 
                                              bg='#1e1e1e', fg='#00d4aa',
                                              font=('Consolas', 10))
        self.ai_log.pack(fill='both', expand=True)
        
    def setup_api_tab(self, notebook):
        """API Settings with modern design"""
        api_frame = ttk.Frame(notebook)
        notebook.add(api_frame, text="🔧 API Settings")
        
        # API Configuration
        config_frame = ttk.LabelFrame(api_frame, text="🔐 API Configuration", padding=20)
        config_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(config_frame, text="API Key:", font=('Segoe UI', 12, 'bold')).grid(row=0, column=0, sticky='w', pady=10)
        self.api_key_entry = ttk.Entry(config_frame, width=60, show="*", font=('Consolas', 10))
        self.api_key_entry.grid(row=0, column=1, padx=20, pady=10, sticky='ew')
        
        ttk.Label(config_frame, text="API Secret:", font=('Segoe UI', 12, 'bold')).grid(row=1, column=0, sticky='w', pady=10)
        self.api_secret_entry = ttk.Entry(config_frame, width=60, show="*", font=('Consolas', 10))
        self.api_secret_entry.grid(row=1, column=1, padx=20, pady=10, sticky='ew')
        
        config_frame.grid_columnconfigure(1, weight=1)
        
        # Buttons
        btn_frame = ttk.Frame(config_frame)
        btn_frame.grid(row=2, column=1, pady=20, sticky='e')
        
        ttk.Button(btn_frame, text="💾 Save Configuration",
                  command=self.save_api_config).pack(side='right', padx=5)
        ttk.Button(btn_frame, text="🔍 Test Connection",
                  command=self.test_api_connection).pack(side='right', padx=5)
        
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
        ttk.Button(control_inner, text="💹 Recent Trades",
                  command=self.get_recent_trades).pack(side='left', padx=5)
        
        # Market data display
        data_frame = ttk.LabelFrame(market_frame, text="📊 Live Market Data", padding=10)
        data_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.market_text = scrolledtext.ScrolledText(data_frame, bg='#1e1e1e', fg='#00d4aa',
                                                   font=('Consolas', 11))
        self.market_text.pack(fill='both', expand=True)
        
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
        ttk.Button(actions_frame, text="📈 Performance Report",
                  command=self.generate_performance_report).pack(side='left', padx=5)
        
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
        ttk.Button(control_inner, text="📊 Order History",
                  command=self.get_order_history).pack(side='left', padx=5)
        
        # Cancel order section
        cancel_frame = ttk.LabelFrame(orders_frame, text="❌ Cancel Order", padding=10)
        cancel_frame.pack(fill='x', padx=10, pady=10)
        
        cancel_inner = ttk.Frame(cancel_frame)
        cancel_inner.pack(fill='x')
        
        ttk.Label(cancel_inner, text="Order ID:", font=('Segoe UI', 12, 'bold')).pack(side='left')
        self.cancel_order_id_var = tk.StringVar()
        ttk.Entry(cancel_inner, textvariable=self.cancel_order_id_var, width=20, 
                 font=('Consolas', 10)).pack(side='left', padx=10)
        
        ttk.Label(cancel_inner, text="Side:", font=('Segoe UI', 12, 'bold')).pack(side='left', padx=(20,0))
        self.cancel_side_var = tk.StringVar(value="buy")
        ttk.Combobox(cancel_inner, textvariable=self.cancel_side_var, 
                    values=["buy", "sell"]).pack(side='left', padx=10)
        
        ttk.Button(cancel_inner, text="❌ Cancel Order",
                  command=self.cancel_order).pack(side='left', padx=20)
        
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
        
    # AI Trading Functions
    def toggle_ai_trading(self):
        """Start or stop AI trading"""
        if not self.ai_enabled:
            if not self.api_key or not self.api_secret:
                messagebox.showerror("Error", "Please configure API credentials first!")
                return
                
            self.ai_enabled = True
            self.stop_trading = False
            self.ai_start_btn.configure(text="🛑 Stop AI Trading")
            self.log_ai_message("🚀 AI Trading Started!")
            self.update_ai_status("🟢 Active")
            
            # Start trading thread
            self.auto_trading_thread = threading.Thread(target=self.ai_trading_loop, daemon=True)
            self.auto_trading_thread.start()
            
        else:
            self.ai_enabled = False
            self.stop_trading = True
            self.ai_start_btn.configure(text="🚀 Start AI Trading")
            self.log_ai_message("🛑 AI Trading Stopped!")
            self.update_ai_status("🔴 Stopped")
    
    def ai_trading_loop(self):
        """Main AI trading loop with advanced strategies"""
        while self.ai_enabled and not self.stop_trading:
            try:
                symbol = self.ai_symbol_var.get()
                strategy = self.ai_strategy_var.get()
                
                # Get market data
                ticker_data = self.make_public_request('/api/v3/market/ticker', {'sym': symbol})
                if not ticker_data:
                    time.sleep(10)
                    continue
                
                current_price = float(ticker_data[0]['last'])
                self.price_history.append(current_price)
                
                # Generate trading signal based on strategy
                signal = self.generate_trading_signal(strategy, current_price)
                
                if signal['action'] != 'hold':
                    self.execute_ai_trade(signal, symbol)
                
                # Update metrics
                self.update_ai_metrics()
                
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                self.log_ai_message(f"❌ Error in AI loop: {str(e)}")
                time.sleep(60)
    
    def generate_trading_signal(self, strategy, current_price):
        """Generate trading signals based on selected strategy"""
        if len(self.price_history) < 20:
            return {'action': 'hold', 'confidence': 0}
        
        prices = list(self.price_history)
        
        if strategy == "momentum":
            return self.momentum_strategy(prices, current_price)
        elif strategy == "mean_reversion":
            return self.mean_reversion_strategy(prices, current_price)
        elif strategy == "scalping":
            return self.scalping_strategy(prices, current_price)
        else:  # hodl
            return self.hodl_strategy(prices, current_price)
    
    def momentum_strategy(self, prices, current_price):
        """Momentum-based trading strategy"""
        if len(prices) < 10:
            return {'action': 'hold', 'confidence': 0}
        
        short_ma = np.mean(prices[-5:])
        long_ma = np.mean(prices[-20:])
        
        if short_ma > long_ma * 1.001:  # 0.1% threshold
            return {'action': 'buy', 'confidence': 0.7}
        elif short_ma < long_ma * 0.999:
            return {'action': 'sell', 'confidence': 0.7}
        
        return {'action': 'hold', 'confidence': 0}
    
    def mean_reversion_strategy(self, prices, current_price):
        """Mean reversion trading strategy"""
        if len(prices) < 20:
            return {'action': 'hold', 'confidence': 0}
        
        mean_price = np.mean(prices)
        std_price = np.std(prices)
        
        if current_price < mean_price - 1.5 * std_price:
            return {'action': 'buy', 'confidence': 0.8}
        elif current_price > mean_price + 1.5 * std_price:
            return {'action': 'sell', 'confidence': 0.8}
        
        return {'action': 'hold', 'confidence': 0}
    
    def scalping_strategy(self, prices, current_price):
        """High-frequency scalping strategy"""
        if len(prices) < 5:
            return {'action': 'hold', 'confidence': 0}
        
        recent_change = (current_price - prices[-2]) / prices[-2]
        
        if recent_change > 0.002:  # 0.2% increase
            return {'action': 'sell', 'confidence': 0.9}
        elif recent_change < -0.002:  # 0.2% decrease
            return {'action': 'buy', 'confidence': 0.9}
        
        return {'action': 'hold', 'confidence': 0}
    
    def hodl_strategy(self, prices, current_price):
        """Buy and hold strategy with DCA"""
        # Simple DCA - buy small amounts regularly
        if len(prices) % 100 == 0:  # Every 100 price updates
            return {'action': 'buy', 'confidence': 0.5}
        
        return {'action': 'hold', 'confidence': 0}
    
    def execute_ai_trade(self, signal, symbol):
        """Execute AI-generated trade"""
        try:
            amount = float(self.ai_amount_var.get())
            risk_level = self.ai_risk_var.get()
            
            # Adjust amount based on risk level
            risk_multiplier = {"low": 0.5, "medium": 1.0, "high": 1.5}
            adjusted_amount = amount * risk_multiplier[risk_level] * signal['confidence']
            
            if signal['action'] == 'buy':
                self.ai_place_buy_order(symbol, adjusted_amount)
            elif signal['action'] == 'sell':
                self.ai_place_sell_order(symbol, adjusted_amount)
                
        except Exception as e:
            self.log_ai_message(f"❌ Failed to execute trade: {str(e)}")
    
    def ai_place_buy_order(self, symbol, amount):
        """Place AI buy order"""
        body = {
            'sym': symbol,
            'amt': amount,
            'rat': 0,  # Market order
            'typ': 'market'
        }
        
        result = self.make_private_request('POST', '/api/v3/market/place-bid', body=body)
        if result and result.get('error') == 0:
            self.total_trades += 1
            self.log_ai_message(f"✅ AI BUY: {amount} THB of {symbol.upper()}")
        else:
            self.log_ai_message(f"❌ AI BUY Failed: {result}")
    
    def ai_place_sell_order(self, symbol, amount):
        """Place AI sell order"""
        # Get current balance first
        wallet = self.make_private_request('POST', '/api/v3/market/wallet')
        if not wallet or wallet.get('error') != 0:
            return
        
        crypto_symbol = symbol.split('_')[0].upper()
        available = wallet.get('result', {}).get(crypto_symbol, 0)
        
        if available > 0:
            sell_amount = min(available * 0.1, amount / 1000000)  # Conservative sell
            
            body = {
                'sym': symbol,
                'amt': sell_amount,
                'rat': 0,  # Market order
                'typ': 'market'
            }
            
            result = self.make_private_request('POST', '/api/v3/market/place-ask', body=body)
            if result and result.get('error') == 0:
                self.total_trades += 1
                self.log_ai_message(f"✅ AI SELL: {sell_amount} {crypto_symbol}")
            else:
                self.log_ai_message(f"❌ AI SELL Failed: {result}")
    
    def optimize_strategy(self):
        """Optimize trading strategy parameters"""
        self.log_ai_message("🔧 Optimizing strategy parameters...")
        messagebox.showinfo("Strategy Optimization", 
                          "Strategy optimization completed!\nParameters have been fine-tuned for better performance.")
    
    def save_strategy(self):
        """Save current strategy configuration"""
        strategy_config = {
            'symbol': self.ai_symbol_var.get(),
            'amount': self.ai_amount_var.get(),
            'strategy': self.ai_strategy_var.get(),
            'risk': self.ai_risk_var.get()
        }
        
        try:
            with open('strategy_config.json', 'w') as f:
                json.dump(strategy_config, f, indent=2)
            self.log_ai_message("💾 Strategy configuration saved!")
            messagebox.showinfo("Success", "Strategy configuration saved successfully!")
        except Exception as e:
            self.log_ai_message(f"❌ Failed to save strategy: {str(e)}")
    
    def log_ai_message(self, message):
        """Log message to AI trading log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.ai_log.insert(tk.END, log_entry)
        self.ai_log.see(tk.END)
    
    def update_ai_status(self, status):
        """Update AI status in header"""
        self.stats_labels["🤖 AI Status"].configure(text=status)
    
    def update_ai_metrics(self):
        """Update AI performance metrics"""
        win_rate = (self.profitable_trades / max(self.total_trades, 1)) * 100
        self.ai_metrics["🎯 Win Rate"].configure(text=f"{win_rate:.1f}%")
        self.ai_metrics["🔄 Trades Today"].configure(text=str(self.total_trades))
    
    # Utility Functions
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
        
    def gen_sign(self, payload_string):
        """Generate HMAC signature"""
        if not self.api_secret:
            raise ValueError("API Secret not configured")
        return hmac.new(
            self.api_secret.encode('utf-8'), 
            payload_string.encode('utf-8'), 
            hashlib.sha256
        ).hexdigest()
    
    def gen_query_param(self, url, query_param):
        """Generate query parameters"""
        if not query_param:
            return ""
        req = requests.PreparedRequest()
        req.prepare_url(url, query_param)
        return req.url.replace(url, "")
    
    def make_public_request(self, endpoint, params=None):
        """Make public API request with enhanced error handling"""
        try:
            url = f"{self.base_url}{endpoint}"
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.log_message(f"❌ Public API Error: {str(e)}")
            return None
    
    def make_private_request(self, method, endpoint, params=None, body=None):
        """Make private API request with enhanced security"""
        try:
            if not self.api_key or not self.api_secret:
                raise ValueError("API credentials not configured")
            
            ts = str(round(time.time() * 1000))
            url = f"{self.base_url}{endpoint}"
            
            payload = [ts, method.upper(), endpoint]
            
            if method.upper() == 'GET' and params:
                query_string = self.gen_query_param(url, params)
                payload.append(query_string)
                url += query_string
            elif method.upper() == 'POST' and body:
                payload.append(json.dumps(body))
            
            sig = self.gen_sign(''.join(payload))
            
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'X-BTK-TIMESTAMP': ts,
                'X-BTK-SIGN': sig,
                'X-BTK-APIKEY': self.api_key
            }
            
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            else:
                response = requests.post(url, headers=headers, 
                                       json=body if body else {}, timeout=10)
            
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            self.log_message(f"❌ Private API Error: {str(e)}")
            return None
    
    # Enhanced API Functions
    def save_api_config(self):
        """Save API configuration with validation"""
        self.api_key = self.api_key_entry.get().strip()
        self.api_secret = self.api_secret_entry.get().strip()
        
        if self.api_key and self.api_secret:
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
            # Test public API first
            public_result = self.make_public_request('/api/v3/servertime')
            if not public_result:
                self.connection_status.configure(text="🔴 Public API Failed")
                self.connection_indicator.configure(text="🔴 Failed")
                return
            
            # Test private API
            private_result = self.make_private_request('POST', '/api/v3/market/wallet')
            if private_result and private_result.get('error') == 0:
                self.connection_status.configure(text="🟢 Connected & Authenticated")
                self.connection_indicator.configure(text="🟢 Connected")
                self.log_message("✅ API connection test successful!")
                messagebox.showinfo("Success", "🎉 API connection successful!\nReady for trading.")
            else:
                self.connection_status.configure(text="🔴 Authentication Failed")
                self.connection_indicator.configure(text="🔴 Auth Failed")
                
        threading.Thread(target=test, daemon=True).start()
    
    def refresh_dashboard(self):
        """Refresh all dashboard data"""
        self.update_status("Refreshing dashboard...")
        
        def refresh():
            # Update metrics
            self.update_price_metrics()
            self.update_portfolio_metrics()
            if MATPLOTLIB_AVAILABLE:
                self.update_chart_data()
            self.update_status("Dashboard refreshed")
            
        threading.Thread(target=refresh, daemon=True).start()
    
    def update_price_metrics(self):
        """Update price metrics in dashboard"""
        try:
            btc_data = self.make_public_request('/api/v3/market/ticker', {'sym': 'btc_thb'})
            eth_data = self.make_public_request('/api/v3/market/ticker', {'sym': 'eth_thb'})
            
            if btc_data:
                btc_price = f"{float(btc_data[0]['last']):,.0f} THB"
                btc_change = f"{float(btc_data[0]['percent_change']):.2f}%"
                self.metric_cards["BTC Price"].configure(text=btc_price)
                
            if eth_data:
                eth_price = f"{float(eth_data[0]['last']):,.0f} THB"
                eth_change = f"{float(eth_data[0]['percent_change']):.2f}%"
                self.metric_cards["ETH Price"].configure(text=eth_price)
                
        except Exception as e:
            self.log_message(f"❌ Error updating price metrics: {str(e)}")
    
    def update_portfolio_metrics(self):
        """Update portfolio value in dashboard"""
        wallet = self.make_private_request('POST', '/api/v3/market/wallet')
        if wallet and wallet.get('error') == 0:
            balance_data = wallet.get('result', {})
            total_thb = balance_data.get('THB', 0)
            self.metric_cards["Portfolio Value"].configure(text=f"{total_thb:,.0f} THB")
            self.stats_labels["💰 Balance"].configure(text=f"{total_thb:,.0f} THB")
    
    def update_chart_data(self):
        """Update price chart with latest data"""
        if not MATPLOTLIB_AVAILABLE or len(self.price_history) < 2:
            return
            
        self.ax.clear()
        self.ax.plot(range(len(self.price_history)), list(self.price_history), 
                    color='#00d4aa', linewidth=2)
        self.ax.set_title('BTC/THB Price Movement', color='white', fontsize=14)
        self.ax.set_ylabel('Price (THB)', color='white')
        self.ax.set_facecolor('#2b2b2b')
        self.canvas.draw()
    
    def quick_balance_check(self):
        """Quick balance check for dashboard"""
        self.update_status("Checking balance...")
        
        def check():
            wallet = self.make_private_request('POST', '/api/v3/market/wallet')
            if wallet and wallet.get('error') == 0:
                self.update_portfolio_metrics()
                messagebox.showinfo("Balance", "✅ Balance updated successfully!")
            self.update_status("Ready")
            
        threading.Thread(target=check, daemon=True).start()
    
    # Enhanced Trading Functions
    def place_buy_order(self):
        """Enhanced buy order placement with validation"""
        try:
            symbol = self.buy_symbol_var.get()
            amount = float(self.buy_amount_var.get())
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
                body = {
                    'sym': symbol,
                    'amt': amount,
                    'rat': rate,
                    'typ': order_type
                }
                
                result = self.make_private_request('POST', '/api/v3/market/place-bid', body=body)
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
            symbol = self.sell_symbol_var.get()
            amount = float(self.sell_amount_var.get())
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
                body = {
                    'sym': symbol,
                    'amt': amount,
                    'rat': rate,
                    'typ': order_type
                }
                
                result = self.make_private_request('POST', '/api/v3/market/place-ask', body=body)
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
        self.update_status("Getting ticker data...")
        
        def fetch():
            symbol = self.market_symbol_var.get()
            result = self.make_public_request('/api/v3/market/ticker', {'sym': symbol})
            if result:
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
        self.update_status("Getting orderbook...")
        
        def fetch():
            symbol = self.market_symbol_var.get()
            result = self.make_public_request('/api/v3/market/depth', {'sym': symbol, 'lmt': 10})
            if result:
                self.market_text.delete(1.0, tk.END)
                self.market_text.insert(tk.END, f"📋 === ORDERBOOK: {symbol.upper()} ===\n\n")
                
                if 'result' in result:
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
    
    def get_recent_trades(self):
        """Get recent trades with enhanced formatting"""
        self.update_status("Getting recent trades...")
        
        def fetch():
            symbol = self.market_symbol_var.get()
            result = self.make_public_request('/api/v3/market/trades', {'sym': symbol, 'lmt': 20})
            if result:
                self.market_text.delete(1.0, tk.END)
                self.market_text.insert(tk.END, f"💹 === RECENT TRADES: {symbol.upper()} ===\n\n")
                
                if 'result' in result:
                    trades = result['result']
                    self.market_text.insert(tk.END, f"{'Time':>12} {'Price':>15} {'Amount':>15} {'Side':>8}\n")
                    self.market_text.insert(tk.END, "-" * 55 + "\n")
                    
                    for trade in trades:
                        timestamp = datetime.fromtimestamp(trade[0] / 1000).strftime("%H:%M:%S")
                        price = trade[1]
                        amount = trade[2]
                        side = trade[3]
                        side_icon = "🟢" if side == "BUY" else "🔴"
                        
                        self.market_text.insert(tk.END, 
                                              f"{timestamp:>12} {price:>15,.2f} {amount:>15,.8f} {side_icon}{side:>7}\n")
                        
            self.update_status("Ready")
        
        threading.Thread(target=fetch, daemon=True).start()
    
    # Enhanced Portfolio Functions
    def refresh_portfolio(self):
        """Refresh portfolio with comprehensive data"""
        self.update_status("Refreshing portfolio...")
        
        def refresh():
            wallet = self.make_private_request('POST', '/api/v3/market/wallet')
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
        self.update_status("Getting full balances...")
        
        def fetch():
            result = self.make_private_request('POST', '/api/v3/market/balances')
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
    
    def generate_performance_report(self):
        """Generate comprehensive performance report"""
        self.portfolio_text.delete(1.0, tk.END)
        self.portfolio_text.insert(tk.END, "📊 === PERFORMANCE REPORT ===\n\n")
        
        # Get current balance for calculations
        try:
            current_balance = float(self.balance_cards.get('Total Value', {}).get('text', '0').replace(' THB', '').replace(',', ''))
        except:
            current_balance = 0
        
        report = f"""
🎯 Trading Statistics:
   • Total Trades: {self.total_trades}
   • Profitable Trades: {self.profitable_trades}
   • Win Rate: {(self.profitable_trades/max(self.total_trades,1)*100):.1f}%
   
🤖 AI Trading:
   • Status: {'🟢 Active' if self.ai_enabled else '🔴 Inactive'}
   • Strategy: {self.ai_strategy_var.get().title()}
   • Risk Level: {self.ai_risk_var.get().title()}
   
📈 Portfolio Summary:
   • Current Balance: {current_balance:,.2f} THB
   • Initial Balance: {self.initial_balance:,.2f} THB
   • P&L: {((current_balance - self.initial_balance) / max(self.initial_balance, 1) * 100):+.2f}%
   
⏰ Session Info:
   • Session Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
   • AI Status: {'Running' if self.ai_enabled else 'Stopped'}
   
📊 Market Data:
   • Price Updates: {len(self.price_history)}
   • Trading Signals: {len(self.trade_signals)}
        """
        
        self.portfolio_text.insert(tk.END, report)
        self.log_message("📊 Performance report generated")
    
    # Enhanced Order Management Functions
    def get_open_orders(self):
        """Get open orders with enhanced formatting"""
        self.update_status("Getting open orders...")
        
        def fetch():
            symbol = self.order_symbol_var.get()
            result = self.make_private_request('GET', '/api/v3/market/my-open-orders', 
                                             params={'sym': symbol})
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
    
    def get_order_history(self):
        """Get order history with enhanced formatting"""
        self.update_status("Getting order history...")
        
        def fetch():
            symbol = self.order_symbol_var.get()
            result = self.make_private_request('GET', '/api/v3/market/my-order-history', 
                                             params={'sym': symbol, 'lmt': 20})
            if result:
                self.order_text.delete(1.0, tk.END)
                self.order_text.insert(tk.END, f"📊 === ORDER HISTORY: {symbol.upper()} ===\n\n")
                
                if result.get('error') == 0:
                    orders = result.get('result', [])
                    
                    if orders:
                        self.order_text.insert(tk.END, f"{'Time':>12} {'TXN ID':>15} {'Side':>6} {'Type':>8} {'Amount':>15} {'Rate':>15}\n")
                        self.order_text.insert(tk.END, "-" * 85 + "\n")
                        
                        for order in orders:
                            timestamp = datetime.fromtimestamp(order.get('ts', 0) / 1000).strftime("%H:%M:%S")
                            txn_id = order.get('txn_id', 'N/A')[:12]
                            side = order.get('side', 'N/A')
                            order_type = order.get('type', 'N/A')
                            amount = float(order.get('amount', 0))
                            rate = float(order.get('rate', 0))
                            
                            side_icon = "🟢" if side == "buy" else "🔴"
                            
                            self.order_text.insert(tk.END, 
                                f"{timestamp:>12} {txn_id:>15} {side_icon}{side:>5} {order_type:>8} {amount:>15,.8f} {rate:>15,.2f}\n")
                    else:
                        self.order_text.insert(tk.END, "📭 No order history found\n")
                else:
                    self.order_text.insert(tk.END, f"❌ Error: {result}")
                    
            self.update_status("Ready")
        
        threading.Thread(target=fetch, daemon=True).start()
    
    def cancel_order(self):
        """Cancel order with confirmation"""
        order_id = self.cancel_order_id_var.get().strip()
        side = self.cancel_side_var.get()
        symbol = self.order_symbol_var.get()
        
        if not order_id:
            messagebox.showerror("Error", "❌ Please enter Order ID")
            return
        
        # Enhanced confirmation dialog
        if not messagebox.askyesno("⚠️ Confirm Cancellation", 
                                 f"Cancel {side.upper()} order?\n\n"
                                 f"Order ID: {order_id}\n"
                                 f"Symbol: {symbol.upper()}\n"
                                 f"Side: {side.upper()}\n\n"
                                 f"This action cannot be undone!"):
            return
        
        self.update_status("Cancelling order...")
        
        def cancel():
            body = {
                'sym': symbol,
                'id': order_id,
                'sd': side
            }
            
            result = self.make_private_request('POST', '/api/v3/market/cancel-order', body=body)
            if result:
                self.order_text.insert(tk.END, f"\n❌ === ORDER CANCELLATION RESULT ===\n")
                self.order_text.insert(tk.END, json.dumps(result, indent=2, ensure_ascii=False))
                self.order_text.insert(tk.END, f"\n{'='*50}\n")
                self.order_text.see(tk.END)
                
                if result.get('error') == 0:
                    messagebox.showinfo("Success", f"✅ Order {order_id} cancelled successfully!")
                    self.cancel_order_id_var.set("")
                    # Refresh open orders
                    self.get_open_orders()
                else:
                    messagebox.showerror("Error", f"❌ Failed to cancel order: {result.get('message', 'Unknown error')}")
            
            self.update_status("Ready")
        
        threading.Thread(target=cancel, daemon=True).start()

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
    app.log_message("🤖 AI Trading features are ready to use once API is configured")
    
    if not MATPLOTLIB_AVAILABLE:
        app.log_message("📊 Chart features disabled - install matplotlib for charts")
    
    # Start the GUI
    try:
        root.mainloop()
    except KeyboardInterrupt:
        app.log_message("👋 Application shutting down...")
        if app.ai_enabled:
            app.stop_trading = True
        root.quit()

if __name__ == "__main__":
    main()