#------------------------------------------------------
# Localbitcoins is a website where you can buy and sell
# bitcoin via p2p adverts.
# This is a wrapper for the API it has.
#------------------------------------------------------

import requests
import pprint
import json
import urllib

import hmac
import time
import hashlib

pp = pprint.PrettyPrinter(indent=4).pprint

hmac_key = "<hmac_key>"
hmac_secret = "<hmac_secret>"
global_n = 1


class Ad:
    #------------------------------------------------------
    # Object for an advert on localbitcoins
    #------------------------------------------------------

    def __init__(self, d):

        d = d["data"]

        self.user = d["profile"]["username"]
        self.price_in_pennies = int(d["temp_price"].replace(".", ""))

        self.min = d["min_amount"]
        self.max = d["max_amount_available"]

        if self.min is not None:
            self.min = int(float(self.min))
        if self.max is not None:
            self.max = int(float(self.max))

    def __repr__(self):
        return str(self.__dict__)




def getAd(ad_id):
    d = lbc_get("/api/ad-get/{0}/".format(ad_id))
    return Ad(d["data"]["ad_list"][0])


def getBasePriceInPennies():
    ad = getAd(683385)
    return ad.price_in_pennies / 2.0


def strbtc2int(s):
    return int(float(s) * 100000000)


def int2strbtc(i):
    s = ("0"*99) + str(i)

    s = s[0:-8] + "." + s[-8:]

    while s[0] == "0":
        s = s[1:]

    if s[0] == ".":
        s = "0" + s


def getNonce():
    global global_n
    global_n += 1
    return int(time.time()*10000) + global_n


def p2str(integer, symbol=True):
    s = str(integer)
    while len(s) < 3:
        s = "0" + s

    s = "{0}.{1}".format(s[:-2], s[-2:])

    if symbol:
        s = "£ " + s

    return s



class Trade:
    #------------------------------------------------------
    # Object for an open trade on localbitcoins
    #------------------------------------------------------

    def __init__(self, d):
        
        self.raw = d
        d = d["data"]

        self.id = d["contact_id"]
        self.ad_id = d["advertisement"]["id"]
        self.buyer = d["buyer"]["username"]
        self.amount_in_pennies = int(float(d["amount"]) * 100.0)
        self.amount_BTC = float(d["amount_btc"])
        self.fee_BTC = float(d["fee_btc"])
        self.escrow_BTC = round(self.amount_BTC + self.fee_BTC, 8)
        self.ref = d["reference_code"]
        self.created = d["created_at"]



    def __repr__(self):
        return str(self.__dict__)


    def release_btc(self):
        r = lbc_post("/api/contact_release/" + str(self.id) + "/")

        return r

    def price_string(self, symbol=True):
        return p2str(self.amount_in_pennies, symbol)

    def send_message(self, message):
        send_trade_message(self.id, message)



def send_trade_message(trade_id, message):
        p = {"msg": message}
        r = lbc_post("/api/contact_message_post/{0}/".format(trade_id), params=p)

        return r


def get_trade_list(id_list=None):
    #------------------------------------------------------
    # Get the current open trades the user is involved in
    #------------------------------------------------------
    j = lbc_get("/api/dashboard/")

    trades_json = j["data"]["contact_list"]

    if id_list is None:
        trades = [Trade(trade_json) for trade_json in trades_json]
    else:
        trades = [Trade(trade_json) for trade_json in trades_json if trade_json["data"]["advertisement"]["id"] in id_list]

    return trades




def get_ad_list(n):
    j = lbc_get("/buy-bitcoins-online/GB/united-kingdom/national-bank-transfer/.json")

    ads_json = j["data"]["ad_list"]

    ads = []

    for ad_json in ads_json[0:n]:
        ads.append(Ad(ad_json))

    return ads


def price(n):
    return "£ " + str(n)[:-2] + "." + str(n)[-2:]


def lbc_get(suffix, params={}):
    #------------------------------------------------------
    # Generic localbitcoins API GET call
    #------------------------------------------------------

    nonce = getNonce()
    params_urlencoded = urllib.parse.urlencode(params)
    message = str(nonce) + hmac_key + suffix + params_urlencoded
    message_bytes = message.encode('utf-8')
    signature = hmac.new(hmac_secret.encode('utf-8'), msg=message_bytes, digestmod=hashlib.sha256).hexdigest().upper()


    headers = {}
    headers["Apiauth-Key"] = hmac_key
    headers["Apiauth-Nonce"] = str(nonce)
    headers["Apiauth-Signature"] = signature


    r = requests.get("https://localbitcoins.com" + suffix, headers=headers)

    if r.status_code != 200:
        print("Status code: " + str(r.status_code))
        print(str(r.__dict__))
        raise Exception

    j = json.loads(r.text)

    if "error" in j:
        print(j["error"])
        raise Exception

    return j


def lbc_post(suffix, params={}):
    #------------------------------------------------------
    # Generic localbitcoins API POST call
    #------------------------------------------------------

    nonce = getNonce()
    params_urlencoded = urllib.parse.urlencode(params)
    message = str(nonce) + hmac_key + suffix + params_urlencoded
    message_bytes = message.encode('utf-8')
    signature = hmac.new(hmac_secret.encode('utf-8'), msg=message_bytes, digestmod=hashlib.sha256).hexdigest().upper()


    headers = {}
    headers["Apiauth-Key"] = hmac_key
    headers["Apiauth-Nonce"] = str(nonce)
    headers["Apiauth-Signature"] = signature


    r = requests.post("https://localbitcoins.com" + suffix, headers=headers, data=params)

    if r.status_code != 200:
        print("Status code: " + str(r.status_code))
        print(str(r.__dict__))
        raise Exception

    j = json.loads(r.text)

    if "error" in j:
        print(j["error"])
        raise Exception

    return j


def avg_LB_price(n):
    #------------------------------------------------------
    # Get the average price bitcoin is going for out of
    # the cheapest n adverts
    #------------------------------------------------------

    ads = get_ad_list(n)

    price_sum = 0
    for ad in ads:
        price_sum += ad.price_in_pennies

    return int(price_sum / n)


def overlap(my_min, my_max, ad_min, ad_max):
    #------------------------------------------------------
    # Find if the min/maxs given, overlap
    #------------------------------------------------------

    if ad_min is None:
        ad_min = -9999999999999
    if ad_max is None:
        ad_max = 9999999999999

    if my_max < ad_min or my_min > ad_max:
        return False
    return True


def lowest_price_for(my_min, my_max):
    #------------------------------------------------------
    # Find lowest price for a certain amount of bitcoin
    # for sale on any advert
    #------------------------------------------------------

    ads = get_ad_list(40)

    for ad in ads:
        if overlap(my_min, my_max, ad.min, ad.max):
            if ad.user != "Sammy-Bitcoin":
                return ad

    return None



def get_available_btc():
    #------------------------------------------------------
    # Check wallet for amount of bitcoin left to sell
    #------------------------------------------------------
    d = lbc_get("/api/wallet-balance/")
    return float(d["data"]["total"]["sendable"])


def change_ad_equation(ad_id, equation):
    #------------------------------------------------------
    # Change price of bitcoin on the advert
    #------------------------------------------------------
    params = {"price_equation": str(equation)}
    lbc_post("/api/ad-equation/{0}/".format(ad_id), params)


def change_ad_multiplier(ad_id, multiplier):
    change_ad_equation(ad_id, "btc_in_usd*USD_in_GBP*" + str(multiplier))

