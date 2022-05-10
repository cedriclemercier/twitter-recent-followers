#!/usr/bin/python
from configparser import ConfigParser
import psycopg2
from decouple import config
import os


DATABASE_URL = os.environ.get('DATABASE_URL', config('DATABASE_URL'))


def database_config(filename='database.ini', section='postgresql'):
    # create a parser
    parser = ConfigParser()
    # read config file
    parser.read(filename)

    # get section, default to postgresql
    db = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
    else:
        raise Exception('Section {0} not found in the {1} file'.format(section, filename))

    return db


def connect(args):
    """ Connect to the PostgreSQL database server """
    conn = None
    try:
        
        # if dev is passed as an arg, use local database
        if (len(args) > 1):
            if (args[1] == 'dev'):
                
                # read connection parameters
                params = database_config()

            # connect to the PostgreSQL server
                print('Connecting to the PostgreSQL database locally...')
                conn = psycopg2.connect(**params)
                      # create a cursor
                cur = conn.cursor()
                
            # execute a statement
                print('PostgreSQL database version:')
                cur.execute('SELECT version()')

                # display the PostgreSQL database server version
                db_version = cur.fetchone()
                print(db_version)
            
            # close the communication with the PostgreSQL
                cur.close()

            else:
                raise NameError('argument {} not correct! Should be dev!'.format(args[1]))
        else:
            print('Connecting to the PostgreSQL database on heroku...')
            conn = psycopg2.connect(DATABASE_URL, sslmode='require')
		
            # create a cursor
            cur = conn.cursor()
            
        # execute a statement
            print('PostgreSQL database version:')
            cur.execute('SELECT version()')

            # display the PostgreSQL database server version
            db_version = cur.fetchone()
            print(db_version)
        
        # close the communication with the PostgreSQL
            cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            return conn

def close(conn):
    conn.close()
    print('Database connection closed.')
    
# if __name__ == '__main__':
#     connect()
