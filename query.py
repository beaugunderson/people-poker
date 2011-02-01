import sqlalchemy
import simplejson


def query_user_status(userid):
    """ Returns JSON output for current status of user matching userid. """

    # Read config file
    db = MySQLdb.connect(
        host=self.settings['host'],
        user=self.settings['user'],
        passwd=self.settings['password'],
        db=self.settings['database'])

    cursor = db.cursor()

    cursor.execute("""
            SELECT * FROM current_user_status
            WHERE userid REGEXP %s
            """,  userid)

    statuslist = cursor.fetchall()
    return json_encode(statuslist)


def json_encode(statuslist):
    l = []

    for user, status, last_seen in statuslist:
        l.append({"user": user,
                  "status": status,
                  "last_seen": last_seen.isoformat()})

    return json.dumps(l)

if __name__ == "__main__":
    query_user_status("peter")
