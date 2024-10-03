import requests
import sqlite3
import time
import bocfx
import logging
from flask import Flask, jsonify, render_template
import sys

# 初始化日志系统
logging.basicConfig(filename='exchange_rates.log', level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s:%(message)s')

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(asctime)s %(levelname)s:%(message)s')
console_handler.setFormatter(console_formatter)
logging.getLogger('').addHandler(console_handler)

# 初始化数据库
conn = sqlite3.connect('exchange_rates.db', check_same_thread=False)
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS rates (
        bank TEXT,
        currency TEXT,
        rtbBid REAL,   -- 综合汇率
        rthBid REAL,   -- 现汇买入价
        rtcBid REAL,   -- 现钞买入价
        rthOfr REAL,   -- 现汇卖出价
        rtcOfr REAL,   -- 现钞卖出价
        ratTim TEXT,   -- 时间
        ratDat TEXT,   -- 日期
        UNIQUE(bank, ratTim, ratDat)
    )
''')
conn.commit()

app = Flask(__name__)

def fetch_cmb_rate():
    try:
        url = "https://m.cmbchina.com/api/rate/fx-rate?name=%E7%BE%8E%E5%85%83"
        response = requests.get(url)
        data = response.json()
        rate_info = data["body"]["data"][0]
        
        ratDat = rate_info["ratDat"]
        ratTim = rate_info["ratTim"]
        
        # 按照正确的顺序解析招商银行的五个汇率
        rtbBid = float(rate_info['rtbBid'])    # 综合汇率
        rthBid = float(rate_info['rthBid'])    # 现汇买入价
        rtcBid = float(rate_info['rtcBid'])    # 现钞买入价
        rthOfr = float(rate_info['rthOfr'])    # 现汇卖出价
        rtcOfr = float(rate_info['rtcOfr'])    # 现钞卖出价
        
        # 获取数据库中的最新记录
        c.execute('''
            SELECT rtbBid, rthBid, rtcBid, rthOfr, rtcOfr FROM rates
            WHERE bank='CMB' AND currency='USD'
            ORDER BY ratDat DESC, ratTim DESC LIMIT 1
        ''')
        latest_rate = c.fetchone()

        # 将数据库中的汇率值转换为 float 进行比较
        if latest_rate:
            latest_rate = tuple(map(float, latest_rate))  # 将数据库中的值转换为 float
        
        # 检查汇率是否和最新记录相同
        if latest_rate and (rtbBid, rthBid, rtcBid, rthOfr, rtcOfr) == latest_rate:
            logging.info("招商银行汇率未更新，跳过插入操作。")
            return
        
        # 插入数据时，按照招商银行的汇率结构来映射字段
        c.execute('''
            INSERT OR IGNORE INTO rates (bank, currency, rtbBid, rthBid, rtcBid, rthOfr, rtcOfr, ratTim, ratDat)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            "CMB", 
            "USD", 
            rtbBid, 
            rthBid, 
            rtcBid, 
            rthOfr, 
            rtcOfr,
            ratTim, 
            ratDat
        ))
        conn.commit()
        logging.info(f"招商银行 汇率数据 - 综合汇率：{rtbBid} 现汇卖出价：{rthOfr} 现钞卖出价：{rtcOfr} 现汇买入价：{rthBid} 现钞买入价：{rtcBid}")
    except Exception as e:
        logging.error(f"获取或存储招商银行汇率失败: {e}")

def fetch_boc_rate():
    try:
        boc_data = bocfx.bocfx('USD')[1]
        
        ratTim = boc_data[-1]  # 最后一个元素是时间
        ratDat = ratTim.split(" ")[0]  # 时间中的日期部分
        
        # BOC 汇率解析顺序：
        rthBid = float(boc_data[1])  # 现汇买入价
        rtcBid = float(boc_data[2])  # 现钞买入价
        rthOfr = float(boc_data[3])  # 现汇卖出价
        rtcOfr = float(boc_data[4])  # 现钞卖出价
        rtbBid = float(boc_data[5])  # 折算价（即综合汇率）
        
        # 获取数据库中的最新记录
        c.execute('''
            SELECT rtbBid, rthBid, rtcBid, rthOfr, rtcOfr FROM rates
            WHERE bank='BOC' AND currency='USD'
            ORDER BY ratDat DESC, ratTim DESC LIMIT 1
        ''')
        latest_rate = c.fetchone()

        # 将数据库中的汇率值转换为 float 进行比较
        if latest_rate:
            latest_rate = tuple(map(float, latest_rate))  # 将数据库中的值转换为 float

        # 检查汇率是否和最新记录相同
        if latest_rate and (rtbBid, rthBid, rtcBid, rthOfr, rtcOfr) == latest_rate:
            logging.info("中国银行汇率未更新，跳过插入操作。")
            return

        # 插入数据时，按照中国银行的汇率结构来映射字段
        c.execute('''
            INSERT OR IGNORE INTO rates (bank, currency, rtbBid, rthBid, rtcBid, rthOfr, rtcOfr, ratTim, ratDat)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            "BOC", 
            "USD", 
            rtbBid, 
            rthBid, 
            rtcBid, 
            rthOfr, 
            rtcOfr,
            ratTim.split(" ")[1],  # 仅获取时间部分
            ratDat
        ))
        conn.commit()
        logging.info(f"中国银行 汇率数据 - 综合汇率：{rtbBid} 现汇卖出价：{rthOfr} 现钞卖出价：{rtcOfr} 现汇买入价：{rthBid} 现钞买入价：{rtcBid}")
    except Exception as e:
        logging.error(f"获取或存储中国银行汇率失败: {e}")



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/rates_data')
def rates_data():
    try:
        # 查询招商银行汇率数据
        c.execute('''
            SELECT ratTim, ratDat, rtbBid, rthBid, rtcBid, rthOfr, rtcOfr FROM rates
            WHERE currency='USD' AND bank='CMB'
            ORDER BY ratDat, ratTim
        ''')
        cmb_data = c.fetchall()

        # 查询中国银行汇率数据
        c.execute('''
            SELECT ratTim, ratDat, rtbBid, rthBid, rtcBid, rthOfr, rtcOfr FROM rates
            WHERE currency='USD' AND bank='BOC'
            ORDER BY ratDat, ratTim
        ''')
        boc_data = c.fetchall()

        # 整理数据，分别为CMB和BOC的数据和时间
        cmb_times = [f"{row[1]} {row[0]}" for row in cmb_data]
        cmb_rtbBid = [row[2] for row in cmb_data]
        cmb_rthBid = [row[3] for row in cmb_data]
        cmb_rtcBid = [row[4] for row in cmb_data]
        cmb_rthOfr = [row[5] for row in cmb_data]
        cmb_rtcOfr = [row[6] for row in cmb_data]

        boc_times = [f"{row[1]} {row[0]}" for row in boc_data]
        boc_rtbBid = [row[2] for row in boc_data]
        boc_rthBid = [row[3] for row in boc_data]
        boc_rtcBid = [row[4] for row in boc_data]
        boc_rthOfr = [row[5] for row in boc_data]
        boc_rtcOfr = [row[6] for row in boc_data]

        # 返回JSON数据供前端使用
        return jsonify({
            'cmb': {
                'times': cmb_times,
                'rtbBid': cmb_rtbBid,
                'rthBid': cmb_rthBid,
                'rtcBid': cmb_rtcBid,
                'rthOfr': cmb_rthOfr,
                'rtcOfr': cmb_rtcOfr
            },
            'boc': {
                'times': boc_times,
                'rtbBid': boc_rtbBid,
                'rthBid': boc_rthBid,
                'rtcBid': boc_rtcBid,
                'rthOfr': boc_rthOfr,
                'rtcOfr': boc_rtcOfr
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    try:
        logging.info("启动Flask应用...")
        # 在后台运行数据抓取，每分钟执行一次
        import threading
        def data_collector():
            while True:
                fetch_cmb_rate()
                fetch_boc_rate()
                time.sleep(60)  # 每分钟执行一次
        collector_thread = threading.Thread(target=data_collector)
        collector_thread.daemon = True
        collector_thread.start()
        
        app.run(debug=False, host='100.126.221.127', port=8881)
    except Exception as e:
        logging.critical(f"主程序执行中出现严重错误: {e}")
