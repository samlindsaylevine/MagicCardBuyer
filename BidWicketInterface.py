# -*- coding: utf-8 -*-

import Cookie
import re
import socket
import string
import sys
import urllib2
import urllib
from httplib import HTTPConnection

class BidWicketInterface:
  def __init__(self):
    self.cachedSetPages = {}
    self.itemIds = {}
    self.storeNames = set()
    self.loggedIn = False
    # Count how many purchases made on a single connection.
    self.itemsBought = 0
    
    self.username = "YOUR BIDWICKET USERNAME GOES HERE"
    self.password = "YOUR BIDWICKET PASSWORD GOES HERE"
    
    self.verbose = False

  def write(self, message):
    if self.verbose:
      sys.stderr.write(message)
    
  def login(self):
    self.initConnection()

    self.request("POST", "/TUser?MC=TULN", {"USC_LOGIN_USER_NAME" : self.username,
                                           "USC_LOGIN_PASSWORD"  : self.password})
    self.request("POST", "/TUser?MC=TUHP", {"USC_TRANS_LOGIN_STATUS" : "G"})   
    self.request("GET", "/TUser?MC=CUHP")
    
    self.loggedIn = True
  
  # Load a page, with a timeout, retrying on failures.
  def readUrl(self, url):
    timeoutInSecs = 5
    maxRetries = 5
    for retryCount in xrange(1, maxRetries):
      try:
        return urllib2.urlopen(url, timeout=timeoutInSecs).read()
      except (urllib2.URLError, socket.timeout) as e:
        self.write("Failed to load URL '" + url + "' on attempt " + str(retryCount) + ": " + str(e) + "\n")
        # Try again.
    raise IOError("Couldn't load '" + url + "' after " + str(maxRetries) + " attempts!")
    
  
  def buyItem(self, itemId):
    # Refresh the connection every so often to minimize connection errors.
    if self.itemsBought >= 50:
      self.conn.close()
      self.login()
      self.itemsBought = 0
    self.request("GET", "/TUser?MC=CUVC&Add=" + itemId)
    self.itemsBought = self.itemsBought + 1
  
  def initConnection(self):
    self.conn = HTTPConnection("bidwicket.com", 80, timeout=20)
    self.cookie = Cookie.SimpleCookie()
  
  def request(self, method, url, params={}):
    body = ""
    headers = {}
    
    if method in ['POST', 'PUT', 'DELETE']:
      if params:
        body = urllib.urlencode(params, True)
      headers["Content-type"] = "application/x-www-form-urlencoded"
      headers["Accept"] = "text/plain"
    
    if self.cookie:
      headers['Cookie'] = self.cookie.output(header='').strip()
    
    self.conn.request(method, url, body, headers)
    
    response = self.conn.getresponse()
    responseText = response.read()
    
    cookieStr = response.getheader("Set-Cookie", None)
    if cookieStr:
      self.cookie.load(cookieStr)
    
    return responseText
    
  # Some card names are not the same as their canonical versions.
  def bidWicketName(self, cardName):
    bidWicketCardNames = { "Brush with Death" : "Brush With Death",
                           "Tracker's Instincts" : "Trackers Instincts",
			   "Kin-Tree Invocation" : "Kin-tree Invocation",
			   "Icy Blast" : "Icy blast",
			   "Zurgo Helmsmasher" : "Zurgo, Helmsmasher"}
    if cardName in bidWicketCardNames:
      cardName = bidWicketCardNames[cardName]
    
    return cardName
  
  # Find the prices for a card.
  def findPrices(self, cardName, setName=None):
    cardName = self.bidWicketName(cardName)
  
    if setName == None:
      # If no set is provided, search for the card's name, then find all the
      # sets that it belongs to and return all those prices.
      setNames = self.findSets(cardName)
      
      output = []
      
      for setName in setNames:
        output.extend(self.findPrices(cardName, setName))
        
      return output
    else:
      # Some set names are not the same as their canonical versions.
      bidWicketSetNames = { "Future Sight" : "Futuresight",
                            "Ravnica: City of Guilds" : "Ravnica",
			    "From the Vault: Dragons" : "From the Vault Dragons"}
      if setName in bidWicketSetNames:
        setName = bidWicketSetNames[setName]

      # Lookup the page for the set, taking it from our local cache if already
      # retrieved.
      if setName in self.cachedSetPages:
        setPage = self.cachedSetPages[setName]
      else:
        urlSetName = setName
        for mark in string.punctuation:
          urlSetName = urlSetName.replace(mark, "_")
        urlSetName = urlSetName.replace(" ", "_")
        
        setPageUrl = ("http://bidwicket.com/Category/Collectible_Card_Games/Magic_the_Gathering/Singles/" +
                      urlSetName +
                      ".html")

        self.write("Loading set page " + setName + "...\n")
               
        setPage = self.readUrl(setPageUrl)
        self.cachedSetPages[setName] = setPage
        
      # Find the URL for the item's page and retrieve it.
      itemUrlRegEx = r"a href=\'(/Item[^']*?)\'>" + cardName
      itemMatch = re.search(itemUrlRegEx, setPage)
      
      if itemMatch == None:
        # Some items use a full HTML escape for special characters.
	escapedCardName = cardName.replace("'", "&rsquo;")
	escapedCardName = escapedCardName.replace("Æ", "&AElig;")
	itemUrlRegEx = r"a href=\'(/Item[^']*?)\'>" + escapedCardName
	itemMatch = re.search(itemUrlRegEx, setPage)
      
      if itemMatch == None:
        raise Exception("Can't find " + cardName + " in " + setName + " with pattern " + itemUrlRegEx)
      
      itemUrl = "http://bidwicket.com" + itemMatch.group(1)
        
      self.write("Loading item page for " + cardName + " from set " + setName + 
                 "...\n")
                 
      itemPage = self.readUrl(itemUrl)
      
      # Find the table of prices for this item.    
      tableStart = "<TABLE class=tutlist>"
      tableEnd = "</TABLE>"
      
      tableStartIndex = itemPage.find(tableStart)
      tableStopIndex = itemPage.find(tableEnd, tableStartIndex)

      # "Similar Items For Sale" are usually displayed after the table for this item.
      # Don't try to scrape through that table.
      similarItemsLabel = "Similar Items For Sale"
      similarItemsIndex = itemPage.find(similarItemsLabel)
      if similarItemsIndex > -1 and similarItemsIndex < tableStartIndex:
	self.write("Only found 'similar items' for " + cardName + " & set " + setName + "; skipping\n")
	return []
      
      tableContents = itemPage[tableStartIndex + len(tableStart) : 
                               tableStopIndex]
                               
      # Iterate through each table row and extract the vendor name, price,
      # and unique item ID.
      rowStart = "<TR"
      rowEnd = "</TR>"
      
      # The first row is the header.
      rowStartIndex = tableContents.find(rowStart)
      rowStopIndex = tableContents.find(rowEnd, rowStartIndex)
      headerRow = tableContents[rowStartIndex : rowStopIndex]
      
      
      
      # Advance to the first data row.
      rowStartIndex = tableContents.find(rowStart, rowStartIndex + 1)
      
      output = []
      
      while rowStartIndex > 0:
        rowStopIndex = tableContents.find(rowEnd, rowStartIndex)
        rowContents = tableContents[rowStartIndex : rowStopIndex]
        
        self.rowContents = rowContents
                        
        # The vendor name is the first match.
        vendorRegex = "a class=vendorname[^>]*>([^<]*)</a>"
	vendorMatch = re.search(vendorRegex, rowContents)
	# This can happen when this card is out of stock.
	if vendorMatch == None:
	  rowStartIndex = tableContents.find(rowStart, rowStartIndex + 1)
	  continue
	
        vendorName = vendorMatch.group(1)
        
        priceRegex = "ItemPrice>([^<]*)<"
        priceMatch = re.search(priceRegex, rowContents)
        if priceMatch == None:
          rowStartIndex = tableContents.find(rowStart, rowStartIndex + 1)
          continue

        price = float(re.search(priceRegex, rowContents).group(1))
        
        itemIdRegex = r"/TUser\?MC=CUVC&Add=([^']*)'"
        itemId = re.search(itemIdRegex, rowContents).group(1)
        
        # The quantity is in the 5th "TD"; the description in the 4th.
        quantityRegex = "<TD[^>]*?>([^<]*?)(?=<)"
	
        tds = re.findall(quantityRegex, rowContents)
        
        description = tds[3].strip()
        quantity = int(tds[4].strip().replace(",", ""))
	
        # Some vendors cap the number of items you can buy from them.
        cappedVendors = {"Power 9 Games" : 1}
        
        if vendorName in cappedVendors:
          quantity = min(cappedVendors[vendorName], quantity)
          
        # Don't buy cards that aren't mint or near mint. This also eliminates 
        # foils & foreign language.       
        if (description == "Mint" or description == "Near Mint"):
          self.itemIds[(cardName, vendorName, setName)] = itemId
          self.storeNames.add(vendorName)
          output.append((vendorName, setName, quantity, price))
        
        rowStartIndex = tableContents.find(rowStart, rowStartIndex + 1)
      
    return output
      
  # Find all the sets a provided card name belongs to.
  # Assumes the name is already in its Bidwicket form.
  def findSets(self, cardName):
    # Search for the card's name.
    searchUrl = "http://bidwicket.com/TUser?MC=CUSE&T=" + urllib.quote(cardName)
    searchPage = self.readUrl(searchUrl)    
    
    # Find the contents of the table of hit results.
    tableStart = "<TABLE class=tutlist>"
    tableEnd = "</TABLE>"
    
    tableStartIndex = searchPage.find(tableStart)
    tableStopIndex = searchPage.find(tableEnd, tableStartIndex)
    
    tableContents = searchPage[tableStartIndex + len(tableStart) : 
                               tableStopIndex]
    
    # Find the text of each link in the table.
    linkRegex = "<a href[^>]*?>([^<]*?)(?=<)"
    linkTexts = re.findall(linkRegex, tableContents)
    
    output = []
    
    for linkText in linkTexts:
      splitLinkText = linkText.split(" - ")
      if len(splitLinkText) == 3:
        cardGame, setName, itemName = linkText.split(" - ")
	
	# Bidwicket idiosyncracies.
	setName = setName.replace("Ravinca", "Ravnica")
	setName = setName.replace("Heros vs Monstors", "Heroes vs Monsters")
	setName = setName.replace("Dragons of Takir", "Dragons of Tarkir")
	
	# The item name might have its rarity in parentheses.
	parenthesisRegex = "(.*)\(.*"
	parenthesisMatch = re.match(parenthesisRegex, itemName)
	if (parenthesisMatch != None):
	  itemName = parenthesisMatch.group(1)
	  
        if cardGame.strip() == "Magic the Gathering" and itemName.strip() == cardName.strip():
          output.append(setName)
    
    return output
    
  # The card name is not in Bid wicket form.
  def buyCard(self, cardName, storeName, setName, quantity):
    cardName = self.bidWicketName(cardName)
    itemId = self.itemIds[(cardName, storeName, setName)]
    
    if (not self.loggedIn):
      self.login()
    
    for i in range(quantity):
      try:
        self.buyItem(itemId)
      except:
        # Retry the purchase.
        self.conn.close()
        self.login()
        self.buyItem(itemId)

  
if __name__ == "__main__":
  interface = BidWicketInterface()
  interface.findPrices("Horned Turtle", "Tempest")
  interface.buyCard("Horned Turtle", "Magus of Magic", "Tempest", 3)