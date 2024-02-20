# AntBot Project (under active development)

## Overview

This project synopsis document presents a guide for the AntBot codebase. The AntBot is a high-performance trading application tailored for the OKX exchange. It emphasizes real-time data processing, efficient resource management, and
robust technological stack.

### Document Details

- **Document Title:** AntBot Project Synopsis Documentation
- **Visual Reference:**

[Screencast from 02-19-2024 07:16:27 PM.webm](https://github.com/Bucanero06/AntBot/assets/60953006/177c7bd3-46c8-4cd1-9a02-ff0e9ced38e8)

## Deployment Guidelines

### Initial Setup

1. **Prerequisite Installation:**
    - Install the latest version of Docker for compatibility and specific feature support:
      ```bash
      sudo snap refresh docker --channel=latest/edge # Incorporates essential fixes
      ```

2. **Repository Initialization:**
    - Clone and prepare the AntBot repository:
      ```bash
      git clone https://github.com/Bucanero06/AntBot.git
      cd AntBot
      ```
    - Verify `.env` file configuration for environmental consistency.

### Container Deployment

1. **Container Initialization:**
    - Deploy Docker containers efficiently, ensuring build and execution in a non-interactive mode:
      ```bash
      docker-compose up -d --build
      ```

2. **Log Monitoring:**
    - For comprehensive logs:
      ```bash
      docker-compose logs -f
      ```
    - For targeted container logs:
      ```bash
      docker-compose logs -f <container_name>
      ```

3. **Docker-Compose Specification:**
    - Utilization of docker-compose version 2.2 is strategic for optimal resource management within a VM environment,
      despite version 3.x offering the latest features.

## Technology Stack Summary 

The AntBot project integrates an array of leading-edge technologies, each contributing uniquely to the system's overall
performance and versatility:

1. **FastAPI & Uvicorn:**
    - Implements a modern, high-performance framework with Uvicorn serving for high concurrency and reliability.

2. **Pydantic & Redis:**
    - Employs Pydantic for robust data structuring and Redis for fast, scalable data processing.

3. **Supplementary Technologies:**
    - Nginx, Asyncio, Wave, Poetry, VectorBT(PRO), Nautilus Trader, and TradingView enrich the stack with capabilities ranging
      from request management to advanced backtesting and market analysis (under development) 

4. **Additional Components:**
    - Incorporates Websockets, Requests, Docker, GCP Logging & Monitoring, Firebase (GCP), and OAuth2 to fortify the
      infrastructure, security, and operational monitoring.
    - Prometheus and Grafana are being integrated to provide comprehensive monitoring and alerting.

Each of these has many features yet to be fully integrated into the AntBot project, but the potential for expansion
and enhancement is vast, many low-hanging fruits are available for the taking. 

## Entry Waypoints
dashboard
```yaml
port 10101 or behind a reverse proxy (e.g. Nginx) on port 80
```
[Screencast from 02-07-2024 01:06:45 AM.webm](https://github.com/Bucanero06/AntBot/assets/60953006/d47830d0-bd6c-4718-bb3e-ecce9da40ffe)

okx_signal_handler:
```yaml
# Global 
instID="BTC-USDT-240628",
leverage=0,
max_orderbook_limit_price_offset=None,
clear_prior_to_new_order=False,
red_button=False,
# Principal Order 
usd_order_size=0,
order_side="BUY",
order_type="MARKET",
flip_position_if_opposite_side=True,
# Principal Order's TP/SL/Trail
tp_trigger_price_offset=100,
tp_execution_price_offset=90,
sl_trigger_price_offset=100,
sl_execution_price_offset=90,
trailing_stop_activation_price_offset=100,
trailing_stop_callback_offset=10,
# DCA Orders (are not linked to the principal order)
dca_parameters=[
    DCAInputParameters(
        usd_amount=100,
        order_type="LIMIT",
        order_side="BUY",
        trigger_price_offset=100,
        execution_price_offset=90,
        tp_trigger_price_offset=100,
        tp_execution_price_offset=90,
        sl_trigger_price_offset=100,
        sl_execution_price_offset=90
    ),
    DCAInputParameters(
        usd_amount=100,
        order_type="LIMIT",
        order_side="BUY",
        trigger_price_offset=150,
        execution_price_offset=149,
        tp_trigger_price_offset=100,
        tp_execution_price_offset=90,
        sl_trigger_price_offset=100,
        sl_execution_price_offset=90
    )
]

```
... more to be documented




## Redis Stack 
[Screencast from 02-18-2024 06:06:26 PM.webm](https://github.com/Bucanero06/AntBot/assets/60953006/2e26fcde-6fa6-4aa7-8c61-9472f78e54d8)

Currently there are a few channels used by default, here are all that have been implemented.


### Quick Usage of `on_stream_data`

The `on_stream_data` decorator lets you easily link callback functions to specific Redis streams. When new data arrives on a stream, the corresponding callback is triggered automatically.

#### Define Your Callbacks:

```python
@on_stream_data('stock_updates')
async def handle_stock_updates(data):
    print(f"Received stock update: {data}")

@on_stream_data('currency_fluctuations')
async def handle_currency_fluctuations(data):
    print(f"Received currency fluctuation: {data}")
```

#### Start Listening:

```python
asyncio.run(start_listening(['stock_updates', 'currency_fluctuations']))
```

That's it! The callbacks `handle_stock_updates` and `handle_currency_fluctuations` will process data from their respective streams in real-time. Simple and straightforward! 😊

#### Consumers Management

Once your callbacks are set up and listening, you can manage your stream listeners and data processing with functions like add_listener_task, remove_listener_task, and get_all_listener_tasks. These allow you to dynamically control and monitor your stream listeners for optimal operation and maintenance.

That's the quick overview! For detailed operations or further assistance, dive into the specific functions or ask away! 😊

### Rest API Channels
```redis
okx:webhook@okx_premium_indicator@input@{instrument_id}
okx:webhook@okx_premium_indicator@response@{instrument_id}
```
```redis
okx:webhook@okx_antbot_webhook@input@{instrument_id}
okx:webhook@okx_antbot_webhook@response@{instrument_id}
```
```redis
okx:rest@fill@3months
okx:reports@fill_metrics
```

### Websockets
```redis
okx:websockets@all
```
```redis
okx:websockets@{message_channel} 
```
where `message_channel` is one of the following:
```yaml
{
    "price-limit": PriceLimitChannel,
    "instruments": InstrumentsChannel,
    "mark-price": MarkPriceChannel,
    "index-tickers": IndexTickersChannel,
    "tickers": TickersChannel,
    "books5": OrderBookChannel,
    "books": OrderBookChannel,
    "bbo-tbt": OrderBookChannel,
    "books50-l2-tbt": OrderBookChannel,
    "books-l2-tbt": OrderBookChannel,
    "mark-price-candle{**}": MarkPriceCandleSticksChannel,
    "index-candle{**}": IndexCandleSticksChannel,
    "account": AccountChannel,  # Missing coinUsdPrice
    "positions": PositionsChannel,  # Missing pTime
    "balance_and_position": BalanceAndPositionsChannel,
    "orders": OrdersChannel
}
```
```redis
okx:reports@balance_and_position
okx:reports@account
okx:reports@positions
okx:reports@orders
okx:reports@mark-price@{instId}
okx:reports@{tickers}
okx:reports@{message_channel}@{instId}
```
where `message_channel` is one of the following:
```yaml
[
   "books5", 
   "books", 
   "bbo-tbt", 
   "books50-l2-tbt", 
   "books-l2-tbt"
]
```
## TradingView Alerts Configuration

A forthcoming feature includes an automated alert creation and management page. Initial steps to set up alerts using the
LuxAlgo Premium Indicator are detailed, emphasizing customization and webhook integration for comprehensive strategy
alerting.

---

### Creating the TradingView Alerts

Automated Alert Creation and Management Page coming soon
![Screenshot from 2024-02-18 18-16-02](https://github.com/Bucanero06/AntBot/assets/60953006/b93fa5d9-7329-4684-8d4e-0534a4987845)

```
e.g. LuxAlgo Premium Indicator
    i   - Create Alert on {ASSET}
    ii  - Set Alert "Condition" to ["LuxAlgo Premium"]["Any Confirmation"]
    iii - Set Alert "Action" to "Webhook"
    iv  - Set appropriate "Expiration Time" (e.g. 1 hour, 1 month, Open-ended)
    v   - Set "Webhook URL" to your Hosted app URL (e.g. http://your-app-ip:your-port/yourtvendpoint)
            make sure to select the Webhook URL check box so that the alert is sent using the Webhook
    vi  - Name Alert Name (e.g. "LuxAlgo Premium") to something that is easy to identify in the logs
    vii - Add the Message as found in the JSON payload examples below, you can customize the message to your liking
    viii - Create Alert - Congratulations you just set up your first TradingView Strategy Alert Webhook!
            if you want other conditions to trigger alerts, repeat steps i-viii since LuxAlgo Premium Indicator
            does not allow for custom webhooks  explicitly but you easily adjust. This application is designed to be used with the LuxAlgo Premium Indicator
            but can be used with any TradingView Strategy Alert Webhook that is sent in the correct format.
            See the TradingView Webhook Documentation for more information on how to create a custom webhook and notify
            the bot of your custom webhook format for entries and exits. *TODO: See the "Expanding the Bot" section in this 
            ReadMe for more.*
```

## Disclaimer

This project is for informational purposes only. You should not construe this information or any other material as
legal, tax, investment, financial or other advice. Nothing contained herein constitutes a solicitation, recommendation,
endorsement or offer by us or any third-party provider to buy or sell any securities or other financial instruments in
this or any other jurisdiction in which such solicitation or offer would be unlawful under the securities laws of such
jurisdiction.

***If you intend to use real money, use it at your own risk.***

Under no circumstances will we be responsible or liable for any claims, damages, losses, expenses, costs or liabilities
of any kind, including but not limited to direct or indirect damages for loss of profits.

For further elaboration or specific details, please proceed to the codebase documentation or refer to the official
documentation of each integrated component or library.

## Contact US
Reach out to us if you would like to contribute and help maintain this project, monitary assistance can be provided to contributors that can bring valuable changes and additions, from meaningful features and task completions to documentation and testing. If you are interested in using AntBot yourself and have questions please reach out to me directly at `ruben@carbonyl.org`
