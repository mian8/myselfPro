#coding=utf8

"""
pygame的大球吃小球游戏
做出碰撞和清除功能
"""

import pygame
from enum import Enum,unique
from math import sqrt
from random import randint

@unique
class Color(Enum):
    """颜色"""
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    GRAY = (242, 242, 242)

    @staticmethod
    def random_color():
        r=randint(0,255)
        g=randint(0,255)
        b=randint(0,255)
        return (r,g,b)

class Ball(object):
    def __init__(self,x,y,radius,sx,sy,color=Color.RED):
        """初始化"""
        self.x=x
        self.y=y
        self.radius=radius
        self.sx=sx
        self.sy=sy
        self.color=color
        self.alive=True

    def move(self,screen):
        """移动"""
        self.x+=self.sx
        self.y+=self.sy

        if self.x-self.radius<=0 or self.x+self.radius>=screen.get_width():
            self.sx=-self.sx
        if self.y-self.radius<=0 or self.y+self.radius>=screen.get_height():
            self.sy=-self.sy

    def eat(self,other):
        if self.alive and other.alive and self !=other:
            dx,dy=self.x-other.x,self.y-other.y
            distance=sqrt(dx**2+dy**2)
            if distance < self.radius+other.radius and self.radius>other.radius:
                other.alive=False
                self.radius=self.radius+int(other.radius*0.146)


    def draw(self,screen):
        """绘制在窗口"""
        pygame.draw.circle(screen,self.color,(self.x,self.y),self.radius,0)


def main():
    #定义球容器
    balls=[]
    #格式化窗口
    pygame.init()
    #实例化屏幕
    screen=pygame.display.set_mode((800,600))
    #窗口名称
    pygame.display.set_caption("大球吃小球")
    #定义初始位置
    running=True
    # #设置背景色
    # screen.fill((242,242,242))
    # #预处理图片
    # ball_image=pygame.image.load("./res/邻里4-1活动.png")
    # #屏幕加载图片(图片对象,（位置））
    # screen.blit(ball_image,(50,50))

    #开始主程序
    while running:
        #从队列中获取事件执行
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running=False
            elif event.type ==pygame.MOUSEBUTTONDOWN and event.button==1:
                #获取鼠标点击位置
                x,y=event.pos
                # c创建一个球(大小，速度和颜色)
                radius=randint(10,50)
                sx,sy=randint(-20,20),randint(-20,20)
                color=Color.random_color()
                ball=Ball(x,y,radius,sx,sy,color)
                #将球添加到容器
                balls.append(ball)
        screen.fill((255,255,255))
        for ba in balls:
            if ba.alive:
                ba.draw(screen)
            else:balls.remove(ba)

        pygame.display.flip()

        #定时刷新
        pygame.time.delay(10)
        for ba in balls:
            ba.move(screen)
            for other in balls:
                ba.eat(other)


if __name__ == "__main__":
    main()


