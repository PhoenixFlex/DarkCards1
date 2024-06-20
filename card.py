import random
import sqlite3
class Card:
    def __init__(self,verse): #инициализация
        self.verse = verse

    def rarity_generator(self):
        cards = {
            'Basic': 69.5,
            'Unusual': 20,
            'Epic': 8,
            'Legendary': 2,
            'Mythic': 0.5
        }
        self.rarity = random.choices(list(cards.keys()), weights=cards.values())[0]

        
    def generate_card(self):
        self.point_values = {
            "Basic":1000,
            'Unusual':2000,
            'Epic':3000,
            'Legendary':5000,
            'Mythic':10000
        }
        
        self.rarity_generator()
        conn = sqlite3.connect(f"verse_{self.verse}.db")
        curs = conn.cursor()
        curs.execute(f'''SELECT card_name,photo,rarity,hp,attack,defense,crit_rate,speed FROM {self.verse} WHERE rarity = ?''',(self.rarity,))
        result = curs.fetchall()
        conn.close()
        card_num = random.randint(0,len(result)-1)
        card_name = result[card_num][0]
        card_photo = result[card_num][1]
        card_hp = result[card_num][3]
        card_attack = result[card_num][4]
        card_defense = result[card_num][5]
        card_crit_rate = result[card_num][6]
        card_speed = result[card_num][7]
        card_rarity = result[card_num][2]
        return card_name,card_photo,card_rarity,card_hp,card_attack,card_defense,card_crit_rate,card_speed
        



