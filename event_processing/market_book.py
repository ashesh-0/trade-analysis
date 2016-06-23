from cdefs.defines import MarketEvent_t, TradingStatus_t
from cdefs.watch import USING_EST_CUSTOM_TRADING_DATE
from cdefs.watch_listener import DateChangeListener
from utils.datetime_convertor import get_secs_from_midnight, get_custom_est_secs_from_midnight

import pytz


class TradeTime(object):
    def __init__(self, hhmm, tz):
        self.hhmm = hhmm
        self.tz = tz


##
# Tracks the latest snapshot of the market view for a security
# One instance of Market Book will correspond to one security
#
class MarketBook(DateChangeListener):

    unique_instances = [None] * 256

    def __init__(self, watch, secid):
        self.watch = watch
        self.secid = secid
        self.latest_price = None
        self.one_minute_bar = None  # The latest one minute bar view of the security
        self.market_event_listener_list = []  # List of listeners of the updates of this market book

        # Track the trading times
        self.watch.add_date_change_watch_listener(
            self)  # Listen to date change events because we need to refresh the book and trading times
        self.trade_open_time = TradeTime(930, pytz.timezone("EST"))
        self.trade_close_time = TradeTime(1600, pytz.timezone("EST"))
        self.trade_open_time_midsec = None  # The seconds since midnight when this security starts trading
        self.trade_close_time_midsec = None  # The seconds since midnight when this security stops trading

        # Tracks the type of the latest event received by the market book
        self.latest_event_type = MarketEvent_t.Invalid
        self.trading_status = TradingStatus_t.Invalid

        self.is_exchange_symbol_mapping_change_notification_received = False

    ## Static function to get a reference to the unique instance of the market book of a given security
    @staticmethod
    def GetUniqueInstance(watch, secid):
        if MarketBook.unique_instances[secid] is None:
            MarketBook.unique_instances[secid] = MarketBook(watch, secid)
        return MarketBook.unique_instances[secid]

    ## Static function to get a reference to the unique instance of the market book of all the securities
    @staticmethod
    def GetUniqueInstances(watch):
        return MarketBook.unique_instances

    ## Called at the end of sim.Deletes the unique instance
    @staticmethod
    def RemoveUniqueInstances():
        MarketBook.unique_instances = [None] * 256

    ## Function to add a new market event listener
    def add_market_event_listener(self, new_listener):
        self.market_event_listener_list.append(new_listener)

    def remove_market_event_listener(self, listener):
        self.market_event_listener_list.remove(listener)

        ## Provides information about the type of the latest market event this book has recieved
    def latest_market_event_type(self):
        return self.latest_event_type

    ## Provides information about the type of the latest market event this book has recieved
    def trading_status(self):
        return self.trading_status

    ## Getter to access the latest one minute bar of a security
    def get_latest_one_minute_bar(self):
        return self.one_minute_bar

    ## Whenever a new one minute bar is generated, this function should be called to update the market book with the latest one minute bar
    def on_new_minute_bar(self, new_bar, minute_bar_period):
        # if not self.is_minute_bar_valid( new_bar ):
        #     return

        watch_midsec = self.watch.secs_since_midnight
        # Update the tradng status of the security */
        if (watch_midsec >= self.trade_open_time_midsec) and (watch_midsec <= self.trade_close_time_midsec):
            self.trading_status = TradingStatus_t.Trading
        elif watch_midsec < self.trade_open_time_midsec:
            self.trading_status = TradingStatus_t.PreOpen
        elif watch_midsec > self.trade_close_time_midsec:
            self.trading_status = TradingStatus_t.PostClose

        self.one_minute_bar = new_bar
        self.latest_event_type = MarketEvent_t.OneMinuteBar

        self.latest_price = (new_bar.close.bid_price + new_bar.close.ask_price) / 2

        for listener in self.market_event_listener_list:
            listener.on_market_update(self.secid, self)

    ## Called by watch whenever the date changes, here the market book will invalidate all the previous data
    def on_date_change(self, new_date):
        self.one_minute_bar = None

        if USING_EST_CUSTOM_TRADING_DATE:
            self.trade_open_time_midsec = get_custom_est_secs_from_midnight(
                self.watch.current_date, self.trade_open_time.hhmm, self.trade_open_time.tz)
            self.trade_close_time_midsec = get_custom_est_secs_from_midnight(
                self.watch.current_date, self.trade_close_time.hhmm, self.trade_close_time.tz)
        else:
            self.trade_open_time_midsec = get_secs_from_midnight(self.watch.current_date, self.trade_open_time.hhmm,
                                                                 self.trade_open_time.tz)
            self.trade_close_time_midsec = get_secs_from_midnight(self.watch.current_date, self.trade_close_time.hhmm,
                                                                  self.trade_close_time.tz)

        self.trading_status = None
        self.is_exchange_symbol_mapping_change_notification_received = False
