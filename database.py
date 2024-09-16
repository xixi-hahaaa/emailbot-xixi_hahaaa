import pymysql
import json
import os
from query import load_query

class DatabaseEvent:

    def __init__(self):
        self.db = None

    def connect(self):
        json_file = "json/db.json"

        if not os.path.exists(json_file):
            print("Error: The configuration file 'db.json' does not exist.")
            return

        try:
            with open(json_file, 'r') as file:
                queries = json.load(file)
                host = queries.get("host")
                user = queries.get("user")
                password = queries.get("password")
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error reading the JSON file: {e}")
            return

        if not all([host, user, password]):
            print("Error: Missing database configuration details in 'db.json'.")
            return

        try:
            self.db = pymysql.connect(
                host=host,
                user=user,
                password=password
            )
            print("Database connection successful.")
        except pymysql.MySQLError as e:
            print(f"Error connecting to the database: {e}")
            return

    def setup(self):
        file_path = "sql/setup.sql"
        if not self.db:
            self.connect()

        try:
            with open(file_path, 'r') as file:
                sql_commands = file.read()

            # Split the SQL commands by semicolons and execute them
            with self.db.cursor() as cursor:
                for command in sql_commands.split(';'):
                    command = command.strip()
                    if command:
                        cursor.execute(command)
                        print(f"Executed: {command}")

            # Commit changes
            self.db.commit()
            print("SQL file executed successfully.")
        except (IOError, pymysql.MySQLError) as e:
            print(f"Error executing SQL file: {e}")

    def close(self):
        if self.db:
            self.db.close()
            print("Database connection closed.")

    def insert_hydro_entry(self, info):
        sent_date = info["sent_date"]
        details = info["snippet"]
        
        json_file = "json/query.json"
        queries = load_query(json_file)        

        query = queries.get("hydro_bill_query", "")
    
        # Find the "from" part of the query
        from_part = "from:"
        if from_part in query:
            start = query.find(from_part) + len(from_part)
            end = query.find(" ", start) if query.find(" ", start) != -1 else len(query)
            sender = query[start:end].strip()
        
        try:
            with self.db.cursor() as cursor:
                cursor.execute("USE emails;")
                query = "INSERT INTO hydro_gmail (date_day, sender_email, details, paid) VALUES (%s, %s, %s, 0)"
                data = (sent_date, sender, details)
                cursor.execute(query, data)
                self.db.commit()
        except pymysql.MySQLError as e:
            print(f"Error inserting into database: {e}")
        
    def get_most_recent_hydro_entry(self):
        try:
            with self.db.cursor() as cursor:
                cursor.execute("USE emails;")
                cursor.execute("SELECT * FROM hydro_gmail ORDER BY date_day DESC LIMIT 1;")
                self.db.commit()
                result = cursor.fetchone()
                return result
        except pymysql.MySQLError as e:
            print(f"Error getting most recent entry from database: {e}")
        
        return None
    
    def mark_bill_as_paid(self, id):
        try:
            with self.db.cursor() as cursor:
                cursor.execute("USE emails;")
                cursor.execute(f"UPDATE hydro_gmail SET paid = 1 WHERE id = {id};")
                self.db.commit()
                result = cursor.fetchone()
        except pymysql.MySQLError as e:
            print(f"Error updating bill payment status: {e}")

    def get_bill_id_by_date(self, date_day):
        try:
            with self.db.cursor() as cursor:
                cursor.execute("USE emails;")
                cursor.execute(f"SELECT id FROM hydro_gmail WHERE date_day = '{date_day}';")
                self.db.commit()
                result = cursor.fetchone()
                return result
        except pymysql.MySQLError as e:
            print(f"Error - no hydro bill due on {date_day}: {e}")
            return -1

    def mark_recent_as_paid(self):
        try:
            with self.db.cursor() as cursor:
                cursor.execute("USE emails;")
                cursor.execute("SELECT id FROM hydro_gmail ORDER BY date_day DESC LIMIT 1;")
                result = cursor.fetchone()
                if result:
                    bill_id = result[0]  # Get the ID of the most recent entry
                    cursor.execute("UPDATE hydro_gmail SET paid = 1 WHERE id = %s;", (bill_id,))
                    self.db.commit()
                    print(f"Bill with ID {bill_id} marked as paid.")
                else:
                    print("No recent entries found to mark as paid.")
        except pymysql.MySQLError as e:
            print(f"Error updating bill payment status: {e}")
    
    def check_unpaid_collection(self):
        try:
            with self.db.cursor() as cursor:
                cursor.execute("USE emails;")
                cursor.execute("SELECT COUNT(*) FROM hydro_gmail WHERE paid = 0;")
                count = cursor.fetchone()[0]  # Get the count from the result
                return count
        except pymysql.MySQLError as e:
            print(f"Error checking unpaid collections: {e}")
            return None
        
    def get_unpaid_bills(self):
        try:
            with self.db.cursor() as cursor:
                cursor.execute("USE emails;")
                cursor.execute("SELECT id FROM hydro_gmail WHERE paid = 0;")
                self.db.commit()
                result = cursor.fetchone()
                return result
        except pymysql.MySQLError as e:
            print(f"Error fetching unpaid bills: {e}")
            return None
        
    def get_unpaid_bills_info(self):
        try:
            with self.db.cursor() as cursor:
                cursor.execute("USE emails;")
                cursor.execute("SELECT * FROM hydro_gmail WHERE paid = 0;")
                self.db.commit()
                result = cursor.fetchall()
                return result
        except pymysql.MySQLError as e:
            print(f"Error fetching unpaid bills: {e}")
            return None
        
    def get_all(self):
        try:
            with self.db.cursor() as cursor:
                cursor.execute("USE emails;")
                cursor.execute("SELECT * FROM hydro_gmail;")
                self.db.commit()
                result = cursor.fetchall()
                return result
        except pymysql.MySQLError as e:
            print(f"Error fetching all bills: {e}")
            return None
            




