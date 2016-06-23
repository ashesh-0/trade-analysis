from abc import ABCMeta, abstractmethod


##
# Interface class to derive all the classes who want to listen every price event for a given security
#
class MarketEventListener:
    __metaclass__ = ABCMeta

    ##
    # Called on every new market event
    # @param sec_id Security id to which the market event corresponds
    # @param market_info A reference to the latest market book
    #
    @abstractmethod
    def on_market_update(self, sec_id, market_info):
        pass
