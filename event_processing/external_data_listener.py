from abc import ABCMeta, abstractmethod
from cdefs.watch import Watch

##
# Interface class for all the file sources
# ASSUMPTIONS: When a file source does not have any events left, it enters into passive mode and sets next_event_timestamp_ =0
#
class ExternalDataListener( object ):
    def __init__( self, watch ):
        self.watch = watch
        self.next_event_timestamp = None

    ## Reads and discards the events until a given time
    @abstractmethod
    def seek_to_first_event_after( self, end_time, source_has_events ):
        pass

    ## Looks into events file and sets source to its first event based on timestamp
    @abstractmethod
    def compute_earliest_data_timestamp( self, source_has_events ):
        pass

    ## 
    # Main callback for processing events, used only in case of single source since there we are not worried about 
    # sorting events based on time from multiple sources rather we just want to process the source on its own
    #
    @abstractmethod
    def process_all_events( self ):
        pass

    ##
    # Processes all events it has till the time given as input
    # Typically it should have at least 1 event 
    # This callback will let sources know till when they need to read and process the events
    #
    @abstractmethod
    def process_events_till( self ):
        pass

    ## Getter method for next event time of a source
    def get_next_event_timestamp( self ):
        return self.next_event_timestamp
