import logging
from abc import ABCMeta, abstractmethod

import datetime
import time
from cdefs.defines import TradeType_t
from order_routing.base_order import Order
from order_routing.backtester import BackTester, OrderConfirmedListener, OrderExecutedListener, OrderCancelledListener, OrderRejectedListener, OrderCancelRejectedListener
from order_routing.base_sim_trader import BaseSimTrader


## @class PositionUpdateListener
#  @brief Abstract class for listeners to all the position updates for a user
#
class PositionUpdateListener:
    __metaclass__ = ABCMeta

    @abstractmethod
    def on_position_update(self, secid, size, buysell, fill_price):
        pass


class BaseOrderManager(OrderConfirmedListener, OrderExecutedListener, OrderCancelledListener, OrderRejectedListener,
                       OrderCancelRejectedListener):
    def __init__(self, watch, uid):
        self.watch = watch
        self.orderid = 0
        self.uid = uid
        self.base_trader = self.instantiate_base_trader(uid)
        self.unconfirmed_orders = [[] for i in range(256)]
        self.confirmed_orders = [[] for i in range(256)]
        self.position_update_listener_list = []
        self.execution_completion_listener_list = []

        backtester = BackTester.GetUniqueInstance(watch)
        backtester.add_order_confirmed_listener(self.uid, self)
        backtester.add_order_executed_listener(self.uid, self)
        backtester.add_order_cancelled_listener(self.uid, self)
        backtester.add_order_rejected_listener(self.uid, self)
        backtester.add_order_cancel_rejected_listener(self.uid, self)

    def instantiate_base_trader(self, uid):
        return BaseSimTrader(BackTester.GetUniqueInstance(self.watch), uid)

    def send_order(self, secid, buysell, ordertype, size, price=0.0):
        new_order = Order()
        new_order.secid = secid
        new_order.buysell = buysell
        new_order.ordertype = ordertype
        new_order.price = price
        new_order.size_requested = size
        new_order.size_remaining = size
        new_order.size_executed = 0
        new_order.orderid = self.orderid
        self.orderid += 1
        self.unconfirmed_orders[secid].append(new_order)
        self.base_trader.send_order(new_order)

    def cancel_order(self, order):
        self.base_trader.cancel_order(order)

    def sum_pending_orders(self, secid):
        size = 0
        unconfirmed_orders = self.unconfirmed_orders[secid]
        for order in unconfirmed_orders:
            if order.buysell == TradeType_t.Buy:
                size += order.size_remaining
            elif order.buysell == TradeType_t.Sell:
                size -= order.size_remaining
        confirmed_orders = self.confirmed_orders[secid]
        for order in confirmed_orders:
            if order.buysell == TradeType_t.Buy:
                size += order.size_remaining
            elif order.buysell == TradeType_t.Sell:
                size -= order.size_remaining
        return size

    def on_order_confirmed(self, orderid, secid):
        unconfirmed_indexes = [i for i, order in enumerate(self.unconfirmed_orders[secid]) if order.orderid == orderid]
        if len(unconfirmed_indexes) == 1:
            unconfirmed_index = unconfirmed_indexes[0]
            order = self.unconfirmed_orders[secid][unconfirmed_index]
            del self.unconfirmed_orders[secid][unconfirmed_index]
            self.confirmed_orders[secid].append(order)
        else:
            pass
            # Something fishy going on!

    def on_order_executed(self, orderid, secid, size, price):
        confirmed_indexes = [i for i, order in enumerate(self.confirmed_orders[secid]) if order.orderid == orderid]
        if len(confirmed_indexes) == 1:
            confirmed_index = confirmed_indexes[0]
            order = self.confirmed_orders[secid][confirmed_index]
            assert size <= order.size_remaining
            buysell = order.buysell
            order.size_remaining -= size
            order.size_executed += size
            if order.size_remaining == 0:
                del self.confirmed_orders[secid][confirmed_index]
                self.notify_execution_completion_listener(secid, size, buysell, price)
            self.notify_position_update_listeners(secid, size, buysell, price)
        else:
            # Maybe we received exec notification for an unconfirmed order
            unconfirmed_indexes = [i for i, order in enumerate(self.unconfirmed_orders[secid])
                                   if order.orderid == orderid]
            if len(unconfirmed_indexes) == 1:
                unconfirmed_index = unconfirmed_indexes[0]
                order = self.unconfirmed_orders[secid][unconfirmed_index]
                assert size <= order.size_remaining
                buysell = order.buysell
                order.size_remaining -= size
                order.size_executed += size
                if order.size_remaining == 0:
                    self.unconfirmed_order[secid][unconfirmed_index]
                    self.notify_execution_completion_listener(secid, size, buysell, price)
                else:
                    self.unconfirmed_order[secid][unconfirmed_index]
                    self.confirmed_orders[secid].append(order)
                self.notify_position_update_listeners(secid, size, buysell, price)
            else:
                pass
                # Something fishy going on!

    def on_order_cancelled(self, orderid, secid):
        unconfirmed_indexes = [i for i, order in enumerate(self.unconfirmed_orders[secid]) if order.orderid == orderid]
        if len(unconfirmed_indexes) == 1:
            unconfirmed_index = unconfirmed_indexes[0]
            del self.unconfirmed_orders[secid][unconfirmed_index]
        else:
            confirmed_indexes = [i for i, order in enumerate(self.confirmed_orders[secid]) if order.orderid == orderid]
            if len(confirmed_indexes) == 1:
                confirmed_index = confirmed_indexes[0]
                del self.confirmed_orders[secid][confirmed_index]
            else:
                pass
                # Something fishy going on!

    def on_order_rejected(self, orderid, secid):
        unconfirmed_indexes = [i for i, order in enumerate(self.unconfirmed_orders[secid]) if order.orderid == orderid]
        if len(unconfirmed_indexes) == 1:
            unconfirmed_index = unconfirmed_indexes[0]
            del self.unconfirmed_orders[secid][unconfirmed_index]
        else:
            confirmed_indexes = [i for i, order in enumerate(self.confirmed_orders[secid]) if order.orderid == orderid]
            if len(confirmed_indexes) == 1:
                confirmed_index = confirmed_indexes[0]
                del self.confirmed_orders[secid][confirmed_index]
            else:
                pass
                # Something fishy going on!

    def on_order_cancel_rejected(self, orderid, secid):
        pass

    def add_position_update_listener(self, listener):
        self.position_update_listener_list.append(listener)

    def add_execution_completion_listener(self, listener):
        self.execution_completion_listener_list.append(listener)

    def notify_execution_completion_listener(self, secid, size, buysell, price):
        for listener in self.execution_completion_listener_list:
            listener.on_executed(secid, size, buysell, price)

    def notify_position_update_listeners(self, secid, size, buysell, price):
        for listener in self.position_update_listener_list:
            listener.on_position_update(secid, size, buysell, price)
