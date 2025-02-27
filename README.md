# CS50 Finance - My Version

## Overview
This project is an implementation of CS50's "Finance" problem set, which allows users to manage a virtual stock portfolio. It includes features such as buying and selling stocks, viewing transaction history, and checking stock prices. Additionally, I have implemented:

- **Deposit Feature**: Users can add virtual cash to their account.
- **AJAX-based Stock Quotes**: Stock prices are fetched dynamically without page reloads.

## Features
- **User Authentication**: Users can register and log in securely.
- **Buy & Sell Stocks**: Users can purchase stocks based on real-time prices and sell them later.
- **Transaction History**: Displays a record of all trades.
- **Portfolio Overview**: Shows current holdings and account balance.
- **Deposit Cash**: Users can increase their balance by adding virtual money (magically!).
- **Live Stock Quotes (AJAX)**: Stock quotes are retrieved dynamically without refreshing the page.

## Technologies Used
- **Python** (Flask for backend)
- **SQLite** (Database for user accounts and transactions)
- **HTML, CSS, Bootstrap** (Frontend UI)
- **JavaScript (AJAX, Fetch API)** (For fetching stock prices asynchronously)
- **API** (Used for fetching stock data)

## Installation & Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/cs50-finance.git
   cd cs50-finance
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up the database:
   ```bash
   flask db upgrade
   ```

4. Set environment variables:
   ```bash
   export FLASK_APP=application.py
   export API_KEY=your_api_key_here  # For stock quotes
   ```

5. Run the application:
   ```bash
   flask run
   ```

6. Access the app in your browser at:
   ```
   http://127.0.0.1:5000
   ```

## Custom Features Implementation
### Deposit Feature
- Users can add funds via a **Deposit** button.
- The amount is validated and updated in the database.
- The new balance is displayed in the portfolio.

### AJAX-based Stock Quotes
- Used JavaScript `fetch()` to get real-time stock data from the API.
- Updates stock information without reloading the page.

## Future Improvements
- Implement user authentication with OAuth (e.g., Google Login).
- Improve UI with more interactive elements.
- Add email notifications for portfolio changes.

## Acknowledgments
- This project is based on the CS50 Finance problem set.
- Special thanks to CS50 staff for providing the foundation for this application.

---

Feel free to fork this repository and make your own modifications! 🚀
