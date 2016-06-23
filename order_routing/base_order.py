from cdefs.defines import TradeType_t, OrderType_t


class Order(object):
    def __init__(self):
        self.secid = 0  # Security Id
        self.orderid = 0  # Order Id
        self.uid = 0  # User Id ( Used in backtester )
        self.buysell = TradeType_t.Invalid  # To represent buy or sell, TODO: Can keep this as a boolean
        self.ordertype = OrderType_t.Invalid  # To represent the type of order, can be limit, market, FOK etc.
        self.price = 0  # price at which we are placing this order, the price at which this got executed can be different
        self.int_price = 0
        self.size_remaining = 0  # Size of the order still remaining
        self.size_requested = 0  # Initial size of the order
        self.size_executed = 0  # Size of the order already executed

    def execute(self, size):
        self.size_remaining -= size
        self.size_executed += size
