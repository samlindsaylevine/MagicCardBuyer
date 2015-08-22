import sys
from BidWicketInterface import BidWicketInterface
from BuyListReader import BuyListReader
from BuyOptimizer import BuyOptimizer

class MagicCardBuyer:
  def __init__(self):
    self.storeInterfaces = [ BidWicketInterface() ]
    
    self.verbose = True
    
    self.maximumAllowedPrice = 1.00
    
  def write(self, message):
    if self.verbose:
      sys.stderr.write(message)
    
  def buy(self):
    reader = BuyListReader()
    
    self.write("Reading from file...\n")
        
    buyList = reader.read()
    
    self.write("Found " + str(len(buyList)) + " cards to buy.\n")
    
    # This price list is a list of 3-tuples - (card name, quantity desired,
    # list of 4-tuples), where the 4-tuples are the price options, each tuple
    # being (store name, set name, quantity available, price).
    priceList = []
    
    self.write("Retrieving price information...\n")
    
    cardNumber = 0
    
    for cardInfo in buyList:
      cardName, cardSet, quantity = cardInfo
      priceOptions = []
      for storeInterface in self.storeInterfaces:
        storeInterface.verbose = self.verbose
        priceOptions.extend(storeInterface.findPrices(cardName, cardSet))
      if len(priceOptions) == 0:
        raise Exception("Could not find card " + cardName)
      priceList.append((cardName, quantity, priceOptions))     
        
    getPriceFromOption = lambda(option) : option[3]
    getOptionsFromEntry = lambda(entry) : entry[2]
    getMinPriceFromEntry = lambda(entry) : reduce(min, map(getPriceFromOption,
                                                           getOptionsFromEntry(entry)))
    
    if self.maximumAllowedPrice > 0:
      tooExpensiveEntries = [entry for entry in priceList if 
                             getMinPriceFromEntry(entry) > self.maximumAllowedPrice]
      tooExpensiveCards = []
      for entry in tooExpensiveEntries:
        tooExpensiveCards.extend([entry[0]] * entry[1])                         
      priceList = [entry for entry in priceList if 
                     getMinPriceFromEntry(entry) <= self.maximumAllowedPrice]
            
    self.write("\nOptimizing purchase...\n")
      
    optimizer = BuyOptimizer()
    optimizer.verbose = self.verbose
    
    # This is a list of orders; each order is a tuple (card name, list) with 
    # the list containing 3-tuples that are (store name, set name, quantity).
    buyOrders = optimizer.solve(priceList)
    
    self.write("Estimated total cost: " + str(optimizer.totalPrice(buyOrders)) + "\n")
    
    for buyOrder in buyOrders:
      cardName, orderList = buyOrder
      totalQuantity = sum([order[2] for order in orderList])
      totalPrice = sum([order[2]*order[3] for order in orderList])
      priceString = ", ".join([str(order[2]) + " @ " + str(order[3])])
      #self.write(str(totalQuantity) + " " + cardName + ": " + priceString + "; total " + str(totalPrice) + "\n")
    
    self.write("Purchasing cards...\n")
       
    cardNumber = 0
    
    for buyOrder in buyOrders:
      cardName, orderList = buyOrder
      
      for order in orderList:
        storeName, setName, quantity, price = order
        for interface in self.storeInterfaces:
          if storeName in interface.storeNames:
            try:
              interface.buyCard(cardName, storeName, setName, quantity)
              pass
            except:
              self.write("\nUnable to purchase " + str(quantity) + " " + setName + " " + cardName + " from " + storeName + "\n")
            
      cardNumber = cardNumber + 1
      self.write(".")
      if (cardNumber % 10 == 0):
        self.write("[" + str(cardNumber) + "]")
        
    self.write("\n")
    
    if self.maximumAllowedPrice > 0:
      self.write("Outputting unpurchased cards...\n")
      for cardName in tooExpensiveCards:
        print cardName
    
        
if __name__ == "__main__":
  buyer = MagicCardBuyer()
  buyer.buy()