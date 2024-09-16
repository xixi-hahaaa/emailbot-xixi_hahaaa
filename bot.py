import discord
from discord.ext import commands, tasks
from gmailevent import GmailEvent
from database import DatabaseEvent
from analyzer import Analyzer
from query import load_query
import pandas as pd

# Initialize components
gmail_event = GmailEvent()
database_event = DatabaseEvent()
analyzer = Analyzer()
intents = discord.Intents.all()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Authenticate Gmail and setup the database connection
gmail_event.authenticate()
database_event.connect()
database_event.setup()

@tasks.loop(minutes=60)  # Check for emails every hour
async def check_hydro_bill_email_task():
    """This task checks for new emails and sends notifications if needed."""
    hydro_bill = gmail_event.check_hydro_bill()
    snippet = hydro_bill['snippet']

    """ Run analysis on hydro usage """
    pay_info = analyzer.hydro_bill_split(snippet)

    date = hydro_bill['sent_date']

    if hydro_bill:
        recent_entry = database_event.get_most_recent_hydro_entry()

        # Flag to track if a notification is sent
        notification_sent = False

        # If no recent entry or a different bill was received
        if not recent_entry or (str(recent_entry[1]) != str(hydro_bill['sent_date'])):
            database_event.insert_hydro_entry(hydro_bill)
            id = database_event.get_bill_id_by_date(date)[0]
            pay_info += "\nYour bill id is " + str(id)
            await send_discord_notification(pay_info)  # Send the notification using the bot
            notification_sent = True  # Mark that a notification was sent

        # If it's the same bill, check if it's paid
        if recent_entry and (str(recent_entry[1]) == str(hydro_bill['sent_date'])) and recent_entry[4] == b'\x00':
            # Bill not paid, send a reminder
            if not notification_sent:  # Only send if a new bill notification wasn't sent
                id = database_event.get_bill_id_by_date(date)[0]
                pay_info += "\nYour bill id is " + str(id)
                await send_discord_notification(pay_info)
            else:
                # Send a celebratory message
                message = "Woohoo! Hydro paid ontime 🥳🥳🥳"
                await send_discord_notification(message)
    else:
        print("No hydro bill found.")

async def send_discord_notification(message):
    """Send a message to a Discord channel using the bot."""
    discord_json = "json/discord.json"
    queries = load_query(discord_json)
    
    channel_id = queries.get("channel_id")
    channel = bot.get_channel(channel_id)
    if channel:
        await channel.send(message)
    else:
        print("Channel not found. Make sure the bot has access to the channel.")

@bot.command(name="paid")
async def mark_as_paid(ctx, bill_id):
    """Mark a specific hydro bill as paid."""
    recent_unpaid_bills = database_event.get_unpaid_bills()
    
    # Check if the bill ID is valid
    matching_bill = None
    for bill in recent_unpaid_bills:
        if str(bill) == bill_id: 
            matching_bill = bill
            break
    
    if matching_bill:
        # Mark the bill as paid in the database
        database_event.mark_bill_as_paid(bill_id)
        await ctx.send(f"Bill {bill_id} has been marked as paid. 🎉")
    else:
        await ctx.send(f"No unpaid bill found with ID {bill_id}. Please check and try again.")

@bot.command(name="paidRecent")
async def mark_as_paid_recent(ctx):
    """Set most recent bill status as paid"""
    unpaid_bill_count = database_event.check_unpaid_collection()

    if unpaid_bill_count and unpaid_bill_count == 1:
        database_event.mark_recent_as_paid()
        await ctx.send("Most recent bil has been marked as paid.")
    elif unpaid_bill_count == 0:
        await ctx.send("No outstanding bills to pay.")
    else:
        await ctx.send("More than one outstanding bill. Please use paid command and specify bill id.")

@bot.command(name="hello")
async def hello(ctx):
    """Says hello back"""
    await send_discord_notification("Hello!")

@bot.command(name="viewBills")
async def view_bills(ctx):
    """Displays all unpaid bills"""
    unpaid_bills = database_event.get_unpaid_bills_info()
    print(unpaid_bills)
    if not unpaid_bills:
        await ctx.send("No outstanding bills found.")
        return
    response = "Here are all your outstanding bills:\n"
    for bill in unpaid_bills:
        # Assuming bill is a dictionary with keys 'id', 'amount', 'due_date'
        response += "Bill Id: " + str(bill[0]) + "\nDetails: " + bill[2] + "\nDue Date: " + bill[3] + " \n"
    response += "🙈"
    await ctx.send(response)

@bot.command(name="analysisTrendFull")
async def full_analysis(ctx):
    """Analyzes hydro bill trends for up to a year or 12 bills"""
    
    # Initialize lists to collect data
    costs = []
    dates = []
    
    # Retrieve all past biils

    info = database_event.get_all()
    
    for i in info:
        # Extract bill date and snippet (assuming `i[1]` is date and `i[3]` is the snippet)
        bill_date = i[1]
        snippet = i[3]

        # Get the cost from the snippet using the analyzer
        try:
            value = analyzer.get_value(snippet)
            if value is not None:
                costs.append(value)
                dates.append(bill_date)
        except Exception as e:
            print(f"Error getting value from snippet: {e}")
    
    if not costs or not dates:
        await ctx.send("No sufficient data available for trend analysis.")
        return
    
    # Convert lists to Pandas DataFrame for analysis
    df = pd.DataFrame({
        'Date': pd.to_datetime(dates),
        'Balance': costs
    })

    result = analyzer.hydro_bill_analysis(df)

    image = discord.File(result)

    await ctx.send(file=image)
    

@bot.command(name="halp")
async def help(ctx):
    """Same as !help but with spice"""
    help_msg = "EmailBot commands: \n!hello - says hello back 🙋🏻‍♀️🙋🏻 \n!paid {bill_id} - sets bill with bill_id status to paid \n!paidRecent - sets most recent bill status to paid \n!viewBills - sends relevant information for all outstanding bills \n!halp - displays this message" 
    await ctx.send(help_msg)


@bot.event
async def on_ready():
    """Triggered when the bot is ready."""
    print(f'Bot is logged in as {bot.user}')

    if not check_hydro_bill_email_task.is_running():
        check_hydro_bill_email_task.start()



# Load bot token and run the bot
bot_json = "json/discord.json"
bot_queries = load_query(bot_json)
token = bot_queries.get("token")
bot.run(token)
