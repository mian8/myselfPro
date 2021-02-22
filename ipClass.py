#coding=utf8
"""

"""


import requests,lxml,re
import logging
import json
import subprocess
from bs4 import BeautifulSoup
from selenium import webdriver
from threading import Thread
from queue import Queue

from myLibrary import getTime
from sqlClass import sqlDeal

#获取ip的类
class getIpAndCheck(object):
    def __init__(self):
        self.headers={'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                   'Accept-Encoding': 'gzip, deflate, sdch', 'Accept-Language': 'zh-CN,zh;q=0.8',
                   'Cache-Control': 'max-age=0', 'Connection': 'keep-alive',
                   'Cookie': '_free_proxy_session=BAh7B0kiD3Nlc3Npb25faWQGOgZFVEkiJTRhMTU0ZWM5ODJiYzJlYjQ4NDExN2Y5ODE3YTQ0NTJhBjsAVEkiEF9jc3JmX3Rva2VuBjsARkkiMW9mQWp0dDZkUk5LdFZCUFBUVDRpdHJJNklQU0JvT3N2V0ZYQ1RGd3ZETUk9BjsARg%3D%3D--621bafde391b32c3c994463d8809cb9c91c09ebf; Hm_lvt_0cf76c77469e965d2957f0553e6ecf59=1530606053,1530606061,1530606065,1530607108; Hm_lpvt_0cf76c77469e965d2957f0553e6ecf59=1530607108',
                   'Host': 'www.xicidaili.com', 'If-None-Match': 'W/"a5db219236a51312e5a622f1537ee0fa"',
                   'Upgrade-Insecure-Requests': '1',
                   'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.221 Safari/537.36 SE 2.X MetaSr 1.0'}
        self.proxies = ""
        self.ips = []
        self.sqlDB=sqlDeal()

    #爬取A网址ip，通过指定方式A解析页面数据
    def getAndlxml(self,url,func):
        logging.info("开始爬取ip")
        ipDict = func(url) #通过指定方法解析出ip列表

        validIp= self.checkIp(ipDict) #验证获取有效ip

        end = self.sqlAndSave(validIp) #存储可用ip到数据库
        logging.warning(validIp)
        if end :
            logging.warning(f"**********\n本次获取到可用ip共{end}条\n**********")
        return ipDict

    #页面解析方法A
    def funcA(self,url):
        headers=self.headers
        proxies=self.proxies
        if proxies:
            response = requests.get(url, headers=headers, proxies=proxies)
        else:
            response = requests.get(url, headers=headers)
        logging.info("解析页面")
        html = BeautifulSoup(response.text, "lxml")
        # print(html)
        logging.debug(html)
        body = html.find("table", {"class": "table table-bordered table-striped"})
        ipDict = {}
        if body is None:logging.warning("没有定位到目标位置")
        else:
            tdLines = body.find_all("tr")
            for line in tdLines[1:]:
                # print(line)
                thValues = line.find_all("td")
                ip = thValues[0].get_text()
                port = thValues[1].get_text()
                ipDict[ip]=port
            # print(ipList)
        if ipDict== {} :
            logging.warning("目标页面没有获取到ip")
        logging.info(f"初始ip列表{ipDict}")
        return ipDict

    #页面解析方法B
    def funcB(self,url):
        driver = webdriver.Firefox()
        driver.get(url)
        htmlpage=driver.page_source
        driver.close()
        logging.info("解析页面")
        html = BeautifulSoup(htmlpage, "lxml")
        # print(html)
        logging.debug(html)
        body = html.find("table", {"class": "table table-hover"})
        ipDict = {}
        if body is None:
            logging.warning("没有定位到目标位置")
        else:
            tdLines = body.find_all("tr")
            for line in tdLines[1:]:
                # print(line)
                thValues = line.find_all("td")
                ipPort = thValues[0].get_text()
                ip, port =ipPort.split(":")
                ipDict[ip] = port
            # print(ipList)
        if ipDict == {}:
            logging.warning("目标页面没有获取到ip")
        logging.info(f"初始ip列表{ipDict}")
        return ipDict

    #页面解析方法C
    def funcC(self,url):
        """
        :param url:https://checkerproxy.net/api/archive/2020-11-25
        :return: {ip:port}
        """
        url=url+getTime(types="d")
        logging.info(url)
        text=requests.get(url).text
        IpJson=json.loads(text)
        ipDict = {}
        for line in IpJson:
            #通过限制延迟来缩小验证的数据量
            if line["timeout"] < 5000 and line["type"] in (1,2) and line["kind"] != 0:
                ip, port = line["addr"].split(":")
                ipDict[ip] = port
        logging.info(f"ip爬取成功,共计{len(ipDict)}条")
        logging.debug(f"初始ip列表{ipDict}")
        return ipDict

    #剔除无用ip
    def checkIp(self,ipList):

        logging.info("检查IP是否有响应")
        #设置线程总数
        num_threads = 3
        q = Queue()
        #批量创建线程
        for i in range(num_threads):
            t = Thread(target=self._checkIPThread, args=(i, q))  # 批量创建线程
            t.setDaemon(True)  # 设置为守护线程  主线程A中，创建了子线程B，将A设置为守护线程，此时主线程A执行结束啦，不管子线程B是否执行完成，一并和A一起退出
            t.start()
        #循环推送变量至线程
        for i in ipList.items():
            q.put(i)
        print("主线程等待中 ...")
        q.join()  # 主线程A中，创建了子线程B，并在主线程中设置B.join(),那么，主线程A会在调用的地方等待，直到子线程B完成操作后，才可以继续向下执行。

        logging.debug(self.ips)
        logging.info("本次获取ip验证完毕")
        return self.ips

    # 通过ping验证ip是否有效
    def _checkIPThread(self,i,ipQueue):
        while True :
            #获取队列中一个待测试ip
            waiteChickIp=ipQueue.get()
            logging.debug(f"线程{i}正在开始验证:{waiteChickIp}")
            newIpLine={}
            #如果是包含端口的i字符串，则取前段
            newIpLine["ipAdress"] = ip = waiteChickIp[0]
            newIpLine["port"] = waiteChickIp[1]
            logging.debug("Thread {} pinging {}".format(i, ip))
            #内部验重，如果该ip出现在数据库，则直接舍弃验证
            if not self.sqlDB.duplicationIP(ip):
                #对ip进行ping，获取返回内容
                cmd_input = subprocess.Popen(["ping.exe", ip], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                             stderr=subprocess.PIPE, shell=True)
                cmd_out = cmd_input.stdout.read()
                #通过正则获取字段，判断ping结果是否符合要求
                regex = re.compile("\d+%", re.IGNORECASE)
                logging.debug(cmd_out.decode("gbk"))
                logging.debug("Thread {} end. {}".format(i, ip))
                wastePercentage=regex.findall(cmd_out.decode("gbk"))
                if wastePercentage == ["0%"] and b"ms" in cmd_out :
                    newIpLine["status"]=1
                    logging.debug("{}可用".format(ip))
                else:
                    logging.debug(f"丢失率{wastePercentage}%")
                    newIpLine["status"] = 0
                newIpLine["webcheck"]=1
                logging.debug(newIpLine)
                self.ips.append(newIpLine)
                logging.info(f"已完成验证 {len(self.ips)} 条……")
            else:newIpLine["status"]=0

            #队列为空时，结束线程
            if ipQueue.empty:
                ipQueue.task_done()
        return

    #组合sql，存储ip，清空ips
    def sqlAndSave(self,argv):
        logging.info("存储本次获取的ip")
        # self.sqlDB.saveIp(argv)
        end=self.sqlDB.saveIpList(argv)
        return end



if __name__=="__main__":
    fool = getIpAndCheck()
    # iplist = fool.getAndlxml("https://www.kuaidaili.com/free/intr/",fool.funcA)
    # iplist=['121.69.10.62:9090', '183.247.152.98:53281', '223.82.106.253:3128','123.139.56.238:9999']
    # ss= fool.checkIp(iplist)
    # validIp=[{'ipAdress': '39.109.123.188', 'port': '3128', 'status': 1}, {'ipAdress': '222.94.196.241', 'port': '3128', 'status': 1}, {'ipAdress': '113.204.164.194', 'port': '8080', 'status': 1}, {'ipAdress': '222.94.196.138', 'port': '3128', 'status': 1}, {'ipAdress': '222.90.110.194', 'port': '8080', 'status': 1}, {'ipAdress': '190.122.186.222', 'port': '8080', 'status': 1}, {'ipAdress': '47.91.137.211', 'port': '3128', 'status': 1}, {'ipAdress': '183.196.170.247', 'port': '9000', 'status': 1}, {'ipAdress': '117.141.155.242', 'port': '53281', 'status': 1}]
    # fool.sqlAndSave(validIp)

    # 废物代理网站
    # fool.getAndlxml("https://www.kuaidaili.com/free/inha/",fool.funcA)
    # fool.getAndlxml("https://www.kuaidaili.com/free/intr/",fool.funcA)
    # 代理网站checkerproxy，大量ip，慢慢验证
    fool.getAndlxml("https://checkerproxy.net/api/archive/", fool.funcC)
    # fool.getAndlxml("http://www.goubanjia.com/",fool.funcB)
    # fool.getAndlxml("https://www.zdaye.com/",fool.funcC)