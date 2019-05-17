from abc import ABC, abstractmethod
from typing import Callable, List
from buy_list_reader import Card
from buy_optimizer import PurchaseOption

class ExecutablePurchaseOption(PurchaseOption):
	purchase: Callable[[int], None]

class StoreInterface(ABC):
	@abstractmethod
	def find_options(card: Card) -> List[ExecutablePurchaseOption]:
		pass