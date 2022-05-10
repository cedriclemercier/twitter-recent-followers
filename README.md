# Query recent twitter account followings

This app query what a selected twitter account has been following recently and send it to a discord bot. 
Interacts with twitter API

```bash
├── databases
│    └── an_account.csv     # recent followings saved as a csv file named 
│                           # after the account
├── main.py                 
├── database.ini            # local DB config
├── .env                    # local env variables
└── test_data.json          # For development and API limits query a json 
                            # file containing recent followers used in 
                            # connect_to_endpoint_test in main()
```

## Packages
- `requests`
- `discord`: to interact with discord api
- `decouple`: for local development
- `psycopg2`: for postgres

## Local Development

Create an `.env` file containing these variables
- `WEBHOOK` = discord bot webhook
- `MAX_RESULTS` = limit the number of recent follows queried every time
- `MESSAGE_TEMPLATE` = Custom message to discord bot, like "Hello! This is the daily digest of followings"
- `BEARER_TOKEN`= Bearer token obtained on your own twitter app that allows interacting with the api. You need to create an app for this check https://developer.twitter.com
-`DATABASE_URL`=heroku database URL

### Initialising

In root folder, create an `accounts.csv` file containing 2 columns, column 1 is twitter ID and 2nd is twitter username. These are the accounts you want to retrieve followings from
Example:

`accounts.csv`
```python
123124129,elonmusk
121241242,ladygaga
```

You can create a `test_data.json` file to query dummy data.
To use it, modify the line in `main.py`
```python
json_response = connect_to_endpoint(url, params)
# change it to
json_response = connect_to_endpoint_test(url, params)
```
Data queried from recent followings will follow this structure:
```json
{
    "data": [
        {
            "created_at": "2018-02-28T09:50:25.000Z",
            "id": "123456789",
            "name": "Elon Musk",
            "username": "elonmusk"
        },
        ...
    ]
}
```

### database.ini file
To use local postgres database, create a `database.ini` config file:
```ini
[postgresql]
host=localhost
database=dbname
user=your-username
password=your-password
```

### Running the script
Just type `python main.py` - will automatically connect to heroku DB URL set in environment variables file, create a `account` table and select data from `accounts.csv` file and insert it into the table

**TO USE LOCAL DATABASE** -> run `python main.py dev` with that extra argument

Then data retrieved will be saved into file named after the accounts retrieved from in `/databases` as csv files, and new data will be send to the discord webhook provided in environment variables.


## Running on Heroku
You can set it as a cron scheduled job and run this script once or twice per day like a daily digest