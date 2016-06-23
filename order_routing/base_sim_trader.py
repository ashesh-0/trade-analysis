from order_routing.base_trader import BaseTrader

class BaseSimTrader( BaseTrader ):
    def __init__( self, backtester, uid ):
        BaseTrader.__init__( self, uid )
        self.backtester = backtester

    def send_order( self, order ):
        self.backtester.send_order_exch( self.uid, order )

    def cancel_order( self, order ):
        self.backtester.cancel_order_exch( self.uid, order )
