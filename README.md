# Python-quantitative-development

## 研究思路
### 通过WebSocket连接bybit：
#### WebSocket协议
WebSocket是双向的，在客户端-服务器通信的场景中使用的全双工协议，与HTTP不同，它以ws:// 或wss:// 开头。它是一个有状态协议，这意味着客户端和服务器之间的连接将保持活动状态，直到被任何一方（客户端或服务器）终止。在通过客户端和服务器中的任何一方关闭连接之后，连接将从两端终止。

让我们以客户端-服务器通信为例，每当我们启动客户端和服务器之间的连接时，客户端-服务器进行握手随后创建一个新的连接，该连接将保持活动状态，直到被他们中的任何一方终止。建立连接并保持活动状态后，客户端和服务器将使用相同的连接通道进行通信，直到连接终止。
```Python
ws  =  WebSocket(
     endpoint = 'wss://stream.bybit.com/realtime' , 
     subscriptions = [ 'order' , 'position' ], 
     api_key = '...' ,
     api_secret = '...' 
)
```
```Python
# Import the WebSocket object from pybit.
from pybit import WebSocket

# Define your endpoint URLs and subscriptions.
endpoint_public = 'wss://stream.bybit.com/realtime_public'
endpoint_private = 'wss://stream.bybit.com/realtime_private'
subs = [
    'orderBookL2_25.BTCUSD',
    'instrument_info.100ms.BTCUSD',
    'instrument_info.100ms.ETHUSD'
]

# Connect without authentication!
ws_unauth = WebSocket(endpoint_public, subscriptions=subs)

# Connect with authentication!
ws_auth = WebSocket(
    endpoint_private,
    subscriptions=['position'],
    api_key='...',
    api_secret='...'
)

# Let's fetch the orderbook for BTCUSD.
print(
    ws_unauth.fetch('orderBookL2_25.BTCUSD')
)

# We can also create a dict containing multiple results.
print(
    {i: ws_unauth.fetch(i) for i in subs}
)

# Check on your position. Note that no position data is received until a
# change in your position occurs (initially, there will be no data).
print(
    ws_auth.fetch('position')
)
```
### 通过Bybit APIs发送或检索信息
```Python
# Get orderbook.
session.orderbook(symbol='BTCUSD')

# Create five long orders.
orders = [{
    'symbol': 'BTCUSD', 
    'order_type': 'Limit', 
    'side': 'Buy', 
    'qty': 100, 
    'price': i,
    'time_in_force': 'GoodTillCancel'
} for i in [5000, 5500, 6000, 6500, 7000]]

# Submit the orders in bulk.
session.place_active_order_bulk(orders)

# Check on your order and position through WebSocket.
ws.fetch('order')
ws.fetch('position')
```
### Market Data Endpoints
orderbook/trade channel: orderbook() #'orderBookL2_25', 'orderBookL2_200', 'trade'
```Python
class WebSocket:

    def __init__(self):

        self.data = {}

        websocket.enableTrace(True)
        self.ws = websocket.WebSocketApp(
            "wss://stream.bytick.com/realtime",
            on_open=self._on_open(self.ws),
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close(self.ws),
        )
        # Setup the thread running WebSocketApp.
        self.wst = threading.Thread(target=lambda: self.ws.run_forever(
            sslopt={"cert_reqs": ssl.CERT_NONE},
        ))

        # Configure as daemon; start.
        self.wst.daemon = True
        self.wst.start()

    def orderbook(self):
        return self.data.get('orderBook_200.100ms.BTCUSD')

    @staticmethod
    def _on_message(self, message):
        m = json.loads(message)
        if 'topic' in m and m.get('topic') == 'orderBook_200.100ms.BTCUSD' and m.get('type') == 'snapshot':
            print('Hi!')
            self.data[m.get('topic')] = m.get('data')

    @staticmethod
    def _on_error(self, error):
        print(error)

    @staticmethod
    def _on_close(ws):
        print("### closed ###")

    @staticmethod
    def _on_open(ws):
        print('Submitting subscriptions...')
        ws.send(json.dumps({
            'op': 'subscribe',
            'args': ['orderBook_200.100ms.BTCUSD']
        }))


if __name__ == '__main__':
    session = WebSocket()

    time.sleep(5)

    print(session.orderbook())
```
### ZMQ
#### Pyzmq的几种模式
1. 请求应答模式（Request-Reply）（rep 和 req）

消息双向的，有来有往，req端请求的消息，rep端必须答复给req端

2. 订阅发布模式 （pub 和 sub）

消息单向的，有去无回的。可按照发布端可发布制定主题的消息，订阅端可订阅喜欢的主题，订阅端只会收到自己已经订阅的主题。发布端发布一条消息，可被多个订阅端同事收到。

3. push pull模式

消息单向的，也是有去无回的。push的任何一个消息，始终只会有一个pull端收到消息.

后续的代理模式和路由模式等都是在三种基本模式上面的扩展或变异。
#### sever.py
```Python
import zmq import sys
context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("tcp://*:5555")
while True:
     try:
     print("wait for client ...")
     message = socket.recv()
     print("message from client:", message.decode('utf-8'))
     socket.send(message)
     except Exception as e:
     print('异常:',e)
     sys.exit()
 ```
 #### client.py
 ```Python
import zmq import sys
context = zmq.Context()
print("Connecting to server...")
socket = context.socket(zmq.REQ)
socket.connect("tcp://localhost:5555")
while True:
     input1 = input("请输入内容：").strip()
     if input1 == 'b':
     sys.exit()
     socket.send(input1.encode('utf-8'))
     message = socket.recv()
     print("Received reply: ", message.decode('utf-8'))
 ```
### 参考资料
1. https://blog.csdn.net/weixin_34293911/article/details/93467995?utm_medium=distribute.pc_relevant.none-task-blog-2%7Edefault%7EsearchFromBaidu%7Edefault-1.pc_relevant_baidujshouduan&depth_1-utm_source=distribute.pc_relevant.none-task-blog-2%7Edefault%7EsearchFromBaidu%7Edefault-1.pc_relevant_baidujshouduan

2. https://github.com/coinrising/okex-api-v5/blob/4e1d2d2e55c68f200d334ce6a966b63ce5bacdcc/websocket_example.py#L176 

3. https://github.com/zeromq/pyzmq

### 一点感悟
6个小时只能蜻蜓点水的浏览所有资料，对各个部分没有能够深入地理解，再一次认识到自己不是天才的事实，像电影里的特工那样随意更换身份的天才，可望不可即。


