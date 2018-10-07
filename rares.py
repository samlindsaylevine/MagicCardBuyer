#! /usr/bin/env python
import re
import sys
import urllib2
import urllib
import json

if (len(sys.argv) < 2):
  print "Please enter a set name."
  raise SystemExit

setName = sys.argv[1]

countString = ""

rarities = ["rare", "mythic"]

if (len(sys.argv) > 2):
    rarities = sys.argv[2].split(",")

if (len(sys.argv) >=4):
  countString = sys.argv[3] + " "   
    
# Look up the set code of the provided set name from 
# https://api.scryfall.com/sets
setsUrl = "https://api.scryfall.com/sets"
setsResult = urllib2.urlopen(setsUrl).read()
sets = json.loads(setsResult)
codes = [set['code'] for set in sets['data'] if (set['name'] == setName)]

if (len(codes) != 1):
  print "Expected to find one set code for set " + setName + " but found " + len(codes)
  raise SystemExit

rareParameter = "(" + " or ".join(["r:" + rarity for rarity in rarities]) + ")"
searchString = "set:" + codes[0] + " " + rareParameter

searchUrl = "https://api.scryfall.com/cards/search?" + urllib.urlencode([('q', searchString)])

# Not handling pagination right now, this will misbehave if returning >175 cards.

cards = json.loads(urllib2.urlopen(searchUrl).read())
cardNames = [card['name'] for card in cards['data']]

for cardName in cardNames:
  print countString + cardName
    