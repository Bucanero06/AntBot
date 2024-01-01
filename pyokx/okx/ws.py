from pyokx.okx.websocket.WsPprivateAsync import WsPrivateAsync
ws_private_async = WsPrivateAsync(apiKey=os.getenv('OKX_API_KEY'), secretKey=os.getenv('OKX_SECRET_KEY'),
                                  passphrase=os.getenv('OKX_PASSPHRASE'),
                                  url='wss://wspap.okx.com:8443/ws/v5/business?brokerId=9999',
                                  useServerTime=False)
ws_private_async.start()
ws_private_async.subscribe('/api/v5/trade/order-algo', {'instId': INSTID})