from collections import namedtuple
from abc import ABCMeta, abstractmethod

## @brief Interface class to be used by modules who want to recieve a notification whenever the date changes
class DateChangeListener:
    __metaclass__ = ABCMeta

    @abstractmethod
    def on_date_change( self, new_date ):
        pass

## @brief Interface class to be used by modules who want to recieve a notification whenever the year changes
class YearChangeListener:
    __metaclass__ = ABCMeta

    @abstractmethod
    def on_year_change( self, new_year ):
        pass

## @brief Provides an interface for listeners who want to be notified every x seconds by the watch 
class TimePeriodWatchListener:
    __metaclass__ = ABCMeta

    @abstractmethod
    def on_time_period_update( self, current_time ):
        pass

## @brief Provides an interface for listeners who want to be notified at a particular time of the day by the watch 
class DailyWatchListener:
    __metaclass__ = ABCMeta

    @abstractmethod
    def on_daily_time_update( self, current_time ):
        pass

DailyWatchListenerPair = namedtuple( 'DailyWatchListenerPair', 'secs_since_midnight daily_watch_listener' )
