#coding = utf8

import requests
from bs4 import BeautifulSoup
import logging
import time,datetime,json
import urllib3
import jieba
from myLibrary import strRepeatability,cutWords

logging.basicConfig(level=logging.INFO)
urllib3.disable_warnings()

#顶点小说专用解析方法
class forBiquge(object):
    def __init__(self):
        self.firstParams={"name":"h2","intro":("div",{"class":"small"}),"index":("div",{"class":"listmain"})}
        self.secondParams={"name":"h2","intro":("div",{"class":"small"}),"index":("div",{"class":"listmain"})}
        self.thirdParams={}
        self.source="https://www.biqulu.net"

    #选择处理方法，且对结果进行标记
    def chooseFunc(self,response):
        if "book" in response.url and "html" not in response.url:
            results = self.first(response.text)
        elif "html" not in response.url:
            results = self.second(response.text)
        else:
            results = self.third(response.text)


    #书籍目录
    def first(self,html):
        """
        :param html:页面
        :return: {"status":1,"message":"获取成功","bookMsg":{}}
        """
        results ,bookMsg = {"status":1,"message":"获取成功","bookMsg":{}} ,{}
        bsHtml=BeautifulSoup(html,"lxml")

        #统计基本信息
        # nametag = bsHtml.find("h2")
        nametag = bsHtml.find(self.firstParams["name"])
        if nametag == None:
            results["status"] ,results["message"] = -2,"书名获取失败"
            return results
        bookMsg["name"] = nametag.get_text(strip = True)

        #定位书籍简介
        small = bsHtml.find("div",{"class":"small"})
        if small == None:
            results["status"] = -1
            bookMsg={"没有获取到目录"}
            return results
        else:
            smalllist = small.find_all("span")
            #按照指定顺序，获取书籍信息
            keys=["author","kind","isend","wordsnum","lasttime","lastchapter","intro"]
            logging.debug(f"关键字{keys}\n爬取的内容{smalllist}")
            logging.debug(smalllist)
            for num in range(0,len(smalllist)):
                value=smalllist[num].get_text()
                logging.debug(f"key:{keys[num]} , value:{value.split('：')[-1]}")
                bookMsg[keys[num]]=value.split("：")[-1]

            if bookMsg["isend"] != "完结":bookMsg["isend"]=2
            bookMsg["keywords"] = ",".join(cutWords(bookMsg["kind"]))

            logging.info(f"书籍信息:\n{bookMsg}")

        #获取目录
        listmain = bsHtml.find("div",{"class":"listmain"})
        try:
            dt = listmain.dl.find("dt").find_next("dt")
        except Exception as e:
            print("目录只找到一个dt")
            return
        dd = dt.find_next_siblings("dd")
        logging.debug(dd)
        num = 0
        index=[]
        for x in dd:
            name,link=x.a.string,x.a.attrs["href"]
            logging.debug(f"章节名{name},链接{link}")
            index.append((num,name,link))
            num+=1
        logging.info(f"书籍目录：\n{index}")

        bookMsg["index"]=index
        results["bookMsg"]=bookMsg
        return results

    #正文
    def second(self,html):
        """
        :param html:页面
        :return: {"status":1,"message":"获取成功","bookMsg":{}}
        """
        results, chapterMsg = {"status": 1, "message": "获取成功", "chapterMsg": {}}, {}
        bsHtml = BeautifulSoup(html, "lxml")

        #统计基本信息:文章标题
        nametag = bsHtml.find("h1")
        # nametag = bsHtml.find(self.firstParams["name"])
        if nametag == None:
            results["status"] ,results["message"] = -2,"书名获取失败"
            return results
        chapterMsg["chaptername"] = nametag.get_text(strip = True)

        #定位书籍简介
        body = bsHtml.find("div",{"class":"showtxt","id":"content"})
        if body == None:
            results["status"] = -1
            bookMsg={"没有获取到正文"}
            return results
        else:
            logging.debug(f"正文:\n{body}")
            # 通过改变tag属性，去掉多于的的字符串
            scriptList = body.find_all("script")
            for line in scriptList:
                line.string = ""
            #整理正文
            newline = ""
            for line in body.stripped_strings:
                if "www.biquge"  not in line :
                    if line.strip() != "":
                        newline += "\n"+line
            body=newline.strip()
            #获取验重字符串
            chapterMsg["hundred"]=body[0:50]
            chapterMsg["body"]=body

            results["chapterMsg"]=chapterMsg
            logging.debug(results)
            return results

    #将传入的网页，书籍链接卷包烩
    def third(self,html):
        """
        :param html:
        :return: {"status":1,"message":"获取成功","bookMsg":{}}

        """
        results = {"status": 1, "message": "获取成功", "getlink": {}}
        end = BeautifulSoup(html, "lxml")
        alllink = end.find_all("a")
        newDict = {}
        for line in alllink:
            name = line.get_text().strip()
            singlelink = line.attrs["href"]
            #排除了章节
            if "html" in singlelink or len(name) < 1 :
                continue
            if "biquge" in singlelink and len(singlelink) > 22:
                continue
            elif "book" in singlelink:
                newlink = self.source + singlelink
            else:
                continue
            if newlink not in newDict.values():
                logging.info(f"书名：{name}\n链接：{singlelink}")

                newDict[name] = newlink
        return newDict

    #书籍分类特殊处理
    def bookType(self,list):
        allType = {"笔趣阁www.biquge.lu": "https://www.biqulu.net/", "首页": "https://www.biqulu.net/", "玄幻小说": "https://www.biqulu.net/xuanhuanxiaoshuo/", "修真小说": "https://www.biqulu.net/xiuzhenxiaoshuo/", "都市小说": "https://www.biqulu.net/dushixiaoshuo/", "穿越小说": "https://www.biqulu.net/chuanyuexiaoshuo/", "网游小说": "https://www.biqulu.net/wangyouxiaoshuo/", "科幻小说": "https://www.biqulu.net/kehuanxiaoshuo/", "排行榜单": "https://www.biqulu.net/paihangbang/", "完本小说": "https://www.biqulu.net/wanben/1_1", "小说大全": "https://www.biqulu.net/xiaoshuodaquan/"}

    #关键字搜索
    def search(self,keys):
        pass

class mock(object):
    def gethtml(self,url,kind=1):
        if kind == 1:
            with open("./temp.html","r",encoding="utf8") as f:
                response=f.read()
            return response
        else:
            response=requests.get(url)
            self.save(response.text)
            return response.text

    def save(self,html):
        try:
            with open("./temp.html","w",encoding="utf8") as f:
                f.write(html)
                code=1
        except Exception as e:
            print(e)
            code=0
        return code

    def demo(self):
        seg_list = jieba.cut("玄幻小说")
        print("Full Mode: " + "/ ".join(seg_list))  # 全模式

if __name__=="__main__":
    x = mock()
    fool = forBiquge()

    html = x.gethtml("https://www.biqulu.net/xiuzhenxiaoshuo/", kind=1)
    results = fool.third(html)
    print(json.dumps(results, ensure_ascii=False))

    # html = x.gethtml("https://www.biqulu.net/book/8279/25303123.html",kind=1)
    # results = fool.second(html)
    # print(json.dumps(results, ensure_ascii=False))

    # html = x.gethtml("https://www.biqulu.net/book/8279/",kind=2)
    # results = fool.first(html)
    # print(json.dumps(results,ensure_ascii=False))

