#coding=utf8

"""
连接池
用于小说爬取的sql处理方法
方法由三层构成
1.外层接收需要处理的列表/字典
2.辅助层处理基本的sql语句
3.内层循环执行拼接的sql语句
"""
from dbutils.pooled_db import PooledDB
import pymysql
import logging
import warnings
import datetime

logging.basicConfig(level=logging.INFO)


#直接写死方法和对应的语句
class sqlDeal(object):
    def __init__(self):
        # self.config  = {'host': '127.0.0.1', 'user': 'root', 'password': 'qwer1234', 'db': 'novel', 'port': 3306, 'charset': 'utf8mb4', 'cursorclass':pymysql.cursors.DictCursor}
        self.config  = {'host': '127.0.0.1', 'user': 'root', 'password': 'qwer1234', 'db': 'novel', 'port': 3306, 'charset': 'utf8mb4'}
        self.limit_count=3 #最低预启动数据库连接数量
        self.pool=PooledDB(pymysql,self.limit_count,use_unicode = True,**self.config)

    #简单sql执行方法
    def smallFactory(self,sqlLine):
        #获取连接池的一个连接，创建游标
        conn=self.pool.connection()
        cursor=conn.cursor()
        #执行sql语句，非select语句，进行一次提交
        try:
            cursor.execute(sqlLine)
            results = cursor.fetchall()
            if "select" not in sqlLine.lower():
                cursor.execute("commit;")
        except Exception as e:
            print(e)
            return
        finally:
            #关闭游标，释放连接到连接池
            cursor.close()
            conn.close()
        return results

    #基础的筛选
    def selectNormal(self,key,sheet,values=" 1=1"):
        text=f"SELECT {key} FROM {sheet} where {values};"
        logging.debug(text)
        return text

    #基本的更新执行方法
    def updateNormal(self,sheet,values,items):
        text = f"UPDATE {sheet} SET {values} where {items};"
        logging.debug(text)
        return text

    #插入sql，mysql使用ignore会返回warning信息，调用warning模块屏蔽
    def insertIgnore(self,key,sheet,values):
        example="INSERT IGNORE INTO books (iplog) VALUES ('MySQL Manual')"
        warnings.filterwarnings("ignore")
        text=f"INSERT IGNORE INTO `{sheet}` ({key}) VALUES ({values});"
        return text

    #存入时，验证是否在表内存在，不存在则存入
    def saveIpList(self,iplist):
        useTable="iplog"
        # 获取初始ip总数，
        logging.info(f"初始ip总数{iplist}")
        selectSql = self.selectNormal("*", useTable)
        logging.debug(selectSql)
        startNum = self.smallFactory(selectSql)
        key=("`ipadress`,`port`,`STATUS`,createtime,updatetime,webcheck")
        for line in iplist:
            logging.info(f"遍历对象{line}")
            ip,port,status,webcheck=line["ipAdress"],line["port"],line["status"],line["webcheck"]
            values = (f"'{ip}',{port},{status},NOW(),NOW(),{webcheck}")
            #此方法存在隐患，会使ip数值急剧增加
            sql=self.insertIgnore(key,useTable,values)
            logging.info(sql)
            self.smallFactory(sql)
        endNum = self.smallFactory(selectSql)
        #总数的变化，可用可不可用的ip都被存入了数据库
        Num=len(endNum) - len(startNum)
        logging.warning(f"*****本次成功新增ip共{Num}条*****")
        return Num

    #获取所有状态为1,webcheck小于5的ip
    def getIpList(self,choose=0,limit=5,webcheck=5):
        useTable="iplog"
        if choose==0:
            #用于网络验证demo
            sql=self.selectNormal("id,ipadress,port",useTable,f" status=1 and webcheck<>1  limit 5")
        elif choose==1:
            #用于多线程验证的ip生成器
            sql=self.selectNormal("id,ipadress,port,webcheck,status",useTable,f" status=1 and webcheck<{webcheck} and webcheck>0 GROUP BY id DESC limit {limit}")
        else:sql=""
        logging.debug(f"获取可用ip的sql\n{sql}")
        results=self.smallFactory(sql)
        return results

    # 获取所有已使用状态为2、黑名单状态为2的url
    def getUrlList(self,useTable="allurl",limit=5):
        """
        :param useTable: 表名
        :param limit: 取值范围
        :return: ((id,oldurl,used,black).)
        """
        sql=self.selectNormal("id,oldurl,used,black",useTable,f" black=2 and used=2 limit {limit}")
        logging.debug(f"获取可用url的sql\n{sql}")
        results=self.smallFactory(sql)
        return results

    #简单的数据验证
    def checkEveringThing(self,useTable,kind="and",**where):
        """
        :param useTable:表名
        :param kind: 条件链接方式
        :param where: 条件字典
        :return: 返回结果
        """
        newline=" "
        for key,value in where.items():
            newline += str(key)
            newline = newline+f" = '{value}' "
            newline += f" {kind} "
        newline=newline[:-4]
        logging.debug(where)
        sql = self.selectNormal("*",useTable,newline)
        logging.debug(sql)
        results = self.smallFactory(sql)
        return results


    #更新Url状态
    def updateUrlStatus(self,used,black,id):
        useTable="allurl"
        sql1 = self.updateNormal(useTable,f"used={used},black={black}",f" id={id}")
        logging.debug(f"执行\n{sql1}\n更改状态")
        logging.info("将id {}状态改为used {}, black {}".format(id,used,black))
        results = self.smallFactory(sql1)
        return results

    #更新ip状态
    def updateIpStatus(self,useTable,status,webcheck,id):
        sql1 = self.updateNormal(useTable,f"status={status},updatetime=now(),webcheck={webcheck}",f" id={id}")
        logging.debug(f"执行\n{sql1}\n更改状态")
        logging.info("将id {}状态改为status {}, webcheck {}".format(id,status,webcheck))
        results = self.smallFactory(sql1)
        return results

    #批量修改ip状态
    def updateIpListStatus(self,ipLine,webcheck=1):
        useTable = "iplog"
        for line in ipLine:
            id,status=line[0],line[1]
            self.updateIpStatus(useTable,status,webcheck,id)
        return True

    #简单sql的执行方法
    def small(self,sql):
        self.cursor.execute(sql)
        if "select" not in sql and "SELECT" not in sql:
            self.cursor.execute("commit;")
        results = self.cursor.fetchall()
        logging.info(results)
        logging.info("顺利执行完成")
        return results

    #存放可能用到的语句
    def waite(self):
        datetime.datetime(2020, 10, 30, 16, 23, 37).strftime('%Y-%m-%d %H:%M:%S')


    #搜索ip是否存在
    def duplicationIP(self,argv,status=None):
        useTable="iplog"
        if status:
            sqlLine = self.selectNormal("ipadress,STATUS", useTable, " ipadress =\'{}\' and status = \'{}\'".format(argv,status))
        else:
            sqlLine=self.selectNormal("ipadress,STATUS",useTable," ipadress =\'{}\'".format(argv))
        results=self.smallFactory(sqlLine)
        logging.debug(results)
        return results


    #存储url
    def saveAllUrl(self,allUrls):
        useTable = "allurl"
        # 获取初始url总数
        logging.info(f"初始url总数{len(allUrls)}")
        selectSql = self.selectNormal("*", useTable)
        logging.debug(selectSql)
        startNum = self.smallFactory(selectSql)
        #url地址，是否被使用过，是标记黑名单
        key = ("oldurl,used,black")
        for line in allUrls.values():
            logging.debug(f"遍历对象{line}")
            oldurl, used, black= line,2,2
            values = (f"'{oldurl}',{used},{black}")
            # 此方法存在隐患，会使id数值急剧增加
            sql = self.insertIgnore(key, useTable, values)
            results = self.checkEveringThing(useTable,oldurl=line)
            if len(results) == 0:
                logging.debug(sql)
                self.smallFactory(sql)
            else:pass
        endNum = self.smallFactory(selectSql)
        # 总数的变化，可用可不可用的ip都被存入了数据库
        Num = len(endNum) - len(startNum)
        logging.warning(f"*****本次成功新增url共{Num}条*****")
        return Num




class oldsql(object):
    #装饰器，用于sql方法执行前后的数据库链接和关闭
    def startAndEnd(func):
        def wrapper(self,argv):
            self.conectSql()
            end=func(self,argv)
            self.closeSql()
            return end
        return wrapper

    #链接数据库，获取游标
    def conectSql(self,):
        # 打开数据库连接
        self.db = pymysql.connect(**self.config)
        # 使用cursor()方法获取操作游标
        self.cursor  = self.db.cursor()
        return
    #断开数据库
    def closeSql(self):
        # self.cursor.close()
        self.db.close()
        return


if __name__=="__main__":
    fool = sqlDeal()
    # fool.conectSql()
    # fool.selectNormal("*","iplog","")
    # print(fool.insertIgnore())

    # validIp = ['123.139.56.238:9999', '210.61.240.162:8080', '203.189.89.153:8080', '27.191.234.69:9999',
    #            '210.61.240.162:8080', '103.249.100.152:80', '121.89.194.145:3128', '117.141.155.244:53281',
    #            '222.249.238.138:8080', '101.36.160.87:3128', '118.163.13.200:8080', '124.205.155.158:9090',
    #            '47.56.9.58:3128']
    # end=fool.duplicationIP("123.139.56.268")
    # statusList = [(254, 0), (255, 0), (257, 0), (261, 0), (263, 0), (265, 0), (266, 0)]
    # fool.updateIpListStatus(statusList)
    dicts={'秦风龙小云': 'https://www.biquge.lu/book/51043/', '沧元图': 'https://www.biquge.lu/book/49717/', '临渊行': 'https://www.biquge.lu/book/30903/', '圣墟': 'https://www.biquge.lu/book/8/', '夫人你马甲又掉了': 'https://www.biquge.lu/book/49836/', '凤凰门': 'https://www.biquge.lu/book/34510/', '元尊': 'https://www.biquge.lu/book/16364/', '我是至尊': 'https://www.biquge.lu/book/8279/', '万古神帝': 'https://www.biquge.lu/book/7390/', '都市造化神医': 'https://www.biquge.lu/book/4470/', '一念永恒': 'https://www.biquge.lu/book/4427/', '牧神记': 'https://www.biquge.lu/book/3354/', '滇娇传之天悦东方': 'https://www.biquge.lu/book/240/', '祖宗模拟器': 'https://www.biquge.lu/book/64500/', '剑圣就该出肉装': 'https://www.biquge.lu/book/60714/', '我夺舍了魔皇': 'https://www.biquge.lu/book/53582/', '一剑独尊': 'https://www.biquge.lu/book/48750/', '我不会武功': 'https://www.biquge.lu/book/46540/', '伏天氏': 'https://www.biquge.lu/book/41333/', '斗罗大陆III龙王传说': 'https://www.biquge.lu/book/5500/', '九星霸体诀': 'https://www.biquge.lu/book/4105/', '逆天邪神': 'https://www.biquge.lu/book/542/', '造化之王': 'https://www.biquge.lu/book/301/', '帝霸': 'https://www.biquge.lu/book/187/', '无上神王': 'https://www.biquge.lu/book/61/', '我师兄实在太稳健了': 'https://www.biquge.lu/book/64422/', '修真家族平凡路': 'https://www.biquge.lu/book/61912/', '烂柯棋缘': 'https://www.biquge.lu/book/61492/', '沈氏家族崛起': 'https://www.biquge.lu/book/61393/', '仙道长青': 'https://www.biquge.lu/book/55104/', '我在江湖兴风作浪': 'https://www.biquge.lu/book/55054/', '横扫大千': 'https://www.biquge.lu/book/53319/', '青梅仙道': 'https://www.biquge.lu/book/48681/', '我是仙凡': 'https://www.biquge.lu/book/42072/', '永恒国度': 'https://www.biquge.lu/book/22600/', '永恒圣王': 'https://www.biquge.lu/book/22005/', '凡人修仙之仙界篇': 'https://www.biquge.lu/book/3215/', '都市狂枭': 'https://www.biquge.lu/book/64201/', '祖传土豪系统': 'https://www.biquge.lu/book/62834/', '天后的绯闻老爸': 'https://www.biquge.lu/book/62563/', '天降我才必有用': 'https://www.biquge.lu/book/62559/', '重生大亨崛起': 'https://www.biquge.lu/book/62496/', '文娱从综艺开始': 'https://www.biquge.lu/book/62468/', '最强赘婿': 'https://www.biquge.lu/book/54610/', '生活系游戏': 'https://www.biquge.lu/book/51595/', '我的奶爸人生': 'https://www.biquge.lu/book/48496/', '我身上有条龙': 'https://www.biquge.lu/book/37799/', '重生完美时代': 'https://www.biquge.lu/book/5838/', '特种兵在都市': 'https://www.biquge.lu/book/983/', '极品全能学生': 'https://www.biquge.lu/book/580/', '大秦从献仙药开始': 'https://www.biquge.lu/book/63569/', '红楼庶长子': 'https://www.biquge.lu/book/62057/', '农女的锦鲤人生': 'https://www.biquge.lu/book/61965/', '我绝不当皇帝': 'https://www.biquge.lu/book/61780/', '和离之后再高嫁': 'https://www.biquge.lu/book/61192/', '北颂': 'https://www.biquge.lu/book/58415/', '家有庶夫套路深': 'https://www.biquge.lu/book/55370/', '神圣罗马帝国': 'https://www.biquge.lu/book/53214/', '至尊妖孽兵王': 'https://www.biquge.lu/book/42751/', '帝国吃相': 'https://www.biquge.lu/book/42642/', '山沟皇帝': 'https://www.biquge.lu/book/37370/', '寒门崛起': 'https://www.biquge.lu/book/977/', '神话版三国': 'https://www.biquge.lu/book/630/', '联盟之冠军之路': 'https://www.biquge.lu/book/64660/', '英雄联盟之第四防御塔': 'https://www.biquge.lu/book/64181/', '艾泽拉斯月夜之影': 'https://www.biquge.lu/book/63880/', '英雄联盟之缔造王朝': 'https://www.biquge.lu/book/62585/', '亏成首富从游戏开始': 'https://www.biquge.lu/book/62074/', '猎魔烹饪手册': 'https://www.biquge.lu/book/61410/', 'NBA最强主教': 'https://www.biquge.lu/book/57752/', 'LCK的中国外援': 'https://www.biquge.lu/book/55341/', '我是传奇BOSS': 'https://www.biquge.lu/book/53047/', '英雄联盟之兼职主播': 'https://www.biquge.lu/book/50930/', '天行': 'https://www.biquge.lu/book/48909/', '英雄联盟之决胜巅峰': 'https://www.biquge.lu/book/14776/', '重生之最强剑神': 'https://www.biquge.lu/book/3451/', '第九特区': 'https://www.biquge.lu/book/64410/', '银河科技帝国': 'https://www.biquge.lu/book/62302/', '都市圣骑异闻录': 'https://www.biquge.lu/book/61999/', '诸天之从新做人': 'https://www.biquge.lu/book/61093/', '学霸的科幻世界': 'https://www.biquge.lu/book/60916/', '我的细胞监狱': 'https://www.biquge.lu/book/57203/', '诸天万界神龙系统': 'https://www.biquge.lu/book/49826/', '全球诸天在线': 'https://www.biquge.lu/book/49704/', '九星毒奶': 'https://www.biquge.lu/book/49042/', '踏星': 'https://www.biquge.lu/book/45146/', '黎明之剑': 'https://www.biquge.lu/book/42253/', '我的小人国': 'https://www.biquge.lu/book/39475/', '末日轮盘': 'https://www.biquge.lu/book/7126/', '老子修仙回来了': 'https://www.biquge.lu/book/52237/', '第八百七十章 仙师之上！': 'https://www.biquge.lu/book/52237/', '我的宠物是鳄龟': 'https://www.biquge.lu/book/96584/', '第324章 呐喊助威': 'https://www.biquge.lu/book/96584/', '汉世祖': 'https://www.biquge.lu/book/61699/', '第65章 开封府尹的问题': 'https://www.biquge.lu/book/61699/', '大魏春': 'https://www.biquge.lu/book/93514/', '第九十七章 舅舅都想坑': 'https://www.biquge.lu/book/93514/', '神级上门女婿': 'https://www.biquge.lu/book/77595/', '第一百一十八章 心碎的滋味（二更）': 'https://www.biquge.lu/book/77595/', '文明之万界领主': 'https://www.biquge.lu/book/73677/', '第3617章、行动': 'https://www.biquge.lu/book/73677/', '强化医生': 'https://www.biquge.lu/book/75046/', '614 粪便移植': 'https://www.biquge.lu/book/75046/', '全能少夫人美又爆': 'https://www.biquge.lu/book/11423/', '第689章：感觉自己好像在乘船': 'https://www.biquge.lu/book/11423/', '讨命人': 'https://www.biquge.lu/book/87981/', '第416章   真会玩': 'https://www.biquge.lu/book/87981/', '从签到开始制霸全球': 'https://www.biquge.lu/book/73470/', '646 硬菜': 'https://www.biquge.lu/book/73470/', '时总宠妻超无敌': 'https://www.biquge.lu/book/52323/', '第1016章：接力赛，终篇，四杀，史上最惨反派！': 'https://www.biquge.lu/book/52323/', '武唐仙': 'https://www.biquge.lu/book/9211/', '第四十三章 魏思温': 'https://www.biquge.lu/book/9211/', '不败战神秦惜杨辰': 'https://www.biquge.lu/book/27992/', '第2097章': 'https://www.biquge.lu/book/13919/', '不败神婿杨辰秦惜': 'https://www.biquge.lu/book/13939/', '不败神婿杨辰秦惜小说': 'https://www.biquge.lu/book/13938/', '杨辰秦惜不败神婿': 'https://www.biquge.lu/book/13934/', '不败神婿全文免费阅读': 'https://www.biquge.lu/book/13931/', '不败神婿笑傲余生': 'https://www.biquge.lu/book/13921/', '不败神婿': 'https://www.biquge.lu/book/14042/', '不败神婿杨辰': 'https://www.biquge.lu/book/14023/', '不败神婿全本免费阅读': 'https://www.biquge.lu/book/14039/', '无敌战王杨辰': 'https://www.biquge.lu/book/14037/', '杨辰秦惜': 'https://www.biquge.lu/book/14034/', '无敌战王': 'https://www.biquge.lu/book/14033/', '不败战神杨辰免费阅读': 'https://www.biquge.lu/book/14030/', '杨辰秦惜小说全文免费阅读': 'https://www.biquge.lu/book/14029/', '杨辰秦惜小说': 'https://www.biquge.lu/book/14027/', '杨辰秦惜全本免费': 'https://www.biquge.lu/book/14017/', '惊天战龙杨辰秦惜': 'https://www.biquge.lu/book/13919/', '医妃火辣辣摄政王爷有喜了': 'https://www.biquge.lu/book/99614/', '她不做天神好多年': 'https://www.biquge.lu/book/99612/', '每天被陛下借用身体': 'https://www.biquge.lu/book/99616/', '开挂成名后我被冷王盯上了': 'https://www.biquge.lu/book/99613/', '快穿之炮灰女配自救系统': 'https://www.biquge.lu/book/99611/', '回到古代做手术': 'https://www.biquge.lu/book/99615/', '穿成下堂妻后男主变苟了': 'https://www.biquge.lu/book/99605/', '重生之绯闻女王': 'https://www.biquge.lu/book/99606/', '肥妻有喜：王爷你是我的菜': 'https://www.biquge.lu/book/99610/', '重生七零：媳妇有点辣': 'https://www.biquge.lu/book/99609/', '厉少的小祖宗甜又野': 'https://www.biquge.lu/book/99607/', '夫人又撩又飒': 'https://www.biquge.lu/book/99608/', '全后宫穿进逃生游戏': 'https://www.biquge.lu/book/99604/', '至强龙尊叶辰萧初然': 'https://www.biquge.lu/book/6970/', '至强龙尊叶公子': 'https://www.biquge.lu/book/6960/', '济世医婿': 'https://www.biquge.lu/book/6948/', '济世医婿许飞柳如烟': 'https://www.biquge.lu/book/6947/', '神品龙王': 'https://www.biquge.lu/book/6938/', '花村神医林木李秋华': 'https://www.biquge.lu/book/6928/', '神品龙王棋乐': 'https://www.biquge.lu/book/6925/', '神品龙王陈江河江璐': 'https://www.biquge.lu/book/6924/', '花村神医': 'https://www.biquge.lu/book/6922/', '花村神医农民哥哥': 'https://www.biquge.lu/book/6917/', '穿到三千小世界里当炮灰': 'https://www.biquge.lu/book/6916/', '高冷学弟乖一点': 'https://www.biquge.lu/book/6913/', '男主全在黑化中[快穿]': 'https://www.biquge.lu/book/6900/', '重生后我靠捡垃圾暴富了': 'https://www.biquge.lu/book/6899/', '重生后我被反派大佬看穿了': 'https://www.biquge.lu/book/6897/', '全能大小姐她又美又飒': 'https://www.biquge.lu/book/6888/', '[综童话]看穿渣王子的特殊技巧': 'https://www.biquge.lu/book/6885/', '飞剑问道': 'https://www.biquge.lu/book/15676/', '凡人修仙传仙界篇': 'https://www.biquge.lu/book/14872/', '通天仙路': 'https://www.biquge.lu/book/424/', '逍遥梦路': 'https://www.biquge.lu/book/14451/', '直死无限': 'https://www.biquge.lu/book/3547/', '斗战狂潮': 'https://www.biquge.lu/book/5228/', '武道宗师': 'https://www.biquge.lu/book/637/', '重生之神级学霸': 'https://www.biquge.lu/book/402/', '超级神基因': 'https://www.biquge.lu/book/29029/', '天道图书馆': 'https://www.biquge.lu/book/29029/', '五行天': 'https://www.biquge.lu/book/14988/', '永夜君王': 'https://www.biquge.lu/book/14627/'}

    fool.saveAllUrl(dicts)
