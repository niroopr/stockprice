#!/usr/bin/env python

from __future__ import print_function
from future.standard_library import install_aliases
install_aliases()

from urllib.parse import urlparse, urlencode
from urllib.request import urlopen, Request
from urllib.error import HTTPError

import json
import os

from flask import Flask
from flask import request
from flask import make_response

# Flask app should start in global layout
app = Flask(__name__)


@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)

    print("Request:")
    print(json.dumps(req, indent=4))

    res = processRequest(req)

    res = json.dumps(res, indent=4)
    # print(res)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r
    
def processRequest(req):
    if req.get("result").get("action") != "finance.stocks":
        return {}
    baseurl = "https://query.yahooapis.com/v1/public/yql?"
    yql_query = makeYqlQuery(req)
    if yql_query is None:
        return {}
    yql_url = baseurl + urlencode({'q': yql_query}) + "&format=json&env=store%3A%2F%2Fdatatables.org%2Falltableswithkeys&callback="
    result = urlopen(yql_url).read()
    data = json.loads(result)
    res = makeWebhookResult(data)
    return res

def makeYqlQuery(req):
    result = req.get("result")
    parameters = result.get("parameters")
    ticker = parameters.get("company_ticker")
    if ticker is None:
        return None

    return "select * from yahoo.finance.quotes where symbol in ('" + ticker + "')"

def makeWebhookResult(data):
    query = data.get('query')
    if query is None:
        return {}

    result = query.get('results')
    if result is None:
        return {}

    quote = result.get('quote')
    if quote is None:
        return {}

    #speech = "Today in " + location.get('city') + ": " + condition.get('text') + \
            # ", the temperature is " + condition.get('temp') + " " + units.get('temperature')
    speech = "Last Trade Price of " + quote.get('symbol') + " is: $" + quote.get('LastTradePriceOnly') + \
             ", Open price is $" + quote.get('Open') + ", change is $" + quote.get('Change') + \
             ", change % is " + quote.get('ChangeinPercent')
    
    print("Response:")
    print(speech)

    return {
        "speech": speech,
        "displayText": speech,
        # "data": data,
        # "contextOut": [],
        "source": "niroop's webhook"
    }

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))

    print("Starting app on port %d" % port)

    app.run(debug=False, port=port, host='0.0.0.0')