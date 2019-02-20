# BitcoinSeller

**THIS CODE IS PUBLIC TO DEMONSTRATE MY METHOD OF AUTOMATING THE PROCESS. IT IS IN NO STATE TO BE RUN BY ANYONE WHO DIDN'T WRITE IT THEMSELVES AND KNOWS EXACTLY WHAT IT DOES. THIS IS NOT FOR PUBLIC USE. DO NOT USE IT.**

This program automates every part of selling Bitcoin to users on localbitcoins.com and buying it back at a cheaper price on the coinfloor.com bitcoin exchange.  Including verifying payment and changing the price to undercut other users advertisements.

# Coinfloor

Coinfloor is an online GBP/Bitcoin exchange with an API.

# LocalBitcoins

LocalBitcoins is an online person to person bitcoin selling/buying website where users can post advertisements offering to sell bitcoins for a certain amount. And where other users can accept these advertisements and trade with the users.


# The program

This program automates the process of featuring an advert on lbc (LocalBitcoins), and then buying back any bitcoins sold again on cf (CoinFloor). Localbitcoins is the far easier platform to buy bitcoins on for those who aren't able to sign up to an exchange and therefore prices are generally higher.

It roughly works as follows

1. Get all open trades on lbc
2. Get all bank transactions from monzo
3. Check for new trades and send opening message with instructions
4. Check bank transactions for payments with references to individual trades on lbc.
5. If a payment matches a lbc trade, confirm the trade on lbc and send thank you message
6. Buy back the amount of bitcoin sold on localbitcoins immediatley on cf (price is constantly checked to ensure a profit can be made and advert priced accordingly)
7. Check other adverts on lbc, change price of our advert to undercut them by 0.1% if needed.
