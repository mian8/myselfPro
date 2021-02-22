#coding=utf8

import requests,hashlib
from interfaceConnection import baseFunc

#参数整理

customerParams={'id': '', 'name': '客户新增测试3', 'customer_age': '', 'phone': '185953628627', 'attribution': '河南-周口', 'attributionid': '1673', 'email': '', 'idcard': '', 'industry': '0', 'province': '1673', 'city': '1842', 'datailaddress': '', 'comment': '', 'status': '', 'otherphone1': '', 'otherphone2': '', 'demand_id': '', 'demand_country': '55', 'demand_city': '0', 'demand_premises': '0', 'demand_budget': '0', 'demand_purpose': '', 'demand_wuye': '0', 'empid': '630', 'maritalstatus': '', 'demand_district': '0', 'demand_housestyle': '', 'demand_hallsnum': '', 'demand_toiletnum': '', 'demand_parkingnum': '', 'yudaoempid': '', 'wechat': '', 'resourcetype': '2', 'sourceid': '12', 'network': '', 'supercustid': '0', 'channelid': '0', 'showeid': '0', 'activity': '0'}
subParams={'customerid': '378534', 'subscriptiondate': '2019-07-10', 'premisesid': '15', 'ispaydown': '1', 'downpaymentprice': '', 'downpaymentcny': '0', 'downpaytype': '0', 'issign': '1', 'signdate': '', 'isothers': '1', 'buyerlawyer': '', 'roomnumber': '76-32', 'area': '', 'totalpice': '1000.00', 'buyername1': '客户新增测试3', 'buyername2': '', 'buyerphone1': '185953628627', 'familyconnection': '', 'buyeraddress': '', 'buyeridcard1': '', 'buyeridcard2': '', 'buyeremail': '', 'companyconnection': '', 'resempid': '630', 'salespid': '', 'salempid': '630', 'ausempid': '0', 'ausmanagerempid': '0', 'paytype': '1', 'lenders': '0', 'downpaymentmoeny': '', 'loanperiod': '', 'stampduty': '', 'repaymentmode': '0', 'paymentmoderemark': '', 'downpayment': '', 'paymentrental': '', 'lawyertax': '', 'bankids': '', 'recordids': '', 'property': '0', 'isnomination': '0', 'contractdate': '', 'isexternal': '0', 'seehouseid': '0', 'apartmentprice': '1000', 'carposprice': '', 'levelupprice': '', 'groundprice': '', 'buildingprice': '', 'combineprice': '', 'paydate': '', 'firstpaymoney': '100.00', 'devdiscount': '无', 'allpaylawyer': '', 'firstpaylawyer': '', 'lastpaylawyer': '', 'firbmoney': '', 'singlmoney': '', 'comdisids': '336'}

text="""
customerid:378534
subscriptiondate:2019-07-10
premisesid:15
ispaydown:1
downpaymentprice:
downpaymentcny:0
downpaytype:0
issign:1
signdate:
isothers:1
buyerlawyer:
roomnumber:76-32
area:
totalpice:1000.00
buyername1:客户新增测试3
buyername2:
buyerphone1:185953628627
familyconnection:
buyeraddress:
buyeridcard1:
buyeridcard2:
buyeremail:
companyconnection:
resempid:630
salespid:
salempid:630
ausempid:0
ausmanagerempid:0
paytype:1
lenders:0
downpaymentmoeny:
loanperiod:
stampduty:
repaymentmode:0
paymentmoderemark:
downpayment:
paymentrental:
lawyertax:
bankids:
recordids:
property:0
isnomination:0
contractdate:
isexternal:0
seehouseid:0
apartmentprice:1000
carposprice:
levelupprice:
groundprice:
buildingprice:
combineprice:
paydate:
firstpaymoney:100.00
devdiscount:无
allpaylawyer:
firstpaylawyer:
lastpaylawyer:
firbmoney:
singlmoney:
comdisids:336
Name
getPremisesByName.jhtml
getPremisesByName.jhtml
saveOrUpdate.jhtml
savceSubscription.jhtml

"""
#参数整理方法
def dealParams(params):
    newParams = {}
    for x in params.split("\n"):
       if ":" in x:
           items=x.split(":")
           newParams[items[0]]=items[1]
           print(items[0]+"\t"+items[1])
       else:
           print(f"非参数{x}")
    print(newParams)

# dealParams(text)
def creatcustomer():
    deal = baseFunc.proTotal()
    quser = {"account": "lzxst", "pwd": "1234567a"}
    params=(deal.CRMuser(quser))
    session=deal.CRMlogin(params)
    tomain=session.get(deal.tomain)
    end=session.post(url=deal.save,params=customerParams)
    print(end.text)
    if "true" in end.text:
        pass

dealParams(text)
creatcustomer()

