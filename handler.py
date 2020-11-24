import json
import os
import sys
import stringlibrary

here = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(here, "./vendored"))

import requests
from bs4 import BeautifulSoup

TOKEN = os.environ["TELEGRAM_TOKEN"]
BASE_URL = "https://api.telegram.org/bot{}".format(TOKEN)


def hello(event, context):
    try:
        data = json.loads(event["body"])
        message = str(data["message"]["text"])
        if message.startswith(stringlibrary.SEARCH_CMD):
            search(data)

    except Exception as e:
        print(e)

    return {"statusCode": 200}


def search(data):
    chat_id = data["message"]["chat"]["id"]
    try:
        params = data["message"]["text"].split(" ")
        if len(params) == 1:
            raise (IndexError)
        searchQuery = "+".join(params[1:])
        r = requests.get("https://www.tori.fi/koko_suomi?q={}".format(searchQuery))
        soup = BeautifulSoup(r.text, "html.parser")
        itemlist = soup.find("div", class_="list_mode_thumb").find_all(
            "a", "item_row_flex"
        )
        response = str(itemlist[0]["href"])
        sendMessage({"text": response.encode("utf8"), "chat_id": chat_id})
    except IndexError as e:
        response = stringlibrary.ILLEGAL_SEARCH
        sendMessage({"text": response.encode("utf8"), "chat_id": chat_id})


def sendMessage(data):
    url = BASE_URL + "/sendMessage"
    requests.post(url, data)
