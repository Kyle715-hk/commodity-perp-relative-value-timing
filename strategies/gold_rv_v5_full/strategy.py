import json
import os
import numpy as np
from clawstock_strategy import BaseStrategy, StrategyContext, BarBatch, TargetPosition

class Strategy(BaseStrategy):
    def initialize(self, context: StrategyContext) -> None:
        # Resolve path to strategy.json within the same toolkit directory
        base_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(base_dir, "strategy.json")

        # Load parameters from strategy.json if present, or fallback to defaults
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                config = json.load(f)
            params = config.get("parameters", {})
            costs = config.get("costs", {})

            self.paxg_sym = config["universe"][0] if len(config.get("universe", [])) > 0 else "gateio:perp:PAXG_USDT"
            self.xaut_sym = config["universe"][1] if len(config.get("universe", [])) > 1 else "gateio:perp:XAUT_USDT"
            self.z_entry = params.get("z_entry_threshold", 3.0)
            self.z_exit = params.get("z_exit_threshold", 0.5)
            self.lookback = params.get("lookback_window", 2880)
        else:
            self.paxg_sym = "gateio:perp:PAXG_USDT"
            self.xaut_sym = "gateio:perp:XAUT_USDT"
            self.z_entry = 3.0
            self.z_exit = 0.5
            self.lookback = 2880

        self.paxg_prices = []
        self.xaut_prices = []
        self.current_bar = 0
        self.pos = 0  # State: -1 = Short Spread, +1 = Long Spread, 0 = Flat
        self.decision_every = 1440  # Daily evaluation interval (1440 1-min bars)

    def _targets(self):
        if self.pos == -1:
            wp, wx = -0.5, 0.5
        elif self.pos == 1:
            wp, wx = 0.5, -0.5
        else:
            wp, wx = 0.0, 0.0
        return [
            TargetPosition(instrument=self.paxg_sym, target_weight=wp),
            TargetPosition(instrument=self.xaut_sym, target_weight=wx),
        ]

    def on_bar(self, context: StrategyContext, bars: BarBatch):
        self.current_bar += 1

        if self.paxg_sym in bars and self.xaut_sym in bars:
            self.paxg_prices.append(float(bars[self.paxg_sym].close))
            self.xaut_prices.append(float(bars[self.xaut_sym].close))

        if len(self.paxg_prices) > 8000:
            self.paxg_prices = self.paxg_prices[-8000:]
            self.xaut_prices = self.xaut_prices[-8000:]

        # Evaluate signal once per daily decision interval
        if (self.current_bar % self.decision_every == 0) and len(self.paxg_prices) >= self.lookback:
            paxg_log = np.log(np.asarray(self.paxg_prices[-self.lookback:], dtype=float))
            xaut_log = np.log(np.asarray(self.xaut_prices[-self.lookback:], dtype=float))
            cov = np.cov(paxg_log, xaut_log)
            beta = cov[0, 1] / cov[1, 1] if cov[1, 1] != 0 else 1.0
            spread = paxg_log - beta * xaut_log
            mu = spread[-1440:].mean()
            sd = spread[-1440:].std()
            if sd > 1e-8:
                z = (spread[-1] - mu) / sd
                if self.pos == 0:
                    if z >= self.z_entry:
                        self.pos = -1
                    elif z <= -self.z_entry:
                        self.pos = 1
                else:
                    if abs(z) <= self.z_exit:
                        self.pos = 0

        # Continuously emit target weights to hold positions in the engine
        return self._targets()
