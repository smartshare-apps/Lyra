import sqlite3
import MySQLdb
import database.config as config


def instance_handle():
    try:
        conn = sqlite3.connect('modules/instance_config.db')
        conn.text_factory = str
    except Exception as e:
        print 'Error opening instance database: ', e
        return None
    return conn


def db_handle(instance_db):
    db_settings = config.getDatabaseSettings(instance_db.cursor())
    print db_settings

    try:
        conn = MySQLdb.connect(host=db_settings['host'], port=int(db_settings['port']), user=db_settings['username'],
                               passwd=db_settings['password'], db=db_settings['default_db'], use_unicode=True,
                               charset='utf8', connect_timeout=1)
    except Exception as e:
        print 'Exception connecting: ', e
        return None
    return conn


def setup_db():
    pass
