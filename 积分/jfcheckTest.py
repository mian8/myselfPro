#coding=utf8

"""
测试环境
通过手机号验证用户的积分，剩余积分是否符合记录
"""


#调用高级方法
from functools import reduce
#调用bs网页解析方法
from bs4 import BeautifulSoup
#调用调试库，打印日志、时间控制
import logging,time
#调用请求库、页面解析模式
import requests,lxml
#Excel表格处理库：读、写
import xlrd,xlwt
#随机数
import random

#设置等级
logging.basicConfig(level= logging.WARN)


class jfCheckDemo(object):
    def __init__(self):
        #页面解析的用于处理验证码的基字符
        self.sCode = "A,B,C,D,E,F,G,H,J,K,L,M,N,P,Q,R,S,T,U,V,W,X,Y,Z,1,2,3,4,5,6,7,8,9".split(",")
        #设置每次验证间隔的随机时间、单位秒
        self.waitsecond= [0.005,0.001]

    def makeCodeAndpPost(self):
        """
        生成验证码
        :return:返回一个符合规则的验证码
        """
        code = "".join(random.sample(self.sCode,4)).replace(",","")
        return code

    def login(self,name,pwd):
        """
        登录方法，返回的session直接用于登录后积分验证
        :param name: 账号
        :param pwd: 密码
        :return:已登录的session
        """
        session=requests.Session()
        session.get("https://jftest.jindingtimes.com/Admin/Index/login")
        #该项目的验证码来自前端随机生成，然后发送到服务器
        code=self.makeCodeAndpPost()
        session.post("https://jftest.jindingtimes.com/Admin/Index/saveCode",data={"code":code})

        #验证当前发送的验证码与之前发送的验证码一致
        params={"username":name,"password":pwd,"code":code}
        session.post("https://jftest.jindingtimes.com/Admin/Index/checkLogin",data=params)
        session.get("https://jftest.jindingtimes.com/Admin/Index/index")
        return session

    def getMemberjf(self,session,phone):
        """
        爬虫主方法，用于获取总积分、积分明细list、系统赠送明细list
        :param session:可用的session
        :param phone:待验证手机号
        :return:包含积分明细list、系统赠送明细list的元组 (list,list)
        """
        #进入会员列表
        session.get("https://jftest.jindingtimes.com/Admin/Member/index")
        #搜索指定会员
        searchParams={'search_type': 'phone', 'keyword': phone, 'min_integral': '', 'max_integral': '', 'start_time': '', 'end_time': '', 'sort_by': '', 'order_by': '', 'p': '1'}
        codejson=session.post("https://jftest.jindingtimes.com/Admin/Member/search",data=searchParams).json()
        #获取会员id，用于进入积分明细和系统赠送明细页面，顺便将总积分保存到对象
        id = self.getCanUse2(phone,codejson)
        page1=session.get("https://jftest.jindingtimes.com/Admin/Member/desc_list/id/{}/type/1".format(id))
        page2=session.get("https://jftest.jindingtimes.com/Admin/Member/desc_list/id/{}/type/3/back_page/1".format(id))
        #解析页面，获取积分明细list、系统赠送明细list
        jf1=self.dealHtml(page1.text)
        jf2=self.dealHtml(page2.text)
        logging.info(jf1)
        logging.info(jf2)
        return jf1,jf2

    def dealHtml(self,html):
        """
        积分页面解析通过方法
        :param html: 积分列表页面的html
        :return:积分list：-2定位失败，2列表没有积分记录，-1解析积分异常
        """
        #将页面处理为bs对象
        html = BeautifulSoup(html, "lxml")
        logging.debug(html)
        #获取页面class为table table-striped b-light的所有table标签
        tables = html.find_all("table", {"class": "table table-striped b-light"})
        logging.debug(tables)
        #从第一个table中获取tbody标签
        tbody=tables[0].find("tbody")
        logging.debug(tbody)
        #获取积分list
        jfLict = []
        if tbody is None:#获取积分列表失败
            logging.warning("没有定位到目标位置")
            jfLict=-2
        else:
            try:
                tdLines = tbody.find_all("tr")
                #列表没有找到积分记录
                if len(tdLines)<2 and "没有找到相关数据" in tdLines[0].get_text():
                    jfLict=["0"]
                else:
                    #从第二行开始，每个tr的第三个td标签为积分值
                    for line in tdLines[0:]:
                        thValues = line.find_all("td")
                        jfchange = thValues[2].string#通过string属性或者get_text方法可以获取文本
                        #干掉文本中所有的额\n\s\r
                        jfLict.append(jfchange.replace(" ","").replace("\r","").replace("\n",""))
            except Exception as e:
                logging.warning(e)
                jfLict=-1
        #只能验证有积分的页面，且积分记录页面仅检查一页，多于1页的积分记录为手动验证
        if jfLict !=["0"]:
            #页码标签直接获取不到，只能获取全部后取第一个
            ul = html.find_all("ul",{"class":"pagination pagination-sm m-t-sm m-b-none"})
            page=ul[0].get("data-pages-total")#获取总页数
            if int(page)>1:
                jfLict = -2
            else:logging.info("这个列表只有{}页".format(page))
        return jfLict

    def getCanUse2(self,phone,jscontent):
        """
        #获取总积分和会员id
        :param phone:客户手机号
        :param jscontent:存放于json中的页面
        :return:会员id
        """
        #取出content中的带解析页面
        content=jscontent["content"]
        #拆分为标题和多列会员信息
        asdkji = content.split("</a>")
        #统计有多少列包含了该手机号
        num = 0
        for line in asdkji:
            if phone in line:num+=1
        #首条为标题，解析第二条（排第一的会员）
        html = BeautifulSoup(asdkji[1], "lxml")
        #获取所有包含指定属性的tr标签
        tr = html.find_all("tr",{"style":"text-align: center"})
        #获取所有的td标签
        td = html.find_all("td")
        #如果手机搜索出来的客户多于两条，记录为手动验证；否则获取总积分
        if num>=2:
            self.count=False
        else:
            self.count=td[6].get_text()
        #获取会员id，通过get方法获取标签中的指定属性
        td=html.find("input",{"name":"ids"})
        end=td.get('value')
        return end

    @staticmethod
    def add(a,b):
        c =int(a)+int(b)
        return int(c)

    def mainF(self,phoneL):
        """
        主方法，遍历传入的手机号列表
        :param phoneL:手机号列表
        :return:
        """
        #登录积分平台
        session= self.login("xcd","1234567a")
        results=[]
        #判断进度
        stopPonit=self.getStopPonit()#上次最后一条测试手机号
        if stopPonit and len(phoneL)>220:#获取断点的条件：获取到了上次手机号且传入的手机号列表大于220
            phone=stopPonit.split(" ")[0]
            num = phoneL.index(phone)
            phoneL=phoneL[num+1:]
        #开始遍历手机号
        for p in phoneL:
            #随机间隔时间
            second= random.choice(self.waitsecond)
            time.sleep(second)
            #清除手机号前后空格
            p=p.strip()
            logging.info(p)
            #获取积分明细list、系统赠送明细list
            jf1, jf2= self.getMemberjf(session,p)
            #异常处理
            if self.count==False: end = "该手机号查出多条客户"
            elif jf1==-1 or jf2==-1: end = "数据获取异常"
            elif jf1==-2 or jf2==-2: end = "积分明细或系统赠送有翻页，建议手动处理"
            else:
                #求和
                part1=reduce(self.add,jf1)
                part2=reduce(self.add,jf2)
                #计算积分结果
                end = int( self.count) - int(part1) -int(part2)
            logging.info(end)
            print("%%%%%%%\n"+p+"  "+str(end)+"\n%%%%%%%%")
            #每次追加记录
            with open("jfFile.txt", "a+", encoding="utf8") as f:
                f.write(p+" "+str(end)+"\n")
            results.append((p,end),)
        #将最终结果记录于Excel
        self.write_excel(results)



    def sheetRead(self):
        """
        表格读取
        :return: 读取指定文件的第一列，输出列表
        """
        workbook = xlrd.open_workbook(r'E:\F\myselfPro\积分\start\数据校验.xls')
        sheet1 = workbook.sheet_by_index(0)
        #显示行与列的数量
        print(sheet1.nrows,sheet1.ncols)
        #获取单行值
        # phone=sheet1.cell_value(1,0)
        phoneList = [str(sheet1.cell_value(i, 0)) for i in range(0, sheet1.nrows)]
        # phoneList=list(set(phoneList))
        # print("去重后列表还剩{}".format(len(phoneList)))
        return phoneList

    def set_style(self,name,height,bold=False):
        """
        设置表格样式
        :param name:
        :param height:
        :param bold:
        :return:
        """
        style = xlwt.XFStyle()  # 初始化样式

        font = xlwt.Font()  # 为样式创建字体
        font.name = name  # 'Times New Roman'
        font.bold = bold
        font.color_index = 4
        font.height = height
        style.font = font
        # style.borders = borders

        return style

    #读取拼接的验证结果文本（txt）
    def readIt(self):
        """
        :return:[(phone,status)]
        """
        fileAdress=r"E:\F\myselfPro\积分\jfFile.txt"
        with open(fileAdress,"r",encoding="utf8") as f:
            text=f.readlines()
        allLines=[]
        for line in text:
            phone,status=line.split(" ")[0],line.split(" ")[1].replace("\n","")
            newline=(phone,status)
            allLines.append(newline)
        # print(allLines)
        return allLines

    #获取当前已验证的手机号
    def getStopPonit(self):
        fileAdress=r"E:\F\myselfPro\积分\jfFile.txt"
        with open(fileAdress,"r",encoding="utf8") as f:
            text=f.read()
        text=text.split("\n")
        if "" in text: text.remove("")
        if "\n" in text:text.remove("\n")
        if not text:return None
        back=text[-1]
        return back


    def write_excel(self,phoneList):
        """
        将结果写入Excel表
        :param phoneList:[(phone,status)]
        :return:
        """
        f = xlwt.Workbook()  # 创建工作簿
        '''
        创建第一个sheet:
          sheet1
        '''
        sheet1 = f.add_sheet('sheet1', cell_overwrite_ok=True)  # 创建sheet
        # 生成第一行
        print(phoneList)
        for i in range(0, len(phoneList)):
            #sheet1.write(行，列，值)
            phoneANDstatus = phoneList[i]
            print(phoneANDstatus)
            sheet1.write(i,0,phoneANDstatus[0],self.set_style('Times New Roman', 220, True))
            sheet1.write(i,1,phoneANDstatus[1],self.set_style('Times New Roman', 220, True))

        f.save('demo2.xlsx')  # 保存文件

    def check(self):
        #获取总的phone和已验证的phone
        list1=self.sheetRead()
        list2=self.readIt()
        list2=[x[0] for x in list2 ]
        #记录缺失的手机号
        lost=[]
        for phone in list1:
            if phone not in list2:
                lost.append(phone)
        print(lost)
        return (lost)

    def sortIt(self):
        #获取总的phone和已验证的phone
        list1=self.sheetRead()
        list2=self.readIt()
        #将已验证的手机号处理为字典{手机号:验证结果}
        dict2={x[0]:x[1] for x in list2 }
        lost=[]
        #排序
        for phone in list1:
            if phone in dict2.keys():
                lost.append((phone,dict2[phone]),)
        print(lost)
        return (lost)



if __name__ == '__main__':
    fool=jfCheckDemo()
    """
    特殊数据
    #消费记录存在翻页
    13829798308
    #多个搜索结果
    13606020202
    """

    # phoneList=fool.sortIt()
    # phoneList=fool.sheetRead()
    # phoneList=['13600850357', '13960065580', '13817636515', '13325119509', '18822890823', '13701724593', '15900769393', '15859000142', '13908233216', '15336748599', '13585342323', '13817388900', '18629695111', '15801761578', '13829130318', '15921039110', '13305360979', '13328861060', '13313851057', '13908308362', '13971565411', '15810100100', '18805928883', '13909856677', '13929553331', '18702181535', '13813137331', '13600869702', '13907002255', '13328106256', '13916039027', '13788917812', '13806064588', '13515059308', '13901839194', '13918180331', '13601786695', '13716228686', '15238218688', '18505086565', '13754202000', '13501711174', '13801826705', '13918098558', '13905798226', '13764196906', '15905311778', '18805325327', '13808879007', '18665855888', '13916904286', '13701869509', '13681818088', '13321808572', '18554828888', '13601212293', '13795265906', '15901202301', '18660266166', '13829981796', '13916833788', '13901200035', '13764215484', '13764730260', '18610557819', '15201547339', '13894855686', '15279115856', '13716971100', '13827066000', '13801213783', '13382581099', '18657960822', '13660730065', '13511011299', '13802581804', '13651143006', '13373644656', '17727850097', '13764399988', '13901048880', '13816334456', '13808190536', '18676832616', '16601166529', '15801082888', '13753112345', '13636655229', '13901480840', '13811098277', '18651646656', '13566522626', '13837888808', '15121088018', '18607147881', '13860677076', '18611423858', '13807196029', '13904733482', '15921922492', '13574124165', '13634110290', '13575898732', '13574199907', '18616806878', '13810878017', '13521032377', '13320231866', '13805056817', '13600570578', '15562551158', '13529194278', '18173573666', '15859258272', '15828243810', '13801561938', '13313771888', '15372403302', '17767262509', '0406633483', '13764301376', '13819885892', '13696870304', '13950107606', '13715262072', '15827357886', '13651999081', '13770267768', '15618795787', '13806025900', '13615289558', '15868106268', '13911041993', '15998155144', '13508370608', '13173230613', '13917277268', '13556161898', '8618688787022', '0481206159', '18615277860', '18573114599', '13668077232', '13817450819', '18203996669', '18062595566', '18339918126', '18929522566', '13611934279', '13703512539', '18665355693', '13600904892', '13616006272', '13681666611', '13546371780', '13917895232', '15967567116', '13868087928', '13508620297', '18069081122', '18605111188', '13162956126', '13881965626', '13901491351', '13767659888', '13910115849', '15853226800', '13801263164', '13816399251', '13506987131', '13860115777', '18669797767', '13917534666', '18620102890', '13818972982', '15060067960', '13314935158', '15108333338', '13948058181', '13808609292', '13918166812', '13277098784', '13801698703', '13811553293', '13505408282', '13960779988', '13601781615', '13953220808', '13822832345', '13857378222', '18668111211', '13901287646', '13707043999', '13435108388', '13986160751', '13608329245', '13834699899', '15384014124', '18959282086', '13970003685', '13850121327', '13305361716', '13926152980', '17628049160', '17628049160']
    phoneList=['18900560018',
 '18900560017',
 '18900560016',
 '18900560015',
 '17818015999',
 '17818015998',
 '17818015997',
 '17818015996',
 '17818015995',
 '17818015994']

    fool.mainF(phoneList)

    # phoneList=fool.readIt()
    # fool.write_excel(phoneList)
