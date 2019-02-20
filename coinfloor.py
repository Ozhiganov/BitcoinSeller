#------------------------------------------------------
# Wrapper for the coinfloor API
#------------------------------------------------------

import requests
import getpass
import json

import pprint
pp = pprint.PrettyPrinter(indent=4).pprint

user_id = "<USER_ID>"
api_key = "<API_KEY>"

pw = getpass.getpass(prompt="Coinfloor password: ")
id_and_key = user_id + "/" + api_key


def test():
    #------------------------------------------------------
    # Test coinfloor api online
    #------------------------------------------------------

    pip = balance_in_pennies()

    print("Coinfloor balance: " + p2str(pip))


def pounds2p(pounds):
    return int(round(float(pounds)*100.0, 2))


def p2str(integer):
    #------------------------------------------------------
    # Create money string
    #------------------------------------------------------
    s = str(integer)
    while len(s) < 3:
        s = "0" + s
    return "£ {0}.{1}".format(s[:-2], s[-2:])


def get_CF(suffix, params={}):
    #------------------------------------------------------
    # General API GET call with endpoint passed in
    #------------------------------------------------------

    r = requests.get("https://webapi.coinfloor.co.uk:8090/bist/" + suffix, params=params, auth=(id_and_key, pw))

    if r.status_code != 200:
        print("Coinfloor api call failed: " + suffix)
        print("Error code: " + str(r.status_code))
        print(str(r.__dict__))
        raise Exception

    return json.loads(r.text)


def post_CF(suffix, data={}):
    #------------------------------------------------------
    # General API POST call with endpoint passed in
    #------------------------------------------------------

    url = "https://webapi.coinfloor.co.uk:8090/bist/"

    r = requests.post(url + suffix, data=data, auth=(id_and_key, pw))

    if r.status_code != 200:
        print("Coinfloor api call failed: " + suffix)
        print("Error code: " + str(r.status_code))
        raise Exception

    return json.loads(r.text)


def balance_in_pennies():
    #------------------------------------------------------
    # Get account balance
    #------------------------------------------------------

    d = get_CF("XBT/GBP/balance/")

    return pounds2p(d["gbp_available"])


def getMarketEstimateInPennies(btc):
    #------------------------------------------------------
    # Get estimate of price if bought now
    #------------------------------------------------------

    p = {"quantity": str(btc)}
    d = post_CF("XBT/GBP/estimate_buy_market/", p)

    assert float(d["quantity"]) == btc

    return pounds2p(d["total"])


def buyBitcoin(btc):

    p = {"quantity": str(btc)}

    d = post_CF("XBT/GBP/buy_market/", p)

    if "remaining" not in d or float(d["remaining"]) != 0.0:
        print("buyBitcoin error")
        print(str(d))
        raise Exception

    return d


def getLast():
    #------------------------------------------------------
    # Get latest price
    #------------------------------------------------------
    d = get_CF("XBT/GBP/ticker/")
    return pounds2p(d["last"])


def getPriceOfPrevious(bitcoin):
    #------------------------------------------------------
    # One trade can be split into many smaller trades,
    # go through old trades and find the price of the
    # previous trade made by adding up previous trades
    # until value is hit.
    #------------------------------------------------------
    p = {"limit": 20, "sort": "desc"}
    d = get_CF("XBT/GBP/user_transactions/", params=p)

    trades = []
    btcSoFar = 0.0000
    pSoFar = 0

    #------------------------------------------------------
    # Go through past trades until bitcoin amount reached
    #------------------------------------------------------
    for trade_dict in d:
        if (trade_dict["type"] == 2) and (float(trade_dict["xbt"]) > 0.0):

            trade = {"price": -1 * pounds2p(trade_dict["gbp"]),
                     "btc": round(float(trade_dict["xbt"]), 4),
                     "fee": pounds2p(trade_dict["fee"]) }

            btcSoFar = round(btcSoFar + trade["btc"], 4)
            pSoFar += trade["price"] + trade["fee"]

            trades.append(trade)

            if btcSoFar >= round(bitcoin, 4):
                break

    if btcSoFar > round(bitcoin, 4):
        print("ERROR: Past price adding not correct")
    elif btcSoFar < round(bitcoin, 4):
        print("ERROR: Not enough bitcoin in past transactions")


    return {"price": pSoFar, "btc": btcSoFar, "trades": trades}

test()