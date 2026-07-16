from typing import List, Dict, Any

class Order:
    def __init__(self, agent_id: str, resource_type: str, quantity: float, price: float, order_type: str):
        self.agent_id = agent_id
        self.resource_type = resource_type
        self.quantity = quantity
        self.price = price
        self.order_type = order_type # "BID" (buy) or "ASK" (sell)

class MarketBook:
    """Orderbook matcher with dynamic price discovery mechanisms"""
    def __init__(self, market_id: str, name: str):
        self.market_id = market_id
        self.name = name
        self.bids: Dict[str, List[Order]] = {"food": [], "wood": [], "stone": [], "iron": []}
        self.asks: Dict[str, List[Order]] = {"food": [], "wood": [], "stone": [], "iron": []}
        
        # Historic base prices
        self.prices: Dict[str, float] = {"food": 1.0, "wood": 2.0, "stone": 3.0, "iron": 5.0}

    def submit_order(self, order: Order):
        res = order.resource_type
        if res not in self.prices:
            return
            
        if order.order_type == "BID":
            self.bids[res].append(order)
            self.bids[res].sort(key=lambda o: o.price, reverse=True) # Highest bid first
        else:
            self.asks[res].append(order)
            self.asks[res].sort(key=lambda o: o.price) # Lowest ask first
            
        self.match_orders(res)

    def match_orders(self, resource: str):
        """Standard double-auction order matching engine"""
        bids = self.bids[resource]
        asks = self.asks[resource]
        
        trades_volume = 0
        total_trade_val = 0.0

        while bids and asks:
            best_bid = bids[0]
            best_ask = asks[0]
            
            if best_bid.price >= best_ask.price:
                # Trade can happen. Price is the midpoint
                trade_price = (best_bid.price + best_ask.price) / 2.0
                qty = min(best_bid.quantity, best_ask.quantity)
                
                # Execute transaction updates
                best_bid.quantity -= qty
                best_ask.quantity -= qty
                
                trades_volume += qty
                total_trade_val += qty * trade_price
                
                # Cleanup zero quantities
                if best_bid.quantity <= 0:
                    bids.pop(0)
                if best_ask.quantity <= 0:
                    asks.pop(0)
            else:
                break # No match possible

        # Discover new base price based on supply & demand shifts
        if trades_volume > 0:
            avg_price = total_trade_val / trades_volume
            # Update price with a learning coefficient alpha = 0.1
            self.prices[resource] = self.prices[resource] * 0.9 + avg_price * 0.1
        else:
            # Adjust price based on imbalance
            num_bids = sum(b.quantity for b in bids)
            num_asks = sum(a.quantity for a in asks)
            if num_bids > num_asks:
                self.prices[resource] *= 1.05 # Inflation: high demand
            elif num_asks > num_bids:
                self.prices[resource] *= 0.95 # Deflation: high supply
