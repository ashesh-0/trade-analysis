from cdefs.defines import TradeType_t, OrderType_t


class MeanReversion:
    '''
    If price is going up for two consequitive minutes then it believes that the price will go down.
    Similar mean reversion for prices going down.
    '''

    def __init__(self,
                 watch,
                 secid,
                 trade_type,
                 order_type,
                 int_order_to_place,
                 start_midnight_seconds,
                 order_manager,
                 execution_window=2600):
        self.secid = secid
        self.trade_type = trade_type
        self.order_type = order_type
        self.size = int_order_to_place
        self.order_manager = order_manager
        self.watch = watch
        self.start_midnight_seconds = start_midnight_seconds
        self.execution_window = execution_window
        self.hist_minute_bars = []
        self.arrival_price = -1
        self.execution_window = 7200
        self.order_sent = False

        # we keep last 10 minute bars
        self.hist_minute_bar_size = 2

    def _set_arrival_price(self):
        '''
        We compare the performance of execution algorithm against the market price when execution algorithm starts.
        '''
        op = self.hist_minute_bars[-1].open
        self.arrival_price = (op.bid_price + op.ask_price) / 2

    def on_market_update(self, secid, market_info):
        '''
        Gets called on every minute bar
        '''
        assert (secid == self.secid)
        self.hist_minute_bars.append(market_info.get_latest_one_minute_bar())

        # maintain the latest 2 one minute bars.
        while (len(self.hist_minute_bars) > self.hist_minute_bar_size):
            del self.hist_minute_bars[0]

        if self.watch.secs_since_midnight < self.start_midnight_seconds or self.order_sent:
            return

        if self.arrival_price == -1:
            self._set_arrival_price()

        self.trading_logic()

    def signal(self):
        '''
        If last 2 minute bars were positive, we assume that prices will revert back. We place Sell orders at that point. Similarly for buy.
        '''
        if len(self.hist_minute_bars) < self.hist_minute_bar_size:
            return False

        signal = self.minute_bar_movement(self.hist_minute_bars[-1]) + self.minute_bar_movement(self.hist_minute_bars[
            -2])
        if self.trade_type == TradeType_t.Buy and signal == -2:
            return True
        elif self.trade_type == TradeType_t.Sell and signal == 2:
            return True
        return False

    def timelimitexeeded(self):
        '''
        We implicitly limit the max loss by limiting the amount of time given to execution algorithm.
        '''
        return self.watch.secs_since_midnight >= self.start_midnight_seconds + self.execution_window

    def trading_logic(self):
        '''
        We wait for the correct signal. On getting the signal we place market orders.
        '''

        if self.signal() or self.timelimitexeeded():
            self.order_manager.send_order(self.secid, self.trade_type, self.order_type, self.size)
            self.order_sent = True

    def minute_bar_movement(self, minute_bar):
        '''
        It returns whether the price has increased or decreased. It uses market weighted price as a measure of price.
        '''
        op = minute_bar.open
        cl = minute_bar.close
        open_price = (op.bid_price * op.ask_size + op.ask_price * op.bid_size) / (op.bid_size + op.ask_size)
        close_price = (cl.bid_price * cl.ask_size + cl.ask_price * cl.bid_size) / (cl.bid_size + cl.ask_size)
        diff = close_price - open_price

        if diff > 0.005:
            signal = 1
        elif diff < -0.005:
            signal = -1
        else:
            signal = 0

        return signal
