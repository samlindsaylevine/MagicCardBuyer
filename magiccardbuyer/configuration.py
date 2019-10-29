import configparser

class Configuration:
	def __init__(self):
		config = configparser.ConfigParser()
		config.read("config.ini")
 
		price_str = config['MagicCardBuyer'].get("MaximumPrice")
		self.maximum_price = None if price_str is None else int(price_str)
		self.tcgplayer_username = config['TcgPlayer'].get("Username")
		self.tcgplayer_password = config['TcgPlayer'].get("Password")
		self.minimum_purchase = int(config['MagicCardBuyer'].get("MinimumPurchase"))
		self.cache = config['MagicCardBuyer'].get("Cache") == "True"