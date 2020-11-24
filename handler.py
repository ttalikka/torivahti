# Basic imports
import json
import os
import sys
import stringlibrary

here = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(here, "./vendored"))

# Vendored imports
import requests
from bs4 import BeautifulSoup

# Base variables
TOKEN = os.environ["TELEGRAM_TOKEN"]
BASE_URL = "https://api.telegram.org/bot{}".format(TOKEN)


# Event handler
def hello(event, context):
    try:
        data = json.loads(event["body"])
        message = str(data["message"]["text"])
        if message.startswith(stringlibrary.SEARCH_CMD):
            search(data)

    except Exception as e:
        print(e)

    return {"statusCode": 200}


# Basic search, ingests event body objects
def search(data):
    chat_id = data["message"]["chat"]["id"]
    try:
        # Split the received message into search terms
        params = data["message"]["text"].split(" ")
        if len(params) == 1:
            # Raise a general search error if no search terms are included
            raise (IndexError)
        # Build a URL-friendly search query
        searchQuery = "+".join(params[1:])
        # Run the search, soupify it
        r = requests.get("https://www.tori.fi/koko_suomi?q={}".format(searchQuery))
        soup = BeautifulSoup(r.text, "html.parser")
        # Items found in the search are in the list_mode_thumb -div
        itemlist = soup.find("div", class_="list_mode_thumb").find_all(
            "a", "item_row_flex"
        )
        # Just respond with a link to the latest posting
        response = str(itemlist[0]["href"])
        sendMessage({"text": response.encode("utf8"), "chat_id": chat_id})
    except IndexError as e:
        # Generic search error
        response = stringlibrary.ILLEGAL_SEARCH
        sendMessage({"text": response.encode("utf8"), "chat_id": chat_id})


# Handles bot message sending, must include text and chat_id JSON entries
def sendMessage(data):
    url = BASE_URL + "/sendMessage"
    requests.post(url, data)
