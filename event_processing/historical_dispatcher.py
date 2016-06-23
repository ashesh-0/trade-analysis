from cdefs.heap import Heap

##
#  @brief Gets a list of historical/logged file sources, ExternalDataListener will know the first timestamp for the events 
#  it's processing, this class will ask them to read the data and depending on whether there is any data of interest 
#  ( for instance it could have data but of securities that are not of interest ),
#  compute the next_event_timestamp
#
#  Once the sources have next_event_timestamp two choices here :
#  (i) sort the events based on time and based on the event time call the corresponding ExternalDataListener to process that event
#  and fetch the next_event_timestamp and resort if the next_event_timestamp is != 0 
#  (ii) all the sources that have some data in the channels, sequentially call them to process all data they have
#  and call any listeners as and when they feel a need to 
#  downsides of method (ii) : 
#  (a) if the time we take in processing events is very high then events from other sources could be ignored.
#  (b) events are sure to not be chronological in live and hence different in hist and live
# 
#  At the end HistoricalDispatcher collects all sources in prev_external_data_listener_vec_ and calls delete on them 
#
class HistoricalDispatcher( object ):
    def __init__( self ):
        self.external_data_listener_list = []
        self.prev_external_data_listener_list = []
        self.first_event_enqueued = False

    ##
    #  @brief If needed this can seek the historical sources to skip processing event until a given time, i.e start of trading hours etc 
    #
    #  @param end_time time till which we want to seek forward the historical file sources 
    #
    def seek_hist_file_sources_to( self, seek_time ):
      external_data_listener_list_copy = self.external_data_listener_list[ : ] # Will iterate over copy and delete from original
      if not self.first_event_enqueued:
          for listener in external_data_listener_list_copy: # Iterate over copy
              has_events = listener.seek_to_first_event_after( seek_time )
              if not has_events:
                  self.prev_external_data_listener_list.append( listener )
                  self.external_data_listener_list.remove( listener ) # Delete from original   # TODO check would this work
          self.first_event_enqueued = True

    ##
    #  @brief Adds a listener for the data events, the listner also deals with its own data
    #  All it needs from historical dispatcher is a callback which notifies when to process the events and upto 
    #  what time the events can be processed 
    # 
    #  @param new_data_listener A base class pointer through which various dereived listener/filesources will be added 
    #
    def add_external_data_listener( self, new_data_listener ):
        self.external_data_listener_list.append( new_data_listener )

    ## 
    #  @brief A busy loop which processes a bunch of data sources earlier added and distributes events to its listeners
    #  Once called, will keep on processing until all events have been comsumed
    #
    def run( self ):
        external_data_listener_heap = Heap( self.external_data_listener_list, lambda x : x.next_event_timestamp )

        # Only way to get out of this loop is when all sources have been removed. This is the only while loop in the program
        while external_data_listener_heap.size( ) > 0:  # only way to get out of this loop is when all sources have been removed. This is the only while loop in the program
            top_edl = external_data_listener_heap.pop( )
            if external_data_listener_heap.size( ) == 0:
                top_edl.process_all_events( )
                return
            top_edl.process_events_till( external_data_listener_heap.top( ).next_event_timestamp ) # process all events in this source till the next event is older the one on the new top
            next_event_timestamp_from_edl = top_edl.next_event_timestamp # ask the source to get the next_event_timestamp ( the first event that is older than the specified endtime )
            source_has_events = next_event_timestamp_from_edl != 0 # if 0 then no events .. and in historical this means this source can be removed, since it has finished reading the file it was reading from
            if source_has_events:
                external_data_listener_heap.push( top_edl )  # Reinsert into heap
            heap_size = external_data_listener_heap.size( )
            if heap_size == 1: 
                external_data_listener_heap.top( ).process_all_events( ) # Since ComputeEarliestDataTimestamp () has been called, or ProcessEventsTill has been called, the next_event_timestamp will be valid
                external_data_listener_heap.pop( )
                return
            if heap_size == 0:
                return
