import re
import sys
import urllib
from typing import List

from bs4 import BeautifulSoup

from magiccardbuyer.buy_list_reader import Card
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

    def __init__(self, webpage_reader=None):
        self.verbose = True
        self.allowedConditions = ["Near Mint", "Lightly Played"]
        self.webpage_reader = WebpageReader.from_config(Configuration()) if webpage_reader is None else webpage_reader

    def find_options(self, card: Card) -> List[ExecutablePurchaseOption]:
        self.write(f"Finding purchase options for {card.name} from "
                   f"{'any set' if card.setName is None else card.setName}\n")
        product_ids = self._find_product_ids(card)
        purchase_options = [option for product_id in product_ids for option in self._purchase_options(card, product_id)]
        # Right now, only allowing those with free shipping.
        # Room for improvement: allow those with threshold shipping and have minimum purchase prices per vendor
        return [option for option in purchase_options if
                option.condition in self.allowedConditions and
                option.minimum_purchase == TcgPlayerInterface.minimum_purchase]

    def write(self, message):
        if self.verbose:
            sys.stderr.write(message)

    def _find_product_ids(self, card: Card) -> List[str]:
        # For a set:
        # https://shop.tcgplayer.com/magic/war-of-the-spark?ProductName=giant+growth
        # For no set:
        # https://shop.tcgplayer.com/magic/product/show?ProductName=giant+growth
        card_path = self._card_name_path_element(card.name)
        url = (f"https://shop.tcgplayer.com/magic/product/show?ProductName={card_path}" if card.setName is None
               else f"https://shop.tcgplayer.com/magic/{self._set_path_element(card.setName)}?ProductName={card_path}")
        html = self.webpage_reader.read(url)
        page = BeautifulSoup(html, 'html.parser')
        # Need to filter to pick only options that match the provided card name exactly.
        return [self._extract_product_id(details_node) for details_node in
                page.find_all('div', class_="product__details")
                if self._extract_product_name(details_node) == card.name]

    @staticmethod
    def _set_path_element(set_name: str) -> str:
        return set_name.lower().replace(" ", "-")

    @staticmethod
    def _card_name_path_element(card_name: str) -> str:
        return urllib.parse.quote_plus(card_name.lower())

    @staticmethod
    def _extract_product_name(product_details_node) -> str:
        raw_name = product_details_node.find('a', class_="product__name").string.strip()
        # For some reason the names often have lots of spaces between words; normalize to one.
        return re.sub('\\s+', ' ', raw_name)

    @staticmethod
    def _extract_product_id(product_details_node) -> str:
        link = product_details_node.find('a', class_="product__price-guide")
        price_guide_url = link.get('href')
        prefix = "#a"
        index = price_guide_url.find(prefix)
        if index == -1:
            raise TcgPlayerError(f"Could not parse product ID from {price_guide_url}")
        return price_guide_url[index + len(prefix):]

    def _purchase_options(self, card: Card, product_id: str):
        url = f"https://shop.tcgplayer.com/productcatalog/product/getpricetable?pageSize=50&productId={product_id}" + \
              "&gameName=magic"
        html = self.webpage_reader.read(url)
        page = BeautifulSoup(html, 'html.parser')
        listings = page.find_all("div", class_="product-listing")
        return [TcgPlayerPurchaseOption.from_node(card, listing) for listing in listings]


class TcgPlayerPurchaseOption(ExecutablePurchaseOption):
    def __init__(self, card, vendor, available_quantity, price, purchase_id, condition, minimum_purchase):
        self.good = card
        self.vendor = vendor
        self.availableQuantity = available_quantity
        self.price = price
        self.purchase_id = purchase_id
        # TODO - base off purchase ID, see what happens when we purchase
        self.purchase = lambda quantity: print(f"Buying {quantity} {card.name} from {vendor} at {self.price}")
        self.condition = condition
        self.minimum_purchase = minimum_purchase

    def key(self):
        return self.purchase_id

    @classmethod
    def from_node(cls, card: Card, soup_node):
        vendor = soup_node.find("a", class_="seller__name").string.strip()
        available_quantity = int(soup_node.find(id="quantityAvailable").get("value"))
        (price, minimumPurchase) = TcgPlayerPurchaseOption._price_and_minimum(soup_node)
        purchase_id = soup_node.find(id="priceId").get("value")
        condition = soup_node.find(class_="condition").string.strip()
        return TcgPlayerPurchaseOption(card, vendor, available_quantity, price, purchase_id, condition, minimumPurchase)

    @classmethod
    def _price_and_minimum(cls, soup_node):
        base_price = TcgPlayerPurchaseOption._cents_from_price(soup_node.find(class_="product-listing__price").string)
        shipping_node = soup_node.find(class_="product-listing__shipping")
        purchase_link = shipping_node.find("a")
        if purchase_link is None:
            # Shipping cost is additional; only the base minimum price applies.
            shipping_cost_str = shipping_node.contents[-1].strip()
            shipping_cost = TcgPlayerPurchaseOption._parse_shipping_cost(shipping_cost_str)
            return base_price + shipping_cost, TcgPlayerInterface.minimum_purchase
        else:
            # Shipping is free (with a minimum).
            return base_price, TcgPlayerPurchaseOption._parse_minimum(purchase_link.string)

    @classmethod
    def _cents_from_price(cls, price: str) -> int:
        assert price.startswith('$')
        return int(price[1:].replace('.', ''))

    @classmethod
    def _parse_shipping_cost(cls, shipping_cost_str: str) -> int:
        prefix = "+ Shipping: "
        if shipping_cost_str.startswith(prefix):
            return TcgPlayerPurchaseOption._cents_from_price(shipping_cost_str[len(prefix):])
        raise TcgPlayerError(f"Couldn't parse shipping cost {shipping_cost_str}")

    @classmethod
    def _parse_minimum(cls, minimum_str: str) -> int:
        if minimum_str == "+ Shipping: Included":
            return TcgPlayerInterface.minimum_purchase
        orders_over = "Free Shipping on Orders Over $"
        if minimum_str.startswith(orders_over):
            return int(minimum_str[len(orders_over):]) * 100
        raise TcgPlayerError(f"Couldn't parse minimum purchase {minimum_str}")


class TcgPlayerError(Exception):
    def __init__(self, message):
        super().__init__(message)
