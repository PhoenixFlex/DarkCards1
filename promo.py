import sqlite3

conn = sqlite3.connect("verse_onepunchman.db")
curs = conn.cursor()
curs.execute(f'''CREATE TABLE IF NOT EXISTS onepunchman (id INTEGER PRIMARY KEY AUTOINCREMENT,card_name TEXT, rarity TEXT,photo TEXT, card_info TEXT,hp INTEGER,attack INTEGER,defense INTEGER,crit_rate INTEGER,speed INTEGER)''')