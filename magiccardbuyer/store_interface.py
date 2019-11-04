from abc import ABC, abstractmethod
from typing import Callable, List
from magiccardbuyer.buy_list_reader import Card
from magiccardbuyer.buy_optimizer import PurchaseOption


class ExecutablePurchaseOption(PurchaseOption):
    purchase: Callable[[int], None]


class StoreInterface(ABC):
    @abstractmethod
    def find_options(self, card: Card) -> List[ExecutablePurchaseOption]:
        pass
