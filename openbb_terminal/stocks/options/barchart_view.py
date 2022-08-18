"""Helper functions for scraping options data"""
__docformat__ = "numpy"

import logging
import os

from openbb_terminal.decorators import log_start_end
from openbb_terminal.helper_funcs import export_data, print_rich_table
from openbb_terminal.stocks.options import barchart_model

logger = logging.getLogger(__name__)


@log_start_end(log=logger)
def print_options_data(symbol: str = "PM", export: str = ""):
    """Scrapes Barchart.com for the options information

    Parameters
    ----------
    symbol: str
        Ticker symbol to get options info for
    export: str
        Format of export file
    """

    data = barchart_model.get_options_info(symbol)

    print_rich_table(
        data, show_index=False, headers=["Info", "Value"], title="Options Information"
    )

    export_data(export, os.path.dirname(os.path.abspath(__file__)), "info", data)
