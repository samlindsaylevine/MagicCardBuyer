#! /usr/bin/env python
import re
import sys
import urllib2
import urllib

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
    
# Look up the edition_id of the provided set in 
# http://magiccards.info/search.html.
searchUrl = "http://magiccards.info/search.html"
searchPage = urllib2.urlopen(searchUrl).read()

regExPattern = ( '<option value="([^"]+)">'  +
                 setName + '</option' )

regEx = re.compile(regExPattern)
idResult = regEx.search(searchPage)

if idResult == None:
  print "Unrecognized set name: " + setName
  raise SystemExit

setId = idResult.group(1)

rareParameter = "(" + " or ".join(map(lambda(str) : "r:" + str, rarities)) + ")"

rareUrl = ('http://www.magiccards.info/query?' + 
	       urllib.urlencode( [ ('q', rareParameter + ' e:' + setId),
                               ('v', 'list') ]))

raresPage = urllib2.urlopen(rareUrl).read()

tableStart = raresPage.find('table cellpadding="3"')
tableStop = raresPage.find("</table>", tableStart)
tableString = raresPage[tableStart:tableStop]

rows = tableString.split("</tr>")

for row in rows:
  aHrefLocation = row.find("<a href")
  if (aHrefLocation != -1):
    closeTagLocation = row.find(">", aHrefLocation)
    slashALocation = row.find("</a>", closeTagLocation)
    cardName = row[closeTagLocation + 1:slashALocation]
    print countString + cardName
    