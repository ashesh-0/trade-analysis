'''
This file mananges the executions. We add constraint that there should be one active order per secid.
All other orders for that secid will get executed after the order is completed.
'''

from algo.mean_reversion import MeanReversion
from algo.momentum import Momentum
from cdefs.defines import ExecAlgoType_t, TradeType_t
from cdefs.security_name_indexer import SecurityNameIndexer


class ExecutionManager():
    def __init__(self, watch, market_books, order_manager, algo_type=ExecAlgoType_t.Direct):
        self.market_books = market_books
        self.order_manager = order_manager
        self.orders = []
        self.watch = watch
        self.active_execution_requests = []
        self.algo_type = algo_type
        self.order_manager.add_execution_completion_listener(self)

    def activate(self, secid):
        '''
        Starts the execution algorithms for the exeuction request which has security id as  secid
        '''
        index = -1
        for index, order in enumerate(self.orders):
            if order[0] == secid:
                if self.algo_type == ExecAlgoType_t.Direct:
                    self.order_manager.send_order(order[0], order[1], order[2], order[3])
                    break
                elif self.algo_type == ExecAlgoType_t.MeanRev:
                    a = MeanReversion(self.watch, order[0], order[1], order[2], order[3], order[4], self.order_manager)
                elif self.algo_type == ExecAlgoType_t.Momentum:
                    a = Momentum(self.watch, order[0], order[1], order[2], order[3], order[4], self.order_manager)
                else:
                    raise ValueError("Unknown algorithm: {}".format(self.algo_type))
                self.active_execution_requests.append(a)
                self.market_books[secid].add_market_event_listener(a)
                break

        del self.orders[index]

    def activated(self, secid):
        '''
        Check if an execution request for security id secid is under execution
        '''
        for active in self.active_execution_requests:
            if active.secid == secid:
                return True
        return False

    def execute_all(self):
        for order in self.orders:
            if not self.activated(order[0]):
                self.activate(order[0])

    def execute(self, secid, trade_type, order_type, int_order_to_place, secs_from_midnight):
        self.orders.append((secid, trade_type, order_type, int_order_to_place, secs_from_midnight))
        self.execute_all()

    def _print_stats(self, avg_price, size, algo_instance):
        '''
        Prints the performance of execution
        '''
        sni = SecurityNameIndexer.GetUniqueInstance()
        hh = int(algo_instance.start_midnight_seconds / 3600)
        mm = int((algo_instance.start_midnight_seconds - hh * 3600) / 60)
        ss = int((algo_instance.start_midnight_seconds - hh * 3600) / 60)

        hh = str(hh) if hh > 9 else '0{}'.format(hh)
        mm = str(mm) if mm > 9 else '0{}'.format(mm)
        ss = str(ss) if ss > 9 else '0{}'.format(ss)

        buysell = 'Buy' if algo_instance.trade_type == TradeType_t.Buy else 'Sell'
        savings = avg_price - algo_instance.arrival_price
        duration = self.watch.secs_since_midnight - algo_instance.start_midnight_seconds
        if buysell == 'Buy':
            savings *= -1
        print('{}:{}:{}:UTC Order:{} {} {}'.format(hh, mm, ss, sni.get_shortcode_from_id(algo_instance.secid),
                                                   algo_instance.size, buysell))
        print('Performance: Arrival_Price:{} Executed_Price:{} Executed_Size:{} Savings:{} Duration:{}'.format(
            algo_instance.arrival_price, avg_price, size, savings, duration))

    def on_executed(self, secid, size, buysell, price):
        '''
        Base order manager calls this when order is completely executed.
        '''

        index = -1
        exec_request_found = False
        for index, req in enumerate(self.active_execution_requests):
            if req.secid == secid:
                exec_request_found = True
                self._print_stats(price, size, req)
                self.market_books[secid].remove_market_event_listener(req)
                break
        if exec_request_found:
            del self.active_execution_requests[index]
        else:
            print('Performance:Executed_Price:{} Executed_Size:{}'.format(price, size))
        self.execute_all()
