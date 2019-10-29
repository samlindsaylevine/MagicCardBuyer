from typing import List
import sys	
import urllib
from bs4 import BeautifulSoup
from magiccardbuyer.buy_list_reader import Card, CardToBuy
from magiccardbuyer.configuration import Configuration
from magiccardbuyer.store_interface import ExecutablePurchaseOption, StoreInterface
from magiccardbuyer.webpage_reader import WebpageReader

class TcgPlayerInterface(StoreInterface):
	"""TCG Player has a REST API, but it requires manually signing up and getting human-approved
	to get an API key. I don't want script users to have to do that, and I definitely don't want
	to get such a key myself and then check it into Github. So, it's HTML scraping ahoy in here.
	I guess that's the public, unauthenticated interface...
	"""

	minimum_purchase = Configuration().minimum_purchase

	def __init__(self, webpage_reader = None):
		self.verbose = True
		self.allowedConditions = ["Near Mint", "Lightly Played"]
		self.webpage_reader = WebpageReader.from_config(Configuration()) if webpage_reader is None else webpage_reader

	def find_options(self, card: Card) -> List[ExecutablePurchaseOption]:
		self.write(f"Finding purchase options for {card.name} from {card.setName}\n")
		product_ids = self._find_product_ids(card)
		options = [option for product_id in product_ids for option in self._purchase_options(card, product_id)]
		# Right now, only allowing those with free shipping.
		# Room for improvement: allow those with threshold shipping and have minimum purchase prices per vendor
		return [option for option in options if option.condition in self.allowedConditions and option.minimumPurchase == TcgPlayerInterface.minimum_purchase]

	def write(self, message):
	  if self.verbose:
	    sys.stderr.write(message)

	def _find_product_ids(self, card: Card) -> List[str]:
		# For a set:
		# https://shop.tcgplayer.com/magic/war-of-the-spark?ProductName=giant+growth
		# For no set:
		# https://shop.tcgplayer.com/magic/product/show?ProductName=giant+growth
		cardPath = self._card_name_path_element(card.name)
		url = (f"https://shop.tcgplayer.com/magic/product/show?ProductName={cardPath}" if card.setName is None
			else f"https://shop.tcgplayer.com/magic/{self._set_path_element(card.setName)}?ProductName={cardPath}") 
		html = self.webpage_reader.read(url)
		page = BeautifulSoup(html, 'html.parser')
		return [self._extract_product_id(link.get('href')) for link in page.find_all('a', class_="product__price-guide")]

	def _set_path_element(self, set: str) -> str:
		return set.lower().replace(" ", "-")

	def _card_name_path_element(self, cardName: str) -> str:
		return urllib.parse.quote_plus(cardName.lower())

	def _extract_product_id(self, price_guide_url: str) -> str:
		prefix = "#a"
		index = price_guide_url.find(prefix)
		if index == -1:
			raise TcgPlayerError(f"Could not parse product ID from {price_guide_url}")
		return price_guide_url[index + len(prefix):]

	def _purchase_options(self, card: Card, productId: str):
		url = f"https://shop.tcgplayer.com/productcatalog/product/getpricetable?pageSize=50&productId={productId}&gameName=magic"
		html = self.webpage_reader.read(url)
		page = BeautifulSoup(html, 'html.parser')
		listings = page.find_all("div", class_="product-listing")
		return [TcgPlayerPurchaseOption.from_node(card, listing) for listing in listings]

class TcgPlayerPurchaseOption(ExecutablePurchaseOption):
	def __init__(self, card, vendor, availableQuantity, price, purchaseId, condition, minimumPurchase):
		self.good = card
		self.vendor = vendor
		self.availableQuantity = availableQuantity
		self.price = price
		# TODO - base off purchase ID, see what happens when we purchase
		self.purchase = lambda quantity: print(f"Buying {quantity} {card.name} from {vendor}")
		self.condition = condition
		self.minimumPurchase = minimumPurchase

	@classmethod
	def from_node(cls, card: Card, soupNode):
		vendor = soupNode.find("a", class_="seller__name").string.strip()
		availableQuantity = int(soupNode.find(id="quantityAvailable").get("value"))
		(price, minimumPurchase) = TcgPlayerPurchaseOption._price_and_minimum(soupNode) 
		purchaseId = soupNode.find(id="priceId").get("value") 
		condition = soupNode.find(class_="condition").string.strip()
		return TcgPlayerPurchaseOption(card, vendor, availableQuantity, price, purchaseId, condition, minimumPurchase)

	@classmethod
	def _price_and_minimum(cls, soupNode):
		base_price = TcgPlayerPurchaseOption._cents_from_price(soupNode.find(class_="product-listing__price").string)
		shipping_node = soupNode.find(class_="product-listing__shipping")
		purchase_link = shipping_node.find("a")
		if purchase_link is None:
			# Shipping cost is additional; only the base minimum price applies.
			shipping_cost_str = shipping_node.contents[-1].strip()
			shipping_cost = TcgPlayerPurchaseOption._parse_shipping_cost(shipping_cost_str)
			return (base_price + shipping_cost, TcgPlayerInterface.minimum_purchase)
		else:
			# Shipping is free (with a minimum).
			return (base_price, TcgPlayerPurchaseOption._parse_minimum(purchase_link.string))


	@classmethod
	def _cents_from_price(cls, price: str) -> int:
		assert price.startswith('$')
		return int(price[1:].replace('.', ''))

	@classmethod
	def _parse_shipping_cost(cls, shipping_cost_str: str) -> int:
		prefix = "+ Shipping: "
		if (shipping_cost_str.startswith(prefix)):
			return TcgPlayerPurchaseOption._cents_from_price(shipping_cost_str[len(prefix):])
		raise TcgPlayerError(f"Couldn't parse shipping cost {shipping_cost_str}")

	@classmethod
	def _parse_minimum(cls, minimumStr: str) -> int:
		if (minimumStr == "+ Shipping: Included"):
			return TcgPlayerInterface.minimum_purchase
		ordersOver = "Free Shipping on Orders Over $"
		if (minimumStr.startswith(ordersOver)):
			return int(minimumStr[len(ordersOver):]) * 100
		raise TcgPlayerError(f"Couldn't parse minimum purchase {minimumStr}")


class TcgPlayerError(Exception):
	def __init__(self, message):
		super().__init__(message)

if __name__ == '__main__':
	options = TcgPlayerInterface().find_options(Card("Giant Growth", None))
	options[0].purchase(1)