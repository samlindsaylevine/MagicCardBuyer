import configparser

class Configuration:
	def __init__(self):
		config = configparser.ConfigParser()
		config.read("config.ini")
		
		self.maximum_price = config['MagicCardBuyer'].get("MaximumPrice")
		self.tcgplayer_username = config['TcgPlayer'].get("Username")
		self.tcgplayer_password = config['TcgPlayer'].get("Password")