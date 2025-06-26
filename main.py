import requests
import sqlite3
import time
import bocfx
import logging
from flask import Flask, jsonify, render_template


# Initialize logging system
logging.basicConfig(filename='exchange_rates.log', level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s:%(message)s')

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(asctime)s %(levelname)s:%(message)s')
console_handler.setFormatter(console_formatter)
logging.getLogger('').addHandler(console_handler)

# Initialize database
conn = sqlite3.connect('exchange_rates.db', check_same_thread=False)
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS rates (
        bank TEXT,
        currency TEXT,
        rtbBid REAL,   -- Composite rate
        rthBid REAL,   -- Telegraphic transfer buying rate
        rtcBid REAL,   -- Cash buying rate
        rthOfr REAL,   -- Telegraphic transfer selling rate
        rtcOfr REAL,   -- Cash selling rate
        ratTim TEXT,   -- Time
        ratDat TEXT,   -- Date
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
        
        ratDat_unformmated = rate_info["ratDat"]
        ratDat = ratDat_unformmated.replace('年', '-').replace('月', '-').replace('日', '')  # Format date
        ratTim = rate_info["ratTim"]  # Time

        # Parse CMB's five exchange rates in correct order
        rtbBid = float(rate_info['rtbBid'])    # Composite rate
        rthBid = float(rate_info['rthBid'])    # Telegraphic transfer buying rate
        rtcBid = float(rate_info['rtcBid'])    # Cash buying rate
        rthOfr = float(rate_info['rthOfr'])    # Telegraphic transfer selling rate
        rtcOfr = float(rate_info['rtcOfr'])    # Cash selling rate
        
        # Fetch the latest record from the database
        c.execute('''
            SELECT rtbBid, rthBid, rtcBid, rthOfr, rtcOfr FROM rates
            WHERE bank='CMB' AND currency='USD'
            ORDER BY ratDat DESC, ratTim DESC LIMIT 1
        ''')
        latest_rate = c.fetchone()

        # Convert the rates in the database to float for comparison
        if latest_rate:
            latest_rate = tuple(map(float, latest_rate))  # Convert values to float
        
        # Check if the rate is the same as the latest record
        if latest_rate and (rtbBid, rthBid, rtcBid, rthOfr, rtcOfr) == latest_rate:
            logging.info("CMB exchange rate has not been updated, skipping insert operation.")
            return
        
        # Insert data into the database, mapping fields to CMB rate structure
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
        logging.info(f"CMB Exchange Rate Data - Composite Rate: {rtbBid} TT Selling Rate: {rthOfr} Cash Selling Rate: {rtcOfr} TT Buying Rate: {rthBid} Cash Buying Rate: {rtcBid}")
    except Exception as e:
        logging.error(f"Failed to fetch or store CMB exchange rate: {e}")

def fetch_boc_rate():
    try:
        boc_data = bocfx.bocfx('USD')[1]
        
        ratTim = boc_data[-1]  # Last element is the time
        ratDat = ratTim.split(" ")[0]  # Extract the date part from time
        
        # BOC rate parsing order:
        rthBid = float(boc_data[1])  # TT Buying Rate
        rtcBid = float(boc_data[2])  # Cash Buying Rate
        rthOfr = float(boc_data[3])  # TT Selling Rate
        rtcOfr = float(boc_data[4])  # Cash Selling Rate
        rtbBid = float(boc_data[5])  # Conversion Rate (Composite Rate)
        
        # Fetch the latest record from the database
        c.execute('''
            SELECT rtbBid, rthBid, rtcBid, rthOfr, rtcOfr FROM rates
            WHERE bank='BOC' AND currency='USD'
            ORDER BY ratDat DESC, ratTim DESC LIMIT 1
        ''')
        latest_rate = c.fetchone()

        # Convert the rates in the database to float for comparison
        if latest_rate:
            latest_rate = tuple(map(float, latest_rate))  # Convert values to float

        # Check if the rate is the same as the latest record
        if latest_rate and (rtbBid, rthBid, rtcBid, rthOfr, rtcOfr) == latest_rate:
            logging.info("BOC exchange rate has not been updated, skipping insert operation.")
            return

        # Insert data into the database, mapping fields to BOC rate structure
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
            ratTim.split(" ")[1],  # Only get the time part
            ratDat
        ))
        conn.commit()
        logging.info(f"BOC Exchange Rate Data - Composite Rate: {rtbBid} TT Selling Rate: {rthOfr} Cash Selling Rate: {rtcOfr} TT Buying Rate: {rthBid} Cash Buying Rate: {rtcBid}")
    except Exception as e:
        logging.error(f"Failed to fetch or store BOC exchange rate: {e}")



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/rates_data')
def rates_data():
    try:
        # Query all bank data with currency='USD' from the database
        c.execute('''
            SELECT bank, ratTim, ratDat, rtbBid, rthBid, rtcBid, rthOfr, rtcOfr FROM rates
            WHERE currency='USD'
            ORDER BY ratDat, ratTim
        ''')
        all_data = c.fetchall()

        # Create a dictionary to store data for all banks
        banks_data = {}

        # Iterate over the query results and organize data by bank
        for row in all_data:
            bank = row[0]  # Get the bank name
            timestamp = f"{row[2]} {row[1]}"  # Combine date and time
            rtbBid = row[3]  # Composite rate
            rthBid = row[4]  # TT Buying Rate
            rtcBid = row[5]  # Cash Buying Rate
            rthOfr = row[6]  # TT Selling Rate
            rtcOfr = row[7]  # Cash Selling Rate

            # If the bank is not already in banks_data, create a new entry
            if bank not in banks_data:
                banks_data[bank] = {
                    'times': [],
                    'rtbBid': [],
                    'rthBid': [],
                    'rtcBid': [],
                    'rthOfr': [],
                    'rtcOfr': []
                }

            # Add data to the corresponding bank entry
            banks_data[bank]['times'].append(timestamp)
            banks_data[bank]['rtbBid'].append(rtbBid)
            banks_data[bank]['rthBid'].append(rthBid)
            banks_data[bank]['rtcBid'].append(rtcBid)
            banks_data[bank]['rthOfr'].append(rthOfr)
            banks_data[bank]['rtcOfr'].append(rtcOfr)

        # Return JSON data for frontend use
        return jsonify(banks_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    try:
        logging.info("Starting Flask application...")
        # Run data collection in the background every minute
        import threading
        def data_collector():
            while True:
                fetch_cmb_rate()
                fetch_boc_rate()
                time.sleep(60)  # Execute every minute
        collector_thread = threading.Thread(target=data_collector)
        collector_thread.daemon = True
        collector_thread.start()
        
        app.run(debug=False, host='100.126.221.127', port=8881)
    except Exception as e:
        logging.critical(f"Critical error occurred in main program: {e}")
