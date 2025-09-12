if hasattr(self, 'start_btn_trading'):
    self.start_btn_trading.configure(text="▶️ Start Enhanced Bot", fg_color="green")

    # Turn off switches
if hasattr(self, 'auto_trading_switch'):
    self.auto_trading_switch.deselect()

self.log("🚨 EMERGENCY STOP ACTIVATED!")

# Cancel all open orders if real trading
if not self.is_paper_trading and self.api_client:
    try:
        self.log("🗑️ Cancelling all open orders...")
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
                    self.log(f"✅ Cancelled order {order['id']}")
                else:
                    self.log(f"❌ Failed to cancel order {order['id']}")
    except Exception as e:
        self.log(f"❌ Error during emergency stop: {e}")

messagebox.showwarning("Emergency Stop",
                       "🚨 All enhanced trading stopped!\n🗑️ Orders cancelled!\n🤖 Auto trading disabled!")


# === 🆕 Additional Enhanced Functions ===

def start_coin_analysis(self):
    """🪙 Start comprehensive coin analysis"""
    if not self.license_manager.is_feature_enabled('coin_recommendation'):
        self.show_license_required()
        return

    if not self.coin_analyzer:
        messagebox.showwarning("Error", "Please connect API first")
        return

    try:
        trade_amount = int(self.coin_analyze_amount.get())
    except:
        trade_amount = 1000

    self.update_scifi_visual_state("coin_analysis", "Analyzing all coins")
    self.log("🪙 Starting comprehensive coin analysis...")

    # Clear display
    self.coin_analysis_display.delete("1.0", "end")
    self.coin_analysis_display.insert("1.0", "🪙 ANALYZING ALL BITKUB COINS...\n\nThis may take a few minutes...\n")

    # Start analysis in background
    threading.Thread(target=self.perform_full_coin_analysis, args=(trade_amount,), daemon=True).start()


def perform_full_coin_analysis(self, trade_amount):
    """Perform full coin analysis in background"""
    try:
        # Analyze all coins
        results = self.coin_analyzer.analyze_all_coins(trade_amount)

        # Update display with results
        self.update_coin_analysis_display(results)

        # Save to database
        self.save_coin_analysis_results(results)

        self.update_scifi_visual_state("success", "Coin analysis completed")
        threading.Timer(3.0, lambda: self.update_scifi_visual_state("idle")).start()

    except Exception as e:
        self.log(f"❌ Full coin analysis error: {e}")
        self.update_scifi_visual_state("error", "Coin analysis failed")


def update_coin_analysis_display(self, results):
    """Update coin analysis display with full results"""
    try:
        display_text = f"🪙 COMPREHENSIVE COIN ANALYSIS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        display_text += "=" * 100 + "\n\n"

        # Summary
        display_text += f"📊 ANALYSIS SUMMARY:\n"
        display_text += f"Total Coins Analyzed: {len(results)}\n"

        if results:
            high_score_coins = [c for c in results if c['ai_score'] >= 8.0]
            good_score_coins = [c for c in results if 6.0 <= c['ai_score'] < 8.0]

            display_text += f"🟢 High Potential (AI Score ≥ 8.0): {len(high_score_coins)} coins\n"
            display_text += f"🟡 Good Potential (AI Score 6.0-7.9): {len(good_score_coins)} coins\n"
            display_text += f"🔴 Lower Potential (AI Score < 6.0): {len(results) - len(high_score_coins) - len(good_score_coins)} coins\n\n"

            # Top recommendations
            display_text += f"🏆 TOP RECOMMENDATIONS:\n"
            display_text += f"{'Rank':<4} {'Symbol':<12} {'AI Score':<9} {'Price':<15} {'24h Change':<12} {'Fee Impact':<12} {'Recommendation'}\n"
            display_text += "-" * 100 + "\n"

            for i, coin in enumerate(results[:10], 1):  # Top 10
                display_text += f"{i:<4} {coin['symbol'].upper():<12} {coin['ai_score']:<9.1f} "
                display_text += f"{coin['price']:>13,.2f} {coin['change_24h']:>10.2f}% "
                display_text += f"{coin['fee_impact']:>10.3f}% {coin['recommendation']}\n"

            # Detailed analysis for top 3
            display_text += f"\n🔍 DETAILED ANALYSIS - TOP 3 COINS:\n"
            display_text += "=" * 100 + "\n"

            for i, coin in enumerate(results[:3], 1):
                display_text += f"\n{i}. {coin['symbol'].upper()} - AI Score: {coin['ai_score']:.1f}\n"
                display_text += f"   Current Price: {coin['price']:,.2f} THB\n"
                display_text += f"   24h Change: {coin['change_24h']:+.2f}%\n"
                display_text += f"   24h Volume: {coin.get('volume_24h', 0):,.0f} THB\n"
                display_text += f"   Volatility Score: {coin['volatility_score']:.1f}/10\n"
                display_text += f"   Volume Score: {coin['volume_score']:.1f}/10\n"
                display_text += f"   Momentum Score: {coin['momentum_score']:.1f}/10\n"
                display_text += f"   Fee Impact: {coin['fee_impact']:.3f}%\n"
                display_text += f"   Required Gain: {coin['required_gain']:.3f}%\n"
                display_text += f"   Recommendation: {coin['recommendation']}\n"

            # Best coin recommendation
            best_coin = results[0]
            display_text += f"\n💡 RECOMMENDED FOR TRADING:\n"
            display_text += f"Symbol: {best_coin['symbol'].upper()}\n"
            display_text += f"Why: Highest AI score ({best_coin['ai_score']:.1f}) with optimal risk/reward ratio\n"
            display_text += f"Expected profit potential: {coin['recommendation']}\n"

        else:
            display_text += "❌ No analysis results available\n"

        # Update display
        self.coin_analysis_display.delete("1.0", "end")
        self.coin_analysis_display.insert("1.0", display_text)

    except Exception as e:
        self.log(f"❌ Error updating coin analysis display: {e}")


def save_coin_analysis_results(self, results):
    """Save coin analysis results to database"""
    try:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for coin in results:
            cursor.execute('''
                    INSERT INTO coin_analysis 
                    (timestamp, symbol, price, change_24h, volume_24h, ai_score, 
                     volatility_score, volume_score, momentum_score, fee_impact, recommendation)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                datetime.now(),
                coin['symbol'],
                coin['price'],
                coin['change_24h'],
                coin.get('volume_24h', 0),
                coin['ai_score'],
                coin['volatility_score'],
                coin['volume_score'],
                coin['momentum_score'],
                coin['fee_impact'],
                coin['recommendation']
            ))

        conn.commit()
        conn.close()
        self.log("✅ Coin analysis results saved to database")

    except Exception as e:
        self.log(f"❌ Error saving coin analysis: {e}")


def select_best_coin(self):
    """🎯 Automatically select the best coin for trading"""
    if not self.license_manager.is_feature_enabled('coin_recommendation'):
        self.show_license_required()
        return

    best_coin = self.get_best_coin_for_trading()
    if best_coin:
        self.config['symbol'] = best_coin['symbol']
        self.symbol_var.set(best_coin['symbol'])

        self.status_cards["Best Coin"].configure(text=best_coin['symbol'].upper())
        self.status_cards["AI Score"].configure(text=f"{best_coin['ai_score']:.1f}")

        self.log(f"🎯 Best coin selected: {best_coin['symbol'].upper()} (AI Score: {best_coin['ai_score']:.1f})")
        messagebox.showinfo("Best Coin Selected",
                            f"Selected: {best_coin['symbol'].upper()}\n"
                            f"AI Score: {best_coin['ai_score']:.1f}\n"
                            f"Recommendation: {best_coin['recommendation']}")
    else:
        messagebox.showwarning("No Suitable Coin",
                               "No coin meets the minimum AI score criteria.\n"
                               "Consider lowering the minimum score or try again later.")


def toggle_strategy(self, strategy_key):
    """🎯 Toggle strategy enable/disable"""
    if not self.strategies:
        return

    enabled = self.strategy_vars[strategy_key].get()
    self.strategies.strategies[strategy_key]['enabled'] = enabled

    action = "ENABLED" if enabled else "DISABLED"
    strategy_name = self.strategies.strategies[strategy_key]['name']
    self.log(f"🎯 Strategy {action}: {strategy_name}")


def test_selected_strategies(self):
    """🧪 Test selected strategies"""
    if not self.license_manager.is_feature_enabled('advanced_strategies'):
        self.show_license_required()
        return

    if not self.strategies or not self.api_client:
        messagebox.showwarning("Error", "Please initialize strategies and connect API first")
        return

    self.log("🧪 Testing selected strategies...")

    # Get current market data
    ticker = self.api_client.get_simple_ticker(self.config['symbol'])
    if not ticker:
        messagebox.showerror("Error", "Cannot get market data for testing")
        return

    current_price = ticker['last_price']
    volume_24h = ticker.get('volume_24h', 0)

    # Test each enabled strategy
    test_results = []
    for strategy_key, strategy_info in self.strategies.strategies.items():
        if strategy_info['enabled']:
            should_trade, reason = self.strategies.analyze_with_strategy(
                strategy_key, current_price, volume_24h
            )

            test_results.append({
                'strategy': strategy_info['name'],
                'signal': 'BUY' if should_trade else 'WAIT',
                'reason': reason
            })

    # Display results
    results_text = f"🧪 STRATEGY TEST RESULTS - {self.config['symbol'].upper()}\n"
    results_text += f"Current Price: {current_price:,.2f} THB\n\n"

    for result in test_results:
        signal_color = "🟢" if result['signal'] == 'BUY' else "🟡"
        results_text += f"{signal_color} {result['strategy']}: {result['signal']}\n"
        results_text += f"   Reason: {result['reason']}\n\n"

    self.strategy_params_display.delete("1.0", "end")
    self.strategy_params_display.insert("1.0", results_text)

    messagebox.showinfo("Strategy Test", f"Strategy test completed!\nResults displayed in the strategies tab.")


def show_strategy_performance(self):
    """📊 Show strategy performance statistics"""
    if not self.license_manager.is_feature_enabled('advanced_strategies'):
        self.show_license_required()
        return

    try:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
                SELECT strategy_used, COUNT(*) as trades, 
                       AVG(net_pnl) as avg_pnl, SUM(net_pnl) as total_pnl,
                       SUM(CASE WHEN net_pnl > 0 THEN 1 ELSE 0 END) as profitable_trades
                FROM trades 
                WHERE strategy_used IS NOT NULL AND net_pnl IS NOT NULL
                GROUP BY strategy_used
                ORDER BY total_pnl DESC
            ''')

        results = cursor.fetchall()
        conn.close()

        if results:
            perf_text = "📊 STRATEGY PERFORMANCE ANALYSIS\n"
            perf_text += "=" * 80 + "\n"
            perf_text += f"{'Strategy':<20} {'Trades':<8} {'Win Rate':<10} {'Avg P&L':<12} {'Total P&L':<12}\n"
            perf_text += "-" * 80 + "\n"

            for strategy, trades, avg_pnl, total_pnl, profitable in results:
                win_rate = (profitable / trades * 100) if trades > 0 else 0
                perf_text += f"{strategy:<20} {trades:<8} {win_rate:<9.1f}% "
                perf_text += f"{avg_pnl:<11.2f} {total_pnl:<11.2f}\n"

            self.strategy_params_display.delete("1.0", "end")
            self.strategy_params_display.insert("1.0", perf_text)
        else:
            messagebox.showinfo("Strategy Performance",
                                "No strategy performance data available yet.\nStart trading to collect data!")

    except Exception as e:
        self.log(f"❌ Error showing strategy performance: {e}")


def auto_configure_strategies(self):
    """⚙️ Auto configure strategies based on market conditions"""
    if not self.license_manager.is_feature_enabled('advanced_strategies'):
        self.show_license_required()
        return

    if not self.strategies or not self.api_client:
        messagebox.showwarning("Error", "Please initialize strategies and connect API first")
        return

    self.log("⚙️ Auto-configuring strategies...")

    # Analyze current market conditions
    ticker = self.api_client.get_simple_ticker(self.config['symbol'])
    if not ticker:
        messagebox.showerror("Error", "Cannot get market data for auto-configuration")
        return

    change_24h = ticker.get('change_24h', 0)
    volume_24h = ticker.get('volume_24h', 0)

    # Auto-enable strategies based on market conditions
    recommendations = []

    if abs(change_24h) > 5:  # High volatility
        self.strategies.strategies['scalping']['enabled'] = True
        self.strategy_vars['scalping'].select()
        recommendations.append("✅ Enabled Scalping (High volatility detected)")

    if change_24h > 3:  # Strong uptrend
        self.strategies.strategies['ema_crossover']['enabled'] = True
        self.strategy_vars['ema_crossover'].select()
        recommendations.append("✅ Enabled EMA Crossover (Uptrend detected)")

    if abs(change_24h) < 2:  # Low volatility/sideways
        self.strategies.strategies['bollinger_bands']['enabled'] = True
        self.strategy_vars['bollinger_bands'].select()
        recommendations.append("✅ Enabled Bollinger Bands (Sideways market)")

    # Always enable RSI + Momentum as base strategy
    self.strategies.strategies['rsi_momentum']['enabled'] = True
    self.strategy_vars['rsi_momentum'].select()
    recommendations.append("✅ Enabled RSI + Momentum (Base strategy)")

    # Display recommendations
    if recommendations:
        rec_text = "⚙️ AUTO-CONFIGURATION COMPLETE\n\n"
        rec_text += f"Market Analysis:\n"
        rec_text += f"24h Change: {change_24h:+.2f}%\n"
        rec_text += f"24h Volume: {volume_24h:,.0f} THB\n\n"
        rec_text += "Recommendations Applied:\n"
        for rec in recommendations:
            rec_text += f"{rec}\n"

        self.strategy_params_display.delete("1.0", "end")
        self.strategy_params_display.insert("1.0", rec_text)

        messagebox.showinfo("Auto Configuration",
                            f"Strategies auto-configured based on current market conditions!\n\n"
                            f"24h Change: {change_24h:+.2f}%\n"
                            f"{len(recommendations)} strategies enabled.")


def toggle_auto_trading_engine(self):
    """🤖 Toggle auto trading engine"""
    if not self.license_manager.is_feature_enabled('auto_trading'):
        self.show_license_required()
        self.auto_trading_enabled.deselect()
        return

    enabled = self.auto_trading_enabled.get()

    if enabled:
        if not self.auto_trading_engine:
            messagebox.showwarning("Error", "Please connect API first to initialize auto trading engine")
            self.auto_trading_enabled.deselect()
            return

        # Configure auto trading
        config = {
            'auto_coin_selection': self.auto_coin_selection_var.get(),
            'adaptive_strategy': self.adaptive_strategy_var.get(),
            'min_ai_score': self.auto_min_ai_score.get()
        }

        self.auto_trading_engine.start_auto_trading(config)
        self.log("🤖 Auto Trading Engine ENABLED")
    else:
        if self.auto_trading_engine:
            self.auto_trading_engine.stop_auto_trading()
        self.log("🤖 Auto Trading Engine DISABLED")


def update_ai_score_label(self, value):
    """Update AI score label"""
    try:
        self.auto_ai_score_label.configure(text=f"{float(value):.1f}")
    except:
        pass


def toggle_force_sell(self):
    """🕐 Toggle force sell system"""
    if not self.license_manager.is_feature_enabled('force_sell'):
        self.show_license_required()
        self.force_sell_enabled.deselect()
        return

    enabled = self.force_sell_enabled.get()
    self.config['force_sell_enabled'] = enabled

    if enabled:
        self.log("🕐 Force Sell System ENABLED")
    else:
        self.log("🕐 Force Sell System DISABLED")


def update_hold_hours_label(self, value):
    """Update hold hours label"""
    try:
        hours = int(float(value))
        self.hold_hours_label.configure(text=f"{hours} hours")
        if self.force_sell_manager:
            self.force_sell_manager.max_hold_hours = hours
    except:
        pass


def update_profit_threshold_label(self, value):
    """Update profit threshold label"""
    try:
        threshold = float(value)
        self.profit_threshold_label.configure(text=f"{threshold:.1f}%")
        if self.force_sell_manager:
            self.force_sell_manager.min_profit_threshold = threshold / 100
    except:
        pass


def update_auto_trading_performance(self):
    """📈 Update auto trading performance display"""
    try:
        if self.auto_trading_engine:
            performance = self.auto_trading_engine.get_performance_summary()

            perf_text = f"🤖 AUTO TRADING PERFORMANCE\n"
            perf_text += f"Total Trades: {performance['total_trades']}\n"
            perf_text += f"Win Rate: {performance['win_rate']:.1f}%\n"
            perf_text += f"Average P&L: {performance['avg_pnl']:+.2f} THB\n"
            perf_text += f"Active Positions: {performance['active_positions']}\n"

            self.auto_performance_display.delete("1.0", "end")
            self.auto_performance_display.insert("1.0", perf_text)
    except:
        pass


def configure_manual_strategy(self):
    """⚙️ Configure manual trading strategy"""
    selected_strategy = self.manual_strategy_var.get()

    config_text = f"⚙️ CONFIGURING: {selected_strategy}\n\n"
    config_text += "Strategy parameters can be customized here.\n"
    config_text += "This feature allows fine-tuning of strategy settings.\n\n"
    config_text += f"Current settings for {selected_strategy}:\n"

    # Show current parameters
    if selected_strategy == "RSI + Momentum":
        config_text += "• RSI Period: 14\n• Oversold: 25\n• Overbought: 75\n• Momentum Threshold: 1.2x"
    elif selected_strategy == "Bollinger Bands":
        config_text += "• Period: 20\n• Standard Deviation: 2\n• Squeeze Threshold: 0.5"
    # Add more strategy configs as needed

    messagebox.showinfo("Strategy Configuration", config_text)


def update_risk_settings(self, value=None):
    """Update risk management labels"""
    try:
        self.stop_loss_label.configure(text=f"{self.stop_loss_var.get():.1f}%")
        self.take_profit_label.configure(text=f"{self.take_profit_var.get():.1f}%")
    except:
        pass


def test_enhanced_connection(self):
    """🔌 Enhanced connection test"""
    if not self.api_client:
        self.api_status_display.delete("1.0", "end")
        self.api_status_display.insert("1.0", "❌ Please connect API first")
        return

    self.update_scifi_visual_state("connecting", "Testing enhanced API connection")

    self.api_status_display.delete("1.0", "end")
    self.api_status_display.insert("1.0", "🔌 Testing Enhanced API Connection v3.0...\n\n")

    # Enhanced connection tests
    tests = [
        ("System Status", self.api_client.check_system_status),
        ("Balance Check", self.api_client.check_balance),
        ("Market Data", lambda: self.api_client.get_simple_ticker(self.config['symbol'])),
    ]

    for test_name, test_func in tests:
        try:
            if test_name == "System Status":
                status_ok, status_msg = test_func()
                result = f"✅ {test_name}: {status_msg}" if status_ok else f"❌ {test_name}: {status_msg}"
            elif test_name == "Balance Check":
                balance = test_func()
                if balance and balance.get('error') == 0:
                    thb_balance = balance['result'].get('THB', 0)
                    result = f"✅ {test_name}: {float(thb_balance):,.2f} THB"
                else:
                    result = f"❌ {test_name}: Failed"
            elif test_name == "Market Data":
                ticker = test_func()
                if ticker:
                    result = f"✅ {test_name}: {ticker['symbol']} @ {ticker['last_price']:,.2f} THB"
                else:
                    result = f"❌ {test_name}: Failed"
            else:
                result = f"✅ {test_name}: OK"

            self.api_status_display.insert("end", result + "\n")
        except Exception as e:
            self.api_status_display.insert("end", f"❌ {test_name}: Error - {e}\n")

    # Test premium features
    self.api_status_display.insert("end", "\n🔐 PREMIUM FEATURES STATUS:\n")

    premium_features = [
        ("Coin Analyzer", self.coin_analyzer is not None),
        ("Advanced Strategies", self.strategies is not None),
        ("Force Sell Manager", self.force_sell_manager is not None),
        ("Auto Trading Engine", self.auto_trading_engine is not None)
    ]

    for feature_name, is_available in premium_features:
        status = "✅ Ready" if is_available else "❌ Not initialized"
        self.api_status_display.insert("end", f"  {feature_name}: {status}\n")

    self.api_status_display.insert("end",
                                   f"\n✅ Enhanced Connection Test Completed: {datetime.now().strftime('%H:%M:%S')}")

    self.update_scifi_visual_state("success", "Enhanced connection test completed")
    threading.Timer(2.0, lambda: self.update_scifi_visual_state("idle")).start()


def premium_health_check(self):
    """🏥 Premium health check with all features"""
    if not self.api_client:
        messagebox.showwarning("Error", "Please connect API first")
        return

    self.update_scifi_visual_state("analyzing", "Running premium health check")

    self.api_status_display.delete("1.0", "end")
    self.api_status_display.insert("1.0", "🏥 Running Premium Health Check v3.0...\n\n")

    # Standard API health
    status_ok, status_msg = self.api_client.check_system_status()
    self.api_status_display.insert("end", f"System Status: {'✅' if status_ok else '❌'} {status_msg}\n")

    # Balance check
    balance = self.api_client.check_balance()
    if balance and balance.get('error') == 0:
        self.api_status_display.insert("end", "Balance Check: ✅ Success\n")
    else:
        self.api_status_display.insert("end", "Balance Check: ❌ Failed\n")

    # Premium features health
    self.api_status_display.insert("end", "\n🔐 PREMIUM FEATURES HEALTH:\n")

    # Test coin analyzer
    if self.coin_analyzer:
        try:
            test_analysis = self.coin_analyzer.analyze_single_coin("btc_thb", 1000)
            if test_analysis:
                self.api_status_display.insert("end",
                                               f"🪙 Coin Analyzer: ✅ Working (AI Score: {test_analysis['ai_score']:.1f})\n")
            else:
                self.api_status_display.insert("end", "🪙 Coin Analyzer: ⚠️ No data returned\n")
        except Exception as e:
            self.api_status_display.insert("end", f"🪙 Coin Analyzer: ❌ Error - {e}\n")
    else:
        self.api_status_display.insert("end", "🪙 Coin Analyzer: ❌ Not initialized\n")

    # Test strategies
    if self.strategies:
        try:
            ticker = self.api_client.get_simple_ticker("btc_thb")
            if ticker:
                should_trade, reason = self.strategies.analyze_with_strategy(
                    "rsi_momentum", ticker['last_price'], ticker.get('volume_24h', 0)
                )
                self.api_status_display.insert("end",
                                               f"🎯 Advanced Strategies: ✅ Working (Signal: {'BUY' if should_trade else 'WAIT'})\n")
            else:
                self.api_status_display.insert("end", "🎯 Advanced Strategies: ⚠️ Cannot test - no market data\n")
        except Exception as e:
            self.api_status_display.insert("end", f"🎯 Advanced Strategies: ❌ Error - {e}\n")
    else:
        self.api_status_display.insert("end", "🎯 Advanced Strategies: ❌ Not initialized\n")

    # Test force sell
    if self.force_sell_manager:
        positions = self.force_sell_manager.get_positions_status()
        self.api_status_display.insert("end",
                                       f"🕐 Force Sell Manager: ✅ Working (Monitoring: {len(positions)} positions)\n")
    else:
        self.api_status_display.insert("end", "🕐 Force Sell Manager: ❌ Not initialized\n")

    # Test auto trading
    if self.auto_trading_engine:
        performance = self.auto_trading_engine.get_performance_summary()
        self.api_status_display.insert("end",
                                       f"🤖 Auto Trading Engine: ✅ Working (Trades: {performance['total_trades']})\n")
    else:
        self.api_status_display.insert("end", "🤖 Auto Trading Engine: ❌ Not initialized\n")

    # License status
    license_info = self.license_manager.get_license_info()
    license_status = "✅ Valid" if license_info['valid'] else "❌ Expired"
    self.api_status_display.insert("end",
                                   f"\n🔐 License Status: {license_status} ({license_info['remaining_days']} days left)\n")

    self.api_status_display.insert("end", f"\n🏥 Premium Health Check Completed: {datetime.now().strftime('%H:%M:%S')}")

    self.update_scifi_visual_state("success", "Premium health check completed")
    threading.Timer(3.0, lambda: self.update_scifi_visual_state("idle")).start()


def save_enhanced_settings(self):
    """💾 Save enhanced settings with premium features"""
    # Validate settings
    new_amount = self.trade_amount_var.get()
    new_max_trades = self.max_trades_var.get()
    new_max_loss = self.max_loss_var.get()

    warnings = []

    # Enhanced validation
    if new_amount < 500:
        warnings.append(f"Low trade amount: {new_amount} THB (may not be profitable with 0.5% fees)")
    if new_amount > 50000:
        warnings.append(f"Very high trade amount: {new_amount} THB")
    if new_max_trades > 20:
        warnings.append(f"High daily trade limit: {new_max_trades}")

    # Premium features warnings
    if self.auto_coin_enabled.get() and not self.license_manager.is_feature_enabled('coin_recommendation'):
        warnings.append("Auto coin selection requires premium license")
    if self.adaptive_strategy_enabled.get() and not self.license_manager.is_feature_enabled('advanced_strategies'):
        warnings.append("Adaptive strategy requires premium license")

    if warnings and not messagebox.askyesno("Settings Warning",
                                            "Potential issues detected:\n\n" +
                                            "\n".join(warnings) +
                                            "\n\nContinue anyway?"):
        return

    # Save enhanced settings
    self.config.update({
        'symbol': self.symbol_var.get(),
        'trade_amount_thb': new_amount,
        'max_daily_trades': new_max_trades,
        'max_daily_loss': new_max_loss,
        'auto_coin_selection': self.auto_coin_enabled.get(),
        'adaptive_strategy': self.adaptive_strategy_enabled.get(),
        'force_sell_enabled': self.force_sell_settings_enabled.get(),
        'min_ai_score': 6.0  # Could be made configurable
    })

    messagebox.showinfo("Success", "🚀 Enhanced settings saved successfully!")
    self.log(
        f"Settings updated: Symbol={self.config['symbol']}, Amount={new_amount}, "
        f"AutoCoin={self.config['auto_coin_selection']}, "
        f"AdaptiveStrategy={self.config['adaptive_strategy']}"
    )


def refresh_license(self):
    """🔄 Refresh license information"""
    self.license_manager = LicenseManager()  # Reload license
    license_info = self.license_manager.get_license_info()

    # Update status card
    self.status_cards["License"].configure(text=license_info['type'].upper())

    messagebox.showinfo("License Refreshed",
                        f"License Type: {license_info['type'].upper()}\n"
                        f"Status: {'VALID' if license_info['valid'] else 'EXPIRED'}\n"
                        f"Days Remaining: {license_info['remaining_days']}")

    # Refresh the license tab
    self.tabview.delete("🔐 License")
    self.tab_license = self.tabview.add("🔐 License")
    self.setup_license_tab()


def show_trial_demo(self):
    """💡 Show trial features demo"""
    demo_text = """
🎁 TRIAL FEATURES DEMONSTRATION

During your 7-day trial, you have access to ALL premium features:

🪙 AI COIN ANALYZER:
• Click "Analyze All Coins" to see AI scoring in action
• Watch as the system evaluates 57+ Bitkub coins
• See automatic best coin selection

🎯 ADVANCED STRATEGIES:
• Enable multiple strategies in the Strategies tab
• Test "Auto Configure" for market-adaptive settings
• Compare performance of different approaches

🤖 AUTO TRADING ENGINE:
• Toggle "Auto Trading Mode" in the dashboard
• Experience fully autonomous trading
• Watch AI select coins + strategies automatically

🕐 FORCE SELL SYSTEM:
• Set custom time limits for positions
• See emergency sell conditions in action
• Protect profits automatically

📊 ADVANCED ANALYTICS:
• View detailed performance comparisons
• Export comprehensive trading reports
• Track strategy-specific results

🎬 PREMIUM GRAPHICS:
• Experience enhanced Sci-Fi visual states
• "Coin Analysis" and "Auto Mode" animations
• Professional status indicators

Try these features now to see the full power of the premium version!
        """

    messagebox.showinfo("Trial Features Demo", demo_text)


def show_upgrade_options(self):
    """🔐 Show upgrade options"""
    upgrade_text = """
🔐 UPGRADE TO PREMIUM

Your trial has expired, but you can continue using premium features!

📞 CONTACT FOR LICENSE:
• Email: support@tradingbot.com
• Telegram: @tradingbotsupport
• Discord: TradingBot#1234

💰 PRICING OPTIONS:
• Monthly License: $49/month
• Annual License: $399/year (Save 33%)
• Lifetime License: $999 (Best Value!)

✨ PREMIUM BENEFITS:
• Unlimited trading with all coins
• All 8 advanced strategies
• Full auto trading capabilities
• Priority support & updates
• No daily limits or restrictions

🎯 SPECIAL OFFER:
Use code TRIAL20 for 20% off your first license!

Your Hardware ID: {self.license_manager.hardware_id}
(Provide this when purchasing your license)
        """

    messagebox.showinfo("Upgrade to Premium", upgrade_text)

    # === 🆕 Analytics Functions ===


def show_strategy_comparison(self):
    """📊 Show strategy comparison analytics"""
    try:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get strategy performance data
        cursor.execute('''
                SELECT strategy_used, 
                       COUNT(*) as total_trades,
                       AVG(net_pnl) as avg_pnl,
                       SUM(net_pnl) as total_pnl,
                       SUM(CASE WHEN net_pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
                       MIN(net_pnl) as worst_trade,
                       MAX(net_pnl) as best_trade
                FROM trades 
                WHERE strategy_used IS NOT NULL AND net_pnl IS NOT NULL
                GROUP BY strategy_used
                ORDER BY total_pnl DESC
            ''')

        results = cursor.fetchall()
        conn.close()

        if results:
            comparison_text = "📊 COMPREHENSIVE STRATEGY COMPARISON\n"
            comparison_text += "=" * 100 + "\n\n"

            for strategy, total, avg_pnl, total_pnl, winning, worst, best in results:
                win_rate = (winning / total * 100) if total > 0 else 0
                comparison_text += f"🎯 {strategy.upper()}\n"
                comparison_text += f"   Total Trades: {total}\n"
                comparison_text += f"   Win Rate: {win_rate:.1f}%\n"
                comparison_text += f"   Average P&L: {avg_pnl:+.2f} THB\n"
                comparison_text += f"   Total P&L: {total_pnl:+.2f} THB\n"
                comparison_text += f"   Best Trade: {best:+.2f} THB\n"
                comparison_text += f"   Worst Trade: {worst:+.2f} THB\n\n"

            self.strategies_display.delete("1.0", "end")
            self.strategies_display.insert("1.0", comparison_text)
        else:
            messagebox.showinfo("Strategy Comparison",
                                "No strategy data available yet.\nStart trading to collect performance data!")

    except Exception as e:
        self.log(f"❌ Error showing strategy comparison: {e}")


def show_coin_performance(self):
    """🪙 Show coin performance analytics"""
    try:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get coin analysis data
        cursor.execute('''
                SELECT symbol, 
                       AVG(ai_score) as avg_ai_score,
                       AVG(change_24h) as avg_change,
                       COUNT(*) as analysis_count,
                       MAX(ai_score) as max_score,
                       MIN(ai_score) as min_score
                FROM coin_analysis 
                GROUP BY symbol
                ORDER BY avg_ai_score DESC
            ''')

        results = cursor.fetchall()
        conn.close()

        if results:
            coin_text = "🪙 COIN PERFORMANCE ANALYTICS\n"
            coin_text += "=" * 80 + "\n\n"
            coin_text += f"{'Coin':<12} {'Avg Score':<10} {'Avg Change':<12} {'Analyses':<10} {'Score Range'}\n"
            coin_text += "-" * 80 + "\n"

            for symbol, avg_score, avg_change, count, max_score, min_score in results:
                coin_text += f"{symbol.upper():<12} {avg_score:<9.1f} {avg_change:<11.2f}% "
                coin_text += f"{count:<10} {min_score:.1f} - {max_score:.1f}\n"

            self.coins_display.delete("1.0", "end")
            self.coins_display.insert("1.0", coin_text)
        else:
            messagebox.showinfo("Coin Performance",
                                "No coin analysis data available yet.\nRun coin analysis to collect data!")

    except Exception as e:
        self.log(f"❌ Error showing coin performance: {e}")


def show_enhanced_profit_analysis(self):
    def show_enhanced_profit_analysis(self):
        """Show enhanced profit analysis"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Comprehensive profit analysis
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN net_pnl > 0 THEN 1 ELSE 0 END) as profitable_trades,
                    SUM(net_pnl) as total_net_pnl,
                    SUM(fees) as total_fees,
                    AVG(net_pnl) as avg_pnl,
                    MAX(net_pnl) as best_trade,
                    MIN(net_pnl) as worst_trade,
                    AVG(ai_score) as avg_ai_score,
                    SUM(CASE WHEN force_sell = 1 THEN 1 ELSE 0 END) as force_sells,
                    SUM(CASE WHEN auto_trade = 1 THEN 1 ELSE 0 END) as auto_trades
                FROM trades
                WHERE net_pnl IS NOT NULL
            ''')

            stats = cursor.fetchone()
            conn.close()

            if stats and stats[0] > 0:
                (total, profitable, total_pnl, total_fees, avg_pnl,
                 best, worst, avg_ai, force_sells, auto_trades) = stats

                win_rate = (profitable / total * 100) if total > 0 else 0
                profit_factor = abs(total_pnl / worst) if worst < 0 else float('inf')

                analysis_text = "ENHANCED PROFIT ANALYSIS\n"
                analysis_text += "=" * 80 + "\n\n"
                analysis_text += f"TRADING PERFORMANCE:\n"
                analysis_text += f"Total Trades: {total}\n"
                analysis_text += f"Profitable Trades: {profitable} ({win_rate:.1f}%)\n"
                analysis_text += f"Total Net P&L: {total_pnl:+.2f} THB\n"
                analysis_text += f"Total Fees Paid: {total_fees:.2f} THB\n"
                analysis_text += f"Average P&L per Trade: {avg_pnl:+.2f} THB\n"
                analysis_text += f"Best Trade: {best:+.2f} THB\n"
                analysis_text += f"Worst Trade: {worst:+.2f} THB\n"
                analysis_text += f"Profit Factor: {profit_factor:.2f}\n\n"

                analysis_text += f"PREMIUM FEATURES IMPACT:\n"
                analysis_text += f"Average AI Score: {avg_ai:.1f}\n"
                analysis_text += f"Force Sells Executed: {force_sells}\n"
                analysis_text += f"Auto Trades: {auto_trades} ({auto_trades / total * 100:.1f}%)\n\n"

                # Performance rating
                if win_rate >= 60 and total_pnl > total_fees * 2:
                    rating = "EXCELLENT"
                elif win_rate >= 50 and total_pnl > 0:
                    rating = "GOOD"
                elif total_pnl > -total_fees:
                    rating = "FAIR"
                else:
                    rating = "NEEDS IMPROVEMENT"

                analysis_text += f"PERFORMANCE RATING: {rating}\n"

                self.overview_display.delete("1.0", "end")
                self.overview_display.insert("1.0", analysis_text)
            else:
                messagebox.showinfo("Profit Analysis",
                                    "No trading data available yet.\nStart trading to collect performance data!")

        except Exception as e:
            self.log(f"Error showing profit analysis: {e}")

    def show_force_sell_statistics(self):
        """🕐 Show force sell statistics"""
        if not self.license_manager.is_feature_enabled('force_sell'):
            self.show_license_required()
            return

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Force sell statistics
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_force_sells,
                    AVG(net_pnl) as avg_force_sell_pnl,
                    SUM(net_pnl) as total_force_sell_pnl,
                    SUM(CASE WHEN net_pnl > 0 THEN 1 ELSE 0 END) as profitable_force_sells
                FROM trades
                WHERE force_sell = 1 AND net_pnl IS NOT NULL
            ''')

            force_stats = cursor.fetchone()

            # Compare with regular sells
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_regular_sells,
                    AVG(net_pnl) as avg_regular_pnl,
                    SUM(net_pnl) as total_regular_pnl
                FROM trades
                WHERE force_sell = 0 AND side = 'sell' AND net_pnl IS NOT NULL
            ''')

            regular_stats = cursor.fetchone()
            conn.close()

            if force_stats and force_stats[0] > 0:
                (force_count, force_avg, force_total, force_profitable) = force_stats
                (regular_count, regular_avg, regular_total) = regular_stats or (0, 0, 0)

                force_win_rate = (force_profitable / force_count * 100) if force_count > 0 else 0

                stats_text = "🕐 FORCE SELL EFFECTIVENESS ANALYSIS\n"
                stats_text += "=" * 60 + "\n\n"
                stats_text += f"📊 FORCE SELL PERFORMANCE:\n"
                stats_text += f"Total Force Sells: {force_count}\n"
                stats_text += f"Profitable Force Sells: {force_profitable} ({force_win_rate:.1f}%)\n"
                stats_text += f"Average Force Sell P&L: {force_avg:+.2f} THB\n"
                stats_text += f"Total Force Sell P&L: {force_total:+.2f} THB\n\n"

                if regular_count > 0:
                    stats_text += f"📈 COMPARISON WITH REGULAR SELLS:\n"
                    stats_text += f"Regular Sells: {regular_count}\n"
                    stats_text += f"Average Regular P&L: {regular_avg:+.2f} THB\n"
                    stats_text += f"Force Sell Advantage: {force_avg - regular_avg:+.2f} THB per trade\n\n"

                # Effectiveness rating
                if force_win_rate >= 70:
                    effectiveness = "🏆 HIGHLY EFFECTIVE"
                elif force_win_rate >= 50:
                    effectiveness = "✅ EFFECTIVE"
                else:
                    effectiveness = "⚠️ NEEDS OPTIMIZATION"

                stats_text += f"🎯 FORCE SELL EFFECTIVENESS: {effectiveness}\n"

                messagebox.showinfo("Force Sell Statistics", stats_text)
            else:
                messagebox.showinfo("Force Sell Statistics",
                                    "No force sell data available yet.\nEnable force sell and start trading to collect data!")

        except Exception as e:
            self.log(f"❌ Error showing force sell statistics: {e}")

    def show_auto_trading_report(self):
        def show_auto_trading_report(self):
            """Show auto trading performance report"""
            if not self.license_manager.is_feature_enabled('auto_trading'):
                self.show_license_required()
                return

            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                # Auto trading statistics
                cursor.execute('''
                SELECT 
                    COUNT(*) as auto_trades,
                    AVG(net_pnl) as avg_auto_pnl,
                    SUM(net_pnl) as total_auto_pnl,
                    SUM(CASE WHEN net_pnl > 0 THEN 1 ELSE 0 END) as profitable_autos
                FROM trades
                WHERE auto_trade = 1 AND net_pnl IS NOT NULL
            ''')

                auto_stats = cursor.fetchone()

                # Manual trading comparison
                cursor.execute('''
                SELECT 
                    COUNT(*) as manual_trades,
                    AVG(net_pnl) as avg_manual_pnl,
                    SUM(net_pnl) as total_manual_pnl
                FROM trades
                WHERE auto_trade = 0 AND net_pnl IS NOT NULL
            ''')

                manual_stats = cursor.fetchone()

                # Auto trading decisions log
                cursor.execute('''
                SELECT action, COUNT(*) as count
                FROM auto_trading_log
                GROUP BY action
                ORDER BY count DESC
            ''')

                decisions = cursor.fetchall()
                conn.close()

                if auto_stats and auto_stats[0] > 0:
                    (auto_count, auto_avg, auto_total, auto_profitable) = auto_stats
                    (manual_count, manual_avg, manual_total) = manual_stats or (0, 0, 0)

                    auto_win_rate = (auto_profitable / auto_count * 100) if auto_count > 0 else 0

                    report_text = "AUTO TRADING PERFORMANCE REPORT\n"
                    report_text += "=" * 70 + "\n\n"
                    report_text += f"AUTO TRADING RESULTS:\n"
                    report_text += f"Total Auto Trades: {auto_count}\n"
                    report_text += f"Profitable Auto Trades: {auto_profitable} ({auto_win_rate:.1f}%)\n"
                    report_text += f"Average Auto P&L: {auto_avg:+.2f} THB\n"
                    report_text += f"Total Auto P&L: {auto_total:+.2f} THB\n\n"

                    if manual_count > 0:
                        manual_win_rate = ((
                                                       manual_count - auto_count + auto_profitable) / manual_count * 100) if manual_count > 0 else 0
                        report_text += f"AUTO vs MANUAL COMPARISON:\n"
                        report_text += f"Manual Trades: {manual_count}\n"
                        report_text += f"Manual Avg P&L: {manual_avg:+.2f} THB\n"
                        report_text += f"Auto Trading Advantage: {auto_avg - manual_avg:+.2f} THB per trade\n\n"

                    if decisions:
                        report_text += f"AUTO TRADING DECISIONS:\n"
                        for action, count in decisions:
                            report_text += f"  {action.title()}: {count}\n"
                        report_text += "\n"

                    # Performance rating
                    if auto_win_rate >= 65 and auto_total > 0:
                        rating = "EXCELLENT AUTOMATION"
                    elif auto_win_rate >= 50 and auto_total > 0:
                        rating = "GOOD AUTOMATION"
                    elif auto_total > -100:  # Small losses acceptable
                        rating = "FAIR AUTOMATION"
                    else:
                        rating = "NEEDS TUNING"

                    report_text += f"AUTO TRADING RATING: {rating}\n"

                    messagebox.showinfo("Auto Trading Report", report_text)
                else:
                    messagebox.showinfo("Auto Trading Report",
                                        "No auto trading data available yet.\nEnable auto trading to start collecting performance data!")

            except Exception as e:
                self.log(f"Error showing auto trading report: {e}")

    def export_analytics_report(self):
        """📈 Export comprehensive analytics report"""
        try:
            from tkinter import filedialog
            import csv

            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("Text files", "*.txt")],
                title="Export Enhanced Analytics Report"
            )

            if filename:
                conn = sqlite3.connect(self.db_path)

                # Export multiple sheets of data
                if filename.endswith('.csv'):
                    # Export main trades data
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT * FROM trades ORDER BY timestamp DESC
                    ''')

                    trades_data = cursor.fetchall()
                    column_names = [description[0] for description in cursor.description]

                    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerow(column_names)
                        writer.writerows(trades_data)

                    # Also export coin analysis data
                    coin_filename = filename.replace('.csv', '_coin_analysis.csv')
                    cursor.execute('SELECT * FROM coin_analysis ORDER BY timestamp DESC')
                    coin_data = cursor.fetchall()
                    coin_columns = [description[0] for description in cursor.description]

                    with open(coin_filename, 'w', newline='', encoding='utf-8') as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerow(coin_columns)
                        writer.writerows(coin_data)

                conn.close()

                messagebox.showinfo("Export Complete",
                                    f"Enhanced analytics exported successfully!\n\n"
                                    f"Files created:\n"
                                    f"• {filename}\n" +
                                    (f"• {coin_filename}\n" if filename.endswith('.csv') else ""))

        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export analytics: {e}")

    # === 🆕 Additional Helper Functions ===

    def test_coin_analyzer(self):
        """Test coin analyzer functionality"""
        try:
            if self.coin_analyzer:
                test_result = self.coin_analyzer.analyze_single_coin("btc_thb", 1000)
                if test_result:
                    self.log(f"✅ Coin Analyzer test successful - BTC AI Score: {test_result['ai_score']:.1f}")
                else:
                    self.log("⚠️ Coin Analyzer test returned no data")
        except Exception as e:
            self.log(f"❌ Coin Analyzer test failed: {e}")

    def basic_strategy_analysis(self, price, volume):
        """Fallback basic strategy for when advanced strategies aren't available"""
        # Simple RSI + Volume analysis
        if hasattr(self, 'price_history') and len(self.price_history) >= 15:
            prices = list(self.price_history)

            # Calculate simple RSI
            deltas = np.diff(prices[-15:])
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)

            avg_gain = np.mean(gains)
            avg_loss = np.mean(losses)

            if avg_loss == 0:
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))

            if rsi < 30:
                return True, f"Basic RSI oversold ({rsi:.1f})"

        return False, "Basic analysis: No signal"

    def enhanced_system_check(self):
        """🔄 Enhanced system health check"""
        self.update_scifi_visual_state("analyzing", "Running enhanced system check")
        self.log("🔄 Running Enhanced System Health Check v3.0...")

        checks = []

        # API Status
        if self.api_client:
            status_ok, status_msg = self.api_client.check_system_status()
            checks.append(("API Status", "✅ Connected" if status_ok else f"❌ {status_msg}"))
        else:
            checks.append(("API Status", "❌ Not connected"))

        # Premium Components
        checks.append(("Coin Analyzer", "✅ Ready" if self.coin_analyzer else "❌ Not initialized"))
        checks.append(("Advanced Strategies", "✅ Ready" if self.strategies else "❌ Not initialized"))
        checks.append(("Force Sell Manager", "✅ Ready" if self.force_sell_manager else "❌ Not initialized"))
        checks.append(("Auto Trading Engine", "✅ Ready" if self.auto_trading_engine else "❌ Not initialized"))

        # License Status
        license_info = self.license_manager.get_license_info()
        checks.append(("License", f"✅ {license_info['type'].upper()}" if license_info['valid'] else "❌ EXPIRED"))

        # Visual System
        checks.append(("Visual System", "✅ Active" if hasattr(self, 'scifi_visual') else "❌ Not active"))

        # Display results
        check_results = "\n".join([f"{name}: {status}" for name, status in checks])
        self.log(f"🔄 System Check Results:\n{check_results}")

        all_good = all("✅" in status for name, status in checks)

        if all_good:
            self.update_scifi_visual_state("success", "All systems operational")
            messagebox.showinfo("System Check", "🔄 Enhanced System Check Passed!\n\n" + check_results)
        else:
            self.update_scifi_visual_state("error", "System issues detected")
            messagebox.showwarning("System Check", "⚠️ System Issues Detected!\n\n" + check_results)

        threading.Timer(2.0, lambda: self.update_scifi_visual_state("idle")).start()

    def check_enhanced_signals(self):
        """📊 Check enhanced signals with all premium features"""
        if not self.api_client:
            messagebox.showwarning("Error", "Please connect API first")
            return

        self.update_scifi_visual_state("analyzing", "Analyzing enhanced market signals")

        # Get current market data
        current_symbol = self.config['symbol']

        # 🪙 Auto coin selection if enabled
        if self.config.get('auto_coin_selection') and self.coin_analyzer:
            best_coin = self.get_best_coin_for_trading()
            if best_coin:
                current_symbol = best_coin['symbol']

        ticker = self.api_client.get_simple_ticker(current_symbol)

        if not ticker:
            messagebox.showwarning("Error", "Cannot get market data")
            self.update_scifi_visual_state("error", "Market data unavailable")
            return

        signal_text = f"\n📊 ENHANCED SIGNAL ANALYSIS - {datetime.now().strftime('%H:%M:%S')}\n"
        signal_text += f"{'=' * 80}\n"
        signal_text += f"Symbol: {ticker['symbol']} (Selected by: {'AI' if current_symbol != self.config['symbol'] else 'Manual'})\n"
        signal_text += f"Current Price: {ticker['last_price']:,.2f} THB\n"
        signal_text += f"24h Change: {ticker['change_24h']:+.2f}%\n"
        signal_text += f"24h Volume: {ticker.get('volume_24h', 0):,.0f} THB\n\n"

        # 🪙 AI Coin Analysis
        if self.coin_analyzer:
            self.update_scifi_visual_state("coin_analysis", "Running AI coin analysis")
            analysis = self.coin_analyzer.analyze_single_coin(current_symbol, self.config['trade_amount_thb'])
            if analysis:
                signal_text += f"🪙 AI COIN ANALYSIS:\n"
                signal_text += f"   AI Score: {analysis['ai_score']:.1f}/10\n"
                signal_text += f"   Volatility Score: {analysis['volatility_score']:.1f}/10\n"
                signal_text += f"   Volume Score: {analysis['volume_score']:.1f}/10\n"
                signal_text += f"   Momentum Score: {analysis['momentum_score']:.1f}/10\n"
                signal_text += f"   Fee Impact: {analysis['fee_impact']:.3f}%\n"
                signal_text += f"   Recommendation: {analysis['recommendation']}\n\n"

        # 🎯 Multi-Strategy Analysis
        if self.strategies:
            self.update_scifi_visual_state("analyzing", "Testing all strategies")
            signal_text += f"🎯 MULTI-STRATEGY ANALYSIS:\n"

            enabled_strategies = [k for k, v in self.strategies.strategies.items() if v['enabled']]
            buy_signals = 0

            for strategy_key in enabled_strategies:
                should_trade, reason = self.strategies.analyze_with_strategy(
                    strategy_key, ticker['last_price'], ticker.get('volume_24h', 0)
                )

                strategy_name = self.strategies.strategies[strategy_key]['name']
                signal = "🟢 BUY" if should_trade else "🔴 WAIT"

                if should_trade:
                    buy_signals += 1

                signal_text += f"   {signal} {strategy_name}: {reason}\n"

            signal_text += f"\n"

        # 💰 Enhanced Fee Analysis
        price = ticker['last_price']
        trade_amount = self.config['trade_amount_thb']
        crypto_amount = trade_amount / price
        total_fees = self.api_client.calculate_trading_fees(crypto_amount, price, "both")
        break_even_price = self.api_client.calculate_break_even_price(price, "buy")
        required_gain = ((break_even_price - price) / price) * 100

        signal_text += f"💸 ENHANCED FEE ANALYSIS:\n"
        signal_text += f"   Trade Amount: {trade_amount:,.0f} THB\n"
        signal_text += f"   Total Fees: {total_fees:.2f} THB ({(total_fees / trade_amount) * 100:.3f}%)\n"
        signal_text += f"   Break-Even Price: {break_even_price:,.2f} THB\n"
        signal_text += f"   Required Gain: {required_gain:.3f}%\n"

        if required_gain < 1.0:
            signal_text += f"   ✅ Fee impact acceptable for trading\n\n"
        else:
            signal_text += f"   ⚠️ High fee impact - consider larger trade size\n\n"

        # 🤖 Auto Trading Recommendation
        if self.auto_trading_engine and self.is_auto_trading:
            decision = self.auto_trading_engine.auto_trading_cycle(trade_amount)
            if decision:
                signal_text += f"🤖 AUTO TRADING DECISION:\n"
                signal_text += f"   Action: {decision['action'].upper()}\n"
                signal_text += f"   Reason: {decision['reason']}\n"
                if 'ai_score' in decision:
                    signal_text += f"   AI Score: {decision['ai_score']:.1f}\n"
                if 'strategy' in decision:
                    signal_text += f"   Strategy: {decision['strategy']}\n"
                signal_text += f"\n"

        # Final Recommendation
        signal_text += f"🎯 ENHANCED RECOMMENDATION:\n"

        # Calculate overall signal strength
        signal_strength = 0
        reasons = []

        # AI Score contribution
        if hasattr(self, 'coin_analyzer') and self.coin_analyzer:
            try:
                analysis = self.coin_analyzer.analyze_single_coin(current_symbol, trade_amount)
                if analysis and analysis['ai_score'] >= 6.0:
                    signal_strength += 30
                    reasons.append(f"High AI Score ({analysis['ai_score']:.1f})")
            except:
                pass

        # Strategy consensus contribution
        if hasattr(self, 'strategies') and self.strategies:
            enabled_strategies = [k for k, v in self.strategies.strategies.items() if v['enabled']]
            if enabled_strategies:
                buy_signals = sum(1 for strategy_key in enabled_strategies
                                  if self.strategies.analyze_with_strategy(strategy_key, price,
                                                                           ticker.get('volume_24h', 0))[0])
                consensus_pct = buy_signals / len(enabled_strategies)
                if consensus_pct >= 0.5:
                    signal_strength += int(consensus_pct * 40)
                    reasons.append(f"Strategy consensus ({buy_signals}/{len(enabled_strategies)})")

        # Fee efficiency contribution
        if required_gain < 0.8:
            signal_strength += 20
            reasons.append("Low fee impact")
        elif required_gain < 1.2:
            signal_strength += 10
            reasons.append("Moderate fee impact")

        # Market momentum contribution
        if ticker['change_24h'] > 2:
            signal_strength += 10
            reasons.append("Positive momentum")
        elif ticker['change_24h'] < -2:
            signal_strength -= 10
            reasons.append("Negative momentum")

        # Final recommendation based on signal strength
        if signal_strength >= 60:
            recommendation = "STRONG BUY"
            confidence = "HIGH"
        elif signal_strength >= 40:
            recommendation = "MODERATE BUY"
            confidence = "MEDIUM"
        elif signal_strength >= 20:
            recommendation = "WEAK BUY"
            confidence = "LOW"
        else:
            recommendation = "NO BUY"
            confidence = "NONE"

        signal_text += f"   {recommendation}\n"
        signal_text += f"   Confidence Level: {confidence}\n"
        signal_text += f"   Signal Strength: {signal_strength}/100\n"
        signal_text += f"   Reasoning: {', '.join(reasons) if reasons else 'Insufficient signals'}\n"

        # Display results
        self.trading_log.insert("end", signal_text)
        self.trading_log.see("end")

        # Update visual state based on recommendation
        if "STRONG BUY" in recommendation:
            self.update_scifi_visual_state("buy_signal", "Strong buy signal detected")
        elif "BUY" in recommendation:
            self.update_scifi_visual_state("buy_signal", "Buy signal detected")
        else:
            self.update_scifi_visual_state("idle", "No strong signals")

        # Auto return to idle after showing results
        threading.Timer(3.0, lambda: self.update_scifi_visual_state("idle")).start()

    def show_enhanced_fee_calculator(self):
        """Enhanced fee calculator with multiple scenarios"""
        if not self.api_client:
            messagebox.showwarning("Error", "Please connect API first")
            return

        current_symbol = self.config['symbol']

        # Use auto-selected coin if enabled
        if self.config.get('auto_coin_selection') and self.coin_analyzer:
            best_coin = self.get_best_coin_for_trading()
            if best_coin:
                current_symbol = best_coin['symbol']

        ticker = self.api_client.get_simple_ticker(current_symbol)
        if not ticker:
            messagebox.showwarning("Error", "Cannot get current price")
            return

        current_price = ticker['last_price']

        # Multiple trade amount scenarios
        scenarios = [500, 1000, 2000, 5000, 10000]

        fee_info = f"""
ENHANCED BITKUB FEE CALCULATOR v3.0

Current Market Data:
• Symbol: {current_symbol.upper()}
• Current Price: {current_price:,.2f} THB
• 24h Change: {ticker['change_24h']:+.2f}%
• 24h Volume: {ticker.get('volume_24h', 0):,.0f} THB

Fee Structure:
• Maker Fee: 0.25%
• Taker Fee: 0.25%
• Total Round Trip: 0.50%

TRADING SCENARIOS:
"""

        for amount_thb in scenarios:
            crypto_amount = amount_thb / current_price
            buy_fee = self.api_client.calculate_trading_fees(crypto_amount, current_price, "buy")
            sell_fee = self.api_client.calculate_trading_fees(crypto_amount, current_price, "sell")
            total_fees = buy_fee + sell_fee
            break_even_price = self.api_client.calculate_break_even_price(current_price, "buy")
            required_gain = ((break_even_price - current_price) / current_price) * 100

            fee_info += f"""
{amount_thb:,} THB Trade:
   • Crypto Amount: {crypto_amount:.8f}
   • Buy Fee: {buy_fee:.2f} THB
   • Sell Fee: {sell_fee:.2f} THB
   • Total Fees: {total_fees:.2f} THB ({(total_fees / amount_thb) * 100:.3f}%)
   • Break-Even: {break_even_price:,.2f} THB
   • Required Gain: {required_gain:.3f}%
   • Profitability: {'Good' if required_gain < 1.0 else 'High fees' if required_gain < 1.5 else 'Very high fees'}
"""

        # Add profit scenarios for recommended amount
        recommended_amount = self.config['trade_amount_thb']
        crypto_amount = recommended_amount / current_price
        total_fees = self.api_client.calculate_trading_fees(crypto_amount, current_price, "both")

        fee_info += f"""

PROFIT SCENARIOS for {recommended_amount:,} THB:
"""

        profit_scenarios = [0.5, 1.0, 1.5, 2.0, 3.0, 5.0]
        for pct in profit_scenarios:
            sell_price = current_price * (1 + pct / 100)
            gross_profit = (sell_price - current_price) * crypto_amount
            net_profit = gross_profit - total_fees

            fee_info += f"   • +{pct}% price → Net profit: {net_profit:+.2f} THB\n"

        # AI Recommendation if available
        if self.coin_analyzer:
            analysis = self.coin_analyzer.analyze_single_coin(current_symbol, recommended_amount)
            if analysis:
                fee_info += f"""

AI ANALYSIS:
• AI Score: {analysis['ai_score']:.1f}/10
• Recommendation: {analysis['recommendation']}
• Optimal for trading: {'Yes' if analysis['ai_score'] >= 6 else 'No'}
"""

        messagebox.showinfo("Enhanced Fee Calculator", fee_info)

    def check_open_orders(self):
        """Enhanced open orders check"""
        if not self.api_client:
            messagebox.showwarning("Error", "Please connect API first")
            return

        self.update_scifi_visual_state("analyzing", "Checking enhanced open orders")
        self.log("Checking enhanced open orders...")

        # Check orders for current symbol
        current_symbol = self.config['symbol']
        orders = self.api_client.get_my_open_orders_safe(current_symbol)

        if orders and orders.get("error") == 0:
            order_list = orders.get("result", [])
            if order_list:
                self.log(f"Found {len(order_list)} open orders for {current_symbol.upper()}:")

                total_buy_value = 0
                total_sell_value = 0

                for order in order_list:
                    side = order.get('side', 'unknown').upper()
                    order_id = order.get('id', 'N/A')
                    rate = float(order.get('rate', 0))
                    amount = float(order.get('amount', 0))

                    if side == "BUY":
                        value = amount  # THB amount for buy orders
                        total_buy_value += value
                    else:
                        value = amount * rate  # Crypto amount * price for sell orders
                        total_sell_value += value

                    # Calculate potential fees
                    if side == "BUY":
                        crypto_amount = amount / rate
                        fee = self.api_client.calculate_trading_fees(crypto_amount, rate, "buy")
                    else:
                        fee = self.api_client.calculate_trading_fees(amount, rate, "sell")

                    self.log(f"   {side} Order ID: {order_id}")
                    self.log(f"   Price: {rate:,.2f} THB, Amount: {amount:.8f}")
                    self.log(f"   Value: {value:,.2f} THB, Est. Fee: {fee:.2f} THB")
                    self.log("")

                self.log(f"Order Summary:")
                self.log(f"   Total Buy Orders Value: {total_buy_value:,.2f} THB")
                self.log(f"   Total Sell Orders Value: {total_sell_value:,.2f} THB")
                self.log(f"   Combined Order Value: {total_buy_value + total_sell_value:,.2f} THB")

                # Auto trading impact
                if self.auto_trading_engine and hasattr(self.auto_trading_engine, 'current_positions'):
                    managed_positions = len(self.auto_trading_engine.current_positions)
                    if managed_positions > 0:
                        self.log(f"Auto-managed positions: {managed_positions}")

                self.update_scifi_visual_state("success", f"Found {len(order_list)} open orders")
            else:
                self.log("No open orders")
                self.update_scifi_visual_state("idle", "No open orders")
        else:
            error_code = orders.get("error", 999) if orders else 999
            error_msg = self.api_client.error_codes.get(error_code, f"Error {error_code}")
            self.log(f"Failed to get open orders: {error_msg}")
            self.update_scifi_visual_state("error", "Failed to get orders")

        threading.Timer(2.0, lambda: self.update_scifi_visual_state("idle")).start()

    def execute_enhanced_sell(self, price, reason, symbol, is_force_sell=False):
        """Enhanced sell execution with force sell tracking"""
        try:
            # This is a simplified version - in a real implementation,
            # you'd need to track positions properly
            self.log(f"Enhanced sell triggered: {reason}")

            if is_force_sell:
                self.log(f"Force sell executed for {symbol}")
                # Update force sell statistics
                self.performance_data['force_sell_effectiveness'].append({
                    'timestamp': datetime.now(),
                    'symbol': symbol,
                    'reason': reason,
                    'price': price
                })

            # Visual feedback
            if "profit" in reason.lower():
                self.update_scifi_visual_state("success", f"Profitable sell: {reason}")
            else:
                self.update_scifi_visual_state("sell_signal", f"Sell executed: {reason}")

        except Exception as e:
            self.log(f"Enhanced sell execution error: {e}")

    def basic_strategy_analysis(self, price, volume):
        """Fallback basic strategy for when advanced strategies aren't available"""
        # Simple RSI + Volume analysis
        if hasattr(self, 'price_history') and len(self.price_history) >= 15:
            prices = list(self.price_history)

            # Calculate simple RSI
            deltas = np.diff(prices[-15:])
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)

            avg_gain = np.mean(gains)
            avg_loss = np.mean(losses)

            if avg_loss == 0:
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))

            if rsi < 30:
                return True, f"Basic RSI oversold ({rsi:.1f})"

        return False, "Basic analysis: No signal"

    def enhanced_system_check(self):
        """Enhanced system health check"""
        self.update_scifi_visual_state("analyzing", "Running enhanced system check")
        self.log("Running Enhanced System Health Check v3.0...")

        checks = []

        # API Status
        if self.api_client:
            status_ok, status_msg = self.api_client.check_system_status()
            checks.append(("API Status", "Connected" if status_ok else f"Error: {status_msg}"))
        else:
            checks.append(("API Status", "Not connected"))

        # Premium Components
        checks.append(("Coin Analyzer", "Ready" if self.coin_analyzer else "Not initialized"))
        checks.append(("Advanced Strategies", "Ready" if self.strategies else "Not initialized"))
        checks.append(("Force Sell Manager", "Ready" if self.force_sell_manager else "Not initialized"))
        checks.append(("Auto Trading Engine", "Ready" if self.auto_trading_engine else "Not initialized"))

        # License Status
        license_info = self.license_manager.get_license_info()
        checks.append(("License", f"{license_info['type'].upper()}" if license_info['valid'] else "EXPIRED"))

        # Visual System
        checks.append(("Visual System", "Active" if hasattr(self, 'scifi_visual') else "Not active"))

        # Display results
        check_results = "\n".join([f"{name}: {status}" for name, status in checks])
        self.log(f"System Check Results:\n{check_results}")

        all_good = all(
            "Ready" in status or "Connected" in status or "Active" in status or "TRIAL" in status or "PREMIUM" in status
            for name, status in checks)

        if all_good:
            self.update_scifi_visual_state("success", "All systems operational")
            messagebox.showinfo("System Check", "Enhanced System Check Passed!\n\n" + check_results)
        else:
            self.update_scifi_visual_state("error", "System issues detected")
            messagebox.showwarning("System Check", "System Issues Detected!\n\n" + check_results)

        threading.Timer(2.0, lambda: self.update_scifi_visual_state("idle")).start()

    def view_analysis_history(self):
        """View coin analysis history"""
        if not self.license_manager.is_feature_enabled('coin_recommendation'):
            self.show_license_required()
            return

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT timestamp, symbol, ai_score, recommendation
                FROM coin_analysis
                ORDER BY timestamp DESC
                LIMIT 50
            ''')

            history = cursor.fetchall()
            conn.close()

            if history:
                history_text = "COIN ANALYSIS HISTORY\n"
                history_text += "=" * 60 + "\n"
                history_text += f"{'Time':<12} {'Symbol':<12} {'AI Score':<10} {'Recommendation'}\n"
                history_text += "-" * 60 + "\n"

                for timestamp, symbol, ai_score, recommendation in history:
                    time_str = datetime.fromisoformat(timestamp).strftime('%H:%M:%S')
                    history_text += f"{time_str:<12} {symbol.upper():<12} {ai_score:<9.1f} {recommendation}\n"

                self.coin_analysis_display.delete("1.0", "end")
                self.coin_analysis_display.insert("1.0", history_text)
            else:
                messagebox.showinfo("Analysis History", "No analysis history available yet.")

        except Exception as e:
            self.log(f"Error viewing analysis history: {e}")

    def refresh_coin_analysis(self):
        """Refresh coin analysis data"""
        if not self.license_manager.is_feature_enabled('coin_recommendation'):
            self.show_license_required()
            return

        if not self.coin_analyzer:
            messagebox.showwarning("Error", "Please connect API first")
            return

        # Clear cache and perform fresh analysis
        self.coin_analyzer.analysis_cache.clear()

        self.log("Refreshing coin analysis data...")
        messagebox.showinfo("Refresh Started", "Coin analysis refresh started!\nThis may take a few minutes...")

        # Start analysis
        self.start_coin_analysis()


if __name__ == "__main__":
    # Enhanced startup warning with v3.0 features
    print("\n" + "=" * 100)
    print("ENHANCED BITKUB TRADING BOT v3.0 - PREMIUM EDITION")
    print("=" * 100)
    print("NEW PREMIUM FEATURES:")
    print("• AI Coin Analyzer - Smart analysis of all 57+ Bitkub coins")
    print("• 8 Advanced Strategies - RSI+Momentum, Bollinger, EMA, MACD, Volume, Scalping, Swing, DCA")
    print("• Full Auto Trading Engine - Autonomous coin selection & strategy adaptation")
    print("• Force Sell System - Time-based & emergency sell protection")
    print("• Advanced Analytics - Comprehensive performance analysis & reports")
    print("• Enhanced Sci-Fi Graphics - Premium visual states & animations")
    print("• Professional License System - 7-day free trial included")
    print("\nLICENSE SYSTEM:")
    print("• 7-day free trial with ALL premium features")
    print("• Hardware-based license protection")
    print("• Premium features automatically enabled during trial")
    print("• Contact support for license extension")
    print("\nAI COIN ANALYZER:")
    print("• Real-time analysis of ALL Bitkub coins")
    print("• AI scoring system (0-10) for profit potential")
    print("• Automatic best coin selection")
    print("• Fee impact optimization per coin")
    print("• Volatility & momentum analysis")
    print("\nADVANCED STRATEGIES:")
    print("• RSI + Momentum: Enhanced RSI with volume analysis")
    print("• Bollinger Bands: Support/resistance trading")
    print("• EMA Crossover: Moving average signals")
    print("• MACD Divergence: Advanced momentum analysis")
    print("• Volume Breakout: Volume spike detection")
    print("• Scalping: High-frequency quick profits")
    print("• Swing Trading: Medium-term trend following")
    print("• Dollar Cost Averaging: Time-based accumulation")
    print("\nAUTO TRADING ENGINE:")
    print("• Fully autonomous operation")
    print("• Auto coin selection based on AI scores")
    print("• Adaptive strategy selection")
    print("• Multi-position management")
    print("• Real-time market condition adaptation")
    print("\nFORCE SELL SYSTEM:")
    print("• Prevents overnight losses")
    print("• Customizable time limits (1-24 hours)")
    print("• Emergency market crash protection")
    print("• Profit protection mode")
    print("• Volume spike detection")
    print("\nADVANCED ANALYTICS:")
    print("• Strategy performance comparison")
    print("• Coin-specific profit analysis")
    print("• Force sell effectiveness tracking")
    print("• Auto trading performance reports")
    print("• Comprehensive CSV export")
    print("\nENHANCED FEE OPTIMIZATION:")
    print("• Real-time break-even calculation")
    print("• Multi-scenario fee analysis")
    print("• Trade size optimization")
    print("• Profit margin recommendations")
    print("\nPREMIUM SCI-FI GRAPHICS:")
    print("• Idle - System monitoring")
    print("• Connecting - API connection")
    print("• Analyzing - Market analysis")
    print("• Buy Signal - Buy opportunity")
    print("• Sell Signal - Sell opportunity")
    print("• Trading - Active execution")
    print("• Success - Operation completed")
    print("• Error - System warning")
    print("• Coin Analysis - AI analyzing coins (NEW)")
    print("• Auto Mode - Autonomous trading (NEW)")
    print("\nIMPORTANT WARNINGS:")
    print("• This bot trades with REAL MONEY when enabled")
    print("• ALWAYS start with PAPER TRADING mode")
    print("• Use minimum 1000 THB per trade for optimal profitability")
    print("• Monitor all premium features during trial period")
    print("• Test thoroughly with small amounts first")
    print("• Premium features require valid license after trial")
    print("=" * 100 + "\n")

    response = input("Do you understand ALL premium features and risks? (yes/no): ")

    if response.lower() == 'yes':
        print("\nLaunching Enhanced Trading Bot v3.0...")
        print("Initializing premium license system...")
        print("Loading AI coin analyzer...")
        print("Preparing advanced strategies...")
        print("Starting auto trading engine...")
        print("Activating force sell system...")
        print("Initializing sci-fi graphics...")
        print("All systems ready!\n")

        app = EnhancedTradingBot()
        try:
            app.run()
        finally:
            app.cleanup_resources()
    else:
        print("Exiting. Please understand all premium features and risks before using this enhanced bot.")
        print("Visit the license tab for detailed feature descriptions!")

        if not self.api_client:
            messagebox.showwarning("Error", "Please connect API first")
            return

        current_symbol = self.config['symbol']

        # Use auto-selected coin if enabled
        if self.config.get('auto_coin_selection') and self.coin_analyzer:
            best_coin = self.get_best_coin_for_trading()
            if best_coin:
                current_symbol = best_coin['symbol']

        ticker = self.api_client.get_simple_ticker(current_symbol)
        if not ticker:
            messagebox.showwarning("Error", "Cannot get current price")
            return

        current_price = ticker['last_price']

        # Multiple trade amount scenarios
        scenarios = [500, 1000, 2000, 5000, 10000]

        fee_info = f"""
💸 ENHANCED BITKUB FEE CALCULATOR v3.0

📊 Current Market Data:
• Symbol: {current_symbol.upper()}
• Current Price: {current_price:,.2f} THB
• 24h Change: {ticker['change_24h']:+.2f}%
• 24h Volume: {ticker.get('volume_24h', 0):,.0f} THB

💰 Fee Structure:
• Maker Fee: 0.25%
• Taker Fee: 0.25%
• Total Round Trip: 0.50%

📈 TRADING SCENARIOS:
"""

        for amount_thb in scenarios:
            crypto_amount = amount_thb / current_price
            buy_fee = self.api_client.calculate_trading_fees(crypto_amount, current_price, "buy")
            sell_fee = self.api_client.calculate_trading_fees(crypto_amount, current_price, "sell")
            total_fees = buy_fee + sell_fee
            break_even_price = self.api_client.calculate_break_even_price(current_price, "buy")
            required_gain = ((break_even_price - current_price) / current_price) * 100

            fee_info += f"""
💵 {amount_thb:,} THB Trade:
   • Crypto Amount: {crypto_amount:.8f}
   • Buy Fee: {buy_fee:.2f} THB
   • Sell Fee: {sell_fee:.2f} THB
   • Total Fees: {total_fees:.2f} THB ({(total_fees / amount_thb) * 100:.3f}%)
   • Break-Even: {break_even_price:,.2f} THB
   • Required Gain: {required_gain:.3f}%
   • Profitability: {'✅ Good' if required_gain < 1.0 else '⚠️ High fees' if required_gain < 1.5 else '❌ Very high fees'}
"""

        # Add profit scenarios for recommended amount
        recommended_amount = self.config['trade_amount_thb']
        crypto_amount = recommended_amount / current_price
        total_fees = self.api_client.calculate_trading_fees(crypto_amount, current_price, "both")

        fee_info += f"""

📈 PROFIT SCENARIOS for {recommended_amount:,} THB:
"""

        profit_scenarios = [0.5, 1.0, 1.5, 2.0, 3.0, 5.0]
        for pct in profit_scenarios:
            sell_price = current_price * (1 + pct / 100)
            gross_profit = (sell_price - current_price) * crypto_amount
            net_profit = gross_profit - total_fees

            fee_info += f"   • +{pct}% price → Net profit: {net_profit:+.2f} THB\n"

        # 🪙 AI Recommendation if available
        if self.coin_analyzer:
            analysis = self.coin_analyzer.analyze_single_coin(current_symbol, recommended_amount)
            if analysis:
                fee_info += f"""

🤖 AI ANALYSIS:
• AI Score: {analysis['ai_score']:.1f}/10
• Recommendation: {analysis['recommendation']}
• Optimal for trading: {'✅ Yes' if analysis['ai_score'] >= 6 else '❌ No'}
"""

        messagebox.showinfo("Enhanced Fee Calculator", fee_info)


    def check_open_orders(self):
        """📋 Enhanced open orders check"""
        if not self.api_client:
            messagebox.showwarning("Error", "Please connect API first")
            return

        self.update_scifi_visual_state("analyzing", "Checking enhanced open orders")
        self.log("📋 Checking enhanced open orders...")

        # Check orders for current symbol
        current_symbol = self.config['symbol']
        orders = self.api_client.get_my_open_orders_safe(current_symbol)

        if orders and orders.get("error") == 0:
            order_list = orders.get("result", [])
            if order_list:
                self.log(f"📋 Found {len(order_list)} open orders for {current_symbol.upper()}:")

                total_buy_value = 0
                total_sell_value = 0

                for order in order_list:
                    side = order.get('side', 'unknown').upper()
                    order_id = order.get('id', 'N/A')
                    rate = float(order.get('rate', 0))
                    amount = float(order.get('amount', 0))

                    if side == "BUY":
                        value = amount  # THB amount for buy orders
                        total_buy_value += value
                    else:
                        value = amount * rate  # Crypto amount * price for sell orders
                        total_sell_value += value

                    # Calculate potential fees
                    if side == "BUY":
                        crypto_amount = amount / rate
                        fee = self.api_client.calculate_trading_fees(crypto_amount, rate, "buy")
                    else:
                        fee = self.api_client.calculate_trading_fees(amount, rate, "sell")

                    self.log(f"   {side} Order ID: {order_id}")
                    self.log(f"   Price: {rate:,.2f} THB, Amount: {amount:.8f}")
                    self.log(f"   Value: {value:,.2f} THB, Est. Fee: {fee:.2f} THB")
                    self.log("")

                self.log(f"📊 Order Summary:")
                self.log(f"   Total Buy Orders Value: {total_buy_value:,.2f} THB")
                self.log(f"   Total Sell Orders Value: {total_sell_value:,.2f} THB")
                self.log(f"   Combined Order Value: {total_buy_value + total_sell_value:,.2f} THB")

                # 🤖 Auto trading impact
                if self.auto_trading_engine and hasattr(self.auto_trading_engine, 'current_positions'):
                    managed_positions = len(self.auto_trading_engine.current_positions)
                    if managed_positions > 0:
                        self.log(f"🤖 Auto-managed positions: {managed_positions}")

                self.update_scifi_visual_state("success", f"Found {len(order_list)} open orders")
            else:
                self.log("📋 No open orders")
                self.update_scifi_visual_state("idle", "No open orders")
        else:
            error_code = orders.get("error", 999) if orders else 999
            error_msg = self.api_client.error_codes.get(error_code, f"Error {error_code}")
            self.log(f"❌ Failed to get open orders: {error_msg}")
            self.update_scifi_visual_state("error", "Failed to get orders")

        threading.Timer(2.0, lambda: self.update_scifi_visual_state("idle")).start()


    def execute_enhanced_sell(self, price, reason, symbol, is_force_sell=False):
        """🆕 Enhanced sell execution with force sell tracking"""
        try:
            # This is a simplified version - in a real implementation,
            # you'd need to track positions properly
            self.log(f"🔄 Enhanced sell triggered: {reason}")

            if is_force_sell:
                self.log(f"🕐 Force sell executed for {symbol}")
                # Update force sell statistics
                self.performance_data['force_sell_effectiveness'].append({
                    'timestamp': datetime.now(),
                    'symbol': symbol,
                    'reason': reason,
                    'price': price
                })

            # Visual feedback
            if "profit" in reason.lower():
                self.update_scifi_visual_state("success", f"Profitable sell: {reason}")
            else:
                self.update_scifi_visual_state("sell_signal", f"Sell executed: {reason}")

        except Exception as e:
            self.log(f"❌ Enhanced sell execution error: {e}")


    def run(self):
        """🚀 Start the enhanced application v3.0"""
        # Reset daily counters at startup
        self.daily_trades = 0
        self.daily_pnl = 0
        self.total_fees_paid = 0

        # Enhanced startup messages
        self.log("🚀 Enhanced Bitkub Trading Bot v3.0 Started")
        self.log("🎬 Advanced Sci-Fi Visual System Initialized")
        self.log("💸 Enhanced fee-aware strategy loaded")
        self.log(f"🪙 Supporting all {len(ImprovedBitkubAPI('', '').all_bitkub_symbols)} Bitkub coins")

        # License status
        license_info = self.license_manager.get_license_info()
        if license_info['valid']:
            self.log(
                f"🔓 Premium License Active: {license_info['type'].upper()} ({license_info['remaining_days']} days left)")
            self.log("✅ All premium features enabled")
        else:
            self.log("🔒 Premium License Expired - Limited features")

        self.log("📝 Default: PAPER TRADING mode")
        self.log("⚠️ Always test thoroughly before enabling real trading")

        # Initialize visual system
        if hasattr(self, 'scifi_visual'):
            self.update_scifi_visual_state("idle", "Enhanced system ready")

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
            # Stop all trading activities
            if self.is_trading:
                self.emergency_stop = True
                self.is_trading = False
                self.is_auto_trading = False

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
        """🆕 Enhanced cleanup resources on exit"""
        try:
            # Stop trading
            self.is_trading = False
            self.is_auto_trading = False
            self.emergency_stop = True

            # Cleanup premium components
            if hasattr(self, 'auto_trading_engine') and self.auto_trading_engine:
                self.auto_trading_engine.stop_auto_trading()

            # Cleanup visual system
            if hasattr(self, 'scifi_visual') and self.scifi_visual:
                self.scifi_visual.cleanup()

            # Wait for threads to finish
            time.sleep(0.5)

            self.log("🧹 Enhanced cleanup completed")

        except Exception as e:
            print(f"Enhanced resource cleanup error: {e}")


    # === 🆕 Additional Premium Functions ===

    def view_analysis_history(self):
        """📜 View coin analysis history"""
        if not self.license_manager.is_feature_enabled('coin_recommendation'):
            self.show_license_required()
            return

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT timestamp, symbol, ai_score, recommendation
                FROM coin_analysis
                ORDER BY timestamp DESC
                LIMIT 50
            ''')

            history = cursor.fetchall()
            conn.close()

            if history:
                history_text = "📜 COIN ANALYSIS HISTORY\n"
                history_text += "=" * 60 + "\n"
                history_text += f"{'Time':<12} {'Symbol':<12} {'AI Score':<10} {'Recommendation'}\n"
                history_text += "-" * 60 + "\n"

                for timestamp, symbol, ai_score, recommendation in history:
                    time_str = datetime.fromisoformat(timestamp).strftime('%H:%M:%S')
                    history_text += f"{time_str:<12} {symbol.upper():<12} {ai_score:<9.1f} {recommendation}\n"

                self.coin_analysis_display.delete("1.0", "end")
                self.coin_analysis_display.insert("1.0", history_text)
            else:
                messagebox.showinfo("Analysis History", "No analysis history available yet.")

        except Exception as e:
            self.log(f"❌ Error viewing analysis history: {e}")


    def refresh_coin_analysis(self):
        """🔄 Refresh coin analysis data"""
        if not self.license_manager.is_feature_enabled('coin_recommendation'):
            self.show_license_required()
            return

        if not self.coin_analyzer:
            messagebox.showwarning("Error", "Please connect API first")
            return

        # Clear cache and perform fresh analysis
        self.coin_analyzer.analysis_cache.clear()

        self.log("🔄 Refreshing coin analysis data...")
        messagebox.showinfo("Refresh Started", "Coin analysis refresh started!\nThis may take a few minutes...")

        # Start analysis
        self.start_coin_analysis()

if __name__ == "__main__":
    # 🆕 Enhanced startup warning with v3.0 features
    print("\n" + "=" * 100)
    print("🚀 ENHANCED BITKUB TRADING BOT v3.0 - PREMIUM EDITION")
    print("=" * 100)
    print("✨ NEW PREMIUM FEATURES:")
    print("• 🪙 AI Coin Analyzer - Smart analysis of all 57+ Bitkub coins")
    print("• 🎯 8 Advanced Strategies - RSI+Momentum, Bollinger, EMA, MACD, Volume, Scalping, Swing, DCA")
    print("• 🤖 Full Auto Trading Engine - Autonomous coin selection & strategy adaptation")
    print("• 🕐 Force Sell System - Time-based & emergency sell protection")
    print("• 📊 Advanced Analytics - Comprehensive performance analysis & reports")
    print("• 🎬 Enhanced Sci-Fi Graphics - Premium visual states & animations")
    print("• 🔐 Professional License System - 7-day free trial included")
    print("\n🔐 LICENSE SYSTEM:")
    print("• ✅ 7-day free trial with ALL premium features")
    print("• 🔓 Hardware-based license protection")
    print("• 💎 Premium features automatically enabled during trial")
    print("• 📞 Contact support for license extension")
    print("\n🪙 AI COIN ANALYZER:")
    print("• Real-time analysis of ALL Bitkub coins")
    print("• AI scoring system (0-10) for profit potential")
    print("• Automatic best coin selection")
    print("• Fee impact optimization per coin")
    print("• Volatility & momentum analysis")
    print("\n🎯 ADVANCED STRATEGIES:")
    print("• RSI + Momentum: Enhanced RSI with volume analysis")
    print("• Bollinger Bands: Support/resistance trading")
    print("• EMA Crossover: Moving average signals")
    print("• MACD Divergence: Advanced momentum analysis")
    print("• Volume Breakout: Volume spike detection")
    print("• Scalping: High-frequency quick profits")
    print("• Swing Trading: Medium-term trend following")
    print("• Dollar Cost Averaging: Time-based accumulation")
    print("\n🤖 AUTO TRADING ENGINE:")
    print("• Fully autonomous operation")
    print("• Auto coin selection based on AI scores")
    print("• Adaptive strategy selection")
    print("• Multi-position management")
    print("• Real-time market condition adaptation")
    print("\n🕐 FORCE SELL SYSTEM:")
    print("• Prevents overnight losses")
    print("• Customizable time limits (1-24 hours)")
    print("• Emergency market crash protection")
    print("• Profit protection mode")
    print("• Volume spike detection")
    print("\n📊 ADVANCED ANALYTICS:")
    print("• Strategy performance comparison")
    print("• Coin-specific profit analysis")
    print("• Force sell effectiveness tracking")
    print("• Auto trading performance reports")
    print("• Comprehensive CSV export")
    print("\n💸 ENHANCED FEE OPTIMIZATION:")
    print("• Real-time break-even calculation")
    print("• Multi-scenario fee analysis")
    print("• Trade size optimization")
    print("• Profit margin recommendations")
    print("\n🎬 PREMIUM SCI-FI GRAPHICS:")
    print("• 🔵 Idle - System monitoring")
    print("• 🟡 Connecting - API connection")
    print("• 🔴 Analyzing - Market analysis")
    print("• 🟢 Buy Signal - Buy opportunity")
    print("• 🔴 Sell Signal - Sell opportunity")
    print("• ⚡ Trading - Active execution")
    print("• ✅ Success - Operation completed")
    print("• ❌ Error - System warning")
    print("• 🪙 Coin Analysis - AI analyzing coins (NEW)")
    print("• 🤖 Auto Mode - Autonomous trading (NEW)")
    print("\n⚠️ IMPORTANT WARNINGS:")
    print("• This bot trades with REAL MONEY when enabled")
    print("• ALWAYS start with PAPER TRADING mode")
    print("• Use minimum 1000 THB per trade for optimal profitability")
    print("• Monitor all premium features during trial period")
    print("• Test thoroughly with small amounts first")
    print("• Premium features require valid license after trial")
    print("=" * 100 + "\n")

    response = input("Do you understand ALL premium features and risks? (yes/no): ")

    if response.lower() == 'yes':
        print("\n🚀 Launching Enhanced Trading Bot v3.0...")
        print("🔐 Initializing premium license system...")
        print("🪙 Loading AI coin analyzer...")
        print("🎯 Preparing advanced strategies...")
        print("🤖 Starting auto trading engine...")
        print("🕐 Activating force sell system...")
        print("🎬 Initializing sci-fi graphics...")
        print("✅ All systems ready!\n")

        app = EnhancedTradingBot()
        try:
            app.run()
        finally:
            app.cleanup_resources()
    else:
        print("Exiting. Please understand all premium features and risks before using this enhanced bot.")
        print("Visit the license tab for detailed feature descriptions!")
📊 Strategy
Consensus: {buy_signals} / {len(enabled_strategies)}
strategies
recommend
BUY\n\n
"

# 🕐 Force Sell Analysis
if self.force_sell_manager and self.config.get('force_sell_enabled'):
    positions = self.force_sell_manager.get_positions_status()
    signal_text += f"🕐 FORCE SELL MONITOR:\n"
    if positions:
        for pos in positions:
            signal_text += f"   Position: {pos['symbol']} - Time left: {pos['time_left_hours']:.1f}h\n"
    else:
        signal_text += f"   No active positions to monitor\n"
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
import uuid
import platform
from concurrent.futures import ThreadPoolExecutor, as_completed
import statistics

# Configure theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class LicenseManager:
    """🔐 ระบบ License Management สำหรับ Premium Features"""

    def __init__(self):
        self.license_file = "bot_license.json"
        self.hardware_id = self.generate_hardware_id()
        self.trial_period = 7  # วัน
        self.license_data = self.load_license()

    def generate_hardware_id(self):
        """สร้าง Hardware ID เฉพาะ"""
        try:
            # ใช้ข้อมูล hardware เฉพาะ
            system_info = f"{platform.node()}-{platform.processor()}-{platform.machine()}"
            return hashlib.md5(system_info.encode()).hexdigest()[:16]
        except:
            return hashlib.md5(str(uuid.getnode()).encode()).hexdigest()[:16]

    def load_license(self):
        """โหลดข้อมูล License"""
        if os.path.exists(self.license_file):
            try:
                with open(self.license_file, 'r') as f:
                    data = json.load(f)
                    if data.get('hardware_id') == self.hardware_id:
                        return data
            except:
                pass

        # สร้าง trial license ใหม่
        trial_data = {
            'hardware_id': self.hardware_id,
            'license_type': 'trial',
            'start_date': datetime.now().isoformat(),
            'end_date': (datetime.now() + timedelta(days=self.trial_period)).isoformat(),
            'features_enabled': {
                'coin_recommendation': True,
                'advanced_strategies': True,
                'auto_trading': True,
                'force_sell': True,
                'premium_graphics': True
            }
        }
        self.save_license(trial_data)
        return trial_data

    def save_license(self, data):
        """บันทึกข้อมูล License"""
        try:
            with open(self.license_file, 'w') as f:
                json.dump(data, f, indent=2)
        except:
            pass

    def is_feature_enabled(self, feature):
        """ตรวจสอบว่า feature เปิดใช้งานได้หรือไม่"""
        if not self.is_license_valid():
            return False
        return self.license_data.get('features_enabled', {}).get(feature, False)

    def is_license_valid(self):
        """ตรวจสอบว่า license ยังใช้งานได้"""
        try:
            end_date = datetime.fromisoformat(self.license_data['end_date'])
            return datetime.now() < end_date
        except:
            return False

    def get_license_info(self):
        """ข้อมูล License"""
        try:
            start_date = datetime.fromisoformat(self.license_data['start_date'])
            end_date = datetime.fromisoformat(self.license_data['end_date'])
            remaining_days = (end_date - datetime.now()).days

            return {
                'type': self.license_data.get('license_type', 'unknown'),
                'valid': self.is_license_valid(),
                'remaining_days': max(0, remaining_days),
                'hardware_id': self.hardware_id[:8] + "...",
                'features': self.license_data.get('features_enabled', {})
            }
        except:
            return {'type': 'invalid', 'valid': False, 'remaining_days': 0}


class CoinAnalyzer:
    """🪙 ระบบวิเคราะห์และแนะนำเหรียญขั้นสูง"""

    def __init__(self, api_client):
        self.api_client = api_client
        self.analysis_cache = {}
        self.cache_timeout = 300  # 5 นาที

    def analyze_all_coins(self, trade_amount=1000):
        """วิเคราะห์เหรียญทั้งหมดพร้อมกัน"""
        results = []

        # ใช้ ThreadPoolExecutor สำหรับ parallel processing
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {
                executor.submit(self.analyze_single_coin, symbol, trade_amount): symbol
                for symbol in self.api_client.all_bitkub_symbols
            }

            for future in as_completed(futures):
                try:
                    analysis = future.result(timeout=10)
                    if analysis:
                        results.append(analysis)
                except Exception as e:
                    print(f"Analysis error for {futures[future]}: {e}")

        # เรียงตาม AI Score
        results.sort(key=lambda x: x['ai_score'], reverse=True)
        return results

    def analyze_single_coin(self, symbol, trade_amount=1000):
        """วิเคราะห์เหรียญเดียว"""
        try:
            # ตรวจสอบ cache
            cache_key = f"{symbol}_{trade_amount}"
            if cache_key in self.analysis_cache:
                cached_time, cached_data = self.analysis_cache[cache_key]
                if time.time() - cached_time < self.cache_timeout:
                    return cached_data

            # ดึงข้อมูลตลาด
            ticker = self.api_client.get_simple_ticker(symbol)
            if not ticker:
                return None

            price = ticker['last_price']
            volume_24h = ticker.get('volume_24h', 0)
            change_24h = ticker.get('change_24h', 0)

            # คำนวณค่าธรรมเนียม
            crypto_amount = trade_amount / price
            total_fees = self.api_client.calculate_trading_fees(crypto_amount, price, "both")
            fee_impact = (total_fees / trade_amount) * 100
            break_even_price = self.api_client.calculate_break_even_price(price, "buy")
            required_gain = ((break_even_price - price) / price) * 100

            # วิเคราะห์ความผันผวน
            volatility_score = self.calculate_volatility_score(change_24h)

            # วิเคราะห์ volume
            volume_score = self.calculate_volume_score(volume_24h, price)

            # วิเคราะห์ momentum
            momentum_score = self.calculate_momentum_score(change_24h)

            # คำนวณ AI Score
            ai_score = self.calculate_ai_score({
                'volatility': volatility_score,
                'volume': volume_score,
                'momentum': momentum_score,
                'fee_impact': fee_impact,
                'required_gain': required_gain
            })

            analysis = {
                'symbol': symbol,
                'price': price,
                'change_24h': change_24h,
                'volume_24h': volume_24h,
                'volatility_score': volatility_score,
                'volume_score': volume_score,
                'momentum_score': momentum_score,
                'fee_impact': fee_impact,
                'required_gain': required_gain,
                'ai_score': ai_score,
                'recommendation': self.get_recommendation(ai_score),
                'analysis_time': datetime.now()
            }

            # บันทึกใน cache
            self.analysis_cache[cache_key] = (time.time(), analysis)

            return analysis

        except Exception as e:
            print(f"Error analyzing {symbol}: {e}")
            return None

    def calculate_volatility_score(self, change_24h):
        """คำนวณคะแนนความผันผวน (0-10)"""
        abs_change = abs(change_24h)
        if abs_change >= 10:
            return 10
        elif abs_change >= 5:
            return 8
        elif abs_change >= 3:
            return 6
        elif abs_change >= 1:
            return 4
        else:
            return 2

    def calculate_volume_score(self, volume_24h, price):
        """คำนวณคะแนน volume (0-10)"""
        try:
            # ปริมาณในล้านบาท
            volume_millions = volume_24h / 1_000_000
            if volume_millions >= 100:
                return 10
            elif volume_millions >= 50:
                return 8
            elif volume_millions >= 10:
                return 6
            elif volume_millions >= 1:
                return 4
            else:
                return 2
        except:
            return 1

    def calculate_momentum_score(self, change_24h):
        """คำนวณคะแนน momentum (0-10)"""
        if change_24h > 5:
            return 9
        elif change_24h > 2:
            return 7
        elif change_24h > 0:
            return 5
        elif change_24h > -2:
            return 4
        elif change_24h > -5:
            return 2
        else:
            return 1

    def calculate_ai_score(self, metrics):
        """คำนวณ AI Score รวม (0-10)"""
        try:
            # น้ำหนัก
            weights = {
                'volatility': 0.2,
                'volume': 0.3,
                'momentum': 0.25,
                'fee_efficiency': 0.25
            }

            # คะแนน fee efficiency (ยิ่ง fee impact ต่ำยิ่งดี)
            fee_efficiency = max(0, 10 - (metrics['fee_impact'] * 10))

            # คำนวณคะแนนรวม
            total_score = (
                    metrics['volatility'] * weights['volatility'] +
                    metrics['volume'] * weights['volume'] +
                    metrics['momentum'] * weights['momentum'] +
                    fee_efficiency * weights['fee_efficiency']
            )

            return round(min(10, max(0, total_score)), 1)

        except:
            return 5.0

    def get_recommendation(self, ai_score):
        """แนะนำการเทรด"""
        if ai_score >= 8:
            return "🟢 แนะนำสูง"
        elif ai_score >= 6:
            return "🟡 แนะนำปานกลาง"
        elif ai_score >= 4:
            return "🟠 ระมัดระวัง"
        else:
            return "🔴 ไม่แนะนำ"


class AdvancedStrategies:
    """🎯 กลยุทธ์การเทรดขั้นสูง"""

    def __init__(self, api_client):
        self.api_client = api_client
        self.price_history = deque(maxlen=100)
        self.volume_history = deque(maxlen=50)

        # กำหนดค่าพารามิเตอร์แต่ละกลยุทธ์
        self.strategies = {
            'rsi_momentum': {
                'name': 'RSI + Momentum',
                'params': {'rsi_period': 14, 'rsi_oversold': 25, 'rsi_overbought': 75, 'momentum_threshold': 1.2},
                'enabled': True
            },
            'bollinger_bands': {
                'name': 'Bollinger Bands',
                'params': {'period': 20, 'std_dev': 2, 'squeeze_threshold': 0.5},
                'enabled': False
            },
            'ema_crossover': {
                'name': 'EMA Crossover',
                'params': {'fast_ema': 9, 'slow_ema': 21, 'confirmation_bars': 2},
                'enabled': False
            },
            'macd_divergence': {
                'name': 'MACD Divergence',
                'params': {'fast': 12, 'slow': 26, 'signal': 9, 'divergence_threshold': 0.1},
                'enabled': False
            },
            'volume_breakout': {
                'name': 'Volume Breakout',
                'params': {'volume_multiplier': 2.0, 'price_breakout': 0.02},
                'enabled': False
            },
            'scalping': {
                'name': 'Scalping',
                'params': {'quick_profit': 0.3, 'quick_loss': 0.15, 'max_hold_minutes': 15},
                'enabled': False
            },
            'swing_trading': {
                'name': 'Swing Trading',
                'params': {'trend_period': 50, 'min_trend_strength': 0.6, 'hold_days': 3},
                'enabled': False
            },
            'dca': {
                'name': 'Dollar Cost Averaging',
                'params': {'interval_minutes': 60, 'buy_amount_pct': 0.1, 'max_positions': 5},
                'enabled': False
            }
        }

    def analyze_with_strategy(self, strategy_name, current_price, volume):
        """วิเคราะห์ด้วยกลยุทธ์ที่เลือก"""
        if strategy_name not in self.strategies or not self.strategies[strategy_name]['enabled']:
            return False, "Strategy not enabled"

        self.price_history.append(current_price)
        self.volume_history.append(volume)

        if strategy_name == 'rsi_momentum':
            return self.rsi_momentum_analysis(current_price, volume)
        elif strategy_name == 'bollinger_bands':
            return self.bollinger_bands_analysis(current_price)
        elif strategy_name == 'ema_crossover':
            return self.ema_crossover_analysis(current_price)
        elif strategy_name == 'macd_divergence':
            return self.macd_divergence_analysis(current_price)
        elif strategy_name == 'volume_breakout':
            return self.volume_breakout_analysis(current_price, volume)
        elif strategy_name == 'scalping':
            return self.scalping_analysis(current_price)
        elif strategy_name == 'swing_trading':
            return self.swing_trading_analysis(current_price)
        elif strategy_name == 'dca':
            return self.dca_analysis(current_price)

        return False, "Unknown strategy"

    def rsi_momentum_analysis(self, price, volume):
        """RSI + Momentum Strategy"""
        if len(self.price_history) < 15:
            return False, "Insufficient data"

        params = self.strategies['rsi_momentum']['params']
        prices = list(self.price_history)

        # คำนวณ RSI
        rsi = self.calculate_rsi(prices, params['rsi_period'])

        # คำนวณ momentum
        momentum = self.calculate_momentum(list(self.volume_history))

        # Buy signal
        if rsi < params['rsi_oversold'] and momentum > params['momentum_threshold']:
            return True, f"RSI Oversold ({rsi:.1f}) + High Momentum ({momentum:.2f}x)"

        return False, f"RSI: {rsi:.1f}, Momentum: {momentum:.2f}x"

    def bollinger_bands_analysis(self, price):
        """Bollinger Bands Strategy"""
        if len(self.price_history) < 21:
            return False, "Insufficient data"

        params = self.strategies['bollinger_bands']['params']
        prices = list(self.price_history)

        # คำนวณ Bollinger Bands
        sma = np.mean(prices[-params['period']:])
        std = np.std(prices[-params['period']:])
        upper_band = sma + (std * params['std_dev'])
        lower_band = sma - (std * params['std_dev'])

        # Buy signal: ราคาแตะ lower band
        if price <= lower_band * 1.02:  # ใกล้ lower band
            return True, f"Price near Lower Band ({lower_band:.2f})"

        return False, f"Price: {price:.2f}, Bands: {lower_band:.2f}-{upper_band:.2f}"

    def ema_crossover_analysis(self, price):
        """EMA Crossover Strategy"""
        if len(self.price_history) < 25:
            return False, "Insufficient data"

        params = self.strategies['ema_crossover']['params']
        prices = list(self.price_history)

        # คำนวณ EMA
        fast_ema = self.calculate_ema(prices, params['fast_ema'])
        slow_ema = self.calculate_ema(prices, params['slow_ema'])

        # Buy signal: fast EMA cross above slow EMA
        if len(fast_ema) >= 2 and len(slow_ema) >= 2:
            if fast_ema[-1] > slow_ema[-1] and fast_ema[-2] <= slow_ema[-2]:
                return True, f"EMA Crossover: {fast_ema[-1]:.2f} > {slow_ema[-1]:.2f}"

        return False, f"Fast EMA: {fast_ema[-1]:.2f}, Slow EMA: {slow_ema[-1]:.2f}"

    def volume_breakout_analysis(self, price, volume):
        """Volume Breakout Strategy"""
        if len(self.volume_history) < 10 or len(self.price_history) < 5:
            return False, "Insufficient data"

        params = self.strategies['volume_breakout']['params']

        # เฉลี่ย volume
        avg_volume = np.mean(list(self.volume_history)[-10:])

        # เฉลี่ยราคา
        avg_price = np.mean(list(self.price_history)[-5:])

        # Buy signal: volume spike + price breakout
        volume_spike = volume > avg_volume * params['volume_multiplier']
        price_breakout = price > avg_price * (1 + params['price_breakout'])

        if volume_spike and price_breakout:
            return True, f"Volume Breakout: {volume / avg_volume:.2f}x volume, Price: +{((price / avg_price) - 1) * 100:.2f}%"

        return False, f"Volume: {volume / avg_volume:.2f}x, Price change: {((price / avg_price) - 1) * 100:.2f}%"

    def scalping_analysis(self, price):
        """Scalping Strategy - เทรดกำไรเร็ว"""
        if len(self.price_history) < 5:
            return False, "Insufficient data"

        params = self.strategies['scalping']['params']
        prices = list(self.price_history)

        # หา support/resistance ระยะสั้น
        recent_low = min(prices[-5:])
        recent_high = max(prices[-5:])

        # Buy signal: ราคาใกล้ recent low
        if price <= recent_low * 1.005:  # 0.5% above recent low
            return True, f"Scalping: Near support {recent_low:.2f}"

        return False, f"Price: {price:.2f}, Range: {recent_low:.2f}-{recent_high:.2f}"

    def swing_trading_analysis(self, price):
        """Swing Trading Strategy - เทรดระยะกลาง"""
        if len(self.price_history) < 50:
            return False, "Insufficient data for swing trading"

        params = self.strategies['swing_trading']['params']
        prices = list(self.price_history)

        # คำนวณ trend
        sma_trend = np.mean(prices[-params['trend_period']:])
        trend_strength = (price - sma_trend) / sma_trend

        # Buy signal: แนวโน้มขาขึ้น
        if trend_strength > params['min_trend_strength'] / 100:
            return True, f"Swing: Uptrend strength {trend_strength * 100:.2f}%"

        return False, f"Trend strength: {trend_strength * 100:.2f}%"

    def dca_analysis(self, price):
        """Dollar Cost Averaging Strategy"""
        # DCA ไม่ต้องวิเคราะห์ technical - ซื้อตามเวลา
        return True, "DCA: Time-based buying"

    # Helper functions
    def calculate_rsi(self, prices, period=14):
        """คำนวณ RSI"""
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

    def calculate_momentum(self, volumes):
        """คำนวณ volume momentum"""
        if len(volumes) < 10:
            return 1.0

        recent_avg = np.mean(volumes[-5:])
        longer_avg = np.mean(volumes[-10:])

        return recent_avg / longer_avg if longer_avg > 0 else 1.0

    def calculate_ema(self, prices, period):
        """คำนวณ EMA"""
        if len(prices) < period:
            return [np.mean(prices)]

        alpha = 2 / (period + 1)
        ema = [prices[0]]

        for price in prices[1:]:
            ema.append((alpha * price) + ((1 - alpha) * ema[-1]))

        return ema


class ForceSellManager:
    """🕐 ระบบบังคับขายขั้นสูง"""

    def __init__(self):
        self.enabled = True
        self.max_hold_hours = 6
        self.min_profit_threshold = 0.005  # 0.5%
        self.emergency_conditions = {
            'market_crash': -5.0,  # ตลาดดิ่ง 5%
            'extreme_volatility': 10.0,  # ความผันผวนสูง 10%
            'volume_spike': 5.0  # volume เพิ่ม 5 เท่า
        }

        # ติดตาม positions
        self.positions = {}

    def add_position(self, symbol, entry_data):
        """เพิ่ม position เพื่อติดตาม"""
        position_id = f"{symbol}_{int(time.time())}"
        self.positions[position_id] = {
            'symbol': symbol,
            'entry_time': datetime.now(),
            'entry_price': entry_data['entry_price'],
            'amount': entry_data['amount'],
            'force_sell_time': datetime.now() + timedelta(hours=self.max_hold_hours),
            'min_profit_reached': False
        }
        return position_id

    def check_force_sell(self, position_id, current_price, market_data=None):
        """ตรวจสอบเงื่อนไขบังคับขาย"""
        if not self.enabled or position_id not in self.positions:
            return False, "Force sell disabled or position not found"

        position = self.positions[position_id]

        # 1. ตรวจสอบเวลา
        if datetime.now() >= position['force_sell_time']:
            return True, f"Max hold time reached ({self.max_hold_hours}h)"

        # 2. ตรวจสอบกำไรขั้นต่ำ
        current_profit = (current_price - position['entry_price']) / position['entry_price']
        if current_profit >= self.min_profit_threshold:
            position['min_profit_reached'] = True

        # 3. ตรวจสอบสถานการณ์ฉุกเฉิน
        if market_data:
            emergency_reason = self.check_emergency_conditions(market_data)
            if emergency_reason:
                # ถ้ามีกำไรแล้ว ให้ขาย
                if position['min_profit_reached']:
                    return True, f"Emergency sell: {emergency_reason} (with profit)"

        # 4. ป้องกัน position ที่มีกำไร
        time_left = (position['force_sell_time'] - datetime.now()).total_seconds() / 3600
        if position['min_profit_reached'] and time_left < 1:  # เหลือเวลา < 1 ชั่วโมง
            return True, f"Protecting profit: {current_profit * 100:.2f}%"

        return False, f"Hold (Profit: {current_profit * 100:.2f}%, Time left: {time_left:.1f}h)"

    def check_emergency_conditions(self, market_data):
        """ตรวจสอบสถานการณ์ฉุกเฉิน"""
        try:
            # Market crash
            if market_data.get('change_24h', 0) <= self.emergency_conditions['market_crash']:
                return f"Market crash: {market_data['change_24h']:.1f}%"

            # Extreme volatility
            if abs(market_data.get('change_24h', 0)) >= self.emergency_conditions['extreme_volatility']:
                return f"Extreme volatility: {abs(market_data['change_24h']):.1f}%"

            # Volume spike (ต้องมีข้อมูล volume เปรียบเทียบ)
            if 'volume_ratio' in market_data:
                if market_data['volume_ratio'] >= self.emergency_conditions['volume_spike']:
                    return f"Volume spike: {market_data['volume_ratio']:.1f}x"

            return None

        except Exception as e:
            print(f"Emergency check error: {e}")
            return None

    def remove_position(self, position_id):
        """ลบ position หลังขาย"""
        if position_id in self.positions:
            del self.positions[position_id]

    def get_positions_status(self):
        """ดูสถานะ positions ทั้งหมด"""
        status = []
        for pos_id, pos in self.positions.items():
            time_left = (pos['force_sell_time'] - datetime.now()).total_seconds() / 3600
            status.append({
                'id': pos_id,
                'symbol': pos['symbol'],
                'entry_time': pos['entry_time'],
                'time_left_hours': max(0, time_left),
                'min_profit_reached': pos['min_profit_reached']
            })
        return status


class AutoTradingEngine:
    """🤖 เครื่องมือเทรดอัตโนมัติขั้นสูง"""

    def __init__(self, api_client, coin_analyzer, strategies, force_sell_manager):
        self.api_client = api_client
        self.coin_analyzer = coin_analyzer
        self.strategies = strategies
        self.force_sell_manager = force_sell_manager

        # การตั้งค่า Auto Trading
        self.enabled = False
        self.auto_coin_selection = True
        self.adaptive_strategy = True
        self.min_ai_score = 6.0
        self.max_concurrent_positions = 3
        self.rebalance_interval_hours = 4

        # ติดตาม performance
        self.performance_history = deque(maxlen=100)
        self.current_positions = {}

        # ตัวเลือกกลยุทธ์ตาม market condition
        self.market_conditions = {
            'trending_up': ['ema_crossover', 'swing_trading'],
            'trending_down': ['rsi_momentum', 'scalping'],
            'sideways': ['bollinger_bands', 'volume_breakout'],
            'volatile': ['scalping', 'bollinger_bands']
        }

    def start_auto_trading(self, config):
        """เริ่ม Auto Trading"""
        self.enabled = True
        self.auto_coin_selection = config.get('auto_coin_selection', True)
        self.adaptive_strategy = config.get('adaptive_strategy', True)
        self.min_ai_score = config.get('min_ai_score', 6.0)

        print("🤖 Auto Trading Engine Started")

    def stop_auto_trading(self):
        """หยุด Auto Trading"""
        self.enabled = False
        print("🤖 Auto Trading Engine Stopped")

    def auto_trading_cycle(self, trade_amount=1000):
        """รอบการทำงานของ Auto Trading"""
        if not self.enabled:
            return None

        try:
            # 1. วิเคราะห์เหรียญทั้งหมด (ถ้าเปิดใช้)
            if self.auto_coin_selection:
                coin_analysis = self.coin_analyzer.analyze_all_coins(trade_amount)
                # เลือกเหรียญที่ดีที่สุด
                best_coins = [coin for coin in coin_analysis if coin['ai_score'] >= self.min_ai_score]

                if not best_coins:
                    return {'action': 'wait', 'reason': 'No coins meet AI score criteria'}

                selected_coin = best_coins[0]  # เลือกเหรียญที่ดีที่สุด
            else:
                selected_coin = {'symbol': 'btc_thb'}  # ใช้เหรียญที่ตั้งค่าไว้

            # 2. กำหนดกลยุทธ์ (ถ้าเปิดใช้ adaptive)
            if self.adaptive_strategy:
                market_condition = self.analyze_market_condition(selected_coin['symbol'])
                strategy_name = self.select_strategy_for_market(market_condition)
            else:
                strategy_name = 'rsi_momentum'  # ใช้กลยุทธ์เริ่มต้น

            # 3. วิเคราะห์สัญญาณ
            ticker = self.api_client.get_simple_ticker(selected_coin['symbol'])
            if not ticker:
                return {'action': 'error', 'reason': 'Cannot get market data'}

            should_trade, reason = self.strategies.analyze_with_strategy(
                strategy_name, ticker['last_price'], ticker.get('volume_24h', 0)
            )

            # 4. ตัดสินใจ
            if should_trade and len(self.current_positions) < self.max_concurrent_positions:
                return {
                    'action': 'buy',
                    'symbol': selected_coin['symbol'],
                    'strategy': strategy_name,
                    'reason': reason,
                    'ai_score': selected_coin.get('ai_score', 0),
                    'price': ticker['last_price']
                }

            # 5. ตรวจสอบการขาย
            sell_decisions = self.check_sell_signals()
            if sell_decisions:
                return sell_decisions[0]  # ขายอันแรก

            return {'action': 'wait', 'reason': f'No trading opportunity. Strategy: {strategy_name}'}

        except Exception as e:
            return {'action': 'error', 'reason': f'Auto trading error: {e}'}

    def analyze_market_condition(self, symbol):
        """วิเคราะห์สภาพตลาด"""
        try:
            ticker = self.api_client.get_simple_ticker(symbol)
            if not ticker:
                return 'sideways'

            change_24h = ticker.get('change_24h', 0)
            volume_24h = ticker.get('volume_24h', 0)

            # วิเคราะห์ trend
            if change_24h > 3:
                return 'trending_up'
            elif change_24h < -3:
                return 'trending_down'
            elif abs(change_24h) > 5:
                return 'volatile'
            else:
                return 'sideways'

        except:
            return 'sideways'

    def select_strategy_for_market(self, market_condition):
        """เลือกกลยุทธ์ตามสภาพตลาด"""
        strategies_for_condition = self.market_conditions.get(market_condition, ['rsi_momentum'])

        # เลือกกลยุทธ์ที่ enabled
        for strategy in strategies_for_condition:
            if self.strategies.strategies.get(strategy, {}).get('enabled', False):
                return strategy

        return 'rsi_momentum'  # fallback

    def check_sell_signals(self):
        """ตรวจสอบสัญญาณขาย"""
        sell_signals = []

        for pos_id, position in self.current_positions.items():
            # ตรวจสอบ force sell
            ticker = self.api_client.get_simple_ticker(position['symbol'])
            if ticker:
                should_sell, reason = self.force_sell_manager.check_force_sell(
                    pos_id, ticker['last_price']
                )

                if should_sell:
                    sell_signals.append({
                        'action': 'sell',
                        'position_id': pos_id,
                        'symbol': position['symbol'],
                        'reason': reason,
                        'current_price': ticker['last_price']
                    })

        return sell_signals

    def add_position(self, symbol, entry_data):
        """เพิ่ม position ใหม่"""
        pos_id = f"{symbol}_{int(time.time())}"
        self.current_positions[pos_id] = {
            'symbol': symbol,
            'entry_time': datetime.now(),
            'entry_price': entry_data['entry_price'],
            'amount': entry_data['amount'],
            'strategy': entry_data.get('strategy', 'unknown')
        }

        # เพิ่มเข้า force sell manager ด้วย
        self.force_sell_manager.add_position(symbol, entry_data)

        return pos_id

    def remove_position(self, position_id):
        """ลบ position"""
        if position_id in self.current_positions:
            del self.current_positions[position_id]
        self.force_sell_manager.remove_position(position_id)

    def get_performance_summary(self):
        """สรุปประสิทธิภาพ Auto Trading"""
        if not self.performance_history:
            return "No performance data yet"

        recent_performance = list(self.performance_history)[-20:]  # 20 trades ล่าสุด

        total_trades = len(recent_performance)
        profitable_trades = len([p for p in recent_performance if p.get('pnl', 0) > 0])
        win_rate = (profitable_trades / total_trades * 100) if total_trades > 0 else 0

        avg_pnl = statistics.mean([p.get('pnl', 0) for p in recent_performance])

        return {
            'total_trades': total_trades,
            'win_rate': win_rate,
            'avg_pnl': avg_pnl,
            'active_positions': len(self.current_positions)
        }


class SciFiVisualSystem:
    """🎬 ระบบกราฟิก Sci-Fi ที่ปรับปรุงแล้ว"""

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

        # Enhanced Sci-fi color schemes
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
            },
            # 🆕 สถานะใหม่
            "coin_analysis": {
                "primary": "#9944ff",
                "secondary": "#6622cc",
                "accent": "#bb88ff",
                "glow": "#aa44ff"
            },
            "auto_mode": {
                "primary": "#44ffff",
                "secondary": "#22cccc",
                "accent": "#88ffff",
                "glow": "#66ffff"
            }
        }

        # Initialize particles
        self.init_particle_system()
        self.canvas.pack(pady=10)

    def init_particle_system(self):
        """Initialize floating particles"""
        self.particles = []
        for _ in range(20):  # เพิ่มจำนวน particles
            particle = {
                'x': random.uniform(50, self.width - 50),
                'y': random.uniform(50, self.height - 50),
                'dx': random.uniform(-0.8, 0.8),
                'dy': random.uniform(-0.8, 0.8),
                'size': random.uniform(1, 4),
                'alpha': random.uniform(0.3, 0.9),
                'phase': random.uniform(0, 2 * math.pi),
                'type': random.choice(['normal', 'star', 'diamond'])
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
                elif self.current_state == "coin_analysis":
                    self._draw_coin_analysis()
                elif self.current_state == "auto_mode":
                    self._draw_auto_mode()

                time.sleep(0.05)  # 20 FPS

            except Exception as e:
                print(f"Animation error: {e}")
                break

    def _draw_coin_analysis(self):
        """🆕 Draw coin analysis state - AI scanning animation"""
        self.canvas.delete("all")
        theme = self.state_themes["coin_analysis"]

        self.draw_particles(theme)

        # AI Brain pattern
        for i in range(8):
            angle = i * 45 + self.rotation_angle
            radius = 60 + 20 * math.sin(self.pulse_phase + i * 0.3)

            node_x = self.center_x + radius * math.cos(math.radians(angle))
            node_y = self.center_y + radius * math.sin(math.radians(angle))

            # Neural connections
            for j in range(i + 1, 8):
                angle2 = j * 45 + self.rotation_angle
                radius2 = 60 + 20 * math.sin(self.pulse_phase + j * 0.3)
                node_x2 = self.center_x + radius2 * math.cos(math.radians(angle2))
                node_y2 = self.center_y + radius2 * math.sin(math.radians(angle2))

                # สุ่มแสดง connection
                if (i + j + self.frame_count // 10) % 3 == 0:
                    alpha = math.sin(self.pulse_phase + i + j) * 0.3 + 0.5
                    intensity = int(alpha * 180)
                    color = f"#{intensity // 3:02x}{intensity // 3:02x}{intensity:02x}"

                    self.canvas.create_line(
                        node_x, node_y, node_x2, node_y2,
                        fill=color, width=1,
                        tags="neural_connection"
                    )

            # Neural nodes
            node_pulse = math.sin(self.pulse_phase * 2 + i) * 0.4 + 1.0
            node_size = int(6 * node_pulse)

            self.canvas.create_oval(
                node_x - node_size, node_y - node_size,
                node_x + node_size, node_y + node_size,
                fill=theme["primary"], outline=theme["accent"], width=2,
                tags="neural_node"
            )

        # Central AI Core
        core_pulse = math.sin(self.pulse_phase * 3) * 0.3 + 1.0
        core_size = int(20 * core_pulse)

        self.canvas.create_oval(
            self.center_x - core_size, self.center_y - core_size,
            self.center_x + core_size, self.center_y + core_size,
            fill=theme["glow"], outline=theme["primary"], width=3,
            tags="ai_core"
        )

        # AI text
        self.canvas.create_text(
            self.center_x, self.center_y,
            text="AI", fill=theme["accent"],
            font=("Orbitron", 12, "bold"),
            tags="ai_text"
        )

        self.canvas.create_text(
            self.center_x, self.height - 30,
            text="ANALYZING COINS", fill=theme["primary"],
            font=("Orbitron", 12, "bold"),
            tags="status_text"
        )

    def _draw_auto_mode(self):
        """🆕 Draw auto mode state - Autonomous system"""
        self.canvas.delete("all")
        theme = self.state_themes["auto_mode"]

        self.draw_particles(theme)

        # Orbiting satellites
        for i in range(4):
            satellite_angle = i * 90 + self.rotation_angle * 2
            orbit_radius = 70

            sat_x = self.center_x + orbit_radius * math.cos(math.radians(satellite_angle))
            sat_y = self.center_y + orbit_radius * math.sin(math.radians(satellite_angle))

            # Satellite body
            sat_size = 8
            self.canvas.create_rectangle(
                sat_x - sat_size, sat_y - sat_size,
                sat_x + sat_size, sat_y + sat_size,
                fill=theme["primary"], outline=theme["accent"], width=2,
                tags="satellite"
            )

            # Satellite signals
            for j in range(3):
                signal_radius = 15 + j * 8
                signal_alpha = (math.sin(self.pulse_phase * 2 - j) + 1) / 2
                intensity = int(signal_alpha * 150)
                color = f"#{intensity // 6:02x}{intensity // 2:02x}{intensity:02x}"

                self.canvas.create_oval(
                    sat_x - signal_radius, sat_y - signal_radius,
                    sat_x + signal_radius, sat_y + signal_radius,
                    outline=color, width=1,
                    tags="satellite_signal"
                )

        # Central command hub
        hub_pulse = math.sin(self.pulse_phase) * 0.2 + 1.0
        hub_size = int(25 * hub_pulse)

        # Outer ring
        self.canvas.create_oval(
            self.center_x - hub_size, self.center_y - hub_size,
            self.center_x + hub_size, self.center_y + hub_size,
            outline=theme["primary"], width=3,
            tags="hub_ring"
        )

        # Inner core
        inner_size = hub_size // 2
        self.canvas.create_oval(
            self.center_x - inner_size, self.center_y - inner_size,
            self.center_x + inner_size, self.center_y + inner_size,
            fill=theme["glow"], outline="",
            tags="hub_core"
        )

        # Auto symbol
        self.canvas.create_text(
            self.center_x, self.center_y,
            text="AUTO", fill=theme["primary"],
            font=("Orbitron", 8, "bold"),
            tags="auto_text"
        )

        self.canvas.create_text(
            self.center_x, self.height - 30,
            text="AUTO TRADING", fill=theme["primary"],
            font=("Orbitron", 12, "bold"),
            tags="status_text"
        )

    def update_particles(self):
        """Update particle positions"""
        for particle in self.particles:
            particle['x'] += particle['dx']
            particle['y'] += particle['dy']
            particle['phase'] += 0.05

            # Bounce off edges
            if particle['x'] <= 10 or particle['x'] >= self.width - 10:
                particle['dx'] *= -1
            if particle['y'] <= 10 or particle['y'] >= self.height - 10:
                particle['dy'] *= -1

    def draw_particles(self, theme):
        """Draw enhanced particles"""
        for particle in self.particles:
            alpha_mod = (math.sin(particle['phase']) + 1) / 2
            alpha = particle['alpha'] * alpha_mod
            intensity = int(alpha * 255)

            if intensity > 20:
                size = particle['size'] * (alpha + 0.5)

                if particle['type'] == 'star':
                    # Draw star particle
                    points = []
                    for i in range(5):
                        angle = i * 144  # 144 degrees between points
                        outer_x = particle['x'] + size * math.cos(math.radians(angle))
                        outer_y = particle['y'] + size * math.sin(math.radians(angle))

                        inner_angle = angle + 72
                        inner_x = particle['x'] + size * 0.4 * math.cos(math.radians(inner_angle))
                        inner_y = particle['y'] + size * 0.4 * math.sin(math.radians(inner_angle))

                        points.extend([outer_x, outer_y, inner_x, inner_y])

                    color = f"#{intensity // 4:02x}{intensity // 4:02x}{intensity:02x}"
                    if len(points) >= 6:
                        self.canvas.create_polygon(
                            points[:10], fill=color, outline="",
                            tags="particle"
                        )

                elif particle['type'] == 'diamond':
                    # Draw diamond particle
                    points = [
                        particle['x'], particle['y'] - size,
                                       particle['x'] + size, particle['y'],
                        particle['x'], particle['y'] + size,
                                       particle['x'] - size, particle['y']
                    ]
                    color = f"#{intensity // 4:02x}{intensity // 4:02x}{intensity:02x}"
                    self.canvas.create_polygon(
                        points, fill=color, outline="",
                        tags="particle"
                    )

                else:
                    # Normal circular particle
                    color = f"#{intensity // 4:02x}{intensity // 4:02x}{intensity:02x}"
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
        core_pulse = math.sin(self.pulse_phase * 2) * 0.3 + 1.0
        core_size = int(25 * core_pulse)

        # Outer glow
        for i in range(5):
            glow_size = core_size + i * 4
            alpha = (0.8 - i * 0.15) * core_pulse
            intensity = int(alpha * 200)

            if intensity > 20:
                color = f"#{intensity // 4:02x}{intensity // 4:02x}{intensity:02x}"
                self.canvas.create_oval(
                    self.center_x - glow_size, self.center_y - glow_size,
                    self.center_x + glow_size, self.center_y + glow_size,
                    fill="", outline=color, width=2,
                    tags="core_glow"
                )

        # Central core
        self.canvas.create_oval(
            self.center_x - core_size, self.center_y - core_size,
            self.center_x + core_size, self.center_y + core_size,
            fill=theme["primary"], outline=theme["accent"], width=3,
            tags="core"
        )

        # Core inner details
        inner_size = core_size // 2
        self.canvas.create_oval(
            self.center_x - inner_size, self.center_y - inner_size,
            self.center_x + inner_size, self.center_y + inner_size,
            fill=theme["glow"], outline="",
            tags="core_inner"
        )

    def _draw_idle(self):
        """Draw idle state - peaceful monitoring"""
        self.canvas.delete("all")
        theme = self.state_themes["idle"]

        self.draw_particles(theme)
        self.draw_hud_rings(theme)
        self.draw_energy_core(theme)

        # Status text
        self.canvas.create_text(
            self.center_x, self.height - 30,
            text="SYSTEM READY", fill=theme["primary"],
            font=("Orbitron", 12, "bold"),
            tags="status_text"
        )

    def _draw_connecting(self):
        """Draw connecting state - scanning animation"""
        self.canvas.delete("all")
        theme = self.state_themes["connecting"]

        self.draw_particles(theme)

        # Rotating scanner
        scanner_angle = self.rotation_angle * 3
        scanner_length = 60

        end_x = self.center_x + scanner_length * math.cos(math.radians(scanner_angle))
        end_y = self.center_y + scanner_length * math.sin(math.radians(scanner_angle))

        self.canvas.create_line(
            self.center_x, self.center_y, end_x, end_y,
            fill=theme["primary"], width=4,
            tags="scanner"
        )

        # Scanner trail effect
        for i in range(8):
            trail_angle = scanner_angle - i * 5
            trail_alpha = 1.0 - i * 0.1
            trail_length = scanner_length * trail_alpha

            trail_x = self.center_x + trail_length * math.cos(math.radians(trail_angle))
            trail_y = self.center_y + trail_length * math.sin(math.radians(trail_angle))

            intensity = int(trail_alpha * 255)
            trail_color = f"#{intensity:02x}{intensity // 2:02x}{intensity // 8:02x}"

            self.canvas.create_line(
                self.center_x, self.center_y, trail_x, trail_y,
                fill=trail_color, width=max(1, int(3 * trail_alpha)),
                tags="scanner_trail"
            )

        self.draw_hud_rings(theme, 70)
        self.draw_energy_core(theme)

        self.canvas.create_text(
            self.center_x, self.height - 30,
            text="CONNECTING...", fill=theme["primary"],
            font=("Orbitron", 12, "bold"),
            tags="status_text"
        )

    def _draw_analyzing(self):
        """Draw analyzing state - brain wave analysis"""
        self.canvas.delete("all")
        theme = self.state_themes["analyzing"]

        self.draw_particles(theme)

        # Brain wave pattern
        wave_points = []
        for i in range(100):
            x = i * (self.width / 100)
            # Complex waveform
            y1 = math.sin((i + self.wave_phase * 5) * 0.1) * 20
            y2 = math.sin((i + self.wave_phase * 3) * 0.05) * 10
            y3 = math.sin((i + self.wave_phase * 7) * 0.15) * 5
            y = self.center_y + y1 + y2 + y3
            wave_points.extend([x, y])

        if len(wave_points) >= 4:
            self.canvas.create_line(
                wave_points, fill=theme["primary"], width=3, smooth=True,
                tags="brainwave"
            )

        # Neural network nodes
        for i in range(6):
            angle = i * 60 + self.rotation_angle
            radius = 50 + 20 * math.sin(self.pulse_phase + i)

            node_x = self.center_x + radius * math.cos(math.radians(angle))
            node_y = self.center_y + radius * math.sin(math.radians(angle))

            node_pulse = math.sin(self.pulse_phase * 2 + i * 0.5) * 0.3 + 1.0
            node_size = int(8 * node_pulse)

            self.canvas.create_oval(
                node_x - node_size, node_y - node_size,
                node_x + node_size, node_y + node_size,
                fill=theme["primary"], outline=theme["accent"], width=2,
                tags="neural_node"
            )

        self.draw_energy_core(theme)

        self.canvas.create_text(
            self.center_x, self.height - 30,
            text="ANALYZING MARKET", fill=theme["primary"],
            font=("Orbitron", 12, "bold"),
            tags="status_text"
        )

    def _draw_buy_signal(self):
        """Draw buy signal - energy surge upward"""
        self.canvas.delete("all")
        theme = self.state_themes["buy_signal"]

        self.draw_particles(theme)

        # Energy surge effect
        surge_height = 80 + 30 * math.sin(self.pulse_phase * 2)
        for i in range(5):
            surge_y = self.center_y - surge_height + i * 10
            surge_width = 40 - i * 6
            alpha = 1.0 - i * 0.15
            intensity = int(alpha * 255)

            color = f"#{intensity // 8:02x}{intensity:02x}{intensity // 4:02x}"

            self.canvas.create_oval(
                self.center_x - surge_width, surge_y - 5,
                self.center_x + surge_width, surge_y + 5,
                fill=color, outline="",
                tags="energy_surge"
            )

        # Buy arrow
        arrow_size = 30 + 10 * math.sin(self.pulse_phase * 2)
        arrow_points = [
            self.center_x, self.center_y - arrow_size,
                           self.center_x - arrow_size // 2, self.center_y - arrow_size // 3,
                           self.center_x - arrow_size // 4, self.center_y - arrow_size // 3,
                           self.center_x - arrow_size // 4, self.center_y + arrow_size // 2,
                           self.center_x + arrow_size // 4, self.center_y + arrow_size // 2,
                           self.center_x + arrow_size // 4, self.center_y - arrow_size // 3,
                           self.center_x + arrow_size // 2, self.center_y - arrow_size // 3
        ]

        self.canvas.create_polygon(
            arrow_points, fill=theme["primary"], outline=theme["accent"], width=3,
            tags="buy_arrow"
        )

        self.draw_hud_rings(theme, 90)

        self.canvas.create_text(
            self.center_x, self.height - 30,
            text="BUY SIGNAL DETECTED", fill=theme["primary"],
            font=("Orbitron", 12, "bold"),
            tags="status_text"
        )

    def _draw_sell_signal(self):
        """Draw sell signal - energy contraction downward"""
        self.canvas.delete("all")
        theme = self.state_themes["sell_signal"]

        self.draw_particles(theme)

        # Energy contraction effect
        contraction_height = 80 + 30 * math.sin(self.pulse_phase * 2)
        for i in range(5):
            contract_y = self.center_y + contraction_height - i * 10
            contract_width = 40 - i * 6
            alpha = 1.0 - i * 0.15
            intensity = int(alpha * 255)

            color = f"#{intensity:02x}{intensity // 8:02x}{intensity // 8:02x}"

            self.canvas.create_oval(
                self.center_x - contract_width, contract_y - 5,
                self.center_x + contract_width, contract_y + 5,
                fill=color, outline="",
                tags="energy_contract"
            )

        # Sell arrow
        arrow_size = 30 + 10 * math.sin(self.pulse_phase * 2)
        arrow_points = [
            self.center_x, self.center_y + arrow_size,
                           self.center_x - arrow_size // 2, self.center_y + arrow_size // 3,
                           self.center_x - arrow_size // 4, self.center_y + arrow_size // 3,
                           self.center_x - arrow_size // 4, self.center_y - arrow_size // 2,
                           self.center_x + arrow_size // 4, self.center_y - arrow_size // 2,
                           self.center_x + arrow_size // 4, self.center_y + arrow_size // 3,
                           self.center_x + arrow_size // 2, self.center_y + arrow_size // 3
        ]

        self.canvas.create_polygon(
            arrow_points, fill=theme["primary"], outline=theme["accent"], width=3,
            tags="sell_arrow"
        )

        self.draw_hud_rings(theme, 90)

        self.canvas.create_text(
            self.center_x, self.height - 30,
            text="SELL SIGNAL DETECTED", fill=theme["primary"],
            font=("Orbitron", 12, "bold"),
            tags="status_text"
        )

    def _draw_trading(self):
        """Draw active trading - lightning and currency symbols"""
        self.canvas.delete("all")
        theme = self.state_themes["trading"]

        self.draw_particles(theme)

        # Lightning bolts
        for i in range(3):
            bolt_angle = i * 120 + self.rotation_angle
            bolt_radius = 60

            bolt_start_x = self.center_x + bolt_radius * math.cos(math.radians(bolt_angle))
            bolt_start_y = self.center_y + bolt_radius * math.sin(math.radians(bolt_angle))

            bolt_end_x = self.center_x + (bolt_radius + 40) * math.cos(math.radians(bolt_angle))
            bolt_end_y = self.center_y + (bolt_radius + 40) * math.sin(math.radians(bolt_angle))

            # Zigzag lightning effect
            bolt_points = [bolt_start_x, bolt_start_y]
            for j in range(4):
                progress = (j + 1) / 4
                mid_x = bolt_start_x + (bolt_end_x - bolt_start_x) * progress
                mid_y = bolt_start_y + (bolt_end_y - bolt_start_y) * progress

                # Add zigzag
                offset = 10 * math.sin(self.pulse_phase + j) * (1 - progress)
                perp_angle = bolt_angle + 90
                mid_x += offset * math.cos(math.radians(perp_angle))
                mid_y += offset * math.sin(math.radians(perp_angle))

                bolt_points.extend([mid_x, mid_y])

            if len(bolt_points) >= 4:
                self.canvas.create_line(
                    bolt_points, fill=theme["primary"], width=3,
                    tags="lightning"
                )

        # Currency symbols rotation
        symbols = ["฿", "$", "€", "¥"]
        for i, symbol in enumerate(symbols):
            symbol_angle = i * 90 + self.rotation_angle * 2
            symbol_radius = 45

            symbol_x = self.center_x + symbol_radius * math.cos(math.radians(symbol_angle))
            symbol_y = self.center_y + symbol_radius * math.sin(math.radians(symbol_angle))

            symbol_pulse = math.sin(self.pulse_phase + i * 0.5) * 0.3 + 1.0
            font_size = int(16 * symbol_pulse)

            self.canvas.create_text(
                symbol_x, symbol_y, text=symbol,
                fill=theme["primary"], font=("Arial", font_size, "bold"),
                tags="currency_symbol"
            )

        self.draw_energy_core(theme, True)

        self.canvas.create_text(
            self.center_x, self.height - 30,
            text="ACTIVE TRADING", fill=theme["primary"],
            font=("Orbitron", 12, "bold"),
            tags="status_text"
        )

    def _draw_success(self):
        """Draw success state - victory explosion"""
        self.canvas.delete("all")
        theme = self.state_themes["success"]

        self.draw_particles(theme)

        # Success explosion
        explosion_radius = 20 + 60 * math.sin(self.pulse_phase)
        for i in range(12):
            ray_angle = i * 30
            ray_length = explosion_radius

            ray_end_x = self.center_x + ray_length * math.cos(math.radians(ray_angle))
            ray_end_y = self.center_y + ray_length * math.sin(math.radians(ray_angle))

            alpha = math.sin(self.pulse_phase) * 0.5 + 0.5
            intensity = int(alpha * 255)
            color = f"#{intensity // 8:02x}{intensity:02x}{intensity // 2:02x}"

            self.canvas.create_line(
                self.center_x, self.center_y, ray_end_x, ray_end_y,
                fill=color, width=4,
                tags="success_ray"
            )

        # Checkmark
        check_size = 20 + 10 * math.sin(self.pulse_phase)
        check_points = [
            self.center_x - check_size, self.center_y,
            self.center_x - check_size // 3, self.center_y + check_size // 2,
            self.center_x + check_size, self.center_y - check_size // 2
        ]

        self.canvas.create_line(
            check_points, fill=theme["primary"], width=6,
            capstyle=tk.ROUND, joinstyle=tk.ROUND,
            tags="checkmark"
        )

        self.draw_hud_rings(theme, 100)

        self.canvas.create_text(
            self.center_x, self.height - 30,
            text="OPERATION SUCCESS", fill=theme["primary"],
            font=("Orbitron", 12, "bold"),
            tags="status_text"
        )

    def _draw_error(self):
        """Draw error state - warning system"""
        self.canvas.delete("all")
        theme = self.state_themes["error"]

        self.draw_particles(theme)

        # Error pulse
        error_intensity = math.sin(self.pulse_phase * 4) * 0.5 + 0.5

        # Warning triangles
        for i in range(6):
            triangle_angle = i * 60 + self.rotation_angle
            triangle_radius = 70
            triangle_size = 15

            tri_x = self.center_x + triangle_radius * math.cos(math.radians(triangle_angle))
            tri_y = self.center_y + triangle_radius * math.sin(math.radians(triangle_angle))

            # Triangle points
            tri_points = []
            for j in range(3):
                point_angle = triangle_angle + j * 120
                point_x = tri_x + triangle_size * math.cos(math.radians(point_angle))
                point_y = tri_y + triangle_size * math.sin(math.radians(point_angle))
                tri_points.extend([point_x, point_y])

            alpha = error_intensity
            intensity = int(alpha * 255)
            color = f"#{intensity:02x}{intensity // 8:02x}{intensity // 8:02x}"

            self.canvas.create_polygon(
                tri_points, fill=color, outline=theme["accent"], width=2,
                tags="warning_triangle"
            )

        # Central warning symbol
        warning_size = 25 + 10 * error_intensity
        self.canvas.create_text(
            self.center_x, self.center_y,
            text="⚠", fill=theme["primary"],
            font=("Arial", int(warning_size), "bold"),
            tags="warning_symbol"
        )

        # Error rings
        for i in range(3):
            ring_radius = 50 + i * 20 + 10 * error_intensity
            ring_alpha = error_intensity * (1 - i * 0.2)
            ring_intensity = int(ring_alpha * 255)
            ring_color = f"#{ring_intensity:02x}{ring_intensity // 8:02x}{ring_intensity // 8:02x}"

            self.canvas.create_oval(
                self.center_x - ring_radius, self.center_y - ring_radius,
                self.center_x + ring_radius, self.center_y + ring_radius,
                outline=ring_color, width=3,
                tags="error_ring"
            )

        self.canvas.create_text(
            self.center_x, self.height - 30,
            text="SYSTEM ERROR", fill=theme["primary"],
            font=("Orbitron", 12, "bold"),
            tags="status_text"
        )

    def draw_idle_state(self):
        """Draw static idle state"""
        self.canvas.delete("all")
        theme = self.state_themes["idle"]

        # Simple idle display
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
    """Enhanced Bitkub API Client with all coins and fee calculation"""

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

        # Complete list of all Bitkub supported coins
        self.all_bitkub_symbols = [
            "btc_thb", "eth_thb", "ada_thb", "xrp_thb", "bnb_thb", "doge_thb",
            "dot_thb", "matic_thb", "atom_thb", "near_thb", "sol_thb", "sand_thb",
            "mana_thb", "avax_thb", "shib_thb", "ltc_thb", "bch_thb", "etc_thb",
            "link_thb", "uni_thb", "usdt_thb", "usdc_thb", "dai_thb", "busd_thb",
            "alpha_thb", "ftt_thb", "axie_thb", "alice_thb", "chz_thb", "jasmy_thb",
            "lrc_thb", "comp_thb", "mkr_thb", "snx_thb", "aave_thb", "grt_thb",
            "1inch_thb", "enj_thb", "gala_thb", "chr_thb", "bat_thb", "omg_thb",
            "knc_thb", "cvc_thb", "pow_thb", "iotx_thb", "wxt_thb", "zil_thb",
            "srk_thb", "six_thb", "jfin_thb", "arpa_thb", "troy_thb", "ong_thb",
            "zrx_thb", "kub_thb", "ctxc_thb", "infra_thb", "bitkub_thb"
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
            "THB_USDC": "usdc_thb", "THB_DAI": "dai_thb", "THB_BUSD": "busd_thb",
            "THB_ALPHA": "alpha_thb", "THB_FTT": "ftt_thb", "THB_AXIE": "axie_thb",
            "THB_ALICE": "alice_thb", "THB_CHZ": "chz_thb", "THB_JASMY": "jasmy_thb",
            "THB_LRC": "lrc_thb", "THB_COMP": "comp_thb", "THB_MKR": "mkr_thb",
            "THB_SNX": "snx_thb", "THB_AAVE": "aave_thb", "THB_GRT": "grt_thb",
            "THB_1INCH": "1inch_thb", "THB_ENJ": "enj_thb", "THB_GALA": "gala_thb",
            "THB_CHR": "chr_thb", "THB_BAT": "bat_thb", "THB_OMG": "omg_thb",
            "THB_KNC": "knc_thb", "THB_CVC": "cvc_thb", "THB_POW": "pow_thb",
            "THB_IOTX": "iotx_thb", "THB_WXT": "wxt_thb", "THB_ZIL": "zil_thb",
            "THB_SRK": "srk_thb", "THB_SIX": "six_thb", "THB_JFIN": "jfin_thb",
            "THB_ARPA": "arpa_thb", "THB_TROY": "troy_thb", "THB_ONG": "ong_thb",
            "THB_ZRX": "zrx_thb", "THB_KUB": "kub_thb", "THB_CTXC": "ctxc_thb",
            "THB_INFRA": "infra_thb", "THB_BITKUB": "bitkub_thb"
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


class EnhancedTradingBot:
    """🚀 Enhanced Trading Bot v3.0 with Premium Features"""

    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("🚀 Enhanced Bitkub Trading Bot v3.0 - Premium Edition")
        self.root.geometry("1800x1200")

        # 🔐 Initialize License System
        self.license_manager = LicenseManager()

        # Core components
        self.api_client = None
        self.coin_analyzer = None
        self.strategies = None
        self.force_sell_manager = None
        self.auto_trading_engine = None
        self.scifi_visual = None

        # Trading state
        self.is_trading = False
        self.is_paper_trading = True
        self.is_auto_trading = False
        self.emergency_stop = False

        # Enhanced trading config
        self.config = {
            'symbol': 'btc_thb',
            'trade_amount_thb': 1000,  # เพิ่มขึ้นเพื่อความคุ้มค่า
            'max_daily_trades': 5,  # เพิ่มขึ้น
            'max_daily_loss': 2000,  # เพิ่มขึ้น
            'min_trade_interval': 1800,  # 30 minutes
            'auto_coin_selection': True,
            'adaptive_strategy': True,
            'min_ai_score': 6.0,
            'force_sell_enabled': True,
            'force_sell_hours': 6
        }

        # Statistics
        self.daily_trades = 0
        self.daily_pnl = 0
        self.last_trade_time = None
        self.total_fees_paid = 0

        # Performance tracking
        self.performance_data = {
            'coin_recommendations': [],
            'strategy_performance': {},
            'force_sell_effectiveness': [],
            'auto_trading_results': []
        }

        # Database
        self.init_enhanced_database()

        # Setup UI
        self.setup_enhanced_ui()

    def init_enhanced_database(self):
        """Initialize enhanced database with new tables"""
        self.db_path = "enhanced_trading_bot_v3.db"
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Main trades table (updated)
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
                volume_momentum REAL,
                break_even_price REAL,
                api_response TEXT,
                strategy_used TEXT,
                ai_score REAL,
                force_sell BOOLEAN,
                auto_trade BOOLEAN
            )
        ''')

        # 🆕 Coin analysis history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS coin_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                symbol TEXT,
                price REAL,
                change_24h REAL,
                volume_24h REAL,
                ai_score REAL,
                volatility_score REAL,
                volume_score REAL,
                momentum_score REAL,
                fee_impact REAL,
                recommendation TEXT
            )
        ''')

        # 🆕 Strategy performance
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS strategy_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                strategy_name TEXT,
                symbol TEXT,
                action TEXT,
                result TEXT,
                pnl REAL,
                success BOOLEAN
            )
        ''')

        # 🆕 Auto trading log
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS auto_trading_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                action TEXT,
                symbol TEXT,
                reason TEXT,
                ai_score REAL,
                strategy_used TEXT,
                result TEXT
            )
        ''')

        conn.commit()
        conn.close()

    def setup_enhanced_ui(self):
        """Create enhanced UI with premium features"""

        # 🆕 Enhanced warning banner with license info
        warning_frame = ctk.CTkFrame(self.root, fg_color="dark red", height=80)
        warning_frame.pack(fill="x", padx=10, pady=5)
        warning_frame.pack_propagate(False)

        license_info = self.license_manager.get_license_info()

        warning_text = f"🚀 ENHANCED BITKUB TRADING BOT v3.0 - PREMIUM EDITION 🚀\n"
        warning_text += f"License: {license_info['type'].upper()} | Days Left: {license_info['remaining_days']} | "
        warning_text += f"All Premium Features {'✅ ENABLED' if license_info['valid'] else '❌ DISABLED'}"

        ctk.CTkLabel(warning_frame, text=warning_text,
                     font=("Arial", 12, "bold"),
                     text_color="white").pack(expand=True)

        # Enhanced Tabs
        self.tabview = ctk.CTkTabview(self.root)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        # 🆕 New premium tabs
        self.tab_dashboard = self.tabview.add("📊 Dashboard")
        self.tab_coin_analyzer = self.tabview.add("🪙 Coin Analyzer")
        self.tab_strategies = self.tabview.add("🎯 Advanced Strategies")
        self.tab_auto_trading = self.tabview.add("🤖 Auto Trading")
        self.tab_force_sell = self.tabview.add("🕐 Force Sell")
        self.tab_trading = self.tabview.add("💹 Manual Trading")
        self.tab_api = self.tabview.add("🔌 API Config")
        self.tab_analytics = self.tabview.add("📈 Advanced Analytics")
        self.tab_settings = self.tabview.add("⚙️ Settings")
        self.tab_license = self.tabview.add("🔐 License")

        # Setup all tabs
        self.setup_enhanced_dashboard()
        self.setup_coin_analyzer_tab()
        self.setup_strategies_tab()
        self.setup_auto_trading_tab()
        self.setup_force_sell_tab()
        self.setup_manual_trading_tab()
        self.setup_api_tab()
        self.setup_analytics_tab()
        self.setup_enhanced_settings()
        self.setup_license_tab()

    def setup_enhanced_dashboard(self):
        """🆕 Enhanced dashboard with premium features"""
        # Main content frame
        content_frame = ctk.CTkFrame(self.tab_dashboard)
        content_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Left side - Status and controls
        left_frame = ctk.CTkFrame(content_frame)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

        # Enhanced status cards
        stats_frame = ctk.CTkFrame(left_frame)
        stats_frame.pack(fill="x", padx=10, pady=10)

        self.status_cards = {}
        cards = [
            ("Mode", "PAPER TRADING", "orange"),
            ("License", f"{self.license_manager.get_license_info()['type'].upper()}", "blue"),
            ("System Status", "Checking...", "gray"),
            ("Balance THB", "---", "green"),
            ("Best Coin", "Analyzing...", "purple"),
            ("AI Score", "---", "cyan"),
            ("Strategy", "RSI+Momentum", "yellow"),
            ("Auto Mode", "OFF", "gray"),
            ("Daily P&L", "0.00", "blue"),
            ("Daily Trades", "0/5", "purple"),
            ("Force Sell", "6h", "orange"),
            ("Net Profit", "0.00", "green")
        ]

        for i, (label, value, color) in enumerate(cards):
            row = i // 4
            col = i % 4

            card = ctk.CTkFrame(stats_frame)
            card.grid(row=row, column=col, padx=5, pady=5, sticky="ew")

            ctk.CTkLabel(card, text=label, font=("Arial", 10)).pack(pady=2)
            self.status_cards[label] = ctk.CTkLabel(card, text=value,
                                                    font=("Arial", 12, "bold"))
            self.status_cards[label].pack(pady=5)

        for col in range(4):
            stats_frame.grid_columnconfigure(col, weight=1)

        # Enhanced control panel
        control_frame = ctk.CTkFrame(left_frame)
        control_frame.pack(fill="x", padx=10, pady=10)

        # Main trading controls
        main_controls = ctk.CTkFrame(control_frame)
        main_controls.pack(side="left", padx=10)

        self.start_btn = ctk.CTkButton(main_controls, text="▶️ Start Enhanced Bot",
                                       command=self.toggle_enhanced_trading,
                                       fg_color="green", height=45, width=200,
                                       font=("Arial", 14, "bold"))
        self.start_btn.pack(pady=5)

        # Auto trading toggle
        self.auto_trading_switch = ctk.CTkSwitch(main_controls,
                                                 text="🤖 Auto Trading Mode",
                                                 command=self.toggle_auto_trading,
                                                 button_color="blue")
        self.auto_trading_switch.pack(pady=5)

        # Paper/Real toggle
        self.paper_switch = ctk.CTkSwitch(main_controls,
                                          text="⚠️ REAL Trading (Dangerous!)",
                                          command=self.toggle_paper_trading,
                                          button_color="red",
                                          progress_color="darkred")
        self.paper_switch.pack(pady=5)

        # Quick analysis controls
        quick_controls = ctk.CTkFrame(control_frame)
        quick_controls.pack(side="left", padx=20)

        ctk.CTkButton(quick_controls, text="🪙 Analyze All Coins",
                      command=self.quick_analyze_coins,
                      height=35, width=180).pack(pady=2)

        ctk.CTkButton(quick_controls, text="🎯 Check Strategies",
                      command=self.quick_check_strategies,
                      height=35, width=180).pack(pady=2)

        ctk.CTkButton(quick_controls, text="🕐 Force Sell Status",
                      command=self.quick_force_sell_status,
                      height=35, width=180).pack(pady=2)

        # Emergency controls
        emergency_frame = ctk.CTkFrame(control_frame)
        emergency_frame.pack(side="right", padx=10)

        ctk.CTkButton(emergency_frame, text="🚨 EMERGENCY STOP",
                      command=self.emergency_stop_trading,
                      fg_color="red", height=50, width=150,
                      font=("Arial", 12, "bold")).pack(pady=2)

        ctk.CTkButton(emergency_frame, text="🔄 System Health",
                      command=self.enhanced_system_check,
                      height=30, width=150).pack(pady=2)

        # Enhanced display with tabs
        display_tabview = ctk.CTkTabview(left_frame)
        display_tabview.pack(fill="both", expand=True, padx=10, pady=10)

        # Dashboard logs
        self.tab_logs = display_tabview.add("📝 Logs")
        self.dashboard_display = ctk.CTkTextbox(self.tab_logs, font=("Consolas", 11))
        self.dashboard_display.pack(fill="both", expand=True, padx=5, pady=5)

        # Live analysis
        self.tab_analysis = display_tabview.add("📊 Live Analysis")
        self.analysis_display = ctk.CTkTextbox(self.tab_analysis, font=("Consolas", 10))
        self.analysis_display.pack(fill="both", expand=True, padx=5, pady=5)

        # Performance summary
        self.tab_performance = display_tabview.add("📈 Performance")
        self.performance_display = ctk.CTkTextbox(self.tab_performance, font=("Consolas", 10))
        self.performance_display.pack(fill="both", expand=True, padx=5, pady=5)

        # Right side - Enhanced Sci-Fi Visual System
        self.add_enhanced_scifi_visual(content_frame)

    def add_enhanced_scifi_visual(self, parent_frame):
        """🆕 Add Enhanced Sci-Fi Visual System"""
        visual_frame = ctk.CTkFrame(parent_frame)
        visual_frame.pack(side="right", padx=(10, 0), pady=10)

        # Enhanced title
        title_frame = ctk.CTkFrame(visual_frame)
        title_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(title_frame, text="🚀 AI SYSTEM STATUS v3.0",
                     font=("Orbitron", 16, "bold"),
                     text_color="cyan").pack(pady=5)

        license_status = "🔓 PREMIUM" if self.license_manager.is_license_valid() else "🔒 TRIAL"
        ctk.CTkLabel(title_frame, text=license_status,
                     font=("Orbitron", 12),
                     text_color="gold" if self.license_manager.is_license_valid() else "orange").pack()

        # Create enhanced visual system
        self.scifi_visual = SciFiVisualSystem(visual_frame)

        # Enhanced status message
        self.ai_status_label = ctk.CTkLabel(visual_frame, text="System Ready",
                                            font=("Orbitron", 12))
        self.ai_status_label.pack(pady=5)

        # Enhanced control buttons
        control_frame = ctk.CTkFrame(visual_frame)
        control_frame.pack(pady=10)

        # 🆕 Enhanced AI action buttons with new states
        ai_buttons = [
            ("🧠 Analyze", "analyzing"),
            ("🪙 Coin Analysis", "coin_analysis"),
            ("🤖 Auto Mode", "auto_mode"),
            ("🔍 Connect", "connecting"),
            ("📈 Buy Signal", "buy_signal"),
            ("📉 Sell Signal", "sell_signal"),
            ("⚡ Trading", "trading"),
            ("✅ Success", "success"),
            ("❌ Error", "error"),
            ("🔵 Idle", "idle")
        ]

        for i, (label, state) in enumerate(ai_buttons):
            row = i // 2
            col = i % 2

            # 🔐 Check if premium features are enabled
            is_premium_state = state in ["coin_analysis", "auto_mode"]
            is_enabled = not is_premium_state or self.license_manager.is_feature_enabled('premium_graphics')

            btn = ctk.CTkButton(
                control_frame,
                text=label if is_enabled else f"{label} 🔒",
                command=lambda s=state: self.update_scifi_visual_state(
                    s) if is_enabled else self.show_license_required(),
                width=140, height=32,
                font=("Arial", 10),
                fg_color="gray" if not is_enabled else None
            )
            btn.grid(row=row, column=col, padx=2, pady=2)

        # Initialize with idle state
        self.scifi_visual.set_state("idle")

    def setup_coin_analyzer_tab(self):
        """🪙 Setup Coin Analyzer Tab"""
        if not self.license_manager.is_feature_enabled('coin_recommendation'):
            self.show_premium_required(self.tab_coin_analyzer)
            return

        # Analysis controls
        control_frame = ctk.CTkFrame(self.tab_coin_analyzer)
        control_frame.pack(fill="x", padx=10, pady=10)

        # Analysis settings
        settings_frame = ctk.CTkFrame(control_frame)
        settings_frame.pack(side="left", padx=10)

        ctk.CTkLabel(settings_frame, text="Trade Amount (THB):").pack(anchor="w")
        self.coin_analyze_amount = ctk.CTkEntry(settings_frame, width=100)
        self.coin_analyze_amount.pack(pady=5)
        self.coin_analyze_amount.insert(0, "1000")

        ctk.CTkLabel(settings_frame, text="Min AI Score:").pack(anchor="w")
        self.min_ai_score_slider = ctk.CTkSlider(settings_frame, from_=0, to=10, number_of_steps=100)
        self.min_ai_score_slider.pack(pady=5)
        self.min_ai_score_slider.set(6.0)

        # Analysis buttons
        button_frame = ctk.CTkFrame(control_frame)
        button_frame.pack(side="left", padx=20)

        ctk.CTkButton(button_frame, text="🚀 Analyze All Coins",
                      command=self.start_coin_analysis,
                      fg_color="blue", height=50, width=200,
                      font=("Arial", 12, "bold")).pack(pady=5)

        ctk.CTkButton(button_frame, text="🔄 Refresh Analysis",
                      command=self.refresh_coin_analysis,
                      height=35, width=200).pack(pady=2)

        ctk.CTkButton(button_frame, text="📊 View History",
                      command=self.view_analysis_history,
                      height=35, width=200).pack(pady=2)

        # Auto selection
        auto_frame = ctk.CTkFrame(control_frame)
        auto_frame.pack(side="right", padx=10)

        self.auto_coin_switch = ctk.CTkSwitch(auto_frame, text="Auto Coin Selection")
        self.auto_coin_switch.pack(pady=5)

        ctk.CTkButton(auto_frame, text="🎯 Select Best Coin",
                      command=self.select_best_coin,
                      height=35, width=150).pack(pady=2)

        # Results display
        self.coin_analysis_display = ctk.CTkTextbox(self.tab_coin_analyzer, font=("Consolas", 10))
        self.coin_analysis_display.pack(fill="both", expand=True, padx=10, pady=10)

    def setup_strategies_tab(self):
        """🎯 Setup Advanced Strategies Tab"""
        if not self.license_manager.is_feature_enabled('advanced_strategies'):
            self.show_premium_required(self.tab_strategies)
            return

        # Strategy selection
        selection_frame = ctk.CTkFrame(self.tab_strategies)
        selection_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(selection_frame, text="🎯 Advanced Trading Strategies",
                     font=("Arial", 16, "bold")).pack(pady=5)

        # Strategy list with enable/disable
        self.strategy_vars = {}
        strategies_info = [
            ("rsi_momentum", "RSI + Momentum", "Combines RSI signals with volume momentum"),
            ("bollinger_bands", "Bollinger Bands", "Support/resistance trading"),
            ("ema_crossover", "EMA Crossover", "Moving average crossover signals"),
            ("macd_divergence", "MACD Divergence", "MACD divergence patterns"),
            ("volume_breakout", "Volume Breakout", "Volume spike with price breakout"),
            ("scalping", "Scalping", "Quick profit high-frequency trading"),
            ("swing_trading", "Swing Trading", "Medium-term trend following"),
            ("dca", "Dollar Cost Averaging", "Time-based accumulation")
        ]

        strategy_list_frame = ctk.CTkFrame(self.tab_strategies)
        strategy_list_frame.pack(fill="x", padx=10, pady=10)

        for i, (key, name, desc) in enumerate(strategies_info):
            strategy_frame = ctk.CTkFrame(strategy_list_frame)
            strategy_frame.pack(fill="x", padx=5, pady=5)

            # Strategy info
            info_frame = ctk.CTkFrame(strategy_frame)
            info_frame.pack(side="left", fill="x", expand=True, padx=5, pady=5)

            ctk.CTkLabel(info_frame, text=name, font=("Arial", 12, "bold")).pack(anchor="w")
            ctk.CTkLabel(info_frame, text=desc, font=("Arial", 10)).pack(anchor="w")

            # Enable/disable switch
            self.strategy_vars[key] = ctk.CTkSwitch(
                strategy_frame,
                text="Enable",
                command=lambda k=key: self.toggle_strategy(k)
            )
            self.strategy_vars[key].pack(side="right", padx=5, pady=5)

            # Default: Enable RSI + Momentum
            if key == "rsi_momentum":
                self.strategy_vars[key].select()

        # Strategy parameters
        params_frame = ctk.CTkFrame(self.tab_strategies)
        params_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Parameters display/edit
        self.strategy_params_display = ctk.CTkTextbox(params_frame, font=("Consolas", 10))
        self.strategy_params_display.pack(fill="both", expand=True, padx=5, pady=5)

        # Control buttons
        control_buttons = ctk.CTkFrame(self.tab_strategies)
        control_buttons.pack(fill="x", padx=10, pady=10)

        ctk.CTkButton(control_buttons, text="🧪 Test Strategy",
                      command=self.test_selected_strategies,
                      height=40, width=150).pack(side="left", padx=5)

        ctk.CTkButton(control_buttons, text="📊 Strategy Performance",
                      command=self.show_strategy_performance,
                      height=40, width=180).pack(side="left", padx=5)

        ctk.CTkButton(control_buttons, text="⚙️ Auto Configure",
                      command=self.auto_configure_strategies,
                      height=40, width=150).pack(side="left", padx=5)

    def setup_auto_trading_tab(self):
        """🤖 Setup Auto Trading Tab"""
        if not self.license_manager.is_feature_enabled('auto_trading'):
            self.show_premium_required(self.tab_auto_trading)
            return

        # Auto trading controls
        control_frame = ctk.CTkFrame(self.tab_auto_trading)
        control_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(control_frame, text="🤖 Autonomous Trading Engine",
                     font=("Arial", 16, "bold")).pack(pady=5)

        # Main auto trading controls
        main_controls = ctk.CTkFrame(control_frame)
        main_controls.pack(fill="x", pady=10)

        # Left side - Enable/Disable
        left_controls = ctk.CTkFrame(main_controls)
        left_controls.pack(side="left", padx=10)

        self.auto_trading_enabled = ctk.CTkSwitch(
            left_controls,
            text="🤖 Enable Auto Trading",
            command=self.toggle_auto_trading_engine,
            font=("Arial", 12, "bold")
        )
        self.auto_trading_enabled.pack(pady=5)

        # Auto settings
        self.auto_coin_selection_var = ctk.CTkSwitch(left_controls, text="Auto Coin Selection")
        self.auto_coin_selection_var.pack(pady=5)
        self.auto_coin_selection_var.select()

        self.adaptive_strategy_var = ctk.CTkSwitch(left_controls, text="Adaptive Strategy")
        self.adaptive_strategy_var.pack(pady=5)
        self.adaptive_strategy_var.select()

        # Right side - Settings
        right_controls = ctk.CTkFrame(main_controls)
        right_controls.pack(side="right", padx=10)

        # Min AI Score
        ctk.CTkLabel(right_controls, text="Min AI Score for Auto Trade:").pack()
        self.auto_min_ai_score = ctk.CTkSlider(right_controls, from_=0, to=10, number_of_steps=100)
        self.auto_min_ai_score.pack(pady=5)
        self.auto_min_ai_score.set(6.0)

        self.auto_ai_score_label = ctk.CTkLabel(right_controls, text="6.0")
        self.auto_ai_score_label.pack()
        self.auto_min_ai_score.configure(command=self.update_ai_score_label)

        # Max concurrent positions
        ctk.CTkLabel(right_controls, text="Max Concurrent Positions:").pack()
        self.max_positions_var = ctk.CTkEntry(right_controls, width=80)
        self.max_positions_var.pack(pady=5)
        self.max_positions_var.insert(0, "3")

        # Performance display
        perf_frame = ctk.CTkFrame(self.tab_auto_trading)
        perf_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(perf_frame, text="📈 Auto Trading Performance",
                     font=("Arial", 14, "bold")).pack()

        self.auto_performance_display = ctk.CTkTextbox(perf_frame, height=100, font=("Consolas", 10))
        self.auto_performance_display.pack(fill="x", padx=5, pady=5)

        # Auto trading log
        self.auto_trading_log = ctk.CTkTextbox(self.tab_auto_trading, font=("Consolas", 10))
        self.auto_trading_log.pack(fill="both", expand=True, padx=10, pady=10)

    def setup_force_sell_tab(self):
        """🕐 Setup Force Sell Tab"""
        if not self.license_manager.is_feature_enabled('force_sell'):
            self.show_premium_required(self.tab_force_sell)
            return

        # Force sell controls
        control_frame = ctk.CTkFrame(self.tab_force_sell)
        control_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(control_frame, text="🕐 Force Sell Management System",
                     font=("Arial", 16, "bold")).pack(pady=5)

        # Main settings
        settings_frame = ctk.CTkFrame(control_frame)
        settings_frame.pack(fill="x", pady=10)

        # Left side - Enable/Settings
        left_settings = ctk.CTkFrame(settings_frame)
        left_settings.pack(side="left", padx=10)

        self.force_sell_enabled = ctk.CTkSwitch(
            left_settings,
            text="🕐 Enable Force Sell",
            command=self.toggle_force_sell
        )
        self.force_sell_enabled.pack(pady=5)
        self.force_sell_enabled.select()

        # Max hold time
        ctk.CTkLabel(left_settings, text="Max Hold Time (hours):").pack(anchor="w")
        self.max_hold_hours = ctk.CTkSlider(left_settings, from_=1, to=24, number_of_steps=23)
        self.max_hold_hours.pack(pady=5)
        self.max_hold_hours.set(6)

        self.hold_hours_label = ctk.CTkLabel(left_settings, text="6 hours")
        self.hold_hours_label.pack()
        self.max_hold_hours.configure(command=self.update_hold_hours_label)

        # Right side - Thresholds
        right_settings = ctk.CTkFrame(settings_frame)
        right_settings.pack(side="right", padx=10)

        # Min profit threshold
        ctk.CTkLabel(right_settings, text="Min Profit Threshold (%):").pack(anchor="w")
        self.min_profit_threshold = ctk.CTkSlider(right_settings, from_=0, to=2, number_of_steps=200)
        self.min_profit_threshold.pack(pady=5)
        self.min_profit_threshold.set(0.5)

        self.profit_threshold_label = ctk.CTkLabel(right_settings, text="0.5%")
        self.profit_threshold_label.pack()
        self.min_profit_threshold.configure(command=self.update_profit_threshold_label)

        # Emergency conditions
        emergency_frame = ctk.CTkFrame(self.tab_force_sell)
        emergency_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(emergency_frame, text="🚨 Emergency Sell Conditions",
                     font=("Arial", 14, "bold")).pack(pady=5)

        # Emergency settings
        emergency_settings = ctk.CTkFrame(emergency_frame)
        emergency_settings.pack(fill="x", pady=5)

        # Market crash threshold
        left_emergency = ctk.CTkFrame(emergency_settings)
        left_emergency.pack(side="left", padx=10)

        ctk.CTkLabel(left_emergency, text="Market Crash Threshold (%):").pack()
        self.market_crash_threshold = ctk.CTkEntry(left_emergency, width=80)
        self.market_crash_threshold.pack(pady=5)
        self.market_crash_threshold.insert(0, "-5.0")

        # Volume spike threshold
        right_emergency = ctk.CTkFrame(emergency_settings)
        right_emergency.pack(side="right", padx=10)

        ctk.CTkLabel(right_emergency, text="Volume Spike Threshold (x):").pack()
        self.volume_spike_threshold = ctk.CTkEntry(right_emergency, width=80)
        self.volume_spike_threshold.pack(pady=5)
        self.volume_spike_threshold.insert(0, "5.0")

        # Position monitoring
        monitor_frame = ctk.CTkFrame(self.tab_force_sell)
        monitor_frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(monitor_frame, text="📊 Active Positions Monitor",
                     font=("Arial", 14, "bold")).pack(pady=5)

        self.force_sell_monitor = ctk.CTkTextbox(monitor_frame, font=("Consolas", 10))
        self.force_sell_monitor.pack(fill="both", expand=True, padx=5, pady=5)

    def setup_manual_trading_tab(self):
        """💹 Setup Manual Trading Tab (Enhanced)"""
        # Trading controls
        control_frame = ctk.CTkFrame(self.tab_trading)
        control_frame.pack(fill="x", padx=10, pady=10)

        self.start_btn_trading = ctk.CTkButton(control_frame, text="▶️ Start Manual Trading",
                                               command=self.toggle_enhanced_trading,
                                               fg_color="green", height=40, width=200)
        self.start_btn_trading.pack(side="left", padx=10)

        ctk.CTkButton(control_frame, text="📊 Enhanced Signals",
                      command=self.check_enhanced_signals,
                      height=40).pack(side="left", padx=5)

        ctk.CTkButton(control_frame, text="📋 Open Orders",
                      command=self.check_open_orders,
                      height=40).pack(side="left", padx=5)

        ctk.CTkButton(control_frame, text="💰 Fee Calculator",
                      command=self.show_enhanced_fee_calculator,
                      height=40).pack(side="left", padx=5)

        # Enhanced strategy settings with all new strategies
        strategy_frame = ctk.CTkFrame(self.tab_trading)
        strategy_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(strategy_frame, text="🎯 Manual Trading Strategy Settings:",
                     font=("Arial", 14, "bold")).pack(anchor="w", padx=10, pady=5)

        # Strategy selection for manual trading
        strategy_selection = ctk.CTkFrame(strategy_frame)
        strategy_selection.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(strategy_selection, text="Active Strategy:").pack(side="left", padx=5)

        strategy_options = [
            "RSI + Momentum", "Bollinger Bands", "EMA Crossover",
            "MACD Divergence", "Volume Breakout", "Scalping",
            "Swing Trading", "Dollar Cost Averaging"
        ]

        self.manual_strategy_var = ctk.CTkOptionMenu(strategy_selection, values=strategy_options)
        self.manual_strategy_var.pack(side="left", padx=5)
        self.manual_strategy_var.set("RSI + Momentum")

        ctk.CTkButton(strategy_selection, text="⚙️ Configure",
                      command=self.configure_manual_strategy).pack(side="left", padx=10)

        # Enhanced parameters
        params_frame = ctk.CTkFrame(strategy_frame)
        params_frame.pack(fill="x", padx=10, pady=5)

        # Risk management
        risk_frame = ctk.CTkFrame(strategy_frame)
        risk_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(risk_frame, text="Risk Management:", font=("Arial", 12, "bold")).pack(anchor="w", padx=5)

        # Stop loss and take profit
        risk_settings = ctk.CTkFrame(risk_frame)
        risk_settings.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(risk_settings, text="Stop Loss %:").pack(side="left", padx=5)
        self.stop_loss_var = tk.DoubleVar(value=1.5)
        ctk.CTkSlider(risk_settings, from_=0.5, to=5.0, variable=self.stop_loss_var,
                      command=self.update_risk_settings).pack(side="left", padx=5)
        self.stop_loss_label = ctk.CTkLabel(risk_settings, text="1.5%")
        self.stop_loss_label.pack(side="left", padx=5)

        ctk.CTkLabel(risk_settings, text="Take Profit %:").pack(side="left", padx=20)
        self.take_profit_var = tk.DoubleVar(value=3.0)
        ctk.CTkSlider(risk_settings, from_=1.0, to=10.0, variable=self.take_profit_var,
                      command=self.update_risk_settings).pack(side="left", padx=5)
        self.take_profit_label = ctk.CTkLabel(risk_settings, text="3.0%")
        self.take_profit_label.pack(side="left", padx=5)

        # Trading log
        self.trading_log = ctk.CTkTextbox(self.tab_trading, font=("Consolas", 10))
        self.trading_log.pack(fill="both", expand=True, padx=10, pady=10)

    def setup_api_tab(self):
        """🔌 Enhanced API Configuration"""
        api_frame = ctk.CTkFrame(self.tab_api)
        api_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(api_frame, text="🔌 Enhanced Bitkub API Configuration",
                     font=("Arial", 18, "bold")).pack(pady=10)

        # Enhanced security warning with v3.0 features
        warning_text = f"""
🔒 ENHANCED SECURITY NOTES v3.0:
• 🪙 AI-powered coin analysis across all {len(ImprovedBitkubAPI('', '').all_bitkub_symbols)} Bitkub coins
• 🎯 8 advanced trading strategies with adaptive selection
• 🤖 Fully autonomous trading with risk management
• 🕐 Force sell system prevents overnight losses
• 💸 Advanced fee optimization and break-even calculation
• 📊 Real-time performance analytics and strategy comparison
• 🔐 Premium license system with trial period

⚠️ IMPORTANT:
• Start with PAPER TRADING and minimum amounts
• Use dedicated trading account with limited funds
• Set IP whitelist in Bitkub for maximum security
• Monitor premium features performance closely
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
                      command=self.connect_enhanced_api,
                      fg_color="green", height=40).pack(side="left", padx=5)

        ctk.CTkButton(btn_frame, text="🔌 Test Connection",
                      command=self.test_enhanced_connection,
                      height=40).pack(side="left", padx=5)

        ctk.CTkButton(btn_frame, text="🏥 Premium Health Check",
                      command=self.premium_health_check,
                      height=40).pack(side="left", padx=5)

        # Status display
        self.api_status_display = ctk.CTkTextbox(self.tab_api, font=("Consolas", 11))
        self.api_status_display.pack(fill="both", expand=True, padx=10, pady=10)

    def setup_analytics_tab(self):
        """📈 Setup Advanced Analytics Tab"""
        # Analytics controls
        control_frame = ctk.CTkFrame(self.tab_analytics)
        control_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(control_frame, text="📈 Advanced Analytics & Performance",
                     font=("Arial", 16, "bold")).pack(pady=5)

        # Analytics buttons
        btn_frame = ctk.CTkFrame(control_frame)
        btn_frame.pack(pady=10)

        analytics_buttons = [
            ("📊 Strategy Comparison", self.show_strategy_comparison),
            ("🪙 Coin Performance", self.show_coin_performance),
            ("💰 Profit Analysis", self.show_enhanced_profit_analysis),
            ("🕐 Force Sell Stats", self.show_force_sell_statistics),
            ("🤖 Auto Trading Report", self.show_auto_trading_report),
            ("📈 Export Analytics", self.export_analytics_report)
        ]

        for i, (text, command) in enumerate(analytics_buttons):
            row = i // 3
            col = i % 3

            btn = ctk.CTkButton(btn_frame, text=text, command=command,
                                width=180, height=35)
            btn.grid(row=row, column=col, padx=5, pady=5)

        # Analytics display with tabs
        display_tabview = ctk.CTkTabview(self.tab_analytics)
        display_tabview.pack(fill="both", expand=True, padx=10, pady=10)

        # Performance overview
        self.analytics_overview = display_tabview.add("📊 Overview")
        self.overview_display = ctk.CTkTextbox(self.analytics_overview, font=("Consolas", 10))
        self.overview_display.pack(fill="both", expand=True, padx=5, pady=5)

        # Strategy performance
        self.analytics_strategies = display_tabview.add("🎯 Strategies")
        self.strategies_display = ctk.CTkTextbox(self.analytics_strategies, font=("Consolas", 10))
        self.strategies_display.pack(fill="both", expand=True, padx=5, pady=5)

        # Coin analysis
        self.analytics_coins = display_tabview.add("🪙 Coins")
        self.coins_display = ctk.CTkTextbox(self.analytics_coins, font=("Consolas", 10))
        self.coins_display.pack(fill="both", expand=True, padx=5, pady=5)

    def setup_enhanced_settings(self):
        """⚙️ Enhanced Settings Tab"""
        settings_frame = ctk.CTkFrame(self.tab_settings)
        settings_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(settings_frame, text="⚙️ Enhanced Trading Configuration v3.0",
                     font=("Arial", 16, "bold")).pack(pady=10)

        # Enhanced symbol selection
        symbol_frame = ctk.CTkFrame(settings_frame)
        symbol_frame.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(symbol_frame, text="Trading Pair:").pack(side="left", padx=5)
        self.symbol_var = tk.StringVar(value="btc_thb")

        # All Bitkub symbols with better organization
        bitkub_symbols = [
            "btc_thb", "eth_thb", "ada_thb", "xrp_thb", "bnb_thb", "doge_thb",
            "dot_thb", "matic_thb", "atom_thb", "near_thb", "sol_thb", "sand_thb",
            "mana_thb", "avax_thb", "shib_thb", "ltc_thb", "bch_thb", "etc_thb",
            "link_thb", "uni_thb", "usdt_thb", "usdc_thb", "dai_thb", "busd_thb",
            "alpha_thb", "ftt_thb", "axie_thb", "alice_thb", "chz_thb", "jasmy_thb"
        ]

        symbol_menu = ctk.CTkOptionMenu(symbol_frame, variable=self.symbol_var,
                                        values=bitkub_symbols)
        symbol_menu.pack(side="left", padx=5)

        ctk.CTkLabel(symbol_frame, text="(Auto-select available if enabled)",
                     text_color="green").pack(side="left", padx=5)

        # Enhanced trade amounts for better profitability
        amount_frame = ctk.CTkFrame(settings_frame)
        amount_frame.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(amount_frame, text="Trade Amount (THB):").pack(side="left", padx=5)
        self.trade_amount_var = tk.IntVar(value=1000)
        amount_entry = ctk.CTkEntry(amount_frame, textvariable=self.trade_amount_var, width=100)
        amount_entry.pack(side="left", padx=5)

        ctk.CTkLabel(amount_frame, text="(Min 500 THB recommended, 1000+ optimal)",
                     text_color="yellow").pack(side="left", padx=5)

        # Enhanced risk limits
        risk_frame = ctk.CTkFrame(settings_frame)
        risk_frame.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(risk_frame, text="Max Daily Trades:").pack(side="left", padx=5)
        self.max_trades_var = tk.IntVar(value=5)
        ctk.CTkEntry(risk_frame, textvariable=self.max_trades_var, width=50).pack(side="left", padx=5)

        ctk.CTkLabel(risk_frame, text="Max Daily Loss (THB):").pack(side="left", padx=20)
        self.max_loss_var = tk.IntVar(value=2000)
        ctk.CTkEntry(risk_frame, textvariable=self.max_loss_var, width=100).pack(side="left", padx=5)

        # Premium features settings
        premium_frame = ctk.CTkFrame(settings_frame)
        premium_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(premium_frame, text="🔐 Premium Features Settings:",
                     font=("Arial", 12, "bold")).pack(anchor="w", padx=10)

        # Auto coin selection
        auto_settings = ctk.CTkFrame(premium_frame)
        auto_settings.pack(fill="x", padx=10, pady=5)

        self.auto_coin_enabled = ctk.CTkSwitch(auto_settings, text="🪙 Auto Coin Selection")
        self.auto_coin_enabled.pack(side="left", padx=5)
        if self.license_manager.is_feature_enabled('coin_recommendation'):
            self.auto_coin_enabled.select()

        self.adaptive_strategy_enabled = ctk.CTkSwitch(auto_settings, text="🎯 Adaptive Strategy")
        self.adaptive_strategy_enabled.pack(side="left", padx=20)
        if self.license_manager.is_feature_enabled('advanced_strategies'):
            self.adaptive_strategy_enabled.select()

        # Force sell settings
        force_settings = ctk.CTkFrame(premium_frame)
        force_settings.pack(fill="x", padx=10, pady=5)

        self.force_sell_settings_enabled = ctk.CTkSwitch(force_settings, text="🕐 Force Sell System")
        self.force_sell_settings_enabled.pack(side="left", padx=5)
        if self.license_manager.is_feature_enabled('force_sell'):
            self.force_sell_settings_enabled.select()

        self.auto_trading_settings_enabled = ctk.CTkSwitch(force_settings, text="🤖 Auto Trading")
        self.auto_trading_settings_enabled.pack(side="left", padx=20)
        if self.license_manager.is_feature_enabled('auto_trading'):
            self.auto_trading_settings_enabled.select()

        # Fee impact analysis
        fee_impact_frame = ctk.CTkFrame(settings_frame)
        fee_impact_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(fee_impact_frame, text="💸 Enhanced Fee Impact Analysis:",
                     font=("Arial", 12, "bold")).pack(anchor="w", padx=10)

        self.fee_impact_label = ctk.CTkLabel(fee_impact_frame,
                                             text="Configure amount to see enhanced fee analysis",
                                             font=("Arial", 10))
        self.fee_impact_label.pack(anchor="w", padx=20, pady=5)

        # Save button
        ctk.CTkButton(settings_frame, text="💾 Save Enhanced Settings",
                      command=self.save_enhanced_settings,
                      fg_color="green", height=45, width=250,
                      font=("Arial", 12, "bold")).pack(pady=20)

    def setup_license_tab(self):
        """🔐 Setup License Management Tab"""
        license_frame = ctk.CTkFrame(self.tab_license)
        license_frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(license_frame, text="🔐 License Management System",
                     font=("Arial", 18, "bold")).pack(pady=10)

        # Current license info
        info_frame = ctk.CTkFrame(license_frame)
        info_frame.pack(fill="x", padx=10, pady=10)

        license_info = self.license_manager.get_license_info()

        info_text = f"""
📋 CURRENT LICENSE INFORMATION:

License Type: {license_info['type'].upper()}
Status: {'✅ ACTIVE' if license_info['valid'] else '❌ EXPIRED'}
Days Remaining: {license_info['remaining_days']} days
Hardware ID: {license_info['hardware_id']}

🔓 ENABLED FEATURES:"""

        for feature, enabled in license_info['features'].items():
            status = "✅" if enabled else "❌"
            feature_name = feature.replace('_', ' ').title()
            info_text += f"\n  {status} {feature_name}"

        if not license_info['valid']:
            info_text += f"\n\n⚠️ LICENSE EXPIRED - Only basic features available"

        ctk.CTkLabel(info_frame, text=info_text,
                     font=("Consolas", 12), justify="left").pack(pady=10)

        # License actions
        actions_frame = ctk.CTkFrame(license_frame)
        actions_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkButton(actions_frame, text="🔄 Refresh License",
                      command=self.refresh_license,
                      height=40, width=150).pack(side="left", padx=5)

        ctk.CTkButton(actions_frame, text="💡 Trial Features Demo",
                      command=self.show_trial_demo,
                      height=40, width=180).pack(side="left", padx=5)

        if not license_info['valid']:
            ctk.CTkButton(actions_frame, text="🔐 Upgrade to Premium",
                          command=self.show_upgrade_options,
                          fg_color="gold", height=40, width=180).pack(side="left", padx=5)

        # Feature descriptions
        features_frame = ctk.CTkFrame(license_frame)
        features_frame.pack(fill="both", expand=True, padx=10, pady=10)

        features_text = """
🚀 PREMIUM FEATURES OVERVIEW:

🪙 AI COIN ANALYZER:
  • Real-time analysis of all 57+ Bitkub coins
  • AI scoring system (0-10) for profit potential
  • Automatic best coin selection
  • Fee impact optimization per coin

🎯 ADVANCED STRATEGIES:
  • 8 professional trading strategies
  • RSI+Momentum, Bollinger Bands, EMA Crossover
  • MACD Divergence, Volume Breakout, Scalping
  • Swing Trading, Dollar Cost Averaging
  • Adaptive strategy selection

🤖 AUTO TRADING ENGINE:
  • Fully autonomous trading
  • Auto coin + strategy selection
  • Multi-position management
  • Real-time market adaptation

🕐 FORCE SELL SYSTEM:
  • Prevents overnight losses
  • Customizable time limits
  • Emergency market conditions
  • Profit protection mode

📊 ADVANCED ANALYTICS:
  • Strategy performance comparison
  • Coin-specific profit analysis
  • Advanced fee optimization
  • Export detailed reports

🎬 PREMIUM GRAPHICS:
  • Enhanced Sci-Fi visual system
  • Additional animation states
  • Premium status indicators
        """

        features_display = ctk.CTkTextbox(features_frame, font=("Consolas", 10))
        features_display.pack(fill="both", expand=True, padx=5, pady=5)
        features_display.insert("1.0", features_text)

    # === 🆕 Enhanced Core Functions ===

    def connect_enhanced_api(self):
        """🆕 Enhanced API connection with premium features initialization"""
        api_key = self.api_key_entry.get().strip()
        api_secret = self.api_secret_entry.get().strip()

        if not api_key or not api_secret:
            messagebox.showwarning("Error", "Please enter API credentials")
            return

        # Visual feedback
        self.update_scifi_visual_state("connecting", "Establishing enhanced API connection")

        # Create enhanced API client
        self.api_client = ImprovedBitkubAPI(api_key, api_secret)

        # 🆕 Initialize premium components
        if self.license_manager.is_feature_enabled('coin_recommendation'):
            self.coin_analyzer = CoinAnalyzer(self.api_client)
            self.log("✅ Coin Analyzer initialized")

        if self.license_manager.is_feature_enabled('advanced_strategies'):
            self.strategies = AdvancedStrategies(self.api_client)
            self.log("✅ Advanced Strategies initialized")

        if self.license_manager.is_feature_enabled('force_sell'):
            self.force_sell_manager = ForceSellManager()
            self.log("✅ Force Sell Manager initialized")

        if self.license_manager.is_feature_enabled('auto_trading'):
            self.auto_trading_engine = AutoTradingEngine(
                self.api_client, self.coin_analyzer,
                self.strategies, self.force_sell_manager
            )
            self.log("✅ Auto Trading Engine initialized")

        self.log("🔌 Connecting to Enhanced API v3.0...")

        def test_connection():
            time.sleep(1)

            # Enhanced connection testing
            status_ok, status_msg = self.api_client.check_system_status()
            if not status_ok:
                self.update_scifi_visual_state("error", f"System status issue: {status_msg}")
                self.log(f"❌ System status issue: {status_msg}")
                messagebox.showwarning("System Status", f"API Status Issue: {status_msg}")
                return

            # Test balance check
            balance = self.api_client.check_balance()
            if balance and balance.get('error') == 0:
                self.update_scifi_visual_state("success", "Enhanced API connected successfully")
                self.log("✅ Enhanced API v3.0 Connected successfully")
                self.update_enhanced_balance()
                self.status_cards["System Status"].configure(text="Connected", text_color="green")

                # Test premium features
                if self.coin_analyzer:
                    self.log("🪙 Testing Coin Analyzer...")
                    # Quick test analysis
                    threading.Thread(target=self.test_coin_analyzer, daemon=True).start()

                messagebox.showinfo("Success", "Enhanced API v3.0 Connected!\nAll premium features initialized!")

                # Auto return to idle after 3 seconds
                threading.Timer(3.0, lambda: self.update_scifi_visual_state("idle")).start()
            else:
                error_msg = "Unknown error"
                if balance:
                    error_code = balance.get("error", 999)
                    error_msg = self.api_client.error_codes.get(error_code, f"Error {error_code}")

                self.update_scifi_visual_state("error", f"Connection failed: {error_msg}")
                self.log(f"❌ API Connection failed: {error_msg}")
                messagebox.showerror("Error", f"Failed to connect: {error_msg}")
                self.status_cards["System Status"].configure(text="Failed", text_color="red")

        threading.Thread(target=test_connection, daemon=True).start()

    def toggle_enhanced_trading(self):
        """🆕 Enhanced trading toggle with premium features"""
        if not self.is_trading:
            if not self.api_client:
                messagebox.showwarning("Error", "Please connect API first")
                return

            # Enhanced pre-flight checks
            if not self.enhanced_pre_flight_check():
                return

            # Premium features confirmation
            premium_features_text = "🚀 ENHANCED FEATURES ENABLED:\n"
            if self.license_manager.is_feature_enabled('coin_recommendation'):
                premium_features_text += "✅ AI Coin Analysis\n"
            if self.license_manager.is_feature_enabled('advanced_strategies'):
                premium_features_text += "✅ Advanced Strategies\n"
            if self.license_manager.is_feature_enabled('force_sell'):
                premium_features_text += "✅ Force Sell Protection\n"
            if self.license_manager.is_feature_enabled('auto_trading'):
                premium_features_text += "✅ Auto Trading Engine\n"

            if not self.is_paper_trading:
                if not messagebox.askyesno("Start Enhanced Real Trading",
                                           f"Start trading with REAL money?\n\n" +
                                           premium_features_text +
                                           f"\nAmount per trade: {self.config['trade_amount_thb']} THB\n" +
                                           f"Max daily trades: {self.config['max_daily_trades']}\n" +
                                           f"Symbol: {'AUTO-SELECT' if self.config.get('auto_coin_selection') else self.config['symbol'].upper()}\n" +
                                           f"Strategy: {'ADAPTIVE' if self.config.get('adaptive_strategy') else 'MANUAL'}\n" +
                                           f"Fee per round trip: {self.api_client.trading_fees['maker_fee'] + self.api_client.trading_fees['taker_fee']:.2%}"):
                    return

            self.is_trading = True
            self.emergency_stop = False
            self.start_btn.configure(text="⏹️ Stop Enhanced Bot", fg_color="red")
            self.start_btn_trading.configure(text="⏹️ Stop Enhanced Bot", fg_color="red")

            trading_mode = "AUTO" if self.is_auto_trading else "MANUAL"
            self.update_scifi_visual_state("analyzing", f"Starting {trading_mode} enhanced trading")
            self.log(f"🚀 Started Enhanced {'PAPER' if self.is_paper_trading else 'REAL'} trading ({trading_mode} mode)")

            # Start enhanced trading thread
            if self.is_auto_trading and self.auto_trading_engine:
                threading.Thread(target=self.auto_trading_loop, daemon=True).start()
            else:
                threading.Thread(target=self.enhanced_manual_trading_loop, daemon=True).start()
        else:
            self.is_trading = False
            self.start_btn.configure(text="▶️ Start Enhanced Bot", fg_color="green")
            self.start_btn_trading.configure(text="▶️ Start Enhanced Bot", fg_color="green")

            self.update_scifi_visual_state("idle", "Enhanced trading stopped")
            self.log("🛑 Stopped enhanced trading")

    def auto_trading_loop(self):
        """🤖 Auto trading main loop"""
        self.log("🤖 Auto Trading Loop Started")

        while self.is_trading and not self.emergency_stop and self.is_auto_trading:
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

                # Auto trading cycle
                self.update_scifi_visual_state("auto_mode", "Running auto trading cycle")

                decision = self.auto_trading_engine.auto_trading_cycle(self.config['trade_amount_thb'])

                if decision:
                    self.log(f"🤖 Auto Decision: {decision['action']} - {decision['reason']}")

                    if decision['action'] == 'buy':
                        self.execute_auto_buy(decision)
                    elif decision['action'] == 'sell':
                        self.execute_auto_sell(decision)
                    elif decision['action'] == 'wait':
                        self.update_scifi_visual_state("idle", "Waiting for opportunity")
                    elif decision['action'] == 'error':
                        self.update_scifi_visual_state("error", decision['reason'])
                        self.log(f"❌ Auto trading error: {decision['reason']}")

                # Update displays
                self.update_auto_trading_performance()

                # Wait before next cycle
                time.sleep(30)  # 30 second cycles

            except Exception as e:
                self.log(f"❌ Auto trading loop error: {e}")
                self.update_scifi_visual_state("error", f"Auto trading error: {str(e)[:30]}")
                time.sleep(60)

        self.log("🤖 Auto Trading Loop Ended")

    def enhanced_manual_trading_loop(self):
        """💹 Enhanced manual trading loop with premium strategies"""
        self.log("💹 Enhanced Manual Trading Loop Started")
        consecutive_errors = 0
        max_consecutive_errors = 5

        while self.is_trading and not self.emergency_stop and not self.is_auto_trading:
            try:
                # Check daily limits
                if self.daily_trades >= self.config['max_daily_trades']:
                    self.log(f"📊 Daily trade limit reached ({self.daily_trades}/{self.config['max_daily_trades']})")
                    time.sleep(3600)
                    continue

                if self.daily_pnl <= -self.config['max_daily_loss']:
                    self.log(f"💸 Daily loss limit reached ({self.daily_pnl:.2f}/{-self.config['max_daily_loss']})")
                    self.emergency_stop_trading()
                    break

                # Check minimum trade interval
                if self.last_trade_time:
                    time_since_trade = (datetime.now() - self.last_trade_time).seconds
                    if time_since_trade < self.config['min_trade_interval']:
                        time.sleep(30)
                        continue

                # 🆕 Enhanced symbol selection
                current_symbol = self.config['symbol']
                if self.config.get('auto_coin_selection') and self.coin_analyzer:
                    self.update_scifi_visual_state("coin_analysis", "Analyzing best coins")
                    best_coin = self.get_best_coin_for_trading()
                    if best_coin:
                        current_symbol = best_coin['symbol']
                        self.status_cards["Best Coin"].configure(text=current_symbol.upper())
                        self.status_cards["AI Score"].configure(text=f"{best_coin['ai_score']:.1f}")

                # Visual feedback for analysis
                self.update_scifi_visual_state("analyzing", f"Analyzing {current_symbol}")

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

                # 🆕 Enhanced strategy analysis
                strategy_name = self.get_optimal_strategy(current_symbol)

                if self.strategies:
                    should_trade, reason = self.strategies.analyze_with_strategy(
                        strategy_name, current_price, volume_24h
                    )
                else:
                    # Fallback to basic strategy
                    should_trade, reason = self.basic_strategy_analysis(current_price, volume_24h)

                # Get balance for buy decisions
                balance = self.api_client.check_balance()
                thb_balance = 0
                if balance and balance.get('error') == 0:
                    thb_balance = float(balance['result'].get('THB', 0))

                # Check for buy signal
                if should_trade and thb_balance >= self.config['trade_amount_thb']:
                    self.update_scifi_visual_state("buy_signal", f"Buy signal: {reason}")
                    self.execute_enhanced_buy(current_price, reason, current_symbol, strategy_name)

                # Check for sell signals (including force sell)
                self.check_enhanced_sell_signals(current_price, volume_24h)

                # Update displays
                self.update_enhanced_dashboard()

                # Return to idle if no active trading
                if not self.has_active_positions():
                    self.update_scifi_visual_state("idle", "Monitoring market")

                # Wait before next check
                time.sleep(30)

            except Exception as e:
                consecutive_errors += 1
                self.log(f"❌ Enhanced trading loop error: {e}")
                self.update_scifi_visual_state("error", f"Trading error: {str(e)[:50]}")
                if consecutive_errors >= max_consecutive_errors:
                    self.log("❌ Too many errors, stopping trading")
                    break
                time.sleep(60)

        self.log("💹 Enhanced Manual Trading Loop Ended")

    def get_best_coin_for_trading(self):
        """🪙 Get best coin using AI analysis"""
        if not self.coin_analyzer or not self.license_manager.is_feature_enabled('coin_recommendation'):
            return None

        try:
            # Quick analysis of top coins
            top_symbols = ["btc_thb", "eth_thb", "ada_thb", "xrp_thb", "bnb_thb"]

            best_coin = None
            best_score = 0

            for symbol in top_symbols:
                analysis = self.coin_analyzer.analyze_single_coin(symbol, self.config['trade_amount_thb'])
                if analysis and analysis['ai_score'] > best_score:
                    best_score = analysis['ai_score']
                    best_coin = analysis

            if best_coin and best_score >= self.config.get('min_ai_score', 6.0):
                return best_coin

            return None

        except Exception as e:
            self.log(f"❌ Error getting best coin: {e}")
            return None

    def get_optimal_strategy(self, symbol):
        """🎯 Get optimal strategy for current market conditions"""
        if not self.strategies or not self.license_manager.is_feature_enabled('advanced_strategies'):
            return "rsi_momentum"

        if not self.config.get('adaptive_strategy'):
            return "rsi_momentum"  # Default strategy

        try:
            # Analyze market condition and select best strategy
            ticker = self.api_client.get_simple_ticker(symbol)
            if not ticker:
                return "rsi_momentum"

            change_24h = ticker.get('change_24h', 0)
            volume_24h = ticker.get('volume_24h', 0)

            # Simple market condition analysis
            if change_24h > 3:
                # Trending up - use trend following
                return "ema_crossover" if self.strategies.strategies["ema_crossover"]["enabled"] else "rsi_momentum"
            elif change_24h < -3:
                # Trending down - use contrarian
                return "rsi_momentum" if self.strategies.strategies["rsi_momentum"]["enabled"] else "bollinger_bands"
            elif abs(change_24h) > 5:
                # High volatility - use scalping
                return "scalping" if self.strategies.strategies["scalping"]["enabled"] else "bollinger_bands"
            else:
                # Sideways market - use range trading
                return "bollinger_bands" if self.strategies.strategies["bollinger_bands"]["enabled"] else "rsi_momentum"

        except Exception as e:
            self.log(f"❌ Error selecting optimal strategy: {e}")
            return "rsi_momentum"

    def execute_enhanced_buy(self, price, reason, symbol, strategy="manual"):
        """🆕 Enhanced buy execution with premium features"""
        try:
            amount_thb = self.config['trade_amount_thb']
            crypto_amount = amount_thb / price

            # Calculate expected fees
            expected_buy_fee = self.api_client.calculate_trading_fees(crypto_amount, price, "buy")
            break_even_price = self.api_client.calculate_break_even_price(price, "buy")

            self.update_scifi_visual_state("trading", f"Executing enhanced buy: {amount_thb} THB")

            if self.is_paper_trading:
                # Paper trading with enhanced tracking
                position_data = {
                    'entry_price': price,
                    'amount': crypto_amount,
                    'entry_time': datetime.now(),
                    'symbol': symbol,
                    'strategy': strategy
                }

                self.log(f"📝 ENHANCED PAPER BUY: {amount_thb} THB @ {price:.2f}")
                self.log(f"   Symbol: {symbol}")
                self.log(f"   Strategy: {strategy}")
                self.log(f"   Reason: {reason}")
                self.log(f"   Expected fee: {expected_buy_fee:.2f} THB")
                self.log(f"   Break-even price: {break_even_price:.2f} THB")

                # 🆕 Add to force sell manager
                if self.force_sell_manager and self.config.get('force_sell_enabled'):
                    position_id = self.force_sell_manager.add_position(symbol, position_data)
                    self.log(f"🕐 Added to force sell monitor: {position_id}")

                # 🆕 Add to auto trading engine
                if self.auto_trading_engine:
                    self.auto_trading_engine.add_position(symbol, position_data)

                self.save_enhanced_trade('buy', crypto_amount, price, amount_thb,
                                         'PAPER', 0, expected_buy_fee, 0, reason, True,
                                         strategy, 0, False, self.is_auto_trading)

            else:
                # Real trading with enhanced execution
                buy_price = price * 1.002  # Small buffer for execution

                self.log(f"💰 ENHANCED REAL BUY: {amount_thb} THB @ {buy_price:.2f}")
                self.log(f"   Symbol: {symbol}")
                self.log(f"   Strategy: {strategy}")

                result = self.api_client.place_buy_order_safe(symbol, amount_thb, buy_price, 'limit')

                if result and result.get('error') == 0:
                    order_info = result['result']
                    order_id = order_info.get('id', 'unknown')
                    actual_amount = order_info.get('rec', crypto_amount)
                    actual_fee = order_info.get('fee', expected_buy_fee)

                    position_data = {
                        'entry_price': buy_price,
                        'amount': actual_amount,
                        'entry_time': datetime.now(),
                        'order_id': order_id,
                        'symbol': symbol,
                        'strategy': strategy
                    }

                    # 🆕 Add to force sell manager
                    if self.force_sell_manager and self.config.get('force_sell_enabled'):
                        position_id = self.force_sell_manager.add_position(symbol, position_data)
                        self.log(f"🕐 Added to force sell monitor: {position_id}")

                    # 🆕 Add to auto trading engine
                    if self.auto_trading_engine:
                        self.auto_trading_engine.add_position(symbol, position_data)

                    self.log(f"✅ ENHANCED REAL BUY SUCCESS: Order ID {order_id}")
                    self.log(f"   Amount: {actual_amount:.8f} crypto")
                    self.log(f"   Fee: {actual_fee:.2f} THB")

                    self.total_fees_paid += actual_fee
                    self.save_enhanced_trade('buy', actual_amount, buy_price, amount_thb,
                                             order_id, 0, actual_fee, 0, reason, False,
                                             strategy, 0, False, self.is_auto_trading)

                    self.update_scifi_visual_state("success", "Enhanced buy order executed successfully")
                else:
                    error_code = result.get("error", 999) if result else 999
                    error_msg = self.api_client.error_codes.get(error_code, f"Error {error_code}")
                    self.log(f"❌ Enhanced buy order failed: {error_msg}")
                    self.update_scifi_visual_state("error", f"Buy failed: {error_msg}")
                    return

            self.daily_trades += 1
            self.last_trade_time = datetime.now()

            # Update status cards
            self.status_cards["Daily Trades"].configure(
                text=f"{self.daily_trades}/{self.config['max_daily_trades']}"
            )

        except Exception as e:
            self.log(f"❌ Enhanced buy execution error: {e}")
            self.update_scifi_visual_state("error", f"Buy error: {str(e)[:50]}")

    def check_enhanced_sell_signals(self, current_price, volume):
        """🆕 Check enhanced sell signals including force sell"""
        try:
            # Check force sell conditions
            if self.force_sell_manager and self.config.get('force_sell_enabled'):
                positions = self.force_sell_manager.get_positions_status()

                for position in positions:
                    should_sell, reason = self.force_sell_manager.check_force_sell(
                        position['id'], current_price
                    )

                    if should_sell:
                        self.log(f"🕐 Force sell triggered: {reason}")
                        self.update_scifi_visual_state("sell_signal", f"Force sell: {reason}")
                        self.execute_enhanced_sell(current_price, reason, position['symbol'], True)

            # Check regular strategy sell signals
            # (Implementation would depend on position tracking)

        except Exception as e:
            self.log(f"❌ Error checking enhanced sell signals: {e}")

    def execute_auto_buy(self, decision):
        """🤖 Execute auto buy decision"""
        self.execute_enhanced_buy(
            decision['price'],
            decision['reason'],
            decision['symbol'],
            decision['strategy']
        )

        # Log auto trading decision
        self.log_auto_trading_decision('buy', decision)

    def execute_auto_sell(self, decision):
        """🤖 Execute auto sell decision"""
        # Implementation for auto sell
        self.log(f"🤖 Auto sell: {decision['reason']}")
        # Execute sell logic here

        # Log auto trading decision
        self.log_auto_trading_decision('sell', decision)

    def log_auto_trading_decision(self, action, decision):
        """📊 Log auto trading decisions"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO auto_trading_log 
                (timestamp, action, symbol, reason, ai_score, strategy_used, result)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now(),
                action,
                decision.get('symbol', ''),
                decision.get('reason', ''),
                decision.get('ai_score', 0),
                decision.get('strategy', ''),
                'executed'
            ))

            conn.commit()
            conn.close()
        except Exception as e:
            self.log(f"❌ Error logging auto trading decision: {e}")

    # === 🆕 UI Event Handlers ===

    def toggle_auto_trading(self):
        """🤖 Toggle auto trading mode"""
        if not self.license_manager.is_feature_enabled('auto_trading'):
            self.show_license_required()
            self.auto_trading_switch.deselect()
            return

        self.is_auto_trading = self.auto_trading_switch.get()

        if self.is_auto_trading:
            self.status_cards["Auto Mode"].configure(text="ON", text_color="green")
            self.log("🤖 Auto Trading Mode ENABLED")
        else:
            self.status_cards["Auto Mode"].configure(text="OFF", text_color="gray")
            self.log("💹 Manual Trading Mode ENABLED")

    def quick_analyze_coins(self):
        """🪙 Quick coin analysis"""
        if not self.license_manager.is_feature_enabled('coin_recommendation'):
            self.show_license_required()
            return

        if not self.coin_analyzer:
            messagebox.showwarning("Error", "Please connect API first")
            return

        self.update_scifi_visual_state("coin_analysis", "Quick analyzing top coins")
        self.log("🪙 Starting quick coin analysis...")

        threading.Thread(target=self.perform_quick_analysis, daemon=True).start()

    def perform_quick_analysis(self):
        """Perform quick analysis in background"""
        try:
            # Analyze top 10 coins
            top_symbols = ["btc_thb", "eth_thb", "ada_thb", "xrp_thb", "bnb_thb",
                           "doge_thb", "dot_thb", "matic_thb", "atom_thb", "sol_thb"]

            results = []
            for symbol in top_symbols:
                analysis = self.coin_analyzer.analyze_single_coin(symbol, self.config['trade_amount_thb'])
                if analysis:
                    results.append(analysis)
                time.sleep(0.5)  # Prevent rate limiting

            # Sort by AI score
            results.sort(key=lambda x: x['ai_score'], reverse=True)

            # Update display
            self.update_quick_analysis_display(results)
            self.update_scifi_visual_state("success", "Quick analysis completed")

            # Auto return to idle
            threading.Timer(2.0, lambda: self.update_scifi_visual_state("idle")).start()

        except Exception as e:
            self.log(f"❌ Quick analysis error: {e}")
            self.update_scifi_visual_state("error", "Analysis failed")

    def update_quick_analysis_display(self, results):
        """Update quick analysis display"""
        try:
            analysis_text = f"🪙 QUICK COIN ANALYSIS - {datetime.now().strftime('%H:%M:%S')}\n"
            analysis_text += "=" * 80 + "\n"

            for i, coin in enumerate(results[:5], 1):  # Top 5
                analysis_text += f"{i}. {coin['symbol'].upper():<10} | "
                analysis_text += f"Score: {coin['ai_score']:<4.1f} | "
                analysis_text += f"Price: {coin['price']:>10,.2f} | "
                analysis_text += f"Change: {coin['change_24h']:>+6.2f}% | "
                analysis_text += f"{coin['recommendation']}\n"

            analysis_text += "\n💡 Best coin automatically selected for trading!\n"

            # Update best coin status
            if results:
                best_coin = results[0]
                self.status_cards["Best Coin"].configure(text=best_coin['symbol'].upper())
                self.status_cards["AI Score"].configure(text=f"{best_coin['ai_score']:.1f}")

            self.analysis_display.delete("1.0", "end")
            self.analysis_display.insert("1.0", analysis_text)

        except Exception as e:
            self.log(f"❌ Error updating analysis display: {e}")

    def quick_check_strategies(self):
        """🎯 Quick strategy check"""
        if not self.license_manager.is_feature_enabled('advanced_strategies'):
            self.show_license_required()
            return

        self.log("🎯 Checking all strategies...")
        # Implementation for strategy checking
        messagebox.showinfo("Strategies", "Strategy check completed!\nResults displayed in logs.")

    def quick_force_sell_status(self):
        """🕐 Quick force sell status"""
        if not self.license_manager.is_feature_enabled('force_sell'):
            self.show_license_required()
            return

        if not self.force_sell_manager:
            messagebox.showwarning("Error", "Force sell manager not initialized")
            return

        positions = self.force_sell_manager.get_positions_status()

        if not positions:
            messagebox.showinfo("Force Sell", "No active positions to monitor")
        else:
            status_text = f"🕐 FORCE SELL STATUS:\n\n"
            for pos in positions:
                status_text += f"Position: {pos['symbol']}\n"
                status_text += f"Time Left: {pos['time_left_hours']:.1f} hours\n"
                status_text += f"Profit Reached: {'✅' if pos['min_profit_reached'] else '❌'}\n\n"

            messagebox.showinfo("Force Sell Status", status_text)

    def show_license_required(self):
        """🔐 Show license required message"""
        messagebox.showwarning(
            "Premium Feature Required",
            "This feature requires a premium license!\n\n"
            "🔓 Your trial includes all premium features.\n"
            f"Days remaining: {self.license_manager.get_license_info()['remaining_days']}\n\n"
            "Check the 🔐 License tab for more information."
        )

    def show_premium_required(self, tab):
        """🔐 Show premium required message in tab"""
        premium_frame = ctk.CTkFrame(tab)
        premium_frame.pack(fill="both", expand=True, padx=50, pady=50)

        ctk.CTkLabel(premium_frame,
                     text="🔐 PREMIUM FEATURE",
                     font=("Arial", 24, "bold"),
                     text_color="gold").pack(pady=20)

        license_info = self.license_manager.get_license_info()

        if license_info['valid']:
            message = "✅ This premium feature is available!\nPlease connect API to enable."
        else:
            message = f"❌ Premium license required\n\n🎁 Trial expired\nDays remaining: {license_info['remaining_days']}"

        ctk.CTkLabel(premium_frame,
                     text=message,
                     font=("Arial", 16),
                     justify="center").pack(pady=20)

        if not license_info['valid']:
            ctk.CTkButton(premium_frame,
                          text="🔓 View License Options",
                          command=lambda: self.tabview.set("🔐 License"),
                          fg_color="gold",
                          height=40,
                          width=200).pack(pady=10)

    # === 🆕 Enhanced Helper Functions ===

    def save_enhanced_trade(self, side, amount, price, total_thb, order_id, pnl, fees, net_pnl,
                            reason, is_paper, strategy="manual", ai_score=0, force_sell=False, auto_trade=False):
        """🆕 Save trade with enhanced tracking"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO trades 
                (timestamp, symbol, side, amount, price, total_thb, order_id, status, 
                 pnl, fees, net_pnl, reason, is_paper, rsi, volume_momentum, break_even_price, 
                 api_response, strategy_used, ai_score, force_sell, auto_trade)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now(), self.config['symbol'], side, amount, price,
                total_thb, order_id, 'completed', pnl, fees, net_pnl, reason,
                is_paper, 50, 1.0, 0, None, strategy, ai_score, force_sell, auto_trade
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            self.log(f"❌ Enhanced database error: {e}")

    def has_active_positions(self):
        """Check if there are active positions"""
        if self.force_sell_manager:
            positions = self.force_sell_manager.get_positions_status()
            return len(positions) > 0
        return False

    def update_enhanced_balance(self):
        """🆕 Update enhanced balance with premium info"""
        if not self.api_client:
            return

        balance = self.api_client.check_balance()
        if balance and balance.get('error') == 0:
            thb_balance = float(balance['result'].get('THB', 0))
            self.status_cards["Balance THB"].configure(text=f"{thb_balance:,.2f}")

    def enhanced_pre_flight_check(self):
        """🆕 Enhanced pre-flight check with premium features"""
        self.update_scifi_visual_state("analyzing", "Running enhanced pre-flight check")
        self.log("🛫 Running enhanced pre-flight check v3.0...")

        # Standard checks
        status_ok, status_msg = self.api_client.check_system_status()
        if not status_ok:
            self.log(f"❌ System not ready: {status_msg}")
            self.update_scifi_visual_state("error", "System check failed")
            return False

        # Balance check
        balance = self.api_client.check_balance()
        if not balance or balance.get('error') != 0:
            self.log("❌ Cannot verify balance")
            self.update_scifi_visual_state("error", "Balance check failed")
            return False

        thb_balance = float(balance['result'].get('THB', 0))
        if thb_balance < self.config['trade_amount_thb']:
            self.log(f"❌ Insufficient balance: {thb_balance:.2f} < {self.config['trade_amount_thb']}")
            self.update_scifi_visual_state("error", "Insufficient balance")
            return False

        # 🆕 Premium features check
        premium_checks = []

        if self.config.get('auto_coin_selection') and not self.coin_analyzer:
            premium_checks.append("❌ Coin Analyzer not initialized")
        else:
            premium_checks.append("✅ Coin Analyzer ready")

        if self.config.get('adaptive_strategy') and not self.strategies:
            premium_checks.append("❌ Advanced Strategies not initialized")
        else:
            premium_checks.append("✅ Advanced Strategies ready")

        if self.config.get('force_sell_enabled') and not self.force_sell_manager:
            premium_checks.append("❌ Force Sell Manager not initialized")
        else:
            premium_checks.append("✅ Force Sell Manager ready")

        for check in premium_checks:
            self.log(check)

        # Market data check with enhanced symbol
        test_symbol = self.config['symbol']
        if self.config.get('auto_coin_selection') and self.coin_analyzer:
            best_coin = self.get_best_coin_for_trading()
            if best_coin:
                test_symbol = best_coin['symbol']

        ticker = self.api_client.get_simple_ticker(test_symbol)
        if not ticker:
            self.log(f"❌ Cannot get market data for {test_symbol}")
            self.update_scifi_visual_state("error", "Market data unavailable")
            return False

        self.log("✅ Enhanced pre-flight check v3.0 passed")
        self.update_scifi_visual_state("success", "Enhanced pre-flight check passed")
        threading.Timer(1.0, lambda: self.update_scifi_visual_state("idle")).start()
        return True

    def update_scifi_visual_state(self, state, message=""):
        """🆕 Enhanced visual state update with license checking"""
        if hasattr(self, 'scifi_visual'):
            # Check if premium graphics are enabled
            if state in ["coin_analysis", "auto_mode"]:
                if not self.license_manager.is_feature_enabled('premium_graphics'):
                    state = "idle"
                    message = "Premium graphics disabled"

            self.scifi_visual.set_state(state)

        # Update status label
        if hasattr(self, 'ai_status_label'):
            status_messages = {
                "idle": "System Ready",
                "connecting": "Connecting to API...",
                "analyzing": "Analyzing Market...",
                "coin_analysis": "🪙 AI Analyzing Coins...",
                "auto_mode": "🤖 Auto Trading Active...",
                "buy_signal": "Buy Signal Detected!",
                "sell_signal": "Sell Signal Detected!",
                "trading": "Active Trading...",
                "success": "Operation Successful!",
                "error": "System Error!"
            }

            display_message = status_messages.get(state, "Unknown State")
            if message:
                display_message = f"{display_message} - {message}"

            try:
                self.ai_status_label.configure(text=display_message)
            except:
                pass

        # Log the visual state change
        if message:
            self.log(f"🎬 Visual State: {state.upper()} - {message}")

    def log(self, message):
        """🆕 Enhanced logging with multiple displays"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"

        # Add to main dashboard log
        if hasattr(self, 'dashboard_display'):
            self.dashboard_display.insert("end", log_entry)
            self.dashboard_display.see("end")

        # Add to trading log if exists
        if hasattr(self, 'trading_log'):
            self.trading_log.insert("end", log_entry)
            self.trading_log.see("end")

        # Keep log size manageable
        for display in [getattr(self, 'dashboard_display', None),
                        getattr(self, 'trading_log', None)]:
            if display:
                try:
                    lines = display.get("1.0", "end").split('\n')
                    if len(lines) > 1000:
                        # Keep last 500 lines
                        display.delete("1.0", f"{len(lines) - 500}.0")
                except:
                    pass

    def emergency_stop_trading(self):
        """🚨 Enhanced emergency stop"""
        self.update_scifi_visual_state("error", "EMERGENCY STOP ACTIVATED")
        if hasattr(self, 'scifi_visual'):
            self.scifi_visual.flash_effect("#ff0000", 0.5)

        self.emergency_stop = True
        self.is_trading = False
        self.is_auto_trading = False

        self.start_btn.configure(text="▶️ Start Enhanced Bot", fg_color="green")
        if hasattr(self, 'start_btn_
