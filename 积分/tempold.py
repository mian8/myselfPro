# coding=utf8

"""
核对静态认购单积分与管家中心一致
1.核算认购单应该获取的积分(客户crmcode、phone，total)
2.查找管家中心该认购单相关积分记录(不在本方法中实现)
"""

import pymysql
from functools import reduce
import logging, json, time, random
from selenium import webdriver
from dbutils.pooled_db import PooledDB, SharedDBConnection
from bs4 import BeautifulSoup
import string, os
import hashlib
import requests, lxml, re, subprocess, pymysql, requests_html
import xlrd, xlwt

logging.basicConfig(level=logging.INFO)


class baseFunc(object):
    # 将获取到的字符串转化为unicode码
    def get_code(self, line):
        # 没有字典则生成字典
        self.make_dict()
        # 将账号密码转为unicode码
        # 按字典转换
        if isinstance(line, dict):
            new_data = {}
            new_data["code"] = line["code"]
            new_data["account"] = self.get_code(line["account"])
            new_data["pwd"] = self.get_code(line["pwd"])
        else:  # 按字符串转换
            new_data = ""
            for ch in line:
                c = self.char_dict[ch]
                new_data += c
        # print("*"*10,"\n",new_data)
        return new_data

    # 接收两个相同长度列表列表进行整理
    def make_dict(self, chars="", code=""):
        # 默认字典
        if chars == "":
            chars = r"·1234567890~!@#$%^&*()_+qwertyuiop[]\{}|asdfghjkl;':zxcvbnm,./<>?"
        if code == "":
            code = r"\u00b7\u0031\u0032\u0033\u0034\u0035\u0036\u0037\u0038\u0039\u0030\u007e\u0021\u0040\u0023\u0024\u0025\u005e\u0026\u002a\u0028\u0029\u005f\u002b\u0071\u0077\u0065\u0072\u0074\u0079\u0075\u0069\u006f\u0070\u005b\u005d\u005c\u007b\u007d\u007c\u0061\u0073\u0064\u0066\u0067\u0068\u006a\u006b\u006c\u003b\u0027\u003a\u007a\u0078\u0063\u0076\u0062\u006e\u006d\u002c\u002e\u002f\u003c\u003e\u003f"
        # 删除回车，生成unicode码列表
        new_code = code.replace('\\u000a', '').replace("\\", "#\\")[1:].split('#')
        # 生成字典
        char_dict = {}
        for num in range(len(new_code)):
            char_dict[chars[num]] = new_code[num]
        # print(char_dict)
        # 将字典绑定到方法
        self.char_dict = char_dict
        return char_dict


class jfDemo(baseFunc):
    def __init__(self):

        self.baseurl_1="http://112.74.129.135:8180/AustralianPlat/"
        self.baseurl_2 = "http://47.75.253.20:9100/api/"

        # self.baseurl_1 = "http://120.25.85.101/AustralianPlat/"
        # 认购单详情
        self.url = self.baseurl_1 + "sub/api/loadEdit.jhtml"
        # 优惠信息
        url = self.baseurl_2 + "subscription/queryDiscountList"
        # 时间变更
        url = self.baseurl_2 + "subscription/getDcSubLog"
        # 信息维护
        url = self.baseurl_2 + "subscription/getChangeLog"
        # 缴费信息
        url = self.baseurl_2 + "subscription/voucher"
        # 认购通知单详情
        url = self.baseurl_2 + "subscription/getSubInfoById"
        self.address = "./temp/"

    def crm_login(self, name, pwd):
        """
        澳洲CRM登陆
        :param name: 账号
        :param pwd: 密码
        :return: session
        """
        session = requests.Session()
        session.get(self.baseurl_1 + "login.jsp")
        end = session.post(self.baseurl_1 + "random/createCode.jhtml")
        logging.info(end.json())
        code = end.json()["data"]
        # 将密码先md5处理
        pwd = hashlib.md5(pwd.encode(encoding='utf8')).hexdigest()
        user = {"account": f"{name}", "pwd": f"{pwd}", "code": f"{code}"}
        usr = self.get_code(user)
        session.headers["Referer"] = self.baseurl_1 + "login.jsp"
        end = session.post(self.baseurl_1 + "plat/login/tologin.jhtml", data=usr)
        # session.get(self.baseurl_1+"plat/login/tomain.jhtml")
        logging.info(usr)
        logging.info(end.json())
        return session

    def getmessage(self, session):
        end = session.post(url=self.url, data={'SubId': '256'})
        myMsg = {}
        subjson = end.json()
        subData = subjson["data"]
        myMsg["firstpaystate"] = subData["firstpaystate"]
        myMsg["status"] = subData["status"]

        for msg in subData.items():
            print(msg)


    # 逐条将认购单存储到txt文件
    def saveSubIdLIst(self, SubIdDict):
        address = self.address + "/SubIdLIst.txt"
        # 文件存在则删除
        jsonMsg = json.dumps(SubIdDict, ensure_ascii=False)
        with open(address, "a+", encoding="utf8") as file:
            file.write(jsonMsg + "\n")

    # 获取客户手机号和crmCode
    def customerid(self, session, code):
        url = self.baseurl_1 + f"admin/customer/edit.jhtml?customerid={code}&opt=detail&position=info&paramType=6"
        end = session.get(url)
        page = BeautifulSoup(end.text, "lxml")
        phone = page.find("input", {"id": "customer_phone"})
        crmCode = page.find("div", {"class": "col-xs-3 col-sm-3 col-md-3 text-right"})
        crmCode=crmCode.get_text().strip()
        try:
            superCode=page.find("div",{"id":"customer_supercustid"})
            superphone,superCrmCo = self.getSuperCus(session,superCode)
            print(f"推荐人内部id{superCode}，推荐人外部id{superCrmCo}，推荐人手机号{superphone}")
        except Exception as e:
            print(page.find("div",{"id":"customer_supercustid"}))
        return phone.get("value"),crmCode

    def getSuperCus(self,session,superCode):
        superurl = self.baseurl_1 + f"admin/customer/edit.jhtml?customerid={superCode}&opt=detail&position=info&paramType=6"
        end = session.get(url)
        page = BeautifulSoup(end.text, "lxml")
        phone = page.find("input", {"id": "customer_phone"})
        crmCode = page.find("div", {"class": "col-xs-3 col-sm-3 col-md-3 text-right"})
        crmCode = crmCode.get_text().strip()
        return phone.get("value"),crmCode


    # 获取认购单基本信息
    def getSubId(self, session, pageSize=10, pageNum=2):
        index = self.baseurl_1 + "admin/dcSubscription/querylist.jhtml"
        pageParams = {'searchtime_type': 'subdate', 'startTime': '', 'endTime': '', 'searchType': '0', 'keys': '',
                      'totalStart': '', 'totalEnd': '', 'search_city': '0', 'search_region': '', 'search_team': '',
                      'search_status': '', 'search_paystate': '', 'search_transactionForm': '', 'search_substate': '',
                      'search_cooperate': '', 'search_firststate': '', 'search_pause': '', 'urlType': '5', 'opt': '',
                      'userid': '959', 'premisesid': '', 'pageSize': f'{pageSize}', 'pageNum': f'{pageNum}'}
        end = session.post(index, pageParams)
        page = BeautifulSoup(end.text, "lxml")
        allsub = page.find("tbody")
        thisPage = []
        for line in allsub.find_all("tr"):
            cusMsgOutside, cusMsgInside = {}, {}
            num, newKeys = 0, []
            keys = line.find_all("td")
            for key in keys:
                newKeys.append(key.get_text().strip().replace("\n", ""))
                num += 1
            # cusMsgInside["code"],cusMsgOutside["认购单号"]=newKeys[2],newKeys[2]
            cusMsgInside["cusname"], cusMsgOutside["买家姓名"] = newKeys[3], newKeys[3]
            cusMsgInside["cuslink"], cusMsgOutside["买家详情"] = keys[3].a.get("href")[21:-2], keys[3].a.get("href")[21:-2]
            cusMsgInside["phone"], cusMsgOutside["买家电话"] = newKeys[4], newKeys[4]
            # cusMsgInside["yddata"], cusMsgOutside["预定日期"]=newKeys[5],newKeys[5]
            # cusMsgInside["qydata"], cusMsgOutside["签约日期"]=newKeys[6],newKeys[6]
            cusMsgInside["sfqdata"], cusMsgOutside["首付齐日期"] = newKeys[7], newKeys[7]
            cusMsgInside["cjdata"], cusMsgOutside["成交日期"] = newKeys[8], newKeys[8]
            cusMsgInside["proname"], cusMsgOutside["项目名称"] = newKeys[9], newKeys[9]
            cusMsgInside["houseNum"], cusMsgOutside["房号"] = newKeys[10], newKeys[10]
            cusMsgInside["total"], cusMsgOutside["总价(澳元)"] = newKeys[11], newKeys[11]
            # cusMsgInside["saleman"], cusMsgOutside["销售员工"]=newKeys[12],newKeys[12]
            # cusMsgInside["point"], cusMsgOutside["回款比例"]=newKeys[13],newKeys[13]
            # cusMsgInside["regin"], cusMsgOutside["区域"]=newKeys[14],newKeys[14]
            # cusMsgInside["team"], cusMsgOutside["部门"]=newKeys[15],newKeys[15]
            cusMsgInside["substatus"], cusMsgOutside["成交状态"] = newKeys[16], newKeys[16]
            cusMsgInside["paystats"], cusMsgOutside["缴费状态"] = newKeys[17], newKeys[17]
            cusMsgInside["payendtime"], cusMsgOutside["尾款齐日期"] = newKeys[18], newKeys[18]
            # cusMsgInside["creatman"], cusMsgOutside["认购负责人"]=newKeys[19],newKeys[19]
            cusMsgInside["housetype"], cusMsgOutside["房源类型"] = newKeys[20], newKeys[20]
            cusMsgInside["status"], cusMsgOutside["认购状态"] = newKeys[21], newKeys[21]
            cusMsgInside["detaillink"], cusMsgOutside["详情"] = keys[22].a.get("href"), keys[22].a.get("href")
            cusMsgInside["usrcode"] = cusMsgOutside["澳洲客户编号"] = \
            keys[3].a.get("href")[21:-2].split("?")[-1].split("&")[0].split("=")[-1]
            cusMsgInside["subId"] = cusMsgOutside["认购单号"] = \
            keys[22].a.get("href").split("?")[-1].split("&")[0].split("=")[-1]
            """
            #维护不是必要字段
            if "维护" in keys[22].get_text():
               cusMsgInside["edit"], cusMsgOutside["维护"]=keys[22].contents[3].get("href")[21:-2],keys[22].contents[3].get("href")[21:-2]
            """
            # 更新手机号
            if cusMsgInside["usrcode"]:
                cusMsgInside["phone"],cusMsgInside["crmCode"] = self.customerid(session, cusMsgInside["usrcode"])
            else:cusMsgInside["crmCode"]=-1
            thisPage.append(cusMsgInside)
            # 添加到表中
            self.saveSubIdLIst(cusMsgInside)
            # print(cusMsgInside)
        Numb = len(allsub.find_all("tr"))
        logging.info("第{}页 本业认购单数 {} ##每页获取条数 {} ##保存到的认购单数 {}".format(pageNum, Numb, pageSize, len(thisPage)))
        return thisPage, Numb == pageSize

    # 遍历认购列表，组装成认购单列表
    def getAllSubId(self):
        session = self.crm_login("gxcd", "1234567a")
        pageNum = 1
        subList = []
        while 1:
            results = self.getSubId(session, pageNum=pageNum)
            subList.extend(results[0])
            logging.debug(results)
            if not results[1]:
                break
            else:
                print("第{}页".format(pageNum))
            pageNum += 1

        return subList

    def getSubIdFromTxt(self):
        address = self.address + "/SubIdLIst.txt"
        with open(address, "r", encoding="utf8") as file:
            SubIdJson = file.read()
        SubIdList = []
        for line in SubIdJson.strip().split("\n"):
            SubIdDict = json.loads(line)
            SubIdList.append(SubIdDict)
        return SubIdList

    # 是否首付齐，积分档位
    def isFirstpaystate(self, session, subId):
        url = self.baseurl_2 + f"subscription/voucher?subId={subId}"
        end = session.get(url).json()
        payStatus = end["data"]["payStatus"]
        totalpice = self.totalpice = end["data"]["totalpice"]
        logging.debug("{} {}".format(totalpice, payStatus))
        # 首付齐
        if payStatus > 2:
            payStatusMultiple = 1
        else:
            payStatusMultiple = 0
        # 积分档位
        if 0 < totalpice <= 700000:
            totalJF = 17500
        elif 700000 < totalpice <= 1000000:
            totalJF = 25000
        elif totalpice > 1000000:
            totalJF = 35000
        else:
            totalpice = False
        return totalJF, payStatusMultiple

    # 是否项目类型、房屋性质
    def houseType(self, session, subId):
        url = self.baseurl_2 + "subscription/getSubInfoById"
        params = {"subid": f"{subId}", "subsource": "1"}
        end = session.post(url, data=params).json()
        premisesType = end["data"]["propertyinfo"]["premisesType"]
        nature = end["data"]["propertyinfo"]["nature"]
        logging.debug("{} {}".format(premisesType, nature))
        # 是房地则折半，非房地为1
        if premisesType == 2:
            premisesTypeMultiple = 0.5
        else:
            premisesTypeMultiple = 1
        # 1,3为提名房，积分折半
        if nature == 1 or nature == 3:
            natureMultiple = 0.5
        else:
            natureMultiple = 1
        return premisesTypeMultiple, natureMultiple

    # 优惠券
    def queryDiscountList(self, session, subId):
        """
        优惠券为有效优惠，则按照占比折扣积分
        :param j:优惠券json
        :param total:合同总价
        :return: 优惠比例
        """
        url = self.baseurl_2 + "subscription/queryDiscountList"
        params = {"subid": f"{subId}"}
        end = session.post(url, data=params).json()
        totalQuery = end["data"]["totalvalue"]
        scale = (totalQuery / self.totalpice * 100).__round__(3)
        # 根据优惠折扣
        if scale == 0:
            queryMultiple = 1
        elif 0 < scale <= 1:
            queryMultiple = 0.5
        elif scale > 1:
            queryMultiple = 0
        else:
            queryMultiple = False
        logging.debug("优惠占比折扣{}".format(scale))
        return queryMultiple

    # 房屋交割（领取钥匙）
    def isGetKeys(self,session, subId):
        return True

    #认购单详情
    def subdetil(self,session, subId,usrcode,substatusO,statusO):
        status={"0":"退订", "1":"正常","2":"退房"}
        state = {'1': '正常', '2': '退房', '3': '换房', '4': '更名', '5': '换房中', '6': '退房中', '7': '交割违约'}
        allSubstatus={'1': '预订中', '2': '签约中', '3': '公寓交割中', '4': '交房', '5': '已预订', '6': '已签约', '7': '公寓交割完成', '8': '土地交割中', '9': '土地交割完成', '10': '建筑交割中', '11': '建筑交割完成'}
        url = self.baseurl_1 + "sub/api/loadEdit.jhtml"
        params = {"subid": f"{subId}"}
        end = session.post(url,data=params).json()
        substatusI=end["data"]["substatus"]
        #让我看看谁不一样啊
        if substatusO != allSubstatus[str(substatusI)]:print(substatusO, allSubstatus[str(substatusI)])
        #房屋交割积分补发
        if substatusI==11:isFdMultiple=1
        else:isFdMultiple=0
        #认购状态
        if statusO in ["退房","转提名","交割违约"]:statusMultiple=0
        elif statusO in ["正常","转提名","交割违约"]:statusMultiple=1
        else:statusMultiple=-1
        logging.debug(f"成交状态 {substatusO} 认购状态 {statusO}")
        return isFdMultiple,statusMultiple


    def mainF(self, name, pwd, SubIdLIst=""):
        """
        :param name:登录账号
        :param pwd:密码
        :param SubIdLIst:待验证的认购单列表
        :return:
        """
        session = self.crm_login(name, pwd)
        num=0
        for subId in SubIdLIst:
            num+=1
            print(100*"#")
            print(subId["phone"],subId["subId"])
            # print(subId["subId"],subId["crmCode"],subId["usrcode"])
            start = 1
            #认购状态：是否发送积分、成交状态：是否需要补发
            isFdMultiple,statusMultiple =  self.subdetil(session,subId["subId"],subId["usrcode"],subId["substatus"],subId["status"])
            # 合同金额、首付齐
            totalJF, payStatusMultiple = self.isFirstpaystate(session, subId["subId"])
            if payStatusMultiple == 1:
                # 项目类型、房屋性质
                premisesTypeMultiple, natureMultiple = self.houseType(session, subId["subId"])
                # 优惠
                queryMultiple = self.queryDiscountList(session, subId["subId"])
                # 建筑交割，旧数据没有领取钥匙是时间，不从领取钥匙判断
                # self.isGetKeys(session, subId["subId"])
                endPoint = int(
                    start * statusMultiple * totalJF * payStatusMultiple * premisesTypeMultiple * natureMultiple * queryMultiple)
                #交割补齐积分
                followPoint=endPoint * isFdMultiple
                allPoint=endPoint+followPoint
                if premisesTypeMultiple==0.5:
                    print(f"{subId['houseNum']} 应得积分 {allPoint} = 积分档位{totalJF} X 认购状态{isFdMultiple} X 首付齐状态{payStatusMultiple} X 项目类型{premisesTypeMultiple} X 房屋性质{natureMultiple} X 优惠折扣{queryMultiple} + 房屋交割{followPoint}")
                elif premisesTypeMultiple==1:
                    print(f"{subId['houseNum']} 应得积分 {allPoint} = 积分档位{totalJF} X 认购状态{isFdMultiple} X 首付齐状态{payStatusMultiple} X 项目类型{premisesTypeMultiple} X 房屋性质{natureMultiple} X 优惠折扣{queryMultiple}")


            else:
                endPoint = 0
                print(f"未达成积分获取条件")
            if num>1000:
                break



if __name__ == "__main__":
    fool = jfDemo()
    # 获取所有认购单
    # if os.path.exists(fool.address+"/SubIdLIst.txt"):os.remove(fool.address+"/SubIdLIst.txt")
    # SubIdLIst=fool.getAllSubId()


    SubIdLIst = fool.getSubIdFromTxt()
    fool.mainF("gxcd", "1234567a", SubIdLIst)
