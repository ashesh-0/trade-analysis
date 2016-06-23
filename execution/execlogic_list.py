from cdefs.enum import enum
from execution.marketorder_execlogic import MarketOrderExecLogic

Execlogic_t = enum('Invalid', 'MarketOrderExecLogic')


def get_enum_from_execlogic_name(name):
    return Execlogic_t.forward[name]


def instantiate_execlogic(watch, order_manager, portfolio, execlogic_name, uid):
    if execlogic_name == Execlogic_t.MarketOrderExecLogic:
        return MarketOrderExecLogic(watch, order_manager, portfolio, uid)
    elif execlogic_name == Execlogic_t.Invalid:
        raise AssertionError("CONFIG_ERROR : Invalid execlogic name in user image with uid " + str(uid))
