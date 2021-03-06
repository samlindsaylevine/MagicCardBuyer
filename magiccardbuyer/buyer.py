import sys
from collections import Counter

from magiccardbuyer.buy_list_reader import BuyListReader
from magiccardbuyer.buy_optimizer import BuyOptimizer, VendorProblem
from magiccardbuyer.configuration import Configuration
from magiccardbuyer.tcgplayer_interface import TcgPlayerInterface


class MagicCardBuyer:
    def __init__(self):
        self.storeInterfaces = [TcgPlayerInterface()]

        self.verbose = True

        self.config = Configuration()

    def write(self, message):
        if self.verbose:
            sys.stderr.write(message)
            sys.stderr.flush()

    def buy(self, input_stream=sys.stdin):
        reader = BuyListReader()

        self.write("Reading from file...\n")

        buy_list = reader.read(input_stream)

        self.write(f"Found {len(buy_list)} cards to buy.\n")
        self.write("Retrieving price information...\n")

        # Retrieve PurchaseOptions from the store interfaces.
        options = []
        cards_sought = Counter()
        too_expensive = []

        for cardToBuy in buy_list:
            card_options = [option for store in self.storeInterfaces
                            for option in store.find_options(cardToBuy.card)]
            # For any card that is too expensive - i.e., no purchase options exist below our maximum price -
            # skip it and instead add it to our "too expensive list" for output later.
            if self.config.maximum_price is not None and all(
                    option.price > self.config.maximum_price for option in card_options):
                self.write(f"Too expensive {cardToBuy.card}\n")
                too_expensive.append(cardToBuy)
            else:
                # self.write(f"{cardToBuy.card}: {cardToBuy.quantity}\n")
                cards_sought[cardToBuy.card] += cardToBuy.quantity
                options.extend(card_options)

        # Calculate the minimum price for each vendor we discovered amongst our options.
        vendors = {option.vendor for option in options}
        min_by_vendor = {vendor: max([option.minimum_purchase for option in options if option.vendor == vendor
                                      and option.minimum_purchase is not None])
                         for vendor in vendors}

        self.write("Defining purchase problem...\n")
        problem = VendorProblem(dict(cards_sought), options, min_by_vendor)
        self.write("Optimizing purchase options...\n")
        solution = BuyOptimizer().solve(problem)
        self.write(f"Solved; total cost {solution.totalCost}\n")

        self.write("Executing " + str(len(solution.purchasesToMake)) + " purchases...\n")
        purchased_count = 0
        for purchaseToMake in solution.purchasesToMake:
            purchaseToMake.option.purchase(purchaseToMake.quantity)
            purchased_count += 1
            if purchased_count % 10 == 0:
                self.write("[" + str(purchased_count) + "]")
            else:
                self.write(".")
        self.write("\n")

        # Output anything that was too expensive.
        if len(too_expensive) > 0:
            self.write("Outputting unpurchased cards...\n")
        for cardToBuy in too_expensive:
            print(f"{cardToBuy.quantity} {cardToBuy.card.name}")


if __name__ == "__main__":
    buyer = MagicCardBuyer()
    buyer.buy()
