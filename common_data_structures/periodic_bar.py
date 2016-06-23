INVALID_VALUE = -1

## @brief Captures an intraday best quote,i.e. the bid/ask prices/sizes
class Quote( object ):
    def __init__( self, bid_price, bid_size, ask_price, ask_size ):
        self.bid_price = bid_price
        self.bid_size = bid_size
        self.ask_price = ask_price
        self.ask_size = ask_size

    def initialize( self ):
        self.bid_price = INVALID_VALUE
        self.bid_size = INVALID_VALUE
        self.ask_price = INVALID_VALUE
        self.ask_size = INVALID_VALUE

    def is_valid( self ):
        return ( self.bid_price > 0 and self.ask_price > 0 and self.bid_size > 0 and self.ask_size > 0 )

class PeriodicBar( object ):
    def __init__( self, open, close, high, low, volume, ts ):
        self.open = open
        self.close = close
        self.high = high
        self.low = low
        self.volume = volume
        self.ts = ts

    def initialize( self ):
        self.open.initialize( )
        self.close.initialize( )
        self.high = INVALID_VALUE
        self.low = INVALID_VALUE
        self.volume = INVALID_VALUE
        self.ts = 0 

    def is_valid( self ):
        return ( self.low > 0 and self.high > 0 and self.open.is_valid( ) and self.close.is_valid( ) and self.volume >= 0 )
