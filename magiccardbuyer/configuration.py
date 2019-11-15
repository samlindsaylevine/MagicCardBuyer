import configparser


class Configuration:
    def __init__(self):
        config = configparser.ConfigParser()
        config.read("config.ini")

        price_str = config.get('MagicCardBuyer', "MaximumPrice", fallback=None)
        self.maximum_price = None if price_str is None else int(price_str)
        self.tcgplayer_username = config.get('TcgPlayer', "Username")
        self.tcgplayer_password = config['TcgPlayer'].get("Password")
        self.cache = config['MagicCardBuyer'].get("Cache") == "True"
