import configparser


class Configuration:
    def __init__(self, maximum_price, cache, vendor_blacklist):
        self.maximum_price = maximum_price
        self.cache = cache
        self.vendor_blacklist = vendor_blacklist

    @staticmethod
    def from_file():
        config = configparser.ConfigParser()
        config.read("config.ini")

        price_str = config.get('MagicCardBuyer', "MaximumPrice", fallback=None)
        maximum_price = None if price_str is None else int(price_str)
        cache = config['MagicCardBuyer'].get("Cache") == "True"
        vendor_blacklist = config.get('MagicCardBuyer', 'VendorBlacklist', fallback='').split(',')

        return Configuration(maximum_price, cache, vendor_blacklist)
