#! /usr/bin/env python
import sys
import urllib2
import urllib

nameFile = sys.stdin

cardName = nameFile.readline()

htmlPage = "<html><head></head><body>\n"

# readline returns the empty string at the end of the file
while (not (cardName == "")):
  # remove the trailing newline character that readline gives us
  cardName = cardName.strip()
  sys.stderr.write(".")
  
  # go get the magiccards.info page for this card
  url = 'http://magiccards.info/card.php?card=' + \
        cardName
  magiccardsURL = urllib2.urlopen(url.replace(" ", "%20"))
  magiccardsPage = magiccardsURL.read()
  
  # get the image out of this page
  # find the start of the card image block
  tableLocation = magiccardsPage.find('td width="312"')
  cardSrcStart = magiccardsPage.find("img src=", tableLocation)
  cardImageLocationStart = magiccardsPage.find('"', cardSrcStart)
  cardImageLocationStop = magiccardsPage.find('"', cardImageLocationStart + 1)
  
  absoluteLocation = magiccardsPage[cardImageLocationStart+1:cardImageLocationStop]
  
  if (tableLocation == -1 or absoluteLocation == ""):
    sys.stderr.write(cardName + ": unable to find image")
  else:
    htmlPage = htmlPage + '<img src = "' + absoluteLocation + '" height="317" width="222" />\n'
  
  cardName = nameFile.readline()
  
htmlPage = htmlPage + "</body></html>"
# Open for writing
output = sys.stdout
output.write(htmlPage)

# Put a newline on stderr, just for convenience.
sys.stderr.write("\n")