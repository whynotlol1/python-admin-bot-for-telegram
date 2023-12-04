import sqlite3
import json
import time
import os

conn = sqlite3.connect("data/data.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS groups (
    id INTEGER,
    current_preset TEXT
)
""")
conn.commit()
cur.execute("""
CREATE TABLE IF NOT EXISTS reported_users (
    username TEXT,
    group_id INTEGER,
    reports INTEGER
)
""")
conn.commit()
cur.execute("""
CREATE TABLE IF NOT EXISTS muted_users (
    username TEXT,
    muted_in_group_id INTEGER,
    muted_from TEXT,
    muted_for TEXT
)
""")
conn.commit()


def add_group_to_table(group_id):
    check = cur.execute("SELECT * FROM groups WHERE id=?", (int(group_id),)).fetchone()
    if check is None:
        cur.execute("INSERT INTO groups VALUES (?,?)", (int(group_id), "default"))
        conn.commit()


def set_group_preset(group_id, preset_name):
    check = cur.execute("SELECT * FROM groups WHERE id=?", (int(group_id),)).fetchone()
    if check is not None:
        cur.execute("UPDATE groups SET current_preset=? WHERE id=?", (preset_name, int(group_id)))
        conn.commit()


def edit_preset(name, changed_field, changed_value):
    if os.path.isfile(f"config_presets/{name}.json"):
        with open(f"config_presets/{name}.json", "r") as f:
            json_dict = json.loads(f.read())
    else:
        with open("config_presets/default.json", "r") as f:
            json_dict = json.loads(f.read())
    json_dict[changed_field] = changed_value.lower()
    with open(f"config_presets/{name}.json", "w") as f:
        f.write(json.dumps(json_dict))


def get_from_config_preset(group_id, param):
    name = cur.execute("SELECT * FROM groups WHERE id=?", (int(group_id),)).fetchone()[1]
    with open(f"config_presets/{name}.json", "r") as f:
        json_dict = json.loads(f.read())
        return json_dict[param]


def mute_user(username, group_id, for_time):
    from_time = int(time.time())
    for_time = int(for_time) / 60
    data = (
        username,
        int(group_id),
        from_time,
        for_time
    )
    cur.execute("INSERT INTO muted_users VALUES (?,?,?,?)", data)
    conn.commit()


def check_if_user_muted(username, group_id):
    check = cur.execute("SELECT * FROM muted_users WHERE username=? AND muted_in_group_id=?", (username, int(group_id))).fetchone()
    return check is not None


def unmute_user_if_mute_passed_else_return_false(username, group_id):
    data = cur.execute("SELECT * FROM muted_users WHERE username=? AND muted_in_group_id=?", (username, int(group_id))).fetchone()
    if data[2] + data[3] >= int(time.time()):
        cur.execute("DELETE FROM muted_users WHERE username=? AND muted_in_group_id=?", (username, int(group_id)))
        conn.commit()
        return True
    return False


def unmute_user(username, group_id):
    cur.execute("DELETE FROM muted_users WHERE username=? AND muted_in_group_id=?", (username, int(group_id)))
    conn.commit()


def report_user(username, group_id):
    if get_from_config_preset(group_id, "report_system") == "true":
        check = cur.execute("SELECT * FROM reported_users WHERE username=? AND group_id=?", (username, int(group_id))).fetchone()
        if check is None:
            cur.execute("INSERT INTO reported_users VALUES (?,?,?)", (username, int(group_id), 0))
        else:
            old_reports = check[2]
            if old_reports + 1 == get_from_config_preset(group_id, "max_reports"):
                mute_user(username, group_id, get_from_config_preset(group_id, "default_mute_time"))
                cur.execute("UPDATE reported_users SET reports=? WHERE username=? AND group_id=?", (0, username, int(group_id)))
            else:
                cur.execute("UPDATE reported_users SET reports=? WHERE username=? AND group_id=?", (old_reports + 1, username, int(group_id)))
        conn.commit()
