#------------------------------------------------------
# Monzo is a Bank
# This is a wrapper for the API to check incoming 
# transactions
#------------------------------------------------------

import requests
import json
import pprint

pp = pprint.PrettyPrinter(indent=4).pprint


url = "https://api.monzo.com"
lbc_url = "https://localbitcoins.com/api"

accountID = "<account_id>"

user = "<user>"
token = "<token>"



class Transaction:

    def __init__(self, d):

        self.ref = d["notes"]
        if self.ref == "":
            self.ref = None
        self.amount_in_pennies = d["amount"]

    def getData(self):
        return {"ref": self.ref, "amount": self.amount}

    def __repr__(self):
        return str(self.getData())

    def price_string(self):
        s = str(self.amount_in_pennies)
        return s[0:-2] + "." + s[-2:] + " GBP"


def getMonzoTransactions():
    #------------------------------------------------------
    # Return all transactions from monzo account
    #------------------------------------------------------

    header = {"Authorization":"Bearer " + token}
    call = "/transactions?expand[]=merchant&account_id=" + accountID
    r = requests.get(url + call, headers=header)

    if r.status_code != 200:
        print("Error code: " + str(r.status_code))
        print(str(r.__dict__))
        raise Exception

    d = json.loads(r.text)

    full_trans = d["transactions"]

    transactions = []

    for tran in full_trans:

        t = Transaction(tran)
        transactions.append(t)


    return transactions


