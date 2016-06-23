import pytz
import logging
import datetime
from cdefs.watch_listener import DailyWatchListenerPair, DateChangeListener, YearChangeListener, TimePeriodWatchListener
from utils.datetime_convertor import get_unix_timestamp_from_hhmm_tz, get_custom_est_midnight_time_from_date, get_custom_est_ref_time_from_unix_timestamp, get_custom_est_date_from_unix_timestamp

USING_EST_CUSTOM_TRADING_DATE = 1


class Watch(object):
    unique_instance = None

    def __init__(self, start_date, end_date):
        self.current_time = datetime.datetime.fromtimestamp(0).replace(tzinfo=pytz.UTC)
        self.last_ref_time = datetime.datetime.fromtimestamp(0).replace(tzinfo=pytz.UTC)
        self.current_date = datetime.date(1900, 1, 1)
        self.secs_since_midnight = 0
        self.short_duration = 300  # 5 minutes
        self.long_duration = 3600  # 1 hour
        self.secs_since_midnight_short_duration_updated = 0
        self.secs_since_midnight_long_duration_updated = 0
        self.current_idx = 0
        self.daily_watch_listeners = []
        self.inactive_daily_watch_listeners = []
        self.date_change_watch_listeners = []
        self.year_change_watch_listeners = []
        self.short_duration_watch_listeners = []
        self.long_duration_watch_listeners = []

        if USING_EST_CUSTOM_TRADING_DATE:
            self.start_time = get_custom_est_midnight_time_from_date(start_date)
            self.end_time = get_custom_est_midnight_time_from_date(end_date)
        else:
            self.start_time = get_unix_timestamp_from_hhmm_tz(start_date, 0, pytz.timezone('UTC'))
            self.end_time = get_unix_timestamp_from_hhmm_tz(end_date, 2359, pytz.timezone('UTC'))

    @staticmethod
    def SetUniqueInstance(start_date, end_date):
        if Watch.unique_instance is None:
            Watch.unique_instance = Watch(start_date, end_date)
        return Watch.unique_instance

    @staticmethod
    def GetUniqueInstance():
        if Watch.unique_instance is None:
            raise ValueError('Watch : Please call SetUniqueInstance once')
        return Watch.unique_instance

    @staticmethod
    def RemoveUniqueInstance():
        Watch.unique_instance = None

    ## @brief Function to be called to add as a listener of the watch at a particular time everyday
    #  @param hhmmss The time at which the listener wants to be notified
    #  @param listener The pointer to the listener object
    #
    def add_daily_watch_listener(self, hhmmss, listener):
        secs_since_midnight = (hhmmss % 100) + (((hhmmss / 100) % 100) + (((hhmmss / 10000) % 100) * 60)) * 60
        i = 0
        for i in range(len(self.daily_watch_listeners)):
            if self.daily_watch_listeners[i][0] >= secs_since_midnight:
                break
        self.daily_watch_listeners.insert(i, (secs_since_midnight, listener))  # insert at correct place
        self.current_idx += 1

    ## @brief Function to be called to add as a listener of the watch, to be notified on every date change
    #  @param listener The pointer to the listener object
    #
    def add_date_change_watch_listener(self, listener):
        self.date_change_watch_listeners.append(listener)

    ## @brief Used to notify all the listeners of the date change event
    def broadcast_date_change(self, new_date):
        for listener in self.date_change_watch_listeners:
            listener.on_date_change(new_date)

    ## @brief If the date changes or the simulation ends, we need to clear the list of daily listeners
    #  by calling each one of them in order
    #
    def clear_pending_daily_watch_listeners(self):
        while self.current_idx < len(self.daily_watch_listeners):
            top_dwlp = self.daily_watch_listeners[self.current_idx]
            self.current_time = self.last_ref_time + datetime.timedelta(0, top_dwlp[0]
                                                                        )  # These are fake, not based on market data
            self.secs_since_midnight = datetime.timedelta(0, top_dwlp[0])
            top_dwlp[1].on_daily_time_update(self.current_time)
            self.current_idx += 1

    ## @brief On any new event file source should call this function of the watch to update it
    #
    #  File source should call this function before making a call to the market book
    #  because we want the watch to be updated before anyone else on any new market event update
    #
    #  @param latest_time The time associated with the new market event
    #
    def on_new_market_event(self, latest_time):
        new_date = self.current_date
        new_last_ref_time = 0
        date_has_changed = False
        year_has_changed = False

        if (latest_time - self.last_ref_time).total_seconds() >= 82800:  # This means that the date has changed
            if USING_EST_CUSTOM_TRADING_DATE:
                # Calculate new last_ref_time_ if needed
                new_last_ref_time = get_custom_est_ref_time_from_unix_timestamp(latest_time)

                # Calculate new date if needed
                new_date = get_custom_est_date_from_unix_timestamp(latest_time)
            else:
                # Calculate new date if needed
                #new_date = get_utc_yyyymmdd_from_sec_since_epoch( latest_time )

                # Calculate new last_ref_time_ if needed
                #new_last_ref_time = get_time_from_tzhhmm( new_date, 0, pytz.timezone( 'UTC' ) )
                raise AssertionError("Watch : TODo implement")

        if new_date != self.current_date:
            date_has_changed = True
        else:
            new_last_ref_time = self.last_ref_time

        new_secs_since_midnight = (latest_time - new_last_ref_time).total_seconds()

        # If the date has changed, we need to call all the  pending listeners in time sorted order
        # We need to simulate fake timing because listeners might check time or might want to do
        # something related to time
        # Therefore, we cannot update to latest_time and new_date even if the date has changed till we go
        # through the pending listeners
        if date_has_changed:
            self.clear_pending_daily_watch_listeners()
            self.current_idx = 0  # Now that the date has changed, we need to start again
        elif self.current_idx < len(self.daily_watch_listeners):
            while ((self.current_idx < len(self.daily_watch_listeners)) and
                   (self.daily_watch_listeners[self.current_idx][0] < new_secs_since_midnight)):
                self.current_time = new_last_ref_time + datetime.timedelta(
                    0, self.daily_watch_listeners[self.current_idx][0])
                self.secs_since_midnight = self.daily_watch_listeners[self.current_idx][0]
                self.daily_watch_listeners[self.current_idx][1].on_daily_time_update(self.current_time)
                self.current_idx += 1

        if date_has_changed:
            # Check if year has changed
            year_has_changed = self.current_date.year != new_date.year

            self.current_date = new_date  # Update date
            self.last_ref_time = new_last_ref_time  # Update last ref time
            self.current_time = self.last_ref_time
            self.secs_since_midnight = 0  # TODO check
            self.secs_since_midnight_short_duration_updated = 0
            self.secs_since_midnight_long_duration_updated = 0

            # Notify the listeners that the date has changed
            self.broadcast_date_change(new_date)

            # If the date has changed, then we need to move to correct index in vector
            # Here we just need to move to correct index
            while ((self.current_idx < len(self.daily_watch_listeners)) and
                   (self.daily_watch_listeners[self.current_idx][0] < new_secs_since_midnight)):
                self.current_time = new_last_ref_time + datetime.timedelta(
                    0, self.daily_watch_listeners[self.current_idx][0])  # call the listener by simulating fake time
                self.secs_since_midnight = self.daily_watch_listeners[self.current_idx][0]
                self.daily_watch_listeners[self.current_idx][1].on_daily_time_update(self.current_time)
                self.current_idx += 1

        ## We could not update these earlier because we were simulating fake events
        # Update secs_since_midnight
        self.secs_since_midnight = new_secs_since_midnight

        # Update current time
        self.current_time = latest_time

        # Notify Short Duration Listeners
        if self.secs_since_midnight >= self.secs_since_midnight_short_duration_updated + self.short_duration:  # is short duration due
            self.secs_since_midnight_short_duration_updated = self.secs_since_midnight
            for listener in self.short_duration_watch_listeners:
                listener.on_time_period_update(self.current_time)

        # Notify Long Duration Listeners
        if self.secs_since_midnight >= self.secs_since_midnight_long_duration_updated + self.long_duration:  # is long duration due
            self.secs_since_midnight_long_duration_updated = self.secs_since_midnight
            for listener in self.long_duration_watch_listeners:
                listener.on_time_period_update(self.current_time)
