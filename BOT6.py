import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import os
import configparser
from binance.client import Client
from binance.enums import *
import threading
import time
import json
import sqlite3
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import warnings

warnings.filterwarnings('ignore')


# ===== Configuration Management =====
class ConfigManager:
    def __init__(self):
        self.config_file = "config.ini"
        self.config = configparser.ConfigParser()
        self.load_config()

    def load_config(self):
        if os.path.exists(self.config_file):
            self.config.read(self.config_file)
        else:
            self.create_default_config()

    def create_default_config(self):
        self.config['API'] = {
            'api_key': '',
            'api_secret': '',
            'testnet': 'True'
        }
        self.config['TRADING'] = {
            'risk_percent': '2.0',
            'stop_loss_percent': '1.5',
            'take_profit_percent': '3.0',
            'max_positions': '3',
            'min_volume': '1000000',
            'rsi_oversold': '30',
            'rsi_overbought': '70',
            'enable_notifications': 'True'
        }
        self.save_config()

    def save_config(self):
        with open(self.config_file, 'w') as f:
            self.config.write(f)

    def get_api_credentials(self):
        return (
            self.config.get('API', 'api_key', fallback=''),
            self.config.get('API', 'api_secret', fallback=''),
            self.config.getboolean('API', 'testnet', fallback=True)
        )

    def set_api_credentials(self, api_key, api_secret, testnet=True):
        self.config['API']['api_key'] = api_key
        self.config['API']['api_secret'] = api_secret
        self.config['API']['testnet'] = str(testnet)
        self.save_config()


# ===== Enhanced Logging System =====
class TradingLogger:
    def __init__(self, ui_callback=None):
        self.logs = []
        self.ui_callback = ui_callback
        self.log_types = {
            'INFO': {'color': '#74b9ff', 'icon': 'ℹ️'},
            'SUCCESS': {'color': '#00ff88', 'icon': '✅'},
            'WARNING': {'color': '#ffeaa7', 'icon': '⚠️'},
            'ERROR': {'color': '#ff4757', 'icon': '❌'},
            'TRADE': {'color': '#00ff88', 'icon': '📈'},
            'AUTO': {'color': '#a29bfe', 'icon': '🤖'},
            'SIGNAL': {'color': '#fd79a8', 'icon': '📊'}
        }

    def log(self, message, log_type='INFO', details=None):
        timestamp = datetime.now().strftime("%H:%M:%S")
        icon = self.log_types.get(log_type, {}).get('icon', '📝')

        log_entry = {
            'timestamp': timestamp,
            'type': log_type,
            'message': message,
            'details': details,
            'icon': icon
        }

        self.logs.insert(0, log_entry)
        if len(self.logs) > 100:
            self.logs.pop()

        if self.ui_callback:
            self.ui_callback(log_entry)

        print(f"[{timestamp}] {icon} {log_type}: {message}")

    def get_recent_logs(self, count=20):
        return self.logs[:count]


# ===== Helper Functions =====
def calculate_rsi(prices, period=14):
    if len(prices) < period + 1:
        return [50] * len(prices)

    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)

    avg_gains = [np.mean(gains[:period])]
    avg_losses = [np.mean(losses[:period])]

    for i in range(period, len(deltas)):
        avg_gains.append((avg_gains[-1] * (period - 1) + gains[i]) / period)
        avg_losses.append((avg_losses[-1] * (period - 1) + losses[i]) / period)

    rs = np.array(avg_gains) / np.array(avg_losses)
    rsi = 100 - (100 / (1 + rs))

    return [50] + list(rsi)


def calculate_ema(prices, period):
    if len(prices) < period:
        return [prices[0]] * len(prices)

    alpha = 2 / (period + 1)
    ema = [prices[0]]

    for price in prices[1:]:
        ema.append(alpha * price + (1 - alpha) * ema[-1])

    return ema


def calculate_bollinger_bands(prices, period=20, std_dev=2):
    if len(prices) < period:
        return prices, prices, prices

    sma = []
    bb_upper = []
    bb_lower = []

    for i in range(len(prices)):
        if i < period - 1:
            sma.append(prices[i])
            bb_upper.append(prices[i])
            bb_lower.append(prices[i])
        else:
            window = prices[i - period + 1:i + 1]
            mean = np.mean(window)
            std = np.std(window)

            sma.append(mean)
            bb_upper.append(mean + (std * std_dev))
            bb_lower.append(mean - (std * std_dev))

    return sma, bb_upper, bb_lower


# ===== Trading Bot Class =====
class SafeTradingBot:
    def __init__(self):
        self.db_connection = self.init_database()
        self.safety_checks_enabled = True
        self.max_daily_trades = 10
        self.daily_trade_count = 0
        self.last_trade_date = datetime.now().date()
        self.active_signals = []
        self.watchlist = ["BTCUSDT", "ETHUSDT", "ADAUSDT", "DOTUSDT", "LINKUSDT"]

    def init_database(self):
        conn = sqlite3.connect('trading_history.db')
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                symbol TEXT,
                side TEXT,
                quantity REAL,
                price REAL,
                pnl REAL,
                strategy TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                symbol TEXT,
                signal_type TEXT,
                confidence REAL,
                price REAL,
                indicators TEXT
            )
        ''')

        conn.commit()
        return conn

    def safety_check(self):
        current_date = datetime.now().date()

        if current_date != self.last_trade_date:
            self.daily_trade_count = 0
            self.last_trade_date = current_date

        if self.daily_trade_count >= self.max_daily_trades:
            logger.log(f"Daily trade limit ({self.max_daily_trades}) reached", 'WARNING')
            return False

        return True

    def calculate_indicators(self, df):
        try:
            if len(df) == 0:
                return df

            closes = df['close'].values
            volumes = df['volume'].values

            rsi_values = calculate_rsi(closes)
            ema_9_values = calculate_ema(closes, 9)
            ema_21_values = calculate_ema(closes, 21)
            ema_50_values = calculate_ema(closes, 50)

            data_length = len(df)

            def ensure_length(arr, target_length):
                if len(arr) > target_length:
                    return arr[-target_length:]
                elif len(arr) < target_length:
                    padding = [arr[0]] * (target_length - len(arr))
                    return padding + arr
                return arr

            df = df.copy()
            df.loc[:, 'rsi'] = ensure_length(rsi_values, data_length)
            df.loc[:, 'ema_9'] = ensure_length(ema_9_values, data_length)
            df.loc[:, 'ema_21'] = ensure_length(ema_21_values, data_length)
            df.loc[:, 'ema_50'] = ensure_length(ema_50_values, data_length)

            # Bollinger Bands
            bb_middle, bb_upper, bb_lower = calculate_bollinger_bands(closes)
            df.loc[:, 'bb_upper'] = ensure_length(bb_upper, data_length)
            df.loc[:, 'bb_middle'] = ensure_length(bb_middle, data_length)
            df.loc[:, 'bb_lower'] = ensure_length(bb_lower, data_length)

            # MACD
            ema_12 = calculate_ema(closes, 12)
            ema_26 = calculate_ema(closes, 26)
            macd_values = np.array(ensure_length(ema_12, data_length)) - np.array(ensure_length(ema_26, data_length))
            df.loc[:, 'macd'] = macd_values

            macd_signal_values = calculate_ema(macd_values, 9)
            df.loc[:, 'macd_signal'] = ensure_length(macd_signal_values, data_length)

            # Volume SMA
            volume_sma_values = calculate_ema(volumes, 20)
            df.loc[:, 'volume_sma'] = ensure_length(volume_sma_values, data_length)

            return df

        except Exception as e:
            logger.log(f"Error calculating indicators: {e}", 'ERROR')
            return df

    def generate_signal(self, df):
        if len(df) < 50:
            return None, 0

        try:
            latest = df.iloc[-1]
            prev = df.iloc[-2]
            signals = []

            required_columns = ['rsi', 'macd', 'macd_signal', 'ema_9', 'ema_21', 'ema_50', 'bb_upper', 'bb_lower',
                                'close', 'volume', 'volume_sma']
            for col in required_columns:
                if col not in df.columns:
                    logger.log(f"Missing indicator column: {col}", 'WARNING')
                    return None, 0

            # RSI Strategy
            if pd.notna(latest['rsi']) and pd.notna(prev['rsi']):
                if latest['rsi'] < settings['rsi_oversold'] and prev['rsi'] >= settings['rsi_oversold']:
                    signals.append(('RSI_OVERSOLD_BUY', 0.3))
                    logger.log(f"RSI Signal: Oversold condition detected (RSI: {latest['rsi']:.1f})", 'SIGNAL')
                elif latest['rsi'] > settings['rsi_overbought'] and prev['rsi'] <= settings['rsi_overbought']:
                    signals.append(('RSI_OVERBOUGHT_SELL', 0.3))
                    logger.log(f"RSI Signal: Overbought condition detected (RSI: {latest['rsi']:.1f})", 'SIGNAL')

            # MACD Strategy
            if pd.notna(latest['macd']) and pd.notna(latest['macd_signal']) and pd.notna(prev['macd']) and pd.notna(prev['macd_signal']):
                if latest['macd'] > latest['macd_signal'] and prev['macd'] <= prev['macd_signal']:
                    signals.append(('MACD_BULLISH_CROSS', 0.4))
                    logger.log(f"MACD Signal: Bullish crossover detected", 'SIGNAL')
                elif latest['macd'] < latest['macd_signal'] and prev['macd'] >= prev['macd_signal']:
                    signals.append(('MACD_BEARISH_CROSS', 0.4))
                    logger.log(f"MACD Signal: Bearish crossover detected", 'SIGNAL')

            # EMA Strategy
            if all(pd.notna(latest[col]) and pd.notna(prev[col]) for col in ['ema_9', 'ema_21', 'ema_50', 'close']):
                if latest['ema_9'] > latest['ema_21'] > latest['ema_50']:
                    if latest['close'] > latest['ema_9'] and prev['close'] <= prev['ema_9']:
                        signals.append(('EMA_GOLDEN_CROSS', 0.5))
                        logger.log(f"EMA Signal: Golden cross pattern confirmed", 'SIGNAL')
                elif latest['ema_9'] < latest['ema_21'] < latest['ema_50']:
                    if latest['close'] < latest['ema_9'] and prev['close'] >= prev['ema_9']:
                        signals.append(('EMA_DEATH_CROSS', 0.5))
                        logger.log(f"EMA Signal: Death cross pattern confirmed", 'SIGNAL')

            # Bollinger Bands Strategy
            if all(pd.notna(latest[col]) for col in ['close', 'bb_lower', 'bb_upper', 'rsi']):
                if latest['close'] < latest['bb_lower'] and latest['rsi'] < 40:
                    signals.append(('BB_OVERSOLD', 0.3))
                    logger.log(f"BB Signal: Price below lower band with low RSI", 'SIGNAL')
                elif latest['close'] > latest['bb_upper'] and latest['rsi'] > 60:
                    signals.append(('BB_OVERBOUGHT', 0.3))
                    logger.log(f"BB Signal: Price above upper band with high RSI", 'SIGNAL')

            # Volume confirmation
            if pd.notna(latest['volume']) and pd.notna(latest['volume_sma']):
                if latest['volume'] > latest['volume_sma'] * 1.5:
                    for signal in signals:
                        if 'BUY' in signal[0] or 'BULLISH' in signal[0]:
                            signals.append(('VOLUME_CONFIRM_BUY', 0.2))
                        elif 'SELL' in signal[0] or 'BEARISH' in signal[0]:
                            signals.append(('VOLUME_CONFIRM_SELL', 0.2))

            buy_signals = [s for s in signals if any(x in s[0] for x in ['BUY', 'BULLISH', 'OVERSOLD'])]
            sell_signals = [s for s in signals if any(x in s[0] for x in ['SELL', 'BEARISH', 'OVERBOUGHT'])]

            buy_confidence = sum([s[1] for s in buy_signals])
            sell_confidence = sum([s[1] for s in sell_signals])

            if buy_confidence > sell_confidence and buy_confidence > 0.6:
                signal_details = f"Buy signals: {[s[0] for s in buy_signals]}"
                logger.log(f"Strong BUY signal generated", 'SIGNAL', signal_details)
                return 'BUY', min(buy_confidence, 1.0)
            elif sell_confidence > buy_confidence and sell_confidence > 0.6:
                signal_details = f"Sell signals: {[s[0] for s in sell_signals]}"
                logger.log(f"Strong SELL signal generated", 'SIGNAL', signal_details)
                return 'SELL', min(sell_confidence, 1.0)

            return None, 0

        except Exception as e:
            logger.log(f"Error in generate_signal: {e}", 'ERROR')
            return None, 0


# ===== Modern UI Components =====
class ModernCard(tk.Frame):
    def __init__(self, parent, title="", bg_color="#2d3436", title_color="#74b9ff", **kwargs):
        super().__init__(parent, bg=bg_color, relief="flat", bd=1, **kwargs)
        self.configure(highlightbackground="#636e72", highlightthickness=1)

        if title:
            title_frame = tk.Frame(self, bg=bg_color, height=35)
            title_frame.pack(fill="x", padx=10, pady=(8, 0))
            title_frame.pack_propagate(False)

            tk.Label(title_frame, text=title, fg=title_color, bg=bg_color,
                     font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=3)


class ModernButton(tk.Button):
    def __init__(self, parent, text="", command=None, style="primary", **kwargs):
        styles = {
            'primary': {'bg': '#0984e3', 'fg': 'white', 'hover': '#74b9ff'},
            'success': {'bg': '#00b894', 'fg': 'white', 'hover': '#00ff88'},
            'danger': {'bg': '#e17055', 'fg': 'white', 'hover': '#ff7675'},
            'warning': {'bg': '#fdcb6e', 'fg': '#2d3436', 'hover': '#ffeaa7'},
            'dark': {'bg': '#2d3436', 'fg': 'white', 'hover': '#636e72'}
        }

        config = styles.get(style, styles['primary'])

        super().__init__(parent, text=text, command=command,
                         bg=config['bg'], fg=config['fg'],
                         font=("Segoe UI", 9, "bold"),
                         relief="flat", bd=0, padx=15, pady=6,
                         cursor="hand2", **kwargs)

        self.bind("<Enter>", lambda e: self.configure(bg=config['hover']))
        self.bind("<Leave>", lambda e: self.configure(bg=config['bg']))


class PortfolioManager(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#0d1117")
        self.positions_data = []
        self.setup_ui()
        
    def setup_ui(self):
        # Header
        header = tk.Frame(self, bg="#1f2937", height=50)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        tk.Label(header, text="💰 Portfolio Manager", 
                font=("Segoe UI", 14, "bold"), fg="#74b9ff", bg="#1f2937").pack(pady=15)
        
        # Portfolio Summary Cards
        summary_frame = tk.Frame(self, bg="#0d1117")
        summary_frame.pack(fill="x", padx=15, pady=8)
        
        # Total Balance Card
        self.balance_card = ModernCard(summary_frame, title="💎 Total Balance", bg_color="#1a5a3e")
        self.balance_card.pack(side="left", fill="both", expand=True, padx=3)
        
        self.balance_label = tk.Label(self.balance_card, text="$0.00", 
                                     font=("Segoe UI", 16, "bold"), fg="#00ff88", bg="#1a5a3e")
        self.balance_label.pack(pady=15)
        
        # Unrealized PnL Card
        self.pnl_card = ModernCard(summary_frame, title="📊 Unrealized PnL", bg_color="#2d1f3e")
        self.pnl_card.pack(side="left", fill="both", expand=True, padx=3)
        
        self.pnl_label = tk.Label(self.pnl_card, text="$0.00", 
                                 font=("Segoe UI", 16, "bold"), fg="#fd79a8", bg="#2d1f3e")
        self.pnl_label.pack(pady=15)
        
        # Today's Performance Card
        self.daily_pnl_card = ModernCard(summary_frame, title="🚀 Today's P&L", bg_color="#1f2937")
        self.daily_pnl_card.pack(side="left", fill="both", expand=True, padx=3)
        
        self.daily_pnl_label = tk.Label(self.daily_pnl_card, text="$0.00", 
                                       font=("Segoe UI", 16, "bold"), fg="#74b9ff", bg="#1f2937")
        self.daily_pnl_label.pack(pady=15)
        
        # Active Positions Table
        positions_card = ModernCard(self, title="📋 Active Positions")
        positions_card.pack(fill="both", expand=True, padx=15, pady=8)
        
        # Table headers
        table_header = tk.Frame(positions_card, bg="#2d3436")
        table_header.pack(fill="x", padx=10, pady=8)
        
        headers = ["Symbol", "Side", "Size", "Entry Price", "Mark Price", "PnL", "ROE%", "Actions"]
        
        for header in headers:
            tk.Label(table_header, text=header, font=("Segoe UI", 9, "bold"), 
                    fg="#74b9ff", bg="#2d3436").pack(side="left", padx=10)
        
        # Scrollable positions list
        positions_container = tk.Frame(positions_card, bg="#2d3436")
        positions_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        self.positions_canvas = tk.Canvas(positions_container, bg="#2d3436", highlightthickness=0, height=180)
        positions_scrollbar = ttk.Scrollbar(positions_container, orient="vertical", command=self.positions_canvas.yview)
        self.positions_scrollable = tk.Frame(self.positions_canvas, bg="#2d3436")
        
        self.positions_scrollable.bind("<Configure>", 
                                      lambda e: self.positions_canvas.configure(scrollregion=self.positions_canvas.bbox("all")))
        
        self.positions_canvas.create_window((0, 0), window=self.positions_scrollable, anchor="nw")
        self.positions_canvas.configure(yscrollcommand=positions_scrollbar.set)
        
        self.positions_canvas.pack(side="left", fill="both", expand=True)
        positions_scrollbar.pack(side="right", fill="y")
        
    def update_portfolio(self):
        if not client:
            return
            
        try:
            account = client.futures_account()
            balance = float(account['totalWalletBalance'])
            unrealized_pnl = float(account['totalUnrealizedProfit'])
            
            self.balance_label.config(text=f"${balance:,.2f}")
            
            pnl_color = "#00ff88" if unrealized_pnl >= 0 else "#ff4757"
            self.pnl_label.config(text=f"${unrealized_pnl:+,.2f}", fg=pnl_color)
            
            daily_pnl = unrealized_pnl
            daily_color = "#00ff88" if daily_pnl >= 0 else "#ff4757"
            self.daily_pnl_label.config(text=f"${daily_pnl:+,.2f}", fg=daily_color)
            
            self.update_positions_table()
            
        except Exception as e:
            logger.log(f"Error updating portfolio: {e}", 'ERROR')
    
    def update_positions_table(self):
        try:
            for widget in self.positions_scrollable.winfo_children():
                widget.destroy()
                
            positions = client.futures_position_information()
            active_positions = [p for p in positions if float(p['positionAmt']) != 0]
            
            if not active_positions:
                no_pos_label = tk.Label(self.positions_scrollable, 
                                       text="📭 No active positions", 
                                       font=("Segoe UI", 12), fg="#74b9ff", bg="#2d3436")
                no_pos_label.pack(pady=40)
                return
                
            for i, pos in enumerate(active_positions):
                self.create_position_row(pos, i)
                
        except Exception as e:
            logger.log(f"Error updating positions table: {e}", 'ERROR')
    
    def create_position_row(self, pos, row_index):
        row_bg = "#374151" if row_index % 2 == 0 else "#2d3436"
        
        row_frame = tk.Frame(self.positions_scrollable, bg=row_bg, height=40)
        row_frame.pack(fill="x", pady=1)
        row_frame.pack_propagate(False)
        
        symbol = pos['symbol']
        side = "LONG" if float(pos['positionAmt']) > 0 else "SHORT"
        size = abs(float(pos['positionAmt']))
        entry_price = float(pos['entryPrice']) if pos['entryPrice'] != '0' else 0
        mark_price = float(pos['markPrice'])
        pnl = float(pos['unRealizedProfit'])
        
        try:
            roe = float(pos.get('percentage', 0))
        except (ValueError, KeyError):
            if entry_price > 0:
                if side == "LONG":
                    roe = ((mark_price - entry_price) / entry_price) * 100
                else:
                    roe = ((entry_price - mark_price) / entry_price) * 100
            else:
                roe = 0.0
        
        side_color = "#00ff88" if side == "LONG" else "#ff4757"
        pnl_color = "#00ff88" if pnl >= 0 else "#ff4757"
        
        # Data columns with fixed width
        tk.Label(row_frame, text=symbol, font=("Consolas", 8), fg="white", bg=row_bg, width=8).pack(side="left", padx=3, pady=8)
        tk.Label(row_frame, text=side, font=("Consolas", 8), fg=side_color, bg=row_bg, width=6).pack(side="left", padx=3, pady=8)
        tk.Label(row_frame, text=f"{size:.4f}", font=("Consolas", 8), fg="white", bg=row_bg, width=10).pack(side="left", padx=3, pady=8)
        tk.Label(row_frame, text=f"${entry_price:.2f}", font=("Consolas", 8), fg="#a0a0a0", bg=row_bg, width=10).pack(side="left", padx=3, pady=8)
        tk.Label(row_frame, text=f"${mark_price:.2f}", font=("Consolas", 8), fg="#74b9ff", bg=row_bg, width=10).pack(side="left", padx=3, pady=8)
        tk.Label(row_frame, text=f"${pnl:+.2f}", font=("Consolas", 8), fg=pnl_color, bg=row_bg, width=8).pack(side="left", padx=3, pady=8)
        tk.Label(row_frame, text=f"{roe:+.2f}%", font=("Consolas", 8), fg=pnl_color, bg=row_bg, width=8).pack(side="left", padx=3, pady=8)
        
        # Close position button
        close_btn = tk.Button(row_frame, text="❌", command=lambda s=symbol: self.close_position(s),
                             bg="#e17055", fg="white", font=("Segoe UI", 7, "bold"),
                             relief="flat", bd=0, padx=6, pady=2, cursor="hand2")
        close_btn.pack(side="right", padx=8, pady=10)
        
    def close_position(self, symbol):
        try:
            positions = client.futures_position_information(symbol=symbol)
            for pos in positions:
                if float(pos['positionAmt']) != 0:
                    side = SIDE_SELL if float(pos['positionAmt']) > 0 else SIDE_BUY
                    quantity = abs(float(pos['positionAmt']))
                    
                    client.futures_create_order(
                        symbol=symbol,
                        side=side,
                        type='MARKET',
                        quantity=quantity,
                        reduceOnly=True
                    )
                    
                    logger.log(f"Closed position: {symbol}", 'TRADE')
                    show_modern_notification(f"Position closed: {symbol}", "success")
                    break
                    
        except Exception as e:
            logger.log(f"Error closing position {symbol}: {e}", 'ERROR')


class SignalDashboard(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#0d1117")
        self.signals_data = []
        self.market_data = {}
        self.setup_ui()
        
    def setup_ui(self):
        # Header
        header = tk.Frame(self, bg="#1f2937", height=50)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        tk.Label(header, text="🧠 AI Signal Dashboard", 
                font=("Segoe UI", 14, "bold"), fg="#74b9ff", bg="#1f2937").pack(pady=15)
        
        # Signal Strength Meter
        meter_card = ModernCard(self, title="🎯 Current Signal Strength")
        meter_card.pack(fill="x", padx=15, pady=8)
        
        meter_content = tk.Frame(meter_card, bg="#2d3436")
        meter_content.pack(fill="x", padx=10, pady=10)
        
        self.meter_canvas = tk.Canvas(meter_content, width=350, height=60, bg="#2d3436", highlightthickness=0)
        self.meter_canvas.pack()
        
        self.signal_text = tk.Label(meter_content, text="⏳ Analyzing...", 
                                   font=("Segoe UI", 10, "bold"), fg="#74b9ff", bg="#2d3436")
        self.signal_text.pack(pady=(8, 0))
        
        # Market Overview
        market_card = ModernCard(self, title="📊 Market Overview")
        market_card.pack(fill="x", padx=15, pady=8)
        
        market_content = tk.Frame(market_card, bg="#2d3436")
        market_content.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.market_grid = tk.Frame(market_content, bg="#2d3436")
        self.market_grid.pack(fill="x")
        
        # Recent Signals Feed
        signals_card = ModernCard(self, title="📡 Live Signal Feed")
        signals_card.pack(fill="both", expand=True, padx=15, pady=8)
        
        signals_content = tk.Frame(signals_card, bg="#2d3436")
        signals_content.pack(fill="both", expand=True, padx=10, pady=10)
        
        signals_container = tk.Frame(signals_content, bg="#2d3436")
        signals_container.pack(fill="both", expand=True)
        
        self.signals_canvas = tk.Canvas(signals_container, bg="#2d3436", highlightthickness=0)
        signals_scrollbar = ttk.Scrollbar(signals_container, orient="vertical", command=self.signals_canvas.yview)
        self.signals_scrollable = tk.Frame(self.signals_canvas, bg="#2d3436")
        
        self.signals_scrollable.bind("<Configure>", 
                                    lambda e: self.signals_canvas.configure(scrollregion=self.signals_canvas.bbox("all")))
        
        self.signals_canvas.create_window((0, 0), window=self.signals_scrollable, anchor="nw")
        self.signals_canvas.configure(yscrollcommand=signals_scrollbar.set)
        
        self.signals_canvas.pack(side="left", fill="both", expand=True)
        signals_scrollbar.pack(side="right", fill="y")
        
    def update_signal_meter(self, signal, confidence):
        self.meter_canvas.delete("all")
        
        self.meter_canvas.create_rectangle(30, 20, 320, 35, fill="#1f2937", outline="#636e72", width=2)
        
        if signal and confidence > 0:
            meter_width = int(290 * confidence)
            color = "#00ff88" if signal == "BUY" else "#ff4757" if signal == "SELL" else "#74b9ff"
            
            self.meter_canvas.create_rectangle(30, 20, 30 + meter_width, 35, fill=color, outline="")
            
            signal_emoji = "📈" if signal == "BUY" else "📉" if signal == "SELL" else "⏸️"
            self.signal_text.config(text=f"{signal_emoji} {signal} Signal - {confidence:.1%}")
            
            for i in range(0, 101, 25):
                x = 30 + (290 * i / 100)
                self.meter_canvas.create_line(x, 15, x, 20, fill="#636e72", width=1)
                self.meter_canvas.create_text(x, 10, text=f"{i}%", fill="white", font=("Segoe UI", 7))
        else:
            self.signal_text.config(text="⏳ Waiting for signal...")
            
    def update_market_overview(self):
        try:
            for widget in self.market_grid.winfo_children():
                widget.destroy()
                
            if not client:
                return
                
            symbols = bot.watchlist
            
            for i, symbol in enumerate(symbols):
                try:
                    ticker = client.futures_symbol_ticker(symbol=symbol)
                    stats = client.futures_24hr_ticker(symbol=symbol)
                    
                    price = float(ticker['price'])
                    change_percent = float(stats['priceChangePercent'])
                    
                    row = i // 5
                    col = i % 5
                    
                    symbol_frame = tk.Frame(self.market_grid, bg="#374151" if change_percent >= 0 else "#4c1d1d", 
                                           relief="flat", bd=1, width=60, height=60)
                    symbol_frame.grid(row=row, column=col, padx=2, pady=2, sticky="ew")
                    symbol_frame.pack_propagate(False)
                    
                    tk.Label(symbol_frame, text=symbol[:6], font=("Segoe UI", 8, "bold"), 
                            fg="white", bg=symbol_frame['bg']).pack(pady=(4, 1))
                    
                    change_color = "#00ff88" if change_percent >= 0 else "#ff4757"
                    change_arrow = "↗" if change_percent >= 0 else "↘"
                    
                    tk.Label(symbol_frame, text=f"{change_arrow}{change_percent:+.1f}%", 
                            font=("Segoe UI", 7, "bold"), fg=change_color, bg=symbol_frame['bg']).pack(pady=(1, 4))
                    
                except Exception as e:
                    continue
                    
            for i in range(5):
                self.market_grid.grid_columnconfigure(i, weight=1)
                
        except Exception as e:
            logger.log(f"Error updating market overview: {e}", 'ERROR')
            
    def add_signal_entry(self, signal_type, symbol, confidence, price, indicators):
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        signal_frame = tk.Frame(self.signals_scrollable, bg="#1f2937", relief="flat", bd=1)
        signal_frame.pack(fill="x", padx=3, pady=1)
        
        header_frame = tk.Frame(signal_frame, bg="#1f2937")
        header_frame.pack(fill="x", padx=8, pady=4)
        
        tk.Label(header_frame, text=f"[{timestamp}]", font=("Consolas", 8), 
                fg="#636e72", bg="#1f2937").pack(side="left")
        
        signal_color = "#00ff88" if "BUY" in signal_type else "#ff4757" if "SELL" in signal_type else "#74b9ff"
        signal_emoji = "📈" if "BUY" in signal_type else "📉" if "SELL" in signal_type else "⚡"
        
        tk.Label(header_frame, text=f"{signal_emoji} {signal_type}", 
                font=("Segoe UI", 9, "bold"), fg=signal_color, bg="#1f2937").pack(side="left", padx=(8, 0))
        
        conf_bg = "#00b894" if confidence > 0.8 else "#fdcb6e" if confidence > 0.6 else "#636e72"
        conf_frame = tk.Frame(header_frame, bg=conf_bg, relief="flat", bd=0)
        conf_frame.pack(side="right")
        
        tk.Label(conf_frame, text=f"{confidence:.0%}", font=("Segoe UI", 8, "bold"), 
                fg="white", bg=conf_bg).pack(padx=6, pady=1)
        
        details_frame = tk.Frame(signal_frame, bg="#1f2937")
        details_frame.pack(fill="x", padx=10, pady=(0, 6))
        
        tk.Label(details_frame, text=f"{symbol} | ${price:.4f}", 
                font=("Consolas", 8), fg="#a0a0a0", bg="#1f2937").pack(anchor="w")
        
        self.signals_canvas.update_idletasks()
        self.signals_canvas.yview_moveto(1)


# Initialize global objects
config_manager = ConfigManager()
logger = TradingLogger()
bot = SafeTradingBot()

# Global Variables
client = None
running = True
price_data = []
volume_data = []
kline_data = []
positions = {}
orders = []
balance_info = {}
pnl_history = []
auto_trading = False
selected_symbol = "BTCUSDT"
selected_timeframe = "1m"

# Trading Settings
settings = {
    'risk_percent': config_manager.config.getfloat('TRADING', 'risk_percent', fallback=2.0),
    'stop_loss_percent': config_manager.config.getfloat('TRADING', 'stop_loss_percent', fallback=1.5),
    'take_profit_percent': config_manager.config.getfloat('TRADING', 'take_profit_percent', fallback=3.0),
    'max_positions': config_manager.config.getint('TRADING', 'max_positions', fallback=3),
    'min_volume': config_manager.config.getfloat('TRADING', 'min_volume', fallback=1000000),
    'rsi_oversold': config_manager.config.getint('TRADING', 'rsi_oversold', fallback=30),
    'rsi_overbought': config_manager.config.getint('TRADING', 'rsi_overbought', fallback=70),
    'enable_notifications': config_manager.config.getboolean('TRADING', 'enable_notifications', fallback=True)
}

update_thread = None
strategy_thread = None


# ===== API Functions =====
def setup_api_credentials():
    global client

    api_key, api_secret, testnet = config_manager.get_api_credentials()

    if not api_key or not api_secret:
        cred_window = tk.Toplevel(root)
        cred_window.title("🔐 API Credentials Setup")
        cred_window.geometry("600x500")
        cred_window.configure(bg="#1e1e2f")
        cred_window.transient(root)
        cred_window.grab_set()

        header_frame = tk.Frame(cred_window, bg="#0984e3", height=80)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)

        tk.Label(header_frame, text="🔐 Secure API Connection",
                 font=("Segoe UI", 16, "bold"), fg="white", bg="#0984e3").pack(pady=25)

        warning_card = ModernCard(cred_window, title="⚠️ Security Notice", bg_color="#e17055")
        warning_card.pack(fill="x", padx=20, pady=15)

        warning_text = """Your API credentials will be encrypted and stored locally.
Ensure your computer is secure and never share these credentials.
Use testnet for learning and practice trading."""

        tk.Label(warning_card, text=warning_text, fg="white", bg="#e17055",
                 font=("Segoe UI", 10), justify="left", wraplength=500).pack(padx=15, pady=10)

        input_card = ModernCard(cred_window, title="🔑 API Configuration")
        input_card.pack(fill="both", expand=True, padx=20, pady=15)

        tk.Label(input_card, text="Binance API Key:", fg="white", bg="#2d3436",
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=15, pady=(10, 5))
        api_key_entry = tk.Entry(input_card, font=("Consolas", 11), bg="#636e72", fg="white",
                                 insertbackground="white", relief="flat", bd=5)
        api_key_entry.pack(fill="x", padx=15, pady=5)

        tk.Label(input_card, text="Binance API Secret:", fg="white", bg="#2d3436",
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=15, pady=(15, 5))
        api_secret_entry = tk.Entry(input_card, font=("Consolas", 11), bg="#636e72", fg="white",
                                    insertbackground="white", relief="flat", bd=5, show="*")
        api_secret_entry.pack(fill="x", padx=15, pady=5)

        testnet_frame = tk.Frame(input_card, bg="#2d3436")
        testnet_frame.pack(fill="x", padx=15, pady=15)

        testnet_var = tk.BooleanVar(value=True)
        testnet_check = tk.Checkbutton(testnet_frame, text="🧪 Use Testnet (Recommended for testing)",
                                       variable=testnet_var, fg="#74b9ff", bg="#2d3436",
                                       selectcolor="#0984e3", font=("Segoe UI", 10))
        testnet_check.pack(anchor="w")

        def save_and_connect():
            key = api_key_entry.get().strip()
            secret = api_secret_entry.get().strip()

            if not key or not secret:
                messagebox.showerror("Error", "Please enter both API key and secret")
                return

            config_manager.set_api_credentials(key, secret, testnet_var.get())
            cred_window.destroy()
            connect_api()

        btn_frame = tk.Frame(input_card, bg="#2d3436")
        btn_frame.pack(fill="x", padx=15, pady=15)

        ModernButton(btn_frame, text="🚀 Save & Connect", command=save_and_connect,
                     style="success").pack(side="left", padx=5)
        ModernButton(btn_frame, text="❌ Cancel", command=cred_window.destroy,
                     style="danger").pack(side="right", padx=5)

    else:
        connect_api()


def connect_api():
    global client

    try:
        api_key, api_secret, testnet = config_manager.get_api_credentials()

        if not api_key or not api_secret:
            logger.log("API credentials not configured", 'ERROR')
            return

        logger.log("Establishing connection to Binance API...", 'INFO')
        client = Client(api_key, api_secret, testnet=testnet)

        account = client.futures_account()

        try:
            client.futures_change_leverage(symbol=selected_symbol, leverage=5)
            logger.log(f"Leverage set to 5x for {selected_symbol}", 'SUCCESS')
        except Exception as e:
            logger.log(f"Could not set leverage: {e}", 'WARNING')

        network_type = "Testnet" if testnet else "Live"
        logger.log(f"Successfully connected to Binance Futures {network_type}", 'SUCCESS')
        start_data_updates()

        connection_status.set(f"🟢 Connected ({network_type})")
        show_modern_notification(f"Connected to {network_type} Environment", "success")

    except Exception as e:
        logger.log(f"Connection failed: {str(e)}", 'ERROR')
        messagebox.showerror("Connection Error", f"Failed to connect: {str(e)}")


def get_kline_data():
    if not client:
        return None

    try:
        klines = client.futures_klines(
            symbol=selected_symbol,
            interval=selected_timeframe,
            limit=100
        )

        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
        ])

        numeric_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col])

        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return bot.calculate_indicators(df)

    except Exception as e:
        logger.log(f"Error getting kline data: {e}", 'ERROR')
        return None


def get_symbol_info(symbol):
    try:
        exchange_info = client.futures_exchange_info()
        for s in exchange_info['symbols']:
            if s['symbol'] == symbol:
                for filter_item in s['filters']:
                    if filter_item['filterType'] == 'LOT_SIZE':
                        step_size = float(filter_item['stepSize'])
                        min_qty = float(filter_item['minQty'])
                        max_qty = float(filter_item['maxQty'])
                        return step_size, min_qty, max_qty
        return 0.001, 0.001, 10000
    except:
        return 0.001, 0.001, 10000


def get_price_precision(symbol):
    try:
        exchange_info = client.futures_exchange_info()
        for s in exchange_info['symbols']:
            if s['symbol'] == symbol:
                for filter_item in s['filters']:
                    if filter_item['filterType'] == 'PRICE_FILTER':
                        tick_size = float(filter_item['tickSize'])
                        if tick_size >= 1:
                            return 0
                        else:
                            return len(str(tick_size).split('.')[-1].rstrip('0'))
        return 2
    except:
        return 2


def round_step_size(quantity, step_size):
    if step_size == 0:
        return quantity

    if step_size >= 1:
        decimals = 0
    else:
        decimals = len(str(step_size).split('.')[-1].rstrip('0'))

    rounded = round(quantity / step_size) * step_size
    return round(rounded, decimals)


def round_price(price, precision):
    return round(price, precision)


def calculate_position_size():
    try:
        if not client:
            return 0.001

        step_size, min_qty, max_qty = get_symbol_info(selected_symbol)
        account = client.futures_account()
        total_balance = float(account['totalWalletBalance'])

        if total_balance < 100:
            logger.log("Warning: Balance too low for safe trading", 'WARNING')
            return round_step_size(min_qty, step_size)

        risk_amount = total_balance * (settings['risk_percent'] / 100)
        ticker = client.futures_symbol_ticker(symbol=selected_symbol)
        current_price = float(ticker['price'])

        stop_loss_price = current_price * (1 - settings['stop_loss_percent'] / 100)
        risk_per_unit = current_price - stop_loss_price

        if risk_per_unit > 0:
            quantity = risk_amount / risk_per_unit
            max_quantity = total_balance * 0.1 / current_price
            quantity = min(quantity, max_quantity)
            quantity = max(min_qty, min(quantity, max_qty))
            quantity = round_step_size(quantity, step_size)
            return quantity

        return round_step_size(min_qty, step_size)

    except Exception as e:
        logger.log(f"Error calculating position size: {e}", 'ERROR')
        return 0.001


def place_smart_order(side, strategy="MANUAL"):
    if not client:
        show_modern_notification("Please connect API first", "warning")
        return

    if not bot.safety_check():
        show_modern_notification("Trading blocked by safety checks", "warning")
        return

    if strategy == "MANUAL":
        confirm = messagebox.askyesno("Confirm Trade",
                                      f"Place {side} order for {selected_symbol}?\n"
                                      f"Risk: {settings['risk_percent']}%\n"
                                      f"Stop Loss: {settings['stop_loss_percent']}%\n"
                                      f"Take Profit: {settings['take_profit_percent']}%")
        if not confirm:
            return

    try:
        quantity = calculate_position_size()

        if quantity <= 0.001:
            logger.log("Position size too small, order cancelled", 'WARNING')
            return

        logger.log(f"Placing {side} order for {quantity} {selected_symbol}", 'TRADE')

        order = client.futures_create_order(
            symbol=selected_symbol,
            side=side,
            type='MARKET',
            quantity=quantity
        )

        fill_price = float(order.get('avgPrice', 0)) if order.get('avgPrice') else float(order.get('price', 0))
        if fill_price == 0:
            ticker = client.futures_symbol_ticker(symbol=selected_symbol)
            fill_price = float(ticker['price'])

        price_precision = get_price_precision(selected_symbol)

        if side == SIDE_BUY:
            stop_loss = round_price(fill_price * (1 - settings['stop_loss_percent'] / 100), price_precision)
            take_profit = round_price(fill_price * (1 + settings['take_profit_percent'] / 100), price_precision)
        else:
            stop_loss = round_price(fill_price * (1 + settings['stop_loss_percent'] / 100), price_precision)
            take_profit = round_price(fill_price * (1 - settings['take_profit_percent'] / 100), price_precision)

        try:
            sl_order = client.futures_create_order(
                symbol=selected_symbol,
                side=SIDE_SELL if side == SIDE_BUY else SIDE_BUY,
                type='STOP_MARKET',
                quantity=quantity,
                stopPrice=stop_loss,
                reduceOnly=True
            )
            logger.log(f"Stop Loss placed at ${stop_loss:.{price_precision}f}", 'SUCCESS')
        except Exception as e:
            logger.log(f"SL order failed: {e}", 'ERROR')

        try:
            tp_order = client.futures_create_order(
                symbol=selected_symbol,
                side=SIDE_SELL if side == SIDE_BUY else SIDE_BUY,
                type='TAKE_PROFIT_MARKET',
                quantity=quantity,
                stopPrice=take_profit,
                reduceOnly=True
            )
            logger.log(f"Take Profit placed at ${take_profit:.{price_precision}f}", 'SUCCESS')
        except Exception as e:
            logger.log(f"TP order failed: {e}", 'ERROR')

        cursor = bot.db_connection.cursor()
        cursor.execute('''
            INSERT INTO trades (timestamp, symbol, side, quantity, price, pnl, strategy)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (datetime.now().isoformat(), selected_symbol, side, quantity, fill_price, 0, strategy))
        bot.db_connection.commit()

        bot.daily_trade_count += 1

        order_details = f"""Order executed successfully:
Symbol: {order['symbol']} | Side: {side} | Qty: {quantity}
Entry: ${fill_price:,.8f} | SL: ${stop_loss:,.8f} | TP: ${take_profit:,.8f}
Order ID: {order['orderId']} | Strategy: {strategy}"""

        logger.log(f"{side} order executed for {selected_symbol}", 'TRADE', order_details)

        if settings['enable_notifications']:
            show_modern_notification(f"Order Placed: {side} {selected_symbol}", "success")

    except Exception as e:
        logger.log(f"Order failed: {str(e)}", 'ERROR')
        show_modern_notification(f"Order failed: {str(e)}", "error")


def auto_trading_strategy():
    global auto_trading

    logger.log("Auto trading strategy started", 'AUTO')

    while auto_trading and running:
        try:
            if not client:
                time.sleep(5)
                continue

            if not bot.safety_check():
                logger.log("Auto trading paused - safety limits reached", 'AUTO')
                time.sleep(300)
                continue

            df = get_kline_data()
            if df is None or len(df) < 50:
                time.sleep(30)
                continue

            signal, confidence = bot.generate_signal(df)

            if hasattr(root, 'signal_dashboard'):
                latest_price = df.iloc[-1]['close']
                root.after(0, lambda: root.signal_dashboard.update_signal_meter(signal, confidence))
                
                if signal and confidence > 0.7:
                    indicators = {
                        'rsi': df.iloc[-1]['rsi'],
                        'ema_9': df.iloc[-1]['ema_9'],
                        'ema_21': df.iloc[-1]['ema_21']
                    }
                    root.after(0, lambda: root.signal_dashboard.add_signal_entry(
                        signal, selected_symbol, confidence, latest_price, indicators))

            if signal and confidence > 0.8:
                current_positions = get_current_positions()

                logger.log(f"Strong signal detected: {signal} (Confidence: {confidence:.2f})", 'AUTO')

                if len(current_positions) < settings['max_positions']:
                    latest_price = df.iloc[-1]['close']
                    latest_volume = df.iloc[-1]['volume']
                    latest_rsi = df.iloc[-1]['rsi']

                    if latest_volume > settings['min_volume']:
                        side = SIDE_BUY if signal == 'BUY' else SIDE_SELL

                        market_info = f"""Market Analysis:
Price: ${latest_price:.8f} | Volume: {latest_volume / 1000000:.1f}M
RSI: {latest_rsi:.1f} | Confidence: {confidence:.2f}
Active Positions: {len(current_positions)}/{settings['max_positions']}"""

                        logger.log(f"Executing auto {side} order", 'AUTO', market_info)

                        cursor = bot.db_connection.cursor()
                        cursor.execute('''
                            INSERT INTO signals (timestamp, symbol, signal_type, confidence, price, indicators)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (datetime.now().isoformat(), selected_symbol, signal, confidence,
                              latest_price, json.dumps(str(df.iloc[-1].to_dict()))))
                        bot.db_connection.commit()

                        root.after(0, lambda: place_smart_order(side, f"AUTO_{signal}"))
                        time.sleep(120)
                    else:
                        logger.log(f"Volume too low for trading: {latest_volume / 1000000:.1f}M", 'AUTO')
                else:
                    logger.log(f"Max positions reached: {len(current_positions)}/{settings['max_positions']}", 'AUTO')

            time.sleep(15)

        except Exception as e:
            logger.log(f"Auto trading error: {e}", 'ERROR')
            time.sleep(60)

    logger.log("Auto trading strategy stopped", 'AUTO')


def get_current_positions():
    try:
        if not client:
            return []
        positions = client.futures_position_information()
        return [p for p in positions if float(p['positionAmt']) != 0]
    except Exception as e:
        logger.log(f"Error getting positions: {e}", 'ERROR')
        return []


def update_data():
    global running

    while running:
        try:
            if client:
                ticker = client.futures_symbol_ticker(symbol=selected_symbol)
                price = float(ticker['price'])

                root.after(0, lambda: update_price_display(price))
                root.after(0, update_account_info)
                root.after(0, update_portfolio_displays)

                price_data.append(price)
                if len(price_data) > 100:
                    price_data.pop(0)

        except Exception as e:
            logger.log(f"Error updating data: {e}", 'ERROR')

        time.sleep(3)


def update_price_display(price):
    try:
        if len(price_data) > 1:
            prev_price = price_data[-2]
            change = ((price - prev_price) / prev_price) * 100

            if change > 0:
                color = "#00ff88"
                arrow = "📈"
            elif change < 0:
                color = "#ff4757"
                arrow = "📉"
            else:
                color = "#74b9ff"
                arrow = "➡️"

            price_text = f"{arrow} {selected_symbol}\n${price:,.6f} ({change:+.2f}%)"
        else:
            color = "#74b9ff"
            price_text = f"📊 {selected_symbol}\n${price:,.6f}\nInitializing..."

        price_var.set(price_text)
        price_label.config(fg=color)

    except Exception as e:
        logger.log(f"Error updating price display: {e}", 'ERROR')


def update_account_info():
    try:
        if not client:
            return

        account = client.futures_account()
        balance = float(account['totalWalletBalance'])
        unrealized_pnl = float(account['totalUnrealizedProfit'])

        balance_var.set(f"💰 ${balance:,.2f}")

        pnl_color = "#00ff88" if unrealized_pnl >= 0 else "#ff4757"
        pnl_icon = "📈" if unrealized_pnl >= 0 else "📉"
        pnl_var.set(f"{pnl_icon} ${unrealized_pnl:+,.2f}")
        pnl_label.config(fg=pnl_color)

        pnl_history.append(unrealized_pnl)
        if len(pnl_history) > 50:
            pnl_history.pop(0)

    except Exception as e:
        logger.log(f"Error updating account info: {e}", 'ERROR')


def update_portfolio_displays():
    try:
        if hasattr(root, 'portfolio_manager'):
            root.portfolio_manager.update_portfolio()
        
        if hasattr(root, 'signal_dashboard'):
            root.signal_dashboard.update_market_overview()
            
    except Exception as e:
        logger.log(f"Error updating portfolio displays: {e}", 'ERROR')


def start_data_updates():
    global update_thread
    if update_thread is None or not update_thread.is_alive():
        update_thread = threading.Thread(target=update_data, daemon=True)
        update_thread.start()


def toggle_auto_trading():
    global auto_trading, strategy_thread

    if not client:
        show_modern_notification("Please connect API first", "warning")
        return

    if not auto_trading:
        api_key, api_secret, testnet = config_manager.get_api_credentials()
        env_type = "Testnet" if testnet else "LIVE"

        confirm_msg = f"""🤖 Enable Auto Trading?

Environment: {env_type}
Symbol: {selected_symbol}
Risk per trade: {settings['risk_percent']}%
Max daily trades: {bot.max_daily_trades}
Today's trades: {bot.daily_trade_count}

Auto trading will place real orders. Continue?"""

        if not messagebox.askyesno("Confirm Auto Trading", confirm_msg):
            return

    auto_trading = not auto_trading

    if auto_trading:
        auto_btn.configure(text="🛑 STOP AUTO TRADING")
        strategy_thread = threading.Thread(target=auto_trading_strategy, daemon=True)
        strategy_thread.start()
        logger.log("Auto Trading activated - Enhanced safety mode enabled", 'AUTO')
        auto_status.set("🤖 Auto Trading ON")
        show_modern_notification("Auto Trading Started", "success")
    else:
        auto_btn.configure(text="🚀 START AUTO TRADING")
        logger.log("Auto Trading deactivated", 'AUTO')
        auto_status.set("👤 Manual Mode")
        show_modern_notification("Auto Trading Stopped", "info")


def show_modern_notification(message, notification_type="info"):
    try:
        notification = tk.Toplevel(root)
        notification.title("Trading Alert")
        notification.geometry("400x120")
        notification.attributes('-topmost', True)
        notification.transient(root)
        notification.overrideredirect(True)

        x = root.winfo_rootx() + root.winfo_width() - 420
        y = root.winfo_rooty() + 50
        notification.geometry(f"+{x}+{y}")

        colors = {
            'success': {'bg': '#00b894', 'icon': '✅'},
            'error': {'bg': '#e17055', 'icon': '❌'},
            'warning': {'bg': '#fdcb6e', 'icon': '⚠️'},
            'info': {'bg': '#74b9ff', 'icon': 'ℹ️'}
        }

        config = colors.get(notification_type, colors['info'])
        notification.configure(bg=config['bg'])

        content_frame = tk.Frame(notification, bg=config['bg'])
        content_frame.pack(fill="both", expand=True, padx=15, pady=15)

        icon_label = tk.Label(content_frame, text=config['icon'], fg="white", bg=config['bg'],
                              font=("Segoe UI", 16))
        icon_label.pack(side="left", padx=(0, 10))

        msg_label = tk.Label(content_frame, text=message, fg="white", bg=config['bg'],
                             font=("Segoe UI", 11, "bold"), wraplength=300)
        msg_label.pack(side="left", fill="both", expand=True)

        notification.after(4000, notification.destroy)

        def close_notification(event=None):
            notification.destroy()

        notification.bind("<Button-1>", close_notification)
        content_frame.bind("<Button-1>", close_notification)
    except Exception as e:
        print(f"Notification error: {e}")


def close_all_positions():
    if not client:
        show_modern_notification("Please connect API first", "warning")
        return

    current_positions = get_current_positions()
    if not current_positions:
        logger.log("No positions to close", 'INFO')
        return

    pos_info = "\n".join([f"{p['symbol']}: {p['positionAmt']}" for p in current_positions])
    confirm = messagebox.askyesno("Confirm Close Positions",
                                  f"Close all positions?\n\n{pos_info}")
    if not confirm:
        return

    try:
        logger.log(f"Closing {len(current_positions)} positions", 'TRADE')
        closed_count = 0

        for pos in current_positions:
            side = SIDE_SELL if float(pos['positionAmt']) > 0 else SIDE_BUY
            quantity = abs(float(pos['positionAmt']))

            client.futures_create_order(
                symbol=pos['symbol'],
                side=side,
                type='MARKET',
                quantity=quantity,
                reduceOnly=True
            )
            closed_count += 1
            logger.log(f"Closed {side} position: {quantity} {pos['symbol']}", 'TRADE')

        logger.log(f"Successfully closed {closed_count} positions", 'SUCCESS')
        show_modern_notification(f"Closed {closed_count} positions", "success")

    except Exception as e:
        logger.log(f"Error closing positions: {str(e)}", 'ERROR')
        show_modern_notification(f"Error closing positions", "error")


def cancel_all_orders():
    if not client:
        return

    confirm = messagebox.askyesno("Confirm Cancel Orders", "Cancel all open orders?")
    if not confirm:
        return

    try:
        client.futures_cancel_all_open_orders(symbol=selected_symbol)
        logger.log("All orders cancelled successfully", 'SUCCESS')
        show_modern_notification("All orders cancelled", "success")
    except Exception as e:
        logger.log(f"Error canceling orders: {str(e)}", 'ERROR')


def emergency_stop():
    if not client:
        return

    confirm = messagebox.askyesno("🚨 EMERGENCY STOP",
                                  "🚨 EMERGENCY STOP PROTOCOL\n\n"
                                  "This will immediately:\n"
                                  "• Stop all auto trading\n"
                                  "• Cancel ALL open orders\n"
                                  "• Close ALL positions\n\n"
                                  "⚠️ This action cannot be undone!\n\n"
                                  "Proceed with emergency stop?")
    if not confirm:
        return

    global auto_trading
    auto_trading = False

    logger.log("🚨 EMERGENCY STOP INITIATED", 'ERROR')

    try:
        client.futures_cancel_all_open_orders(symbol=selected_symbol)
        logger.log("All open orders cancelled", 'SUCCESS')

        positions = client.futures_position_information()
        closed_positions = 0

        for pos in positions:
            if float(pos['positionAmt']) != 0:
                side = SIDE_SELL if float(pos['positionAmt']) > 0 else SIDE_BUY
                quantity = abs(float(pos['positionAmt']))

                client.futures_create_order(
                    symbol=pos['symbol'],
                    side=side,
                    type=ORDER_TYPE_MARKET,
                    quantity=quantity,
                    reduceOnly=True
                )
                closed_positions += 1

        logger.log(f"🚨 EMERGENCY STOP COMPLETED - {closed_positions} positions closed", 'SUCCESS')
        show_modern_notification("Emergency Stop Completed", "success")

    except Exception as e:
        logger.log(f"Emergency stop error: {str(e)}", 'ERROR')


def change_symbol():
    global selected_symbol

    symbol_window = tk.Toplevel(root)
    symbol_window.title("📊 Select Trading Symbol")
    symbol_window.geometry("500x600")
    symbol_window.configure(bg="#0d1117")

    header = tk.Frame(symbol_window, bg="#1f2937", height=80)
    header.pack(fill="x")
    header.pack_propagate(False)

    tk.Label(header, text="📊 Symbol Selection",
             font=("Segoe UI", 16, "bold"), fg="#74b9ff", bg="#1f2937").pack(pady=25)

    popular_card = ModernCard(symbol_window, title="⭐ Popular Symbols")
    popular_card.pack(fill="both", expand=True, padx=20, pady=15)

    popular_content = tk.Frame(popular_card, bg="#2d3436")
    popular_content.pack(fill="both", expand=True, padx=15, pady=15)

    popular_symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT", "DOTUSDT", "LINKUSDT",
                       "BNBUSDT", "SOLUSDT", "MATICUSDT", "AVAXUSDT", "UNIUSDT"]

    symbol_grid = tk.Frame(popular_content, bg="#2d3436")
    symbol_grid.pack(fill="both", expand=True)

    for i, symbol in enumerate(popular_symbols):
        row = i // 2
        col = i % 2

        btn = ModernButton(symbol_grid, text=symbol,
                           command=lambda s=symbol: select_symbol(s, symbol_window),
                           style="primary")
        btn.grid(row=row, column=col, padx=5, pady=5, sticky="ew")

    symbol_grid.grid_columnconfigure(0, weight=1)
    symbol_grid.grid_columnconfigure(1, weight=1)


def select_symbol(symbol, window):
    global selected_symbol
    selected_symbol = symbol
    symbol_var.set(f"Symbol: {selected_symbol}")
    price_data.clear()
    logger.log(f"Symbol changed to {selected_symbol}", 'INFO')
    show_modern_notification(f"Symbol changed to {selected_symbol}", "info")
    window.destroy()


def change_timeframe():
    global selected_timeframe

    tf_window = tk.Toplevel(root)
    tf_window.title("⏱️ Select Timeframe")
    tf_window.geometry("400x500")
    tf_window.configure(bg="#0d1117")

    header = tk.Frame(tf_window, bg="#1f2937", height=80)
    header.pack(fill="x")
    header.pack_propagate(False)

    tk.Label(header, text="⏱️ Timeframe Selection",
             font=("Segoe UI", 16, "bold"), fg="#74b9ff", bg="#1f2937").pack(pady=25)

    timeframes = {
        "Short Term": ["1m", "3m", "5m", "15m"],
        "Medium Term": ["30m", "1h", "2h", "4h"],
        "Long Term": ["6h", "8h", "12h", "1d"]
    }

    for category, tfs in timeframes.items():
        card = ModernCard(tf_window, title=f"📅 {category}")
        card.pack(fill="x", padx=20, pady=10)

        content = tk.Frame(card, bg="#2d3436")
        content.pack(fill="x", padx=15, pady=15)

        btn_frame = tk.Frame(content, bg="#2d3436")
        btn_frame.pack(fill="x")

        for i, tf in enumerate(tfs):
            btn = ModernButton(btn_frame, text=tf,
                               command=lambda t=tf: select_timeframe(t, tf_window),
                               style="primary")
            btn.pack(side="left", fill="x", expand=True, padx=2)


def select_timeframe(tf, window):
    global selected_timeframe
    selected_timeframe = tf
    timeframe_var.set(f"Timeframe: {selected_timeframe}")
    logger.log(f"Timeframe changed to {selected_timeframe}", 'INFO')
    show_modern_notification(f"Timeframe changed to {selected_timeframe}", "info")
    window.destroy()


def open_settings():
    settings_window = tk.Toplevel(root)
    settings_window.title("⚙️ Trading Settings")
    settings_window.geometry("700x600")
    settings_window.configure(bg="#0d1117")

    header = tk.Frame(settings_window, bg="#1f2937", height=80)
    header.pack(fill="x")
    header.pack_propagate(False)

    tk.Label(header, text="⚙️ Trading Configuration",
             font=("Segoe UI", 16, "bold"), fg="#74b9ff", bg="#1f2937").pack(pady=25)

    main_frame = tk.Frame(settings_window, bg="#0d1117")
    main_frame.pack(fill="both", expand=True, padx=20, pady=20)

    risk_var = tk.DoubleVar(value=settings['risk_percent'])
    sl_var = tk.DoubleVar(value=settings['stop_loss_percent'])
    tp_var = tk.DoubleVar(value=settings['take_profit_percent'])

    def create_setting_row(parent, label, var, min_val, max_val, unit=""):
        card = ModernCard(parent, bg_color="#1f2937")
        card.pack(fill="x", pady=8)

        label_frame = tk.Frame(card, bg="#1f2937")
        label_frame.pack(fill="x", padx=15, pady=8)

        tk.Label(label_frame, text=f"{label}:", fg="white", bg="#1f2937",
                 font=("Segoe UI", 11, "bold")).pack(anchor="w")

        control_frame = tk.Frame(card, bg="#1f2937")
        control_frame.pack(fill="x", padx=15, pady=(0, 10))

        scale = ttk.Scale(control_frame, from_=min_val, to=max_val, variable=var, orient='horizontal')
        scale.pack(fill='x', pady=(5, 0))

        value_label = tk.Label(control_frame, text="", fg="#00ff88", bg="#1f2937",
                               font=("Segoe UI", 10, "bold"))
        value_label.pack(anchor="w", pady=(5, 0))

        def update_label():
            value_label.config(text=f"Value: {var.get():.1f}{unit}")
            control_frame.after(100, update_label)

        update_label()

    create_setting_row(main_frame, "💰 Risk per Trade", risk_var, 0.5, 10, "%")
    create_setting_row(main_frame, "🛡️ Stop Loss", sl_var, 0.5, 5, "%")
    create_setting_row(main_frame, "🎯 Take Profit", tp_var, 1, 10, "%")

    def save_settings():
        try:
            settings['risk_percent'] = risk_var.get()
            settings['stop_loss_percent'] = sl_var.get()
            settings['take_profit_percent'] = tp_var.get()

            for key, value in settings.items():
                config_manager.config.set('TRADING', key, str(value))
            config_manager.save_config()

            logger.log("Trading settings updated successfully", 'SUCCESS')
            show_modern_notification("Settings saved successfully!", "success")
            settings_window.destroy()

        except Exception as e:
            logger.log(f"Error saving settings: {e}", 'ERROR')
            show_modern_notification("Error saving settings", "error")

    save_frame = tk.Frame(settings_window, bg="#0d1117")
    save_frame.pack(fill="x", padx=20, pady=20)

    ModernButton(save_frame, text="💾 Save Settings", command=save_settings,
                 style="success").pack(side="right")


def show_trading_history():
    history_window = tk.Toplevel(root)
    history_window.title("📜 Trading History")
    history_window.geometry("1000x600")
    history_window.configure(bg="#0d1117")

    header = tk.Frame(history_window, bg="#1f2937", height=80)
    header.pack(fill="x")
    header.pack_propagate(False)

    tk.Label(header, text="📜 Trading History",
             font=("Segoe UI", 16, "bold"), fg="#74b9ff", bg="#1f2937").pack(pady=25)

    main_frame = tk.Frame(history_window, bg="#0d1117")
    main_frame.pack(fill="both", expand=True, padx=20, pady=20)

    cursor = bot.db_connection.cursor()
    cursor.execute('SELECT * FROM trades ORDER BY timestamp DESC LIMIT 100')
    trades = cursor.fetchall()

    if trades:
        columns = ("Time", "Symbol", "Side", "Quantity", "Price", "PnL", "Strategy")
        tree = ttk.Treeview(main_frame, columns=columns, show="headings", height=20)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120)

        for trade in trades:
            formatted_time = trade[1][:19] if len(trade[1]) > 19 else trade[1]
            tree.insert("", "end", values=(
                formatted_time, trade[2], trade[3], 
                f"{trade[4]:.6f}", f"${trade[5]:.6f}", 
                f"${trade[6]:+.2f}", trade[7]
            ))

        tree.pack(fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        
    else:
        tk.Label(main_frame, text="📭 No trading history available yet",
                 fg="#74b9ff", bg="#0d1117", font=("Segoe UI", 14)).pack(pady=100)


def show_market_scanner():
    scanner_window = tk.Toplevel(root)
    scanner_window.title("🔍 Market Scanner")
    scanner_window.geometry("800x600")
    scanner_window.configure(bg="#0d1117")

    header = tk.Frame(scanner_window, bg="#1f2937", height=80)
    header.pack(fill="x")
    header.pack_propagate(False)

    tk.Label(header, text="🔍 Market Scanner",
             font=("Segoe UI", 16, "bold"), fg="#74b9ff", bg="#1f2937").pack(pady=25)

    main_frame = tk.Frame(scanner_window, bg="#0d1117")
    main_frame.pack(fill="both", expand=True, padx=20, pady=20)

    if client:
        try:
            tickers = client.futures_ticker()
            volume_sorted = sorted(tickers, key=lambda x: float(x['quoteVolume']), reverse=True)[:20]
            
            scanner_card = ModernCard(main_frame, title="📊 Top Volume Symbols")
            scanner_card.pack(fill="both", expand=True)
            
            scanner_content = tk.Frame(scanner_card, bg="#2d3436")
            scanner_content.pack(fill="both", expand=True, padx=15, pady=15)
            
            columns = ("Rank", "Symbol", "Price", "Change%", "Volume", "Signal")
            tree = ttk.Treeview(scanner_content, columns=columns, show="headings", height=15)
            
            for col in columns:
                tree.heading(col, text=col)
                tree.column(col, width=100)

            for i, ticker in enumerate(volume_sorted):
                symbol = ticker['symbol']
                price = float(ticker['lastPrice'])
                change_percent = float(ticker['priceChangePercent'])
                volume = float(ticker['quoteVolume']) / 1000000
                
                signal_text = "🔥" if abs(change_percent) > 5 else "📈" if change_percent > 2 else "📉" if change_percent < -2 else "➡️"
                
                tree.insert("", "end", values=(
                    f"#{i+1}", symbol, f"${price:.6f}", 
                    f"{change_percent:+.2f}%", f"{volume:.1f}M", signal_text
                ))

            tree.pack(fill="both", expand=True)
            
            scrollbar = ttk.Scrollbar(scanner_content, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            scrollbar.pack(side="right", fill="y")
                
        except Exception as e:
            tk.Label(main_frame, text=f"Error loading scanner data: {e}",
                     fg="#ff4757", bg="#0d1117", font=("Segoe UI", 12)).pack(pady=50)
    else:
        tk.Label(main_frame, text="Please connect API first to use scanner",
                 fg="#74b9ff", bg="#0d1117", font=("Segoe UI", 12)).pack(pady=50)


def show_portfolio_analysis():
    portfolio_window = tk.Toplevel(root)
    portfolio_window.title("📈 Portfolio Analysis")
    portfolio_window.geometry("800x600")
    portfolio_window.configure(bg="#0d1117")

    header = tk.Frame(portfolio_window, bg="#1f2937", height=80)
    header.pack(fill="x")
    header.pack_propagate(False)

    tk.Label(header, text="📈 Portfolio Analytics",
             font=("Segoe UI", 16, "bold"), fg="#74b9ff", bg="#1f2937").pack(pady=25)

    main_frame = tk.Frame(portfolio_window, bg="#0d1117")
    main_frame.pack(fill="both", expand=True, padx=20, pady=20)

    if client and pnl_history:
        metrics_card = ModernCard(main_frame, title="📊 Performance Metrics")
        metrics_card.pack(fill="x", pady=10)
        
        metrics_content = tk.Frame(metrics_card, bg="#2d3436")
        metrics_content.pack(fill="x", padx=15, pady=15)
        
        total_trades = bot.daily_trade_count
        max_pnl = max(pnl_history) if pnl_history else 0
        min_pnl = min(pnl_history) if pnl_history else 0
        current_pnl = pnl_history[-1] if pnl_history else 0
        avg_pnl = np.mean(pnl_history) if pnl_history else 0
        
        metrics_text = f"""📊 Portfolio Performance Summary:

🎯 Total Trades Today: {total_trades}
💰 Current PnL: ${current_pnl:+.2f}
📈 Best Performance: ${max_pnl:+.2f}
📉 Worst Drawdown: ${min_pnl:+.2f}
🧮 Average PnL: ${avg_pnl:+.2f}
📋 Total Records: {len(pnl_history)}

💡 Performance Analysis:
Risk/Reward Ratio: {settings['take_profit_percent']/settings['stop_loss_percent']:.2f}:1
Daily Risk Limit: {settings['risk_percent']}% per trade"""

        tk.Label(metrics_content, text=metrics_text, fg="white", bg="#2d3436",
                 font=("Consolas", 10), justify="left").pack(anchor="w")
                 
    else:
        tk.Label(main_frame, text="📭 Connect API and start trading to see analytics",
                 fg="#74b9ff", bg="#0d1117", font=("Segoe UI", 14)).pack(pady=100)


def on_close():
    global running, auto_trading

    if auto_trading:
        confirm = messagebox.askyesno("Auto Trading Active",
                                      "Auto trading is still running.\n"
                                      "Stop auto trading and close application?")
        if not confirm:
            return

    running = False
    auto_trading = False
    logger.log("Application shutting down...", 'INFO')

    if update_thread and update_thread.is_alive():
        update_thread.join(timeout=2)
    if strategy_thread and strategy_thread.is_alive():
        strategy_thread.join(timeout=2)

    try:
        bot.db_connection.close()
    except:
        pass

    root.destroy()


# ===== Enhanced Log Frame =====
class EnhancedLogFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#1e1e2f")
        self.filter_var = tk.StringVar(value="ALL")
        self.setup_ui()

    def setup_ui(self):
        header = tk.Frame(self, bg="#2d3436", height=35)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header, text="📊 Activity Log",
                 font=("Segoe UI", 11, "bold"), fg="#74b9ff", bg="#2d3436").pack(side="left", padx=15, pady=8)

        filter_frame = tk.Frame(header, bg="#2d3436")
        filter_frame.pack(side="right", padx=15, pady=5)

        filters = ["ALL", "TRADE", "AUTO", "SIGNAL", "ERROR"]

        for filter_type in filters:
            color = "#74b9ff" if filter_type == "ALL" else logger.log_types.get(filter_type, {}).get('color', '#636e72')
            btn = tk.Button(filter_frame, text=filter_type,
                            command=lambda f=filter_type: self.set_filter(f),
                            bg=color, fg="white" if filter_type != "ALL" else "#2d3436",
                            font=("Segoe UI", 7, "bold"), relief="flat", bd=0,
                            padx=6, pady=2)
            btn.pack(side="left", padx=1)

        log_container = tk.Frame(self, bg="#1e1e2f")
        log_container.pack(fill="both", expand=True, padx=8, pady=8)

        self.log_canvas = tk.Canvas(log_container, bg="#1e1e2f", highlightthickness=0)
        self.log_scrollbar = ttk.Scrollbar(log_container, orient="vertical", command=self.log_canvas.yview)
        self.scrollable_frame = tk.Frame(self.log_canvas, bg="#1e1e2f")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.log_canvas.configure(scrollregion=self.log_canvas.bbox("all"))
        )

        self.log_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.log_canvas.configure(yscrollcommand=self.log_scrollbar.set)

        self.log_canvas.pack(side="left", fill="both", expand=True)
        self.log_scrollbar.pack(side="right", fill="y")

        def _on_mousewheel(event):
            self.log_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        self.log_canvas.bind("<MouseWheel>", _on_mousewheel)

    def set_filter(self, filter_type):
        self.filter_var.set(filter_type)
        self.update_log_display()

    def add_log_entry(self, log_entry):
        if self.filter_var.get() != "ALL" and log_entry['type'] != self.filter_var.get():
            return

        entry_frame = tk.Frame(self.scrollable_frame, bg="#2d3436", relief="flat", bd=1)
        entry_frame.pack(fill="x", padx=3, pady=1)

        header_frame = tk.Frame(entry_frame, bg="#2d3436")
        header_frame.pack(fill="x", padx=8, pady=3)

        time_label = tk.Label(header_frame, text=f"[{log_entry['timestamp']}]",
                              font=("Consolas", 8), fg="#636e72", bg="#2d3436")
        time_label.pack(side="left")

        icon_label = tk.Label(header_frame, text=log_entry['icon'],
                              font=("Segoe UI", 9), bg="#2d3436")
        icon_label.pack(side="left", padx=(8, 3))

        type_label = tk.Label(header_frame, text=log_entry['type'],
                              font=("Segoe UI", 8, "bold"),
                              fg=logger.log_types.get(log_entry['type'], {}).get('color', 'white'),
                              bg="#2d3436")
        type_label.pack(side="left")

        msg_label = tk.Label(entry_frame, text=log_entry['message'],
                             font=("Segoe UI", 9), fg="white", bg="#2d3436",
                             wraplength=280, justify="left")
        msg_label.pack(anchor="w", padx=10, pady=(0, 3))

        self.log_canvas.update_idletasks()
        self.log_canvas.yview_moveto(1)

    def update_log_display(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        logs = logger.get_recent_logs(50)
        for log_entry in reversed(logs):
            if self.filter_var.get() == "ALL" or log_entry['type'] == self.filter_var.get():
                self.add_log_entry(log_entry)


# ===== GUI Setup =====
root = tk.Tk()
root.title("🚀 Advanced Trading Bot v2.1 - Portfolio & Signal Dashboard")
root.geometry("1500x850")
root.configure(bg="#0d1117")
root.protocol("WM_DELETE_WINDOW", on_close)
root.resizable(True, True)

# Modern style configuration
style = ttk.Style()
style.theme_use("clam")

# ===== Clean Layout =====
# Header
header_frame = tk.Frame(root, bg="#1f2937", height=80)
header_frame.pack(fill="x")
header_frame.pack_propagate(False)

header_content = tk.Frame(header_frame, bg="#1f2937")
header_content.pack(fill="both", expand=True, padx=20, pady=15)

# Title
title_frame = tk.Frame(header_content, bg="#1f2937")
title_frame.pack(side="left", fill="y")

tk.Label(title_frame, text="🚀 Advanced Portfolio & Signal Dashboard",
         font=("Segoe UI", 18, "bold"), fg="#74b9ff", bg="#1f2937").pack(anchor="w")
tk.Label(title_frame, text="v2.1 Enhanced Edition - Real-time Portfolio Management & AI Signals",
         font=("Segoe UI", 10), fg="#a0a0a0", bg="#1f2937").pack(anchor="w", pady=(3, 0))

# Status panel
status_panel = tk.Frame(header_content, bg="#2d3436", relief="flat", bd=1)
status_panel.pack(side="right", padx=15)

status_content = tk.Frame(status_panel, bg="#2d3436")
status_content.pack(padx=15, pady=10)

price_var = tk.StringVar(value="📊 Loading...")
price_label = tk.Label(status_content, textvariable=price_var,
                       font=("Consolas", 10, "bold"), fg="#00ff88", bg="#2d3436")
price_label.pack()

balance_var = tk.StringVar(value="💰 Balance: Connecting...")
balance_label = tk.Label(status_content, textvariable=balance_var,
                         font=("Consolas", 9), fg="white", bg="#2d3436")
balance_label.pack()

pnl_var = tk.StringVar(value="📊 PnL: Connecting...")
pnl_label = tk.Label(status_content, textvariable=pnl_var,
                     font=("Consolas", 9), fg="white", bg="#2d3436")
pnl_label.pack()

connection_status = tk.StringVar(value="🔴 Disconnected")
connection_label = tk.Label(status_content, textvariable=connection_status,
                            fg="#74b9ff", bg="#2d3436", font=("Segoe UI", 8, "bold"))
connection_label.pack(pady=(5, 0))

# Main content container
main_container = tk.Frame(root, bg="#0d1117")
main_container.pack(fill="both", expand=True, padx=15, pady=15)

# ===== Left Panel - Control Center (CLEAN) =====
left_panel = tk.Frame(main_container, bg="#0d1117", width=300)
left_panel.pack(side="left", fill="y", padx=(0, 10))
left_panel.pack_propagate(False)

# Connection Card
connection_card = ModernCard(left_panel, title="🔗 API Connection")
connection_card.pack(fill="x", pady=5)

connection_content = tk.Frame(connection_card, bg="#2d3436")
connection_content.pack(fill="x", padx=10, pady=10)

ModernButton(connection_content, text="🔐 Setup & Connect API",
             command=setup_api_credentials, style="primary").pack(fill="x")

# Market Selection Card
market_card = ModernCard(left_panel, title="📊 Market Selection")
market_card.pack(fill="x", pady=5)

market_content = tk.Frame(market_card, bg="#2d3436")
market_content.pack(fill="x", padx=10, pady=10)

symbol_var = tk.StringVar(value=f"Symbol: {selected_symbol}")
symbol_label = tk.Label(market_content, textvariable=symbol_var, fg="white", bg="#2d3436",
                        font=("Segoe UI", 10, "bold"))
symbol_label.pack()

timeframe_var = tk.StringVar(value=f"Timeframe: {selected_timeframe}")
timeframe_label = tk.Label(market_content, textvariable=timeframe_var, fg="#a0a0a0", bg="#2d3436",
                           font=("Segoe UI", 9))
timeframe_label.pack()

market_btn_frame = tk.Frame(market_content, bg="#2d3436")
market_btn_frame.pack(fill="x", pady=8)

ModernButton(market_btn_frame, text="📈 Symbol", command=change_symbol,
             style="dark").pack(side="left", fill="x", expand=True, padx=(0, 3))
ModernButton(market_btn_frame, text="⏱️ Time", command=change_timeframe,
             style="dark").pack(side="right", fill="x", expand=True, padx=(3, 0))

# Trading Card
trading_card = ModernCard(left_panel, title="⚡ Manual Trading")
trading_card.pack(fill="x", pady=5)

trading_content = tk.Frame(trading_card, bg="#2d3436")
trading_content.pack(fill="x", padx=10, pady=10)

trade_btn_frame = tk.Frame(trading_content, bg="#2d3436")
trade_btn_frame.pack(fill="x", pady=5)

buy_btn = ModernButton(trade_btn_frame, text="📈 BUY",
                       command=lambda: place_smart_order(SIDE_BUY, "MANUAL"),
                       style="success")
buy_btn.pack(side="left", fill="x", expand=True, padx=(0, 3))

sell_btn = ModernButton(trade_btn_frame, text="📉 SELL",
                        command=lambda: place_smart_order(SIDE_SELL, "MANUAL"),
                        style="danger")
sell_btn.pack(side="right", fill="x", expand=True, padx=(3, 0))

risk_info = tk.Label(trading_content,
                     text=f"Risk: {settings['risk_percent']}% | SL: {settings['stop_loss_percent']}% | TP: {settings['take_profit_percent']}%",
                     fg="#74b9ff", bg="#2d3436", font=("Segoe UI", 8))
risk_info.pack(pady=(8, 0))

# ===== AUTO TRADING CARD - PROMINENT =====
auto_card = ModernCard(left_panel, title="🤖 AUTO TRADING", bg_color="#0d5016", title_color="#00ff88")
auto_card.pack(fill="x", pady=8)

auto_content = tk.Frame(auto_card, bg="#0d5016")
auto_content.pack(fill="x", padx=10, pady=12)

auto_btn = tk.Button(auto_content, text="🚀 START AUTO TRADING",
                     command=toggle_auto_trading,
                     bg="#00b894", fg="white",
                     font=("Segoe UI", 11, "bold"),
                     relief="flat", bd=0, padx=15, pady=10,
                     cursor="hand2")
auto_btn.pack(fill="x")

def on_auto_hover(event):
    auto_btn.config(bg="#00ff88")

def on_auto_leave(event):
    auto_btn.config(bg="#00b894")

auto_btn.bind("<Enter>", on_auto_hover)
auto_btn.bind("<Leave>", on_auto_leave)

auto_status = tk.StringVar(value="👤 Manual Mode")
auto_status_label = tk.Label(auto_content, textvariable=auto_status,
                             fg="#00ff88", bg="#0d5016", font=("Segoe UI", 10, "bold"))
auto_status_label.pack(pady=(8, 0))

safety_info = tk.Label(auto_content,
                       text=f"Daily: {bot.daily_trade_count}/{bot.max_daily_trades} trades",
                       fg="#a0a0a0", bg="#0d5016", font=("Segoe UI", 8))
safety_info.pack()

# Emergency Controls Card
emergency_card = ModernCard(left_panel, title="🚨 Emergency Controls", bg_color="#4a0e0e", title_color="#ff4757")
emergency_card.pack(fill="x", pady=5)

emergency_content = tk.Frame(emergency_card, bg="#4a0e0e")
emergency_content.pack(fill="x", padx=10, pady=10)

emergency_main_btn = tk.Button(emergency_content, text="🚨 EMERGENCY STOP",
                               command=emergency_stop,
                               bg="#d63031", fg="white",
                               font=("Segoe UI", 10, "bold"),
                               relief="raised", bd=2, padx=10, pady=6,
                               cursor="hand2")
emergency_main_btn.pack(fill="x", pady=(0, 5))

def on_emergency_hover(event):
    emergency_main_btn.config(bg="#ff7675")

def on_emergency_leave(event):
    emergency_main_btn.config(bg="#d63031")

emergency_main_btn.bind("<Enter>", on_emergency_hover)
emergency_main_btn.bind("<Leave>", on_emergency_leave)

emergency_btn_frame = tk.Frame(emergency_content, bg="#4a0e0e")
emergency_btn_frame.pack(fill="x")

ModernButton(emergency_btn_frame, text="❌ Close All", command=close_all_positions,
             style="warning").pack(side="left", fill="x", expand=True, padx=(0, 2))
ModernButton(emergency_btn_frame, text="🚫 Cancel All", command=cancel_all_orders,
             style="warning").pack(side="right", fill="x", expand=True, padx=(2, 0))

# Tools Card
tools_card = ModernCard(left_panel, title="📊 Tools")
tools_card.pack(fill="x", pady=5)

tools_content = tk.Frame(tools_card, bg="#2d3436")
tools_content.pack(fill="x", padx=10, pady=10)

tools_btn_frame1 = tk.Frame(tools_content, bg="#2d3436")
tools_btn_frame1.pack(fill="x", pady=2)

ModernButton(tools_btn_frame1, text="🔍 Scanner", command=show_market_scanner,
             style="primary").pack(side="left", fill="x", expand=True, padx=(0, 2))
ModernButton(tools_btn_frame1, text="📈 Analytics", command=show_portfolio_analysis,
             style="primary").pack(side="right", fill="x", expand=True, padx=(2, 0))

tools_btn_frame2 = tk.Frame(tools_content, bg="#2d3436")
tools_btn_frame2.pack(fill="x", pady=2)

ModernButton(tools_btn_frame2, text="📜 History", command=show_trading_history,
             style="dark").pack(side="left", fill="x", expand=True, padx=(0, 2))
ModernButton(tools_btn_frame2, text="⚙️ Settings", command=open_settings,
             style="dark").pack(side="right", fill="x", expand=True, padx=(2, 0))

# ===== Center Panel - Portfolio Manager =====
center_panel = tk.Frame(main_container, bg="#0d1117")
center_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))

portfolio_manager = PortfolioManager(center_panel)
portfolio_manager.pack(fill="both", expand=True)
root.portfolio_manager = portfolio_manager

# ===== Right Panel - Signal Dashboard =====
right_panel = tk.Frame(main_container, bg="#0d1117", width=380)
right_panel.pack(side="right", fill="y")
right_panel.pack_propagate(False)

signal_dashboard = SignalDashboard(right_panel)
signal_dashboard.pack(fill="both", expand=True)
root.signal_dashboard = signal_dashboard

# ===== Activity Log at Bottom =====
bottom_panel = tk.Frame(root, bg="#0d1117", height=120)
bottom_panel.pack(fill="x", side="bottom", padx=15, pady=(0, 15))
bottom_panel.pack_propagate(False)

log_frame = EnhancedLogFrame(bottom_panel)
log_frame.pack(fill="both", expand=True)

def update_log_ui(log_entry):
    try:
        root.after(0, lambda: log_frame.add_log_entry(log_entry))
    except Exception as e:
        print(f"Log UI update error: {e}")

logger.ui_callback = update_log_ui

# ===== Status Bar =====
status_bar = tk.Frame(root, bg="#1f2937", height=40)
status_bar.pack(fill="x", side="bottom")
status_bar.pack_propagate(False)

status_content = tk.Frame(status_bar, bg="#1f2937")
status_content.pack(fill="both", expand=True, padx=20, pady=8)

tk.Label(status_content, text="🚀 Portfolio & Signal Edition v2.1", fg="#74b9ff", bg="#1f2937",
         font=("Segoe UI", 10, "bold")).pack(side="left")

auto_status = tk.StringVar(value="👤 Manual Mode")
tk.Label(status_content, textvariable=auto_status, fg="#74b9ff", bg="#1f2937",
         font=("Segoe UI", 10, "bold")).pack(side="left", padx=50)

safety_status = tk.StringVar(value=f"🚦 Daily: {bot.daily_trade_count}/{bot.max_daily_trades}")
tk.Label(status_content, textvariable=safety_status, fg="#ffeaa7", bg="#1f2937",
         font=("Segoe UI", 10, "bold")).pack(side="right")


def update_status_indicators():
    try:
        if client:
            api_key, api_secret, testnet = config_manager.get_api_credentials()
            env_type = "🧪 Testnet" if testnet else "🔴 Live"
            connection_status.set(f"🟢 Connected ({env_type})")
        else:
            connection_status.set("🔴 Disconnected")

        if auto_trading:
            auto_status.set("🤖 Auto Trading ACTIVE")
            auto_btn.configure(text="🛑 STOP AUTO TRADING")
        else:
            auto_status.set("👤 Manual Mode")
            auto_btn.configure(text="🚀 START AUTO TRADING")

        safety_status.set(f"🚦 Daily: {bot.daily_trade_count}/{bot.max_daily_trades}")
        safety_info.config(text=f"Daily: {bot.daily_trade_count}/{bot.max_daily_trades} trades")

        root.after(2000, update_status_indicators)
    except:
        root.after(2000, update_status_indicators)


# Initialize application
logger.log("🚀 Advanced Portfolio & Signal Dashboard v2.1 initialized", 'SUCCESS')
logger.log("Enhanced Portfolio Management and Real-time Signal Analysis Ready", 'INFO')
logger.log("Modern interface with comprehensive trading tools", 'INFO')
logger.log("Click 'Setup & Connect API' to begin trading", 'AUTO')

# Start status updates
update_status_indicators()

# Keybindings
root.bind('<F1>', lambda e: logger.log("F1 - Portfolio shortcut triggered", 'INFO'))
root.bind('<F2>', lambda e: logger.log("F2 - Signals shortcut triggered", 'INFO'))
root.bind('<Escape>', lambda e: emergency_stop())

# Start the interface
if __name__ == "__main__":
    logger.log("Starting Portfolio & Signal Dashboard interface...", 'SUCCESS')
    root.mainloop()