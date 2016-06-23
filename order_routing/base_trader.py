class BaseTrader( object ):
    def __init__( self, uid ):
        self.uid = uid

    def send_order( self, order ):
        pass

    def cancel_order( self, order ):
        pass
