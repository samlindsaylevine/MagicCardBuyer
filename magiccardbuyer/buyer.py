from collections import Counter
import sys
from magiccardbuyer.buy_list_reader import BuyListReader, CardToBuy
from magiccardbuyer.buy_optimizer import VendorProblem
from magiccardbuyer.configuration import Configuration
from magiccardbuyer.tcgplayer_interface import TcgPlayerInterface

class MagicCardBuyer:
  def __init__(self):
    self.storeInterfaces = [ TcgPlayerInterface() ]
    
    self.verbose = True
    
    self.config = Configuration()
    
  def write(self, message):
    if self.verbose:
      sys.stderr.write(message)
    
  def buy(self, inputStream = sys.stdin):
    reader = BuyListReader()
    
    self.write("Reading from file...\n")
        
    buyList = reader.read(inputStream)
    
    self.write(f"Found {len(buyList)} cards to buy.\n")
    self.write("Retrieving price information...\n")

    # Retrieve PurchaseOptions from the store interfaces.
    options = []
    cardsSought = Counter()
    tooExpensive = []

    for cardToBuy in buyList:
      cardOptions = [option for store in self.storeInterfaces
        for option in store.find_options(cardToBuy.card) ]
      # For any card that is too expensive - i.e., no purchase options exist below our maximum price -
      # skip it and instead add it to our "too expensive list" for output later.
      if self.config.maximum_price is not None and all(option.price > self.config.maximum_price for option in cardOptions):
        tooExpensive.append(cardToBuy)
      else:
        cardsSought[cardToBuy.card] += cardToBuy.quantity
        options.extend(cardOptions)

    self.write("Optimizing purchase options...")
    problem = VendorProblem(cardsSought, options, config.minimum_purchase)
    solution = BuyOptimizer.solve(problem)
    self.write(f"Solved; total cost {solution.totalCost}")

    self.write("Executing purchases...")
    for purchaseToMake in solution.purchasesToMake:
      purchaseToMake.option.purchase(purchaseToMake.quantity)

    # Output anything that was too expensive.
    if len(tooExpensive > 0):
      self.write("Outputting unpurchased cards...\n")
    for cardToBuy in tooExpensive:
      print(f"{cardToBuy.quantity} {cardToBuy.card.name}")    


if __name__ == "__main__":
  buyer = MagicCardBuyer()
  buyer.buy()
