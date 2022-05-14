from numpy import insert
import requests
import os
import json
import csv
from datetime import date
from discord import Webhook, RequestsWebhookAdapter
from decouple import config
from connect import *
import sys

# To set your environment variables in your terminal run the following line:
bearer_token = os.environ.get('BEARER_TOKEN', config('BEARER_TOKEN'))

# DATABASE_URL = os.environ.get('DATABASE_URL', config('BOT_API'))

# BOT_API = os.environ.get('BOT_API', config('BOT_API')) # template
WEBHOOK = os.environ.get('WEBHOOK', config('WEBHOOK'))
MAX_RESULTS = os.environ.get('MAX_RESULTS', config('MAX_RESULTS'))
MESSAGE_TEMPLATE = os.environ.get('MESSAGE_TEMPLATE', config('MESSAGE_TEMPLATE'))
S3_BUCKET = os.environ.get('S3_BUCKET')


def create_url(user):
    # Replace with user ID below
    return "https://api.twitter.com/2/users/{}/following?max_results={}".format(user, MAX_RESULTS)


def get_params():
    return {"user.fields": "created_at"}


def bearer_oauth(r):
    """
    Method required by bearer token authentication.
    """

    r.headers["Authorization"] = f"Bearer {bearer_token}"
    r.headers["User-Agent"] = "v2FollowingLookupPython"
    return r


def save_to_csv(data, user):
    # open the file in the write mode
    name = f'./databases/new_follows_{user}.csv'
    dirname = './databases'
     
    if not os.path.exists(dirname):
        os.mkdir('databases')
    with open(name, 'a' , newline='') as f:
        # create the csv writer
        writer = csv.writer(f)

        # write a row to the csv file
        writer.writerows(data)

    print(f"Saved to file @ {name}. Adding {len(data)} new lines to -> {user}.")

def connect_to_endpoint(url, params):
    response = requests.request("GET", url, auth=bearer_oauth, params=params)
    print(response.status_code)
    if response.status_code != 200:
        raise Exception(
            "Request returned an error: {} {}".format(
                response.status_code, response.text
            )
        )
    return response.json()


# test function
def connect_to_endpoint_test(url, params):
    f = open('test_data.json')
    jsonfile = json.load(f)
    return jsonfile


def find_exists(data, username):
    '''
    Finds if the username already exists in the database
    '''
    results = []
    try:
        with open(f'./databases/new_follows_{username}.csv', 'r') as f:
            csv_reader = csv.reader(f)
            for line in csv_reader:
                results.append(line[0])
                
        new_data = list(filter(lambda a: a not in results, data))
        print('Found file, reading data..')
    except IOError:
        new_data = data
        print('File not exists.')
        
    return new_data


def send_to_discord_batch(data, current_date):
    '''
    Send batch data to discord in a single message. Not used atm
    Discord only accepts messages < 2000 in length, as a result this function should be used
        only if you intend to send less than 3 people data at a time
        
    Accepts:
    Params:
        - data: a dict in from {'username': [1,2,3,4], 'username2': [1,2,3,4]}
        - current_date, just a date for display purposes
    '''
    webhook = Webhook.from_url(WEBHOOK, adapter=RequestsWebhookAdapter())
    
    
    #build message
    message = f"Hellow! This is your digest: {current_date} \n ============== \n"
        
    for user, accounts in data.items():
        message += f'-> New following of {user}: \n'
        for a in accounts:
            message += f"https://twitter.com/{a[0]} \n"
        message += '------------------------------ \n'
    
    # print(message)
    webhook.send(message)
    
    
def send_to_discord_single(data, username, current_date):
    '''
    Send batch data to discord in a single message. Not used atm
    Discord only accepts messages < 2000 in length, as a result this function should be used
        only if you intend to send less than 3 people data at a time
        
    Accepts:
    Params:
        - data: an array of account usernames
        - username of the account we are interested in
        - current_date, just a date for display purposes
    '''
    webhook = Webhook.from_url(WEBHOOK, adapter=RequestsWebhookAdapter())
    
    
    #build message
    message = f"====================\n {MESSAGE_TEMPLATE} user {username} on {current_date} \n ==================== \n "
    
    if (len(data) != 0):
        for user in data:
            message += f"https://twitter.com/{user} \n"
            
        message += '\n---------------------------\n'
    else:
        message += 'No recent follows for this user.\n'
    
    # print(message)
    try:
        webhook.send(message)
    except:
        print("Error sending to webhook")
        
        
def save_to_db(connection, username, records, current_date):
    cursor = connection.cursor()
    
    # create DB with the name of the account if not exists
    create_table = """
    CREATE TABLE IF NOT EXISTS new_followers_{} (
    username VARCHAR(64) PRIMARY KEY,
    date DATE NOT NULL);
    """.format(username)
    
    print("Creating table for user if not exists...")
    cursor.execute(create_table)
    
    
    # add rows
    sql_insert_query = """ INSERT INTO new_followers_{} (username, date) 
                           VALUES (%s,%s)""".format(username)
    
    # get usernames query
    sql_get_usernames = """
    SELECT * FROM new_followers_{}
    """.format(username)
    
    # get all usernames present in a account db's
    cursor.execute(sql_get_usernames)
    result = cursor.fetchall()
    
    # Filter. Records are what we retrieved from twitter data. Result are records present. Filter data that is not present
    new_users = list(filter(lambda a: a not in result, records))
    
    # append date to records to put in database
    new_records = [(u, current_date) for u in new_users]
            
    # inserting records into each user respective database               
    try:
        print("Inserting values into user db...")
        cursor.executemany(sql_insert_query, new_records)
    except:
        print("Values existing already. Passing..")
        
    connection.commit()
    
    return new_users

def main(accounts, connection):
    current_date = date.today()
    
    for user in accounts:
        user_id = user[0]
        username = user[1]
        
        url = create_url(user_id)
        params = get_params()
        json_response = connect_to_endpoint_test(url, params)
        
        # stores data for further filtering
        data = []

        # get the json data twitter usernames and append to list with current date
        for res in json_response['data']:
            data.append([res['username'], current_date])
            
        # get only the usernames in a list
        users_list = [i[0] for i in data]
        
        # find if that twitter username already exists in the database for a particular user
        new_data = save_to_db(connection, username, users_list, current_date)
        
        send_to_discord_single(new_data, username, current_date)
        # # batch sending
        # discord_data[username] = new_data
    
    ## batch sending
    # send_to_discord_batch(discord_data, current_date)
    
    

def insert_accounts(connection):
    cursor = connection.cursor()
    
    records = []
    try:
        with open('accounts.csv', newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            for twitter_id, twitter_username in reader:
                records.append((twitter_id, twitter_username))
    except:
        print("Can't find accounts.csv file")    
    
    sql_insert_query = """ INSERT INTO accounts (twitter_id, twitter_username) 
                           VALUES (%s,%s) """
    create_table = """
    CREATE TABLE IF NOT EXISTS accounts (
    twitter_id VARCHAR(64) PRIMARY KEY,
    twitter_username VARCHAR(64) UNIQUE NOT NULL);
    """
    cursor.execute(create_table)
    try:
        cursor.executemany(sql_insert_query, records)
    except:
        print("Values existing already. Passing..")
        pass

    connection.commit()
    count = cursor.rowcount
    print(count, "Record inserted successfully into accounts table")


def get_rows(connection):
    query = "select * from accounts"
    cursor = connection.cursor()
    cursor.execute(query)
    records = cursor.fetchall()
    return records


if __name__ == "__main__":
    connection = connect(sys.argv)
    if connection is not None:
        insert_accounts(connection)
        accounts = get_rows(connection)
        main(accounts, connection)
        close(connection)
    else:
        print('Connection problem.')

        