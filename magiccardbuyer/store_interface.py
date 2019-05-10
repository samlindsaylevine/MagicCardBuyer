from abc import ABC, abstractmethod
from typing import List
from buy_list_reader import CardToBuy
from buy_optimizer import PurchaseOption

class ExecutablePurchaseOption(PurchaseOption):
	purchase: Callable[[int], None]

class StoreInterface(ABC):
	@abstractmethod
	def find_options(cardTobuy: CardToBuy) -> List[ExecutablePurchaseOption]:
		pass