import MySQLdb
import ConfigParser
import json

def query_user_status(userid):
    """ Returns JSON output for current status of user matching userid. """

    # Read config file
    config = ConfigParser.ConfigParser()
    config.read("config.ini")

    dbconn = MySQLdb.connect(
        host = config.get("database" , "host"),
        user = config.get("database" , "user"),
        passwd = config.get("database" , "password"),
        db = config.get("database" , "dbname"))

    cursor = dbconn.cursor()

    cursor.execute("""
            SELECT * FROM current_user_status
            WHERE userid REGEXP %s
            """,  userid )

    statuslist = cursor.fetchall()
    return json_encode(statuslist)

def json_encode(statuslist):
    l = []

    for user,status,last_seen in statuslist:
        l.append({ "user": user,
                   "status": status,
                   "last_seen": last_seen.isoformat() })
    print l

    return json.dumps(l)

if __name__ == "__main__":
    query_user_status("peter")
