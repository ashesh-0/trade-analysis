#/usr/bin/env python
import os
import sys
import datetime
import argparse
import random
import pytz

# Common classes

from cdefs.watch import Watch
from cdefs.security_name_indexer import SecurityNameIndexer

from cdefs.defines import TradeType_t, OrderType_t, get_algo_from_str
from execution.execution_manager import ExecutionManager

from order_routing.base_order_manager import BaseOrderManager
from order_routing.backtester import BackTester

# Filesources and data handlers
from mds_messages.periodic_bar_file_source import PeriodicBarFileSource

from event_processing.market_book import MarketBook
from event_processing.historical_dispatcher import HistoricalDispatcher
from utils.datetime_convertor import get_unix_timestamp_from_hhmm_tz


def main():
    #add arguments
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('start_date', type=str, help='Date of the simulation')
    parser.add_argument('shortcode', type=str, help='Security for which we want to simulate execution')

    parser.add_argument('buysell', type=str, help='"B" for Buy, "S" for Sell.')
    parser.add_argument('size', type=int, help='size to buy/sell')
    parser.add_argument('algorithm', type=str, help='Momentum,MeanReversion, Direct')
    parser.add_argument('hhmmss', type=int, help='hhmmss (UTC timezone)')

    # parse arguments
    args = parser.parse_args()

    start_date = datetime.datetime.strptime(args.start_date, '%Y%m%d').date()
    end_date = start_date + datetime.timedelta(1)
    shortcode = args.shortcode
    buysell = TradeType_t.Buy if args.buysell == 'B' else TradeType_t.Sell
    size = args.size
    execution_algorithm = get_algo_from_str(args.algorithm)
    hhmmss = args.hhmmss

    watch = Watch.SetUniqueInstance(start_date, end_date)

    # Create instance of security name indexer, created only once in whole program
    sec_name_indexer = SecurityNameIndexer.GetUniqueInstance()
    sec_name_indexer.add_symbol(shortcode)

    # Create the unqiue instance of historical dispatcher, this is the only dispatcher object for the whole program
    historical_dispatcher = HistoricalDispatcher()

    # Create instance of backtester
    backtester = BackTester.GetUniqueInstance(watch)

    watch.add_date_change_watch_listener(backtester)

    market_book = MarketBook.GetUniqueInstance(watch, 0)  # Create a market book for this security
    market_book.add_market_event_listener(backtester)  # Backtester listens to all the market books

    # Create minute bar file sources
    this_file_source = PeriodicBarFileSource(shortcode, watch, start_date, end_date)
    historical_dispatcher.add_external_data_listener(this_file_source)

    # We do not want any file source to have data prior to start date
    historical_dispatcher.seek_hist_file_sources_to(get_unix_timestamp_from_hhmm_tz(start_date, 0, pytz.timezone(
        'UTC')))
    # Instantiate order manager.
    order_manager = BaseOrderManager(watch, 0)

    # Instantiate execution manager.
    market_books = MarketBook.GetUniqueInstances(watch)
    execution_manager = ExecutionManager(watch, market_books, order_manager, execution_algorithm)

    start_midnight_seconds = 3600 * int(hhmmss / 10000) + 60 * (int(hhmmss % 10000) / 100) + hhmmss % 100
    execution_manager.execute(0, buysell, OrderType_t.Market, size, start_midnight_seconds)

    # Run the dispatcher
    historical_dispatcher.run()

    # There might be some listeners which could not be called for the last day
    # since there was no market event at that time. Calling them explicitly
    watch.clear_pending_daily_watch_listeners()
    return True


if __name__ == '__main__':
    main()
