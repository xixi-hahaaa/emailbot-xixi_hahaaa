import re
from datetime import datetime
from query import load_query
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import seaborn as sns

class Analyzer:

    def __init__(self):
        pass

    def __get_days(self, due_date):
        today = datetime.now().date()
        days = (due_date - today).days
        return days
    
    def get_value(self, snippet):
        match = re.search(r'\$(\d+\.\d+)', snippet)
        if match:
            value = match.group(1)  # Get the value from the first capturing group
            return value
        return 0

    def hydro_bill_split(self, snippet):
        """Calculates the cost per person this month"""
        value = 0.00
        pay_json = "json/pay.json"

        # Extract dollar amount
        value = self.get_value(snippet)
        split_value = float(value) / 5  # Example: split the bill among 5 roommates

    
        # Extract dates
        matches = re.findall(r'\w+ \d{2}, \d{4}', snippet)
        if len(matches) < 2:
            print("Date information is incomplete.")
            return
        
        sent_date_str = matches[0]
        due_date_str = matches[1]

        # Convert strings to datetime objects
        sent_date = datetime.strptime(sent_date_str, '%B %d, %Y').date()
        due_date = datetime.strptime(due_date_str, '%B %d, %Y').date()

        # Calculate days remaining until the due date
        days_remaining = self.__get_days(due_date)

        # Load email details
        queries = load_query(pay_json)
        transfer_email = queries.get("transfer") # not needed currently

        message = (
            f"NOTICE!!! New Hydro Bill\n"
            f"Monthly hydro cost: ${value}\n"
            f"Per tenant charge: ${split_value:.2f}\n"
            f"Bill due on {due_date_str}\n"
            f"This bill was sent out on {sent_date_str}. "
            f"Days remaining: {days_remaining}"
        )
        
        return message


    def hydro_bill_analysis(self, info):
        """Generate an analysis of the monthly costs using a simple average prediction."""
        # REQUIRE MORE DATA BEFORE SARIMA MODEL ETC.
        # Ensure the data is sorted by date
        info = info.sort_values(by='Date')

        # Extract values for analysis
        costs = info['Balance'].values
        dates = info['Date']

        balances = []

        # Convert costs from str to float for mean calculation
        for c in costs:
            c = float(c)
            balances.append(c)

        # Create a DataFrame for plotting
        data = pd.DataFrame({
            'Date': dates,
            'Balance': balances
        })

        # Plot the existing data
        plt.figure(figsize=(10, 6))
        sns.lineplot(x='Date', y='Balance', data=data, marker='o')
        plt.title('Monthly Hydro Bill Analysis')
        plt.xlabel('Date')
        plt.ylabel('Balance ($)')
        plt.xticks(rotation=45)
        
        # Calculate the average balance
        average_balance = np.mean(balances)

        # Extend the dates for predictions
        future_dates = pd.date_range(start=dates.max() + pd.DateOffset(months=1), periods=12, freq='M')
        future_balances = [average_balance] * len(future_dates)

        # Plot the future predictions
        future_data = pd.DataFrame({
            'Date': future_dates,
            'Balance': future_balances
        })
        sns.lineplot(x='Date', y='Balance', data=future_data, linestyle='--', color='red')

        plt.legend(['Historical Data', 'Predicted Data'])

        # Timestamp
        timestamp = datetime.now()
        
        # Save the plot
        img_path = 'imgs/hydro_bill_analysis.' + timestamp + '.png'
        plt.savefig(img_path)
        plt.close()
        
        return img_path
