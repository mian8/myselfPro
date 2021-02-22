#coding=utf8

import time,asyncio
import myLibrary

async def hello():
    time.sleep(2)

def run():
    for i in range(5):
        loop.run_until_complete(hello())
        print('Hello World:%s' % myLibrary.getTime("s"))  # 任何伟大的代码都是从Hello World 开始的！



loop = asyncio.get_event_loop()
if __name__=="__main__":
    run()