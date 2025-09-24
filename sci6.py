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


import json
import time
import threading
from datetime import datetime, timedelta
import sqlite3
import numpy as np
from collections import deque
import random
import logging


# === Full Auto Trading System Classes ===

class AIDecisionEngine:
    """🧠 AI Decision Making Engine สำหรับ Full Auto Trading"""

    def __init__(self):
        self.decision_weights = {
            'technical_score': 0.3,
            'volume_momentum': 0.2,
            'market_sentiment': 0.2,
            'risk_reward_ratio': 0.15,
            'coin_stability': 0.15
        }

        # Advanced parameters
        self.volatility_threshold = 0.15  # 15% volatility limit
        self.volume_surge_threshold = 1.5  # 50% above average volume
        self.rsi_oversold = 25
        self.rsi_overbought = 75

    def make_trading_decision(self, coin_data, strategy_context, current_positions, balance):
        """ตัดสินใจเทรดด้วย AI หลายมิติ"""

        # วิเคราะห์หลายมิติ
        technical_score = self.analyze_technical_indicators(coin_data)
        volume_score = self.analyze_volume_pattern(coin_data)
        sentiment_score = self.analyze_market_sentiment(coin_data)
        risk_score = self.calculate_risk_reward_ratio(coin_data, balance)
        stability_score = self.analyze_coin_stability(coin_data)

        # คำนวณคะแนนรวม
        total_score = (
                technical_score * self.decision_weights['technical_score'] +
                volume_score * self.decision_weights['volume_momentum'] +
                sentiment_score * self.decision_weights['market_sentiment'] +
                risk_score * self.decision_weights['risk_reward_ratio'] +
                stability_score * self.decision_weights['coin_stability']
        )

        # ตัดสินใจพร้อมเหตุผล
        action, confidence = self.determine_action(total_score, coin_data, current_positions)

        return {
            'action': action,
            'confidence': confidence,
            'total_score': total_score,
            'scores': {
                'technical': technical_score,
                'volume': volume_score,
                'sentiment': sentiment_score,
                'risk_reward': risk_score,
                'stability': stability_score
            },
            'reasoning': self.generate_reasoning(total_score, action, coin_data),
            'recommended_amount': self.calculate_position_size(balance, total_score, risk_score)
        }

    def analyze_technical_indicators(self, coin_data):
        """วิเคราะห์ Technical Indicators ขั้นสูง"""
        score = 5.0  # Base score

        try:
            # RSI Analysis
            if hasattr(coin_data, 'rsi') and coin_data.rsi:
                if 20 <= coin_data.rsi <= 30:  # Oversold zone
                    score += 2.5
                elif 70 <= coin_data.rsi <= 80:  # Overbought zone
                    score -= 1.5
                elif 40 <= coin_data.rsi <= 60:  # Neutral zone
                    score += 1.0

            # Price momentum
            if hasattr(coin_data, 'price_change_24h'):
                change_24h = abs(coin_data.price_change_24h)
                if 2 <= change_24h <= 8:  # Good volatility
                    score += 1.5
                elif change_24h > 15:  # Too volatile
                    score -= 2.0

            # Volume confirmation
            if hasattr(coin_data, 'volume_24h') and coin_data.volume_24h > 1000000:
                score += 1.0

        except Exception as e:
            print(f"Technical analysis error: {e}")

        return max(0, min(10, score))

    def analyze_volume_pattern(self, coin_data):
        """วิเคราะห์รูปแบบ Volume"""
        score = 5.0

        try:
            if hasattr(coin_data, 'volume_24h') and hasattr(coin_data, 'volume_avg'):
                volume_ratio = coin_data.volume_24h / max(coin_data.volume_avg, 1)

                if volume_ratio > 2.0:  # Volume surge
                    score += 3.0
                elif volume_ratio > 1.5:
                    score += 2.0
                elif volume_ratio > 1.2:
                    score += 1.0
                elif volume_ratio < 0.5:  # Low volume
                    score -= 2.0
            else:
                # Fallback: basic volume check
                if hasattr(coin_data, 'volume_24h'):
                    if coin_data.volume_24h > 50000000:  # >50M THB
                        score += 2.0
                    elif coin_data.volume_24h > 10000000:  # >10M THB
                        score += 1.0
                    elif coin_data.volume_24h < 1000000:  # <1M THB
                        score -= 2.0

        except Exception as e:
            print(f"Volume analysis error: {e}")

        return max(0, min(10, score))

    def analyze_market_sentiment(self, coin_data):
        """วิเคราะห์ Market Sentiment"""
        score = 5.0

        try:
            # Market cap trend
            if hasattr(coin_data, 'market_cap_change'):
                if coin_data.market_cap_change > 5:  # Growing market cap
                    score += 2.0
                elif coin_data.market_cap_change < -5:  # Declining market cap
                    score -= 1.5

            # Trading pairs activity
            if hasattr(coin_data, 'trading_pairs') and coin_data.trading_pairs > 3:
                score += 1.0

            # Time-based sentiment
            current_hour = datetime.now().hour
            if 9 <= current_hour <= 17:  # Business hours - higher activity
                score += 0.5
            elif 22 <= current_hour or current_hour <= 6:  # Night time - lower activity
                score -= 0.5

        except Exception as e:
            print(f"Sentiment analysis error: {e}")

        return max(0, min(10, score))

    def calculate_risk_reward_ratio(self, coin_data, balance):
        """คำนวณอัตราส่วนความเสี่ยงต่อผลตอบแทน"""
        score = 5.0

        try:
            # Volatility-based risk
            if hasattr(coin_data, 'price_change_24h'):
                volatility = abs(coin_data.price_change_24h)
                if volatility < 5:  # Low risk
                    score += 2.0
                elif volatility > 15:  # High risk
                    score -= 2.0

            # Liquidity risk
            if hasattr(coin_data, 'spread_pct'):
                if coin_data.spread_pct < 0.5:  # Low spread
                    score += 1.5
                elif coin_data.spread_pct > 2.0:  # High spread
                    score -= 2.0

            # Position size relative to balance
            recommended_size = min(balance * 0.1, 1000)  # Max 10% of balance or 1000 THB
            if balance > recommended_size * 10:  # Good balance cushion
                score += 1.0
            elif balance < recommended_size * 2:  # Tight balance
                score -= 1.5

        except Exception as e:
            print(f"Risk analysis error: {e}")

        return max(0, min(10, score))

    def analyze_coin_stability(self, coin_data):
        """วิเคราะห์ความเสถียรของเหรียญ"""
        score = 5.0

        try:
            # Price stability over time
            if hasattr(coin_data, 'price_volatility_7d'):
                if coin_data.price_volatility_7d < 20:  # Stable
                    score += 2.0
                elif coin_data.price_volatility_7d > 50:  # Very volatile
                    score -= 2.0

            # Market presence
            if hasattr(coin_data, 'symbol'):
                major_coins = ['THB_BTC', 'THB_ETH', 'THB_BNB', 'THB_ADA', 'THB_XRP']
                if coin_data.symbol in major_coins:
                    score += 1.5

            # Trading history
            if hasattr(coin_data, 'days_active') and coin_data.days_active > 365:
                score += 1.0

        except Exception as e:
            print(f"Stability analysis error: {e}")

        return max(0, min(10, score))

    def determine_action(self, total_score, coin_data, current_positions):
        """กำหนด Action และ Confidence"""

        # Base decision thresholds
        if total_score >= 7.5:
            action = 'BUY'
            confidence = min(95, int(total_score * 10))
        elif total_score <= 3.0:
            action = 'SELL'
            confidence = min(95, int((10 - total_score) * 10))
        else:
            action = 'HOLD'
            confidence = 50

        # Override logic for existing positions
        if len(current_positions) >= 3:  # Too many positions
            if action == 'BUY':
                action = 'HOLD'
                confidence = 30

        # Market condition overrides
        current_hour = datetime.now().hour
        if current_hour < 6 or current_hour > 22:  # Night time - be conservative
            if action == 'BUY':
                confidence = max(0, confidence - 20)
                if confidence < 60:
                    action = 'HOLD'

        return action, confidence

    def calculate_position_size(self, balance, total_score, risk_score):
        """คำนวณขนาด Position ที่เหมาะสม"""

        # Base position size (5-15% of balance)
        base_pct = 0.10  # 10%

        # Adjust based on confidence
        if total_score >= 8:
            multiplier = 1.5  # Increase position
        elif total_score >= 6:
            multiplier = 1.0  # Normal position
        else:
            multiplier = 0.5  # Reduce position

        # Adjust based on risk
        if risk_score >= 7:
            risk_multiplier = 1.2  # Low risk - increase
        elif risk_score <= 4:
            risk_multiplier = 0.6  # High risk - reduce
        else:
            risk_multiplier = 1.0

        # Calculate final amount
        position_pct = base_pct * multiplier * risk_multiplier
        position_amount = balance * position_pct

        # Apply limits
        max_amount = min(balance * 0.20, 2000)  # Max 20% or 2000 THB
        min_amount = 100  # Minimum 100 THB

        return max(min_amount, min(position_amount, max_amount))

    def generate_reasoning(self, total_score, action, coin_data):
        """สร้างเหตุผลการตัดสินใจ"""
        reasoning = []

        if action == 'BUY':
            reasoning.append(f"Strong signals detected (Score: {total_score:.1f}/10)")
            if hasattr(coin_data, 'rsi') and coin_data.rsi < 30:
                reasoning.append("RSI in oversold territory")
            if hasattr(coin_data, 'volume_24h') and coin_data.volume_24h > 10000000:
                reasoning.append("High volume activity")

        elif action == 'SELL':
            reasoning.append(f"Weak market conditions (Score: {total_score:.1f}/10)")
            if hasattr(coin_data, 'rsi') and coin_data.rsi > 70:
                reasoning.append("RSI in overbought territory")

        else:  # HOLD
            reasoning.append(f"Mixed signals (Score: {total_score:.1f}/10)")
            reasoning.append("Waiting for clearer market direction")

        return " | ".join(reasoning)


class SmartCoinSelector:
    """🪙 ระบบเลือกเหรียญอัจฉริยะ"""

    def __init__(self, api_client, coin_recommender=None):
        self.api_client = api_client
        self.coin_recommender = coin_recommender
        self.market_analyzer = MarketAnalyzer()

        # Coin categories for different market conditions
        self.coin_categories = {
            'STABLE': ['THB_BTC', 'THB_ETH', 'THB_USDT', 'THB_USDC'],
            'GROWTH': ['THB_ADA', 'THB_DOT', 'THB_SOL', 'THB_AVAX', 'THB_MATIC'],
            'VOLATILE': ['THB_DOGE', 'THB_SHIB', 'THB_MANA', 'THB_SAND'],
            'DEFI': ['THB_UNI', 'THB_LINK', 'THB_AAVE', 'THB_COMP']
        }

    def select_best_coin_for_current_market(self, balance=1000):
        """เลือกเหรียญที่ดีที่สุดตามสภาพตลาดปัจจุบัน"""

        try:
            # วิเคราะห์สภาพตลาด
            market_condition = self.market_analyzer.get_current_market_condition()

            # เลือกกลุ่มเหรียญตามสภาพตลาด
            candidate_coins = self.get_candidate_coins(market_condition)

            # ใช้ Coin Recommender ถ้ามี
            if self.coin_recommender:
                analyzed_coins = []
                for coin in candidate_coins[:10]:  # จำกัดที่ 10 เหรียญ
                    analysis = self.coin_recommender.analyze_single_coin(coin, balance)
                    if analysis:
                        analyzed_coins.append(analysis)

                if analyzed_coins:
                    # เรียงตาม AI Score
                    analyzed_coins.sort(key=lambda x: x['ai_score'], reverse=True)
                    best = analyzed_coins[0]

                    return {
                        'symbol': best['symbol'],
                        'score': best['ai_score'],
                        'market_condition': market_condition,
                        'reasoning': f"AI selected based on {market_condition} market (Score: {best['ai_score']:.1f})",
                        'price': best['price'],
                        'volume_24h': best['volume_24h']
                    }

            # Fallback: simple selection
            best_coin = self.simple_coin_selection(candidate_coins, balance)

            return {
                'symbol': best_coin,
                'score': 6.0,  # Default score
                'market_condition': market_condition,
                'reasoning': f"Selected based on {market_condition} market condition",
                'price': 0,
                'volume_24h': 0
            }

        except Exception as e:
            print(f"Coin selection error: {e}")
            return {
                'symbol': 'THB_BTC',  # Safe fallback
                'score': 5.0,
                'market_condition': 'UNKNOWN',
                'reasoning': f"Fallback selection due to error: {str(e)[:50]}",
                'price': 0,
                'volume_24h': 0
            }

    def get_candidate_coins(self, market_condition):
        """เลือกเหรียญตามสภาพตลาด"""

        if market_condition == 'BULLISH':
            # ตลาดดี - เลือกเหรียญ growth และ volatile
            return self.coin_categories['GROWTH'] + self.coin_categories['VOLATILE'][:3]

        elif market_condition == 'BEARISH':
            # ตลาดแย่ - เลือกเหรียญ stable
            return self.coin_categories['STABLE'] + self.coin_categories['DEFI'][:2]

        else:  # SIDEWAYS or UNKNOWN
            # ตลาดนิ่ง - เลือกเหรียญหลักและ DeFi
            return self.coin_categories['STABLE'][:2] + self.coin_categories['GROWTH'][:3] + self.coin_categories[
                                                                                                 'DEFI'][:2]

    def simple_coin_selection(self, candidate_coins, balance):
        """เลือกเหรียญแบบง่าย"""

        # ให้ความสำคัญกับเหรียญหลัก
        priority_coins = ['THB_BTC', 'THB_ETH', 'THB_ADA']

        for coin in priority_coins:
            if coin in candidate_coins:
                return coin

        # ถ้าไม่มีเหรียญหลัก ส่งคืนตัวแรก
        return candidate_coins[0] if candidate_coins else 'THB_BTC'


class MarketAnalyzer:
    """📊 ระบบวิเคราะห์ภาวะตลาด"""

    def __init__(self):
        self.market_data = {}
        self.last_analysis_time = 0

    def get_current_market_condition(self):
        """วิเคราะห์สภาพตลาดปัจจุบัน"""

        # Cache analysis for 5 minutes
        if time.time() - self.last_analysis_time < 300:
            return getattr(self, 'cached_condition', 'SIDEWAYS')

        try:
            # วิเคราะห์จากหลายปัจจัย
            time_factor = self.analyze_time_factor()
            volume_factor = self.analyze_volume_factor()
            volatility_factor = self.analyze_volatility_factor()

            # รวมคะแนน
            total_score = (time_factor + volume_factor + volatility_factor) / 3

            if total_score >= 6.5:
                condition = 'BULLISH'
            elif total_score <= 4.5:
                condition = 'BEARISH'
            else:
                condition = 'SIDEWAYS'

            # Cache result
            self.cached_condition = condition
            self.last_analysis_time = time.time()

            return condition

        except Exception as e:
            print(f"Market analysis error: {e}")
            return 'SIDEWAYS'  # Safe default

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

        # สุ่มค่าเพื่อจำลอง (ในการใช้งานจริงต้องเปลี่ยน)
        random_volume_trend = random.uniform(0, 10)
        return random_volume_trend

    def analyze_volatility_factor(self):
        """วิเคราะห์ปัจจัยความผันผวน"""
        # Mock implementation - ในระบบจริงจะวิเคราะห์ volatility จริง

        # สุ่มค่าเพื่อจำลอง (ในการใช้งานจริงต้องเปลี่ยน)
        random_volatility = random.uniform(0, 10)
        return random_volatility


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
                    positions_count INTEGER,
                    reasoning TEXT,
                    market_condition TEXT,
                    elapsed_hours REAL,
                    raw_data TEXT,
                    profit_target REAL,
                    stop_loss REAL,
                    execution_result TEXT,
                    actual_pnl REAL
                )
            ''')

            # Performance tracking table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trading_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE,
                    start_time TEXT,
                    end_time TEXT,
                    initial_balance REAL,
                    final_balance REAL,
                    total_trades INTEGER,
                    winning_trades INTEGER,
                    total_pnl REAL,
                    max_drawdown REAL,
                    target_profit_pct REAL,
                    max_loss_pct REAL,
                    session_duration_hours REAL,
                    stop_reason TEXT,
                    ai_decisions_count INTEGER,
                    avg_confidence REAL
                )
            ''')

            conn.commit()
            conn.close()

        except Exception as e:
            print(f"Database init error: {e}")

    def save_decision(self, log_entry, session_id=None):
        """บันทึก Decision ลง Database และไฟล์"""
        try:
            # บันทึกลง Database
            self.save_to_database(log_entry, session_id)

            # บันทึกลงไฟล์ JSON
            self.save_to_file(log_entry)

        except Exception as e:
            print(f"Decision log save error: {e}")

    def save_to_database(self, log_entry, session_id=None):
        """บันทึกลง Database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # แยกข้อมูลจาก log_entry
            data = log_entry.get('data', {})
            decision = data.get('decision', {})
            scores = decision.get('scores', {})

            cursor.execute('''
                INSERT INTO full_auto_decisions 
                (timestamp, session_id, decision_type, coin_symbol, action, confidence,
                 technical_score, volume_score, sentiment_score, risk_score, stability_score,
                 total_score, balance, position_size, positions_count, reasoning, 
                 market_condition, elapsed_hours, raw_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                log_entry.get('timestamp'),
                session_id or 'default',
                log_entry.get('type'),
                data.get('coin', {}).get('symbol', ''),
                decision.get('action', ''),
                decision.get('confidence', 0),
                scores.get('technical', 0),
                scores.get('volume', 0),
                scores.get('sentiment', 0),
                scores.get('risk_reward', 0),
                scores.get('stability', 0),
                decision.get('total_score', 0),
                log_entry.get('balance', 0),
                decision.get('recommended_amount', 0),
                log_entry.get('positions', 0),
                decision.get('reasoning', ''),
                data.get('market_condition', ''),
                log_entry.get('elapsed_hours', 0),
                json.dumps(data)
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            print(f"Database save error: {e}")

    def save_to_file(self, log_entry):
        """บันทึกลงไฟล์ JSON"""
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False, indent=2) + '\n')
        except Exception as e:
            print(f"File save error: {e}")

    def save_trading_session(self, session_data):
        """บันทึกข้อมูล Trading Session"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO trading_sessions
                (session_id, start_time, end_time, initial_balance, final_balance,
                 total_trades, winning_trades, total_pnl, max_drawdown,
                 target_profit_pct, max_loss_pct, session_duration_hours,
                 stop_reason, ai_decisions_count, avg_confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session_data.get('session_id'),
                session_data.get('start_time'),
                session_data.get('end_time'),
                session_data.get('initial_balance', 0),
                session_data.get('final_balance', 0),
                session_data.get('total_trades', 0),
                session_data.get('winning_trades', 0),
                session_data.get('total_pnl', 0),
                session_data.get('max_drawdown', 0),
                session_data.get('target_profit_pct', 0),
                session_data.get('max_loss_pct', 0),
                session_data.get('session_duration_hours', 0),
                session_data.get('stop_reason', ''),
                session_data.get('ai_decisions_count', 0),
                session_data.get('avg_confidence', 0)
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            print(f"Session save error: {e}")


class PerformanceAnalyzer:
    """📊 ระบบวิเคราะห์ผลการเทรดขั้นสูง"""

    def __init__(self, db_path="full_auto_trading_decisions.db"):
        self.db_path = db_path

    def analyze_trading_session(self, session_id=None, start_time=None):
        """วิเคราะห์ผลการเทรดครบวงจร"""

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Query ข้อมูล Decision
            if session_id:
                cursor.execute('''
                    SELECT * FROM full_auto_decisions 
                    WHERE session_id = ?
                    ORDER BY timestamp
                ''', (session_id,))
            elif start_time:
                cursor.execute('''
                    SELECT * FROM full_auto_decisions 
                    WHERE timestamp >= ?
                    ORDER BY timestamp
                ''', (start_time,))
            else:
                cursor.execute('''
                    SELECT * FROM full_auto_decisions 
                    ORDER BY timestamp DESC 
                    LIMIT 1000
                ''')

            decisions = cursor.fetchall()

            # Query session data
            if session_id:
                cursor.execute('''
                    SELECT * FROM trading_sessions 
                    WHERE session_id = ?
                ''', (session_id,))
                session_data = cursor.fetchone()
            else:
                session_data = None

            conn.close()

            if not decisions:
                return {"error": "No decision data found"}

            # Comprehensive analysis
            analysis = {
                "basic_stats": self.calculate_basic_stats(decisions),
                "decision_analysis": self.analyze_decision_patterns(decisions),
                "performance_metrics": self.calculate_performance_metrics(decisions, session_data),
                "ai_effectiveness": self.analyze_ai_effectiveness(decisions),
                "time_analysis": self.analyze_time_patterns(decisions),
                "coin_analysis": self.analyze_coin_performance(decisions),
                "risk_analysis": self.analyze_risk_patterns(decisions),
                "recommendations": self.generate_recommendations(decisions),
                "session_summary": self.create_session_summary(session_data) if session_data else None
            }

            return analysis

        except Exception as e:
            return {"error": f"Analysis failed: {e}"}

    def calculate_basic_stats(self, decisions):
        """คำนวณสถิติพื้นฐาน"""
        total_decisions = len(decisions)

        action_counts = {}
        confidence_sum = {}
        score_sum = 0

        for decision in decisions:
            action = decision[4]  # action column
            confidence = decision[5] or 0  # confidence column
            total_score = decision[11] or 0  # total_score column

            action_counts[action] = action_counts.get(action, 0) + 1
            confidence_sum[action] = confidence_sum.get(action, 0) + confidence
            score_sum += total_score

        # Calculate averages
        avg_confidence = {}
        for action in action_counts:
            if action_counts[action] > 0:
                avg_confidence[action] = confidence_sum[action] / action_counts[action]

        avg_score = score_sum / total_decisions if total_decisions > 0 else 0

        return {
            "total_decisions": total_decisions,
            "action_breakdown": action_counts,
            "avg_confidence_by_action": avg_confidence,
            "avg_total_score": avg_score,
            "decision_frequency": total_decisions / max(1, self.get_session_duration_hours(decisions))
        }

    def analyze_decision_patterns(self, decisions):
        """วิเคราะห์รูปแบบการตัดสินใจ"""
        patterns = {
            "high_confidence_decisions": [],
            "low_confidence_decisions": [],
            "score_distribution": {},
            "action_sequences": [],
            "decision_consistency": 0
        }

        # Analyze confidence levels
        for decision in decisions:
            confidence = decision[5] or 0
            action = decision[4]
            total_score = decision[11] or 0

            if confidence >= 80:
                patterns["high_confidence_decisions"].append({
                    "action": action,
                    "confidence": confidence,
                    "score": total_score
                })
            elif confidence <= 40:
                patterns["low_confidence_decisions"].append({
                    "action": action,
                    "confidence": confidence,
                    "score": total_score
                })

        # Score distribution
        score_ranges = [(0, 3), (3, 5), (5, 7), (7, 8.5), (8.5, 10)]
        for min_score, max_score in score_ranges:
            range_key = f"{min_score}-{max_score}"
            count = sum(1 for d in decisions if min_score <= (d[11] or 0) < max_score)
            patterns["score_distribution"][range_key] = count

        return patterns

    def calculate_performance_metrics(self, decisions, session_data):
        """คำนวณเมตริกประสิทธิภาพ"""
        if not session_data:
            return {"error": "No session data available"}

        # Extract session data
        initial_balance = session_data[3] or 0
        final_balance = session_data[4] or 0
        total_trades = session_data[5] or 0
        winning_trades = session_data[6] or 0
        total_pnl = session_data[7] or 0

        # Calculate metrics
        roi = ((final_balance - initial_balance) / initial_balance * 100) if initial_balance > 0 else 0
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        avg_pnl_per_trade = total_pnl / total_trades if total_trades > 0 else 0

        return {
            "roi_percentage": roi,
            "win_rate": win_rate,
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": total_trades - winning_trades,
            "total_pnl": total_pnl,
            "avg_pnl_per_trade": avg_pnl_per_trade,
            "initial_balance": initial_balance,
            "final_balance": final_balance
        }

    def analyze_ai_effectiveness(self, decisions):
        """วิเคราะห์ประสิทธิภาพของ AI"""

        # Analyze score components
        score_components = {
            'technical': [],
            'volume': [],
            'sentiment': [],
            'risk_reward': [],
            'stability': []
        }

        for decision in decisions:
            score_components['technical'].append(decision[6] or 0)
            score_components['volume'].append(decision[7] or 0)
            score_components['sentiment'].append(decision[8] or 0)
            score_components['risk_reward'].append(decision[9] or 0)
            score_components['stability'].append(decision[10] or 0)

        # Calculate averages
        avg_scores = {}
        for component, scores in score_components.items():
            if scores:
                avg_scores[component] = sum(scores) / len(scores)

        return {
            "average_component_scores": avg_scores,
            "strongest_component": max(avg_scores, key=avg_scores.get) if avg_scores else None,
            "weakest_component": min(avg_scores, key=avg_scores.get) if avg_scores else None,
            "score_consistency": self.calculate_score_consistency(score_components)
        }

    def analyze_time_patterns(self, decisions):
        """วิเคราะห์รูปแบบตามเวลา"""

        hour_distribution = {}
        day_distribution = {}

        for decision in decisions:
            timestamp = decision[1]  # timestamp column
            try:
                dt = datetime.fromisoformat(timestamp)
                hour = dt.hour
                day = dt.strftime('%A')

                hour_distribution[hour] = hour_distribution.get(hour, 0) + 1
                day_distribution[day] = day_distribution.get(day, 0) + 1

            except Exception:
                continue

        # Find peak hours
        peak_hour = max(hour_distribution, key=hour_distribution.get) if hour_distribution else None
        peak_day = max(day_distribution, key=day_distribution.get) if day_distribution else None

        return {
            "hourly_distribution": hour_distribution,
            "daily_distribution": day_distribution,
            "peak_trading_hour": peak_hour,
            "peak_trading_day": peak_day,
            "total_active_hours": len(hour_distribution)
        }

    def analyze_coin_performance(self, decisions):
        """วิเคราะห์ประสิทธิภาพแต่ละเหรียญ"""

        coin_stats = {}

        for decision in decisions:
            coin = decision[3] or 'Unknown'  # coin_symbol column
            action = decision[4]  # action column
            confidence = decision[5] or 0  # confidence column

            if coin not in coin_stats:
                coin_stats[coin] = {
                    'total_decisions': 0,
                    'buy_decisions': 0,
                    'sell_decisions': 0,
                    'hold_decisions': 0,
                    'avg_confidence': 0,
                    'total_confidence': 0
                }

            coin_stats[coin]['total_decisions'] += 1
            coin_stats[coin]['total_confidence'] += confidence
            coin_stats[coin][f'{action.lower()}_decisions'] += 1

        # Calculate averages
        for coin in coin_stats:
            stats = coin_stats[coin]
            if stats['total_decisions'] > 0:
                stats['avg_confidence'] = stats['total_confidence'] / stats['total_decisions']

        # Sort by activity
        sorted_coins = sorted(coin_stats.items(),
                              key=lambda x: x[1]['total_decisions'],
                              reverse=True)

        return {
            "coin_statistics": dict(sorted_coins),
            "most_traded_coin": sorted_coins[0][0] if sorted_coins else None,
            "total_coins_analyzed": len(coin_stats)
        }

    def generate_recommendations(self, decisions):
        """สร้างข้อเสนะแนะเพื่อปรับปรุง"""
        recommendations = []

        # Analyze confidence levels
        low_confidence_count = sum(1 for d in decisions if (d[5] or 0) < 50)
        if low_confidence_count > len(decisions) * 0.3:
            recommendations.append({
                "type": "CONFIDENCE_IMPROVEMENT",
                "priority": "HIGH",
                "issue": "High percentage of low-confidence decisions",
                "suggestion": "Consider adjusting AI decision weights or adding more indicators",
                "impact": "Better decision quality"
            })

        # Analyze score distribution
        low_score_count = sum(1 for d in decisions if (d[11] or 0) < 4)
        if low_score_count > len(decisions) * 0.25:
            recommendations.append({
                "type": "SCORING_OPTIMIZATION",
                "priority": "MEDIUM",
                "issue": "Many decisions with low total scores",
                "suggestion": "Review and optimize scoring algorithms",
                "impact": "More accurate signal detection"
            })

        return recommendations

    def get_session_duration_hours(self, decisions):
        """คำนวณระยะเวลา session"""
        if len(decisions) < 2:
            return 1

        try:
            first_time = datetime.fromisoformat(decisions[-1][1])  # Oldest
            last_time = datetime.fromisoformat(decisions[0][1])  # Newest
            duration = (last_time - first_time).total_seconds() / 3600
            return max(duration, 0.1)  # Minimum 0.1 hour
        except:
            return 1

    def calculate_score_consistency(self, score_components):
        """คำนวณความสม่ำเสมอของ score"""
        try:
            all_scores = []
            for component_scores in score_components.values():
                all_scores.extend(component_scores)

            if len(all_scores) > 1:
                avg_score = sum(all_scores) / len(all_scores)
                variance = sum((score - avg_score) ** 2 for score in all_scores) / len(all_scores)
                consistency = max(0, 10 - variance)  # Convert to 0-10 scale
                return consistency
            else:
                return 5.0  # Default
        except:
            return 5.0

    def create_session_summary(self, session_data):
        """สร้าง summary ของ session"""
        if not session_data:
            return None

        return {
            "session_id": session_data[1],
            "start_time": session_data[2],
            "end_time": session_data[3],
            "duration_hours": session_data[12] or 0,
            "initial_balance": session_data[4] or 0,
            "final_balance": session_data[5] or 0,
            "roi_percentage": ((session_data[5] or 0) - (session_data[4] or 0)) / max(session_data[4] or 1, 1) * 100,
            "stop_reason": session_data[13] or "Unknown"
        }


class FullAutoTradingEngine:
    """🤖 ระบบเทรดอัตโนมัติแบบ Full Auto ที่สมบูรณ์"""

    def __init__(self, api_client, coin_recommender=None, initial_balance=500):
        self.api_client = api_client
        self.coin_recommender = coin_recommender
        self.initial_balance = initial_balance
        self.current_balance = initial_balance

        # Trading parameters
        self.target_profit_pct = 20  # เป้าหมายกำไร 20%
        self.max_loss_pct = 10  # ขาดทุนสูงสุด 10%
        self.max_trading_hours = 24  # เทรดสูงสุด 24 ชั่วโมง
        self.max_concurrent_positions = 3  # สูงสุด 3 positions
        self.min_trade_interval_minutes = 5  # ห่างการเทรดอย่างน้อย 5 นาที

        # Core components
        self.decision_engine = AIDecisionEngine()
        self.coin_selector = SmartCoinSelector(api_client, coin_recommender)
        self.decision_logger = DecisionLogger()
        self.performance_analyzer = PerformanceAnalyzer()

        # Trading state
        self.is_auto_trading = False
        self.trading_start_time = None
        self.session_id = None
        self.total_trades = 0
        self.winning_trades = 0
        self.current_positions = {}
        self.last_trade_time = None
        self.max_drawdown = 0
        self.peak_balance = initial_balance

        # Decision tracking
        self.decisions_made = 0
        self.total_confidence = 0

    def start_full_auto_trading(self, target_time_hours=24, target_profit_pct=20, max_loss_pct=10):
        """🚀 เริ่มการเทรดอัตโนมัติแบบเต็มรูปแบบ"""

        if self.is_auto_trading:
            return False, "Auto trading already running"

        # Initialize session
        self.session_id = f"auto_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.is_auto_trading = True
        self.trading_start_time = datetime.now()
        self.max_trading_hours = target_time_hours
        self.target_profit_pct = target_profit_pct
        self.max_loss_pct = max_loss_pct

        # Reset counters
        self.total_trades = 0
        self.winning_trades = 0
        self.decisions_made = 0
        self.total_confidence = 0
        self.current_positions = {}
        self.peak_balance = self.current_balance

        # Log session start
        self.log_decision("SESSION_START", {
            "session_id": self.session_id,
            "initial_balance": self.initial_balance,
            "current_balance": self.current_balance,
            "target_profit_pct": self.target_profit_pct,
            "max_loss_pct": self.max_loss_pct,
            "max_hours": target_time_hours,
            "max_positions": self.max_concurrent_positions,
            "start_time": self.trading_start_time.isoformat()
        })

        # เริ่ม Main Trading Loop
        threading.Thread(target=self.main_auto_trading_loop, daemon=True).start()

        return True, f"Full Auto Trading Started! Session: {self.session_id}"

    def main_auto_trading_loop(self):
        """🔄 Main Auto Trading Loop ที่สมบูรณ์"""

        consecutive_errors = 0
        max_consecutive_errors = 5

        print(f"🤖 Starting Full Auto Trading Loop - Session: {self.session_id}")

        while self.is_auto_trading:
            try:
                # 1. ตรวจสอบเงื่อนไขหยุด
                stop_reason = self.should_stop_trading()
                if stop_reason:
                    self.stop_auto_trading(stop_reason)
                    break

                # 2. ตรวจสอบ rate limiting
                if self.last_trade_time:
                    minutes_since_trade = (datetime.now() - self.last_trade_time).total_seconds() / 60
                    if minutes_since_trade < self.min_trade_interval_minutes:
                        time.sleep(30)  # Wait 30 seconds
                        continue

                # 3. อัปเดตสถานะปัจจุบัน
                self.update_current_status()

                # 4. วิเคราะห์ตลาดและเลือกเหรียญ
                selected_coin = self.coin_selector.select_best_coin_for_current_market(
                    self.current_balance
                )

                # 5. ตัดสินใจเทรด
                trading_decision = self.decision_engine.make_trading_decision(
                    coin_data=selected_coin,
                    strategy_context={'session_id': self.session_id},
                    current_positions=self.current_positions,
                    balance=self.current_balance
                )

                # 6. บันทึกการตัดสินใจ
                self.log_decision("TRADING_DECISION", {
                    "coin": selected_coin,
                    "decision": trading_decision,
                    "balance": self.current_balance,
                    "positions_count": len(self.current_positions),
                    "market_condition": selected_coin.get('market_condition', 'UNKNOWN')
                })

                # 7. ดำเนินการเทรด (ถ้าจำเป็น)
                if trading_decision['action'] != 'HOLD':
                    execution_result = self.execute_trading_decision(
                        trading_decision, selected_coin
                    )

                    if execution_result['success']:
                        self.total_trades += 1
                        self.last_trade_time = datetime.now()

                        if execution_result.get('profit', 0) > 0:
                            self.winning_trades += 1

                # 8. จัดการ positions ที่มีอยู่
                self.manage_existing_positions()

                # 9. อัปเดต performance tracking
                self.update_performance_tracking()

                # Reset error counter
                consecutive_errors = 0

                # รอก่อนรอบถัดไป
                time.sleep(30)  # 30 วินาที

            except Exception as e:
                consecutive_errors += 1
                print(f"❌ Trading loop error: {e}")

                self.log_decision("ERROR", {
                    "error": str(e),
                    "consecutive_errors": consecutive_errors,
                    "timestamp": datetime.now().isoformat()
                })

                if consecutive_errors >= max_consecutive_errors:
                    print("❌ Too many consecutive errors, stopping trading")
                    self.stop_auto_trading("TOO_MANY_ERRORS")
                    break

                time.sleep(60)  # รอ 1 นาทีถ้าเกิดข้อผิดพลาด

    def should_stop_trading(self):
        """ตรวจสอบเงื่อนไขการหยุดเทรด"""

        if not self.trading_start_time:
            return "NO_START_TIME"

        # เวลาหมด
        elapsed_hours = (datetime.now() - self.trading_start_time).total_seconds() / 3600
        if elapsed_hours >= self.max_trading_hours:
            return "TIME_LIMIT_REACHED"

        # ถึงเป้าหมายกำไร
        profit_pct = ((self.current_balance - self.initial_balance) / self.initial_balance) * 100
        if profit_pct >= self.target_profit_pct:
            return "PROFIT_TARGET_REACHED"

        # ขาดทุนเกินกำหนด
        if profit_pct <= -self.max_loss_pct:
            return "STOP_LOSS_TRIGGERED"

        # ยอดเงินต่ำเกินไป
        if self.current_balance < self.initial_balance * 0.1:  # เหลือ 10%
            return "INSUFFICIENT_BALANCE"

        return None  # ไม่ต้องหยุด

    def execute_trading_decision(self, decision, coin_data):
        """ดำเนินการเทรดตามการตัดสินใจ"""

        try:
            action = decision['action']
            recommended_amount = decision.get('recommended_amount', 1000)

            # Simulate trading execution
            execution_result = {
                'success': False,
                'action': action,
                'amount': recommended_amount,
                'coin': coin_data.get('symbol', 'UNKNOWN'),
                'profit': 0,
                'error': None
            }

            if action == 'BUY':
                if len(self.current_positions) >= self.max_concurrent_positions:
                    execution_result['error'] = "Max positions reached"
                    return execution_result

                if self.current_balance >= recommended_amount:
                    # Simulate buy execution
                    position_id = f"{coin_data.get('symbol', 'UNK')}_{datetime.now().strftime('%H%M%S')}"

                    self.current_positions[position_id] = {
                        'symbol': coin_data.get('symbol'),
                        'entry_price': coin_data.get('price', 1000),
                        'amount': recommended_amount,
                        'entry_time': datetime.now(),
                        'decision_confidence': decision['confidence'],
                        'target_profit': recommended_amount * 0.025,  # 2.5% target
                        'stop_loss': recommended_amount * 0.015  # 1.5% stop loss
                    }

                    self.current_balance -= recommended_amount
                    execution_result['success'] = True

                    print(f"🟢 BUY executed: {coin_data.get('symbol')} - {recommended_amount} THB")

                else:
                    execution_result['error'] = "Insufficient balance"

            elif action == 'SELL':
                # Find positions to sell
                positions_to_sell = list(self.current_positions.keys())[:1]  # Sell one position

                for pos_id in positions_to_sell:
                    position = self.current_positions[pos_id]

                    # Simulate sell with profit/loss
                    mock_current_price = position['entry_price'] * random.uniform(0.95, 1.05)
                    profit = (mock_current_price - position['entry_price']) * (
                                position['amount'] / position['entry_price'])

                    self.current_balance += position['amount'] + profit
                    execution_result['profit'] = profit
                    execution_result['success'] = True

                    del self.current_positions[pos_id]

                    print(f"🔴 SELL executed: {position['symbol']} - Profit: {profit:.2f} THB")
                    break

            return execution_result

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'action': decision.get('action', 'UNKNOWN')
            }

    def manage_existing_positions(self):
        """จัดการ positions ที่มีอยู่"""

        positions_to_close = []
        current_time = datetime.now()

        for pos_id, position in self.current_positions.items():
            try:
                # ตรวจสอบ time-based exit
                hours_held = (current_time - position['entry_time']).total_seconds() / 3600

                if hours_held >= 12:  # Hold สูงสุด 12 ชั่วโมง
                    positions_to_close.append((pos_id, "TIME_EXIT"))
                    continue

                # Mock current price check
                entry_price = position['entry_price']
                mock_current_price = entry_price * random.uniform(0.9, 1.1)

                current_pnl = (mock_current_price - entry_price) * (position['amount'] / entry_price)
                pnl_pct = current_pnl / position['amount']

                # Take profit
                if pnl_pct >= 0.025:  # 2.5% profit
                    positions_to_close.append((pos_id, "TAKE_PROFIT"))

                # Stop loss
                elif pnl_pct <= -0.015:  # 1.5% loss
                    positions_to_close.append((pos_id, "STOP_LOSS"))

            except Exception as e:
                print(f"Position management error for {pos_id}: {e}")

        # Close positions
        for pos_id, reason in positions_to_close:
            self.close_position(pos_id, reason)

    def close_position(self, position_id, reason):
        """ปิด position"""

        try:
            if position_id not in self.current_positions:
                return

            position = self.current_positions[position_id]

            # Simulate closing
            entry_price = position['entry_price']
            mock_exit_price = entry_price * random.uniform(0.95, 1.05)

            profit = (mock_exit_price - entry_price) * (position['amount'] / entry_price)
            self.current_balance += position['amount'] + profit

            # Log position close
            self.log_decision("POSITION_CLOSED", {
                "position_id": position_id,
                "symbol": position['symbol'],
                "entry_price": entry_price,
                "exit_price": mock_exit_price,
                "amount": position['amount'],
                "profit": profit,
                "reason": reason,
                "hold_duration_hours": (datetime.now() - position['entry_time']).total_seconds() / 3600
            })

            if profit > 0:
                self.winning_trades += 1

            del self.current_positions[position_id]

            print(f"🔄 Position closed: {position['symbol']} - Reason: {reason} - P&L: {profit:+.2f}")

        except Exception as e:
            print(f"Close position error: {e}")

    def update_current_status(self):
        """อัปเดตสถานะปัจจุบัน"""

        # Update peak balance and drawdown
        if self.current_balance > self.peak_balance:
            self.peak_balance = self.current_balance

        current_drawdown = (self.peak_balance - self.current_balance) / self.peak_balance * 100
        if current_drawdown > self.max_drawdown:
            self.max_drawdown = current_drawdown

    def update_performance_tracking(self):
        """อัปเดต performance tracking"""

        self.decisions_made += 1
        # Additional performance tracking logic here

    def stop_auto_trading(self, reason="MANUAL_STOP"):
        """หยุดการเทรดอัตโนมัติ"""

        self.is_auto_trading = False

        # Close all remaining positions
        for pos_id in list(self.current_positions.keys()):
            self.close_position(pos_id, "SESSION_END")

        # Calculate final statistics
        elapsed_hours = (
                                    datetime.now() - self.trading_start_time).total_seconds() / 3600 if self.trading_start_time else 0
        final_pnl = self.current_balance - self.initial_balance
        roi = (final_pnl / self.initial_balance) * 100 if self.initial_balance > 0 else 0
        win_rate = (self.winning_trades / max(self.total_trades, 1)) * 100
        avg_confidence = self.total_confidence / max(self.decisions_made, 1)

        # Log session end
        session_data = {
            "session_id": self.session_id,
            "start_time": self.trading_start_time.isoformat() if self.trading_start_time else "",
            "end_time": datetime.now().isoformat(),
            "initial_balance": self.initial_balance,
            "final_balance": self.current_balance,
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "total_pnl": final_pnl,
            "max_drawdown": self.max_drawdown,
            "target_profit_pct": self.target_profit_pct,
            "max_loss_pct": self.max_loss_pct,
            "session_duration_hours": elapsed_hours,
            "stop_reason": reason,
            "ai_decisions_count": self.decisions_made,
            "avg_confidence": avg_confidence,
            "roi_percentage": roi,
            "win_rate": win_rate
        }

        self.log_decision("SESSION_END", session_data)
        self.decision_logger.save_trading_session(session_data)

        print(f"🏁 Auto Trading Stopped - Reason: {reason}")
        print(
            f"📊 Final Results: Balance: {self.current_balance:.2f} THB, ROI: {roi:+.2f}%, Trades: {self.total_trades}")

    def log_decision(self, decision_type, data):
        """บันทึก Decision Log แบบละเอียด"""

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


# === Integration Functions สำหรับเพิ่มใน Scci5.py ===

def add_full_auto_to_existing_bot(existing_bot_class):
    """
    ฟังก์ชันสำหรับเพิ่ม Full Auto Trading ใน Trading Bot ที่มีอยู่

    วิธีใช้:
    1. เรียกฟังก์ชันนี้ใน __init__ ของ bot ที่มีอยู่
    2. เพิ่ม UI สำหรับ Full Auto
    3. เชื่อมต่อกับ API client ที่มีอยู่
    """

    def setup_full_auto_system(self):
        """เพิ่มระบบ Full Auto เข้าใน Bot ที่มีอยู่"""

        # สร้าง Full Auto Engine
        self.full_auto_engine = None
        self.performance_analyzer = PerformanceAnalyzer()

        # เพิ่ม UI สำหรับ Full Auto
        self.setup_full_auto_ui()

    def setup_full_auto_ui(self):
        """เพิ่ม UI สำหรับ Full Auto Trading"""

        # สร้าง Frame สำหรับ Full Auto Controls
        full_auto_frame = ctk.CTkFrame(self.root)
        full_auto_frame.pack(fill="x", padx=10, pady=10)

        # Title
        ctk.CTkLabel(full_auto_frame, text="🤖 Full Auto Trading System",
                     font=("Arial", 18, "bold")).pack(pady=10)

        # Configuration Frame
        config_frame = ctk.CTkFrame(full_auto_frame)
        config_frame.pack(fill="x", padx=10, pady=10)

        # Initial Balance
        balance_frame = ctk.CTkFrame(config_frame)
        balance_frame.pack(side="left", padx=10)

        ctk.CTkLabel(balance_frame, text="Initial Balance (THB):").pack()
        self.auto_balance_var = ctk.StringVar(value="500")
        ctk.CTkEntry(balance_frame, textvariable=self.auto_balance_var, width=100).pack()

        # Trading Hours
        hours_frame = ctk.CTkFrame(config_frame)
        hours_frame.pack(side="left", padx=10)

        ctk.CTkLabel(hours_frame, text="Trading Hours:").pack()
        self.auto_hours_var = ctk.StringVar(value="24")
        ctk.CTkEntry(hours_frame, textvariable=self.auto_hours_var, width=100).pack()

        # Target Profit
        profit_frame = ctk.CTkFrame(config_frame)
        profit_frame.pack(side="left", padx=10)

        ctk.CTkLabel(profit_frame, text="Target Profit (%):").pack()
        self.auto_profit_var = ctk.StringVar(value="20")
        ctk.CTkEntry(profit_frame, textvariable=self.auto_profit_var, width=100).pack()

        # Max Loss
        loss_frame = ctk.CTkFrame(config_frame)
        loss_frame.pack(side="left", padx=10)

        ctk.CTkLabel(loss_frame, text="Max Loss (%):").pack()
        self.auto_loss_var = ctk.StringVar(value="10")
        ctk.CTkEntry(loss_frame, textvariable=self.auto_loss_var, width=100).pack()

        # Control Buttons
        button_frame = ctk.CTkFrame(full_auto_frame)
        button_frame.pack(pady=20)

        self.start_full_auto_btn = ctk.CTkButton(
            button_frame, text="🚀 Start Full Auto Trading",
            command=self.start_full_auto_trading,
            fg_color="purple", height=50, width=250,
            font=("Arial", 14, "bold")
        )
        self.start_full_auto_btn.pack(side="left", padx=10)

        ctk.CTkButton(
            button_frame, text="📊 Show Performance",
            command=self.show_full_auto_performance,
            fg_color="blue", height=50, width=200
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            button_frame, text="⏹️ Stop Full Auto",
            command=self.stop_full_auto_trading,
            fg_color="red", height=50, width=200
        ).pack(side="left", padx=10)

        # Status Display
        self.full_auto_status_frame = ctk.CTkFrame(full_auto_frame)
        self.full_auto_status_frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(self.full_auto_status_frame, text="📈 Full Auto Status & Logs",
                     font=("Arial", 14, "bold")).pack()

        self.full_auto_display = ctk.CTkTextbox(self.full_auto_status_frame, height=300)
        self.full_auto_display.pack(fill="both", expand=True, padx=10, pady=10)

        # Initial message
        self.full_auto_display.insert("1.0",
                                      "🤖 FULL AUTO TRADING SYSTEM\n\n"
                                      "📋 FEATURES:\n"
                                      "• AI-powered decision making\n"
                                      "• Smart coin selection\n"
                                      "• Automatic risk management\n"
                                      "• Comprehensive logging\n"
                                      "• Performance analytics\n\n"
                                      "🎯 CONFIGURATION:\n"
                                      "• Set initial balance (500-5000 THB recommended)\n"
                                      "• Choose trading duration (1-48 hours)\n"
                                      "• Set profit target (10-50%)\n"
                                      "• Set maximum loss (5-20%)\n\n"
                                      "⚠️ IMPORTANT:\n"
                                      "• Test with paper trading first\n"
                                      "• Monitor system actively\n"
                                      "• Start with small amounts\n"
                                      "• Understand the risks\n\n"
                                      "🚀 Ready to start Full Auto Trading!"
                                      )

    def start_full_auto_trading(self):
        """เริ่ม Full Auto Trading"""
        try:
            if not self.api_client:
                messagebox.showwarning("Error", "Please connect API first")
                return

            # Get configuration
            balance = float(self.auto_balance_var.get())
            hours = float(self.auto_hours_var.get())
            profit_target = float(self.auto_profit_var.get())
            max_loss = float(self.auto_loss_var.get())

            # Validation
            if balance < 100 or balance > 10000:
                messagebox.showwarning("Error", "Balance must be between 100-10,000 THB")
                return

            if hours < 1 or hours > 48:
                messagebox.showwarning("Error", "Trading hours must be between 1-48")
                return

            # Final confirmation
            if not messagebox.askyesno("🤖 START FULL AUTO TRADING",
                                       f"Start Full Auto Trading?\n\n"
                                       f"💰 Balance: {balance:,.0f} THB\n"
                                       f"⏰ Duration: {hours} hours\n"
                                       f"🎯 Target Profit: {profit_target}%\n"
                                       f"⚠️ Max Loss: {max_loss}%\n\n"
                                       f"The system will trade automatically!\n"
                                       f"Continue?"):
                return

            # สร้าง Full Auto Engine
            coin_recommender = getattr(self, 'coin_recommender', None)
            self.full_auto_engine = FullAutoTradingEngine(
                self.api_client,
                coin_recommender,
                balance
            )

            # เริ่มการเทรด
            success, message = self.full_auto_engine.start_full_auto_trading(
                hours, profit_target, max_loss
            )

            if success:
                self.start_full_auto_btn.configure(text="🤖 Full Auto Running...",
                                                   fg_color="orange", state="disabled")
                self.full_auto_display.insert("end", f"\n\n🚀 {message}\n")
                self.full_auto_display.insert("end", f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

                if hasattr(self, 'log'):
                    self.log(f"🤖 Full Auto Started: {balance} THB, {hours}h, {profit_target}% target")

                # เริ่มการอัปเดตสถานะ
                self.start_full_auto_monitoring()

            else:
                self.full_auto_display.insert("end", f"\n❌ {message}\n")
                messagebox.showerror("Error", message)

        except ValueError:
            messagebox.showerror("Error", "Please enter valid numeric values")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start Full Auto: {e}")

    def stop_full_auto_trading(self):
        """หยุด Full Auto Trading"""
        if self.full_auto_engine and self.full_auto_engine.is_auto_trading:
            self.full_auto_engine.stop_auto_trading("MANUAL_STOP")

            self.start_full_auto_btn.configure(text="🚀 Start Full Auto Trading",
                                               fg_color="purple", state="normal")

            self.full_auto_display.insert("end", f"\n⏹️ Full Auto Stopped: {datetime.now().strftime('%H:%M:%S')}\n")

            if hasattr(self, 'log'):
                self.log("⏹️ Full Auto Trading stopped manually")
        else:
            messagebox.showinfo("Info", "Full Auto Trading is not running")

    def start_full_auto_monitoring(self):
        """เริ่มการ monitor สถานะ Full Auto"""

        def monitor_loop():
            while (self.full_auto_engine and
                   self.full_auto_engine.is_auto_trading):
                try:
                    # ดึงสถานะปัจจุบัน
                    summary = self.full_auto_engine.get_session_summary()

                    # อัปเดต display
                    status_text = f"""
📊 FULL AUTO STATUS (Updated: {datetime.now().strftime('%H:%M:%S')})

🔄 Status: {summary['status']}
⏰ Elapsed: {summary['elapsed_hours']:.1f} hours
💰 Balance: {summary['current_balance']:,.2f} THB
📈 P&L: {summary['total_pnl']:+,.2f} THB ({summary['roi_percentage']:+.1f}%)
🎯 Trades: {summary['total_trades']} (Win: {summary['winning_trades']}, Rate: {summary['win_rate']:.1f}%)
📊 Positions: {summary['active_positions']}
📉 Max Drawdown: {summary['max_drawdown']:.1f}%
🧠 Decisions: {summary['decisions_made']}
"""

                    # Update display (ใน thread หลัก)
                    self.root.after(0, lambda: self.update_full_auto_display(status_text))

                    # ตรวจสอบว่าเสร็จสิ้นแล้วหรือไม่
                    if not self.full_auto_engine.is_auto_trading:
                        self.root.after(0, self.on_full_auto_finished)
                        break

                    time.sleep(10)  # อัปเดตทุก 10 วินาที

                except Exception as e:
                    print(f"Full Auto monitoring error: {e}")
                    break

        threading.Thread(target=monitor_loop, daemon=True).start()

    def update_full_auto_display(self, status_text):
        """อัปเดต Full Auto display"""
        try:
            # Clear และแสดงสถานะใหม่
            self.full_auto_display.delete("1.0", "end")
            self.full_auto_display.insert("1.0", status_text)
        except Exception as e:
            print(f"Display update error: {e}")

    def on_full_auto_finished(self):
        """เมื่อ Full Auto เสร็จสิ้น"""
        try:
            # Reset button
            self.start_full_auto_btn.configure(text="🚀 Start Full Auto Trading",
                                               fg_color="purple", state="normal")

            # Show final results
            if self.full_auto_engine:
                summary = self.full_auto_engine.get_session_summary()

                result_message = f"""🏁 FULL AUTO COMPLETED!

💰 Final Balance: {summary['current_balance']:,.2f} THB
📈 Total P&L: {summary['total_pnl']:+,.2f} THB
📊 ROI: {summary['roi_percentage']:+.2f}%
🎯 Total Trades: {summary['total_trades']}
✅ Winning Trades: {summary['winning_trades']}
📈 Win Rate: {summary['win_rate']:.1f}%
⏰ Duration: {summary['elapsed_hours']:.1f} hours
"""

                self.full_auto_display.insert("end", f"\n{result_message}")

                # Show popup with results
                messagebox.showinfo("🏁 Full Auto Completed", result_message)

                if hasattr(self, 'log'):
                    self.log(f"🏁 Full Auto completed - ROI: {summary['roi_percentage']:+.2f}%")

        except Exception as e:
            print(f"Full Auto finish error: {e}")

    def show_full_auto_performance(self):
        """แสดงผลการวิเคราะห์ Full Auto"""
        if not self.performance_analyzer:
            messagebox.showinfo("Info", "Performance analyzer not available")
            return

        try:
            # วิเคราะห์ผลการเทรด
            analysis = self.performance_analyzer.analyze_trading_session()

            if "error" in analysis:
                messagebox.showinfo("Analysis", f"No data available: {analysis['error']}")
                return

            # สร้างรายงาน
            basic_stats = analysis.get('basic_stats', {})
            performance_metrics = analysis.get('performance_metrics', {})
            ai_effectiveness = analysis.get('ai_effectiveness', {})

            report = f"""📊 FULL AUTO PERFORMANCE ANALYSIS

📈 BASIC STATISTICS:
• Total Decisions: {basic_stats.get('total_decisions', 0)}
• Decision Frequency: {basic_stats.get('decision_frequency', 0):.1f} per hour
• Average Score: {basic_stats.get('avg_total_score', 0):.1f}/10

🎯 PERFORMANCE METRICS:
• ROI: {performance_metrics.get('roi_percentage', 0):+.2f}%
• Win Rate: {performance_metrics.get('win_rate', 0):.1f}%
• Total Trades: {performance_metrics.get('total_trades', 0)}
• Avg P&L per Trade: {performance_metrics.get('avg_pnl_per_trade', 0):+.2f} THB

🧠 AI EFFECTIVENESS:
• Strongest Component: {ai_effectiveness.get('strongest_component', 'N/A')}
• Weakest Component: {ai_effectiveness.get('weakest_component', 'N/A')}
• Score Consistency: {ai_effectiveness.get('score_consistency', 0):.1f}/10

💡 RECOMMENDATIONS:
"""

            recommendations = analysis.get('recommendations', [])
            for i, rec in enumerate(recommendations, 1):
                report += f"{i}. {rec.get('suggestion', 'No recommendations')}\n"

            # แสดงในหน้าต่างใหม่
            self.show_performance_window(report)

        except Exception as e:
            messagebox.showerror("Error", f"Performance analysis failed: {e}")

    def show_performance_window(self, report):
        """แสดงหน้าต่างรายงานผลการเทรด"""

        # สร้างหน้าต่างใหม่
        perf_window = ctk.CTkToplevel(self.root)
        perf_window.title("📊 Full Auto Performance Analysis")
        perf_window.geometry("800x600")
        perf_window.grab_set()

        # Title
        ctk.CTkLabel(perf_window, text="📊 Full Auto Performance Analysis",
                     font=("Arial", 20, "bold")).pack(pady=20)

        # Report display
        report_display = ctk.CTkTextbox(perf_window, height=400, width=750)
        report_display.pack(fill="both", expand=True, padx=20, pady=10)
        report_display.insert("1.0", report)

        # Close button
        ctk.CTkButton(perf_window, text="✅ Close",
                      command=perf_window.destroy,
                      height=40, width=150).pack(pady=20)

    # เพิ่ม methods เข้าไปใน class
    existing_bot_class.setup_full_auto_system = setup_full_auto_system
    existing_bot_class.setup_full_auto_ui = setup_full_auto_ui
    existing_bot_class.start_full_auto_trading = start_full_auto_trading
    existing_bot_class.stop_full_auto_trading = stop_full_auto_trading
    existing_bot_class.start_full_auto_monitoring = start_full_auto_monitoring
    existing_bot_class.update_full_auto_display = update_full_auto_display
    existing_bot_class.on_full_auto_finished = on_full_auto_finished
    existing_bot_class.show_full_auto_performance = show_full_auto_performance
    existing_bot_class.show_performance_window = show_performance_window


# === วิธีการใช้งานใน Scci5.py ===

"""
วิธีเพิ่ม Full Auto System เข้าใน Scci5.py:

1. Copy โค้ดทั้งหมดด้านบนใส่ในไฟล์ Scci5.py (ก่อน class หลัก)

2. ใน __init__ ของ ImprovedTradingBot เพิ่ม:

   def __init__(self):
       # ... โค้ดเดิม ...

       # เพิ่ม Full Auto System
       add_full_auto_to_existing_bot(ImprovedTradingBot)
       self.setup_full_auto_system()

3. ใน setup_ui() เพิ่มการเรียก setup_full_auto_ui():

   def setup_ui(self):
       # ... โค้ดเดิม ...

       # เพิ่ม Full Auto UI
       self.setup_full_auto_ui()

4. รัน Scci5.py จะมี Full Auto Trading System เพิ่มขึ้นมา!

คุณสมบัติที่จะได้:
✅ AI Decision Making Engine
✅ Smart Coin Selection  
✅ Automatic Risk Management
✅ Comprehensive Logging
✅ Performance Analytics
✅ Real-time Monitoring
✅ Session Management
✅ Detailed Reporting
"""

class ImprovedTradingBot:
    """🔥 ENHANCED TRADING BOT WITH REAL MONEY TRADING CAPABILITY"""

    def __init__(self):

        from license_simple import check_license

        print("=== 🔐 ระบบตรวจสอบ License ===")
        user_name = input("ชื่อผู้ใช้: ")
        license_key = input("License Key: ")

        if not check_license(license_key, user_name):
            print("🚫 ไม่สามารถใช้งาน Trading Bot ได้")
            exit()

        print(f"🎉 ยินดีต้อนรับ {user_name}!")

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
        # เพิ่ม Full Auto System
        add_full_auto_to_existing_bot(ImprovedTradingBot)
        self.setup_full_auto_system()


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
        # ... โค้ดเดิมทั้งหมด ...

        # เพิ่มบรรทัดนี้ท้ายสุด
        self.setup_full_auto_ui()

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

    # === แก้ไขเฉพาะ Method toggle_real_trading ===

    def toggle_real_trading(self):
        """Toggle between paper and real trading - FIX MODE DISPLAY"""

        # ✅ อัปเดต state ให้ถูกต้อง
        switch_is_on = self.real_trading_var.get()  # True = switch เปิด (Real), False = switch ปิด (Paper)
        self.is_paper_trading = not switch_is_on  # กลับค่า: switch เปิด = Real mode (not paper)

        # ✅ อัปเดต Mode Display ให้ตรงกับ switch
        if switch_is_on:  # switch เปิด = REAL TRADING
            mode_text = "REAL TRADING"
            mode_color = "red"
            log_msg = "🔥 Switched to REAL TRADING mode - ACTUAL MONEY AT RISK!"
        else:  # switch ปิด = PAPER TRADING
            mode_text = "PAPER TRADING"
            mode_color = "orange"
            log_msg = "📝 Switched to PAPER TRADING mode"

        # ✅ อัปเดต status card "Mode"
        if hasattr(self, 'status_cards') and 'Mode' in self.status_cards:
            self.status_cards['Mode'].configure(text=mode_text, text_color=mode_color)

        # ✅ อัปเดต trading mode label (ถ้ามี)
        if hasattr(self, 'trading_mode_label') and self.trading_mode_label:
            full_mode_text = f"📝 {mode_text} MODE ACTIVE ({'SAFE' if not switch_is_on else 'DANGER!'})"
            self.trading_mode_label.configure(text=full_mode_text, text_color=mode_color)

        # ✅ Log การเปลี่ยนแปลง
        if hasattr(self, 'log'):
            self.log(log_msg)

        # ✅ Debug output
        print(f"✅ Switch: {'ON (Real)' if switch_is_on else 'OFF (Paper)'}")
        print(f"✅ Mode Display: {mode_text}")
        print(f"✅ Internal State: {'Paper' if self.is_paper_trading else 'Real'}")

    # === ทดสอบการทำงาน ===
    """
    เมื่อแก้ไขแล้ว:

    1. Switch ปิด (เทา) → Mode Display: "PAPER TRADING" (ส้ม)
    2. Switch เปิด (แดง) → Mode Display: "REAL TRADING" (แดง)

    ผลลัพธ์ที่คาดหวัง:
    - Switch เปิด → Mode แสดง "REAL TRADING" 
    - Switch ปิด → Mode แสดง "PAPER TRADING"
    """

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


# เพิ่มใน should_buy_profitable() method ใน ProfitableTradingStrategy class

def should_buy_profitable(self, price, volume, balance_thb, trade_amount):
    """Enhanced buy signal with debug logging"""

    # Debug logging
    self.api_client.log(f"🔍 DEBUG: Checking buy conditions")
    self.api_client.log(f"   Price: {price:.2f}")
    self.api_client.log(f"   Volume: {volume:,.0f}")
    self.api_client.log(f"   Balance: {balance_thb:.2f}")
    self.api_client.log(f"   Trade Amount: {trade_amount:.2f}")

    if self.position:
        self.api_client.log(f"❌ Already have position")
        return False, "Already have position"

    if balance_thb < trade_amount:
        self.api_client.log(f"❌ Insufficient balance: {balance_thb:.2f} < {trade_amount}")
        return False, f"Insufficient balance: {balance_thb:.2f} < {trade_amount}"

    self.price_history.append(price)

    # Calculate break-even price including fees
    break_even_price = self.api_client.calculate_break_even_price(price, "buy")
    required_gain_pct = (break_even_price - price) / price

    self.api_client.log(f"🎯 Break-even: {break_even_price:.2f} ({required_gain_pct * 100:.2f}%)")

    # Only proceed if profit potential is realistic
    if required_gain_pct > self.min_profit_margin:
        self.api_client.log(f"❌ Required gain too high: {required_gain_pct * 100:.2f}%")
        return False, f"Required gain too high: {required_gain_pct * 100:.2f}%"

    conditions = []

    # RSI check
    if len(self.price_history) >= 15:
        rsi = self.calculate_rsi(list(self.price_history))
        self.api_client.log(f"📊 RSI: {rsi:.1f} (need < {self.rsi_oversold})")
        if rsi < self.rsi_oversold:
            conditions.append(f"RSI oversold ({rsi:.1f})")
            self.api_client.log(f"✅ RSI condition met")
        elif rsi > 50:  # Don't buy if RSI > 50
            self.api_client.log(f"❌ RSI too high ({rsi:.1f})")
            return False, f"RSI too high ({rsi:.1f})"
    else:
        self.api_client.log(f"⚠️ Not enough price history ({len(self.price_history)}/15)")

    # Volume momentum check
    volume_momentum = self.calculate_volume_momentum(volume)
    self.api_client.log(f"📈 Volume momentum: {volume_momentum:.2f}x (need > 1.2x)")
    if volume_momentum > 1.2:  # Volume 20% above average
        conditions.append(f"Volume surge ({volume_momentum:.2f}x)")
        self.api_client.log(f"✅ Volume condition met")

    # Price momentum check
    if len(self.price_history) >= 10:
        recent_prices = list(self.price_history)[-5:]
        older_prices = list(self.price_history)[-10:-5]

        recent_avg = np.mean(recent_prices)
        older_avg = np.mean(older_prices)

        price_momentum = (recent_avg - older_avg) / older_avg
        self.api_client.log(f"📉 Price momentum: {price_momentum * 100:.2f}% (need < -1%)")
        if price_momentum < -0.01:  # Price declining 1%
            conditions.append(f"Price dip ({price_momentum * 100:.2f}%)")
            self.api_client.log(f"✅ Price dip condition met")
    else:
        self.api_client.log(f"⚠️ Not enough price history for momentum ({len(self.price_history)}/10)")

    # Debug summary
    self.api_client.log(f"🔍 Conditions found: {len(conditions)}/2")
    for i, condition in enumerate(conditions, 1):
        self.api_client.log(f"   {i}. {condition}")

    # Need at least 2 conditions for buy signal
    if len(conditions) >= 2:
        self.api_client.log(f"✅ BUY SIGNAL TRIGGERED!")
        return True, " & ".join(conditions)

    self.api_client.log(f"❌ Not enough conditions ({len(conditions)}/2)")
    return False, f"Conditions: {len(conditions)}/2 ({', '.join(conditions) if conditions else 'None'})"

if __name__ == "__main__":

    print("🚀 Starting Enhanced Trading Bot...")
    app = ImprovedTradingBot()
    app.run()
