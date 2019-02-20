#------------------------------------------------------
# This script simply records the price of bitcoin on
# both localbitcoins and coinfloor to track the
# potential margain between the two throughout the day.
# To find when the best time to sell is.
#------------------------------------------------------

import LBC
import requests
import json
import csv
from time import gmtime, strftime
import sched, time


s = sched.scheduler(time.time, time.sleep)
interval = 5*60
global_n = 1


def getNonce():
    global global_n
    global_n += 99999
    return int(time.time()) + global_n

def getLBCprice1():

	#------------------------------------------------------
	# DO NOT USE
	# Scans html of localbitcoins for current price
	#------------------------------------------------------

	r = requests.get("https://localbitcoins.com")
	html = r.text

	#------------------------------------------------------
	# Find selling area of page
	#------------------------------------------------------
	html = html[html.find("purchase-bitcoins-online"):]
	
	#------------------------------------------------------
	# Find price fields
	#------------------------------------------------------
	lookfor = "column-price\">"
	html = html[html.find(lookfor) + len(lookfor):]
	end = html.find("</td>")
	html = html[:end].strip()

	#------------------------------------------------------
	# Remove all but the number from the price string
	#------------------------------------------------------
	for i in [" ", ",", "GBP", "\n"]:
		html = html.replace(i, "")

	return float(html)

def getLBCprice():
	return LBC.avg_LB_price(5)


def getCFprice():
	#------------------------------------------------------
	# Check coinfloor API for the current price of btc
	#------------------------------------------------------
	r = requests.get("https://webapi.coinfloor.co.uk:8090/bist/XBT/GBP/ticker/")

	d = json.loads(r.text)

	return [float(d["last"]), float(d["volume"])]



def writeline(line):
	#------------------------------------------------------
	# Write a line to the csv to store results for 
	# analysing later.
	#------------------------------------------------------
	with open("BTC_Margain.csv", "a", newline="\n", encoding="utf-8") as file:
		wr = csv.writer(file)
		wr.writerow(line)


def record():

	err = False

	try:

		time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
		[CF, volume] = getCFprice()
		LBC = getLBCprice() / 100.0

		
		
		LBCFEE = 0.01*LBC
		CFFEE = 0.003*CF
		
		MARG = LBC - CF - LBCFEE - CFFEE
		
		perc = MARG / LBC
		
		line = [time, LBC, CF, volume, MARG, perc]

		perc_str = str(perc*100.0)[0:5] + "%"

		print("Taking record : " + str(line) + " " + perc_str)

		writeline(line)

	except Exception as e:
		err = True
		print("Error occured " + str(e))


	if err:
		s.enter(5, 1, record, ())
	else:
		s.enter(interval, 1, record, ())

	


s.enter(0, 1, record, ())
s.run()






