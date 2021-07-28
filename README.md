# Python-quantitative-development
## 目标：Asyncio Websocket Receiver
Bybit 交易所的 API文档：https://bybit-exchange.github.io/docs/zh-cn/inverse/#t-websocket

使用 Python - Asyncio 异步库，写出
1. 含有 orderbook channel 和 trade channel 的 Websocket  Receiver 从交易所获得 raw data，orderbook需要是组装好的，并将数据使用zmq.publish()（Zero MQ）广播出去。
2. Python - Asyncio 异步程序，zmq.receive() 接收并打印出数据
## 项目标准结构
```
ProjectName
    |----- docs
    |       |----- README.md
    |----- scripts #放置运行脚本（启动、停止、备份、清洗数据等脚本）
    |       |----- run.sh
    |----- config.json #启动脚本
    |----- src     #源码代码
    |       |----- main.py   #入口文件
    |       |----- strategy
    |               |----- strategy1.py
    |               |----- strategy2.py
    |               |----- ...
    |----- .gitignore
    |----- README.md
```
### 终端运行方法
```
(base) ubuntu@ip-172-31-40-137:~/.vscode-server$ cd ~/.vscode-server/first_project
(base) ubuntu@ip-172-31-40-137:~/.vscode-server/first_project$ python src/main.py
```
按`Ctrl + C`停止运行

<img src="https://github.com/SelenaMa9812/Python-quantitative-development/blob/main/pictures/%E7%BB%88%E7%AB%AF%E8%BF%90%E8%A1%8C.png" width="500" height="100" />

## 研究思路
### 通过WebSocket连接bybit：
#### WebSocket协议
WebSocket是双向的，在客户端-服务器通信的场景中使用的全双工协议，与HTTP不同，它以ws:// 或wss:// 开头。它是一个有状态协议，这意味着客户端和服务器之间的连接将保持活动状态，直到被任何一方（客户端或服务器）终止。在通过客户端和服务器中的任何一方关闭连接之后，连接将从两端终止。

让我们以客户端-服务器通信为例，每当我们启动客户端和服务器之间的连接时，客户端-服务器进行握手随后创建一个新的连接，该连接将保持活动状态，直到被他们中的任何一方终止。建立连接并保持活动状态后，客户端和服务器将使用相同的连接通道进行通信，直到连接终止。

<img src="https://github.com/SelenaMa9812/Python-quantitative-development/blob/main/pictures/websocket.jpg" width="500" height="250" />

#### 不能使用WebSocket的场景
如果我们需要通过网络传输的任何实时更新或连续数据流，则可以使用WebSocket。如果我们要获取旧数据，或者只想获取一次数据供应用程序使用，则应该使用HTTP协议，不需要很频繁或仅获取一次的数据可以通过简单的HTTP请求查询，因此在这种情况下最好不要使用WebSocket。

#### src/pybit/webSocket.py 定义获取数据的函数不需要考虑异步处理
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
#### 非异步处理的提取数据文件（在此基础上改为异步）
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

### 异步并发处理
#### asyncio
并发地运行 Python 协程，并对其执行过程实现完全控制；执行网络 IO 和 IPC；控制子进程；通过队列实现分布式任务；同步并发代码。

```Python
import asyncio

async def func():
    print(1)
    await asyncio.sleep(2)
    print(2)
    return "返回值"

async def main():
    print("main开始")
    # 创建协程，将协程封装到Task对象中并添加到事件循环的任务列表中，等待事件循环去执行（默认是就绪状态）。
    # 在调用
    task_list = [
        asyncio.create_task(func(), name="n1"),
        asyncio.create_task(func(), name="n2")
    ]
    print("main结束")
    # 当执行某协程遇到IO操作时，会自动化切换执行其他任务。
    # 此处的await是等待所有协程执行完毕，并将所有协程的返回值保存到done
    # 如果设置了timeout值，则意味着此处最多等待的秒，完成的协程返回值写入到done中，未完成则写到pending中。
    done, pending = await asyncio.wait(task_list, timeout=None)
    print(done, pending)

asyncio.run(main())
```
特别地，在爬虫过程中，可以通过休眠若干秒，来应对网页中的反爬虫设置。
```Python
async def func():
    print(1)
    await asyncio.sleep(2)
    print(2)
    return "返回值"

async def main():
    print("main开始")
    # 创建协程，将协程封装到一个Task对象中并立即添加到事件循环的任务列表中，等待事件循环去执行（默认是就绪状态）。
    task1 = asyncio.create_task(func())
    # 创建协程，将协程封装到一个Task对象中并立即添加到事件循环的任务列表中，等待事件循环去执行（默认是就绪状态）。
    task2 = asyncio.create_task(func())
    print("main结束")

    # 当执行某协程遇到IO操作时，会自动化切换执行其他任务。
    # 此处的await是等待相对应的协程全都执行完毕并获取结果
    ret1 = await task1
    ret2 = await task2
    print(ret1, ret2)

asyncio.run(main())
```
### 异步接收数据
receiver.py
```Python
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
```
### src/main.py
```Python
# 获取和创建事件循环
loop = asyncio.get_event_loop() # 创建一个事件循环
loop.run_until_complete() # 运行直到future被完成：将协程当做任务提交到事件循环的任务列表中，协程执行完成之后终止。
loop.run_forever() #运行事件循环直到 stop() 被调用，在量化交易系统中使用，无限执行
```

```Python
# -*-coding:utf-8-*- 
import asyncio
# from aioquant import quant

def myreceiver(): #入口函数
    from strategy.receiver import Receiver
    Receiver()

if __name__ == "__main__":
    '''
    config_file = "config.json"
    quant.start(config_file,receiver)
    '''
    loop = asyncio.get_event_loop() #启动框架
    loop.run_forever(myreceiver)
    loop.close() 

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
 将下面代码添加到server的main文件最前面：
 ```Python
import zmq import sys
context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("tcp://*:5555")
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
 将下面代码直接在client中执行：
 ```Python
import zmq
import json
context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.connect("tcp://localhost:5555")
socket.setsockopt_string(zmq.SUBSCRIBE, '')  # 消息过滤
while True:
    response = socket.recv_string()
    response = json.loads(response)
    if isinstance(response, list):
        for r in response:
            print(r)
    else:
        print(response)
 ```
### 参考资料
1. asyncio异步编程，你搞懂了吗？ - 知乎  https://zhuanlan.zhihu.com/p/137057192

2. https://blog.csdn.net/weixin_34293911/article/details/93467995?utm_medium=distribute.pc_relevant.none-task-blog-2%7Edefault%7EsearchFromBaidu%7Edefault-1.pc_relevant_baidujshouduan&depth_1-utm_source=distribute.pc_relevant.none-task-blog-2%7Edefault%7EsearchFromBaidu%7Edefault-1.pc_relevant_baidujshouduan

3. https://github.com/coinrising/okex-api-v5/blob/4e1d2d2e55c68f200d334ce6a966b63ce5bacdcc/websocket_example.py#L176 

4. https://github.com/zeromq/pyzmq

5. 【AIOQuant量化交易框架】第3期 利用REST API拉取行情数据  https://www.bilibili.com/video/BV15J411B7bG
 
6. endwenscheng/demo  https://github.com/endwenscheng/demo

7. 【AIOQuant量化交易框架】paulran/aioquant: Asynchronous event I/O driven quantitative trading framework.  https://github.com/paulran/aioquant

### 特别致谢—— https://github.com/xiandong79
感谢作者(我的面试官)在我没做出笔试题的情况下，提供ubuntu服务器给我摸索代码的机会；通过一段有温度的聊天，帮助我捋清量化岗位的职业方向和能力需求；从职业发展的角度，给我提升编程能力的建议。

### 一点感悟
接到题目后，6个小时只能蜻蜓点水的浏览所有资料，对各个部分没有能够深入地理解，再一次认识到自己不是天才的事实，像电影里的特工那样随意更换身份的天才，可望不可即。

当一点点深入开发的各个部分，发现很多视频课程中的教学内容采用的是已封装好的框架，不知道开发岗位的工作过程中可不可以调用外部框架；对于协程、异步，接收端、发送端代码的使用，还是认识模糊，一旦调包使用的某个函数出现问题，我很难找出解决办法。


