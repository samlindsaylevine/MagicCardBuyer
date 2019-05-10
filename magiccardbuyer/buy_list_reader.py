from dataclasses import dataclass
from typing import List, Optional
import re
import sys

@dataclass
class CardToBuy:
  name: str
  quantity: int
  setName: Optional[str]

class BuyListReader:
  def read(self, inputStream = sys.stdin) -> List[CardToBuy]:    
    currentSet = None
    
    output = []
    
    for line in inputStream:
      line = line.strip()
      if (line == ""):
        # Ignore empty lines.
        pass
      elif line[len(line) - 1] == ":":
        # Lines ending in colons are either rarities (ignore) or set names.
        if (line in ["Common:",
                     "Uncommon:",
                     "Rare:",
                     "Flip:"]):
          #Ignore rarities.
          pass
        else:
          currentSet = line[0:len(line) - 1]
          if currentSet == "Any":
            currentSet = None
      else:
        # All other lines are card names.
        cardRegex = "(\d*)\s*(.*)"
        match = re.match(cardRegex, line)
        quantityStr = match.group(1)
        if (quantityStr == ""):
          quantity = 1
        else:
          quantity = int(quantityStr)
        cardName = match.group(2)
        output.append(CardToBuy(cardName, quantity, currentSet))
    
    return output
    
if __name__ == "__main__":
  reader = BuyListReader()
  print(reader.read())