#counding=utf8

import pika,time,json


#消费者
def messgaeConsumer():
    #链接MQ
    connection = pika.BlockingConnection(pika.ConnectionParameters(host="120.25.85.101",port=5672,credentials=pika.PlainCredentials("root","root"),virtual_host="/"))
    channel=connection.channel()
    #若没有队列，创建队列
    channel.queue_declare(queue="auspiont",durable=True,auto_delete=False,exclusive=False)

    #消耗方法
    def callback(ch,method,properties,body):
        print("[删除客户] recv {}".format(body))

    channel.basic_consume(on_message_callback=callback,queue ="auspiont",auto_ack=True)
    #持续循环
    channel.start_consuming()

#生产者
def messageCreat():
    #链接MQ
    connection=pika.BlockingConnection(pika.ConnectionParameters(host="120.25.85.101",port=5672,credentials=pika.PlainCredentials("root","root"),virtual_host="/"))
    channel=connection.channel()
    #若没有队列，创建队列
    channel.queue_declare(queue="auspiont",durable=True,auto_delete=False,exclusive=False)
    channel.basic_publish(exchange="",routing_key="auspiont",body=json.dumps({"id":"77777阿萨德7"}))
    print("发送成功")
    #关闭链接
    connection.close()


messageCreat()
