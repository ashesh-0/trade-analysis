import heapq

# Wrapper class around heapq so that we can directly pass the key and dont have to make tuples
class Heap( object ):
    def __init__( self, initial = None, key = lambda x : x ):
        self.key = key
        if initial:
            self._data = [ ( key( item ), item ) for item in initial ]
            heapq.heapify( self._data )
        else:
            self._data = [ ]

    def push( self, item ):
        heapq.heappush( self._data, ( self.key( item ), item ) )

    def pop( self ):
        if len( self._data ) > 0:
            return heapq.heappop( self._data )[ 1 ]    
        else:
            return None

    def top( self ):
        return self._data[ 0 ][ 1 ]
      
    def size( self ):
        return len( self._data )
