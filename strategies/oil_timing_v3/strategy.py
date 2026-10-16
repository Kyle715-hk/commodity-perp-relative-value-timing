import numpy as np
from clawstock_strategy import BaseStrategy, StrategyContext, BarBatch, TargetPosition

class Strategy(BaseStrategy):
    def initialize(self, context: StrategyContext) -> None:
        self.cl_prices = []
        self.cl_fundings = []
        self.last_rebalance_bar = -10**9
        self.current_bar = 0
        self.current_w = 0.0
        self.cl_sym = "gateio:perp:CL_USDT"

        self.rebalance_cooldown = 240   # 4-hour rebalance cooldown
        self.max_abs_w = 0.15          # Position size cap for drawdown control
        self.entry_threshold = 1.5     # Required composite signal strength
        self.min_change = 0.15

    def on_bar(self, context: StrategyContext, bars: BarBatch):
        self.current_bar += 1

        if self.cl_sym in bars:
            self.cl_prices.append(float(bars[self.cl_sym].close))
            fr = getattr(bars[self.cl_sym], "funding_rate", 0.0)
            self.cl_fundings.append(0.0 if fr is None else float(fr))

        if len(self.cl_prices) > 5000:
            self.cl_prices = self.cl_prices[-5000:]
            self.cl_fundings = self.cl_fundings[-5000:]

        if self.current_bar - self.last_rebalance_bar < self.rebalance_cooldown:
            return []

        if len(self.cl_prices) < 2880:
            return []

        cl = np.asarray(self.cl_prices, dtype=float)
        ema_fast = cl[-720:].mean()
        ema_slow = cl[-2880:].mean()
        vol = cl[-1440:].std()
        i_trend = (ema_fast - ema_slow) / vol if vol > 1e-6 else 0.0

        avg_f = np.mean(self.cl_fundings[-1440:]) if len(self.cl_fundings) >= 1440 else 0.0
        i_fund = -np.sign(avg_f) * min(abs(avg_f) / 0.0001, 1.0)

        composite = 0.85 * i_trend + 0.15 * i_fund

        if composite >= self.entry_threshold:
            raw = self.max_abs_w
        elif composite <= -self.entry_threshold:
            raw = -self.max_abs_w
        else:
            raw = 0.0

        if abs(raw - self.current_w) < self.min_change:
            return []

        self.current_w = raw
        self.last_rebalance_bar = self.current_bar
        return [TargetPosition(instrument=self.cl_sym, target_weight=self.current_w)]
