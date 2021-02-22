#coding=utf8

"""
#澳洲金鼎并发脚本
"""


from concurrent.futures import ThreadPoolExecutor as Pool
import requests,random,lxml,time
from bs4 import BeautifulSoup


#起始进程数
startNum=100
#累加进程数
addNum=5
#跑批后休眠时间
sleepTime=2




class futures(object):
    def __init__(self):
        #基础地址
        self.indexUrl="http://112.74.129.135:8080/Erp_V0.1/admin/login/logout.php?tablefrom=1"
        #登录
        self.loginUrl="http://112.74.129.135:8080/Erp_V0.1/admin/login/tologin.php"
        #客户列表
        self.customer1="http://112.74.129.135:8080/Erp_V0.1/erp/cgcallorder/list.php"
        self.customer2=""
        #可用账户
        self.accountList=['scxcd66', 'scxcd66', 'jnxcd66', ' jnxcd67', 'xyxcd66', ' xyxcd67']
        # self.accountList=['chengdu096', 'chengdu033']
        self.char_dict={}

        self.pwd="fe008700f25cb28940ca8ed91b23b354"

        self.usrDict={}
        #客户跟进记录请求地址
        self.followUrl="http://192.168.0.8:8081/AustralianPlat/admin/customerfollow/saveOrUpdatefollow.jhtml"


    def task(self,url,timeout=80):
        try:
            account=self.accountList[random.randint(0,len(self.accountList)-1)]
            session=self.usrDict[account]
            response= session.get(url,timeout=timeout)
            sp=BeautifulSoup(response.text,"lxml")
            print("%s进入页面'%s'"%(account, sp.title.get_text()))
            if '澳洲金鼎'==sp.title.get_text():
                return -2
            qc=sp.find("tr",{"class":"onc_click"})
            if qc :
                # print(qc)
                zxc=qc.find_all("td",limit=2)
                print("获取客户id",zxc[1].get_text())
                custid=zxc[1].get_text()
                followtime=time.strftime("%Y/%m/%d %H:%M", time.localtime())
            else:
                print("%s 没有客户，剔除该测试用户"%(account))
                if account in self.accountList:
                    self.accountList.remove(account)
                return -1

            follow= {'custid': custid, 'followtime': followtime, 'contactway': '78', 'result': '123123123',
             'stage': '82', 'estate': '150', 'ismeet': '0', 'meetaddress': '', 'nextfollow': '2018-06-01',
             'followtype': '1'}
            results=session.get(self.followUrl,params=follow)
            print("%s跟进返回内容：%s"%(account,results.text))
            return response
        except requests.exceptions.ConnectTimeout as e:
            print("请求超时")
            return -1
        except requests.exceptions.ReadTimeout as e:
            print("%s建立连接超时" % e)
            return -1
        except Exception as e:
            print("%s请求发生错误" % e)
            return -1


if __name__=="__main__":
    num=startNum
    juice = futures()
    usrDict={}
    #按照用户列表，创建句柄字典
    for act in juice.accountList:
        session = requests.Session()
        session.get(juice.indexUrl)
        print(act,juice.pwd)
        accountData = {"account": act, "pwd": juice.pwd, "code": "1234","sysCode":"systemtwo"}
        response=session.get(juice.loginUrl, params=accountData)
        session.get("http://192.168.0.8:8081/AustralianPlat/plat/login/tomain.jhtml")
        usrDict[act]=session
    juice.usrDict=usrDict
    print("创建句柄字典完毕")
    #按要求生成进程，请求客户列表
    while 1 :
        x=0
        pool = Pool(max_workers=num)
        print("当前进程数%s"%num)
        urllist=("http://192.168.0.8:8081/AustralianPlat/admin/customer/query.jhtml,"*num).split(",")[:-1]
        results = pool.map(juice.task,urllist)
        timeList=[]
        for ret in results:
            if ret==-1:
                print("超出标准时间,当前用户数%s"%num)
                x+=1
            elif ret ==-2:
                x=len(juice.accountList)
            else:
                x=0
                print('%s, %ss' % (ret.url, ret.elapsed.total_seconds()))
                timeList.append(ret.elapsed.total_seconds())
        #失败比例
        if x/len(juice.accountList)>0.6 :
            print("超过60\%的请求超过标准时间")
            break
        else:
            print("当前进程数%s" % num)
        num+=addNum
        print("timeList",timeList)
        time.sleep(sleepTime)
    print("当前进程数%s"%num)
