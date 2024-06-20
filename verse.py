import sqlite3
import random

conn = sqlite3.connect(f"verse_tokyo_revengers.db")
curs = conn.cursor()

            


curs.execute('''SELECT rarity FROM tokyo_revengers''')
raw_all_rarities = curs.fetchall()

row_id = 97
all_rarities = [result[0] for result in raw_all_rarities]
for rarity in all_rarities:
    if rarity == "Basic":
        hp = random.randint(1000,1200)
        atk = random.randint(200,300)
        defense = random.randint(100,150)
        crit_rate = random.randint(1,10)
        spd = random.randint(80,120)
    if rarity == "Unusual":
        hp = random.randint(1200,1500)
        atk = random.randint(300,400)
        defense = random.randint(150,225)
        crit_rate = random.randint(5,15)
        spd = random.randint(85,125)
    if rarity == "Epic":
        hp = random.randint(1450,1900)
        atk = random.randint(375,525)
        defense = random.randint(200,350)
        crit_rate = random.randint(10,20)
        spd = random.randint(90,130)
    if rarity == "Legendary":
        hp = random.randint(2000,2500)
        atk = random.randint(500,700)
        defense = random.randint(375,475)
        crit_rate = random.randint(15,25)
        spd = random.randint(95,135)
    if rarity == "Mythic":
        hp = random.randint(3000,4500)
        atk = random.randint(650,900)
        defense = random.randint(500,600)
        crit_rate = random.randint(20,30)
        spd = random.randint(100,140)
    curs.execute(f'''UPDATE tokyo_revengers SET (hp,attack,defense,crit_rate,speed) = (?,?,?,?,?) WHERE rowid = ?''',(hp,atk,defense,crit_rate,spd,row_id))
    conn.commit()
    row_id +=1 

conn.close()