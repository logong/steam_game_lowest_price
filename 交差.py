import MySQLdb

def start():
    #万事开头难
    global conn,curs
    conn = MySQLdb.connect("127.0.0.1", "root", "nideshengri", "nidekuzi", charset='utf8' )
    # 使用cursor()方法获取操作游标 
    curs = conn.cursor()

#此方法需要传入游戏名，返回其历次更新数据
def getdata(name):
    start()
    mtags=['massively multiplayer','Action','Adventure','Casual','Indie','RPG','Simulation','Racing','Sports','Strategy']
    dic={}
    for mtag in mtags:
        sql='SELECT `%s`.`SteamId` FROM `%s` WHERE `%s`.`Name`="%s"'%(mtag,mtag,mtag,name)
        curs.execute(sql)
        idn=curs.fetchone()
        if idn==None:
            continue
        else:
            mtag+='updata'
            sql="SELECT * FROM `%s` WHERE `%s`.`SteamId`='%s'"%(mtag,mtag,idn[0])
            curs.execute(sql)
            datas=curs.fetchall()
            for data in datas:
                price=float(data[1][:-1])
                time=data[-1]
                time=time.strftime("%Y%m%d")
                dic[time]=price
        break
    return dic

#此方法可以传回两个列表，第一个包含所有的tag，第二个包含每个tag对应的游戏数量
def getid():
    start()
    x_data=['1980s']
    y_data=[0]
    sql='SELECT * FROM `id_tag` ORDER BY `id_tag`.`Tag` ASC'
    curs.execute(sql)
    datas=curs.fetchall()
    i=0
    tem=[]
    for data in datas:
        if(x_data[i]!=data[1]):
            tem=[]
            x_data.append(data[1])
            y_data.append(1)
            tem.append(data[0])
            i+=1
        elif not(data[0] in tem):
            y_data[i]+=1
    return x_data,y_data