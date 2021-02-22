#coding=utf8

"""
1.小说源获取
定向搜索
网站遍历
2.书籍列表添加
3.获取小说内容
4.特殊类型小说获取

"""

import requests,lxml,re,subprocess,pymysql,requests_html
from bs4 import BeautifulSoup
from zhconv import convert
from threading import Thread
from queue import Queue
import logging
import warnings,random
import time,datetime,json
import random,time
import copy
import urllib3


from myLibrary import getTime
from sqlClass import sqlDeal
from ipClass import getIpAndCheck

logging.basicConfig(level=logging.DEBUG)
urllib3.disable_warnings()

#基础数据配置
class changConfig(object):
    def __init__(self):
        self.sqlc=sqlDeal()
        self.webcheckLimit = 3
        pass

    def randomHeaders(self):
        """
        随机返回headers
        :return:
        """
        pass

    def ipToProxies(self,ipline):
        """
        将ip处理为proxies
        :param ipline: [id,ipadress,port,webcheck]
        :return: [id,ipadress,port,webcheck,proxies]
        """
        iport = ipline[1] + ":" + str(ipline[2])
        proxies = {"http": iport, "https": iport}
        ipline.append(proxies)
        return ipline

    def getIpFromSql(self):
        """
        :return:{"status":,"ipGenerator:,"length":}
        """
        #入参sql查询类型，结果上限，网页代理验证失败次数
        #获取到的数据结构为((id,ipadress,port,webcheck,status),)
        results= self.sqlc.getIpList(choose=1, limit=10,webcheck=self.webcheckLimit)
        logging.debug(f"获取到的ip{results}")
        length = len(results)
        if length != 0:
            status=1
            ipGenerator = (list(x) for x in results)
        #没有符合条件的ip则报错，让程序停止
        else:
            status = -1
            ipGenerator = 0
        ipGeneratorD={"status":status,"ipGenerator":ipGenerator,"length":length}
        return ipGeneratorD

    def getUrlFromSql(self):
        """
        :return:{"status":,"urlGenerator:,"length":}
        """
        #入参sql查询类型，结果上限，网页代理验证失败次数
        #获取到的数据结构为((id,ipadress,port,webcheck),)
        results= self.sqlc.getUrlList(useTable="allurl", limit=10)
        logging.info(f"获取到的url{results}")
        length = len(results)
        if length != 0:
            status=1
            urlGenerator = (list(x) for x in results)
        #没有符合条件的ip则报错，让程序停止
        else:
            status = -1
            urlGenerator = 0
        urlGeneratorD={"status":status,"urlGenerator":urlGenerator,"length":length}
        return urlGeneratorD

#session处理
class mySession(object):
    def __init__(self):
        self.session=requests.Session()
        self.headers=""

    #替换默认的headers
    def changeHeaders(self):
        self.session.headers=self.headers

#通过源获取小说
class getBooknameFromSourse(object):
    def __init__(self):
        self.baseUrl=""
        self.session=requests_html.HTMLSession()
        self.headers=""
        self.sqlc=sqlDeal()
        self.source=changConfig()
        self.ips=self.source.getIpFromSql()
        self.urls=self.source.getUrlFromSql()

    #线程管理
    def startThread(self):
        t1 = Thread(target=self.coreThread,args=(1,))
        t2 = Thread(target=self.coreThread,args=(2,))
        t1.start()
        t2.start()


    #核心线程
    def coreThread(self,num):
        """
        :return:num
        """
        #线程初初始化session
        session=mySession().session

        #初始化ip和url，并赋值
        #{"status":,"urlGenerator:,"length":}
        if self.urls["status"] > 0 and self.ips["status"] > 0:
            urlline,ipline = next(self.urls["urlGenerator"]), next(self.ips["ipGenerator"])
            self.urls["length"],self.ips["length"]=self.urls["length"]-1,self.ips["length"]-1
            ipline = self.source.ipToProxies(ipline)
        else:return {"status":0}

        #线程任务循环
        while 1:
            logging.info(f"本次执行使用：{urlline} , {ipline} ")

            #获取执行结果
            results = self.checkError(session, urlline,ipline)
            print(results["message"])

            # #模拟网络请求结果
            # results={}
            # results["statusCode"] = random.choice([-1,-2,1])
            if results["statusCode"]==200:
                print(results["response"].text)
            else:print(results["message"])

            #根据请求结果更新url和ip，返回格式{"status":1,"message":"正常","ipline":"","urlline":""}
            mewIpAndUrl=self.updateUrlAndIp(results["statusCode"],ipline,urlline,num)
            if mewIpAndUrl["status"]==1:
                ipline,urlline=mewIpAndUrl["ipline"],mewIpAndUrl["urlline"]
            else:
                print(mewIpAndUrl["status"],mewIpAndUrl["message"])
                break

            time.sleep(1)

        #输出新获取到的url和正文
        #或者输出未解析的html，等待二次解析
        return


    #根据需求，遍历更新ip和url
    def updateUrlAndIp(self,statusCode,ipline,urlline,num):
        results,status ,message = {}, 1,"正常"
        if statusCode == -1:  # ip类异常
            #(id,ipadress,port,webcheck,status)
            # 旧ipline处理：webcheck+1后，存入sql
            oldIpLine = copy.deepcopy(ipline)
            oldIpLine[3] += 1
            if oldIpLine[3]>=self.source.webcheckLimit :oldIpLine[4]=0
            # 替换ip:从生成器区值，生成器无值则重新从sql获取，注意计数
            if self.ips["length"] == 0:  # 没有值则调用生成器获取
                self.ips = self.source.getIpFromSql()
                print("ips用完了")
                # 获取结果为0，则中断循环
                if self.ips["status"] == 0:
                    status = -1
                    message = "没有可用的ip"
            ipline = next(self.ips["ipGenerator"])
            self.ips["length"] = self.ips["length"] - 1
            results["ipline"] = self.source.ipToProxies(ipline)
            #将更改ip的状态
            print(oldIpLine)
            self.sqlc.updateIpStatus("iplog",oldIpLine[4],oldIpLine[3],oldIpLine[0])
        elif statusCode == -2:  # 模拟url异常
            # print(f"正常执行{ipline, urlline}")
            urlline = self._updateLine(urlline,kind=1)

        else:
            # print(f"正常执行{ipline, urlline}")
            urlline = self._updateLine(urlline,kind=2)

        results={"status":status,"message":message,"ipline":ipline,"urlline":urlline,}

        return results

    #urlline更新方法（防止维护麻烦，不处理ipline
    def _updateLine(self,urlline,kind):
        """
        :param urlline: [id, oldurl, used, black]
        :param kind:
        :return:
        """
        oldUrlLine = copy.deepcopy(urlline)
        #访问失败添加到黑名单
        if kind == 1:
            oldUrlLine[3] = oldUrlLine[3] - 1
        oldUrlLine[2] = oldUrlLine[2] - 1
        # 替换url:从生成器取值，生成器无值则重新从sql获取，注意计数
        if self.urls["length"] == 0:  # 没有值则调用生成器获取
            self.urls = self.source.getUrlFromSql()
            print(f"url用完了")
            # 获取结果为0，则中断循环
            if self.urls["status"] == 0:
                status = -2
                message = "没有可用的url"
        urlline = next(self.urls["urlGenerator"])
        self.urls["length"] = self.urls["length"] - 1

        #更新url状态[id, oldurl, used, black]
        logging.info(oldUrlLine)
        self.sqlc.updateUrlStatus(oldUrlLine[2],oldUrlLine[3],oldUrlLine[0])

        return urlline

    #异常处理
    def checkError(self,session,urlline,ipline):
        """
        :param urlline:[id,url,used,black]
        :param ipline:[id,ip,port,webcheck,proxies]
        :return:{"status":"","html":object}
        """
        #初始化结果
        results={"statusCode":1}
        try:
            response = session.get(url=urlline[1], proxies=ipline[-1], verify=False, timeout=10)
            # if end.text==ip[0]:
            logging.debug(f"**网页正文如下\n{response.text}**")
            #正常执行
            if response.status_code != 200:
                logging.debug(response.status_code)
                results["statusCode"] = response.status_code
                logging.info("statusCode不是200，请检查")
            else:
                results["response"]=response
            results["message"] = f"正常"
        except requests.exceptions.ProxyError as e:
            # 代理不可用
            results["statusCode"] = -1
            results["message"] = "代理不可用"
        except requests.exceptions.ConnectTimeout as e:
            # 链接代理超时
            results["statusCode"] = -1
            results["message"] = "链接代理超时"
        except requests.exceptions.ReadTimeout as e:
            # 链接、读取超时
            results["statusCode"] = -1
            results["message"] = "链接、读取超时"
        except requests.exceptions.ConnectionError as e:
            # 未知服务器
            results["statusCode"] = -1
            results["message"] = "未知服务器"
        except Exception as e:
            # 限定内的其他异常
            results["statusCode"] = -2
            results["message"] = f"其他异常\n{e}"
        finally:
            results["response"]=""
            logging.debug(results)
            #如果访问失败，考虑调用方法修改ip状态
            return results


    #获取页面所有url
    def letsDoIt(self,url):
        print("获取书籍列表")
        #使用代理方法，ip处理
        indexPage=requests.get(url,verify=False)

        #异常处理及bs化
        #ip失效，本网站被拉黑，500，403
        end=BeautifulSoup(indexPage.text,"lxml")

        #获取所有url
        alllink=end.find_all("a")
        newDict={}
        for line in alllink:
            name=line.get_text().strip()
            singlelink=line.attrs["href"]
            if "html" in  singlelink or len(name)<1 :
                continue
            if "biquge" in singlelink and len(singlelink)>22:
                pass
            elif "book"  in singlelink:
                singlelink = url+singlelink
            else:continue
            print(singlelink)
            print(name)
            newDict[name]=singlelink

        print(newDict)
        #调用sql方法存储到数据库



    #通过搜索获取
    def getToSearch(self,key):
        url=self.baseUrl+ "/searchbook.php"
        params={"keyword":f"{key}"}
        response = self.session.get(url,params=params)
        print(response.url)
        html=BeautifulSoup(response.text)
        step1 = html.find("div",{"class":"novelslist2"})
        results=step1.find_all("li")[1:]
        #没有找到小说
        if len(results)==0:return False
        novels=[]
        for line in results:
            new=[]
            print(line.get_text())
            for num in range(1,8):
                step = line.find("span", {"class": f"s{num}"})
                text = self.getText(step)
                new.append(text)
                if num == 2:
                    link = step.a.get("href")
                    new.append(link)
                elif num==3:
                    link = step.a.get("href")
                    new.append(link)
            novels.append(new)
        print(novels)
        return novels


    #页面文本处理
    def getText(self,bs):
        text=bs.get_text()
        text=text.strip()
        text=text.replace("[","").replace("]","")
        return text

class mocks():
    def test1(self):
        url1='https://www.dingdiann.com'
        url2="https://www.dingdiann.com/ddk_1/"
        url3="https://www.dingdiann.com/ddk3380/"
        url4="https://www.biquge98.com/"
        url5="https://www.biquge.lu"
        fool = getBooknameFromSourse()
        #获取指定小说
        # fool.getToSearch(url1)
        #通过入口url，按照层级遍历url
        # fool.coreThread()
        fool.startThread()

    def test3Ip(self):
        fool=getIpAndCheck()
        # iplist = fool.getAndlxml("https://www.kuaidaili.com/free/intr/",fool.funcA)
        # iplist=['121.69.10.62:9090', '183.247.152.98:53281', '223.82.106.253:3128','123.139.56.238:9999']
        # ss= fool.checkIp(iplist)
        # validIp=[{'ipAdress': '39.109.123.188', 'port': '3128', 'status': 1}, {'ipAdress': '222.94.196.241', 'port': '3128', 'status': 1}, {'ipAdress': '113.204.164.194', 'port': '8080', 'status': 1}, {'ipAdress': '222.94.196.138', 'port': '3128', 'status': 1}, {'ipAdress': '222.90.110.194', 'port': '8080', 'status': 1}, {'ipAdress': '190.122.186.222', 'port': '8080', 'status': 1}, {'ipAdress': '47.91.137.211', 'port': '3128', 'status': 1}, {'ipAdress': '183.196.170.247', 'port': '9000', 'status': 1}, {'ipAdress': '117.141.155.242', 'port': '53281', 'status': 1}]
        # fool.sqlAndSave(validIp)

        #废物代理网站
        # fool.getAndlxml("https://www.kuaidaili.com/free/inha/",fool.funcA)
        # fool.getAndlxml("https://www.kuaidaili.com/free/intr/",fool.funcA)
        #代理网站checkerproxy，大量ip，慢慢验证
        fool.getAndlxml("https://checkerproxy.net/api/archive/",fool.funcC)
        # fool.getAndlxml("http://www.goubanjia.com/",fool.funcB)
        # fool.getAndlxml("https://www.zdaye.com/",fool.funcC)

    def test4Sql(self):
        fool=sqlDeal()
        # fool.conectSql()
        # fool.selectNormal("*","iplog","")
        # print(fool.insertIgnore())

        # validIp = ['123.139.56.238:9999', '210.61.240.162:8080', '203.189.89.153:8080', '27.191.234.69:9999',
        #            '210.61.240.162:8080', '103.249.100.152:80', '121.89.194.145:3128', '117.141.155.244:53281',
        #            '222.249.238.138:8080', '101.36.160.87:3128', '118.163.13.200:8080', '124.205.155.158:9090',
        #            '47.56.9.58:3128']
        # fool.saveIp(validIp)
        # end=fool.duplicationIP("123.139.56.268")
        statusList=[(254, 0), (255, 0), (257, 0), (261, 0), (263, 0), (265, 0), (266, 0)]
        fool.updateIpListStatus(statusList)


    def testMain(self):
        IPs=getIpAndCheck()





if __name__=="__main__":
    mock=mocks()
    mock.test1()