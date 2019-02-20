import LBC, coinfloor, monzo

from time import gmtime, strftime
import sched, time
import json


s = sched.scheduler(time.time, time.sleep)

wait = 8

#------------------------------------------------------
# IDs of the Adverts to be running on
#------------------------------------------------------
automated_trade_id = 999999
verify_trade_id = 999999
ads_to_run = [automated_trade_id, verify_trade_id]

#------------------------------------------------------
# Max and mins for the volume of btc to sell per trade
#------------------------------------------------------
change_price = True
price_targets = {automated_trade_id: [20, 99],
                 verify_trade_id: [1000, 2000]}

#------------------------------------------------------
# Max and mins of the price margins (%) to sell for
#------------------------------------------------------
lowest_marg = 2.5
highest_marg = 5.5


json_file = "trades_started.json"
message_folder = "messages"


def p2string(p):
    return p2str(p)

def p2str(integer, symbol=True):
    s = str(round(float(integer) / 100.0, 2))
    if symbol:
        s = "£ " + s

    return s


def getEndMessage():
    #------------------------------------------------------
    # Get the end message from file to send when the 
    # trade has finished
    #------------------------------------------------------
    with open(message_folder + "/end_message.txt", 'r') as content_file:
        end_message = content_file.read()
    return end_message

def getStartMessage():
    #------------------------------------------------------
    # Get the start message from file to send when the
    # trade has just started for trades that dont need
    # verification
    #------------------------------------------------------
    with open(message_folder + "/start_message.txt", 'r') as content_file:
        start_message = content_file.read()
    return start_message

def getVerifiedStartMessage():
    #------------------------------------------------------
    # Get the start message from file to send when the
    # trade has just started for trades that need human
    # verification
    #------------------------------------------------------
    with open(message_folder + "/verify_start_message.txt", 'r') as content_file:
        start_message = content_file.read()
    return start_message

def list2file(lis, filename):
    file = open(filename, "w")
    for item in lis:
        file.write(str(item) + "\n")
    file.close()

def file2list(filename):
    lines = [int(line.rstrip('\n')) for line in open(filename)]
    return lines

def dict2file(d, fn):
    json.dump(d, open(fn, "w"))
    

def file2dict(fn):
    return json.load(open(fn))




def changePrice(offer_id):
    #------------------------------------------------------
    # Change price of advert on display
    #------------------------------------------------------

    #------------------------------------------------------
    # Get multiples from the % min maxes
    #------------------------------------------------------
    low_mult = (lowest_marg / 100.0) + 1.0
    high_mult = (highest_marg / 100.0) + 1.0


    #------------------------------------------------------
    # Price target to aim for
    #------------------------------------------------------
    price_target = price_targets[offer_id] 

    #------------------------------------------------------
    # Find the price of the lowest advert on display
    # in the target volume margains.
    #------------------------------------------------------
    lowest_ad =  LBC.lowest_price_for(price_target[0], price_target[1])
    if lowest_ad == None:
        lowest_price_in_pennies = 9999999999
    else:
        lowest_price_in_pennies = lowest_ad.price_in_pennies

    #------------------------------------------------------
    # Generate new price 99.9% price of lowest
    # advert currently available.
    #------------------------------------------------------
    new_price_in_pennies = float(lowest_price_in_pennies) * 0.999


    #------------------------------------------------------
    # Check there's enough money in coinfloor account
    # for price given
    #------------------------------------------------------
    cf_price_in_pennies = coinfloor.getLast()
    lowlimit_pennies = float(cf_price_in_pennies) * low_mult
    hilimit_pennies = float(cf_price_in_pennies) * high_mult

    msg = str(offer_id) + ": "
    if new_price_in_pennies < lowlimit_pennies:
        msg += "Lower limit {0}% hit".format(str(lowest_marg))
        new_price_in_pennies = lowlimit_pennies
    elif new_price_in_pennies > hilimit_pennies:
        msg += "Upper limit {0}% hit".format(str(highest_marg))
        new_price_in_pennies = hilimit_pennies


    #------------------------------------------------------
    # Change our advert to the new price generated above
    #------------------------------------------------------
    new_price_in_pounds = round(new_price_in_pennies / 100.0, 4)
    LBC.change_ad_equation(offer_id, str(new_price_in_pounds))
    print(msg + "CF Price: {0} | New offer: {1}".format(p2str(cf_price_in_pennies), p2str(new_price_in_pennies)))





def check():
    #------------------------------------------------------
    # Main loop which checks all current trades and
    # adverts,
    #------------------------------------------------------

    #------------------------------------------------------
    # Get the current trades in progress from file.
    # This is in case perogram needs to be restarted 
    # during trades in progress.
    #------------------------------------------------------
    trades_started = file2dict(json_file)
    print(trades_started)
    



    while True:

        #------------------------------------------------------
        # Get all our active trades in localbitcoins account
        #------------------------------------------------------
        trades = LBC.get_trade_list(ads_to_run)

        #------------------------------------------------------
        # Get all bank transactions with references and amounts
        #------------------------------------------------------
        transactions_dict = {}
        for transaction in monzo.getMonzoTransactions():

            if type(transaction.ref) is str:
                transaction.ref = transaction.ref.upper()

            transactions_dict[transaction.ref] = transaction


        for LBC_trade in trades:

            #------------------------------------------------------
            # If the trade is new, send 'starting' message and 
            # add ID to list of open trades
            #------------------------------------------------------
            if LBC_trade.id not in trades_started:

                    print("New trade: {0} escrow of {1} for {2}"
                          .format(LBC_trade.buyer, str(LBC_trade.escrow_BTC), LBC_trade.price_string()))

                    #------------------------------------------------------
                    # Send start message depending on trade type
                    #------------------------------------------------------
                    if LBC_trade.ad_id == automated_trade_id:
                        LBC_trade.send_message(getStartMessage())
                    elif LBC_trade.ad_id == verify_trade_id:
                        LBC_trade.send_message(getVerifiedStartMessage())

                    #------------------------------------------------------
                    # Add logs to files
                    #------------------------------------------------------
                    trades_started[LBC_trade.id] = {"start_est": coinfloor.getMarketEstimateInPennies(round(LBC_trade.escrow_BTC + 0.00005, 4)),
                                                    "start_ppb": coinfloor.getLast()}
                    dict2file(trades_started, json_file)


            #------------------------------------------------------
            # If a trade reference matches transaction in bank
            # account.
            #------------------------------------------------------
            if LBC_trade.ref in transactions_dict:

                bank_trans = transactions_dict[LBC_trade.ref]

                timestr = strftime("%H:%M:%S", gmtime())
                datestr = strftime("%Y-%m-%d", gmtime())
                datetimestr = datestr + " " + timestr

                print("-"*60)
                print(datetimestr)



                #------------------------------------------------------
                # Check payment amount is correct
                #------------------------------------------------------
                if bank_trans.amount_in_pennies == LBC_trade.amount_in_pennies:

                    #------------------------------------------------------
                    # Release bitcoins in trade and send ending message
                    #------------------------------------------------------
                    LBC_trade.release_btc()
                    LBC_trade.send_message(getEndMessage())

                    print("SUCCESS! | ID: {0} | ref: {1} | btc: {2} | pay: {3} | buyer: {4}"
                        .format(LBC_trade.id, 
                            LBC_trade.ref, 
                            LBC_trade.escrow_BTC, 
                            LBC_trade.price_string(), 
                            LBC_trade.buyer))

                    #------------------------------------------------------
                    # Buy back amount of bitcoin just sold, on coinfloor
                    # (for less than just sold for)
                    #------------------------------------------------------
                    buy_back = round(LBC_trade.escrow_BTC + 0.00005, 4)
                    coinfloor.buyBitcoin(buy_back)

                    #------------------------------------------------------
                    # Calculate how much it cost to buy bitcoin back on
                    # coinfloor
                    #------------------------------------------------------
                    bought_back = coinfloor.getPriceOfPrevious(buy_back)
                    spent = bought_back["price"]
                    actually_bought = bought_back["btc"]

                    print("{0} BTC buy back done. {1} for {2}".format(str(buy_back), str(actually_bought), p2str(spent)))


                    #------------------------------------------------------
                    # Meta data to put into csv file for analysing
                    #------------------------------------------------------
                    start_est = trades_started[LBC_trade.id]["start_est"]
                    start_ppb = trades_started[LBC_trade.id]["start_ppb"]

                    profit_start = LBC_trade.amount_in_pennies - start_est
                    profit = LBC_trade.amount_in_pennies - spent
                    btc_gain = round(actually_bought - LBC_trade.escrow_BTC, 8)

                    csvline = [LBC_trade.created,
                        LBC_trade.id,
                        LBC_trade.ref,
                        LBC_trade.amount_BTC,
                        LBC_trade.fee_BTC,
                        LBC_trade.escrow_BTC,
                        LBC_trade.price_string(symbol=False),
                        p2str(start_est, symbol=False),
                        p2str(start_ppb, symbol=False),
                        p2str(profit_start, symbol=False),
                        datetimestr,
                        p2str(spent, symbol=False),
                        p2str(profit, symbol=False),
                        btc_gain
                        ]

                    print(str(csvline))



                #------------------------------------------------------
                # If payment made wasn't enough
                #------------------------------------------------------
                elif bank_trans.amount_in_pennies < LBC_trade.amount_in_pennies:
                    print("Trade {0} to {1} for {2} FAILED: NOT ENOUGH SENT".format(LBC_trade.id, LBC_trade.buyer, LBC_trade.price_string()))
                    print("Payment ref: " + LBC_trade.ref)
                    print("Transaction of {0} sent.".format(bank_trans.price_string()))


                #------------------------------------------------------
                # If payment made was too much
                #------------------------------------------------------
                elif bank_trans.amount_in_pennies > LBC_trade.amount_in_pennies:
    
                    print("Trade {0} to {1} for {2} FAIED: TOO MUCH SENT".format(LBC_trade.id, LBC_trade.buyer, LBC_trade.price_string()))
                    print("Payment ref: " + LBC_trade.ref)
                    print("Transaction of {0} sent.".format(bank_trans.price_string()))


                #------------------------------------------------------
                # Shouldn't happen
                #------------------------------------------------------
                else:
                    print("Trade {0} to {1} for {2} THIS SHOULDNT BE HERE".format(LBC_trade.id, LBC_trade.buyer, LBC_trade.price_string()))
                    print("Payment ref: " + LBC_trade.ref)
                    print("Transaction of {0} sent.".format(bank_trans.price_string()))


                print("-"*60)



        #------------------------------------------------------
        # Change the price of the ad depending on the current
        # state of other ads on localbitcoins
        # Undercutting them if price good enough.
        #------------------------------------------------------
        if change_price:
            for ID in ads_to_run:
                changePrice(ID)


        print("...")
        time.sleep(wait)



check()



