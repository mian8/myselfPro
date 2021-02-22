#coding=utf8

from locust import HttpUser,between,task

class MyTaskSet(TaskSet):
    def on_start(self):
        self.client.get("/InfoPlat/login.jsp")
        self.client.post("/InfoPlat/login/toLogin.jhtml",{"account":r"\u0078\u0069\u0061\u006e\u0063\u0068\u0065\u006e\u0067\u0064\u0075\u006f",
               "pwd":r"\u0078\u0069\u0061\u006e\u0063\u0068\u0065\u006e\u0067\u0064\u0075\u006f\u0023\u0031\u0032\u0033",
               "code":"1234"})
        pass

    def on_stop(self):
        pass
    @task
    def index(self):
        self.client.post("/InfoPlat/login/toMain.jhtml")


class WebUser(HttpUser):
    task_set = MyTaskSet
    host = "http://112.74.31.201:8888"
    mainUrl = "http://112.74.31.201:8888/InfoPlat/login.jsp"
    loginUrl="http://112.74.31.201:8888/InfoPlat/login/toLogin.jhtml"
    loginDict={"account":"\u0078\u0069\u0061\u006e\u0063\u0068\u0065\u006e\u0067\u0064\u0075\u006f",
               "pwd":"\u0078\u0069\u0061\u006e\u0063\u0068\u0065\u006e\u0067\u0064\u0075\u006f\u0023\u0031\u0032\u0033",
               "code":"1234"}
    min_wait = 5000
    max_wait = 9000

loginDict={"account":"\u0078\u0069\u0061\u006e\u0063\u0068\u0065\u006e\u0067\u0064\u0075\u006f",
               "pwd":"\u0078\u0069\u0061\u006e\u0063\u0068\u0065\u006e\u0067\u0064\u0075\u006f\u0023\u0031\u0032\u0033",
               "code":"1234"}

print(loginDict)