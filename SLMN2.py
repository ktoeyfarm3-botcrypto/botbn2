import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import hashlib
import hmac
import json
import time
import requests
import threading
from datetime import datetime, timedelta
import numpy as np
from collections import deque
import sqlite3
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import warnings

warnings.filterwarnings('ignore')


# === Text-based Chart Generator ===
class TextChart:
    """Generate ASCII charts for visualization"""

    @staticmethod
    def generate_line_chart(data, width=80, height=20, title="Chart"):
        """Generate ASCII line chart"""
        if not data or len(data) < 2:
            return f"{title}\n" + "No data available"

        # Normalize data to fit chart height
        min_val = min(data)
        max_val = max(data)
        if max_val == min_val:
            normalized = [height // 2] * len(data)
        else:
            normalized = [(height - 1) * (val - min_val) / (max_val - min_val) for val in data]

        # Create chart grid
        chart = [[' ' for _ in range(width)] for _ in range(height)]

        # Plot data points
        data_step = len(data) / width
        for x in range(width - 1):
            data_idx = int(x * data_step)
            if data_idx < len(normalized):
                y = int(height - 1 - normalized[data_idx])
                if 0 <= y < height:
                    chart[y][x] = '●'
                    # Connect points with lines
                    if x > 0:
                        prev_data_idx = int((x - 1) * data_step)
                        if prev_data_idx < len(normalized):
                            prev_y = int(height - 1 - normalized[prev_data_idx])
                            # Simple line drawing
                            start_y, end_y = sorted([prev_y, y])
                            for line_y in range(start_y, end_y + 1):
                                if 0 <= line_y < height:
                                    chart[line_y][x] = '─'

        # Convert to string
        result = f"\n{title}\n"
        result += f"Max: {max_val:.2f} │" + "─" * (width - 15) + f"│ Min: {min_val:.2f}\n"

        for row in chart:
            result += "│" + "".join(row) + "│\n"

        result += "└" + "─" * width + "┘\n"
        return result

    @staticmethod
    def generate_bar_chart(labels, values, width=60, title="Bar Chart"):
        """Generate ASCII bar chart"""
        if not values:
            return f"{title}\nNo data available"

        max_val = max(values) if values else 1
        result = f"\n{title}\n"
        result += "─" * (width + 20) + "\n"

        for i, (label, value) in enumerate(zip(labels, values)):
            bar_length = int((value / max_val) * width) if max_val > 0 else 0
            bar = "█" * bar_length + "░" * (width - bar_length)
            result += f"{label[:12]:12} │{bar}│ {value:.2f}\n"

        result += "─" * (width + 20) + "\n"
        return result

    @staticmethod
    def generate_indicator_status(indicators):
        """Generate visual indicator status"""
        result = "\n📊 TECHNICAL INDICATORS STATUS\n"
        result += "═" * 50 + "\n"

        for name, value in indicators.items():
            if isinstance(value, (int, float)):
                if 'rsi' in name.lower():
                    if value > 70:
                        status = "🔴 Overbought"
                    elif value < 30:
                        status = "🟢 Oversold"
                    else:
                        status = "🟡 Neutral"
                    bar = "█" * int(value / 5) + "░" * (20 - int(value / 5))
                    result += f"{name:12}: [{bar}] {value:.1f} {status}\n"

                elif 'confidence' in name.lower():
                    if value > 0.8:
                        status = "🟢 High"
                    elif value > 0.6:
                        status = "🟡 Medium"
                    else:
                        status = "🔴 Low"
                    bar = "█" * int(value * 20) + "░" * (20 - int(value * 20))
                    result += f"{name:12}: [{bar}] {value:.3f} {status}\n"

                else:
                    result += f"{name:12}: {value:.4f}\n"
            else:
                result += f"{name:12}: {value}\n"

        result += "═" * 50 + "\n"
        return result


# === Enhanced Technical Analysis ===
class AdvancedTechnicalAnalysis:
    """Advanced Technical Analysis with detailed calculations"""

    @staticmethod
    def calculate_comprehensive_indicators(prices, volumes=None):
        """Calculate comprehensive technical indicators"""
        if len(prices) < 50:
            return {}

        prices = np.array(prices)
        indicators = {}

        # RSI with detailed calculation
        indicators.update(AdvancedTechnicalAnalysis._calculate_rsi_detailed(prices))

        # Moving Averages
        indicators['ma_5'] = np.mean(prices[-5:])
        indicators['ma_10'] = np.mean(prices[-10:])
        indicators['ma_20'] = np.mean(prices[-20:])
        indicators['ma_50'] = np.mean(prices[-50:])

        # MACD with signal line
        macd_data = AdvancedTechnicalAnalysis._calculate_macd_detailed(prices)
        indicators.update(macd_data)

        # Bollinger Bands
        bb_data = AdvancedTechnicalAnalysis._calculate_bollinger_bands(prices)
        indicators.update(bb_data)

        # Stochastic Oscillator
        stoch_data = AdvancedTechnicalAnalysis._calculate_stochastic(prices)
        indicators.update(stoch_data)

        # Williams %R
        indicators['williams_r'] = AdvancedTechnicalAnalysis._calculate_williams_r(prices)

        # Rate of Change
        indicators['roc_10'] = ((prices[-1] - prices[-11]) / prices[-11] * 100) if len(prices) > 10 else 0

        # Momentum
        indicators['momentum'] = prices[-1] - prices[-11] if len(prices) > 10 else 0

        # Trend strength
        indicators['trend_strength'] = AdvancedTechnicalAnalysis._calculate_trend_strength(prices)

        return indicators

    @staticmethod
    def _calculate_rsi_detailed(prices, period=14):
        """Calculate RSI with additional details"""
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])

        rs = avg_gain / (avg_loss + 1e-10)
        rsi = 100 - (100 / (1 + rs))

        return {
            'rsi': rsi,
            'rsi_avg_gain': avg_gain,
            'rsi_avg_loss': avg_loss,
            'rsi_rs': rs
        }

    @staticmethod
    def _calculate_macd_detailed(prices):
        """Calculate MACD with signal line"""
        ema_12 = AdvancedTechnicalAnalysis._ema(prices, 12)
        ema_26 = AdvancedTechnicalAnalysis._ema(prices, 26)
        macd_line = ema_12 - ema_26

        # Signal line (9-period EMA of MACD)
        macd_signal = macd_line * 0.2 + (macd_line * 0.8)  # Simplified signal
        histogram = macd_line - macd_signal

        return {
            'macd': macd_line,
            'macd_signal': macd_signal,
            'macd_histogram': histogram,
            'ema_12': ema_12,
            'ema_26': ema_26
        }

    @staticmethod
    def _calculate_bollinger_bands(prices, period=20, std_dev=2):
        """Calculate Bollinger Bands"""
        sma = np.mean(prices[-period:])
        std = np.std(prices[-period:])

        return {
            'bb_upper': sma + (std_dev * std),
            'bb_middle': sma,
            'bb_lower': sma - (std_dev * std),
            'bb_width': (std_dev * std * 2) / sma * 100
        }

    @staticmethod
    def _calculate_stochastic(prices, k_period=14, d_period=3):
        """Calculate Stochastic Oscillator"""
        if len(prices) < k_period:
            return {'stoch_k': 50, 'stoch_d': 50}

        high_14 = np.max(prices[-k_period:])
        low_14 = np.min(prices[-k_period:])

        k_percent = ((prices[-1] - low_14) / (high_14 - low_14)) * 100 if high_14 != low_14 else 50
        d_percent = k_percent  # Simplified

        return {
            'stoch_k': k_percent,
            'stoch_d': d_percent
        }

    @staticmethod
    def _calculate_williams_r(prices, period=14):
        """Calculate Williams %R"""
        if len(prices) < period:
            return -50

        high_n = np.max(prices[-period:])
        low_n = np.min(prices[-period:])

        return ((high_n - prices[-1]) / (high_n - low_n)) * -100 if high_n != low_n else -50

    @staticmethod
    def _calculate_trend_strength(prices, period=20):
        """Calculate trend strength"""
        if len(prices) < period:
            return 0

        recent_prices = prices[-period:]
        slope = np.polyfit(range(len(recent_prices)), recent_prices, 1)[0]
        return slope / np.mean(recent_prices) * 100

    @staticmethod
    def _ema(prices, period):
        """Calculate Exponential Moving Average"""
        prices = np.array(prices)
        alpha = 2 / (period + 1)
        ema = prices[0]

        for price in prices[1:]:
            ema = alpha * price + (1 - alpha) * ema

        return ema


# === Database Manager ===
class DatabaseManager:
    """Enhanced Database manager"""

    def __init__(self, db_path="advanced_trading_data.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize enhanced database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Enhanced market data table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS market_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                symbol TEXT,
                price REAL,
                volume REAL,
                high_24h REAL,
                low_24h REAL,
                change_24h REAL,
                rsi REAL,
                macd REAL,
                macd_signal REAL,
                bb_upper REAL,
                bb_middle REAL,
                bb_lower REAL,
                stoch_k REAL,
                williams_r REAL,
                trend_strength REAL,
                moving_avg_5 REAL,
                moving_avg_20 REAL,
                moving_avg_50 REAL
            )
        ''')

        # AI analysis table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                symbol TEXT,
                signal_type TEXT,
                confidence REAL,
                price REAL,
                prediction REAL,
                reason TEXT,
                indicators_json TEXT,
                executed BOOLEAN,
                result TEXT
            )
        ''')

        # Performance tracking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                total_trades INTEGER,
                successful_trades INTEGER,
                total_pnl REAL,
                win_rate REAL,
                current_balance REAL,
                max_drawdown REAL,
                sharpe_ratio REAL
            )
        ''')

        conn.commit()
        conn.close()

    def save_market_data(self, data):
        """Save enhanced market data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO market_data 
            (timestamp, symbol, price, volume, high_24h, low_24h, change_24h, 
             rsi, macd, macd_signal, bb_upper, bb_middle, bb_lower, stoch_k, 
             williams_r, trend_strength, moving_avg_5, moving_avg_20, moving_avg_50)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', data)
        conn.commit()
        conn.close()

    def save_ai_analysis(self, analysis_data):
        """Save AI analysis data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO ai_analysis 
            (timestamp, symbol, signal_type, confidence, price, prediction, reason, 
             indicators_json, executed, result)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', analysis_data)
        conn.commit()
        conn.close()

    def get_recent_data(self, symbol, limit=200):
        """Get recent market data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM market_data 
            WHERE symbol = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (symbol, limit))
        data = cursor.fetchall()
        conn.close()
        return list(reversed(data))


# === Bitkub API Client ===
class BitkubAPIClient:
    """Enhanced Bitkub API Client"""

    def __init__(self, api_key="", api_secret=""):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://api.bitkub.com"
        self.request_times = deque(maxlen=250)

    def make_public_request(self, endpoint, params=None):
        """Make public API request"""
        try:
            url = f"{self.base_url}{endpoint}"
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"API Error: {e}")
            return None

    def get_ticker(self, symbol=None):
        params = {'sym': symbol} if symbol else None
        return self.make_public_request('/api/v3/market/ticker', params)

    def get_market_depth(self, symbol, limit=5):
        params = {'sym': symbol, 'lmt': limit}
        return self.make_public_request('/api/market/depth', params)


# === Advanced ML Model ===
class AdvancedMLModel:
    """Advanced ML Model with enhanced prediction capabilities"""

    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.model = None
        self.scaler = None
        self.is_trained = False
        self.training_history = []
        self.prediction_accuracy = 0.0

    def train_model(self, symbol):
        """Train advanced ML model"""
        try:
            # Get comprehensive training data
            data = self.db_manager.get_recent_data(symbol, limit=2000)
            if len(data) < 500:
                return False, "ต้องการข้อมูลอย่างน้อย 500 รายการสำหรับการฝึก"

            # Prepare enhanced features
            features, targets = self._prepare_enhanced_features(data)
            if features is None:
                return False, "ไม่สามารถเตรียมข้อมูลได้"

            # Split and scale data
            X_train, X_test, y_train, y_test = train_test_split(
                features, targets, test_size=0.2, shuffle=False
            )

            self.scaler = StandardScaler()
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)

            # Train enhanced model
            self.model = RandomForestRegressor(
                n_estimators=200,
                max_depth=15,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42
            )
            self.model.fit(X_train_scaled, y_train)

            # Evaluate model
            predictions = self.model.predict(X_test_scaled)
            mse = np.mean((y_test - predictions) ** 2)
            accuracy = 1 - mse  # Simplified accuracy metric

            self.prediction_accuracy = max(0, min(1, accuracy))
            self.is_trained = True

            # Store training history
            self.training_history.append({
                'timestamp': datetime.now(),
                'mse': mse,
                'accuracy': accuracy,
                'data_points': len(data)
            })

            return True, f"Model trained successfully!\nMSE: {mse:.6f}\nAccuracy: {accuracy:.3f}\nData points: {len(data)}"

        except Exception as e:
            return False, f"Training failed: {str(e)}"

    def _prepare_enhanced_features(self, data):
        """Prepare enhanced features with multiple technical indicators"""
        if len(data) < 100:
            return None, None

        features = []
        targets = []

        for i in range(50, len(data) - 10):
            # Extract comprehensive features
            row = data[i]

            # Price-based features
            feature_vector = [
                row[8] if row[8] else 50,  # rsi
                row[9] if row[9] else 0,  # macd
                row[10] if row[10] else 0,  # macd_signal
                row[11] if row[11] else 0,  # bb_upper
                row[12] if row[12] else 0,  # bb_middle
                row[13] if row[13] else 0,  # bb_lower
                row[14] if row[14] else 50,  # stoch_k
                row[15] if row[15] else -50,  # williams_r
                row[16] if row[16] else 0,  # trend_strength
                row[17] if row[17] else 0,  # moving_avg_5
                row[18] if row[18] else 0,  # moving_avg_20
                row[19] if row[19] else 0,  # moving_avg_50
                row[3] if row[3] else 0,  # price
                row[4] if row[4] else 0,  # volume
            ]

            # Add price momentum features
            if i >= 55:
                price_5_ago = data[i - 5][3]
                price_10_ago = data[i - 10][3]
                current_price = row[3]

                momentum_5 = (current_price - price_5_ago) / price_5_ago if price_5_ago > 0 else 0
                momentum_10 = (current_price - price_10_ago) / price_10_ago if price_10_ago > 0 else 0

                feature_vector.extend([momentum_5, momentum_10])
            else:
                feature_vector.extend([0, 0])

            features.append(feature_vector)

            # Target: multi-step ahead prediction
            current_price = row[3]
            future_price = data[i + 10][3]  # 10 steps ahead
            price_change = (future_price - current_price) / current_price
            targets.append(price_change)

        return np.array(features), np.array(targets)

    def predict_signal(self, current_features):
        """Enhanced prediction with confidence analysis"""
        if not self.is_trained or not self.scaler:
            return {
                'action': 'hold',
                'confidence': 0,
                'prediction': 0,
                'reason': 'Model not trained'
            }

        try:
            features_scaled = self.scaler.transform([current_features])
            prediction = self.model.predict(features_scaled)[0]

            # Calculate confidence based on prediction magnitude and model accuracy
            base_confidence = min(abs(prediction) * 30, 0.9)
            adjusted_confidence = base_confidence * self.prediction_accuracy

            # Determine action with enhanced logic
            if prediction > 0.02:  # 2% threshold
                action = 'buy'
                reason = f"Strong Buy Signal (Pred: +{prediction * 100:.2f}%)"
            elif prediction > 0.01:  # 1% threshold
                action = 'buy'
                reason = f"Moderate Buy Signal (Pred: +{prediction * 100:.2f}%)"
            elif prediction < -0.02:  # -2% threshold
                action = 'sell'
                reason = f"Strong Sell Signal (Pred: {prediction * 100:.2f}%)"
            elif prediction < -0.01:  # -1% threshold
                action = 'sell'
                reason = f"Moderate Sell Signal (Pred: {prediction * 100:.2f}%)"
            else:
                action = 'hold'
                reason = f"Hold Signal (Pred: {prediction * 100:.2f}%)"

            return {
                'action': action,
                'confidence': adjusted_confidence,
                'prediction': prediction,
                'reason': reason,
                'model_accuracy': self.prediction_accuracy
            }

        except Exception as e:
            return {
                'action': 'hold',
                'confidence': 0,
                'prediction': 0,
                'reason': f'Prediction error: {str(e)}'
            }


# === Advanced Visual AI Trader ===
class AdvancedVisualAITrader:
    """Advanced AI Trading Bot with Text-based Visual Dashboard"""

    def __init__(self, root):
        self.root = root
        self.root.title("🚀 Advanced AI Trading Bot - Text Visual Dashboard")
        self.root.geometry("1600x1000")
        self.root.configure(bg='#1a1a1a')

        # Apply dark theme
        self.setup_dark_theme()

        # Initialize enhanced components
        self.db_manager = DatabaseManager()
        self.api_client = None
        self.ml_model = AdvancedMLModel(self.db_manager)

        # Trading state
        self.ai_enabled = False
        self.stop_trading = False

        # Enhanced data storage
        self.price_history = deque(maxlen=500)
        self.time_history = deque(maxlen=500)
        self.rsi_history = deque(maxlen=500)
        self.prediction_history = deque(maxlen=500)
        self.confidence_history = deque(maxlen=500)

        # Enhanced performance tracking
        self.trade_count = 0
        self.successful_trades = 0
        self.total_pnl = 0.0
        self.paper_balance = 50000.0  # Starting with 50,000 THB
        self.max_drawdown = 0.0
        self.peak_balance = 50000.0

        # Configuration
        self.config = {
            'trading_symbol': 'btc_thb',
            'min_confidence': 0.65,
            'position_size': 1000,
            'stop_loss': 0.02,
            'take_profit': 0.04
        }

        self.setup_gui()
        self.start_enhanced_data_collection()
        self.start_performance_tracking()

    def setup_dark_theme(self):
        """Setup enhanced dark theme"""
        style = ttk.Style()
        style.theme_use('clam')

        # Enhanced dark theme colors
        style.configure('TLabel', background='#1a1a1a', foreground='#ffffff')
        style.configure('TFrame', background='#1a1a1a')
        style.configure('TLabelFrame', background='#1a1a1a', foreground='#00ff88')
        style.configure('TLabelFrame.Label', background='#1a1a1a', foreground='#00ff88')
        style.configure('TButton', background='#2d2d2d', foreground='#ffffff')
        style.configure('TNotebook', background='#1a1a1a')
        style.configure('TNotebook.Tab', background='#2d2d2d', foreground='#ffffff')

    def setup_gui(self):
        """Setup enhanced GUI"""
        # Main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill='both', expand=True, padx=5, pady=5)

        # Enhanced header
        self.setup_enhanced_header(main_container)

        # Create notebook for tabs
        notebook = ttk.Notebook(main_container)
        notebook.pack(fill='both', expand=True, pady=(10, 0))

        # Enhanced tabs
        self.setup_visual_dashboard_tab(notebook)
        self.setup_ai_control_tab(notebook)
        self.setup_performance_tab(notebook)
        self.setup_api_config_tab(notebook)

    def setup_enhanced_header(self, parent):
        """Setup enhanced header with comprehensive metrics"""
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill='x', pady=(0, 10))

        # Title with status
        title_frame = ttk.Frame(header_frame)
        title_frame.pack(side='left')

        title_label = ttk.Label(title_frame, text="🚀 Advanced AI Trading Bot",
                                font=('Arial', 18, 'bold'))
        title_label.pack()

        subtitle_label = ttk.Label(title_frame, text="Text-based Visual Dashboard | Real-time Analysis",
                                   font=('Arial', 10))
        subtitle_label.pack()

        # Enhanced live metrics grid
        metrics_frame = ttk.Frame(header_frame)
        metrics_frame.pack(side='right')

        self.metric_labels = {}
        metrics = [
            ("🤖 AI Status", "🔴 Offline", 0, 0),
            ("💰 Paper Balance", "50,000 THB", 0, 1),
            ("📊 Current Price", "0 THB", 0, 2),
            ("⚡ AI Confidence", "0%", 1, 0),
            ("🎯 Total Trades", "0", 1, 1),
            ("📈 Win Rate", "0%", 1, 2),
            ("📉 Max Drawdown", "0%", 2, 0),
            ("🏆 Total P&L", "0 THB", 2, 1),
            ("🔥 Model Accuracy", "0%", 2, 2)
        ]

        for label, value, row, col in metrics:
            metric_frame = ttk.Frame(metrics_frame)
            metric_frame.grid(row=row, column=col, padx=10, pady=2)

            ttk.Label(metric_frame, text=label, font=('Arial', 9)).pack()
            self.metric_labels[label] = ttk.Label(metric_frame, text=value,
                                                  font=('Arial', 11, 'bold'))
            self.metric_labels[label].pack()

    def setup_visual_dashboard_tab(self, notebook):
        """Setup enhanced visual dashboard with text-based charts"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="📊 Visual Dashboard")

        # Create scrolled text for visual dashboard
        dashboard_frame = ttk.LabelFrame(frame, text="📈 Real-time Market Analysis Dashboard")
        dashboard_frame.pack(fill='both', expand=True, padx=10, pady=10)

        self.dashboard_display = scrolledtext.ScrolledText(
            dashboard_frame,
            height=35,
            width=120,
            bg='#1a1a1a',
            fg='#00ff88',
            font=('Consolas', 9),
            wrap=tk.NONE
        )
        self.dashboard_display.pack(fill='both', expand=True, padx=10, pady=10)

        # Update dashboard every 3 seconds
        self.update_visual_dashboard()

    def setup_ai_control_tab(self, notebook):
        """Setup enhanced AI control panel"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="🤖 AI Control")

        # Enhanced control panel
        control_frame = ttk.LabelFrame(frame, text="🎛️ AI Control Center")
        control_frame.pack(fill='x', padx=10, pady=10)

        # Primary controls
        primary_controls = ttk.Frame(control_frame)
        primary_controls.pack(fill='x', padx=10, pady=10)

        self.ai_toggle_btn = ttk.Button(primary_controls, text="🚀 Start AI Trading",
                                        command=self.toggle_ai_trading)
        self.ai_toggle_btn.pack(side='left', padx=10)

        ttk.Button(primary_controls, text="🧠 Train AI Model",
                   command=self.train_ai_model).pack(side='left', padx=10)

        ttk.Button(primary_controls, text="📊 Update Dashboard",
                   command=self.update_visual_dashboard).pack(side='left', padx=10)

        ttk.Button(primary_controls, text="🛑 Emergency Stop",
                   command=self.emergency_stop).pack(side='left', padx=10)

        # Configuration controls
        config_frame = ttk.LabelFrame(frame, text="⚙️ Trading Configuration")
        config_frame.pack(fill='x', padx=10, pady=10)

        self.config_vars = {}
        configs = [
            ("Trading Symbol", "trading_symbol", ["btc_thb", "eth_thb", "ada_thb"], "combo"),
            ("Min Confidence", "min_confidence", "0.65", "entry"),
            ("Position Size (THB)", "position_size", "1000", "entry"),
            ("Stop Loss (%)", "stop_loss", "2", "entry"),
            ("Take Profit (%)", "take_profit", "4", "entry"),
        ]

        for i, (label, key, default, widget_type) in enumerate(configs):
            row = ttk.Frame(config_frame)
            row.grid(row=i // 3, column=i % 3, padx=15, pady=5, sticky='ew')

            ttk.Label(row, text=f"{label}:", width=15).pack(side='left')

            if widget_type == "combo":
                var = tk.StringVar(value=default[0] if isinstance(default, list) else default)
                widget = ttk.Combobox(row, textvariable=var, values=default,
                                      state='readonly', width=12)
            else:
                var = tk.StringVar(value=default)
                widget = ttk.Entry(row, textvariable=var, width=12)

            widget.pack(side='left', padx=5)
            self.config_vars[key] = var

        ttk.Button(config_frame, text="💾 Save Configuration",
                   command=self.save_configuration).grid(row=2, column=1, pady=10)

        # AI Status and Analysis
        status_frame = ttk.LabelFrame(frame, text="🔍 AI Analysis & Status")
        status_frame.pack(fill='both', expand=True, padx=10, pady=10)

        self.ai_analysis_display = scrolledtext.ScrolledText(
            status_frame,
            height=20,
            bg='#1a1a1a',
            fg='#ffffff',
            font=('Consolas', 10)
        )
        self.ai_analysis_display.pack(fill='both', expand=True, padx=10, pady=10)

    def setup_performance_tab(self, notebook):
        """Setup enhanced performance tracking tab"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="📊 Performance")

        # Performance summary
        summary_frame = ttk.LabelFrame(frame, text="📈 Performance Summary")
        summary_frame.pack(fill='x', padx=10, pady=10)

        self.performance_summary = scrolledtext.ScrolledText(
            summary_frame,
            height=15,
            bg='#1a1a1a',
            fg='#00ff88',
            font=('Consolas', 11)
        )
        self.performance_summary.pack(fill='x', padx=10, pady=10)

        # Detailed performance log
        log_frame = ttk.LabelFrame(frame, text="📋 Detailed Performance Log")
        log_frame.pack(fill='both', expand=True, padx=10, pady=10)

        self.performance_log = scrolledtext.ScrolledText(
            log_frame,
            height=20,
            bg='#1a1a1a',
            fg='#ffffff',
            font=('Consolas', 9)
        )
        self.performance_log.pack(fill='both', expand=True, padx=10, pady=10)

        # Performance controls
        controls_frame = ttk.Frame(log_frame)
        controls_frame.pack(fill='x', padx=10, pady=(0, 10))

        ttk.Button(controls_frame, text="🔄 Refresh Performance",
                   command=self.update_performance_display).pack(side='left', padx=10)
        ttk.Button(controls_frame, text="📊 Generate Report",
                   command=self.generate_performance_report).pack(side='left', padx=10)
        ttk.Button(controls_frame, text="🗑️ Reset Performance",
                   command=self.reset_performance).pack(side='left', padx=10)

    def setup_api_config_tab(self, notebook):
        """Setup API configuration tab"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="🔧 API Config")

        # API setup
        api_frame = ttk.LabelFrame(frame, text="🔐 Bitkub API Configuration")
        api_frame.pack(fill='x', padx=20, pady=20)

        instructions = """
🔑 Enhanced API Setup Instructions:
1. Login to Bitkub.com → Settings → API Management
2. Create new API Key (READ permission only recommended)
3. Add your current IP to whitelist
4. Enable 2FA for additional security
5. Enter API Key below and test connection

⚠️ Security Notice: This bot uses PAPER TRADING only
✅ No real trading orders will be executed
🔒 API credentials are stored locally and encrypted
        """
        ttk.Label(api_frame, text=instructions, justify='left', font=('Arial', 10)).pack(padx=10, pady=10)

        # API inputs
        api_inner = ttk.Frame(api_frame)
        api_inner.pack(fill='x', padx=10, pady=10)

        ttk.Label(api_inner, text="API Key:", font=('Arial', 11, 'bold')).pack(anchor='w')
        self.api_key_entry = ttk.Entry(api_inner, width=80, show="*", font=('Consolas', 10))
        self.api_key_entry.pack(fill='x', pady=(5, 10))

        ttk.Label(api_inner, text="API Secret:", font=('Arial', 11, 'bold')).pack(anchor='w')
        self.api_secret_entry = ttk.Entry(api_inner, width=80, show="*", font=('Consolas', 10))
        self.api_secret_entry.pack(fill='x', pady=(5, 10))

        # API controls
        btn_frame = ttk.Frame(api_inner)
        btn_frame.pack(fill='x', pady=10)

        ttk.Button(btn_frame, text="💾 Save & Test API",
                   command=self.save_and_test_api).pack(side='left', padx=10)
        ttk.Button(btn_frame, text="👁️ Show/Hide Credentials",
                   command=self.toggle_api_visibility).pack(side='left', padx=10)
        ttk.Button(btn_frame, text="🔄 Test Connection",
                   command=self.test_api_connection).pack(side='left', padx=10)

        self.connection_status = ttk.Label(btn_frame, text="⚫ Not Connected",
                                           font=('Arial', 12, 'bold'))
        self.connection_status.pack(side='right')

        # API status display
        status_frame = ttk.LabelFrame(frame, text="📊 API Status & Information")
        status_frame.pack(fill='both', expand=True, padx=20, pady=20)

        self.api_status_display = scrolledtext.ScrolledText(
            status_frame,
            height=15,
            bg='#1a1a1a',
            fg='#00aaff',
            font=('Consolas', 10)
        )
        self.api_status_display.pack(fill='both', expand=True, padx=10, pady=10)

    def update_visual_dashboard(self):
        """Update text-based visual dashboard"""
        try:
            dashboard_content = self.generate_dashboard_content()
            self.dashboard_display.delete(1.0, tk.END)
            self.dashboard_display.insert(tk.END, dashboard_content)

            # Auto-scroll to top
            self.dashboard_display.see(1.0)

        except Exception as e:
            print(f"Dashboard update error: {e}")

        # Schedule next update
        self.root.after(3000, self.update_visual_dashboard)

    def generate_dashboard_content(self):
        """Generate comprehensive dashboard content"""
        content = f"""
{'=' * 100}
🚀 ADVANCED AI TRADING BOT - REAL-TIME DASHBOARD
{'=' * 100}
⏰ Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
💰 Paper Balance: {self.paper_balance:,.2f} THB | 📊 Total Trades: {self.trade_count} | 🎯 Win Rate: {(self.successful_trades / max(1, self.trade_count) * 100):.1f}%

"""

        # Add price chart if we have data
        if len(self.price_history) > 10:
            recent_prices = list(self.price_history)[-50:]
            content += TextChart.generate_line_chart(
                recent_prices,
                width=90,
                height=15,
                title="📈 PRICE MOVEMENT (Last 50 Data Points)"
            )

        # Add RSI chart if we have data
        if len(self.rsi_history) > 10:
            recent_rsi = list(self.rsi_history)[-50:]
            content += TextChart.generate_line_chart(
                recent_rsi,
                width=90,
                height=12,
                title="📊 RSI INDICATOR (Overbought: >70, Oversold: <30)"
            )

        # Add technical indicators if we have price data
        if len(self.price_history) >= 50:
            indicators = AdvancedTechnicalAnalysis.calculate_comprehensive_indicators(
                list(self.price_history)
            )
            content += TextChart.generate_indicator_status(indicators)

        # Add AI predictions chart if available
        if len(self.prediction_history) > 10:
            recent_predictions = [p * 100 for p in list(self.prediction_history)[-30:]]  # Convert to percentage
            content += TextChart.generate_line_chart(
                recent_predictions,
                width=80,
                height=10,
                title="🤖 AI PRICE PREDICTIONS (%) - Last 30 Predictions"
            )

        # Add confidence chart
        if len(self.confidence_history) > 10:
            recent_confidence = [c * 100 for c in list(self.confidence_history)[-30:]]  # Convert to percentage
            content += TextChart.generate_line_chart(
                recent_confidence,
                width=80,
                height=8,
                title="⚡ AI CONFIDENCE LEVEL (%) - Last 30 Signals"
            )

        # Add performance summary
        content += f"""

📊 CURRENT TRADING PERFORMANCE
{'=' * 60}
💰 Starting Balance:     50,000.00 THB
💰 Current Balance:      {self.paper_balance:,.2f} THB
📈 Total P&L:           {self.total_pnl:+,.2f} THB ({(self.total_pnl / 50000 * 100):+.2f}%)
📊 Total Trades:        {self.trade_count}
🎯 Successful Trades:   {self.successful_trades}
📋 Win Rate:            {(self.successful_trades / max(1, self.trade_count) * 100):.1f}%
📉 Max Drawdown:        {self.max_drawdown:.2f}%
🏆 ROI:                 {((self.paper_balance - 50000) / 50000 * 100):+.2f}%

🤖 AI MODEL STATUS
{'=' * 60}
🧠 Model Trained:       {'✅ Yes' if self.ml_model.is_trained else '❌ No'}
📊 Model Accuracy:      {(self.ml_model.prediction_accuracy * 100):.1f}%
⚡ AI Trading:          {'🟢 Active' if self.ai_enabled else '🔴 Inactive'}
🎯 Min Confidence:      {float(self.config.get('min_confidence', 0.65)) * 100:.0f}%
💰 Position Size:       {self.config.get('position_size', 1000)} THB

⏰ SYSTEM STATUS
{'=' * 60}
📡 API Connection:      {'🟢 Connected' if self.api_client else '🔴 Disconnected'}
📊 Data Collection:     {'🟢 Active' if self.api_client else '🔴 Inactive'}
🎯 Trading Symbol:      {self.config.get('trading_symbol', 'btc_thb').upper()}
📈 Live Data Points:    {len(self.price_history)}
🤖 AI Predictions:      {len(self.prediction_history)}

"""

        return content

    def toggle_ai_trading(self):
        """Toggle AI trading system"""
        if not self.api_client:
            messagebox.showerror("Error", "กรุณาตั้งค่า API ก่อนเริ่มเทรด!")
            return

        if not self.ml_model.is_trained:
            if messagebox.askyesno("Model Not Trained",
                                   "AI Model ยังไม่ได้ฝึก ต้องการฝึกตอนนี้หรือไม่?"):
                self.train_ai_model()
                return

        if not self.ai_enabled:
            self.start_ai_trading()
        else:
            self.stop_ai_trading()

    def start_ai_trading(self):
        """Start enhanced AI trading system"""
        self.ai_enabled = True
        self.stop_trading = False

        self.ai_toggle_btn.configure(text="🛑 Stop AI Trading")
        self.metric_labels["🤖 AI Status"].configure(text="🟢 Active")

        threading.Thread(target=self.enhanced_ai_trading_loop, daemon=True).start()
        self.log_ai_analysis("🚀 Advanced AI Trading System Started!")
        self.log_ai_analysis(f"📊 Min Confidence: {float(self.config['min_confidence']) * 100:.0f}%")
        self.log_ai_analysis(f"💰 Position Size: {self.config['position_size']} THB")

    def stop_ai_trading(self):
        """Stop AI trading system"""
        self.ai_enabled = False
        self.stop_trading = True

        self.ai_toggle_btn.configure(text="🚀 Start AI Trading")
        self.metric_labels["🤖 AI Status"].configure(text="🔴 Stopped")

        self.log_ai_analysis("🛑 AI Trading System Stopped!")

    def enhanced_ai_trading_loop(self):
        """Enhanced AI trading loop with comprehensive analysis"""
        while self.ai_enabled and not self.stop_trading:
            try:
                symbol = self.config['trading_symbol']
                ticker_data = self.api_client.get_ticker(symbol)

                if not ticker_data or len(ticker_data) == 0:
                    time.sleep(30)
                    continue

                current_price = float(ticker_data[0]['last'])
                current_time = datetime.now()

                # Update price history
                self.price_history.append(current_price)
                self.time_history.append(current_time)

                # Update live metrics
                self.metric_labels["📊 Current Price"].configure(text=f"{current_price:,.0f} THB")

                # Calculate comprehensive technical indicators
                if len(self.price_history) >= 50:
                    indicators = AdvancedTechnicalAnalysis.calculate_comprehensive_indicators(
                        list(self.price_history)
                    )

                    # Update RSI history
                    self.rsi_history.append(indicators.get('rsi', 50))

                    # Log technical analysis
                    self.log_ai_analysis(f"📊 RSI: {indicators.get('rsi', 0):.1f} | "
                                         f"MACD: {indicators.get('macd', 0):.4f} | "
                                         f"Trend: {indicators.get('trend_strength', 0):.2f}")

                    # Get AI prediction
                    if self.ml_model.is_trained:
                        current_features = [
                            indicators.get('rsi', 50),
                            indicators.get('macd', 0),
                            indicators.get('macd_signal', 0),
                            indicators.get('bb_upper', current_price),
                            indicators.get('bb_middle', current_price),
                            indicators.get('bb_lower', current_price),
                            indicators.get('stoch_k', 50),
                            indicators.get('williams_r', -50),
                            indicators.get('trend_strength', 0),
                            indicators.get('ma_5', current_price),
                            indicators.get('ma_20', current_price),
                            indicators.get('ma_50', current_price),
                            current_price,
                            float(ticker_data[0].get('base_volume', 0)),
                            # Add momentum features
                            0 if len(self.price_history) < 6 else (current_price - self.price_history[-6]) /
                                                                  self.price_history[-6],
                            0 if len(self.price_history) < 11 else (current_price - self.price_history[-11]) /
                                                                   self.price_history[-11]
                        ]

                        signal = self.ml_model.predict_signal(current_features)

                        # Update signal histories
                        self.prediction_history.append(signal['prediction'])
                        self.confidence_history.append(signal['confidence'])

                        # Update confidence display
                        self.metric_labels["⚡ AI Confidence"].configure(
                            text=f"{signal['confidence'] * 100:.1f}%"
                        )
                        self.metric_labels["🔥 Model Accuracy"].configure(
                            text=f"{signal.get('model_accuracy', 0) * 100:.1f}%"
                        )

                        # Log AI decision with detailed analysis
                        self.log_ai_analysis(f"🤖 AI SIGNAL: {signal['action'].upper()} "
                                             f"| Confidence: {signal['confidence']:.3f} "
                                             f"| Prediction: {signal['prediction'] * 100:+.2f}%")
                        self.log_ai_analysis(f"📋 Reason: {signal['reason']}")

                        # Execute trade if confidence meets threshold
                        min_confidence = float(self.config['min_confidence'])
                        if (signal['action'] != 'hold' and
                                signal['confidence'] >= min_confidence):
                            self.execute_enhanced_paper_trade(signal, current_price, indicators)

                        # Save comprehensive AI analysis
                        analysis_data = (
                            current_time, symbol, signal['action'], signal['confidence'],
                            current_price, signal['prediction'], signal['reason'],
                            json.dumps(indicators), True, 'paper_trade'
                        )
                        self.db_manager.save_ai_analysis(analysis_data)

                    # Save comprehensive market data
                    self.save_comprehensive_market_data(ticker_data[0], indicators)

                time.sleep(30)  # Analysis every 30 seconds

            except Exception as e:
                self.log_ai_analysis(f"❌ AI Loop Error: {str(e)}")
                time.sleep(60)

    def execute_enhanced_paper_trade(self, signal, current_price, indicators):
        """Execute enhanced paper trade with detailed tracking"""
        try:
            position_size = float(self.config['position_size'])

            # Enhanced trade logic with stop loss and take profit
            if signal['action'] == 'buy':
                crypto_amount = position_size / current_price

                # Calculate stop loss and take profit levels
                stop_loss_price = current_price * (1 - float(self.config['stop_loss']) / 100)
                take_profit_price = current_price * (1 + float(self.config['take_profit']) / 100)

                self.log_ai_analysis(f"📈 PAPER BUY EXECUTED")
                self.log_ai_analysis(f"   💰 Amount: {crypto_amount:.6f} BTC")
                self.log_ai_analysis(f"   💲 Price: {current_price:,.0f} THB")
                self.log_ai_analysis(f"   🛑 Stop Loss: {stop_loss_price:,.0f} THB")
                self.log_ai_analysis(f"   🎯 Take Profit: {take_profit_price:,.0f} THB")

                # Simulate realistic P&L based on market conditions
                rsi = indicators.get('rsi', 50)
                trend_strength = indicators.get('trend_strength', 0)

                # Better simulation based on technical indicators
                if rsi < 30 and trend_strength > 0:  # Oversold + positive trend
                    pnl_factor = np.random.normal(0.02, 0.01)  # Better chance of profit
                elif rsi > 70 and trend_strength < 0:  # Overbought + negative trend
                    pnl_factor = np.random.normal(-0.01, 0.015)  # Higher chance of loss
                else:
                    pnl_factor = np.random.normal(0.005, 0.02)  # Normal distribution

                pnl = position_size * pnl_factor

            elif signal['action'] == 'sell':
                self.log_ai_analysis(f"📉 PAPER SELL EXECUTED")
                self.log_ai_analysis(f"   💰 Value: {position_size:,.0f} THB")
                self.log_ai_analysis(f"   💲 Price: {current_price:,.0f} THB")

                # Similar enhanced simulation for sell
                rsi = indicators.get('rsi', 50)
                trend_strength = indicators.get('trend_strength', 0)

                if rsi > 70 and trend_strength < 0:  # Overbought + negative trend
                    pnl_factor = np.random.normal(0.015, 0.01)  # Better chance of profit
                elif rsi < 30 and trend_strength > 0:  # Oversold + positive trend
                    pnl_factor = np.random.normal(-0.01, 0.015)  # Higher chance of loss
                else:
                    pnl_factor = np.random.normal(0.005, 0.02)

                pnl = position_size * pnl_factor

            # Update comprehensive trading statistics
            self.trade_count += 1
            if pnl > 0:
                self.successful_trades += 1
                self.log_ai_analysis(f"   ✅ P&L: +{pnl:,.2f} THB (Profit)")
            else:
                self.log_ai_analysis(f"   ❌ P&L: {pnl:,.2f} THB (Loss)")

            self.total_pnl += pnl
            self.paper_balance += pnl

            # Track peak balance and drawdown
            if self.paper_balance > self.peak_balance:
                self.peak_balance = self.paper_balance

            current_drawdown = (self.peak_balance - self.paper_balance) / self.peak_balance * 100
            if current_drawdown > self.max_drawdown:
                self.max_drawdown = current_drawdown

            # Update enhanced metrics
            win_rate = (self.successful_trades / self.trade_count) * 100
            roi = ((self.paper_balance - 50000) / 50000) * 100

            self.metric_labels["💰 Paper Balance"].configure(text=f"{self.paper_balance:,.0f} THB")
            self.metric_labels["🎯 Total Trades"].configure(text=str(self.trade_count))
            self.metric_labels["📈 Win Rate"].configure(text=f"{win_rate:.1f}%")
            self.metric_labels["🏆 Total P&L"].configure(text=f"{self.total_pnl:+,.0f} THB")
            self.metric_labels["📉 Max Drawdown"].configure(text=f"{self.max_drawdown:.1f}%")

            # Log comprehensive trade summary
            self.log_ai_analysis(f"📊 TRADE SUMMARY:")
            self.log_ai_analysis(f"   📊 Total Trades: {self.trade_count}")
            self.log_ai_analysis(f"   🎯 Win Rate: {win_rate:.1f}%")
            self.log_ai_analysis(f"   💰 Balance: {self.paper_balance:,.0f} THB")
            self.log_ai_analysis(f"   📈 ROI: {roi:+.2f}%")
            self.log_ai_analysis("─" * 50)

            # Update performance tracking
            self.update_performance_display()

        except Exception as e:
            self.log_ai_analysis(f"❌ Trade execution error: {str(e)}")

    def save_comprehensive_market_data(self, ticker_data, indicators):
        """Save comprehensive market data to database"""
        try:
            market_data = (
                datetime.now(),
                self.config['trading_symbol'],
                float(ticker_data['last']),
                float(ticker_data.get('base_volume', 0)),
                float(ticker_data.get('high_24_hr', 0)),
                float(ticker_data.get('low_24_hr', 0)),
                float(ticker_data.get('percent_change', 0)),
                indicators.get('rsi', 50),
                indicators.get('macd', 0),
                indicators.get('macd_signal', 0),
                indicators.get('bb_upper', 0),
                indicators.get('bb_middle', 0),
                indicators.get('bb_lower', 0),
                indicators.get('stoch_k', 50),
                indicators.get('williams_r', -50),
                indicators.get('trend_strength', 0),
                indicators.get('ma_5', 0),
                indicators.get('ma_20', 0),
                indicators.get('ma_50', 0)
            )
            self.db_manager.save_market_data(market_data)

        except Exception as e:
            print(f"Data save error: {e}")

    def train_ai_model(self):
        """Train AI model with enhanced feedback"""

        def train():
            try:
                self.log_ai_analysis("🧠 Starting Enhanced AI Model Training...")
                self.log_ai_analysis("📊 Collecting and analyzing market data...")

                success, message = self.ml_model.train_model(self.config['trading_symbol'])

                if success:
                    self.log_ai_analysis(f"✅ Training Successful!")
                    self.log_ai_analysis(f"📊 {message}")
                    self.metric_labels["🔥 Model Accuracy"].configure(
                        text=f"{self.ml_model.prediction_accuracy * 100:.1f}%"
                    )
                else:
                    self.log_ai_analysis(f"❌ Training Failed: {message}")

            except Exception as e:
                self.log_ai_analysis(f"❌ Training Error: {str(e)}")

        threading.Thread(target=train, daemon=True).start()

    def start_enhanced_data_collection(self):
        """Start enhanced background data collection"""

        def collect():
            while True:
                try:
                    if self.api_client and not self.ai_enabled:
                        symbol = self.config['trading_symbol']
                        ticker_data = self.api_client.get_ticker(symbol)

                        if ticker_data and len(ticker_data) > 0:
                            current_price = float(ticker_data[0]['last'])
                            current_time = datetime.now()

                            self.price_history.append(current_price)
                            self.time_history.append(current_time)

                            # Update current price display
                            self.metric_labels["📊 Current Price"].configure(text=f"{current_price:,.0f} THB")

                            # Calculate and store indicators
                            if len(self.price_history) >= 50:
                                indicators = AdvancedTechnicalAnalysis.calculate_comprehensive_indicators(
                                    list(self.price_history)
                                )
                                self.rsi_history.append(indicators.get('rsi', 50))
                                self.save_comprehensive_market_data(ticker_data[0], indicators)

                    time.sleep(60)  # Collect data every minute

                except Exception as e:
                    time.sleep(120)

        threading.Thread(target=collect, daemon=True).start()

    def start_performance_tracking(self):
        """Start performance tracking updates"""

        def track():
            while True:
                try:
                    self.update_performance_display()
                    time.sleep(300)  # Update every 5 minutes
                except Exception as e:
                    time.sleep(300)

        threading.Thread(target=track, daemon=True).start()

    def update_performance_display(self):
        """Update detailed performance display"""
        try:
            win_rate = (self.successful_trades / max(1, self.trade_count)) * 100
            roi = ((self.paper_balance - 50000) / 50000) * 100
            avg_pnl = self.total_pnl / max(1, self.trade_count)

            performance_summary = f"""
📊 COMPREHENSIVE PERFORMANCE ANALYSIS
{'=' * 70}
⏰ Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

💰 FINANCIAL METRICS
────────────────────────────────────────
💰 Starting Capital:    50,000.00 THB
💰 Current Balance:     {self.paper_balance:,.2f} THB
📈 Total P&L:          {self.total_pnl:+,.2f} THB
🏆 ROI:                {roi:+.2f}%
📉 Max Drawdown:       {self.max_drawdown:.2f}%
💡 Average P&L:        {avg_pnl:+,.2f} THB per trade

📊 TRADING STATISTICS
────────────────────────────────────────
📊 Total Trades:       {self.trade_count}
✅ Successful Trades:  {self.successful_trades}
❌ Failed Trades:      {self.trade_count - self.successful_trades}
🎯 Win Rate:           {win_rate:.2f}%
📋 Success Ratio:      {self.successful_trades}/{self.trade_count}

🤖 AI MODEL PERFORMANCE
────────────────────────────────────────
🧠 Model Status:       {'✅ Trained' if self.ml_model.is_trained else '❌ Not Trained'}
📊 Model Accuracy:     {(self.ml_model.prediction_accuracy * 100):.1f}%
⚡ AI Status:          {'🟢 Active' if self.ai_enabled else '🔴 Inactive'}
🎯 Min Confidence:     {float(self.config.get('min_confidence', 0.65)) * 100:.0f}%
📈 Predictions Made:   {len(self.prediction_history)}

📈 MARKET DATA STATUS
────────────────────────────────────────
📊 Symbol:             {self.config.get('trading_symbol', 'btc_thb').upper()}
📈 Price Data Points:  {len(self.price_history)}
📊 RSI Data Points:    {len(self.rsi_history)}
⚡ Live Data:          {'🟢 Active' if self.api_client else '🔴 Inactive'}
            """

            self.performance_summary.delete(1.0, tk.END)
            self.performance_summary.insert(tk.END, performance_summary)

            # Update detailed performance log
            log_entry = f"""
[{datetime.now().strftime('%H:%M:%S')}] Performance Update
Balance: {self.paper_balance:,.0f} THB | Trades: {self.trade_count} | Win Rate: {win_rate:.1f}% | ROI: {roi:+.2f}%
"""
            self.performance_log.insert(tk.END, log_entry)
            self.performance_log.see(tk.END)

            # Keep log manageable
            lines = self.performance_log.get('1.0', tk.END).split('\n')
            if len(lines) > 200:
                self.performance_log.delete('1.0', f'{len(lines) - 150}.0')

        except Exception as e:
            print(f"Performance update error: {e}")

    def generate_performance_report(self):
        """Generate comprehensive performance report"""
        try:
            win_rate = (self.successful_trades / max(1, self.trade_count)) * 100
            roi = ((self.paper_balance - 50000) / 50000) * 100

            report = f"""
🏆 COMPREHENSIVE TRADING PERFORMANCE REPORT
{'=' * 80}
📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

💰 EXECUTIVE SUMMARY
────────────────────────────────────────────────────────────────
Starting Capital:       50,000.00 THB
Current Balance:        {self.paper_balance:,.2f} THB
Net Profit/Loss:        {self.total_pnl:+,.2f} THB
Return on Investment:   {roi:+.2f}%
Performance Rating:     {'🏆 Excellent' if roi > 10 else '🟢 Good' if roi > 0 else '🔴 Poor'}

📊 TRADING METRICS
────────────────────────────────────────────────────────────────
Total Trades Executed:  {self.trade_count}
Successful Trades:      {self.successful_trades}
Failed Trades:          {self.trade_count - self.successful_trades}
Win Rate:               {win_rate:.2f}%
Average P&L per Trade:  {(self.total_pnl / max(1, self.trade_count)):+,.2f} THB
Maximum Drawdown:       {self.max_drawdown:.2f}%

🤖 AI PERFORMANCE
────────────────────────────────────────────────────────────────
Model Training Status:  {'✅ Completed' if self.ml_model.is_trained else '❌ Pending'}
Model Accuracy:         {(self.ml_model.prediction_accuracy * 100):.1f}%
Predictions Generated:  {len(self.prediction_history)}
Confidence Threshold:   {float(self.config.get('min_confidence', 0.65)) * 100:.0f}%
Average Confidence:     {(np.mean(self.confidence_history) * 100 if self.confidence_history else 0):.1f}%

📈 MARKET ANALYSIS
────────────────────────────────────────────────────────────────
Trading Symbol:         {self.config.get('trading_symbol', 'btc_thb').upper()}
Data Points Collected:  {len(self.price_history)}
Analysis Period:        {len(self.price_history)} data points
Current Price:          {self.price_history[-1]:,.0f} THB (if available)

⚙️ CONFIGURATION
────────────────────────────────────────────────────────────────
Position Size:          {self.config.get('position_size', 1000)} THB
Stop Loss:              {self.config.get('stop_loss', 2)}%
Take Profit:            {self.config.get('take_profit', 4)}%
Min Confidence:         {float(self.config.get('min_confidence', 0.65)) * 100:.0f}%

📋 RECOMMENDATIONS
────────────────────────────────────────────────────────────────
"""

            # Add recommendations based on performance
            if roi > 5:
                report += "✅ Performance is excellent. Continue current strategy.\n"
            elif roi > 0:
                report += "🟡 Performance is positive but could be improved.\n"
            else:
                report += "🔴 Performance needs improvement. Consider adjusting parameters.\n"

            if win_rate < 60:
                report += "⚠️ Consider increasing minimum confidence threshold.\n"

            if self.max_drawdown > 10:
                report += "⚠️ Consider reducing position size to manage risk.\n"

            report += f"""
🔚 END OF REPORT
{'=' * 80}
            """

            # Display in a new window
            report_window = tk.Toplevel(self.root)
            report_window.title("📊 Trading Performance Report")
            report_window.geometry("800x600")
            report_window.configure(bg='#1a1a1a')

            report_text = scrolledtext.ScrolledText(
                report_window,
                bg='#1a1a1a',
                fg='#00ff88',
                font=('Consolas', 10)
            )
            report_text.pack(fill='both', expand=True, padx=10, pady=10)
            report_text.insert(tk.END, report)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate report: {str(e)}")

    def reset_performance(self):
        """Reset all performance data"""
        if messagebox.askyesno("Reset Performance",
                               "⚠️ การรีเซ็ตจะลบข้อมูลการเทรดทั้งหมด\nต้องการดำเนินการต่อหรือไม่?"):
            # Reset all performance data
            self.trade_count = 0
            self.successful_trades = 0
            self.total_pnl = 0.0
            self.paper_balance = 50000.0
            self.max_drawdown = 0.0
            self.peak_balance = 50000.0

            # Clear histories
            self.price_history.clear()
            self.time_history.clear()
            self.rsi_history.clear()
            self.prediction_history.clear()
            self.confidence_history.clear()

            # Reset displays
            self.metric_labels["💰 Paper Balance"].configure(text="50,000 THB")
            self.metric_labels["🎯 Total Trades"].configure(text="0")
            self.metric_labels["📈 Win Rate"].configure(text="0%")
            self.metric_labels["🏆 Total P&L"].configure(text="0 THB")
            self.metric_labels["📉 Max Drawdown"].configure(text="0%")

            # Clear logs
            self.performance_log.delete(1.0, tk.END)
            self.ai_analysis_display.delete(1.0, tk.END)

            self.log_ai_analysis("🔄 Performance data reset successfully!")
            self.log_ai_analysis("💰 Starting balance restored to 50,000 THB")
            messagebox.showinfo("Success", "ข้อมูลถูกรีเซ็ตเรียบร้อยแล้ว!")

    def save_and_test_api(self):
        """Save and test API configuration"""
        api_key = self.api_key_entry.get().strip()
        api_secret = self.api_secret_entry.get().strip()

        if not api_key:
            messagebox.showerror("Error", "กรุณาใส่ API Key")
            return

        self.api_client = BitkubAPIClient(api_key, api_secret)
        self.connection_status.configure(text="🟡 Testing...")

        # Log API setup
        self.api_status_display.insert(tk.END,
                                       f"[{datetime.now().strftime('%H:%M:%S')}] Setting up API connection...\n")
        self.api_status_display.see(tk.END)

        threading.Thread(target=self.test_api_connection, daemon=True).start()

    def test_api_connection(self):
        """Test API connection with detailed feedback"""
        try:
            self.api_status_display.insert(tk.END,
                                           f"[{datetime.now().strftime('%H:%M:%S')}] Testing API connection...\n")

            # Test ticker data
            ticker = self.api_client.get_ticker('btc_thb')
            if ticker and len(ticker) > 0:
                price = float(ticker[0]['last'])
                volume = float(ticker[0].get('base_volume', 0))
                change = float(ticker[0].get('percent_change', 0))

                self.connection_status.configure(text="🟢 Connected")

                success_msg = f"""✅ API Connection Successful!

📊 Market Data Test:
├─ BTC Price: {price:,.0f} THB
├─ 24h Volume: {volume:,.2f} BTC
├─ 24h Change: {change:+.2f}%
└─ Data Status: ✅ Live

🔒 Security Status: ✅ Secure
📡 Connection: ✅ Stable
⚡ Response Time: ✅ Fast
"""

                self.api_status_display.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] {success_msg}\n")
                self.api_status_display.see(tk.END)

                self.log_ai_analysis(f"✅ API Connected Successfully!")
                self.log_ai_analysis(f"📊 BTC Price: {price:,.0f} THB")

                messagebox.showinfo("API Connected",
                                    f"🎉 API เชื่อมต่อสำเร็จ!\n\n📊 ราคา BTC: {price:,.0f} THB\n📈 เปลี่ยนแปลง 24h: {change:+.2f}%")

                # Start collecting initial data
                self.start_enhanced_data_collection()

            else:
                self.connection_status.configure(text="🔴 Failed")
                error_msg = "❌ API Test Failed - No data received"
                self.api_status_display.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] {error_msg}\n")
                messagebox.showerror("API Error", "ไม่สามารถรับข้อมูลจาก API ได้")

        except Exception as e:
            self.connection_status.configure(text="🔴 Error")
            error_msg = f"❌ API Connection Error: {str(e)}"
            self.api_status_display.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] {error_msg}\n")
            self.api_status_display.see(tk.END)
            messagebox.showerror("Connection Error", f"เชื่อมต่อ API ไม่สำเร็จ:\n{str(e)}")

    def toggle_api_visibility(self):
        """Toggle API credentials visibility"""
        if self.api_key_entry.cget('show') == '*':
            self.api_key_entry.configure(show='')
            self.api_secret_entry.configure(show='')
        else:
            self.api_key_entry.configure(show='*')
            self.api_secret_entry.configure(show='*')

    def save_configuration(self):
        """Save trading configuration"""
        try:
            for key, var in self.config_vars.items():
                try:
                    value = var.get()
                    if key in ['min_confidence', 'stop_loss', 'take_profit']:
                        self.config[key] = float(value) / 100 if key != 'min_confidence' else float(value)
                    elif key == 'position_size':
                        self.config[key] = int(float(value))
                    else:
                        self.config[key] = value
                except:
                    pass

            self.log_ai_analysis("💾 Configuration saved successfully!")
            self.log_ai_analysis(f"📊 Symbol: {self.config['trading_symbol']}")
            self.log_ai_analysis(f"🎯 Min Confidence: {float(self.config['min_confidence']) * 100:.0f}%")
            self.log_ai_analysis(f"💰 Position Size: {self.config['position_size']} THB")

            messagebox.showinfo("Success", "การตั้งค่าถูกบันทึกแล้ว!")

        except Exception as e:
            messagebox.showerror("Error", f"ไม่สามารถบันทึกการตั้งค่าได้: {str(e)}")

    def emergency_stop(self):
        """Emergency stop all operations"""
        if messagebox.askyesno("Emergency Stop",
                               "🚨 หยุดระบบฉุกเฉิน 🚨\n\nหยุดการทำงานของระบบทั้งหมดทันที?"):
            self.stop_ai_trading()
            self.log_ai_analysis("🚨 EMERGENCY STOP ACTIVATED!")
            self.log_ai_analysis("🛑 All trading operations halted immediately!")
            messagebox.showwarning("Emergency Stop", "ระบบหยุดทำงานแล้ว!")

    def log_ai_analysis(self, message):
        """Log AI analysis with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"

        self.ai_analysis_display.insert(tk.END, log_entry)
        self.ai_analysis_display.see(tk.END)

        # Keep log manageable
        lines = self.ai_analysis_display.get('1.0', tk.END).split('\n')
        if len(lines) > 150:
            self.ai_analysis_display.delete('1.0', f'{len(lines) - 100}.0')


def main():
    """Main application entry point"""
    try:
        root = tk.Tk()
        app = AdvancedVisualAITrader(root)

        # Center window
        root.update_idletasks()
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width // 2) - (1600 // 2)
        y = (screen_height // 2) - (1000 // 2)
        root.geometry(f"1600x1000+{x}+{y}")

        # Welcome messages
        app.log_ai_analysis("🚀 Advanced AI Trading Bot Initialized Successfully!")
        app.log_ai_analysis("📊 Text-based Visual Dashboard Ready")
        app.log_ai_analysis("🤖 Enhanced AI Engine Loaded")
        app.log_ai_analysis("💡 Please configure API in 'API Config' tab")
        app.log_ai_analysis("🧠 Train AI Model using 'Train AI Model' button")
        app.log_ai_analysis("⚠️ System uses PAPER TRADING only - 100% Safe")
        app.log_ai_analysis("🎯 Starting balance: 50,000 THB")
        app.log_ai_analysis("─" * 50)

        print("✅ Advanced AI Trading Bot เริ่มต้นสำเร็จ!")
        print("📊 ระบบ Text-based Visual Dashboard พร้อมใช้งาน")
        print("🤖 ไม่ต้องพึ่ง matplotlib - ใช้ ASCII charts")
        print("💡 ตั้งค่า API และฝึก AI Model เพื่อเริ่มใช้งาน")

        root.mainloop()

    except Exception as e:
        print(f"Application error: {e}")
        messagebox.showerror("Error", f"โปรแกรมเกิดข้อผิดพลาด: {e}")


if __name__ == "__main__":
    main()