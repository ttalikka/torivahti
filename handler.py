# Basic imports
import json
import os
import sys
import stringlibrary
import uuid

here = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(here, "./vendored"))

# Vendored imports
import requests
from bs4 import BeautifulSoup
import boto3

# Base variables
TOKEN = os.environ["TELEGRAM_TOKEN"]
BASE_URL = "https://api.telegram.org/bot{}".format(TOKEN)
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(stringlibrary.DYNAMODB_TABLE)

# Event handler
def hello(event, context):
    try:
        data = json.loads(event["body"])
        message = str(data["message"]["text"])
        if message.startswith(stringlibrary.START_CMD):
            response = "{}{}!".format(
                stringlibrary.HELLO_MSG, data["message"]["from"]["first_name"]
            )
            sendMessage(
                {
                    "text": response.encode("utf8"),
                    "chat_id": data["message"]["chat"]["id"],
                }
            )
        elif message.startswith(stringlibrary.SEARCH_CMD):
            search(data)
        elif message.startswith(stringlibrary.WATCH_CMD):
            watch(data)
        else:
            sendMessage(
                {
                    "text": stringlibrary.ILLEGAL_CMD.encode("utf8"),
                    "chat_id": data["message"]["chat"]["id"],
                }
            )

    except Exception as e:
        print(e)

    return {"statusCode": 200}


# Basic search, ingests event body objects
def search(data):
    chat_id = data["message"]["chat"]["id"]
    try:
        # Split the received message into search terms
        params = getParameters(data)
        # Build a URL-friendly search query
        searchQuery = "+".join(params[1:])
        # Get a list of items based on the search query
        itemlist = searchSales(searchQuery)
        # Just respond with a link to the latest posting
        response = str(itemlist[0]["href"])
    except IndexError as e:
        # Generic search error
        response = stringlibrary.ILLEGAL_SEARCH
    except AttributeError as e:
        # AttributeError is raised when no results are found
        response = stringlibrary.NO_RESULTS_FOUND

    sendMessage({"text": response.encode("utf8"), "chat_id": chat_id})


# Sets a watcher for a search query
def watch(data):
    try:
        # Split the received message into search terms
        params = getParameters(data)
        print(params)
        # Build a URL-friendly search query
        searchQuery = "+".join(params[1:])
        print(searchQuery)
        itemlist = searchSales(searchQuery)
        # Save the search query into the database
        id = str(uuid.uuid4())
        chat = str(data["message"]["chat"]["id"])
        latest = str(itemlist[0]["id"])
        table.put_item(
            Item={
                "id": id,
                "chat": chat,
                "latest": latest,
                "searchQuery": searchQuery,
            }
        )
        sendMessage(
            {
                "text": stringlibrary.WATCH_SAVED.encode("utf8"),
                "chat_id": data["message"]["chat"]["id"],
            }
        )

    except Exception as e:
        pass


# Parses the message that the bot received into search parameters, handles errors
def getParameters(data):
    try:
        # Split the received message into search terms
        params = data["message"]["text"].split(" ")
        if len(params) == 1:
            # Raise a general search error if no search terms are included
            raise (IndexError)
        return params
    except IndexError as e:
        # Generic search error
        response = stringlibrary.ILLEGAL_SEARCH
        sendMessage(
            {"text": response.encode("utf8"), "chat_id": data["message"]["chat"]["id"]}
        )


def searchSales(searchQuery):
    # Run the search, soupify it
    r = requests.get("{}{}".format(stringlibrary.SEARCH_URL, searchQuery))
    soup = BeautifulSoup(r.text, "html.parser")
    # Items found in the search are in the list_mode_thumb -div
    itemlist = soup.find("div", class_="list_mode_thumb").find_all("a", "item_row_flex")
    return itemlist


# Handles bot message sending, must include text and chat_id JSON entries
def sendMessage(data):
    url = BASE_URL + "/sendMessage"
    requests.post(url, data)
