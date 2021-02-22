import pandas as pd
import numpy as np
from pandas import Series,DataFrame

"""
#Series基本特性与字典相似，默认生成数字索引
obj=Series([4,7,-5,3],index=range(-2,2))
obj=Series(obj.values,index= obj.index*2)
print(f"直接打印\n{obj}")
#index与values
print(f"index为:{obj.index}\nvalues为:{obj.values}")
#对index与values 的运算
print(f"获取index大于0的对象：{obj[obj.index>0]}")
print(f"所有的values乘以2：{obj.values*2}")
#字典转化为Series
sdata={"lilith":365,"鲜橙多":846,"香菜":748,"开车苦手鲜橙多":213}
qc=Series(sdata,index=sorted(list(sdata.keys())+["科伦坡"]),name="成绩单")
#需要使用列表才能获取到Series格式的结果
print("lilith" in qc,pd.isnull(qc[[x for x in qc.index if len(x)>=3]]))
print(qc)
"""

"""
#基础数据源
data={"name": [ '开车苦手鲜橙多','lilith', '弗兰肯斯坦', '香菜',"中铁工业","捡垃圾吃的"],
      "record":[365, 846, 748, 213,367,27],
      "pop":[1.5,1.7,3.6,2.4,2.6,38]}
#生成Dataframe实例，可以设定columns和index
df=DataFrame(data,columns=list(data.keys())+["zz"],index=['one', 'two', 'three', 'four','five', 'six'])
print(f"输出前五行{df.head()}")
print(f"取列的两种方式：\n第一种{df['name']}\n第二种{df.record}")
print(f"取出行的方式:\n{df.loc['one']}")
#使用np迭代器添加新的行，缺少数据则添加失败，可以附上相同值
df["newLine"]=np.arange(6)
#生成Series实例，可以设定index
newS=pd.Series(list(range(3)),index=['one', 'two', 'three', 'four','five', 'six'][:3])
#对dataframe添加新的列并赋值，缺少值使用NaN填充
df["pdline"]=newS
print(df)
#判断值是否为NaN，isnull和notnull
df["fordel"]=pd.isnull(df.pdline)
#删除列
del df["fordel"]
"""
'''
#嵌套字典直接转化为dataframe，支持Numpy 的T方法进行转置
pop = {'Nevada': {2001: 2.4, 2002: 2.9},
       'Ohio': {2000: 1.5, 2001: 1.7, 2002: 3.6}}
frame1=DataFrame(pop)
print(frame1.T)
#制定了索引则不会按照内层字典生成
frame2=pd.DataFrame(pop,index=Series([2001,2002,2003]))
pdata={"Ohio":frame1["Ohio"][:-1],"Nevada":frame1["Nevada"][:2]}
frame3=DataFrame(frame1)
#设置行与列的name属性
frame3.index.name="year";frame3.columns.name="state"
#使用values以二维ndarry的形式取出数据
print(frame3,frame3.values)
'''

"""
#索引对象,类型为Index,不可改变，可切片
obj=pd.Series(range(3),index=["a","b","c"])
index=obj.index
#生成Index
labels=pd.Index(np.arange(3))
#Index可以使用重复标签
obj2=pd.Series(range(4),index=["a","b","c","c"])
#Index操作方法都是生成新的Index，原Index不会做改变
"""

#重新索引，reindex
frame=DataFrame(np.arange(9).reshape((3,3)),index=["a","c","d"],columns=['Ohio', 'Texas', 'California'])
#重排index和column
frame2= frame.reindex(["a","b","c","d"],columns=['Ohio', 'Texas', 'California',"Q"])
print(frame2)
obj=Series(["blue","purple","yellow"],index=[0,2,4])
#重排和填充index
obj1=obj.reindex(range(9),method="ffill")
#使用drop删除Series和DataFrame的行或者列，使用inplace=True可以修改数据源，慎用
obj2=obj1.drop([6,7,8])
#使用drop时，axis=1或者columns可以删除列
frame3=frame2.drop(["a","c"]).drop(["Q","Texas"],axis=1)
