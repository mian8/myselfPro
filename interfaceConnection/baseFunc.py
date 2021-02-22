#coding=utf8

#澳洲CRM登陆流程
#输入账号密码，md5处理密码，unicode化账号密码，获取code，登陆

import requests,hashlib,json

class proTotal():
    def __init__(self):
        self.tologin = "http://112.74.129.135:8180/AustralianPlat/plat/login/tologin.jhtml"
        self.tomain = "http://112.74.129.135:8180/AustralianPlat/plat/login/tomain.jhtml"
        self.save = "http://112.74.129.135:8180/AustralianPlat/admin/customer/save.jhtml"
    # 单字符转unicode
    def charToUnic(self, ch):
        tmp_ch = hex(ord(ch))[2:]
        return "0" * (4 - len(tmp_ch)) + tmp_ch

    #字符串转unicode字符串
    def dealNumOrChar(self, strs):
        #仅中文处理
        #"lyqy".encode('unicode_escape').decode()
        newline = ""
        for zchr in list(strs):
            newchar = self.charToUnic(zchr)
            newline = newline + r"\u" + newchar
        return newline

    #字符串md5处理
    def dealMd5(self,strs):
        m = hashlib.md5()
        b = strs.encode(encoding="utf8")
        m.update(b)
        str_md5 = m.hexdigest()
        return str_md5

    #澳洲CRM账号密码处理
    def CRMuser(self,userMsg):
        userMsg["account"]=self.dealNumOrChar(userMsg["account"])
        userMsg["pwd"]=self.dealNumOrChar(self.dealMd5(userMsg["pwd"]))
        return userMsg

    #获取code，登陆
    def CRMlogin(self,params):
        session=requests.Session()
        code=session.post(url="http://112.74.129.135:8180/AustralianPlat/random/createCode.jhtml")
        if code.status_code>200:
            print(f"凉了哦，code.status_code：{code.status_code}")
            return ""
        params["code"]=code.json()["data"]
        back=session.post(url=self.tologin,params=params)
        msg=json.loads(back.text)
        if msg["flag"]!=1:
            print(f"登陆失败:\n{msg}")
            return False
        else:
            print(f"{params['account']},登录成功")
            return session

    #获取code
    def get_code(self):
        session = requests.Session()
        back = session.post(url="http://112.74.129.135:8180/AustralianPlat/random/createCode.jhtml")
        code = back.json()["data"]
        print(code)


if __name__=="__main__":
    deal=proTotal()
    quser = {"account": "lyqy", "pwd": "1234567a"}
    params=(deal.CRMuser(quser))
    print(params)
    print(deal.CRMlogin(params))