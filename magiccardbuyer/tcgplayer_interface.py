from typing import List
from buy_list_reader import CardToBuy
from store_interface import ExecutablePurchaseOption, StoreInterface

class TcgPlayerInterface(StoreInterface):
	def find_options(self, cardTobuy: CardToBuy) -> List[ExecutablePurchaseOption]:
		return []

if __name__ == '__main__':
	options = TcgPlayerInterface().find_options(CardToBuy("Crow Storm", 1, "Unstable"))
	print(options)