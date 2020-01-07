import configparser


class Configuration:
    def __init__(self):
        config = configparser.ConfigParser()
        config.read("config.ini")

        price_str = config.get('MagicCardBuyer', "MaximumPrice", fallback=None)
        self.maximum_price = None if price_str is None else int(price_str)
        self.cache = config['MagicCardBuyer'].get("Cache") == "True"
        self.vendor_blacklist = config.get('MagicCardBuyer', 'VendorBlacklist', fallback='').split(',')
