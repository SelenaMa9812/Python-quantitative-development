# -*-coding:utf-8-*- 
import asyncio
from aioquant import quant
def receiver(): #入口函数
    from strategy.receiver import Receiver
    Receiver()

if __name__ == "__main__":
    config_file = "config.json"
    quant.start(config_file,receiver)
    '''
    loop = asyncio.get_event_loop() #启动框架
    loop.run_until_complete(receiver)
    loop.close() 
    '''