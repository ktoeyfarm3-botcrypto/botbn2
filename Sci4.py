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
from concurrent.futures import ThreadPoolExecutor, as_completed
import statistics

# Configure theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class CoinRecommendationSystem:
    """🪙 ระบบแนะนำเหรียญขั้นสูง"""

    def __init__(self, api_client):
        self.api_client = api_client
        self.analysis_cache = {}
        self.cache_timeout = 300  # 5 นาที
        self.last_analysis_time = 0

    # 🔧 แก้ไขการคำนวณ Spread ใน analyze_single_coin

    def analyze_single_coin(self, symbol, trade_amount=1000):
        """วิเคราะห์เหรียญตัวเดียว - แก้ไข Spread"""
        try:
            # ดึงข้อมูล ticker
            ticker = self.api_client.get_simple_ticker(symbol)
            if not ticker:
                return None

            # คำนวณค่าต่างๆ
            price = float(ticker['last_price'])
            volume_24h = float(ticker.get('volume_24h', 0))
            change_24h = float(ticker.get('change_24h', 0))

            # 🔧 แก้ไขการคำนวณ spread
            spread_pct = 0.5  # ค่า default

            try:
                orderbook = self.api_client.get_orderbook(symbol)
                if orderbook and orderbook.get('bids') and orderbook.get('asks'):
                    bids = orderbook['bids']
                    asks = orderbook['asks']

                    if len(bids) > 0 and len(asks) > 0:
                        best_bid = float(bids[0][0])
                        best_ask = float(asks[0][0])

                        # ตรวจสอบว่าข้อมูลสมเหตุสมผล
                        if best_ask > best_bid > 0 and best_ask < price * 2 and best_bid > price * 0.5:
                            spread_pct = ((best_ask - best_bid) / price) * 100
                        else:
                            print(f"Invalid orderbook data for {symbol}: bid={best_bid}, ask={best_ask}, price={price}")
                            spread_pct = 0.5  # ใช้ค่า default
                    else:
                        spread_pct = 1.0  # ไม่มี liquidity
            except Exception as e:
                print(f"Orderbook error for {symbol}: {e}")
                spread_pct = 0.5  # ใช้ค่า default

            # ตรวจสอบ spread ที่คำนวณได้
            if spread_pct < 0 or spread_pct > 10:
                print(f"Abnormal spread for {symbol}: {spread_pct}%, using default 0.5%")
                spread_pct = 0.5

            # คำนวณค่าธรรมเนียม
            fees = self.api_client.calculate_trading_fees(trade_amount / price, price, "both")
            fee_impact = (fees / trade_amount) * 100

            # คำนวณ AI Score
            ai_score = self.calculate_ai_score(price, volume_24h, change_24h, spread_pct, fee_impact)

            return {
                'symbol': symbol,
                'price': price,
                'volume_24h': volume_24h,
                'change_24h': change_24h,
                'spread_pct': spread_pct,
                'fee_impact': fee_impact,
                'ai_score': ai_score,
                'recommendation': self.get_recommendation(ai_score),
                'analysis_time': datetime.now()
            }

        except Exception as e:
            print(f"Error analyzing {symbol}: {e}")
            return None

    # 🔧 หรือแก้ไขแบบง่ายๆ - เซ็ต spread เป็นค่าคงที่
    def analyze_single_coin_simple_fix(self, symbol, trade_amount=1000):
        """แก้ไขแบบง่าย - ใช้ default spread"""
        try:
            ticker = self.api_client.get_simple_ticker(symbol)
            if not ticker:
                return None

            price = float(ticker['last_price'])
            volume_24h = float(ticker.get('volume_24h', 0))
            change_24h = float(ticker.get('change_24h', 0))

            # ใช้ spread แบบประมาณการตาม volume
            if volume_24h > 100000000:  # >100M THB
                spread_pct = 0.1
            elif volume_24h > 50000000:  # >50M THB
                spread_pct = 0.2
            elif volume_24h > 10000000:  # >10M THB
                spread_pct = 0.3
            else:
                spread_pct = 0.5

            fees = self.api_client.calculate_trading_fees(trade_amount / price, price, "both")
            fee_impact = (fees / trade_amount) * 100

            ai_score = self.calculate_ai_score(price, volume_24h, change_24h, spread_pct, fee_impact)

            return {
                'symbol': symbol,
                'price': price,
                'volume_24h': volume_24h,
                'change_24h': change_24h,
                'spread_pct': spread_pct,
                'fee_impact': fee_impact,
                'ai_score': ai_score,
                'recommendation': self.get_recommendation(ai_score),
                'analysis_time': datetime.now()
            }

        except Exception as e:
            print(f"Error analyzing {symbol}: {e}")
            return None

    def calculate_ai_score(self, price, volume_24h, change_24h, spread_pct, fee_impact):
        """คำนวณ AI Score (0-10)"""
        score = 5.0  # Base score

        # Volume score (0-3 points)
        if volume_24h > 10000000:  # >10M THB
            score += 3
        elif volume_24h > 5000000:  # >5M THB
            score += 2
        elif volume_24h > 1000000:  # >1M THB
            score += 1
        elif volume_24h < 100000:  # <100K THB
            score -= 2

        # Spread score (-2 to +1 points)
        if spread_pct < 0.1:
            score += 1
        elif spread_pct < 0.5:
            score += 0.5
        elif spread_pct > 2.0:
            score -= 2
        elif spread_pct > 1.0:
            score -= 1

        # Fee impact score (-3 to +1 points)
        if fee_impact < 0.5:
            score += 1
        elif fee_impact > 2.0:
            score -= 3
        elif fee_impact > 1.0:
            score -= 1

        # Volatility score (-1 to +2 points)
        abs_change = abs(change_24h)
        if 1 < abs_change < 5:  # Good volatility for trading
            score += 2
        elif 5 <= abs_change < 10:
            score += 1
        elif abs_change > 15:  # Too volatile
            score -= 1

        # Price level bonus
        if 1 < price < 1000:  # Good price range
            score += 0.5

        return max(0, min(10, score))

    def get_recommendation(self, ai_score):
        """แปลง AI Score เป็นคำแนะนำ"""
        if ai_score >= 8:
            return "🚀 EXCELLENT"
        elif ai_score >= 7:
            return "✅ GOOD"
        elif ai_score >= 6:
            return "👍 OK"
        elif ai_score >= 4:
            return "⚠️ POOR"
        else:
            return "❌ AVOID"

    def analyze_all_coins(self, trade_amount=1000, max_results=10):
        """วิเคราะห์เหรียญทั้งหมด"""
        results = []

        # Use only first 20 symbols to avoid overwhelming the system
        # 🪙 รายชื่อเหรียญครบทั้งกระดาน Bitkub (อัพเดต 2024)
        # แทนที่ใน CoinRecommendationSystem → analyze_all_coins

        symbols_to_analyze = [
            # 🏆 Major Cryptocurrencies
            "THB_BTC",  # Bitcoin
            "THB_ETH",  # Ethereum
            "THB_BNB",  # Binance Coin
            "THB_ADA",  # Cardano
            "THB_XRP",  # Ripple
            "THB_SOL",  # Solana
            "THB_DOT",  # Polkadot
            "THB_AVAX",  # Avalanche
            "THB_MATIC",  # Polygon
            "THB_ATOM",  # Cosmos
            "THB_NEAR",  # Near Protocol

            # 🎮 Gaming & Metaverse
            "THB_SAND",  # The Sandbox
            "THB_MANA",  # Decentraland
            "THB_AXS",  # Axie Infinity
            "THB_GALA",  # Gala Games
            "THB_ENJ",  # Enjin Coin
            "THB_ALICE",  # My Neighbor Alice
            "THB_ILV",  # Illuvium

            # 🔗 DeFi & Infrastructure
            "THB_LINK",  # Chainlink
            "THB_UNI",  # Uniswap
            "THB_AAVE",  # Aave
            "THB_COMP",  # Compound
            "THB_MKR",  # Maker
            "THB_SNX",  # Synthetix
            "THB_LRC",  # Loopring
            "THB_1INCH",  # 1inch
            "THB_GRT",  # The Graph
            "THB_BAL",  # Balancer
            "THB_CRV",  # Curve DAO

            # 🪙 Meme & Community
            "THB_DOGE",  # Dogecoin
            "THB_SHIB",  # Shiba Inu
            "THB_PEPE",  # Pepe (ถ้ามี)

            # 💰 Stablecoins & Digital Assets
            "THB_USDT",  # Tether
            "THB_USDC",  # USD Coin
            "THB_USDS",  # USDS
            "THB_DAI",  # Dai
            "THB_BUSD",  # Binance USD (ถ้ายังมี)

            # 🔥 Layer 1 Blockchains
            "THB_LTC",  # Litecoin
            "THB_BCH",  # Bitcoin Cash
            "THB_ETC",  # Ethereum Classic
            "THB_TRX",  # Tron
            "THB_XLM",  # Stellar
            "THB_XTZ",  # Tezos
            "THB_ALGO",  # Algorand
            "THB_FLOW",  # Flow
            "THB_ICP",  # Internet Computer
            "THB_CELO",  # Celo
            "THB_QNT",  # Quant

            # 🌐 Web3 & AI
            "THB_FET",  # Fetch.ai
            "THB_OCEAN",  # Ocean Protocol
            "THB_GRT",  # The Graph
            "THB_FIL",  # Filecoin
            "THB_AR",  # Arweave

            # 🏦 Enterprise & Utility
            "THB_XDC",  # XDC Network
            "THB_VET",  # VeChain
            "THB_HBAR",  # Hedera
            "THB_IOST",  # IOST
            "THB_ONT",  # Ontology

            # ⚡ New & Trending
            "THB_APT",  # Aptos
            "THB_SUI",  # Sui
            "THB_ARB",  # Arbitrum
            "THB_OP",  # Optimism
            "THB_BLUR",  # Blur
            "THB_LDO",  # Lido DAO
            "THB_RPL",  # Rocket Pool
            "THB_FXS",  # Frax Share
            "THB_CVX",  # Convex Finance

            # 🎯 Specialized Sectors
            "THB_CHZ",  # Chiliz (Sports)
            "THB_BAT",  # Basic Attention Token
            "THB_KNC",  # Kyber Network
            "THB_ZRX",  # 0x Protocol
            "THB_STORJ",  # Storj
            "THB_REN",  # Ren Protocol

            # 🚀 High Potential Altcoins
            "THB_RNDR",  # Render Token
            "THB_IMX",  # Immutable X
            "THB_LPT",  # Livepeer
            "THB_API3",  # API3
            "THB_ANKR",  # Ankr
            "THB_CELR",  # Celer Network
            "THB_CTSI",  # Cartesi
            "THB_DYDX",  # dYdX
            "THB_ENS",  # Ethereum Name Service
            "THB_MASK",  # Mask Network

            # 🔮 Emerging Technologies
            "THB_ROSE",  # Oasis Network
            "THB_LUNA",  # Terra Luna Classic
            "THB_LUNC",  # Luna Classic
            "THB_USTC",  # TerraClassicUSD
            "THB_FTM",  # Fantom
            "THB_RUNE",  # THORChain
            "THB_KAVA",  # Kava
            "THB_BAND",  # Band Protocol
            "THB_ALPHA",  # Alpha Finance

            # 🇹🇭 Thai & Regional Projects
            "THB_KUB",  # Bitkub Coin
            "THB_SIX",  # Six Network
            "THB_JFIN",  # JFIN
            "THB_WAN",  # Wanchain

            # 📊 Additional DeFi Protocols
            "THB_YFI",  # Yearn Finance
            "THB_SUSHI",  # SushiSwap
            "THB_CAKE",  # PancakeSwap
            "THB_ALPHA",  # Alpha Homora
            "THB_CREAM",  # Cream Finance
            "THB_BADGER",  # Badger DAO

            # 🎲 Others & Utility Tokens
            "THB_HOT",  # Holo
            "THB_ICX",  # ICON
            "THB_WAN",  # Wanchain
            "THB_ZIL",  # Zilliqa
            "THB_ONT",  # Ontology
            "THB_QTUM",  # Qtum
            "THB_WAVES",  # Waves
            "THB_NANO",  # Nano
            "THB_RVN",  # Ravencoin
            "THB_DOGE",  # Dogecoin

            # 💎 Premium & High-Value
            "THB_YGG",  # Yield Guild Games
            "THB_AUDIO",  # Audius
            "THB_SPELL",  # Spell Token
            "THB_OHM",  # Olympus
            "THB_TRIBE",  # Tribe
            "THB_FEI",  # Fei Protocol

            # 🌟 Latest Additions (2024)
            "THB_PENDLE",  # Pendle
            "THB_GMX",  # GMX
            "THB_MAGIC",  # Magic
            "THB_GRAIL",  # Grail
            "THB_RDNT",  # Radiant Capital
            "THB_VELA",  # Vela Exchange
            "THB_JOE",  # TraderJoe
            "THB_PLS",  # Plutus

            # 🔄 Cross-Chain & Bridges
            "THB_POLY",  # Polymath
            "THB_REN",  # Ren
            "THB_CELR",  # Celer
            "THB_SYNAPSE",  # Synapse Protocol
            "THB_MULTICHAIN",  # Multichain

            # 🎯 Specialized Use Cases
            "THB_OCEAN",  # Ocean Protocol
            "THB_NMR",  # Numeraire
            "THB_MLN",  # Melon
            "THB_REP",  # Augur
            "THB_MTA",  # Meta
            "THB_BADGER",  # Badger DAO

            # 💫 Moonshot Potentials
            "THB_LOOKS",  # LooksRare
            "THB_X2Y2",  # X2Y2
            "THB_SUDO",  # Sudo Protocol
            "THB_BEND",  # Bend DAO
            "THB_JPEG",  # JPEG'd

            # 🔮 Experimental & New
            "THB_BONE",  # Bone ShibaSwap
            "THB_LEASH",  # Doge Killer
            "THB_BABYDOGE",  # Baby Doge
            "THB_ELON",  # Dogelon Mars
            "THB_AKITA",  # Akita Inu
        ]

        # 📊 จัดกลุ่มตาม Market Cap สำหรับการวิเคราะห์
        TIER_1_SYMBOLS = [  # Large Cap (>1B USD)
            "THB_BTC", "THB_ETH", "THB_BNB", "THB_ADA", "THB_XRP",
            "THB_SOL", "THB_DOT", "THB_AVAX", "THB_MATIC", "THB_LINK"
        ]

        TIER_2_SYMBOLS = [  # Mid Cap (100M-1B USD)
            "THB_UNI", "THB_LTC", "THB_ATOM", "THB_NEAR", "THB_AAVE",
            "THB_SAND", "THB_MANA", "THB_AXS", "THB_COMP", "THB_MKR"
        ]

        TIER_3_SYMBOLS = [  # Small Cap (<100M USD)
            "THB_DOGE", "THB_SHIB", "THB_CHZ", "THB_BAT", "THB_ENJ",
            "THB_ALPHA", "THB_KUB", "THB_SIX", "THB_JFIN"
        ]

        # 🎯 ฟังก์ชันสำหรับเลือก symbols ตามความต้องการ
        def get_symbols_by_tier(tier="all", max_count=50):
            """เลือก symbols ตาม tier"""
            if tier == "tier1":
                return TIER_1_SYMBOLS
            elif tier == "tier2":
                return TIER_2_SYMBOLS
            elif tier == "tier3":
                return TIER_3_SYMBOLS
            elif tier == "major":
                return TIER_1_SYMBOLS + TIER_2_SYMBOLS[:10]
            else:
                # ส่งกลับทั้งหมด แต่จำกัดจำนวน
                all_symbols = TIER_1_SYMBOLS + TIER_2_SYMBOLS + TIER_3_SYMBOLS
                return all_symbols[:max_count]

        # 🚀 วิธีใช้งานใน analyze_all_coins:
        def analyze_all_coins_complete(self, trade_amount=1000, max_results=20, tier="major"):
            """วิเคราะห์เหรียญแบบครบ พร้อมเลือก tier"""

            # เลือก symbols ตาม tier
            symbols_to_analyze = get_symbols_by_tier(tier, 50)

            print(f"Analyzing {len(symbols_to_analyze)} coins from {tier} tier...")

            results = []

            # วิเคราะห์แบบ batch เพื่อประสิทธิภาพ
            for i, symbol in enumerate(symbols_to_analyze):
                try:
                    print(f"Progress: {i + 1}/{len(symbols_to_analyze)} - {symbol}")

                    analysis = self.analyze_single_coin(symbol, trade_amount)
                    if analysis and analysis['ai_score'] > 0:
                        results.append(analysis)

                    # Rate limiting
                    if i % 10 == 0:
                        time.sleep(1)  # หยุด 1 วินาทีทุก 10 เหรียญ

                except Exception as e:
                    print(f"Error analyzing {symbol}: {e}")
                    continue

            # เรียงตาม AI Score
            results.sort(key=lambda x: x['ai_score'], reverse=True)

            return results[:max_results]

        # 🔧 การใช้งานใน UI:
        """
        ใน analyze_all_coins() เปลี่ยนจาก:
        symbols_to_analyze = self.api_client.all_bitkub_symbols[:20]

        เป็น:
        symbols_to_analyze = get_symbols_by_tier("major", 30)  # 30 เหรียญหลัก

        หรือ:
        symbols_to_analyze = get_symbols_by_tier("all", 100)   # ทั้งหมด 100 เหรียญ
        """
        # ใช้ ThreadPoolExecutor สำหรับ parallel processing
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {
                executor.submit(self.analyze_single_coin, symbol, trade_amount): symbol
                for symbol in symbols_to_analyze
            }

            for future in as_completed(futures):
                try:
                    analysis = future.result(timeout=10)
                    if analysis and analysis['ai_score'] > 0:
                        results.append(analysis)
                except Exception as e:
                    print(f"Analysis error for {futures[future]}: {e}")

        # เรียงตาม AI Score
        results.sort(key=lambda x: x['ai_score'], reverse=True)

        return results[:max_results]

    def get_best_coin(self, trade_amount=1000):
        """หาเหรียญที่ดีที่สุด"""
        if time.time() - self.last_analysis_time < 60:  # Cache 1 minute
            if hasattr(self, 'cached_best'):
                return self.cached_best

        analysis = self.analyze_all_coins(trade_amount, 5)
        if analysis:
            best = analysis[0]
            self.cached_best = best
            self.last_analysis_time = time.time()
            return best
        return None


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
            "coin_analysis": {
                "primary": "#ff6600",
                "secondary": "#cc4400",
                "accent": "#ff9966",
                "glow": "#ff7733"
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
            particle['phase'] += 0.05

            # Bounce off edges
            if particle['x'] <= 10 or particle['x'] >= self.width - 10:
                particle['dx'] *= -1
            if particle['y'] <= 10 or particle['y'] >= self.width - 10:
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
        pulse = math.sin(self.pulse_phase) * 0.3 + 1.0
        core_size = int(15 * pulse)

        # Outer glow
        for i in range(3):
            glow_size = core_size + i * 8
            alpha = 0.6 - i * 0.2
            intensity = int(alpha * 255)
            glow_color = f"#{intensity // 4:02x}{intensity // 4:02x}{intensity:02x}"

            self.canvas.create_oval(
                self.center_x - glow_size, self.center_y - glow_size,
                self.center_x + glow_size, self.center_y + glow_size,
                fill=glow_color, outline="",
                tags="energy_core"
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
        self.draw_hud_rings(theme, 60)
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
        self.draw_hud_rings(theme, 70)
        self.draw_energy_core(theme)

        # Connecting animation
        for i in range(8):
            angle = (self.frame_count * 5 + i * 45) % 360
            x = self.center_x + 40 * math.cos(math.radians(angle))
            y = self.center_y + 40 * math.sin(math.radians(angle))

            self.canvas.create_oval(
                x - 3, y - 3, x + 3, y + 3,
                fill=theme["accent"], outline="",
                tags="connect_dots"
            )

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

        # Analysis wave
        wave_y = self.center_y + math.sin(self.wave_phase) * 20
        for x in range(0, self.width, 5):
            wave_offset = math.sin(self.wave_phase + x * 0.02) * 10
            y = wave_y + wave_offset

            self.canvas.create_oval(
                x - 1, y - 1, x + 1, y + 1,
                fill=theme["accent"], outline="",
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
        self.draw_hud_rings(theme, 85)
        self.draw_energy_core(theme)

        # Coin analysis scanner
        for i in range(6):
            angle = (self.frame_count * 3 + i * 60) % 360
            radius = 50 + (i % 2) * 20
            x = self.center_x + radius * math.cos(math.radians(angle))
            y = self.center_y + radius * math.sin(math.radians(angle))

            size = 4 + math.sin(self.pulse_phase + i) * 2
            self.canvas.create_oval(
                x - size, y - size, x + size, y + size,
                fill=theme["accent"], outline=theme["primary"], width=1,
                tags="coin_scanner"
            )

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
        self.draw_hud_rings(theme, 100)
        self.draw_energy_core(theme, True)

        # Buy signal arrows
        for i in range(4):
            angle = i * 90 + self.rotation_angle
            start_radius = 60
            end_radius = 80

            start_x = self.center_x + start_radius * math.cos(math.radians(angle))
            start_y = self.center_y + start_radius * math.sin(math.radians(angle))
            end_x = self.center_x + end_radius * math.cos(math.radians(angle))
            end_y = self.center_y + end_radius * math.sin(math.radians(angle))

            self.canvas.create_line(
                start_x, start_y, end_x, end_y,
                fill=theme["primary"], width=4, arrow="last",
                tags="buy_arrows"
            )

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


class ImprovedBitkubAPI:
    """Enhanced Bitkub API Client with REAL TRADING capabilities"""

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

        # Complete list of all Bitkub supported coins (ใช้รูปแบบ trading format)
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
            "THB_USDC": "usdc_thb", "THB_USDS": "usds_thb", "THB_ALPHA": "alpha_thb",
            "THB_CHZ": "chz_thb", "THB_BAT": "bat_thb", "THB_COMP": "comp_thb",
            "THB_KNC": "knc_thb", "THB_CVC": "cvc_thb", "THB_POW": "pow_thb"
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

    def get_orderbook(self, symbol, limit=5):
        """Get orderbook data with improved error handling"""
        try:
            self._wait_for_rate_limit()

            # Try multiple endpoints for orderbook
            endpoints = [
                f"{self.base_url}/api/market/books?sym={symbol}&lmt={limit}",
                f"{self.base_url}/api/v3/market/books?sym={symbol}&lmt={limit}",
                f"{self.base_url}/api/market/depth?symbol={symbol}&limit={limit}"
            ]

            for endpoint in endpoints:
                try:
                    response = requests.get(endpoint, timeout=10)
                    data = response.json()

                    # Handle different response formats
                    if isinstance(data, dict):
                        # Format 1: Direct result
                        if 'result' in data:
                            return data['result']
                        # Format 2: Direct data
                        elif 'bids' in data and 'asks' in data:
                            return data
                        # Format 3: Error response
                        elif 'error' in data:
                            continue

                except requests.exceptions.RequestException:
                    continue
                except Exception:
                    continue

            # Mock orderbook for testing
            return {
                'bids': [['999000', '0.1'], ['998000', '0.2']],
                'asks': [['1001000', '0.1'], ['1002000', '0.2']]
            }

        except Exception as e:
            print(f"Error getting orderbook for {symbol}: {e}")
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
        """🔥 PLACE REAL BUY ORDER - ใช้เงินจริง!"""
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
            print(f"🔥 REAL BUY ORDER - Symbol: {trading_symbol}, Amount: {amount_thb}, Price: {buy_price}")
            print(f"API Response: {result}")

            return result

        except Exception as e:
            return {"error": 999, "message": f"Request failed: {e}"}

    def place_sell_order_safe(self, symbol, amount_crypto, sell_price, order_type="limit"):
        """🔥 PLACE REAL SELL ORDER - ใช้เงินจริง!"""
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

            print(f"🔥 REAL SELL ORDER - Symbol: {trading_symbol}, Amount: {amount_crypto}, Price: {sell_price}")
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
    """🔥 ENHANCED TRADING BOT WITH REAL MONEY TRADING CAPABILITY"""

    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("🔥 REAL TRADING BOT - SciFi Enhanced with Coin Recommendation")
        self.root.geometry("1400x900")

        # Core components
        self.api_client = None
        self.strategy = None
        self.coin_recommender = None
        self.scifi_visual = None

        # Trading state
        self.is_trading = False
        self.is_paper_trading = True
        self.emergency_stop = False
        self.daily_trades = 0
        self.daily_pnl = 0.0
        self.total_fees_paid = 0.0
        self.last_trade_time = None

        # Database
        self.db_path = "real_trading_bot.db"
        self.init_database()

        # Config - ใช้ trading format เลย
        self.config = {
            'symbol': 'btc_thb',  # Trading format
            'trade_amount_thb': 1000,
            'max_daily_trades': 3,
            'max_daily_loss': 500,
            'use_coin_recommendation': False
        }

        self.setup_ui()

    def init_database(self):
        """Initialize SQLite database"""
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

    def setup_ui(self):
        """Setup enhanced user interface"""
        # 🔥 DANGER WARNING BANNER
        warning_frame = ctk.CTkFrame(self.root, fg_color="red", height=60)
        warning_frame.pack(fill="x", padx=10, pady=5)
        warning_frame.pack_propagate(False)

        warning_text = "🔥 REAL TRADING CAPABLE BOT - CAN USE ACTUAL MONEY! 🔥\n⚠️ START WITH PAPER TRADING - UNDERSTAND RISKS BEFORE REAL TRADING ⚠️"
        ctk.CTkLabel(warning_frame, text=warning_text,
                     font=("Arial", 14, "bold"),
                     text_color="white").pack(expand=True)

        # Tabs
        self.tabview = ctk.CTkTabview(self.root)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_dashboard = self.tabview.add("📊 Dashboard")
        self.tab_coins = self.tabview.add("🪙 Coin Analysis")
        self.tab_trading = self.tabview.add("🔥 REAL Trading")  # Emphasize real trading
        self.tab_strategies = self.tabview.add("🎯 Strategies")
        self.tab_api = self.tabview.add("🔌 API Config")
        self.tab_testing = self.tabview.add("🧪 Testing")
        self.tab_history = self.tabview.add("📜 History")
        self.tab_settings = self.tabview.add("⚙️ Settings")

        self.setup_dashboard_tab()
        self.setup_coin_analysis_tab()
        self.setup_trading_tab()
        self.setup_strategies_tab()
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

            ctk.CTkLabel(card, text=label, font=("Arial", 10)).pack()
            self.status_cards[label] = ctk.CTkLabel(
                card, text=value, font=("Arial", 12, "bold"), text_color=color
            )
            self.status_cards[label].pack()

        # Configure grid weights
        for i in range(4):
            stats_frame.grid_columnconfigure(i, weight=1)

        # Control buttons
        controls_frame = ctk.CTkFrame(left_frame)
        controls_frame.pack(fill="x", padx=10, pady=10)

        self.start_btn = ctk.CTkButton(
            controls_frame, text="🔥 Start REAL Trading Bot",
            command=self.toggle_trading,
            fg_color="red", height=50, width=250,
            font=("Arial", 14, "bold")
        )
        self.start_btn.pack(side="left", padx=5)

        ctk.CTkButton(
            controls_frame, text="🔗 Test Connection",
            command=self.test_connection,
            height=50, width=150
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            controls_frame, text="📊 Analyze Best Coin",
            command=self.analyze_best_coin,
            fg_color="purple", height=50, width=150
        ).pack(side="left", padx=5)

        # Trading mode toggle
        mode_frame = ctk.CTkFrame(left_frame)
        mode_frame.pack(fill="x", padx=10, pady=5)

        self.paper_trading_var = ctk.BooleanVar(value=True)
        self.paper_trading_switch = ctk.CTkSwitch(
            mode_frame, text="📝 Paper Trading Mode (SAFE)",
            variable=self.paper_trading_var,
            command=self.toggle_paper_trading
        )
        self.paper_trading_switch.pack(side="left", padx=10)

        # Real trading warning switch
        self.real_trading_var = ctk.BooleanVar(value=False)
        self.real_trading_switch = ctk.CTkSwitch(
            mode_frame, text="🔥 REAL TRADING (DANGER!)",
            variable=self.real_trading_var,
            command=self.toggle_real_trading,
            button_color="red",
            progress_color="darkred"
        )
        self.real_trading_switch.pack(side="left", padx=10)

        # Coin recommendation toggle
        self.coin_rec_var = ctk.BooleanVar(value=False)
        self.coin_rec_switch = ctk.CTkSwitch(
            mode_frame, text="🪙 Auto Coin Selection",
            variable=self.coin_rec_var,
            command=self.toggle_coin_recommendation
        )
        self.coin_rec_switch.pack(side="left", padx=10)

        # Log display
        log_frame = ctk.CTkFrame(left_frame)
        log_frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(log_frame, text="📋 Trading Log", font=("Arial", 14, "bold")).pack()

        self.log_display = ctk.CTkTextbox(log_frame, height=200)
        self.log_display.pack(fill="both", expand=True, padx=10, pady=10)

        # Right side - Sci-Fi Visual System
        right_frame = ctk.CTkFrame(content_frame, width=300)
        right_frame.pack(side="right", fill="y", padx=(10, 0))
        right_frame.pack_propagate(False)

        ctk.CTkLabel(right_frame, text="🎬 Sci-Fi Visual System",
                     font=("Arial", 16, "bold")).pack(pady=10)

        # Initialize Sci-Fi Visual System
        visual_frame = ctk.CTkFrame(right_frame)
        visual_frame.pack(padx=10, pady=10)

        self.scifi_visual = SciFiVisualSystem(visual_frame)

        # Visual status display
        status_frame = ctk.CTkFrame(right_frame)
        status_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(status_frame, text="System Status:", font=("Arial", 12, "bold")).pack()
        self.visual_status_label = ctk.CTkLabel(status_frame, text="IDLE", font=("Orbitron", 11))
        self.visual_status_label.pack()

        # Current coin display
        coin_frame = ctk.CTkFrame(right_frame)
        coin_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(coin_frame, text="Current Coin:", font=("Arial", 12, "bold")).pack()
        self.current_coin_label = ctk.CTkLabel(coin_frame, text="BTC/THB", font=("Arial", 11))
        self.current_coin_label.pack()

        # Recommended coin display
        rec_frame = ctk.CTkFrame(right_frame)
        rec_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(rec_frame, text="Recommended:", font=("Arial", 12, "bold")).pack()
        self.recommended_coin_label = ctk.CTkLabel(rec_frame, text="Analyzing...", font=("Arial", 11))
        self.recommended_coin_label.pack()

    def setup_coin_analysis_tab(self):
        """Setup coin analysis tab"""
        main_frame = ctk.CTkFrame(self.tab_coins)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Title
        ctk.CTkLabel(main_frame, text="🪙 Coin Analysis & Recommendation System",
                     font=("Arial", 18, "bold")).pack(pady=10)

        # Control buttons
        controls_frame = ctk.CTkFrame(main_frame)
        controls_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkButton(
            controls_frame, text="🔍 Analyze All Coins",
            command=self.analyze_all_coins,
            fg_color="blue", height=40, width=150
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            controls_frame, text="🏆 Get Best Coin",
            command=self.get_best_coin,
            fg_color="green", height=40, width=150
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            controls_frame, text="🔄 Refresh Analysis",
            command=self.refresh_coin_analysis,
            fg_color="orange", height=40, width=150
        ).pack(side="left", padx=5)

        # Trade amount input
        amount_frame = ctk.CTkFrame(controls_frame)
        amount_frame.pack(side="right", padx=5)

        ctk.CTkLabel(amount_frame, text="Trade Amount (THB):").pack(side="left", padx=5)
        self.analysis_amount_var = ctk.StringVar(value="1000")
        ctk.CTkEntry(amount_frame, textvariable=self.analysis_amount_var, width=100).pack(side="left", padx=5)

        # Results display
        results_frame = ctk.CTkFrame(main_frame)
        results_frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(results_frame, text="📊 Analysis Results", font=("Arial", 14, "bold")).pack()

        self.coin_analysis_display = ctk.CTkTextbox(results_frame, height=400)
        self.coin_analysis_display.pack(fill="both", expand=True, padx=10, pady=10)

        # Initial message
        self.coin_analysis_display.insert("1.0",
                                          "🪙 COIN RECOMMENDATION SYSTEM\n\n"
                                          "📋 FEATURES:\n"
                                          "• AI-powered coin scoring (0-10)\n"
                                          "• Volume & liquidity analysis\n"
                                          "• Fee impact calculation\n"
                                          "• Volatility assessment\n"
                                          "• Real-time recommendations\n\n"
                                          "🚀 Click 'Analyze All Coins' to start analysis!\n\n"
                                          "📊 SCORING CRITERIA:\n"
                                          "• Volume (0-3 points)\n"
                                          "• Spread (0-1 points) \n"
                                          "• Fee Impact (0-1 points)\n"
                                          "• Volatility (0-2 points)\n"
                                          "• Price Level (0-0.5 points)\n\n"
                                          "🎯 RECOMMENDATIONS:\n"
                                          "• 8-10: 🚀 EXCELLENT\n"
                                          "• 7-8: ✅ GOOD\n"
                                          "• 6-7: 👍 OK\n"
                                          "• 4-6: ⚠️ POOR\n"
                                          "• 0-4: ❌ AVOID"
                                          )

    def setup_trading_tab(self):
        """🔥 Setup REAL TRADING tab"""
        main_frame = ctk.CTkFrame(self.tab_trading)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # 🔥 DANGER WARNING
        danger_frame = ctk.CTkFrame(main_frame, fg_color="darkred", height=60)
        danger_frame.pack(fill="x", padx=10, pady=10)
        danger_frame.pack_propagate(False)

        danger_text = "🔥 REAL MONEY TRADING ZONE 🔥\nCAUTION: ORDERS PLACED HERE USE ACTUAL FUNDS!"
        ctk.CTkLabel(danger_frame, text=danger_text,
                     font=("Arial", 14, "bold"),
                     text_color="white").pack(expand=True)

        # Trading mode status
        mode_frame = ctk.CTkFrame(main_frame)
        mode_frame.pack(fill="x", padx=10, pady=10)

        self.trading_mode_label = ctk.CTkLabel(
            mode_frame, text="📝 PAPER TRADING MODE ACTIVE (SAFE)",
            font=("Arial", 16, "bold"), text_color="green"
        )
        self.trading_mode_label.pack(pady=10)

        # Manual trading controls
        manual_frame = ctk.CTkFrame(main_frame)
        manual_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(manual_frame, text="🎯 Manual Trading Controls",
                     font=("Arial", 14, "bold")).pack()

        buttons_frame = ctk.CTkFrame(manual_frame)
        buttons_frame.pack(pady=10)

        self.manual_buy_btn = ctk.CTkButton(
            buttons_frame, text="💰 Manual Buy",
            command=self.manual_buy,
            fg_color="green", height=50, width=150,
            font=("Arial", 12, "bold")
        )
        self.manual_buy_btn.pack(side="left", padx=5)

        self.manual_sell_btn = ctk.CTkButton(
            buttons_frame, text="💸 Manual Sell",
            command=self.manual_sell,
            fg_color="red", height=50, width=150,
            font=("Arial", 12, "bold")
        )
        self.manual_sell_btn.pack(side="left", padx=5)

        ctk.CTkButton(
            buttons_frame, text="⏹️ Emergency Stop",
            command=self.emergency_stop_trading,
            fg_color="darkred", height=50, width=150,
            font=("Arial", 12, "bold")
        ).pack(side="left", padx=5)

        # Position info
        position_frame = ctk.CTkFrame(main_frame)
        position_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(position_frame, text="📊 Current Position",
                     font=("Arial", 14, "bold")).pack()

        self.position_display = ctk.CTkTextbox(position_frame, height=120)
        self.position_display.pack(fill="x", padx=10, pady=10)

        # Auto trading controls
        auto_frame = ctk.CTkFrame(main_frame)
        auto_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(auto_frame, text="🤖 Automated Trading",
                     font=("Arial", 14, "bold")).pack()

        self.start_btn_trading = ctk.CTkButton(
            auto_frame, text="🔥 Start REAL Trading Bot",
            command=self.toggle_trading,
            fg_color="red", height=60, width=350,
            font=("Arial", 16, "bold")
        )
        self.start_btn_trading.pack(pady=15)

        # Trading info display
        info_frame = ctk.CTkFrame(main_frame)
        info_frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(info_frame, text="📈 Trading Information",
                     font=("Arial", 14, "bold")).pack()

        self.trading_info_display = ctk.CTkTextbox(info_frame, height=200)
        self.trading_info_display.pack(fill="both", expand=True, padx=10, pady=10)

        # Initialize with trading info
        self.update_trading_info_display()

    def setup_strategies_tab(self):
        """Setup strategies configuration tab"""
        main_frame = ctk.CTkFrame(self.tab_strategies)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(main_frame, text="🎯 Trading Strategies Configuration",
                     font=("Arial", 18, "bold")).pack(pady=10)

        # Strategy selection
        strategy_frame = ctk.CTkFrame(main_frame)
        strategy_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(strategy_frame, text="📋 Available Strategies:",
                     font=("Arial", 14, "bold")).pack(anchor="w", padx=10)

        # Initialize strategy variables
        self.strategy_vars = {}
        strategies = [
            ("RSI + Volume", "Enhanced RSI with volume momentum analysis"),
            ("Bollinger Bands", "Support and resistance trading"),
            ("EMA Crossover", "Moving average trend following"),
            ("MACD Divergence", "Advanced momentum analysis"),
            ("Volume Breakout", "Volume spike detection"),
            ("Scalping", "High-frequency quick profits"),
            ("Swing Trading", "Medium-term trend following"),
            ("DCA", "Dollar Cost Averaging")
        ]

        for strategy, description in strategies:
            strategy_row = ctk.CTkFrame(strategy_frame)
            strategy_row.pack(fill="x", padx=10, pady=2)

            self.strategy_vars[strategy] = ctk.BooleanVar(value=(strategy == "RSI + Volume"))
            checkbox = ctk.CTkCheckBox(strategy_row,
                                       text=f"{strategy}: {description}",
                                       variable=self.strategy_vars[strategy])
            checkbox.pack(anchor="w", padx=10, pady=5)

        # Strategy parameters
        params_frame = ctk.CTkFrame(main_frame)
        params_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(params_frame, text="⚙️ Strategy Parameters:",
                     font=("Arial", 14, "bold")).pack(anchor="w", padx=10)

        # RSI Parameters
        rsi_frame = ctk.CTkFrame(params_frame)
        rsi_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(rsi_frame, text="RSI Settings:").pack(side="left", padx=5)
        ctk.CTkLabel(rsi_frame, text="Oversold:").pack(side="left", padx=5)
        self.rsi_oversold_var = ctk.StringVar(value="25")
        ctk.CTkEntry(rsi_frame, textvariable=self.rsi_oversold_var, width=60).pack(side="left", padx=2)

        ctk.CTkLabel(rsi_frame, text="Overbought:").pack(side="left", padx=5)
        self.rsi_overbought_var = ctk.StringVar(value="75")
        ctk.CTkEntry(rsi_frame, textvariable=self.rsi_overbought_var, width=60).pack(side="left", padx=2)

        # Risk Management
        risk_frame = ctk.CTkFrame(params_frame)
        risk_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(risk_frame, text="Stop Loss %:").pack(side="left", padx=5)
        self.stop_loss_var = ctk.StringVar(value="1.5")
        ctk.CTkEntry(risk_frame, textvariable=self.stop_loss_var, width=60).pack(side="left", padx=2)

        ctk.CTkLabel(risk_frame, text="Take Profit %:").pack(side="left", padx=5)
        self.take_profit_var = ctk.StringVar(value="2.5")
        ctk.CTkEntry(risk_frame, textvariable=self.take_profit_var, width=60).pack(side="left", padx=2)

        # Auto configuration buttons
        auto_frame = ctk.CTkFrame(main_frame)
        auto_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkButton(auto_frame, text="🔄 Auto Configure",
                      command=self.auto_configure_strategies,
                      fg_color="blue", height=40, width=200).pack(side="left", padx=5)

        ctk.CTkButton(auto_frame, text="💾 Save Settings",
                      command=self.save_strategy_settings,
                      fg_color="green", height=40, width=200).pack(side="left", padx=5)

        # Strategy display
        self.strategies_display = ctk.CTkTextbox(main_frame, height=200)
        self.strategies_display.pack(fill="both", expand=True, padx=10, pady=10)

        self.strategies_display.insert("1.0", "🎯 Configure your trading strategies above")

    def setup_api_tab(self):
        """Setup API configuration tab"""
        main_frame = ctk.CTkFrame(self.tab_api)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # 🔥 API Warning
        api_warning_frame = ctk.CTkFrame(main_frame, fg_color="darkred", height=80)
        api_warning_frame.pack(fill="x", padx=10, pady=10)
        api_warning_frame.pack_propagate(False)

        warning_text = "🔥 REAL TRADING API CONFIGURATION 🔥\n" \
                       "⚠️ These credentials will be used for REAL money transactions!\n" \
                       "🔒 Ensure API key has only necessary permissions (trading, wallet)"
        ctk.CTkLabel(api_warning_frame, text=warning_text,
                     font=("Arial", 12, "bold"),
                     text_color="white").pack(expand=True)

        ctk.CTkLabel(main_frame, text="🔌 Bitkub API Configuration",
                     font=("Arial", 18, "bold")).pack(pady=10)

        # API credentials
        creds_frame = ctk.CTkFrame(main_frame)
        creds_frame.pack(fill="x", padx=10, pady=10)

        # Security notes
        security_frame = ctk.CTkFrame(creds_frame, fg_color="orange")
        security_frame.pack(fill="x", padx=10, pady=5)

        security_text = "🔒 SECURITY CHECKLIST:\n" \
                        "✅ IP whitelist enabled on Bitkub\n" \
                        "✅ API key has limited permissions (trading only)\n" \
                        "✅ 2FA enabled on Bitkub account\n" \
                        "✅ Using dedicated trading account with limited funds"
        ctk.CTkLabel(security_frame, text=security_text,
                     font=("Arial", 10), justify="left").pack(padx=10, pady=10)

        ctk.CTkLabel(creds_frame, text="API Key:", font=("Arial", 12, "bold")).pack(anchor="w", padx=10)
        self.api_key_entry = ctk.CTkEntry(creds_frame, width=500, show="*")
        self.api_key_entry.pack(padx=10, pady=5)

        ctk.CTkLabel(creds_frame, text="API Secret:", font=("Arial", 12, "bold")).pack(anchor="w", padx=10)
        self.api_secret_entry = ctk.CTkEntry(creds_frame, width=500, show="*")
        self.api_secret_entry.pack(padx=10, pady=5)

        # Connect buttons
        connect_frame = ctk.CTkFrame(creds_frame)
        connect_frame.pack(pady=20)

        ctk.CTkButton(
            connect_frame, text="🔗 Connect & Test API",
            command=self.connect_api,
            fg_color="blue", height=50, width=200,
            font=("Arial", 14, "bold")
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            connect_frame, text="🏥 System Health Check",
            command=self.system_health_check,
            fg_color="green", height=50, width=200
        ).pack(side="left", padx=5)

        # API status display
        status_frame = ctk.CTkFrame(main_frame)
        status_frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(status_frame, text="📊 API Status & Information", font=("Arial", 14, "bold")).pack()

        self.api_status_display = ctk.CTkTextbox(status_frame, height=400)
        self.api_status_display.pack(fill="both", expand=True, padx=10, pady=10)

        # Initial API information
        self.api_status_display.insert("1.0",
                                       "🔌 BITKUB API CONFIGURATION\n\n"
                                       "📋 SETUP INSTRUCTIONS:\n"
                                       "1. Login to your Bitkub account\n"
                                       "2. Go to API Management section\n"
                                       "3. Create new API key with permissions:\n"
                                       "   • View account info\n"
                                       "   • Place orders\n"
                                       "   • Cancel orders\n"
                                       "   • View open orders\n"
                                       "4. Enable IP whitelist for security\n"
                                       "5. Copy API Key and Secret here\n\n"
                                       "🔒 SECURITY BEST PRACTICES:\n"
                                       "• Use separate trading account\n"
                                       "• Limit funds to what you can afford to lose\n"
                                       "• Never share your API credentials\n"
                                       "• Monitor all trading activity\n"
                                       "• Start with small amounts\n\n"
                                       "⚠️ DISCLAIMER:\n"
                                       "This bot will place REAL orders using your API credentials.\n"
                                       "You are fully responsible for all trading activities.\n"
                                       "Always start with paper trading to test strategies!"
                                       )

    def setup_testing_tab(self):
        """Setup testing tab"""
        main_frame = ctk.CTkFrame(self.tab_testing)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(main_frame, text="🧪 Testing & Debugging",
                     font=("Arial", 18, "bold")).pack(pady=10)

        # Test buttons
        test_frame = ctk.CTkFrame(main_frame)
        test_frame.pack(fill="x", padx=10, pady=10)

        buttons = [
            ("🔍 Test Market Data", self.test_market_data),
            ("💰 Test Balance Check", self.test_balance_check),
            ("📋 Test Open Orders", self.test_open_orders),
            ("🎨 Test Sci-Fi Visuals", self.test_scifi_visuals),
            ("💸 Test Fee Calculation", self.test_fee_calculation),
            ("🪙 Test Coin Analysis", self.test_coin_analysis),
            ("🔥 Test Real Order (CAREFUL!)", self.test_real_order_simulation),
            ("📊 Test Trading Signals", self.test_trading_signals)
        ]

        for i, (text, command) in enumerate(buttons):
            row = i // 2
            col = i % 2

            btn_frame = ctk.CTkFrame(test_frame)
            btn_frame.grid(row=row, column=col, padx=5, pady=5, sticky="ew")

            ctk.CTkButton(
                btn_frame, text=text, command=command,
                height=40, width=250
            ).pack(pady=5)

        test_frame.grid_columnconfigure(0, weight=1)
        test_frame.grid_columnconfigure(1, weight=1)

        # Test results
        results_frame = ctk.CTkFrame(main_frame)
        results_frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(results_frame, text="📋 Test Results", font=("Arial", 14, "bold")).pack()

        self.test_results_display = ctk.CTkTextbox(results_frame, height=400)
        self.test_results_display.pack(fill="both", expand=True, padx=10, pady=10)

    def setup_history_tab(self):
        """Setup history tab"""
        main_frame = ctk.CTkFrame(self.tab_history)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(main_frame, text="📜 Trading History & Statistics",
                     font=("Arial", 18, "bold")).pack(pady=10)

        # Controls
        controls_frame = ctk.CTkFrame(main_frame)
        controls_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkButton(
            controls_frame, text="🔄 Refresh History",
            command=self.load_trade_history,
            height=40, width=150
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            controls_frame, text="📊 Show Statistics",
            command=self.show_statistics,
            height=40, width=150
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            controls_frame, text="💸 Fee Analysis",
            command=self.show_fee_analysis,
            height=40, width=150
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            controls_frame, text="🗑️ Clear History",
            command=self.clear_history,
            fg_color="red", height=40, width=150
        ).pack(side="left", padx=5)

        # History display
        history_frame = ctk.CTkFrame(main_frame)
        history_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.history_display = ctk.CTkTextbox(history_frame, height=400)
        self.history_display.pack(fill="both", expand=True, padx=10, pady=10)

    def setup_settings_tab(self):
        """Setup settings tab"""
        main_frame = ctk.CTkFrame(self.tab_settings)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(main_frame, text="⚙️ Trading Settings",
                     font=("Arial", 18, "bold")).pack(pady=10)

        # Trading settings
        trading_frame = ctk.CTkFrame(main_frame)
        trading_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(trading_frame, text="💹 Basic Trading Settings",
                     font=("Arial", 14, "bold")).pack()

        # Symbol selection
        symbol_frame = ctk.CTkFrame(trading_frame)
        symbol_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(symbol_frame, text="Trading Pair:").pack(side="left", padx=5)
        self.symbol_var = ctk.StringVar(value=self.config['symbol'])

        # Popular trading pairs (ใช้ trading format)
        popular_symbols = [
            'btc_thb', 'eth_thb', 'ada_thb', 'xrp_thb', 'bnb_thb', 'doge_thb',
            'sol_thb', 'avax_thb', 'dot_thb', 'matic_thb', 'atom_thb', 'near_thb',
            'link_thb', 'uni_thb', 'ltc_thb', 'bch_thb', 'sand_thb', 'mana_thb',
            'shib_thb', 'usdt_thb', 'usdc_thb'
        ]

        symbol_menu = ctk.CTkOptionMenu(
            symbol_frame,
            variable=self.symbol_var,
            values=popular_symbols,
            width=150
        )
        symbol_menu.pack(side="left", padx=5)

        # Trade amount
        amount_frame = ctk.CTkFrame(trading_frame)
        amount_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(amount_frame, text="Trade Amount (THB):").pack(side="left", padx=5)
        self.amount_var = ctk.StringVar(value=str(self.config['trade_amount_thb']))
        ctk.CTkEntry(amount_frame, textvariable=self.amount_var, width=150).pack(side="left", padx=5)

        # Risk limits
        risk_frame = ctk.CTkFrame(trading_frame)
        risk_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(risk_frame, text="Max Daily Trades:").pack(side="left", padx=5)
        self.max_trades_var = ctk.StringVar(value=str(self.config['max_daily_trades']))
        ctk.CTkEntry(risk_frame, textvariable=self.max_trades_var, width=100).pack(side="left", padx=5)

        ctk.CTkLabel(risk_frame, text="Max Daily Loss (THB):").pack(side="left", padx=20)
        self.max_loss_var = ctk.StringVar(value=str(self.config['max_daily_loss']))
        ctk.CTkEntry(risk_frame, textvariable=self.max_loss_var, width=150).pack(side="left", padx=5)

        # Save button
        ctk.CTkButton(
            trading_frame, text="💾 Save Settings",
            command=self.save_settings,
            fg_color="green", height=40, width=150
        ).pack(pady=20)

        # Real trading warnings
        warning_frame = ctk.CTkFrame(main_frame, fg_color="darkred")
        warning_frame.pack(fill="x", padx=10, pady=10)

        warning_text = "🔥 REAL TRADING WARNINGS 🔥\n" \
                       "• Start with small amounts (100-500 THB)\n" \
                       "• Test all strategies in paper mode first\n" \
                       "• Monitor your positions actively\n" \
                       "• Never risk more than you can afford to lose\n" \
                       "• Set conservative stop losses\n" \
                       "• Use proper position sizing"
        ctk.CTkLabel(warning_frame, text=warning_text,
                     font=("Arial", 12, "bold"),
                     text_color="white", justify="left").pack(padx=20, pady=15)

    # === Core Trading Functions ===

    def connect_api(self):
        """🔥 Connect to Bitkub API for REAL trading"""
        api_key = self.api_key_entry.get().strip()
        api_secret = self.api_secret_entry.get().strip()

        if not api_key or not api_secret:
            messagebox.showwarning("Error", "Please enter both API key and secret")
            return

        # 🔥 REAL TRADING WARNING
        if not messagebox.askyesno("🔥 REAL TRADING API CONNECTION",
                                   "You are connecting to REAL trading API!\n\n"
                                   "This will enable REAL money transactions.\n"
                                   "Have you:\n"
                                   "✅ Tested with paper trading?\n"
                                   "✅ Set up IP whitelist?\n"
                                   "✅ Limited API permissions?\n"
                                   "✅ Using small test amounts?\n\n"
                                   "Connect to REAL trading API?"):
            return

        self.api_client = ImprovedBitkubAPI(api_key, api_secret)
        self.strategy = ProfitableTradingStrategy(self.api_client)
        self.coin_recommender = CoinRecommendationSystem(self.api_client)

        self.update_scifi_visual_state("connecting", "Connecting to REAL API")

        def test_connection():
            balance = self.api_client.check_balance()
            if balance and balance.get('error') == 0:
                try:
                    thb_balance = balance['result'].get('THB', 0)
                    if isinstance(thb_balance, dict):
                        thb_value = thb_balance.get('available', 0)
                    else:
                        thb_value = thb_balance
                    thb_float = float(thb_value) if thb_value else 0.0

                    self.log(f"🔥 REAL API Connected! Balance: {thb_float:,.2f} THB")
                    self.status_cards["System Status"].configure(text="REAL API", text_color="red")
                    self.status_cards["Balance THB"].configure(text=f"{thb_float:,.2f}")
                    self.update_scifi_visual_state("success", "REAL API Connected")

                    # Show balance warning
                    if thb_float > 10000:
                        messagebox.showwarning("High Balance Warning",
                                               f"Your balance is {thb_float:,.2f} THB\n\n"
                                               "Consider:\n"
                                               "• Starting with smaller amounts\n"
                                               "• Using paper trading first\n"
                                               "• Setting conservative limits")

                    threading.Timer(2.0, lambda: self.update_scifi_visual_state("idle")).start()

                except Exception as e:
                    self.log(f"🔥 REAL API Connected! Balance format unknown")
                    self.status_cards["System Status"].configure(text="REAL API", text_color="red")
                    self.update_scifi_visual_state("success", "REAL API Connected")
                    threading.Timer(2.0, lambda: self.update_scifi_visual_state("idle")).start()
            else:
                error_msg = "Unknown error"
                if balance:
                    error_code = balance.get("error", 999)
                    error_msg = self.api_client.error_codes.get(error_code, f"Error {error_code}")

                self.update_scifi_visual_state("error", f"Connection failed: {error_msg}")
                self.log(f"❌ REAL API Connection failed: {error_msg}")
                messagebox.showerror("Error", f"Failed to connect: {error_msg}")
                self.status_cards["System Status"].configure(text="Failed", text_color="red")

        threading.Thread(target=test_connection, daemon=True).start()

    def toggle_paper_trading(self):
        """Toggle paper trading mode"""
        self.is_paper_trading = self.paper_trading_var.get()

        if self.is_paper_trading:
            # Switch to paper trading
            self.real_trading_var.set(False)
            mode_text = "PAPER TRADING (SAFE)"
            mode_color = "green"
            self.trading_mode_label.configure(text=f"📝 {mode_text}", text_color=mode_color)
            self.manual_buy_btn.configure(text="💰 Paper Buy")
            self.manual_sell_btn.configure(text="💸 Paper Sell")
            self.start_btn.configure(text="📝 Start Paper Trading")
            self.start_btn_trading.configure(text="📝 Start Paper Trading")

        self.status_cards["Mode"].configure(text=mode_text, text_color=mode_color)
        self.log(f"🔄 Switched to {mode_text}")

    def toggle_real_trading(self):
        """🔥 Toggle REAL TRADING mode"""
        is_real = self.real_trading_var.get()

        if is_real:
            # 🔥 MULTIPLE CONFIRMATIONS FOR REAL TRADING
            if not messagebox.askyesno("🔥 DANGER - REAL TRADING",
                                       "ENABLE REAL MONEY TRADING?\n\n"
                                       "⚠️ WARNING ⚠️\n"
                                       "• This will use ACTUAL money\n"
                                       "• Orders will be placed on Bitkub\n"
                                       "• You can lose real funds\n\n"
                                       "Have you tested thoroughly with paper trading?"):
                self.real_trading_var.set(False)
                return

            if not messagebox.askyesno("🔥 FINAL WARNING",
                                       "LAST CHANCE TO CANCEL!\n\n"
                                       "You are about to enable REAL money trading.\n\n"
                                       "✅ I understand the risks\n"
                                       "✅ I have tested with paper trading\n"
                                       "✅ I am using funds I can afford to lose\n"
                                       "✅ I take full responsibility\n\n"
                                       "PROCEED WITH REAL TRADING?"):
                self.real_trading_var.set(False)
                return

            # Final API check
            if not self.api_client or not self.api_client.api_key:
                messagebox.showerror("Error", "Please connect API first!")
                self.real_trading_var.set(False)
                return

            # Switch to real trading
            self.paper_trading_var.set(False)
            self.is_paper_trading = False
            mode_text = "🔥 REAL TRADING (DANGER!)"
            mode_color = "red"
            self.trading_mode_label.configure(text=mode_text, text_color=mode_color)
            self.manual_buy_btn.configure(text="🔥 REAL BUY")
            self.manual_sell_btn.configure(text="🔥 REAL SELL")
            self.start_btn.configure(text="🔥 Start REAL Trading")
            self.start_btn_trading.configure(text="🔥 Start REAL Trading")

            # Visual warning
            self.update_scifi_visual_state("error", "REAL TRADING ENABLED")
            if hasattr(self, 'scifi_visual'):
                self.scifi_visual.flash_effect("#ff0000", 1.0)

            self.log("🔥 REAL TRADING ENABLED - EXTREME CAUTION!")
            self.log("⚠️ All orders will use actual money!")
        else:
            # Return to paper trading
            self.toggle_paper_trading()

    def toggle_coin_recommendation(self):
        """Toggle coin recommendation system"""
        self.config['use_coin_recommendation'] = self.coin_rec_var.get()
        status = "ON" if self.config['use_coin_recommendation'] else "OFF"
        self.log(f"🪙 Auto coin selection: {status}")

    def toggle_trading(self):
        """🔥 Toggle trading on/off with REAL money capability"""
        if not self.is_trading:
            if not self.api_client or not self.strategy:
                messagebox.showwarning("Error", "Please connect API first")
                return

            # 🔥 REAL TRADING FINAL CHECK
            if not self.is_paper_trading:
                balance = self.api_client.check_balance()
                if balance and balance.get('error') == 0:
                    try:
                        thb_balance = balance['result'].get('THB', 0)
                        if isinstance(thb_balance, dict):
                            thb_value = thb_balance.get('available', 0)
                        else:
                            thb_value = thb_balance
                        thb_float = float(thb_value) if thb_value else 0.0

                        if not messagebox.askyesno("🔥 START REAL TRADING",
                                                   f"START REAL MONEY TRADING?\n\n"
                                                   f"💰 Available Balance: {thb_float:,.2f} THB\n"
                                                   f"💸 Amount per trade: {self.config['trade_amount_thb']} THB\n"
                                                   f"📊 Max daily trades: {self.config['max_daily_trades']}\n"
                                                   f"🪙 Symbol: {self.config['symbol'].upper()}\n"
                                                   f"🔄 Auto coin selection: {'ON' if self.config.get('use_coin_recommendation') else 'OFF'}\n\n"
                                                   f"⚠️ THIS WILL USE REAL MONEY! ⚠️"):
                            return
                    except:
                        if not messagebox.askyesno("🔥 START REAL TRADING",
                                                   "START REAL MONEY TRADING?\n\n"
                                                   "Balance could not be determined.\n"
                                                   "Proceed at your own risk?"):
                            return

            self.is_trading = True
            self.emergency_stop = False

            if self.is_paper_trading:
                self.start_btn.configure(text="⏹️ Stop Paper Trading", fg_color="orange")
                self.start_btn_trading.configure(text="⏹️ Stop Paper Trading", fg_color="orange")
            else:
                self.start_btn.configure(text="🔥 STOP REAL TRADING", fg_color="darkred")
                self.start_btn_trading.configure(text="🔥 STOP REAL TRADING", fg_color="darkred")

            mode = "PAPER" if self.is_paper_trading else "🔥 REAL"
            self.update_scifi_visual_state("analyzing", f"Starting {mode} trading")
            self.log(f"🚀 Started {mode} trading")
            self.log(f"💰 Trade amount: {self.config['trade_amount_thb']} THB")
            self.log(f"🪙 Symbol: {self.config['symbol'].upper()}")
            self.log(f"🔄 Auto coin selection: {'ON' if self.config.get('use_coin_recommendation') else 'OFF'}")

            threading.Thread(target=self.enhanced_trading_loop, daemon=True).start()
        else:
            self.stop_trading()

    def stop_trading(self):
        """Stop trading"""
        self.is_trading = False
        if self.is_paper_trading:
            self.start_btn.configure(text="📝 Start Paper Trading", fg_color="green")
            self.start_btn_trading.configure(text="📝 Start Paper Trading", fg_color="green")
        else:
            self.start_btn.configure(text="🔥 Start REAL Trading", fg_color="red")
            self.start_btn_trading.configure(text="🔥 Start REAL Trading", fg_color="red")

        self.update_scifi_visual_state("idle", "Trading stopped")
        self.log("⏹️ Trading stopped")

    def enhanced_trading_loop(self):
        """🔥 ENHANCED trading loop with REAL money capability"""
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
                    if time_since_trade < 300:  # 5 minutes minimum
                        time.sleep(30)
                        continue

                # Determine which symbol to trade
                current_symbol = self.config['symbol']

                if self.config.get('use_coin_recommendation') and self.coin_recommender:
                    self.update_scifi_visual_state("coin_analysis", "AI selecting best coin")
                    best_coin = self.coin_recommender.get_best_coin(self.config['trade_amount_thb'])

                    if best_coin and best_coin['ai_score'] >= 6.0:  # Minimum score threshold
                        current_symbol = best_coin['symbol']
                        self.log(f"🎯 AI selected: {current_symbol.upper()} (Score: {best_coin['ai_score']:.1f})")
                        self.current_coin_label.configure(text=current_symbol.upper())
                        self.recommended_coin_label.configure(
                            text=f"{current_symbol.upper()} ({best_coin['ai_score']:.1f})")
                    else:
                        self.log(f"⚠️ No good coins found, using: {current_symbol.upper()}")

                # Visual feedback for analysis
                self.update_scifi_visual_state("analyzing", f"Analyzing {current_symbol.upper()}")

                # Get market data
                ticker = self.api_client.get_simple_ticker(current_symbol)
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
                    try:
                        thb_data = balance['result'].get('THB', 0)
                        if isinstance(thb_data, dict):
                            thb_balance = float(thb_data.get('available', 0))
                        else:
                            thb_balance = float(thb_data)
                    except:
                        thb_balance = 0

                # Check for buy signal with fee consideration
                should_buy, buy_reason = self.strategy.should_buy_profitable(
                    current_price, volume_24h, thb_balance, self.config['trade_amount_thb']
                )

                if should_buy:
                    self.update_scifi_visual_state("buy_signal", f"Buy signal: {buy_reason}")
                    self.execute_enhanced_buy(current_price, current_symbol, buy_reason)

                # Check for sell signal
                if self.strategy.position:
                    should_sell, sell_reason = self.strategy.should_sell_profitable(current_price, volume_24h)
                    if should_sell:
                        if "Profit" in sell_reason or "profit" in sell_reason:
                            self.update_scifi_visual_state("success", f"Profitable sell: {sell_reason}")
                        else:
                            self.update_scifi_visual_state("sell_signal", f"Sell signal: {sell_reason}")
                        self.execute_enhanced_sell(current_price, current_symbol, sell_reason)

                # Update displays
                self.update_enhanced_dashboard()
                self.update_position_display()

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

    def execute_enhanced_buy(self, price, symbol, reason):
        """🔥 Execute REAL or PAPER buy order"""
        try:
            amount_thb = self.config['trade_amount_thb']
            crypto_amount = amount_thb / price

            # Calculate expected fees
            expected_buy_fee = self.api_client.calculate_trading_fees(crypto_amount, price, "buy")
            break_even_price = self.api_client.calculate_break_even_price(price, "buy")

            self.update_scifi_visual_state("trading", f"Executing buy: {amount_thb} THB")

            if self.is_paper_trading:
                # Paper trading
                self.strategy.position = {
                    'symbol': symbol,
                    'entry_price': price,
                    'amount': crypto_amount,
                    'entry_time': datetime.now()
                }

                self.log(f"📝 PAPER BUY: {amount_thb} THB @ {price:.2f}")
                self.log(f"   Amount: {crypto_amount:.8f} {symbol.upper()}")
                self.log(f"   Reason: {reason}")
                self.log(f"   Expected fee: {expected_buy_fee:.2f} THB")
                self.log(f"   Break-even: {break_even_price:.2f} THB")

                self.save_enhanced_trade('buy', crypto_amount, price, amount_thb,
                                         'PAPER', 0, expected_buy_fee, 0, reason, True, symbol)

                self.update_scifi_visual_state("success", "Paper buy executed")
            else:
                # 🔥 REAL TRADING
                buy_price = price * 1.002  # Small buffer for execution

                self.log(f"🔥 REAL BUY: {amount_thb} THB @ {buy_price:.2f}")
                self.log(f"   Symbol: {symbol.upper()}")
                self.log(f"   Expected amount: {crypto_amount:.8f}")

                result = self.api_client.place_buy_order_safe(
                    symbol, amount_thb, buy_price, 'limit'
                )

                if result and result.get('error') == 0:
                    order_info = result['result']
                    order_id = order_info.get('id', 'unknown')
                    actual_amount = order_info.get('rec', crypto_amount)
                    actual_fee = order_info.get('fee', expected_buy_fee)

                    self.strategy.position = {
                        'symbol': symbol,
                        'entry_price': buy_price,
                        'amount': actual_amount,
                        'entry_time': datetime.now(),
                        'order_id': order_id
                    }

                    self.log(f"✅ 🔥 REAL BUY SUCCESS: Order ID {order_id}")
                    self.log(f"   Actual amount: {actual_amount:.8f}")
                    self.log(f"   Actual fee: {actual_fee:.2f} THB")

                    self.total_fees_paid += actual_fee
                    self.save_enhanced_trade('buy', actual_amount, buy_price, amount_thb,
                                             order_id, 0, actual_fee, 0, reason, False, symbol)

                    self.update_scifi_visual_state("success", "🔥 REAL buy executed!")
                else:
                    error_code = result.get("error", 999) if result else 999
                    error_msg = self.api_client.error_codes.get(error_code, f"Error {error_code}")
                    self.log(f"❌ 🔥 REAL buy failed: {error_msg}")
                    self.update_scifi_visual_state("error", f"Real buy failed: {error_msg}")

                    # Show error dialog for real trading
                    messagebox.showerror("🔥 REAL Trading Error",
                                         f"Buy order failed!\n\nError: {error_msg}\n\n"
                                         f"Check your balance and API permissions.")
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
            if not self.is_paper_trading:
                messagebox.showerror("🔥 REAL Trading Error", f"Buy execution failed: {e}")

    def execute_enhanced_sell(self, price, symbol, reason):
        """🔥 Execute REAL or PAPER sell order"""
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

            self.update_scifi_visual_state("trading", f"Executing sell: {amount:.6f}")

            if self.is_paper_trading:
                # Paper trading
                self.log(f"📝 PAPER SELL: {amount:.8f} @ {price:.2f}")
                self.log(f"   Symbol: {symbol.upper()}")
                self.log(f"   Reason: {reason}")
                self.log(f"   Gross P&L: {gross_pnl:.2f} THB")
                self.log(f"   Total fees: {buy_fee + sell_fee:.2f} THB")
                self.log(f"   Net P&L: {net_pnl:.2f} THB")

                self.save_enhanced_trade('sell', amount, price, amount * price,
                                         'PAPER', net_pnl, sell_fee, net_pnl, reason, True, symbol)

                self.update_scifi_visual_state("success", f"Paper sell: {net_pnl:+.2f} THB")
            else:
                # 🔥 REAL TRADING
                sell_price = price * 0.998  # Small buffer for execution

                self.log(f"🔥 REAL SELL: {amount:.8f} @ {sell_price:.2f}")
                self.log(f"   Symbol: {symbol.upper()}")

                result = self.api_client.place_sell_order_safe(
                    symbol, amount, sell_price, 'limit'
                )

                if result and result.get('error') == 0:
                    order_info = result['result']
                    order_id = order_info.get('id', 'unknown')
                    actual_fee = order_info.get('fee', sell_fee)

                    # Recalculate with actual sell price and fee
                    actual_gross_pnl = (sell_price - entry_price) * amount
                    actual_net_pnl = actual_gross_pnl - buy_fee - actual_fee

                    self.log(f"✅ 🔥 REAL SELL SUCCESS: Order ID {order_id}")
                    self.log(f"   Gross P&L: {actual_gross_pnl:.2f} THB")
                    self.log(f"   Total fees: {buy_fee + actual_fee:.2f} THB")
                    self.log(f"   Net P&L: {actual_net_pnl:.2f} THB")

                    self.total_fees_paid += actual_fee
                    self.save_enhanced_trade('sell', amount, sell_price, amount * sell_price,
                                             order_id, actual_net_pnl, actual_fee,
                                             actual_net_pnl, reason, False, symbol)
                    net_pnl = actual_net_pnl

                    if net_pnl > 0:
                        self.update_scifi_visual_state("success", f"🔥 REAL profit: +{net_pnl:.2f} THB")
                        messagebox.showinfo("🔥 REAL Trading Success!",
                                            f"Profitable sale!\n\n"
                                            f"Net Profit: +{net_pnl:.2f} THB\n"
                                            f"Order ID: {order_id}")
                    else:
                        self.update_scifi_visual_state("error", f"🔥 REAL loss: {net_pnl:.2f} THB")
                        messagebox.showwarning("🔥 REAL Trading Loss",
                                               f"Position closed at loss\n\n"
                                               f"Net Loss: {net_pnl:.2f} THB\n"
                                               f"Order ID: {order_id}")
                else:
                    error_code = result.get("error", 999) if result else 999
                    error_msg = self.api_client.error_codes.get(error_code, f"Error {error_code}")
                    self.log(f"❌ 🔥 REAL sell failed: {error_msg}")
                    self.update_scifi_visual_state("error", f"Real sell failed: {error_msg}")

                    messagebox.showerror("🔥 REAL Trading Error",
                                         f"Sell order failed!\n\nError: {error_msg}\n\n"
                                         f"Your position remains open!")
                    return

            self.daily_trades += 1
            self.daily_pnl += net_pnl
            self.strategy.position = None

            self.status_cards["Daily Trades"].configure(text=f"{self.daily_trades}/{self.config['max_daily_trades']}")
            self.status_cards["Position"].configure(text="None")
            self.status_cards["Daily P&L"].configure(text=f"{self.daily_pnl:.2f}")
            self.status_cards["Net Profit"].configure(text=f"{self.daily_pnl - self.total_fees_paid:+.2f}")
            self.status_cards["Total Fees"].configure(text=f"{self.total_fees_paid:.2f}")

        except Exception as e:
            self.log(f"❌ Sell execution error: {e}")
            self.update_scifi_visual_state("error", f"Sell error: {str(e)[:50]}")
            if not self.is_paper_trading:
                messagebox.showerror("🔥 REAL Trading Error", f"Sell execution failed: {e}")

    def save_enhanced_trade(self, side, amount, price, total_thb, order_id, pnl, fees, net_pnl, reason, is_paper,
                            symbol):
        """Save trade with enhanced tracking"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Calculate technical indicators
            rsi = self.strategy.calculate_rsi(list(self.strategy.price_history)) if len(
                self.strategy.price_history) >= 15 else 0
            volume_momentum = self.strategy.calculate_volume_momentum(0) if self.strategy else 0
            break_even_price = self.api_client.calculate_break_even_price(price) if side == "buy" else 0

            cursor.execute('''
                INSERT INTO trades 
                (timestamp, symbol, side, amount, price, total_thb, 
                 order_id, status, pnl, fees, net_pnl, reason, is_paper,
                 rsi, volume_momentum, break_even_price, api_response)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (datetime.now().isoformat(), symbol, side, amount, price,
                  total_thb, order_id, 'completed', pnl, fees, net_pnl, reason,
                  is_paper, rsi, volume_momentum, break_even_price, None))

            conn.commit()
            conn.close()

        except Exception as e:
            self.log(f"❌ Database error: {e}")

    def manual_buy(self):
        """🔥 Manual buy order - REAL or PAPER"""
        if not self.api_client:
            messagebox.showwarning("Error", "Please connect API first")
            return

        if self.strategy and self.strategy.position:
            messagebox.showwarning("Error", "Already have an open position")
            return

        symbol = self.config['symbol']
        ticker = self.api_client.get_simple_ticker(symbol)
        if not ticker:
            messagebox.showerror("Error", "Failed to get market price")
            return

        price = ticker['last_price']

        # Extra confirmation for real trading
        if not self.is_paper_trading:
            if not messagebox.askyesno("🔥 CONFIRM REAL BUY ORDER",
                                       f"Place REAL buy order?\n\n"
                                       f"💰 Amount: {self.config['trade_amount_thb']} THB\n"
                                       f"🪙 Symbol: {symbol.upper()}\n"
                                       f"💵 Price: {price:,.2f} THB\n\n"
                                       f"⚠️ THIS USES REAL MONEY! ⚠️"):
                return

        self.execute_enhanced_buy(price, symbol, "Manual buy order")

    def manual_sell(self):
        """🔥 Manual sell order - REAL or PAPER"""
        if not self.api_client:
            messagebox.showwarning("Error", "Please connect API first")
            return

        if not self.strategy or not self.strategy.position:
            messagebox.showwarning("Error", "No open position to sell")
            return

        symbol = self.strategy.position['symbol']
        ticker = self.api_client.get_simple_ticker(symbol)
        if not ticker:
            messagebox.showerror("Error", "Failed to get market price")
            return

        price = ticker['last_price']

        # Calculate P&L for confirmation
        entry_price = self.strategy.position['entry_price']
        amount = self.strategy.position['amount']
        gross_pnl = (price - entry_price) * amount

        # Extra confirmation for real trading
        if not self.is_paper_trading:
            if not messagebox.askyesno("🔥 CONFIRM REAL SELL ORDER",
                                       f"Place REAL sell order?\n\n"
                                       f"💰 Amount: {amount:.8f} {symbol.upper()}\n"
                                       f"💵 Current Price: {price:,.2f} THB\n"
                                       f"📊 Entry Price: {entry_price:,.2f} THB\n"
                                       f"📈 Gross P&L: {gross_pnl:+.2f} THB\n\n"
                                       f"⚠️ THIS USES REAL MONEY! ⚠️"):
                return

        self.execute_enhanced_sell(price, symbol, "Manual sell order")

    def emergency_stop_trading(self):
        """🔥 Emergency stop with REAL order cancellation"""
        self.update_scifi_visual_state("error", "EMERGENCY STOP ACTIVATED")
        if hasattr(self, 'scifi_visual'):
            self.scifi_visual.flash_effect("#ff0000", 0.5)

        self.emergency_stop = True
        self.is_trading = False

        if self.is_paper_trading:
            self.start_btn.configure(text="📝 Start Paper Trading", fg_color="green")
            self.start_btn_trading.configure(text="📝 Start Paper Trading", fg_color="green")
        else:
            self.start_btn.configure(text="🔥 Start REAL Trading", fg_color="red")
            self.start_btn_trading.configure(text="🔥 Start REAL Trading", fg_color="red")

        self.log("🚨 EMERGENCY STOP ACTIVATED!")

        # Cancel all open orders if real trading
        if not self.is_paper_trading and self.api_client:
            try:
                self.log("🗑️ Cancelling all open REAL orders...")
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
                            self.log(f"✅ Cancelled REAL order {order['id']}")
                        else:
                            self.log(f"❌ Failed to cancel REAL order {order['id']}")
            except Exception as e:
                self.log(f"❌ Error during emergency stop: {e}")

        messagebox.showwarning("Emergency Stop",
                               f"All trading stopped!\n\n"
                               f"{'Paper orders cleared' if self.is_paper_trading else 'REAL orders cancelled'}")

    # === Coin Analysis Functions ===

    def analyze_all_coins(self):
        """Analyze all available coins"""
        if not self.api_client:
            messagebox.showwarning("Error", "Please connect API first")
            return

        self.update_scifi_visual_state("coin_analysis", "Analyzing all coins")
        self.coin_analysis_display.delete("1.0", "end")
        self.coin_analysis_display.insert("1.0",
                                          "🔍 ANALYZING ALL COINS...\n\nPlease wait, this may take 30-60 seconds...\n\n")

        def analyze():
            try:
                trade_amount = float(self.analysis_amount_var.get())
                results = self.coin_recommender.analyze_all_coins(trade_amount, 15)

                if results:
                    analysis_text = f"🪙 COIN ANALYSIS RESULTS ({len(results)} coins)\n"
                    analysis_text += f"💰 Trade Amount: {trade_amount:,.0f} THB\n"
                    analysis_text += f"⏰ Analysis Time: {datetime.now().strftime('%H:%M:%S')}\n\n"
                    analysis_text += "=" * 80 + "\n\n"

                    for i, coin in enumerate(results, 1):
                        analysis_text += f"{i:2d}. {coin['symbol'].upper():<12} "
                        analysis_text += f"Score: {coin['ai_score']:4.1f} "
                        analysis_text += f"{coin['recommendation']:<12} "
                        analysis_text += f"Price: {coin['price']:8.2f} THB\n"
                        analysis_text += f"    Volume: {coin['volume_24h']:12,.0f} THB "
                        analysis_text += f"Change: {coin['change_24h']:+6.2f}% "
                        analysis_text += f"Spread: {coin['spread_pct']:5.2f}%\n"
                        analysis_text += f"    Fee Impact: {coin['fee_impact']:4.2f}% "
                        analysis_text += f"Analysis: {coin['analysis_time'].strftime('%H:%M:%S')}\n\n"

                    analysis_text += "=" * 80 + "\n"
                    analysis_text += f"🏆 BEST COIN: {results[0]['symbol'].upper()} "
                    analysis_text += f"(Score: {results[0]['ai_score']:.1f})\n"
                    analysis_text += f"📊 Average Score: {sum(r['ai_score'] for r in results) / len(results):.1f}\n"

                    self.coin_analysis_display.delete("1.0", "end")
                    self.coin_analysis_display.insert("1.0", analysis_text)

                    self.update_scifi_visual_state("success", f"Analysis complete: {len(results)} coins")
                else:
                    self.coin_analysis_display.delete("1.0", "end")
                    self.coin_analysis_display.insert("1.0",
                                                      "❌ No analysis results available.\n\nPossible issues:\n• API connection problems\n• No market data available\n• All coins below minimum criteria")
                    self.update_scifi_visual_state("error", "Analysis failed")

            except Exception as e:
                self.coin_analysis_display.delete("1.0", "end")
                self.coin_analysis_display.insert("1.0", f"❌ Analysis error: {e}")
                self.update_scifi_visual_state("error", f"Analysis error: {str(e)[:30]}")

        threading.Thread(target=analyze, daemon=True).start()

    def get_best_coin(self):
        """Get the best coin recommendation"""
        if not self.coin_recommender:
            messagebox.showwarning("Error", "Please connect API first")
            return

        self.update_scifi_visual_state("coin_analysis", "Finding best coin")

        def get_best():
            try:
                trade_amount = float(self.analysis_amount_var.get())
                best = self.coin_recommender.get_best_coin(trade_amount)

                if best:
                    result_text = f"🏆 BEST COIN RECOMMENDATION\n\n"
                    result_text += f"Symbol: {best['symbol'].upper()}\n"
                    result_text += f"AI Score: {best['ai_score']:.1f}/10\n"
                    result_text += f"Recommendation: {best['recommendation']}\n"
                    result_text += f"Price: {best['price']:,.2f} THB\n"
                    result_text += f"24h Volume: {best['volume_24h']:,.0f} THB\n"
                    result_text += f"24h Change: {best['change_24h']:+.2f}%\n"
                    result_text += f"Spread: {best['spread_pct']:.2f}%\n"
                    result_text += f"Fee Impact: {best['fee_impact']:.2f}%\n\n"

                    if best['ai_score'] >= 7:
                        result_text += "✅ RECOMMENDED FOR TRADING\n"
                    elif best['ai_score'] >= 5:
                        result_text += "⚠️ MODERATE RECOMMENDATION\n"
                    else:
                        result_text += "❌ NOT RECOMMENDED\n"

                    # Update UI
                    self.recommended_coin_label.configure(text=f"{best['symbol'].upper()} ({best['ai_score']:.1f})")

                    # Ask if user wants to switch
                    if messagebox.askyesno("Switch Coin?",
                                           f"Switch to {best['symbol'].upper()}?\n\n" +
                                           f"Current: {self.config['symbol'].upper()}\n" +
                                           f"Recommended: {best['symbol'].upper()} (Score: {best['ai_score']:.1f})"):
                        self.config['symbol'] = best['symbol']
                        self.symbol_var.set(best['symbol'])
                        self.current_coin_label.configure(text=best['symbol'].upper())
                        self.log(f"🔄 Switched to {best['symbol'].upper()}")

                    self.coin_analysis_display.delete("1.0", "end")
                    self.coin_analysis_display.insert("1.0", result_text)
                    self.update_scifi_visual_state("success", f"Best coin: {best['symbol'].upper()}")
                else:
                    self.coin_analysis_display.delete("1.0", "end")
                    self.coin_analysis_display.insert("1.0", "❌ No suitable coin found")
                    self.update_scifi_visual_state("error", "No suitable coin")

            except Exception as e:
                self.coin_analysis_display.delete("1.0", "end")
                self.coin_analysis_display.insert("1.0", f"❌ Error: {e}")
                self.update_scifi_visual_state("error", f"Error: {str(e)[:30]}")

        threading.Thread(target=get_best, daemon=True).start()

    def analyze_best_coin(self):
        """Quick analyze best coin from dashboard"""
        if not self.coin_recommender:
            messagebox.showwarning("Error", "Please connect API first")
            return

        self.update_scifi_visual_state("coin_analysis", "Quick analysis")

        def quick_analyze():
            try:
                best = self.coin_recommender.get_best_coin(self.config['trade_amount_thb'])
                if best:
                    self.recommended_coin_label.configure(text=f"{best['symbol'].upper()} ({best['ai_score']:.1f})")
                    self.log(f"🏆 Best coin: {best['symbol'].upper()} (Score: {best['ai_score']:.1f})")
                    self.update_scifi_visual_state("success", f"Best: {best['symbol'].upper()}")
                else:
                    self.log("❌ No suitable coin found")
                    self.update_scifi_visual_state("error", "No suitable coin")
            except Exception as e:
                self.log(f"❌ Quick analysis error: {e}")
                self.update_scifi_visual_state("error", "Analysis error")

        threading.Thread(target=quick_analyze, daemon=True).start()

    def refresh_coin_analysis(self):
        """Refresh coin analysis cache"""
        if self.coin_recommender:
            self.coin_recommender.analysis_cache.clear()
            self.coin_recommender.last_analysis_time = 0
            self.log("🔄 Coin analysis cache cleared")
            self.update_scifi_visual_state("success", "Cache cleared")
        else:
            messagebox.showwarning("Error", "Please connect API first")

    # === Testing Functions ===

    def test_connection(self):
        """Test API connection"""
        if not self.api_client:
            self.api_status_display.delete("1.0", "end")
            self.api_status_display.insert("1.0", "❌ Please connect API first")
            return

        self.update_scifi_visual_state("connecting", "Testing connection")
        self.api_status_display.delete("1.0", "end")
        self.api_status_display.insert("1.0", "🔌 Testing REAL API Connection...\n\n")

        def test():
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
                try:
                    thb_data = balance['result'].get('THB', 0)
                    if isinstance(thb_data, dict):
                        thb_value = thb_data.get('available', 0)
                    else:
                        thb_value = thb_data
                    thb_float = float(thb_value) if thb_value else 0.0
                    self.api_status_display.insert("end", f"✅ Balance: {thb_float:,.2f} THB\n")
                except:
                    self.api_status_display.insert("end", f"✅ Balance: Connected (format unknown)\n")
            else:
                self.api_status_display.insert("end", "❌ Balance: Failed\n")

            # Test system status
            status_ok, status_msg = self.api_client.check_system_status()
            self.api_status_display.insert("end", f"{'✅' if status_ok else '❌'} System: {status_msg}\n")

            self.update_scifi_visual_state("success", "Connection test complete")

        threading.Thread(target=test, daemon=True).start()

    def test_market_data(self):
        """Test market data retrieval"""
        if not self.api_client:
            messagebox.showwarning("Error", "Please connect API first")
            return

        self.test_results_display.delete("1.0", "end")
        self.test_results_display.insert("1.0", "🔍 Testing market data...\n\n")

        def test():
            try:
                symbol = self.config['symbol']
                ticker = self.api_client.get_simple_ticker(symbol)
                if ticker:
                    self.test_results_display.insert("end", f"✅ Ticker data for {symbol.upper()}:\n")
                    self.test_results_display.insert("end", f"   Price: {ticker['last_price']:,.2f} THB\n")
                    self.test_results_display.insert("end", f"   Volume: {ticker['volume_24h']:,.0f} THB\n")
                    self.test_results_display.insert("end", f"   Change: {ticker['change_24h']:+.2f}%\n\n")
                else:
                    self.test_results_display.insert("end", f"❌ Failed to get ticker for {symbol}\n\n")

                # Test orderbook
                orderbook = self.api_client.get_orderbook(symbol, 3)
                if orderbook:
                    self.test_results_display.insert("end", f"✅ Orderbook data:\n")
                    if orderbook.get('bids'):
                        self.test_results_display.insert("end", f"   Best bid: {orderbook['bids'][0][0]} THB\n")
                    if orderbook.get('asks'):
                        self.test_results_display.insert("end", f"   Best ask: {orderbook['asks'][0][0]} THB\n")
                else:
                    self.test_results_display.insert("end", f"❌ Failed to get orderbook for {symbol}\n")

            except Exception as e:
                self.test_results_display.insert("end", f"❌ Test error: {e}\n")

        threading.Thread(target=test, daemon=True).start()

    def test_balance_check(self):
        """Test balance checking"""
        if not self.api_client:
            messagebox.showwarning("Error", "Please connect API first")
            return

        self.test_results_display.delete("1.0", "end")
        self.test_results_display.insert("1.0", "💰 Testing balance check...\n\n")

        def test():
            try:
                balance = self.api_client.check_balance()
                if balance and balance.get('error') == 0:
                    self.test_results_display.insert("end", "✅ Balance retrieved:\n")

                    total_value_thb = 0
                    for currency, data in balance['result'].items():
                        if isinstance(data, dict):
                            available = float(data.get('available', 0))
                            reserved = float(data.get('reserved', 0))
                            total = available + reserved
                        else:
                            available = float(data)
                            reserved = 0
                            total = available

                        if total > 0:
                            self.test_results_display.insert("end",
                                                             f"   {currency}: {total:,.8f} (Available: {available:,.8f})\n")

                            if currency == 'THB':
                                total_value_thb += total
                            elif currency != 'THB':
                                # Try to get THB value
                                try:
                                    symbol = f"{currency.lower()}_thb"
                                    ticker = self.api_client.get_simple_ticker(symbol)
                                    if ticker:
                                        thb_value = total * ticker['last_price']
                                        total_value_thb += thb_value
                                        self.test_results_display.insert("end", f"      ≈ {thb_value:,.2f} THB\n")
                                except:
                                    pass

                    self.test_results_display.insert("end",
                                                     f"\n📊 Total portfolio value: ≈ {total_value_thb:,.2f} THB\n")
                else:
                    error_msg = "Unknown error"
                    if balance:
                        error_code = balance.get("error", 999)
                        error_msg = self.api_client.error_codes.get(error_code, f"Error {error_code}")
                    self.test_results_display.insert("end", f"❌ Balance check failed: {error_msg}\n")

            except Exception as e:
                self.test_results_display.insert("end", f"❌ Test error: {e}\n")

        threading.Thread(target=test, daemon=True).start()

    def test_open_orders(self):
        """Test open orders check"""
        if not self.api_client:
            messagebox.showwarning("Error", "Please connect API first")
            return

        self.test_results_display.delete("1.0", "end")
        self.test_results_display.insert("1.0", "📋 Testing open orders check...\n\n")

        def test():
            try:
                orders = self.api_client.get_my_open_orders_safe(self.config['symbol'])
                if orders and orders.get('error') == 0:
                    order_list = orders.get('result', [])
                    if order_list:
                        self.test_results_display.insert("end", f"✅ Found {len(order_list)} open orders:\n")
                        for order in order_list:
                            side = order.get('side', 'unknown').upper()
                            order_id = order.get('id', 'N/A')
                            rate = float(order.get('rate', 0))
                            amount = float(order.get('amount', 0))
                            self.test_results_display.insert("end",
                                                             f"   {side} Order ID: {order_id}, Price: {rate:,.2f}, Amount: {amount:.8f}\n")
                    else:
                        self.test_results_display.insert("end", "✅ No open orders found\n")
                else:
                    error_code = orders.get("error", 999) if orders else 999
                    error_msg = self.api_client.error_codes.get(error_code, f"Error {error_code}")
                    self.test_results_display.insert("end", f"❌ Failed to get orders: {error_msg}\n")

            except Exception as e:
                self.test_results_display.insert("end", f"❌ Test error: {e}\n")

        threading.Thread(target=test, daemon=True).start()

    def test_scifi_visuals(self):
        """Test Sci-Fi visual states"""
        if not self.scifi_visual:
            messagebox.showwarning("Error", "Sci-Fi visual system not initialized")
            return

        states = ["idle", "connecting", "analyzing", "coin_analysis", "buy_signal", "sell_signal", "trading", "success",
                  "error"]

        def cycle_states():
            for state in states:
                self.update_scifi_visual_state(state, f"Testing {state}")
                time.sleep(2)
            self.update_scifi_visual_state("idle", "Test complete")

        self.test_results_display.delete("1.0", "end")
        self.test_results_display.insert("1.0", "🎨 Testing Sci-Fi visual states...\n\n")
        self.test_results_display.insert("end", "Watch the visual system cycle through all states.\n")

        threading.Thread(target=cycle_states, daemon=True).start()

    def test_fee_calculation(self):
        """Test fee calculation system"""
        if not self.api_client:
            messagebox.showwarning("Error", "Please connect API first")
            return

        self.test_results_display.delete("1.0", "end")
        self.test_results_display.insert("1.0", "💸 Testing fee calculation...\n\n")

        try:
            test_amount = 1000  # Test with 1000 THB
            symbol = self.config['symbol']

            ticker = self.api_client.get_simple_ticker(symbol)
            if ticker:
                price = ticker['last_price']
                crypto_amount = test_amount / price

                buy_fee = self.api_client.calculate_trading_fees(crypto_amount, price, "buy")
                sell_fee = self.api_client.calculate_trading_fees(crypto_amount, price, "sell")
                total_fees = self.api_client.calculate_trading_fees(crypto_amount, price, "both")
                break_even = self.api_client.calculate_break_even_price(price, "buy")

                self.test_results_display.insert("end",
                                                 f"✅ Fee calculation for {test_amount} THB on {symbol.upper()}:\n")
                self.test_results_display.insert("end", f"   Current price: {price:,.2f} THB\n")
                self.test_results_display.insert("end", f"   Crypto amount: {crypto_amount:.8f}\n")
                self.test_results_display.insert("end",
                                                 f"   Buy fee: {buy_fee:.2f} THB ({(buy_fee / test_amount) * 100:.3f}%)\n")
                self.test_results_display.insert("end", f"   Sell fee: {sell_fee:.2f} THB\n")
                self.test_results_display.insert("end", f"   Total fees: {total_fees:.2f} THB\n")
                self.test_results_display.insert("end", f"   Break-even price: {break_even:,.2f} THB\n")
                self.test_results_display.insert("end",
                                                 f"   Required gain: {((break_even - price) / price) * 100:.3f}%\n\n")

                # Test profitability scenarios
                self.test_results_display.insert("end", f"📊 Profitability scenarios:\n")
                for pct in [0.5, 1.0, 1.5, 2.0, 3.0]:
                    sell_price = price * (1 + pct / 100)
                    gross_profit = (sell_price - price) * crypto_amount
                    net_profit = gross_profit - buy_fee - sell_fee
                    self.test_results_display.insert("end", f"   +{pct}% → Net profit: {net_profit:+.2f} THB\n")
            else:
                self.test_results_display.insert("end", "❌ Failed to get price data\n")

        except Exception as e:
            self.test_results_display.insert("end", f"❌ Test error: {e}\n")

    def test_coin_analysis(self):
        """Test coin analysis system"""
        if not self.coin_recommender:
            messagebox.showwarning("Error", "Please connect API first")
            return

        self.test_results_display.delete("1.0", "end")
        self.test_results_display.insert("1.0", "🪙 Testing coin analysis system...\n\n")

        def test():
            try:
                # Test single coin analysis
                symbol = self.config['symbol']
                self.test_results_display.insert("end", f"Testing analysis for {symbol.upper()}...\n")

                analysis = self.coin_recommender.analyze_single_coin(symbol, 1000)
                if analysis:
                    self.test_results_display.insert("end", f"✅ Analysis result:\n")
                    self.test_results_display.insert("end", f"   AI Score: {analysis['ai_score']:.1f}/10\n")
                    self.test_results_display.insert("end", f"   Recommendation: {analysis['recommendation']}\n")
                    self.test_results_display.insert("end", f"   Price: {analysis['price']:,.2f} THB\n")
                    self.test_results_display.insert("end", f"   Volume: {analysis['volume_24h']:,.0f} THB\n")
                    self.test_results_display.insert("end", f"   Fee Impact: {analysis['fee_impact']:.2f}%\n")
                else:
                    self.test_results_display.insert("end", f"❌ Failed to analyze {symbol}\n")

            except Exception as e:
                self.test_results_display.insert("end", f"❌ Test error: {e}\n")

        threading.Thread(target=test, daemon=True).start()

    def test_real_order_simulation(self):
        """🔥 Test REAL order simulation (DANGEROUS!)"""
        if not self.api_client:
            messagebox.showwarning("Error", "Please connect API first")
            return

        # 🔥 MULTIPLE WARNINGS
        if not messagebox.askyesno("🔥 DANGER - REAL ORDER TEST",
                                   "This will test REAL order placement!\n\n"
                                   "⚠️ WARNING ⚠️\n"
                                   "• This uses REAL money\n"
                                   "• Orders will be placed on Bitkub\n"
                                   "• Small test amount will be used\n\n"
                                   "Only proceed if you:\n"
                                   "✅ Understand the risks\n"
                                   "✅ Have tested extensively\n"
                                   "✅ Are using test funds\n\n"
                                   "PROCEED WITH REAL ORDER TEST?"):
            return

        if not messagebox.askyesno("🔥 FINAL WARNING",
                                   "LAST CHANCE TO CANCEL!\n\n"
                                   "This will place a REAL order with REAL money.\n\n"
                                   "Test amount: 100 THB\n"
                                   "Symbol: " + self.config['symbol'].upper() + "\n\n"
                                                                                "PLACE REAL TEST ORDER?"):
            return

        self.test_results_display.delete("1.0", "end")
        self.test_results_display.insert("1.0", "🔥 Testing REAL order placement...\n\n")
        self.test_results_display.insert("end", "⚠️ WARNING: This uses REAL money!\n\n")

        def test():
            try:
                symbol = self.config['symbol']
                test_amount = 100  # Small test amount

                # Get current price
                ticker = self.api_client.get_simple_ticker(symbol)
                if not ticker:
                    self.test_results_display.insert("end", "❌ Failed to get market price\n")
                    return

                current_price = ticker['last_price']
                buy_price = current_price * 1.01  # 1% above market

                self.test_results_display.insert("end", f"🔥 Placing REAL test buy order:\n")
                self.test_results_display.insert("end", f"   Symbol: {symbol.upper()}\n")
                self.test_results_display.insert("end", f"   Amount: {test_amount} THB\n")
                self.test_results_display.insert("end", f"   Price: {buy_price:,.2f} THB\n\n")

                # Place REAL order
                result = self.api_client.place_buy_order_safe(symbol, test_amount, buy_price, 'limit')

                if result and result.get('error') == 0:
                    order_info = result['result']
                    order_id = order_info.get('id', 'unknown')

                    self.test_results_display.insert("end", f"✅ 🔥 REAL ORDER PLACED SUCCESSFULLY!\n")
                    self.test_results_display.insert("end", f"   Order ID: {order_id}\n")
                    self.test_results_display.insert("end", f"   Amount: {order_info.get('amt', 'N/A')} THB\n")
                    self.test_results_display.insert("end", f"   Rate: {order_info.get('rat', 'N/A')} THB\n\n")

                    # Ask if user wants to cancel immediately
                    if messagebox.askyesno("Cancel Test Order?",
                                           f"REAL test order placed successfully!\n\n"
                                           f"Order ID: {order_id}\n\n"
                                           f"Cancel this order immediately?"):
                        cancel_result = self.api_client.cancel_order_safe(symbol, order_id, "buy")
                        if cancel_result.get('error') == 0:
                            self.test_results_display.insert("end", f"✅ Test order cancelled successfully\n")
                        else:
                            self.test_results_display.insert("end", f"❌ Failed to cancel test order\n")
                else:
                    error_code = result.get("error", 999) if result else 999
                    error_msg = self.api_client.error_codes.get(error_code, f"Error {error_code}")
                    self.test_results_display.insert("end", f"❌ REAL order failed: {error_msg}\n")

            except Exception as e:
                self.test_results_display.insert("end", f"❌ Test error: {e}\n")

        threading.Thread(target=test, daemon=True).start()

    def test_trading_signals(self):
        """Test trading signal generation"""
        if not self.strategy:
            messagebox.showwarning("Error", "Please connect API first")
            return

        self.test_results_display.delete("1.0", "end")
        self.test_results_display.insert("1.0", "📊 Testing trading signals...\n\n")

        def test():
            try:
                symbol = self.config['symbol']
                ticker = self.api_client.get_simple_ticker(symbol)

                if not ticker:
                    self.test_results_display.insert("end", "❌ Failed to get market data\n")
                    return

                current_price = ticker['last_price']
                volume_24h = ticker.get('volume_24h', 0)

                # Test buy signal
                should_buy, buy_reason = self.strategy.should_buy_profitable(
                    current_price, volume_24h, 10000, self.config['trade_amount_thb']
                )

                self.test_results_display.insert("end", f"📈 BUY SIGNAL TEST:\n")
                self.test_results_display.insert("end", f"   Symbol: {symbol.upper()}\n")
                self.test_results_display.insert("end", f"   Price: {current_price:,.2f} THB\n")
                self.test_results_display.insert("end", f"   Should Buy: {'✅ YES' if should_buy else '❌ NO'}\n")
                self.test_results_display.insert("end", f"   Reason: {buy_reason}\n\n")

                # Test sell signal if position exists
                if self.strategy.position:
                    should_sell, sell_reason = self.strategy.should_sell_profitable(current_price, volume_24h)

                    self.test_results_display.insert("end", f"📉 SELL SIGNAL TEST:\n")
                    self.test_results_display.insert("end", f"   Should Sell: {'✅ YES' if should_sell else '❌ NO'}\n")
                    self.test_results_display.insert("end", f"   Reason: {sell_reason}\n\n")
                else:
                    self.test_results_display.insert("end", f"📉 SELL SIGNAL TEST: No position to test\n\n")

                # Calculate technical indicators
                if len(self.strategy.price_history) >= 15:
                    rsi = self.strategy.calculate_rsi(list(self.strategy.price_history))
                    self.test_results_display.insert("end", f"📊 TECHNICAL INDICATORS:\n")
                    self.test_results_display.insert("end", f"   RSI: {rsi:.1f}\n")

                    if rsi < 30:
                        self.test_results_display.insert("end", f"   RSI Status: Oversold (Bullish)\n")
                    elif rsi > 70:
                        self.test_results_display.insert("end", f"   RSI Status: Overbought (Bearish)\n")
                    else:
                        self.test_results_display.insert("end", f"   RSI Status: Neutral\n")
                else:
                    self.test_results_display.insert("end", f"📊 Need more price history for RSI calculation\n")

            except Exception as e:
                self.test_results_display.insert("end", f"❌ Test error: {e}\n")

        threading.Thread(target=test, daemon=True).start()

    def system_health_check(self):
        """Comprehensive system health check"""
        if not self.api_client:
            messagebox.showwarning("Error", "Please connect API first")
            return

        self.update_scifi_visual_state("analyzing", "Running health check")
        self.api_status_display.delete("1.0", "end")
        self.api_status_display.insert("1.0", "🏥 Running comprehensive system health check...\n\n")

        def health_check():
            try:
                # 1. API Connection
                self.api_status_display.insert("end", "1. Testing API connection...\n")
                balance = self.api_client.check_balance()
                if balance and balance.get('error') == 0:
                    self.api_status_display.insert("end", "   ✅ API connection working\n")
                else:
                    self.api_status_display.insert("end", "   ❌ API connection failed\n")

                # 2. System Status
                self.api_status_display.insert("end", "\n2. Checking Bitkub system status...\n")
                status_ok, status_msg = self.api_client.check_system_status()
                self.api_status_display.insert("end", f"   {'✅' if status_ok else '❌'} {status_msg}\n")

                # 3. Market Data
                self.api_status_display.insert("end", "\n3. Testing market data access...\n")
                ticker = self.api_client.get_simple_ticker(self.config['symbol'])
                if ticker:
                    self.api_status_display.insert("end",
                                                   f"   ✅ Market data available for {self.config['symbol'].upper()}\n")
                    self.api_status_display.insert("end", f"   Price: {ticker['last_price']:,.2f} THB\n")
                else:
                    self.api_status_display.insert("end",
                                                   f"   ❌ Market data failed for {self.config['symbol'].upper()}\n")

                # 4. Balance Check
                self.api_status_display.insert("end", "\n4. Checking account balance...\n")
                if balance and balance.get('error') == 0:
                    try:
                        thb_data = balance['result'].get('THB', 0)
                        if isinstance(thb_data, dict):
                            thb_balance = float(thb_data.get('available', 0))
                        else:
                            thb_balance = float(thb_data)
                        self.api_status_display.insert("end", f"   ✅ THB Balance: {thb_balance:,.2f}\n")

                        if thb_balance >= self.config['trade_amount_thb']:
                            self.api_status_display.insert("end", f"   ✅ Sufficient balance for trading\n")
                        else:
                            self.api_status_display.insert("end",
                                                           f"   ⚠️ Low balance for trade amount ({self.config['trade_amount_thb']} THB)\n")
                    except:
                        self.api_status_display.insert("end", f"   ✅ Balance available (format unknown)\n")

                # 5. Trading Configuration
                self.api_status_display.insert("end", "\n5. Checking trading configuration...\n")
                self.api_status_display.insert("end", f"   Symbol: {self.config['symbol'].upper()}\n")
                self.api_status_display.insert("end", f"   Trade Amount: {self.config['trade_amount_thb']} THB\n")
                self.api_status_display.insert("end", f"   Max Daily Trades: {self.config['max_daily_trades']}\n")
                self.api_status_display.insert("end",
                                               f"   Trading Mode: {'PAPER' if self.is_paper_trading else '🔥 REAL'}\n")

                # 6. Fee Calculation
                self.api_status_display.insert("end", "\n6. Testing fee calculation...\n")
                if ticker:
                    test_fees = self.api_client.calculate_trading_fees(1000 / ticker['last_price'],
                                                                       ticker['last_price'], "both")
                    self.api_status_display.insert("end",
                                                   f"   ✅ Fee calculation working: {test_fees:.2f} THB for 1000 THB trade\n")

                # 7. Strategy Status
                self.api_status_display.insert("end", "\n7. Checking strategy status...\n")
                if self.strategy:
                    self.api_status_display.insert("end", f"   ✅ Strategy loaded\n")
                    self.api_status_display.insert("end", f"   RSI Oversold: {self.strategy.rsi_oversold}\n")
                    self.api_status_display.insert("end", f"   RSI Overbought: {self.strategy.rsi_overbought}\n")
                    if self.strategy.position:
                        self.api_status_display.insert("end",
                                                       f"   📊 Active position: {self.strategy.position['symbol'].upper()}\n")
                    else:
                        self.api_status_display.insert("end", f"   📊 No active position\n")
                else:
                    self.api_status_display.insert("end", f"   ❌ Strategy not loaded\n")

                # 8. Coin Recommendation
                self.api_status_display.insert("end", "\n8. Checking coin recommendation system...\n")
                if self.coin_recommender:
                    self.api_status_display.insert("end", f"   ✅ Coin recommendation system loaded\n")
                    self.api_status_display.insert("end",
                                                   f"   Auto selection: {'ON' if self.config.get('use_coin_recommendation') else 'OFF'}\n")
                else:
                    self.api_status_display.insert("end", f"   ❌ Coin recommendation system not loaded\n")

                # 9. Visual System
                self.api_status_display.insert("end", "\n9. Checking visual system...\n")
                if hasattr(self, 'scifi_visual') and self.scifi_visual:
                    self.api_status_display.insert("end", f"   ✅ Sci-Fi visual system active\n")
                else:
                    self.api_status_display.insert("end", f"   ❌ Visual system not initialized\n")

                # Summary
                self.api_status_display.insert("end", "\n" + "=" * 50 + "\n")
                self.api_status_display.insert("end", "HEALTH CHECK SUMMARY:\n")

                if balance and balance.get('error') == 0 and ticker and self.strategy:
                    self.api_status_display.insert("end", "✅ System ready for trading\n")
                    if not self.is_paper_trading:
                        self.api_status_display.insert("end", "🔥 REAL TRADING MODE - Use extreme caution!\n")
                else:
                    self.api_status_display.insert("end", "⚠️ Some issues detected - check above\n")

                self.api_status_display.insert("end",
                                               f"\nHealth check completed: {datetime.now().strftime('%H:%M:%S')}\n")
                self.update_scifi_visual_state("success", "Health check completed")

            except Exception as e:
                self.api_status_display.insert("end", f"\n❌ Health check error: {e}\n")
                self.update_scifi_visual_state("error", "Health check failed")

        threading.Thread(target=health_check, daemon=True).start()

    # === Strategy Functions ===

    def auto_configure_strategies(self):
        """Auto configure strategies"""
        if not self.api_client:
            messagebox.showwarning("Error", "Please connect API first")
            return

        self.update_scifi_visual_state("analyzing", "Auto-configuring strategies")

        # Enable recommended strategies
        self.strategy_vars["RSI + Volume"].set(True)
        self.strategy_vars["Volume Breakout"].set(True)
        self.strategy_vars["Scalping"].set(False)  # Too risky for beginners

        # Adjust parameters
        self.rsi_oversold_var.set("25")
        self.rsi_overbought_var.set("75")
        self.stop_loss_var.set("1.5")
        self.take_profit_var.set("2.5")

        self.strategies_display.delete("1.0", "end")
        self.strategies_display.insert("1.0",
                                       "🔄 AUTO CONFIGURATION COMPLETE\n\n"
                                       "✅ ENABLED STRATEGIES:\n"
                                       "• RSI + Volume: Conservative settings (25/75)\n"
                                       "• Volume Breakout: Momentum trading\n\n"
                                       "⚙️ RISK MANAGEMENT:\n"
                                       "• Stop Loss: 1.5%\n"
                                       "• Take Profit: 2.5%\n\n"
                                       "🎯 OPTIMIZED FOR:\n"
                                       "• Risk-conscious trading\n"
                                       "• Consistent small profits\n"
                                       "• Fee-aware execution\n\n"
                                       "💡 Test in paper mode first!")

        self.update_scifi_visual_state("success", "Strategies configured")
        self.log("🔄 Auto-configured strategies")

    def save_strategy_settings(self):
        """Save strategy configuration"""
        try:
            # Update strategy object with new parameters
            if self.strategy:
                self.strategy.rsi_oversold = float(self.rsi_oversold_var.get())
                self.strategy.rsi_overbought = float(self.rsi_overbought_var.get())
                self.strategy.stop_loss_pct = float(self.stop_loss_var.get()) / 100
                self.strategy.take_profit_pct = float(self.take_profit_var.get()) / 100

            messagebox.showinfo("Success", "Strategy settings saved successfully!")
            self.log("💾 Strategy settings saved")

        except ValueError:
            messagebox.showerror("Error", "Invalid parameter values")

    # === UI Helper Functions ===

    def update_scifi_visual_state(self, state, message=""):
        """Update Sci-Fi visual system state"""
        try:
            if self.scifi_visual:
                self.scifi_visual.set_state(state)
                if message:
                    self.visual_status_label.configure(text=message.upper())
        except Exception as e:
            print(f"Visual update error: {e}")

    def update_enhanced_dashboard(self):
        """Update enhanced dashboard with real trading info"""
        # Update all status cards
        self.status_cards["Daily Trades"].configure(
            text=f"{self.daily_trades}/{self.config['max_daily_trades']}"
        )
        self.status_cards["Daily P&L"].configure(text=f"{self.daily_pnl:.2f}")
        self.status_cards["Total Fees"].configure(text=f"{self.total_fees_paid:.2f}")

        net_profit = self.daily_pnl - self.total_fees_paid
        self.status_cards["Net Profit"].configure(text=f"{net_profit:.2f}")

        # Update balance
        self.update_balance()

    def update_balance(self):
        """Update balance display"""
        if not self.api_client:
            return

        balance = self.api_client.check_balance()
        if balance and balance.get('error') == 0:
            try:
                thb_data = balance['result'].get('THB', 0)
                if isinstance(thb_data, dict):
                    thb_balance = float(thb_data.get('available', 0))
                else:
                    thb_balance = float(thb_data)
                self.status_cards["Balance THB"].configure(text=f"{thb_balance:,.2f}")
            except:
                self.status_cards["Balance THB"].configure(text="Connected")

    def update_position_display(self):
        """Update position display"""
        try:
            if self.strategy and self.strategy.position:
                pos = self.strategy.position
                current_time = datetime.now()
                duration = current_time - pos['entry_time']

                # Get current price for P&L calculation
                ticker = self.api_client.get_simple_ticker(pos['symbol'])
                if ticker:
                    current_price = ticker['last_price']
                    entry_price = pos['entry_price']
                    amount = pos['amount']

                    # Calculate P&L
                    buy_fee = self.api_client.calculate_trading_fees(amount, entry_price, "buy")
                    sell_fee = self.api_client.calculate_trading_fees(amount, current_price, "sell")
                    gross_pnl = (current_price - entry_price) * amount
                    net_pnl = gross_pnl - buy_fee - sell_fee
                    pnl_pct = (net_pnl / (amount * entry_price)) * 100

                    mode_indicator = "📝 PAPER" if self.is_paper_trading else "🔥 REAL"

                    position_text = f"{mode_indicator} POSITION\n\n"
                    position_text += f"Symbol: {pos['symbol'].upper()}\n"
                    position_text += f"Amount: {amount:.6f}\n"
                    position_text += f"Entry Price: {entry_price:.2f} THB\n"
                    position_text += f"Current Price: {current_price:.2f} THB\n"
                    position_text += f"Duration: {str(duration).split('.')[0]}\n\n"
                    position_text += f"Gross P&L: {gross_pnl:+.2f} THB\n"
                    position_text += f"Estimated Fees: {buy_fee + sell_fee:.2f} THB\n"
                    position_text += f"Net P&L: {net_pnl:+.2f} THB ({pnl_pct:+.2f}%)\n"

                    self.position_display.delete("1.0", "end")
                    self.position_display.insert("1.0", position_text)
            else:
                mode_indicator = "📝 Paper" if self.is_paper_trading else "🔥 Real"
                self.position_display.delete("1.0", "end")
                self.position_display.insert("1.0", f"{mode_indicator} Trading Mode\nNo active position")

        except Exception as e:
            print(f"Position display error: {e}")

    def update_trading_info_display(self):
        """Update trading information display"""
        mode = "📝 PAPER TRADING" if self.is_paper_trading else "🔥 REAL TRADING"

        info_text = f"{mode} INFORMATION\n\n"

        if self.is_paper_trading:
            info_text += "📝 PAPER TRADING MODE:\n"
            info_text += "• No real money used\n"
            info_text += "• Safe for testing strategies\n"
            info_text += "• Simulated orders and fees\n"
            info_text += "• Perfect for learning\n\n"
        else:
            info_text += "🔥 REAL TRADING MODE:\n"
            info_text += "• USES ACTUAL MONEY!\n"
            info_text += "• Orders placed on Bitkub\n"
            info_text += "• Real fees and slippage\n"
            info_text += "• Can result in real losses\n\n"

        info_text += "🎯 MANUAL TRADING:\n"
        info_text += "• Manual Buy/Sell for direct control\n"
        info_text += "• Emergency Stop halts all activity\n"
        info_text += "• Monitor positions in real-time\n\n"

        info_text += "🤖 AUTOMATED TRADING:\n"
        info_text += "• Configure strategies in Strategies tab\n"
        info_text += "• Enable auto coin selection\n"
        info_text += "• Set risk management parameters\n"
        info_text += "• Monitor and adjust as needed\n\n"

        info_text += "⚠️ IMPORTANT REMINDERS:\n"
        info_text += "• Always start with paper trading\n"
        info_text += "• Test strategies thoroughly\n"
        info_text += "• Use appropriate position sizes\n"
        info_text += "• Monitor market conditions\n"
        info_text += "• Never risk more than you can lose"

        if hasattr(self, 'trading_info_display'):
            self.trading_info_display.delete("1.0", "end")
            self.trading_info_display.insert("1.0", info_text)

    # === History and Statistics ===

    def load_trade_history(self):
        """Load and display trade history"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT timestamp, symbol, side, amount, price, total_thb, pnl, fees, net_pnl, 
                       reason, is_paper, order_id
                FROM trades 
                ORDER BY timestamp DESC 
                LIMIT 100
            ''')

            trades = cursor.fetchall()
            conn.close()

            if trades:
                history_text = f"📜 TRADING HISTORY ({len(trades)} recent trades)\n\n"

                for trade in trades:
                    timestamp, symbol, side, amount, price, total_thb, pnl, fees, net_pnl, reason, is_paper, order_id = trade

                    trade_time = datetime.fromisoformat(timestamp).strftime('%m-%d %H:%M')
                    mode = "📝" if is_paper else "🔥"

                    history_text += f"{trade_time} {mode} | {symbol.upper():<8} | {side.upper():<4} | "
                    history_text += f"{amount:8.4f} @ {price:8.2f} | "
                    if net_pnl is not None:
                        history_text += f"P&L: {net_pnl:+7.2f} | "
                    history_text += f"Fee: {fees:.2f}\n"
                    history_text += f"         Reason: {reason}\n"
                    if not is_paper and order_id != 'PAPER':
                        history_text += f"         Order ID: {order_id}\n"
                    history_text += "\n"

                self.history_display.delete("1.0", "end")
                self.history_display.insert("1.0", history_text)
            else:
                self.history_display.delete("1.0", "end")
                self.history_display.insert("1.0", "No trading history available")

        except Exception as e:
            self.history_display.delete("1.0", "end")
            self.history_display.insert("1.0", f"Error loading history: {e}")

    def show_statistics(self):
        """Show enhanced trading statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Overall stats
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN net_pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
                    SUM(net_pnl) as total_pnl,
                    SUM(fees) as total_fees,
                    AVG(net_pnl) as avg_pnl,
                    MAX(net_pnl) as best_trade,
                    MIN(net_pnl) as worst_trade
                FROM trades
                WHERE net_pnl IS NOT NULL
            ''')

            stats = cursor.fetchone()

            # Separate paper and real trading stats
            cursor.execute('''
                SELECT 
                    is_paper,
                    COUNT(*) as trades,
                    SUM(net_pnl) as pnl,
                    SUM(fees) as fees
                FROM trades
                WHERE net_pnl IS NOT NULL
                GROUP BY is_paper
            ''')

            mode_stats = cursor.fetchall()
            conn.close()

            if stats and stats[0] > 0:
                total_trades, winning_trades, total_pnl, total_fees, avg_pnl, best_trade, worst_trade = stats
                win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

                stats_text = f"📊 ENHANCED TRADING STATISTICS\n\n"
                stats_text += f"OVERALL PERFORMANCE:\n"
                stats_text += f"Total Trades: {total_trades}\n"
                stats_text += f"Winning Trades: {winning_trades} ({win_rate:.1f}%)\n"
                stats_text += f"Total Net P&L: {total_pnl:+.2f} THB\n"
                stats_text += f"Total Fees: {total_fees:.2f} THB\n"
                stats_text += f"Average P&L: {avg_pnl:+.2f} THB\n"
                stats_text += f"Best Trade: {best_trade:+.2f} THB\n"
                stats_text += f"Worst Trade: {worst_trade:+.2f} THB\n\n"

                # Mode breakdown
                stats_text += f"TRADING MODE BREAKDOWN:\n"
                for is_paper, trades, pnl, fees in mode_stats:
                    mode_name = "📝 Paper Trading" if is_paper else "🔥 Real Trading"
                    stats_text += f"{mode_name}:\n"
                    stats_text += f"  Trades: {trades}\n"
                    stats_text += f"  P&L: {pnl:+.2f} THB\n"
                    stats_text += f"  Fees: {fees:.2f} THB\n\n"

                # Performance rating
                if win_rate >= 60 and total_pnl > total_fees:
                    stats_text += "🎯 PERFORMANCE: 🚀 EXCELLENT\n"
                elif win_rate >= 50 and total_pnl > 0:
                    stats_text += "🎯 PERFORMANCE: ✅ GOOD\n"
                elif total_pnl > -total_fees:
                    stats_text += "🎯 PERFORMANCE: ⚠️ FAIR\n"
                else:
                    stats_text += "🎯 PERFORMANCE: ❌ NEEDS IMPROVEMENT\n"

                self.history_display.delete("1.0", "end")
                self.history_display.insert("1.0", stats_text)
            else:
                self.history_display.delete("1.0", "end")
                self.history_display.insert("1.0", "No statistics available - no completed trades")

        except Exception as e:
            self.history_display.delete("1.0", "end")
            self.history_display.insert("1.0", f"Error calculating statistics: {e}")

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
                    SUM(net_pnl) as total_net_pnl,
                    SUM(CASE WHEN is_paper THEN fees ELSE 0 END) as paper_fees,
                    SUM(CASE WHEN NOT is_paper THEN fees ELSE 0 END) as real_fees
                FROM trades
                WHERE fees IS NOT NULL
            ''')

            fee_stats = cursor.fetchone()
            conn.close()

            if fee_stats and fee_stats[0]:
                total_fees, trades, avg_fee, total_volume, net_pnl, paper_fees, real_fees = fee_stats
                fee_rate = (total_fees / total_volume * 100) if total_volume > 0 else 0

                fee_analysis = f"💸 COMPREHENSIVE FEE ANALYSIS\n\n"
                fee_analysis += f"FEE OVERVIEW:\n"
                fee_analysis += f"Total Fees Paid: {total_fees:.2f} THB\n"
                fee_analysis += f"📝 Paper Fees: {paper_fees:.2f} THB\n"
                fee_analysis += f"🔥 Real Fees: {real_fees:.2f} THB\n"
                fee_analysis += f"Total Trades: {trades}\n"
                fee_analysis += f"Average Fee per Trade: {avg_fee:.2f} THB\n"
                fee_analysis += f"Effective Fee Rate: {fee_rate:.3f}%\n\n"

                fee_analysis += f"IMPACT ANALYSIS:\n"
                fee_analysis += f"Total Trading Volume: {total_volume:.2f} THB\n"
                fee_analysis += f"Total Net P&L: {net_pnl:+.2f} THB\n"
                fee_analysis += f"P&L After Fees: {net_pnl:.2f} THB\n"

                if net_pnl != 0:
                    fee_impact = (total_fees / abs(net_pnl) * 100)
                    fee_analysis += f"Fee Impact: {fee_impact:.1f}% of P&L\n\n"

                fee_analysis += f"BITKUB FEE COMPARISON:\n"
                fee_analysis += f"Standard Rate: 0.5% per round trip\n"
                fee_analysis += f"Your Rate: {fee_rate:.3f}%\n"
                fee_analysis += f"Efficiency: {'✅ Good' if fee_rate <= 0.55 else '⚠️ Check execution'}\n\n"

                fee_analysis += f"RECOMMENDATIONS:\n"
                if real_fees > 0:
                    fee_analysis += f"• Real trading fees: {real_fees:.2f} THB\n"
                    fee_analysis += f"• Consider trade size optimization\n"
                    fee_analysis += f"• Monitor execution quality\n"
                else:
                    fee_analysis += f"• Only paper trading fees recorded\n"
                    fee_analysis += f"• Test with real small amounts first\n"

                self.history_display.delete("1.0", "end")
                self.history_display.insert("1.0", fee_analysis)
            else:
                self.history_display.delete("1.0", "end")
                self.history_display.insert("1.0", "No fee data available yet.")

        except Exception as e:
            self.history_display.delete("1.0", "end")
            self.history_display.insert("1.0", f"Error in fee analysis: {e}")

    def clear_history(self):
        """Clear trading history"""
        if messagebox.askyesno("Clear History",
                               "Delete all trading history?\n\n"
                               "This will remove both paper and real trading records.\n"
                               "This cannot be undone."):
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('DELETE FROM trades')
                conn.commit()
                conn.close()

                self.history_display.delete("1.0", "end")
                self.history_display.insert("1.0", "All trading history cleared")
                self.log("🗑️ Trading history cleared")

            except Exception as e:
                messagebox.showerror("Error", f"Failed to clear history: {e}")

    def save_settings(self):
        """Save trading settings"""
        try:
            # Validate inputs
            trade_amount = float(self.amount_var.get())
            max_trades = int(self.max_trades_var.get())
            max_loss = float(self.max_loss_var.get())

            if trade_amount < 100:
                messagebox.showwarning("Error", "Trade amount should be at least 100 THB for realistic trading")
                return

            if max_trades < 1 or max_trades > 20:
                messagebox.showwarning("Error", "Max daily trades must be between 1-20")
                return

            # Update config
            self.config.update({
                'symbol': self.symbol_var.get(),
                'trade_amount_thb': trade_amount,
                'max_daily_trades': max_trades,
                'max_daily_loss': max_loss
            })

            messagebox.showinfo("Success", "Settings saved successfully!")
            self.log(f"⚙️ Settings updated: {self.config['symbol'].upper()}, {trade_amount} THB")

        except ValueError:
            messagebox.showerror("Error", "Invalid input values")

    # === Utility Functions ===

    def log(self, message):
        """Add message to log display"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_entry = f"[{timestamp}] {message}\n"

            self.log_display.insert("end", log_entry)
            self.log_display.see("end")

            # Keep only last 100 lines
            lines = self.log_display.get("1.0", "end").split("\n")
            if len(lines) > 100:
                self.log_display.delete("1.0", f"{len(lines) - 100}.0")

        except Exception as e:
            print(f"Log error: {e}")

    def run(self):
        """🔥 Start the REAL TRADING application"""
        # Reset daily counters at startup
        self.daily_trades = 0
        self.daily_pnl = 0
        self.total_fees_paid = 0

        self.log("🔥 REAL TRADING BOT STARTED")
        self.log("🎬 Sci-Fi Visual System Initialized")
        self.log("🪙 Coin Recommendation System Loaded")
        self.log("💸 Fee-aware strategy enabled")
        self.log("📝 Default: PAPER TRADING mode (SAFE)")
        self.log("⚠️ DANGER: Can switch to REAL trading!")
        self.log("🔒 Always test thoroughly before using real money")

        # Initialize visual system
        if hasattr(self, 'scifi_visual'):
            self.update_scifi_visual_state("idle", "System ready")

        # Initialize system status
        self.status_cards["System Status"].configure(text="Not Connected", text_color="gray")

        # Update trading info display
        self.update_trading_info_display()

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

            # Show warning if real trading was used
            if not self.is_paper_trading:
                messagebox.showinfo("🔥 REAL TRADING SESSION ENDED",
                                    "Real trading session has ended.\n\n"
                                    "Please:\n"
                                    "• Check your Bitkub account\n"
                                    "• Verify all positions\n"
                                    "• Review transaction history\n"
                                    "• Cancel any unwanted open orders")

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
        """Cleanup resources on exit"""
        try:
            # Stop trading
            self.is_trading = False
            self.emergency_stop = True

            # Cleanup visual system
            if hasattr(self, 'scifi_visual') and self.scifi_visual:
                self.scifi_visual.cleanup()

            # Wait for threads to finish
            time.sleep(0.5)

            print("Resources cleaned up successfully")

        except Exception as e:
            print(f"Resource cleanup error: {e}")


if __name__ == "__main__":
    # 🔥 ENHANCED STARTUP WARNING FOR REAL TRADING
    print("\n" + "🔥" * 80)
    print("🔥 REAL TRADING CAPABLE BOT - ENHANCED WITH SCI-FI GRAPHICS")
    print("🔥" * 80)
    print("⚠️ CRITICAL WARNING: THIS BOT CAN USE REAL MONEY! ⚠️")
    print("🔥" * 80)
    print("\n✨ ENHANCED FEATURES:")
    print("• 🔥 REAL MONEY TRADING capability on Bitkub")
    print("• 📝 Safe paper trading mode for testing")
    print("• 🪙 AI-powered coin recommendation system")
    print("• 🎯 Automated best coin selection")
    print("• 📊 Real-time market analysis and scoring")
    print("• 🎬 Advanced Sci-Fi visual status system")
    print("• 💰 Accurate fee calculation and profit optimization")
    print("• 📈 Comprehensive trading statistics")
    print("• 🧪 Advanced testing and debugging tools")
    print("• 🔒 Multiple safety confirmations for real trading")

    print("\n🔥 REAL TRADING FEATURES:")
    print("• Direct integration with Bitkub API")
    print("• Real order placement (buy/sell)")
    print("• Real balance checking and monitoring")
    print("• Actual fee calculation and deduction")
    print("• Real profit/loss tracking")
    print("• Emergency stop with order cancellation")
    print("• Real-time position monitoring")

    print("\n🪙 COIN RECOMMENDATION SYSTEM:")
    print("• AI scoring (0-10) for all Bitkub coins")
    print("• Volume and liquidity analysis")
    print("• Spread and fee impact calculation")
    print("• Volatility assessment for opportunities")
    print("• Real-time market condition evaluation")
    print("• Automatic best coin selection during trading")

    print("\n🎬 SCI-FI VISUAL SYSTEM:")
    print("• 🔵 Idle - System monitoring")
    print("• 🟡 Connecting - API connection")
    print("• 🔴 Analyzing - Market analysis")
    print("• 🟠 Coin Analysis - AI coin evaluation")
    print("• 🟢 Buy Signal - Buy opportunity detected")
    print("• 🔴 Sell Signal - Sell opportunity detected")
    print("• ⚡ Trading - Active order execution")
    print("• ✅ Success - Operation completed successfully")
    print("• ❌ Error - System error or warning")

    print("\n💰 TRADING OPTIMIZATION:")
    print("• Fee-aware strategy (0.25% maker + 0.25% taker)")
    print("• Break-even price calculation")
    print("• Minimum profit margin enforcement")
    print("• Real-time P&L tracking with fees")
    print("• Smart position sizing")
    print("• Risk management with stop-loss/take-profit")

    print("\n🔒 SAFETY FEATURES:")
    print("• Multiple confirmations for real trading")
    print("• Paper trading default mode")
    print("• Emergency stop functionality")
    print("• Daily trade and loss limits")
    print("• Real-time balance monitoring")
    print("• Automatic order cancellation on emergency stop")

    print("\n⚠️ CRITICAL WARNINGS:")
    print("🔥 THIS BOT TRADES WITH REAL MONEY WHEN ENABLED!")
    print("🔥 YOU CAN LOSE REAL FUNDS!")
    print("🔥 ALWAYS START WITH PAPER TRADING!")
    print("🔥 TEST ALL STRATEGIES THOROUGHLY!")
    print("🔥 USE ONLY FUNDS YOU CAN AFFORD TO LOSE!")
    print("🔥 MONITOR ALL TRADING ACTIVITY!")
    print("🔥 SET UP PROPER RISK MANAGEMENT!")
    print("🔥 ENSURE API SECURITY (IP WHITELIST, LIMITED PERMISSIONS)!")

    print("\n📋 RECOMMENDED SETUP:")
    print("1. 🔐 Create dedicated Bitkub trading account")
    print("2. 💰 Fund with small test amount (1,000-5,000 THB)")
    print("3. 🔑 Create API key with limited permissions")
    print("4. 🛡️ Enable IP whitelist for security")
    print("5. 📝 Test extensively with paper trading")
    print("6. 🔥 Start real trading with minimal amounts")
    print("7. 📊 Monitor and adjust strategies")
    print("8. 📈 Scale up gradually as you gain confidence")

    print("\n🎯 TRADING STRATEGY TIPS:")
    print("• Start with 500-1000 THB per trade")
    print("• Use stop-loss (1-2%) and take-profit (2-3%)")
    print("• Enable auto coin selection for best opportunities")
    print("• Monitor fee impact on smaller trades")
    print("• Limit daily trades to 3-5 maximum")
    print("• Never risk more than 5% of account per trade")

    print("\n⚖️ DISCLAIMER:")
    print("• You are fully responsible for all trading decisions")
    print("• This software is provided 'as-is' without warranty")
    print("• Past performance does not guarantee future results")
    print("• Cryptocurrency trading involves significant risk")
    print("• The developers are not responsible for any losses")
    print("• Always consult financial advisors if needed")

    print("\n" + "🔥" * 80)
    print("🔥 DO YOU UNDERSTAND THE RISKS AND FEATURES? 🔥")
    print("🔥" * 80)

    # Enhanced confirmation process
    print("\nThis bot includes:")
    print("✅ Paper trading (safe testing)")
    print("🔥 Real trading (actual money)")
    print("🪙 AI coin recommendations")
    print("🎬 Sci-Fi visual effects")
    print("💸 Fee optimization")
    print("📊 Performance tracking")

    response1 = input("\n1. Do you understand this bot can use REAL money? (yes/no): ")
    if response1.lower() != 'yes':
        print("❌ Exiting. Please understand the risks before using this bot.")
        exit()

    response2 = input("2. Will you start with PAPER trading to test? (yes/no): ")
    if response2.lower() != 'yes':
        print("⚠️ WARNING: You should always test with paper trading first!")
        response2b = input("   Continue anyway? (yes/no): ")
        if response2b.lower() != 'yes':
            print("❌ Exiting. Please test with paper trading first.")
            exit()

    response3 = input("3. Do you accept full responsibility for all trading? (yes/no): ")
    if response3.lower() != 'yes':
        print("❌ Exiting. You must accept responsibility for your trading.")
        exit()

    response4 = input("4. Are you using funds you can afford to lose? (yes/no): ")
    if response4.lower() != 'yes':
        print("❌ Exiting. Only trade with money you can afford to lose.")
        exit()

    print("\n🚀 Starting Enhanced Real Trading Bot...")
    print("🔒 Remember: Start with paper trading!")
    print("💡 Test all features before using real money!")
    print("📞 Support: Check Bitkub API documentation for issues")

    app = ImprovedTradingBot()
    try:
        app.run()
    except KeyboardInterrupt:
        print("\n🛑 Bot interrupted by user")
        app.cleanup_resources()
    except Exception as e:
        print(f"\n❌ Bot crashed: {e}")
        app.cleanup_resources()
    finally:
        print("🔚 Bot session ended")
        print("💡 Check your Bitkub account if you used real trading")
        print("📊 Review the trading history in the app")
        print("🔒 Consider changing API keys if needed")
