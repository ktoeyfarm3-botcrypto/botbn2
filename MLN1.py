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
import os
import sqlite3
import pickle
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, mean_squared_error
import warnings

warnings.filterwarnings('ignore')

# Try to import additional libraries
try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.animation import FuncAnimation
    import seaborn as sns

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("Matplotlib/Seaborn not found. Chart features will be limited.")

try:
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    from tensorflow.keras.optimizers import Adam

    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    print("TensorFlow not found. Deep learning features will be disabled.")


class DatabaseManager:
    """Database manager for storing market data and trading history"""

    def __init__(self, db_path="trading_data.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Market data table
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
                bb_upper REAL,
                bb_middle REAL,
                bb_lower REAL,
                moving_avg_5 REAL,
                moving_avg_20 REAL,
                moving_avg_50 REAL
            )
        ''')

        # Trading signals table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trading_signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                symbol TEXT,
                signal_type TEXT,
                confidence REAL,
                price REAL,
                reason TEXT,
                executed BOOLEAN,
                result TEXT
            )
        ''')

        # Trade history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trade_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                symbol TEXT,
                action TEXT,
                amount REAL,
                price REAL,
                fee REAL,
                profit_loss REAL,
                order_id TEXT,
                strategy TEXT
            )
        ''')

        # Model performance table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS model_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                model_name TEXT,
                accuracy REAL,
                precision REAL,
                recall REAL,
                profit_factor REAL,
                total_trades INTEGER,
                winning_trades INTEGER
            )
        ''')

        conn.commit()
        conn.close()

    def save_market_data(self, data):
        """Save market data to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO market_data 
            (timestamp, symbol, price, volume, high_24h, low_24h, change_24h, 
             rsi, macd, bb_upper, bb_middle, bb_lower, moving_avg_5, moving_avg_20, moving_avg_50)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', data)

        conn.commit()
        conn.close()

    def get_market_data(self, symbol, limit=1000):
        """Get market data from database"""
        conn = sqlite3.connect(self.db_path)
        query = '''
            SELECT * FROM market_data 
            WHERE symbol = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        '''
        df = pd.read_sql_query(query, conn, params=(symbol, limit))
        conn.close()
        return df

    def save_trading_signal(self, signal_data):
        """Save trading signal to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO trading_signals 
            (timestamp, symbol, signal_type, confidence, price, reason, executed, result)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', signal_data)

        conn.commit()
        conn.close()

    def save_trade(self, trade_data):
        """Save trade to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO trade_history 
            (timestamp, symbol, action, amount, price, fee, profit_loss, order_id, strategy)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', trade_data)

        conn.commit()
        conn.close()


class BitkubAPIClient:
    """Enhanced Bitkub API Client"""

    def __init__(self, api_key="", api_secret=""):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://api.bitkub.com"
        self.request_times = deque(maxlen=250)
        self.rate_limit_lock = threading.Lock()

    def _wait_for_rate_limit(self):
        """Rate limiting management"""
        with self.rate_limit_lock:
            now = time.time()
            while self.request_times and (now - self.request_times[0]) > 10:
                self.request_times.popleft()

            if len(self.request_times) >= 200:  # Conservative limit
                time.sleep(1)
                self.request_times.clear()

            self.request_times.append(now)

    def _generate_signature(self, payload_string):
        """Generate HMAC signature"""
        if not self.api_secret:
            raise ValueError("API Secret not configured")

        return hmac.new(
            self.api_secret.encode('utf-8'),
            payload_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

    def make_private_request(self, method, endpoint, params=None, body=None):
        """Make authenticated API request"""
        try:
            if not self.api_key or not self.api_secret:
                raise ValueError("API credentials not configured")

            self._wait_for_rate_limit()

            # Get timestamp
            ts = str(round(time.time() * 1000))
            url = f"{self.base_url}{endpoint}"
            payload_parts = [ts, method.upper(), endpoint]

            if method.upper() == 'GET' and params:
                query_string = "&".join([f"{k}={v}" for k, v in params.items()])
                payload_parts.append(f"?{query_string}")
                url += f"?{query_string}"
            elif method.upper() == 'POST' and body:
                json_body = json.dumps(body, separators=(',', ':'))
                payload_parts.append(json_body)
            elif method.upper() == 'POST':
                payload_parts.append('{}')

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
                response = requests.get(url, headers=headers, timeout=15)
            else:
                response = requests.post(url, headers=headers, json=body or {}, timeout=15)

            response.raise_for_status()
            return response.json()

        except Exception as e:
            print(f"API Error: {e}")
            return None

    def make_public_request(self, endpoint, params=None):
        """Make public API request"""
        try:
            self._wait_for_rate_limit()
            url = f"{self.base_url}{endpoint}"
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Public API Error: {e}")
            return None

    # API methods
    def get_ticker(self, symbol=None):
        params = {'sym': symbol} if symbol else None
        return self.make_public_request('/api/v3/market/ticker', params)

    def get_wallet(self):
        return self.make_private_request('POST', '/api/v3/market/wallet')

    def place_buy_order(self, symbol, amount, rate=0, order_type='market'):
        body = {'sym': symbol, 'amt': amount, 'rat': rate, 'typ': order_type}
        return self.make_private_request('POST', '/api/v3/market/place-bid', body=body)

    def place_sell_order(self, symbol, amount, rate=0, order_type='market'):
        body = {'sym': symbol, 'amt': amount, 'rat': rate, 'typ': order_type}
        return self.make_private_request('POST', '/api/v3/market/place-ask', body=body)


class TechnicalAnalysis:
    """Advanced technical analysis with machine learning"""

    @staticmethod
    def calculate_indicators(prices, volumes=None):
        """Calculate comprehensive technical indicators"""
        if len(prices) < 50:
            return {}

        prices = np.array(prices)
        indicators = {}

        # RSI
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        avg_gain = np.mean(gains[-14:])
        avg_loss = np.mean(losses[-14:])
        rs = avg_gain / (avg_loss + 1e-10)
        indicators['rsi'] = 100 - (100 / (1 + rs))

        # Moving averages
        indicators['ma_5'] = np.mean(prices[-5:])
        indicators['ma_20'] = np.mean(prices[-20:])
        indicators['ma_50'] = np.mean(prices[-50:])

        # MACD
        ema_12 = TechnicalAnalysis._ema(prices, 12)
        ema_26 = TechnicalAnalysis._ema(prices, 26)
        indicators['macd'] = ema_12 - ema_26
        indicators['macd_signal'] = TechnicalAnalysis._ema([indicators['macd']] * 9, 9)

        # Bollinger Bands
        bb_period = 20
        bb_std = 2
        bb_middle = np.mean(prices[-bb_period:])
        bb_std_val = np.std(prices[-bb_period:])
        indicators['bb_upper'] = bb_middle + (bb_std * bb_std_val)
        indicators['bb_lower'] = bb_middle - (bb_std * bb_std_val)
        indicators['bb_middle'] = bb_middle

        # Stochastic
        high_14 = np.max(prices[-14:])
        low_14 = np.min(prices[-14:])
        indicators['stoch_k'] = ((prices[-1] - low_14) / (high_14 - low_14)) * 100

        # Williams %R
        indicators['williams_r'] = ((high_14 - prices[-1]) / (high_14 - low_14)) * -100

        # Price momentum
        indicators['momentum_5'] = (prices[-1] - prices[-6]) / prices[-6] * 100 if len(prices) > 5 else 0
        indicators['momentum_10'] = (prices[-1] - prices[-11]) / prices[-11] * 100 if len(prices) > 10 else 0

        # Volume indicators (if available)
        if volumes and len(volumes) == len(prices):
            volumes = np.array(volumes)
            indicators['volume_ma'] = np.mean(volumes[-20:])
            indicators['volume_ratio'] = volumes[-1] / indicators['volume_ma']

        return indicators

    @staticmethod
    def _ema(prices, period):
        """Calculate Exponential Moving Average"""
        prices = np.array(prices)
        alpha = 2 / (period + 1)
        ema = [prices[0]]

        for price in prices[1:]:
            ema.append(alpha * price + (1 - alpha) * ema[-1])

        return ema[-1]


class MLTradingModel:
    """Machine Learning trading model with multiple algorithms"""

    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.models = {}
        self.scalers = {}
        self.label_encoders = {}
        self.feature_columns = []
        self.is_trained = False

        # Initialize models
        self.models['price_predictor'] = RandomForestRegressor(n_estimators=100, random_state=42)
        self.models['signal_classifier'] = RandomForestClassifier(n_estimators=100, random_state=42)

        if TENSORFLOW_AVAILABLE:
            self.models['lstm_predictor'] = self._create_lstm_model()

    def _create_lstm_model(self):
        """Create LSTM model for time series prediction"""
        model = Sequential([
            LSTM(50, return_sequences=True, input_shape=(60, 1)),
            Dropout(0.2),
            LSTM(50, return_sequences=True),
            Dropout(0.2),
            LSTM(50),
            Dropout(0.2),
            Dense(1)
        ])
        model.compile(optimizer=Adam(learning_rate=0.001), loss='mse')
        return model

    def prepare_features(self, market_data):
        """Prepare features for machine learning"""
        if len(market_data) < 100:
            return None, None

        features = []
        targets = []

        for i in range(60, len(market_data)):
            # Technical indicators as features
            price_window = market_data['price'].iloc[i - 60:i].values
            indicators = TechnicalAnalysis.calculate_indicators(price_window)

            feature_vector = [
                indicators.get('rsi', 50),
                indicators.get('ma_5', 0),
                indicators.get('ma_20', 0),
                indicators.get('ma_50', 0),
                indicators.get('macd', 0),
                indicators.get('bb_upper', 0),
                indicators.get('bb_lower', 0),
                indicators.get('stoch_k', 50),
                indicators.get('williams_r', -50),
                indicators.get('momentum_5', 0),
                indicators.get('momentum_10', 0),
                market_data['volume'].iloc[i] if 'volume' in market_data.columns else 0,
                market_data['change_24h'].iloc[i] if 'change_24h' in market_data.columns else 0
            ]

            features.append(feature_vector)

            # Target: price movement in next period
            current_price = market_data['price'].iloc[i]
            next_price = market_data['price'].iloc[min(i + 1, len(market_data) - 1)]
            price_change = (next_price - current_price) / current_price
            targets.append(price_change)

        self.feature_columns = [
            'rsi', 'ma_5', 'ma_20', 'ma_50', 'macd', 'bb_upper', 'bb_lower',
            'stoch_k', 'williams_r', 'momentum_5', 'momentum_10', 'volume', 'change_24h'
        ]

        return np.array(features), np.array(targets)

    def train_models(self, symbol, retrain=False):
        """Train machine learning models"""
        try:
            # Get market data
            market_data = self.db_manager.get_market_data(symbol, limit=5000)
            if len(market_data) < 200:
                return False, "Insufficient data for training"

            # Prepare features
            features, targets = self.prepare_features(market_data)
            if features is None:
                return False, "Failed to prepare features"

            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                features, targets, test_size=0.2, shuffle=False
            )

            # Scale features
            self.scalers['features'] = StandardScaler()
            X_train_scaled = self.scalers['features'].fit_transform(X_train)
            X_test_scaled = self.scalers['features'].transform(X_test)

            # Train price predictor
            self.models['price_predictor'].fit(X_train_scaled, y_train)
            price_predictions = self.models['price_predictor'].predict(X_test_scaled)
            price_mse = mean_squared_error(y_test, price_predictions)

            # Prepare classification targets (buy/hold/sell)
            y_class = np.where(y_train > 0.01, 1, np.where(y_train < -0.01, -1, 0))  # buy/sell/hold

            # Train signal classifier
            self.models['signal_classifier'].fit(X_train_scaled, y_class)
            signal_predictions = self.models['signal_classifier'].predict(X_test_scaled)
            y_class_test = np.where(y_test > 0.01, 1, np.where(y_test < -0.01, -1, 0))
            signal_accuracy = accuracy_score(y_class_test, signal_predictions)

            # Train LSTM if available
            lstm_mse = None
            if TENSORFLOW_AVAILABLE and self.models.get('lstm_predictor'):
                # Reshape for LSTM
                X_lstm = X_train_scaled.reshape((X_train_scaled.shape[0], X_train_scaled.shape[1], 1))
                X_test_lstm = X_test_scaled.reshape((X_test_scaled.shape[0], X_test_scaled.shape[1], 1))

                self.models['lstm_predictor'].fit(
                    X_lstm, y_train,
                    epochs=50, batch_size=32,
                    validation_split=0.2, verbose=0
                )

                lstm_predictions = self.models['lstm_predictor'].predict(X_test_lstm)
                lstm_mse = mean_squared_error(y_test, lstm_predictions.flatten())

            self.is_trained = True

            # Save model performance
            performance_data = (
                datetime.now(), 'combined_model', signal_accuracy,
                signal_accuracy, signal_accuracy, price_mse,
                len(X_test), np.sum(signal_predictions == y_class_test)
            )

            conn = sqlite3.connect(self.db_manager.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO model_performance 
                (timestamp, model_name, accuracy, precision, recall, profit_factor, total_trades, winning_trades)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', performance_data)
            conn.commit()
            conn.close()

            return True, f"Models trained successfully. Signal Accuracy: {signal_accuracy:.3f}, Price MSE: {price_mse:.6f}"

        except Exception as e:
            return False, f"Training failed: {str(e)}"

    def predict_signal(self, current_features):
        """Predict trading signal using trained models"""
        if not self.is_trained or not self.scalers.get('features'):
            return {'action': 'hold', 'confidence': 0, 'reason': 'Model not trained'}

        try:
            # Scale features
            features_scaled = self.scalers['features'].transform([current_features])

            # Get predictions from all models
            price_prediction = self.models['price_predictor'].predict(features_scaled)[0]
            signal_prediction = self.models['signal_classifier'].predict(features_scaled)[0]
            signal_probability = self.models['signal_classifier'].predict_proba(features_scaled)[0]

            # Get LSTM prediction if available
            lstm_prediction = None
            if TENSORFLOW_AVAILABLE and self.models.get('lstm_predictor'):
                features_lstm = features_scaled.reshape((1, features_scaled.shape[1], 1))
                lstm_prediction = self.models['lstm_predictor'].predict(features_lstm)[0][0]

            # Combine predictions
            confidence = max(signal_probability)

            if signal_prediction == 1:  # Buy signal
                action = 'buy'
                reason = f"ML Buy Signal (Price: +{price_prediction:.3f}%, Conf: {confidence:.3f})"
            elif signal_prediction == -1:  # Sell signal
                action = 'sell'
                reason = f"ML Sell Signal (Price: {price_prediction:.3f}%, Conf: {confidence:.3f})"
            else:  # Hold
                action = 'hold'
                reason = f"ML Hold Signal (Price: {price_prediction:.3f}%, Conf: {confidence:.3f})"

            # Adjust confidence based on LSTM prediction
            if lstm_prediction is not None:
                if (lstm_prediction > 0 and action == 'buy') or (lstm_prediction < 0 and action == 'sell'):
                    confidence *= 1.2  # Boost confidence if LSTM agrees
                else:
                    confidence *= 0.8  # Reduce confidence if LSTM disagrees

            return {
                'action': action,
                'confidence': min(confidence, 0.95),
                'reason': reason,
                'price_prediction': price_prediction,
                'ml_signal': signal_prediction
            }

        except Exception as e:
            return {'action': 'hold', 'confidence': 0, 'reason': f'Prediction error: {str(e)}'}


class SmartAITrader:
    """Main AI Trading Bot with machine learning capabilities"""

    def __init__(self, root):
        self.root = root
        self.root.title("Smart AI Trading Bot with Machine Learning")
        self.root.geometry("1600x1000")
        self.root.configure(bg='#1a1a1a')

        # Initialize components
        self.db_manager = DatabaseManager()
        self.api_client = None
        self.ml_model = MLTradingModel(self.db_manager)

        # Trading state
        self.ai_enabled = False
        self.stop_trading = False
        self.learning_mode = True

        # Data storage
        self.price_history = deque(maxlen=1000)
        self.market_data_buffer = deque(maxlen=100)

        # Performance tracking
        self.performance_metrics = {
            'total_trades': 0,
            'successful_trades': 0,
            'total_pnl': 0.0,
            'win_rate': 0.0,
            'sharpe_ratio': 0.0,
            'max_drawdown': 0.0
        }

        # Configuration
        self.config = {
            'trading_symbol': 'btc_thb',
            'risk_level': 'medium',
            'min_confidence': 0.7,
            'position_size': 100,
            'learning_enabled': True,
            'auto_retrain': True,
            'retrain_interval': 24  # hours
        }

        self.setup_gui()
        self.start_data_collection()

    def setup_gui(self):
        """Setup the enhanced GUI"""
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Header
        self.setup_header(main_frame)

        # Notebook
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill='both', expand=True, pady=(10, 0))

        # Create tabs
        self.setup_ai_dashboard_tab(notebook)
        self.setup_ml_analysis_tab(notebook)
        self.setup_api_config_tab(notebook)
        self.setup_trading_config_tab(notebook)
        self.setup_performance_tab(notebook)
        self.setup_data_management_tab(notebook)

        # Status bar
        self.setup_status_bar(main_frame)

    def setup_header(self, parent):
        """Setup header with key metrics"""
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill='x', pady=(0, 10))

        # Title
        ttk.Label(header_frame, text="🤖 Smart AI Trading Bot",
                  font=('Arial', 16, 'bold')).pack(side='left')

        # Status indicators
        status_frame = ttk.Frame(header_frame)
        status_frame.pack(side='right')

        self.status_labels = {}
        statuses = [
            ("AI Status", "🔴 Offline"),
            ("ML Model", "🔴 Not Trained"),
            ("Data Collection", "🟡 Starting"),
            ("Portfolio", "0 THB")
        ]

        for i, (label, value) in enumerate(statuses):
            frame = ttk.Frame(status_frame)
            frame.grid(row=0, column=i, padx=15)

            ttk.Label(frame, text=label, font=('Arial', 9)).pack()
            self.status_labels[label] = ttk.Label(frame, text=value,
                                                  font=('Arial', 11, 'bold'))
            self.status_labels[label].pack()

    def setup_ai_dashboard_tab(self, notebook):
        """AI Dashboard tab"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="🤖 AI Dashboard")

        # Control panel
        control_frame = ttk.LabelFrame(frame, text="AI Control Center")
        control_frame.pack(fill='x', padx=10, pady=10)

        control_inner = ttk.Frame(control_frame)
        control_inner.pack(fill='x', padx=10, pady=10)

        # Main control buttons
        self.ai_toggle_btn = ttk.Button(control_inner, text="🚀 Start AI Trading",
                                        command=self.toggle_ai_trading)
        self.ai_toggle_btn.pack(side='left', padx=10)

        ttk.Button(control_inner, text="🧠 Train Models",
                   command=self.train_models).pack(side='left', padx=10)

        ttk.Button(control_inner, text="🛑 Emergency Stop",
                   command=self.emergency_stop).pack(side='left', padx=10)

        # Learning mode toggle
        self.learning_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(control_inner, text="Learning Mode",
                        variable=self.learning_var).pack(side='right', padx=10)

        # Real-time analysis
        analysis_frame = ttk.LabelFrame(frame, text="Real-time Market Analysis")
        analysis_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Split into two columns
        left_frame = ttk.Frame(analysis_frame)
        left_frame.pack(side='left', fill='both', expand=True, padx=10, pady=10)

        right_frame = ttk.Frame(analysis_frame)
        right_frame.pack(side='right', fill='both', expand=True, padx=10, pady=10)

        # Technical indicators
        indicators_frame = ttk.LabelFrame(left_frame, text="Technical Indicators")
        indicators_frame.pack(fill='x', pady=(0, 10))

        self.indicators = {}
        indicator_names = ["RSI", "MACD", "BB Position", "MA Trend", "Volume", "ML Signal"]

        for name in indicator_names:
            row = ttk.Frame(indicators_frame)
            row.pack(fill='x', padx=10, pady=2)

            ttk.Label(row, text=f"{name}:", width=12).pack(side='left')
            self.indicators[name] = ttk.Label(row, text="--", font=('Arial', 10, 'bold'))
            self.indicators[name].pack(side='left')

        # AI decisions log
        decisions_frame = ttk.LabelFrame(right_frame, text="AI Decision Log")
        decisions_frame.pack(fill='both', expand=True)

        self.decisions_log = scrolledtext.ScrolledText(decisions_frame, height=15,
                                                       bg='#1e1e1e', fg='#00ff88',
                                                       font=('Consolas', 9))
        self.decisions_log.pack(fill='both', expand=True, padx=10, pady=10)

        # Trading log
        trading_frame = ttk.LabelFrame(left_frame, text="Trading Activity")
        trading_frame.pack(fill='both', expand=True)

        self.trading_log = scrolledtext.ScrolledText(trading_frame, height=15,
                                                     bg='#1e1e1e', fg='#ffffff',
                                                     font=('Consolas', 9))
        self.trading_log.pack(fill='both', expand=True, padx=10, pady=10)

    def setup_ml_analysis_tab(self, notebook):
        """Machine Learning Analysis tab"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="🧠 ML Analysis")

        # Model status
        model_frame = ttk.LabelFrame(frame, text="Model Status & Performance")
        model_frame.pack(fill='x', padx=10, pady=10)

        model_inner = ttk.Frame(model_frame)
        model_inner.pack(fill='x', padx=10, pady=10)

        # Model metrics
        self.model_metrics = {}
        metrics = [
            ("Model Accuracy", "Not trained"),
            ("Prediction Confidence", "N/A"),
            ("Last Training", "Never"),
            ("Data Points", "0"),
            ("Feature Importance", "N/A")
        ]

        for i, (label, value) in enumerate(metrics):
            row, col = i // 2, i % 2
            metric_frame = ttk.Frame(model_inner)
            metric_frame.grid(row=row, column=col, padx=20, pady=5, sticky='ew')

            ttk.Label(metric_frame, text=f"{label}:", width=15).pack(side='left')
            self.model_metrics[label] = ttk.Label(metric_frame, text=value,
                                                  font=('Arial', 10, 'bold'))
            self.model_metrics[label].pack(side='left')

        # Training controls
        training_frame = ttk.LabelFrame(frame, text="Model Training & Configuration")
        training_frame.pack(fill='x', padx=10, pady=10)

        training_inner = ttk.Frame(training_frame)
        training_inner.pack(fill='x', padx=10, pady=10)

        ttk.Button(training_inner, text="🔄 Retrain Models",
                   command=self.retrain_models).pack(side='left', padx=10)
        ttk.Button(training_inner, text="📊 Model Performance",
                   command=self.show_model_performance).pack(side='left', padx=10)
        ttk.Button(training_inner, text="💾 Save Models",
                   command=self.save_models).pack(side='left', padx=10)
        ttk.Button(training_inner, text="📁 Load Models",
                   command=self.load_models).pack(side='left', padx=10)

        # Feature analysis
        if MATPLOTLIB_AVAILABLE:
            chart_frame = ttk.LabelFrame(frame, text="Feature Importance & Model Analysis")
            chart_frame.pack(fill='both', expand=True, padx=10, pady=10)

            self.setup_ml_charts(chart_frame)

        # Model predictions
        prediction_frame = ttk.LabelFrame(frame, text="Current Predictions")
        prediction_frame.pack(fill='both', expand=True, padx=10, pady=10)

        self.prediction_text = scrolledtext.ScrolledText(prediction_frame, height=10,
                                                         bg='#1e1e1e', fg='#00aaff',
                                                         font=('Consolas', 9))
        self.prediction_text.pack(fill='both', expand=True, padx=10, pady=10)

    def setup_api_config_tab(self, notebook):
        """API Configuration tab"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="🔧 API Config")

        # API setup
        api_frame = ttk.LabelFrame(frame, text="Bitkub API Configuration")
        api_frame.pack(fill='x', padx=20, pady=20)

        # Instructions
        instructions = """
🔑 API Setup Instructions:
1. Login to Bitkub.com → Settings → API Management
2. Create new API Key with trading permissions
3. Add your IP to whitelist
4. Enter credentials below and test connection
        """
        ttk.Label(api_frame, text=instructions, justify='left').pack(padx=10, pady=10)

        # API inputs
        api_inner = ttk.Frame(api_frame)
        api_inner.pack(fill='x', padx=10, pady=10)

        ttk.Label(api_inner, text="API Key:", font=('Arial', 11, 'bold')).pack(anchor='w')
        self.api_key_entry = ttk.Entry(api_inner, width=80, show="*")
        self.api_key_entry.pack(fill='x', pady=(5, 10))

        ttk.Label(api_inner, text="API Secret:", font=('Arial', 11, 'bold')).pack(anchor='w')
        self.api_secret_entry = ttk.Entry(api_inner, width=80, show="*")
        self.api_secret_entry.pack(fill='x', pady=(5, 10))

        # Control buttons
        btn_frame = ttk.Frame(api_inner)
        btn_frame.pack(fill='x', pady=10)

        ttk.Button(btn_frame, text="💾 Save & Test",
                   command=self.save_and_test_api).pack(side='left', padx=10)
        ttk.Button(btn_frame, text="👁️ Show/Hide",
                   command=self.toggle_api_visibility).pack(side='left', padx=10)

        # Connection status
        self.connection_status = ttk.Label(btn_frame, text="⚫ Not Connected",
                                           font=('Arial', 12, 'bold'))
        self.connection_status.pack(side='right')

    def setup_trading_config_tab(self, notebook):
        """Trading Configuration tab"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="⚙️ Trading Config")

        # Trading parameters
        config_frame = ttk.LabelFrame(frame, text="Trading Parameters")
        config_frame.pack(fill='x', padx=20, pady=20)

        config_inner = ttk.Frame(config_frame)
        config_inner.pack(fill='x', padx=10, pady=10)

        # Configuration variables
        self.config_vars = {}
        configs = [
            ("Trading Symbol", "trading_symbol", ["btc_thb", "eth_thb", "ada_thb"], "combo"),
            ("Risk Level", "risk_level", ["low", "medium", "high"], "combo"),
            ("Min Confidence", "min_confidence", "0.7", "entry"),
            ("Position Size (THB)", "position_size", "100", "entry"),
            ("Max Daily Trades", "max_daily_trades", "10", "entry"),
            ("Stop Loss (%)", "stop_loss", "5", "entry")
        ]

        for i, (label, key, default, widget_type) in enumerate(configs):
            row = ttk.Frame(config_inner)
            row.grid(row=i, column=0, columnspan=2, sticky='ew', pady=5)
            config_inner.grid_columnconfigure(1, weight=1)

            ttk.Label(row, text=f"{label}:", width=20).pack(side='left')

            if widget_type == "combo":
                var = tk.StringVar(value=default[0] if isinstance(default, list) else default)
                widget = ttk.Combobox(row, textvariable=var, values=default if isinstance(default, list) else [default],
                                      state='readonly', width=20)
            else:
                var = tk.StringVar(value=default)
                widget = ttk.Entry(row, textvariable=var, width=20)

            widget.pack(side='left', padx=10)
            self.config_vars[key] = var

        # AI/ML Settings
        ml_frame = ttk.LabelFrame(frame, text="AI/ML Settings")
        ml_frame.pack(fill='x', padx=20, pady=20)

        ml_inner = ttk.Frame(ml_frame)
        ml_inner.pack(fill='x', padx=10, pady=10)

        self.ml_config_vars = {}
        ml_configs = [
            ("Enable Learning", "learning_enabled", True, "check"),
            ("Auto Retrain", "auto_retrain", True, "check"),
            ("Retrain Interval (hours)", "retrain_interval", "24", "entry"),
            ("Data Collection Rate (sec)", "data_rate", "30", "entry"),
            ("Feature Window Size", "feature_window", "60", "entry")
        ]

        for i, (label, key, default, widget_type) in enumerate(ml_configs):
            row = ttk.Frame(ml_inner)
            row.grid(row=i, column=0, columnspan=2, sticky='ew', pady=5)

            ttk.Label(row, text=f"{label}:", width=25).pack(side='left')

            if widget_type == "check":
                var = tk.BooleanVar(value=default)
                widget = ttk.Checkbutton(row, variable=var)
            else:
                var = tk.StringVar(value=str(default))
                widget = ttk.Entry(row, textvariable=var, width=15)

            widget.pack(side='left', padx=10)
            self.ml_config_vars[key] = var

        # Save configuration
        ttk.Button(ml_inner, text="💾 Save Configuration",
                   command=self.save_configuration).grid(row=len(ml_configs), column=1, pady=20)

    def setup_performance_tab(self, notebook):
        """Performance Analysis tab"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="📊 Performance")

        # Performance metrics
        metrics_frame = ttk.LabelFrame(frame, text="Performance Metrics")
        metrics_frame.pack(fill='x', padx=10, pady=10)

        metrics_inner = ttk.Frame(metrics_frame)
        metrics_inner.pack(fill='x', padx=10, pady=10)

        self.performance_labels = {}
        perf_metrics = [
            ("Total Trades", "0"),
            ("Win Rate", "0%"),
            ("Total P&L", "0 THB"),
            ("Sharpe Ratio", "0.00"),
            ("Max Drawdown", "0%"),
            ("Average Trade", "0 THB")
        ]

        for i, (label, value) in enumerate(perf_metrics):
            row, col = i // 3, i % 3
            metric_frame = ttk.Frame(metrics_inner)
            metric_frame.grid(row=row, column=col, padx=20, pady=10, sticky='ew')

            ttk.Label(metric_frame, text=label).pack()
            self.performance_labels[label] = ttk.Label(metric_frame, text=value,
                                                       font=('Arial', 14, 'bold'))
            self.performance_labels[label].pack()

        for i in range(3):
            metrics_inner.grid_columnconfigure(i, weight=1)

        # Trade history
        history_frame = ttk.LabelFrame(frame, text="Trade History")
        history_frame.pack(fill='both', expand=True, padx=10, pady=10)

        self.trade_history_text = scrolledtext.ScrolledText(history_frame,
                                                            bg='#1e1e1e', fg='#ffffff',
                                                            font=('Consolas', 10))
        self.trade_history_text.pack(fill='both', expand=True, padx=10, pady=10)

    def setup_data_management_tab(self, notebook):
        """Data Management tab"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="📁 Data Management")

        # Database info
        db_frame = ttk.LabelFrame(frame, text="Database Information")
        db_frame.pack(fill='x', padx=10, pady=10)

        db_inner = ttk.Frame(db_frame)
        db_inner.pack(fill='x', padx=10, pady=10)

        self.db_info_labels = {}
        db_metrics = [
            ("Market Data Records", "0"),
            ("Trading Signals", "0"),
            ("Trade History", "0"),
            ("Model Performance Records", "0")
        ]

        for i, (label, value) in enumerate(db_metrics):
            row, col = i // 2, i % 2
            metric_frame = ttk.Frame(db_inner)
            metric_frame.grid(row=row, column=col, padx=20, pady=5, sticky='ew')

            ttk.Label(metric_frame, text=f"{label}:", width=25).pack(side='left')
            self.db_info_labels[label] = ttk.Label(metric_frame, text=value,
                                                   font=('Arial', 10, 'bold'))
            self.db_info_labels[label].pack(side='left')

        # Data management controls
        controls_frame = ttk.LabelFrame(frame, text="Data Management")
        controls_frame.pack(fill='x', padx=10, pady=10)

        controls_inner = ttk.Frame(controls_frame)
        controls_inner.pack(fill='x', padx=10, pady=10)

        ttk.Button(controls_inner, text="🔄 Refresh Stats",
                   command=self.refresh_db_stats).pack(side='left', padx=10)
        ttk.Button(controls_inner, text="📤 Export Data",
                   command=self.export_data).pack(side='left', padx=10)
        ttk.Button(controls_inner, text="🗑️ Clean Old Data",
                   command=self.clean_old_data).pack(side='left', padx=10)
        ttk.Button(controls_inner, text="🔧 Optimize Database",
                   command=self.optimize_database).pack(side='left', padx=10)

        # Data analysis
        analysis_frame = ttk.LabelFrame(frame, text="Data Analysis")
        analysis_frame.pack(fill='both', expand=True, padx=10, pady=10)

        self.data_analysis_text = scrolledtext.ScrolledText(analysis_frame,
                                                            bg='#1e1e1e', fg='#ffffff',
                                                            font=('Consolas', 10))
        self.data_analysis_text.pack(fill='both', expand=True, padx=10, pady=10)

    def setup_ml_charts(self, parent):
        """Setup ML analysis charts"""
        if not MATPLOTLIB_AVAILABLE:
            ttk.Label(parent, text="Matplotlib not available for charts").pack()
            return

        # Create figure
        self.ml_fig, ((self.ax1, self.ax2), (self.ax3, self.ax4)) = plt.subplots(2, 2, figsize=(12, 8))
        self.ml_fig.patch.set_facecolor('#1a1a1a')

        for ax in [self.ax1, self.ax2, self.ax3, self.ax4]:
            ax.set_facecolor('#1a1a1a')
            ax.tick_params(colors='white')
            for spine in ax.spines.values():
                spine.set_color('white')

        self.ml_canvas = FigureCanvasTkAgg(self.ml_fig, parent)
        self.ml_canvas.get_tk_widget().pack(fill='both', expand=True, padx=10, pady=10)

    def setup_status_bar(self, parent):
        """Setup status bar"""
        status_frame = ttk.Frame(parent)
        status_frame.pack(side='bottom', fill='x', pady=(10, 0))

        self.status_var = tk.StringVar()
        self.status_var.set("🤖 Smart AI Trading Bot Ready - Initialize API and start learning!")
        status_label = ttk.Label(status_frame, textvariable=self.status_var, relief='sunken')
        status_label.pack(side='left', fill='x', expand=True)

        # Time display
        self.time_var = tk.StringVar()
        time_label = ttk.Label(status_frame, textvariable=self.time_var, relief='sunken')
        time_label.pack(side='right', padx=5)

        self.update_time()

    def update_time(self):
        """Update time display"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_var.set(current_time)
        self.root.after(1000, self.update_time)

    # === Core AI Trading Functions ===

    def toggle_ai_trading(self):
        """Toggle AI trading on/off"""
        if not self.api_client:
            messagebox.showerror("Error", "Please configure API first!")
            return

        if not self.ml_model.is_trained:
            if messagebox.askyesno("Model Not Trained",
                                   "ML model is not trained. Train now?"):
                self.train_models()
                return

        if not self.ai_enabled:
            self.start_ai_trading()
        else:
            self.stop_ai_trading()

    def start_ai_trading(self):
        """Start AI trading"""
        self.ai_enabled = True
        self.stop_trading = False

        self.ai_toggle_btn.configure(text="🛑 Stop AI Trading")
        self.status_labels["AI Status"].configure(text="🟢 Active")

        # Start AI trading thread
        threading.Thread(target=self.ai_trading_loop, daemon=True).start()

        self.log_trading("🚀 AI Trading System Started!")
        self.log_decisions("AI Trading activated with ML model")

    def stop_ai_trading(self):
        """Stop AI trading"""
        self.ai_enabled = False
        self.stop_trading = True

        self.ai_toggle_btn.configure(text="🚀 Start AI Trading")
        self.status_labels["AI Status"].configure(text="🔴 Stopped")

        self.log_trading("🛑 AI Trading System Stopped!")

    def emergency_stop(self):
        """Emergency stop all trading"""
        if messagebox.askyesno("Emergency Stop",
                               "🚨 EMERGENCY STOP 🚨\n\nStop all trading immediately?"):
            self.stop_ai_trading()
            self.log_trading("🚨 EMERGENCY STOP ACTIVATED!")

    def ai_trading_loop(self):
        """Main AI trading loop"""
        last_retrain = time.time()

        while self.ai_enabled and not self.stop_trading:
            try:
                # Get market data
                symbol = self.config['trading_symbol']
                ticker_data = self.api_client.get_ticker(symbol)

                if not ticker_data or len(ticker_data) == 0:
                    time.sleep(30)
                    continue

                current_price = float(ticker_data[0]['last'])
                self.price_history.append(current_price)

                # Collect market data for ML
                self.collect_market_data(ticker_data[0])

                # Get technical indicators
                if len(self.price_history) >= 60:
                    indicators = TechnicalAnalysis.calculate_indicators(list(self.price_history))
                    self.update_indicators_display(indicators)

                    # Prepare features for ML prediction
                    current_features = [
                        indicators.get('rsi', 50),
                        indicators.get('ma_5', current_price),
                        indicators.get('ma_20', current_price),
                        indicators.get('ma_50', current_price),
                        indicators.get('macd', 0),
                        indicators.get('bb_upper', current_price),
                        indicators.get('bb_lower', current_price),
                        indicators.get('stoch_k', 50),
                        indicators.get('williams_r', -50),
                        indicators.get('momentum_5', 0),
                        indicators.get('momentum_10', 0),
                        float(ticker_data[0].get('base_volume', 0)),
                        float(ticker_data[0].get('percent_change', 0))
                    ]

                    # Get ML prediction
                    if self.ml_model.is_trained:
                        signal = self.ml_model.predict_signal(current_features)
                        self.log_decisions(f"ML Signal: {signal['action'].upper()} "
                                           f"(Confidence: {signal['confidence']:.3f}) - {signal['reason']}")

                        # Execute trade if confidence is high enough
                        min_confidence = float(self.config['min_confidence'])
                        if signal['action'] != 'hold' and signal['confidence'] >= min_confidence:
                            self.execute_ai_trade(signal, current_price)

                # Auto-retrain model if enabled
                if (self.ml_config_vars.get('auto_retrain', tk.BooleanVar(value=True)).get() and
                        time.time() - last_retrain > float(
                            self.ml_config_vars.get('retrain_interval', tk.StringVar(value='24')).get()) * 3600):
                    self.log_trading("🔄 Auto-retraining ML model...")
                    self.train_models()
                    last_retrain = time.time()

                # Sleep before next iteration
                time.sleep(30)

            except Exception as e:
                self.log_trading(f"❌ AI Trading Error: {str(e)}")
                time.sleep(60)

    def execute_ai_trade(self, signal, current_price):
        """Execute AI trading decision"""
        try:
            position_size = float(self.config['position_size'])
            symbol = self.config['trading_symbol']

            if signal['action'] == 'buy':
                result = self.api_client.place_buy_order(symbol, position_size, 0, 'market')
                if result and result.get('error') == 0:
                    self.log_trading(f"✅ AI BUY executed: {position_size} THB at {current_price:.2f}")
                    self.performance_metrics['total_trades'] += 1

                    # Save to database
                    trade_data = (
                        datetime.now(), symbol, 'buy', position_size, current_price,
                        0, 0, result.get('result', {}).get('id', ''), 'ML_AI'
                    )
                    self.db_manager.save_trade(trade_data)
                else:
                    self.log_trading(f"❌ AI BUY failed: {result}")

            elif signal['action'] == 'sell':
                # Check crypto balance first
                wallet = self.api_client.get_wallet()
                if wallet and wallet.get('error') == 0:
                    crypto_symbol = symbol.split('_')[0].upper()
                    crypto_balance = wallet.get('result', {}).get(crypto_symbol, 0)

                    if crypto_balance > 0:
                        sell_amount = min(crypto_balance * 0.5, position_size / current_price)

                        result = self.api_client.place_sell_order(symbol, sell_amount, 0, 'market')
                        if result and result.get('error') == 0:
                            self.log_trading(
                                f"✅ AI SELL executed: {sell_amount:.8f} {crypto_symbol} at {current_price:.2f}")
                            self.performance_metrics['total_trades'] += 1

                            # Save to database
                            trade_data = (
                                datetime.now(), symbol, 'sell', sell_amount, current_price,
                                0, 0, result.get('result', {}).get('id', ''), 'ML_AI'
                            )
                            self.db_manager.save_trade(trade_data)
                        else:
                            self.log_trading(f"❌ AI SELL failed: {result}")

            # Save signal to database
            signal_data = (
                datetime.now(), symbol, signal['action'], signal['confidence'],
                current_price, signal['reason'], True, 'executed'
            )
            self.db_manager.save_trading_signal(signal_data)

        except Exception as e:
            self.log_trading(f"❌ Trade execution error: {str(e)}")

    def collect_market_data(self, ticker_data):
        """Collect and store market data for ML"""
        try:
            if len(self.price_history) >= 50:
                indicators = TechnicalAnalysis.calculate_indicators(list(self.price_history))

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
                    indicators.get('bb_upper', 0),
                    indicators.get('bb_middle', 0),
                    indicators.get('bb_lower', 0),
                    indicators.get('ma_5', 0),
                    indicators.get('ma_20', 0),
                    indicators.get('ma_50', 0)
                )

                self.db_manager.save_market_data(market_data)
                self.status_labels["Data Collection"].configure(text="🟢 Collecting")

        except Exception as e:
            self.log_trading(f"❌ Data collection error: {str(e)}")

    def train_models(self):
        """Train ML models"""

        def train():
            try:
                self.log_trading("🧠 Starting ML model training...")
                self.status_labels["ML Model"].configure(text="🟡 Training...")

                success, message = self.ml_model.train_models(self.config['trading_symbol'])

                if success:
                    self.status_labels["ML Model"].configure(text="🟢 Trained")
                    self.log_trading(f"✅ {message}")
                    self.update_model_metrics()
                else:
                    self.status_labels["ML Model"].configure(text="🔴 Failed")
                    self.log_trading(f"❌ Training failed: {message}")

            except Exception as e:
                self.log_trading(f"❌ Training error: {str(e)}")

        threading.Thread(target=train, daemon=True).start()

    def start_data_collection(self):
        """Start background data collection"""

        def collect():
            while True:
                try:
                    if self.api_client:
                        symbol = self.config['trading_symbol']
                        ticker_data = self.api_client.get_ticker(symbol)

                        if ticker_data and len(ticker_data) > 0:
                            current_price = float(ticker_data[0]['last'])
                            self.price_history.append(current_price)

                            # Collect data for ML if learning mode is enabled
                            if self.learning_var.get():
                                self.collect_market_data(ticker_data[0])

                    data_rate = int(self.ml_config_vars.get('data_rate', tk.StringVar(value='30')).get())
                    time.sleep(data_rate)

                except Exception as e:
                    print(f"Data collection error: {e}")
                    time.sleep(60)

        threading.Thread(target=collect, daemon=True).start()

    # === Utility Functions ===

    def log_trading(self, message):
        """Log trading message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"

        self.trading_log.insert(tk.END, log_entry)
        self.trading_log.see(tk.END)

        # Keep only last 100 lines
        lines = self.trading_log.get('1.0', tk.END).split('\n')
        if len(lines) > 100:
            self.trading_log.delete('1.0', f'{len(lines) - 100}.0')

    def log_decisions(self, message):
        """Log AI decision"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"

        self.decisions_log.insert(tk.END, log_entry)
        self.decisions_log.see(tk.END)

        # Keep only last 100 lines
        lines = self.decisions_log.get('1.0', tk.END).split('\n')
        if len(lines) > 100:
            self.decisions_log.delete('1.0', f'{len(lines) - 100}.0')

    def update_indicators_display(self, indicators):
        """Update technical indicators display"""
        self.indicators["RSI"].configure(text=f"{indicators.get('rsi', 0):.1f}")
        self.indicators["MACD"].configure(text=f"{indicators.get('macd', 0):.4f}")

        # BB Position
        bb_pos = "Middle"
        if len(self.price_history) > 0:
            current_price = self.price_history[-1]
            bb_upper = indicators.get('bb_upper', current_price)
            bb_lower = indicators.get('bb_lower', current_price)
            if current_price >= bb_upper:
                bb_pos = "Upper"
            elif current_price <= bb_lower:
                bb_pos = "Lower"

        self.indicators["BB Position"].configure(text=bb_pos)

        # MA Trend
        ma_trend = "Neutral"
        ma_5 = indicators.get('ma_5', 0)
        ma_20 = indicators.get('ma_20', 0)
        if ma_5 > ma_20 * 1.001:
            ma_trend = "Bullish"
        elif ma_5 < ma_20 * 0.999:
            ma_trend = "Bearish"

        self.indicators["MA Trend"].configure(text=ma_trend)
        self.indicators["Volume"].configure(text="Normal")  # Placeholder

        # ML Signal will be updated by ML model

    def update_model_metrics(self):
        """Update ML model performance metrics"""
        try:
            # Get latest model performance from database
            conn = sqlite3.connect(self.db_manager.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT accuracy, precision, recall, total_trades, winning_trades, timestamp
                FROM model_performance 
                ORDER BY timestamp DESC 
                LIMIT 1
            ''')

            result = cursor.fetchone()
            conn.close()

            if result:
                accuracy, precision, recall, total_trades, winning_trades, timestamp = result

                self.model_metrics["Model Accuracy"].configure(text=f"{accuracy:.3f}")
                self.model_metrics["Prediction Confidence"].configure(text=f"{precision:.3f}")
                self.model_metrics["Last Training"].configure(text=timestamp[:16])
                self.model_metrics["Data Points"].configure(text=str(total_trades))

                # Calculate feature importance (simplified)
                if hasattr(self.ml_model.models.get('signal_classifier'), 'feature_importances_'):
                    importances = self.ml_model.models['signal_classifier'].feature_importances_
                    top_feature_idx = np.argmax(importances)
                    if top_feature_idx < len(self.ml_model.feature_columns):
                        top_feature = self.ml_model.feature_columns[top_feature_idx]
                        self.model_metrics["Feature Importance"].configure(text=top_feature)

        except Exception as e:
            self.log_trading(f"Error updating model metrics: {str(e)}")

    def save_and_test_api(self):
        """Save and test API configuration"""
        api_key = self.api_key_entry.get().strip()
        api_secret = self.api_secret_entry.get().strip()

        if not api_key or not api_secret:
            messagebox.showerror("Error", "Please enter both API Key and Secret")
            return

        self.api_client = BitkubAPIClient(api_key, api_secret)
        self.connection_status.configure(text="🟡 Testing...")

        threading.Thread(target=self.test_api_connection, daemon=True).start()

    def test_api_connection(self):
        """Test API connection"""
        try:
            # Test private API
            wallet = self.api_client.get_wallet()
            if wallet and wallet.get('error') == 0:
                balance = wallet.get('result', {}).get('THB', 0)
                self.connection_status.configure(text="🟢 Connected")
                self.status_labels["Portfolio"].configure(text=f"{balance:,.2f} THB")
                messagebox.showinfo("Success", f"API Connected Successfully!\nTHB Balance: {balance:,.2f}")
            else:
                self.connection_status.configure(text="🔴 Auth Failed")
                error_msg = wallet.get('error', 'Unknown') if wallet else 'No response'
                messagebox.showerror("Error", f"API Authentication failed!\nError: {error_msg}")

        except Exception as e:
            self.connection_status.configure(text="🔴 Error")
            messagebox.showerror("Error", f"Connection error: {str(e)}")

    def toggle_api_visibility(self):
        """Toggle API credentials visibility"""
        if self.api_key_entry.cget('show') == '*':
            self.api_key_entry.configure(show='')
            self.api_secret_entry.configure(show='')
        else:
            self.api_key_entry.configure(show='*')
            self.api_secret_entry.configure(show='*')

    def save_configuration(self):
        """Save all configuration settings"""
        try:
            # Update config from GUI
            for key, var in self.config_vars.items():
                try:
                    value = var.get()
                    if key in ['min_confidence', 'position_size']:
                        self.config[key] = float(value)
                    elif key in ['max_daily_trades', 'stop_loss']:
                        self.config[key] = int(float(value))
                    else:
                        self.config[key] = value
                except:
                    pass

            # Update ML config
            for key, var in self.ml_config_vars.items():
                try:
                    if isinstance(var, tk.BooleanVar):
                        self.config[key] = var.get()
                    else:
                        value = var.get()
                        if key in ['retrain_interval', 'data_rate', 'feature_window']:
                            self.config[key] = int(float(value))
                        else:
                            self.config[key] = value
                except:
                    pass

            messagebox.showinfo("Success", "Configuration saved successfully!")
            self.log_trading("Configuration updated")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {str(e)}")

    def retrain_models(self):
        """Retrain ML models"""
        if messagebox.askyesno("Retrain Models",
                               "This will retrain all ML models with latest data.\nContinue?"):
            self.train_models()

    def show_model_performance(self):
        """Show detailed model performance"""
        try:
            conn = sqlite3.connect(self.db_manager.db_path)
            df = pd.read_sql_query('''
                SELECT * FROM model_performance 
                ORDER BY timestamp DESC 
                LIMIT 20
            ''', conn)
            conn.close()

            if len(df) > 0:
                performance_window = tk.Toplevel(self.root)
                performance_window.title("Model Performance History")
                performance_window.geometry("800x400")

                text_widget = scrolledtext.ScrolledText(performance_window, font=('Consolas', 10))
                text_widget.pack(fill='both', expand=True, padx=10, pady=10)

                # Format and display data
                text_widget.insert(tk.END, "Model Performance History\n")
                text_widget.insert(tk.END, "=" * 80 + "\n\n")

                for _, row in df.iterrows():
                    text_widget.insert(tk.END, f"Timestamp: {row['timestamp']}\n")
                    text_widget.insert(tk.END, f"Model: {row['model_name']}\n")
                    text_widget.insert(tk.END, f"Accuracy: {row['accuracy']:.3f}\n")
                    text_widget.insert(tk.END, f"Total Trades: {row['total_trades']}\n")
                    text_widget.insert(tk.END, f"Winning Trades: {row['winning_trades']}\n")
                    text_widget.insert(tk.END, "-" * 40 + "\n")
            else:
                messagebox.showinfo("Info", "No performance data available")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load performance data: {str(e)}")

    def save_models(self):
        """Save trained models to files"""
        try:
            models_dir = "saved_models"
            if not os.path.exists(models_dir):
                os.makedirs(models_dir)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Save sklearn models
            for model_name, model in self.ml_model.models.items():
                if model_name != 'lstm_predictor':  # Skip LSTM for now
                    filename = f"{models_dir}/{model_name}_{timestamp}.pkl"
                    with open(filename, 'wb') as f:
                        pickle.dump(model, f)

            # Save scalers
            for scaler_name, scaler in self.ml_model.scalers.items():
                filename = f"{models_dir}/{scaler_name}_scaler_{timestamp}.pkl"
                with open(filename, 'wb') as f:
                    pickle.dump(scaler, f)

            messagebox.showinfo("Success", f"Models saved to {models_dir}")
            self.log_trading(f"Models saved with timestamp {timestamp}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save models: {str(e)}")

    def load_models(self):
        """Load trained models from files"""
        try:
            models_dir = "saved_models"
            if not os.path.exists(models_dir):
                messagebox.showwarning("Warning", "No saved models directory found")
                return

            # For now, just show available models
            model_files = [f for f in os.listdir(models_dir) if f.endswith('.pkl')]
            if model_files:
                files_text = "\n".join(model_files)
                messagebox.showinfo("Available Models", f"Found models:\n{files_text}")
            else:
                messagebox.showinfo("Info", "No saved models found")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load models: {str(e)}")

    def refresh_db_stats(self):
        """Refresh database statistics"""
        try:
            conn = sqlite3.connect(self.db_manager.db_path)
            cursor = conn.cursor()

            # Get record counts
            tables = ['market_data', 'trading_signals', 'trade_history', 'model_performance']
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]

                label_map = {
                    'market_data': 'Market Data Records',
                    'trading_signals': 'Trading Signals',
                    'trade_history': 'Trade History',
                    'model_performance': 'Model Performance Records'
                }

                if label_map[table] in self.db_info_labels:
                    self.db_info_labels[label_map[table]].configure(text=str(count))

            conn.close()

            # Update data analysis
            self.analyze_data()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh stats: {str(e)}")

    def analyze_data(self):
        """Analyze collected data"""
        try:
            conn = sqlite3.connect(self.db_manager.db_path)

            # Get recent market data analysis
            market_df = pd.read_sql_query('''
                SELECT * FROM market_data 
                WHERE timestamp > datetime('now', '-7 days')
                ORDER BY timestamp DESC
            ''', conn)

            signals_df = pd.read_sql_query('''
                SELECT * FROM trading_signals 
                WHERE timestamp > datetime('now', '-7 days')
                ORDER BY timestamp DESC
            ''', conn)

            trades_df = pd.read_sql_query('''
                SELECT * FROM trade_history 
                WHERE timestamp > datetime('now', '-7 days')
                ORDER BY timestamp DESC
            ''', conn)

            conn.close()

            # Generate analysis report
            self.data_analysis_text.delete(1.0, tk.END)

            analysis_report = "=== DATA ANALYSIS REPORT ===\n"
            analysis_report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

            # Market data analysis
            if len(market_df) > 0:
                analysis_report += f"Market Data (Last 7 days):\n"
                analysis_report += f"- Records: {len(market_df)}\n"
                analysis_report += f"- Price Range: {market_df['price'].min():.2f} - {market_df['price'].max():.2f}\n"
                analysis_report += f"- Avg RSI: {market_df['rsi'].mean():.2f}\n"
                analysis_report += f"- Avg Volume: {market_df['volume'].mean():.2f}\n\n"

            # Trading signals analysis
            if len(signals_df) > 0:
                signal_counts = signals_df['signal_type'].value_counts()
                analysis_report += f"Trading Signals (Last 7 days):\n"
                analysis_report += f"- Total Signals: {len(signals_df)}\n"
                for signal_type, count in signal_counts.items():
                    analysis_report += f"- {signal_type.upper()}: {count}\n"
                analysis_report += f"- Avg Confidence: {signals_df['confidence'].mean():.3f}\n\n"

            # Trade history analysis
            if len(trades_df) > 0:
                buy_trades = len(trades_df[trades_df['action'] == 'buy'])
                sell_trades = len(trades_df[trades_df['action'] == 'sell'])
                analysis_report += f"Trade History (Last 7 days):\n"
                analysis_report += f"- Total Trades: {len(trades_df)}\n"
                analysis_report += f"- Buy Orders: {buy_trades}\n"
                analysis_report += f"- Sell Orders: {sell_trades}\n"
                analysis_report += f"- Avg Amount: {trades_df['amount'].mean():.2f}\n"

                if 'profit_loss' in trades_df.columns:
                    total_pnl = trades_df['profit_loss'].sum()
                    analysis_report += f"- Total P&L: {total_pnl:.2f} THB\n"

            self.data_analysis_text.insert(tk.END, analysis_report)

        except Exception as e:
            self.data_analysis_text.insert(tk.END, f"Analysis error: {str(e)}")

    def export_data(self):
        """Export data to CSV files"""
        try:
            export_dir = "exported_data"
            if not os.path.exists(export_dir):
                os.makedirs(export_dir)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            conn = sqlite3.connect(self.db_manager.db_path)

            # Export tables
            tables = ['market_data', 'trading_signals', 'trade_history', 'model_performance']

            for table in tables:
                df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
                if len(df) > 0:
                    filename = f"{export_dir}/{table}_{timestamp}.csv"
                    df.to_csv(filename, index=False)

            conn.close()

            messagebox.showinfo("Success", f"Data exported to {export_dir}")
            self.log_trading(f"Data exported with timestamp {timestamp}")

        except Exception as e:
            messagebox.showerror("Error", f"Export failed: {str(e)}")

    def clean_old_data(self):
        """Clean old data from database"""
        if messagebox.askyesno("Clean Old Data",
                               "This will remove data older than 30 days.\nContinue?"):
            try:
                conn = sqlite3.connect(self.db_manager.db_path)
                cursor = conn.cursor()

                # Delete old records
                tables = ['market_data', 'trading_signals', 'trade_history']
                for table in tables:
                    cursor.execute(f'''
                        DELETE FROM {table} 
                        WHERE timestamp < datetime('now', '-30 days')
                    ''')

                conn.commit()
                conn.close()

                messagebox.showinfo("Success", "Old data cleaned successfully")
                self.refresh_db_stats()

            except Exception as e:
                messagebox.showerror("Error", f"Cleanup failed: {str(e)}")

    def optimize_database(self):
        """Optimize database performance"""
        try:
            conn = sqlite3.connect(self.db_manager.db_path)
            cursor = conn.cursor()

            # Create indexes
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_market_data_timestamp ON market_data(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_market_data_symbol ON market_data(symbol)",
                "CREATE INDEX IF NOT EXISTS idx_trading_signals_timestamp ON trading_signals(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_trade_history_timestamp ON trade_history(timestamp)"
            ]

            for index_sql in indexes:
                cursor.execute(index_sql)

            # Vacuum database
            cursor.execute("VACUUM")

            conn.commit()
            conn.close()

            messagebox.showinfo("Success", "Database optimized successfully")
            self.log_trading("Database optimized")

        except Exception as e:
            messagebox.showerror("Error", f"Optimization failed: {str(e)}")


def main():
    """Main application entry point"""
    try:
        # Create main window
        root = tk.Tk()

        # Set window properties
        root.configure(bg='#1a1a1a')

        # Initialize the AI Trading Bot
        app = SmartAITrader(root)

        # Center window on screen
        root.update_idletasks()
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width // 2) - (1600 // 2)
        y = (screen_height // 2) - (1000 // 2)
        root.geometry(f"1600x1000+{x}+{y}")

        # Set minimum size
        root.minsize(1400, 800)

        # Welcome messages
        app.log_trading("🤖 Smart AI Trading Bot with Machine Learning Initialized!")
        app.log_trading("🧠 Advanced ML models ready for training and prediction")
        app.log_trading("📊 Real-time data collection and analysis system active")
        app.log_trading("⚠️ Please configure API credentials and train models before trading")

        # Start data collection
        app.refresh_db_stats()

        # Run the application
        root.mainloop()

    except KeyboardInterrupt:
        print("Application interrupted by user")
    except Exception as e:
        print(f"Application error: {e}")
        messagebox.showerror("Critical Error", f"Application failed to start: {e}")


if __name__ == "__main__":
    main()