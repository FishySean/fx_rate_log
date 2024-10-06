# CNY/USD Exchange Rate Comparison Tool

This project is a web application designed to compare the CNY/USD exchange rates offered by the Bank of China (BOC) and China Merchants Bank (CMB).

## Features

- Real-time fetching of CNY/USD exchange rate data from BOC and CMB
- Stores exchange rate data in an SQLite database
- Displays exchange rate data in a line chart through a web interface
- Supports comparison of various rate types (e.g., telegraphic transfer buying rate, cash selling rate, etc.)

## Tech Stack

- Backend: Python, Flask
- Database: SQLite
- Frontend: HTML, JavaScript, Chart.js
- Data Scraping: requests, bocfx library

## Installation and Running

1. Clone the repository:
   ```
   git clone [repository URL]
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   python main.py
   ```

4. Access the application in your browser at `http://127.0.0.1:8881`

## Project Structure

- `main.py`: The main application file containing Flask and data scraping logic
- `templates/index.html`: The frontend HTML template
- `exchange_rates.db`: SQLite database file
- `exchange_rates.log`: Log file

## Notes

- Ensure that your network allows access to the official websites of the Bank of China and China Merchants Bank
- The application updates the exchange rate data every minute
- Please follow the terms and policies of the relevant websites

## Contributions

Feel free to submit issues and pull requests. For major changes, please open an issue first to discuss what you would like to change.
