import threading
import time
from queue import Queue
import requests
from bs4 import BeautifulSoup
import json
import MySQLdb
#zz牛逼教我json
#你看看你个菜鸡用多久
import datetime
#系统牛逼
import os

#正则表达式天下第一
import re

# 用来存放采集线程
g_crawl_list = []
# 用来存放解析线程
g_parse_list = []
ans_list=[]
tt=''

def start():
    #万事开头难
    global conn,curs
    conn = MySQLdb.connect("127.0.0.1", "root", "nideshengri", "nidekuzi", charset='utf8' )
    # 使用cursor()方法获取操作游标 
    curs = conn.cursor()



#插入游戏tag
def inserttag(idn,tags):
    for tag in tags.split(','):
        sql="""INSERT INTO `nidekuzi`.`id_tag`(SteamId,Tag) VALUES (%d,"%s")"""%(idn,tag.lstrip())
        #try:
        curs.execute(sql)
        #except:
            #conn.rollback()
        conn.commit()



    
#插入游戏的函数
def insertgame(mtag,idn,name,platforms,pic,price,tags):
    if len(price)==0:
        return      #价格为空意味着游戏已经下架
    name=filt_emo(name)     #为什么有人在游戏名里加emoji？
    name=transferContent(name)      #转义真是太难了太难了...
    price[0]=filt(price[0])
    price[-1]=filt(price[-1])
    if float(price[-1][:-1])==0:
        cut='0%'
    else:
        cut=str(int((float(price[-1][:-1])-float(price[0][:-1]))/float(price[-1][:-1])*100))
        cut=cut+'%'
    sql = """INSERT INTO `%s`(`SteamId`, `Name`,`Platforms`, `Pic_url`,`CurrentPrice`, `LowestPrice`, `OriginalPrice` , `Cut`)
             VALUES ('%d','%s','%s','%s','%s','%s','%s','%s')"""%(mtag,idn,name,platforms,pic,filt(price[0]),filt(price[0]),filt(price[-1]),cut)
    #try:
    curs.execute(sql)
    #except:
        #conn.rollback()
    conn.commit()
    inserttag(idn,tags)





#转义NMSL，代码我抄的https://blog.csdn.net/lengye7/article/details/79916685
def transferContent(content):
        if content is None:
            return None
        else:
            string = ""
            for c in content:
                if c == '"':
                    string += '\\\"'
                elif c == "'":
                    string += "\\\'"
                elif c == "\\":
                    string += "\\\\"
                else:
                    string += c
            return string





#求求你们不要在游戏名里加emoji了！！
def filt_emo(name):
    restr=''
    try:
        co = re.compile(u'[\U00010000-\U0010ffff]')
    except re.error:
        co = re.compile(u'[\uD800-\uDBFF][\uDC00-\uDFFF]')
    return co.sub(restr, name)





#金钱格式一定要统一啊....
def filt(price):
    price=re.findall("\d+\\.?\d*",price)
    if len(price)==0:
        return '0.00￥'
    else:
        price=float(price[0])
        return '%.2f￥'%price





#每日更新数据的函数
def updata(mtag,idn,name,platforms,pic,price,tags):
    price[0]=filt(price[0])
    platform=''
    for a in platforms:
        platform+=a
    platform=transferContent(platform) 
    sql="SELECT * FROM `%s` WHERE SteamId=%d"%(mtag,idn)
    curs.execute(sql)
    olddata=curs.fetchone()
    if olddata==None:#意味着有新游戏或者游戏遗漏，那么插入游戏
        insertgame(mtag,idn,name,platform,pic,price,tags)
        return
    if price[0] != olddata[-4]:
        recording(mtag,idn,price[0],time)
    if float(price[0][:-1]) <float(olddata[-1][:-1]):
        lowest=price[0]
    else:
        lowest=olddata[-1]
    if float(price[0][:-1])==0:
        cut='0%'
    else:
        cut=str(int((float(olddata[-3][:-1])-float(price[0][:-1]))/float(olddata[-3][:-1])*100))
        cut=cut+'%'
    sql='''UPDATE `%s` SET `Platforms` = '%s', `CurrentPrice` = '%s', `Cut` = '%s', `LowestPrice` = '%s' , `Pic_url` = '%s' WHERE `%s`.`SteamId` = %d'''%(mtag,platform,price[0],cut,lowest,pic,mtag,idn)

    #try:
    curs.execute(sql)
    #except:
        #conn.rollback()
    conn.commit()





#在updata表里留下证据
def recording(mtag,idn,price,time):
    sql = """INSERT INTO `%sUpdata`(`SteamId`, `Price`)
             VALUES ('%d','%s')"""%(mtag,idn,price)
    #try:
    curs.execute(sql)
    #except:
        #conn.rollback()
    conn.commit()





#通用更新函数,没用到这个
#四个参数为表名，id，需要更新的数据，更新数据的字段名
def updatasql(mtag,idn,data,dataname):
    sql='''UPDATE `%s` SET `%s` = '%s' WHERE `%s`.`SteamId` = %d'''%(mtag,dataname,data,mtag,idn)
    #try:
    curs.execute(sql)
    #except:
        #conn.rollback()
    conn.commit()


class CrawlThread(threading.Thread):
    def __init__(self, name, page_queue, data_queue,block):
        super(CrawlThread, self).__init__()
        self.name = name
        self.page_queue = page_queue
        self.data_queue = data_queue
        self.block = block
        self.url = "https://store.steampowered.com/contenthub/querypaginated/tags/NewReleases/render/?query=&start={0}&count=15&cc=CN&l=english&v=4&tag={1}"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
        }

    def run(self):
        print('%s----线程启动' % self.name)
        while 1:
            
            # 判断采集线程何时退出
            if self.page_queue.empty():
                break
            # 从队列中取出页码
            page = self.page_queue.get()
            # 拼接url，发送请求
            url = self.url.format(page,self.block)
            try:
                r = requests.get(url, headers=self.headers)
            except:
                self.page_queue.put(page)
                continue
            # 响应内容存放到data_queue中
            self.data_queue.put(r.text)
            print('{0}----采集{1}完毕'.format(self.name,page))
            time.sleep(3)
        print('%s----线程结束' % self.name)

class ParserThread(threading.Thread):
    def __init__(self, name, data_queue, lock):
        super(ParserThread, self).__init__()
        self.name = name
        self.data_queue = data_queue
        self.lock = lock

    def run(self):
        print('%s----线程启动' % self.name)
        while 1:
            try:
                #print('%s----线程正在干活' % self.name)
                # 从data_queue中取出一页数据
                data = self.data_queue.get(True, 10)
                # 解析内容
                self.parse_content(data)
            except Exception as e:
                print(e)
                break
        print('%s----线程结束' % self.name)

    def parse_content(self, info):
        try:
            info = json.loads(info)['results_html']
            game_block =  BeautifulSoup(info, 'html.parser')
        except:
            print("get info error")
            return
        global tt
        for games in game_block.contents[1::2]:
            pf=[]
            if games.find('span',class_="platform_img win"):
                pf.append("win")
            if games.find('span',class_="platform_img mac"):
                pf.append("mac")
            if games.find('span',class_="platform_img linux"):
                pf.append("linux")
            if games.find('img',class_="tab_item_cap_img")!=None:
                pic=[games.find('img',class_="tab_item_cap_img")['src']]
            game_name = games.find('div',class_="tab_item_name").string
            if games.find('div',class_="discount_final_price")!= None:
                game_price = [games.find('div',class_="discount_final_price").string]
            else:
                game_price = []
            game_tag = games.find_all('span',class_ = "top_tag")
            game_id = games['data-ds-appid']
            if games.find('div',class_="discount_original_price") !=None:
                game_price.append(games.find('div',class_="discount_original_price").string)
            tags = []
            for i in game_tag:
                tags.append(i.string)
            game_tag = "".join(tags)
            ans_list.append({'id':game_id,"name":game_name,"price":game_price,"tags":game_tag,'picture':pic,'platform':pf,'block':tt})
        self.lock.acquire()
        self.lock.release()

def get_page_number(block):
    req =  requests.get("https://store.steampowered.com/contenthub/querypaginated/tags/NewReleases/ConcurrentUsers/render/?query=&start=1&count=15&cc=CN&l=english&v=4&tag="+block)
    #print(json.loads(req.text).keys())
    try: 
        data = json.loads(req.text)['total_count']
    except:
        data = "0"
    return data

# 创建队列
def create_queue(block):
    # 创建页码队列
    page_queue = Queue()
    for page in [i for i in range(int(get_page_number(block))+15) if i%15==0]:
        page_queue.put(page)
    # 创建内容队列
    data_queue = Queue()
    return page_queue, data_queue

# 创建采集线程
def create_crawl_thread(page_queue, data_queue,block):
    crawl_name = ['采集线程1'+block, '采集线程2'+block, '采集线程3'+block,'采集线程4'+block,'采集线程5'+block,'采集线程6'+block]
    global g_crawl_list
    g_crawl_list=[]
    for name in crawl_name:
        # 创建一个采集线程
        tcrwal = CrawlThread(name, page_queue, data_queue,block)
        # 保存到列表中
        g_crawl_list.append(tcrwal)


# 创建解析线程
def create_parse_thread(data_queue, lock,block):
    parse_name = ['解析线程1'+block, '解析线程2'+block, '解析线程3'+block]
    global g_parse_list
    g_parse_list=[]
    for name in parse_name:
        # 创建一个解析线程
        tparse = ParserThread(name, data_queue, lock)
        # 保存到列表中
        g_parse_list.append(tparse)

def main():
    for block in ['Massively Multiplayer']:
        #,'Action','Adventure','Casual','Indie','RPG','Simulation','Racing','Sports','Strategy'

        global tt
        tt=block
        # 创建队列函数
        page_queue, data_queue = create_queue(block)
        # 打开文件
        # 创建锁
        lock = threading.Lock()
        # 创建采集线程
        create_crawl_thread(page_queue, data_queue,block)
        time.sleep(10)
        # 创建解析线程
        create_parse_thread(data_queue, lock,block)
        # 启动所有采集线程
        print(len(g_crawl_list))
        for tcrwal in g_crawl_list:
            tcrwal.start()
        # 启动所有解析线程
        for tparse in g_parse_list:
            tparse.start()
        # 主线程等待子线程结束
        print("等待前")
        for tcrwal in g_crawl_list:
            tcrwal.join()
        print("等待解析前")
        for tparse in g_parse_list:
            tparse.join()
        print("等待后")

        # 关闭文件
        print(block+"线程操作结束,爬取结束")
    print('主线程子线程全部结束')
    ks=datetime.datetime.now()
    start()
    #file的第一项是一个字典就行
    for item in ans_list :
        updata(item['block'],int(item['id']),item['name'],item['platform'],item['picture'][0],item['price'],item['tags'])
        js=datetime.datetime.now()
        print(js-ks)
        # 关闭连接
        conn.close()

if __name__ == '__main__':
    main() 
    #每日更新数据

