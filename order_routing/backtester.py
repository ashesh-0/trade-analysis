import copy
import logging
from abc import ABCMeta, abstractmethod

from cdefs.defines import TradingStatus_t, MarketEvent_t
from cdefs.watch_listener import DateChangeListener
from cdefs.defines import OrderType_t
from order_routing.base_order import Order
from event_processing.market_event_listener import MarketEventListener


## @class OrderConfirmedListener
#  @brief Abstract class for listeners to all the confirmed orders for a user
#
class OrderConfirmedListener:
    __metaclass__ = ABCMeta

    @abstractmethod
    def on_order_confirmed(self, secid, orderid):
        pass


## @class OrderExecutedListener
#  @brief Abstract class for listeners to all the executed orders for a user
#
class OrderExecutedListener:
    __metaclass__ = ABCMeta

    @abstractmethod
    def on_order_executed(self, secid, orderid, size, price):
        pass


## @class OrderCancelledListener
#  @brief Abstract class for listeners to all the cancelled orders for a user
#
class OrderCancelledListener:
    __metaclass__ = ABCMeta

    @abstractmethod
    def on_order_cancelled(self, secid, orderid):
        pass


## @class OrderRejectedListener
#  @brief Abstract class for listeners to all the rejected orders for a user
#
class OrderRejectedListener:
    __metaclass__ = ABCMeta

    @abstractmethod
    def on_order_rejected(self, secid, orderid):
        pass


## @class OrderCancelRejectedListener
#  @brief Abstract class for listeners to all the cancel rejected orders for a user
#
class OrderCancelRejectedListener:
    __metaclass__ = ABCMeta

    @abstractmethod
    def on_order_cancel_rejected(self, secid, orderid):
        pass


class BackTester(MarketEventListener, DateChangeListener):

    unique_instance = None

    def __init__(self, watch):
        self.watch = watch

        # An array indexed by sec id, each entry of the array is a vector of orders for that security
        # This is because on a particular market update,
        # we will update all orders of a particular secid.
        self.secid_to_orders = [[] for x in range(256)]

        # Listeners vector
        self.order_confirmed_listener = {}
        self.order_executed_listener = {}
        self.order_cancelled_listener = {}
        self.order_rejected_listener = {}
        self.order_cancel_rejected_listener = {}

    @staticmethod
    def GetUniqueInstance(watch):
        if BackTester.unique_instance is None:
            BackTester.unique_instance = BackTester(watch)
        return BackTester.unique_instance

    @staticmethod
    def RemoveUniqueInstance():
        BackTester.unique_instance = None

    ## @brief On date change, backtester will send rejection for all the pending orders */
    def on_date_change(self, new_date):
        return
        for secid in range(256):
            this_secid_orders = self.secid_to_orders[secid]
            for order in this_secid_orders:
                self.broadcast_rejection(order.uid, order.secid, order.orderid)
            self.secid_to_orders[secid] = []

    def send_order_exch(self, uid, order):
        new_order = copy.copy(order)
        new_order.uid = uid
        self.secid_to_orders[new_order.secid].append(new_order)
        self.broadcast_confirmation(new_order.uid, new_order.secid, new_order.orderid)

    def cancel_order_exch(self, uid, order):
        orders = self.secid_to_orders[order.secid]
        found = False
        for i in range(len(orders)):
            if (orders[i].uid == uid) and (orders[i].orderid == order.orderid):
                # Found
                del orders[i]
                self.broadcast_cancellation(uid, order.secid, order.orderid)
                found = True
                break
        if not found:
            self.broadcast_cancel_rejection(uid, order.secid, order.orderid)

    def on_market_update(self, secid, market_info):
        trading_status = market_info.trading_status
        latest_price, latest_event_type = market_info.latest_price, market_info.latest_event_type
        if (TradingStatus_t.Trading != trading_status) or (MarketEvent_t.Invalid == latest_event_type):
            return

        orders = self.secid_to_orders[secid]
        unexecuted_orders = []
        for order in orders:
            if order.ordertype == OrderType_t.Market:
                order.execute(order.size_remaining)
                # For the time being, execute it at the best price available now.
                self.broadcast_execution(order.uid, order.secid, order.orderid, order.size_executed, latest_price)
            else:
                # Handle other cases later
                unexecuted_orders.append(order)
        self.secid_to_orders[secid] = unexecuted_orders

    def add_order_confirmed_listener(self, uid, listener):
        self.order_confirmed_listener.setdefault(uid, []).append(listener)

    def add_order_executed_listener(self, uid, listener):
        self.order_executed_listener.setdefault(uid, []).append(listener)

    def add_order_cancelled_listener(self, uid, listener):
        self.order_cancelled_listener.setdefault(uid, []).append(listener)

    def add_order_rejected_listener(self, uid, listener):
        self.order_rejected_listener.setdefault(uid, []).append(listener)

    def add_order_cancel_rejected_listener(self, uid, listener):
        self.order_cancel_rejected_listener.setdefault(uid, []).append(listener)

    # Broadcast functions
    def broadcast_confirmation(self, uid, secid, orderid):
        for listener in self.order_confirmed_listener[uid]:
            listener.on_order_confirmed(orderid, secid)

    def broadcast_execution(self, uid, secid, orderid, size, price):
        for listener in self.order_executed_listener[uid]:
            listener.on_order_executed(orderid, secid, size, price)

    def broadcast_cancellation(self, uid, secid, orderid):
        for listener in self.order_cancelled_listener[uid]:
            listener.on_order_cancelled(orderid, secid)

    def broadcast_rejection(self, uid, secid, orderid):
        for listener in self.order_rejected_listener[uid]:
            listener.on_order_rejected(orderid, secid)

    def broadcast_cancel_rejection(self, uid, secid, orderid):
        for listener in self.cancel_rejected_listener[uid]:
            listener.on_order_cancel_rejected(orderid, secid)
