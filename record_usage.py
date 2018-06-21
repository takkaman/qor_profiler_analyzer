import MySQLdb
import datetime

def record_usage(mode, username):
    conn = MySQLdb.connect(host="pvicc015",user="user",db="preroute_random")
    cursor = conn.cursor(cursorclass=MySQLdb.cursors.DictCursor)
    time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if username and username != "phyan":
        source = "web"
        sql = "insert into qor_analyzer(username,source,mode,date) values(%s,%s,%s,%s)"
        param = (username,source,mode,time,)
        n = cursor.execute(sql,param)