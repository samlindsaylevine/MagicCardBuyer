import sys
from itertools import chain, combinations

class BuyOptimizer:
  def __init__(self):
    self.verbose = False
    
    # To save time when there is a very large number of vendors, we cap the
    # number of stores we are willing to allow into our order. This puts the
    # performance at (numberOfVendors)^(maxNumberOfStores) instead of 
    # 2 ^ (numberOfVendors).
    # From our knowledge of the problem domain, we think that the optimal
    # solution is very unlikely to require more than this number of stores
    # anyways.
    self.maxNumberOfStores = 6

  def write(self, message):
    if self.verbose:
      sys.stderr.write(message)
  
  # Returns a list of orders; each order is a tuple (card name, list) with
  # the list containing 3-tuples that are (store name, set name, quantity,
  # price).
  def solve(self, priceList):
    # The price list is a list of 3-tuples (card name, quantity desired, list) 
    # with the list containing 4-tuples (store name, set name, 
    # quantity available, price).
    
    bestOrder = None
    bestPrice = None
    
    allStores = set()
    for entry in priceList:
      for buyOption in entry[2]:
        allStores.add(buyOption[0])
 
    self.write("Considering options from among " + 
               str(len(allStores)) + 
               " stores...\n")
    
    optionNumber = 0
    
    for storeCombination in self.powerset(allStores, self.maxNumberOfStores):
      order = self.greedy(priceList, storeCombination)
      if order is not None and (bestPrice is None or 
                                self.totalPrice(order) < bestPrice):
        bestOrder = order
        bestPrice = self.totalPrice(order)
      optionNumber += 1
      if (optionNumber % 1000 == 0):
        self.write(".")
      if (optionNumber % 10000 == 0):
        self.write("[" + str(optionNumber) + "]")
        
    self.write("\n")
    
    return bestOrder
    
  def totalPrice(self, orderList):
    includedStores = set()
    
    output = 0.0
    
    for entry in orderList:
      for buyOption in entry[1]:
        includedStores.add(buyOption[0])
        output += buyOption[2] * buyOption[3]
        
    costPerStore = 5.0
    
    output += costPerStore * len(includedStores)
    
    return output
   
  # The 'greedy' solution, picking the cheapest option for each individual
  # item. allowedStores may be None in which case all stores are allowed, or
  # it may be a list of stores, in which case only options from those stores
  # are allowed.
  # If the purchase cannot be made with the allowed stores, None is returned.
  def greedy(self, priceList, allowedStores=None):
    output = []
    
    for priceItem in priceList:
      cardName, quantityDesired, optionList = priceItem
      # Sort all the options by price.
      optionList = sorted(optionList, key = (lambda(entry) : entry[3]))
      
      purchaseList = []
      
      while quantityDesired > 0 and len(optionList) > 0:
        firstOption = optionList[0]
        storeName, setName, quantityAvailable, price = firstOption
        if allowedStores == None or storeName in allowedStores:
          if quantityAvailable >= quantityDesired:
            purchaseList.append((storeName, setName, quantityDesired, price))
            quantityDesired = 0
          else:
            purchaseList.append((storeName, setName, quantityAvailable, price))
            quantityDesired -= quantityAvailable
            optionList = optionList[1:]
        else:
          # This store was not allowed; remove it and continue.
          optionList = optionList[1:]
          
      # If there were not enough of the card available, fail.
      if quantityDesired > 0:
        return None
          
      output.append((cardName, purchaseList))
      
    return output
    
  # Returns an iterator on all possible unordered tuples with elements chosen 
  # from a provided iterable. If a maximum tuple size is provided, only tuples
  # up to that size are included.
  def powerset(self, iterable, maxTupleSize=None):
    s = list(iterable)
    if maxTupleSize is None:
      maxTupleSize = len(s)
    return chain.from_iterable(combinations(s, r) for r in range(maxTupleSize + 1))
    
    
if __name__ == "__main__":
  samplePriceList = [("Card A", 3, [("Store 1", "Tempest", 2, 3.7),
                                    ("Store 2", "Tempest", 17, 5.0),
                                    ("Store 3", "Mirage", 2, 0.01)]),
                     ("Card B", 1, [("Store 1", "Ice Age", 1, 0.04),
                                    ("Store 2", "Ice Age", 1, 0.03),
                                    ("Store 3", "Ice Age", 7, 0.06)]),
                     ("Card C", 17, [("Store 1", "Legends", 100, 0.04),
                                     ("Store 2", "Legends", 1, 0.03),
                                     ("Store 3", "Legends", 19, 0.05)])]
  optimizer = BuyOptimizer()
  greedySolution = optimizer.greedy(samplePriceList)
  print greedySolution, optimizer.totalPrice(greedySolution)
  solution = optimizer.solve(samplePriceList)
  print solution, optimizer.totalPrice(solution)                                   