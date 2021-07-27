# Import the WebSocket object from pybit.
from pybit import WebSocket
import asyncio

class Receiver():
        def __init__(self): 
            # Define your endpoint URLs and subscriptions.
            endpoint_public = 'wss://stream.bybit.com/realtime_public'
            endpoint_private = 'wss://stream.bybit.com/realtime_private'
            subs = [
                'orderBookL2_25.BTCUSD',
                'instrument_info.100ms.BTCUSD',
                'instrument_info.100ms.ETHUSD'
            ]
            self._rest_api = WebSocket(endpoint_public, subscriptions=subs) # Connect without authentication!
            '''
            self._rest_api = WebSocket(
                endpoint_private,
                subscriptions=['position'],
                api_key='...',
                api_secret='...'
            )                                   # Connect with authentication!
            '''
            asyncio.get_event_loop().create_task(self.get_orderbook)
        async def get_orderbook(self):
            eg = 'orderBookL2_25.BTCUSD'
            success,error = await self._rest_api.fetch(eg)
