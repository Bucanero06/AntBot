def get_info_widget(
        ticker: str = "AAPL",
        theme: str = "dark",
):
    width = 1000
    height = 200

    header = '''
        <div class="tradingview-widget-container">
        <div class="tradingview-widget-container__widget"></div>
        <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-symbol-info.js" async>
    '''

    footer = '''
        </script>
        </div>
    '''

    widget = {
        "symbol": ticker,
        "height": height,
        "width": width,
        "locale": "en",
        "colorTheme": theme,
        "isTransparent": False
    }

    widget = (
        str(widget)
        .replace('True', 'true')
        .replace('False', 'false')
        .replace('\'', '"')
    )

    return (
        header + widget + footer,
        width,
        height,
    )


def get_chart_widget(
        ticker: str = "AAPL",
        theme: str = "dark",
):
    height = 600
    width = 1000

    header = '''
      <div class="tradingview-widget-container">
      <div id="technical-analysis-chart-demo"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget(
    '''

    footer = '''
      );
      </script>
      </div>
    '''

    widget = {
        "width": width,
        "height": height,
        "symbol": ticker,
        "interval": "D",
        "timezone": "exchange",
        "theme": theme,
        "style": "1",
        "withdateranges": True,
        "hide_side_toolbar": False,
        "allow_symbol_change": True,
        "studies": [
            {"id": "MASimple@tv-basicstudies", "inputs": {"length": 10}},
            {"id": "MASimple@tv-basicstudies", "inputs": {"length": 20}},
        ],
        "show_popup_button": False,
        "popup_width": "1000",
        "popup_height": "650",
        "locale": "en"
    }

    widget = (
        str(widget)
        .replace('True', 'true')
        .replace('False', 'false')
        .replace('\'', '"')
    )

    return (
        header + widget + footer,
        width,
        height,
    )


def get_fundamentals(
        ticker: str = "AAPL",
        theme: str = "dark",
        display: str = "regular",
):
    width = 400
    height = 825

    header = '''
        <div class="tradingview-widget-container">
        <div class="tradingview-widget-container__widget"></div>
        <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-financials.js" async>
    '''

    footer = '''
        </script>
        </div>
    '''

    widget = {
        "colorTheme": theme,
        "displayMode": display,
        "width": width,
        "height": height,
        "symbol": ticker,
        "locale": "en"
    }

    widget = (
        str(widget)
        .replace('True', 'true')
        .replace('False', 'false')
        .replace('\'', '"')
    )

    return (
        header + '\n' + widget + '\n' + footer,
        width,
        height,
    )