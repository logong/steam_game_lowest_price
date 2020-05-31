import threading
import time
from queue import Queue
import requests
from bs4 import BeautifulSoup
import json


# 用来存放采集线程
g_crawl_list = []
# 用来存放解析线程
g_parse_list = []

class CrawlThread(threading.Thread):
    def __init__(self, name, page_queue, data_queue,block):
        super(CrawlThread, self).__init__()
        self.name = name
        self.page_queue = page_queue
        self.data_queue = data_queue
        self.block = block
        self.url = "https://store.steampowered.com/contenthub/querypaginated/tags/ConcurrentUsers/render/?query=&start={0}&count=15&cc=CN&l=english&v=4&tag={1}"
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
    def __init__(self, name, data_queue, fp, lock):
        super(ParserThread, self).__init__()
        self.name = name
        self.data_queue = data_queue
        self.fp = fp
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
        ans_list = []
        for games in game_block.contents[1::2]:
            
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
            ans_list.append({'id':game_id,"name":game_name,"price":game_price,"tags":game_tag})
        self.lock.acquire()
        self.fp.write(json.dumps(ans_list, ensure_ascii=False) + '\n')
        self.lock.release()

def get_page_number(block):
    req =  requests.get("https://store.steampowered.com/contenthub/querypaginated/tags/ConcurrentUsers/render/?query=&start=1&count=15&cc=CN&l=english&v=4&tag="+block)
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
def create_parse_thread(data_queue, fp, lock,block):
    parse_name = ['解析线程1'+block, '解析线程2'+block, '解析线程3'+block]
    global g_parse_list
    g_parse_list=[]
    for name in parse_name:
        # 创建一个解析线程
        tparse = ParserThread(name, data_queue, fp, lock)
        # 保存到列表中
        g_parse_list.append(tparse)

def main():
    for block in ['Indie','RPG','Simulation','Racing','Sports','Strategy']:
        #'Massively Multiplayer','Action','Adventure','Casual',
        # 创建队列函数
        page_queue, data_queue = create_queue(block)
        # 打开文件
        fp = open(block+'.json', 'a', encoding='utf-8')
        # 创建锁
        lock = threading.Lock()
        # 创建采集线程
        create_crawl_thread(page_queue, data_queue,block)
        time.sleep(10)
        # 创建解析线程
        create_parse_thread(data_queue, fp, lock,block)
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
        fp.close()
        print(block+"线程操作结束,爬取结束")
    print('主线程子线程全部结束')

if __name__ == '__main__':
    main() 
