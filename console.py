import httpx
import sys
import json
from datetime import datetime
from rich import print
from rich.table import Table
from rich.console import Console

TOKEN = ""


def load_token():
    global TOKEN
    with open("token.txt", "r") as infile:
        TOKEN = infile.read()
        TOKEN = TOKEN[:-1]


load_token()
headers = {"Authorization": f"Bearer {TOKEN}"}
queries_filename = "queries.json"

################################
# ------------------------------
################################


def add_tweet_to_table(table, tweet):
    tweet_url = f"https://twitter.com/_/status/{tweet[0]}"
    text = tweet[1]
    has_newline = text.find("\n")
    # print("has_newline:", has_newline)
    if has_newline != -1:
        text = text[:has_newline]
    table.add_row(tweet_url, text)
    # table.add_row(tweet_url, tweet[1])


def add_tweets_to_table(table, tweets):
    for tweet in tweets[:3]:
        # for tweet in tweets[:len(tweets)//2]:
        add_tweet_to_table(table, tweet)


def print_tweets(tweets):
    for tweet in tweets:
        print(tweet)


def update_queries(filename, query_str, queries, timestamp, tweets):
    query = {"timestamp": timestamp, "tweets": tweets}
    queries[query_str] = query
    with open(filename, "w") as outfile:
        outfile.write(json.dumps(queries))


def load_queries(filename):
    with open(filename, "r") as infile:
        queries = json.loads(infile.read())
    return queries


def main():
    load_token()
    client = httpx.Client()
    console = Console()
    # number of seconds between actually hitting the API v.s. using our local cache of searches
    threshold = 300
    queries = load_queries("queries.json")
    while True:
        table = Table(title="tweets")
        text_color = "white"
        url_color = "green"
        table.add_column("tweet_id", style=url_color)
        table.add_column("text", style=text_color)
        query_str = input("Please enter your query: ")
        # Todo: proper URL encoding
        if query_str[0] == "#":
            query_str_fixed = query_str[1:]
            query_str_fixed = "%23" + query_str_fixed
        # elif query_str[0] == '@':
        #    query_str_fixed = query_str[1:]
        #    query_str_fixed = "%40" + query_str_fixed
        else:
            query_str_fixed = query_str
        console.clear()
        if (
            query_str.lower() == "quit"
            or query_str.lower() == "exit"
            or query_str.lower() == "q"
        ):
            break
        # url = f"https://api.twitter.com/2/tweets/search/recent?query={query_str_fixed}"
        url = f"https://api.twitter.com/2/tweets/search/recent?query={query_str_fixed}&max_results=20"
        now = datetime.now()
        timestamp = now.timestamp()
        if queries.get(query_str, None):
            q = queries[query_str]
            ts = q["timestamp"]
            if timestamp - ts > threshold:
                print("Updated search for", query_str)
                response = client.get(url, headers=headers)
                response_json = response.json()
                data = response_json["data"]
                tweets = [(tweet["id"], tweet["text"]) for tweet in data]
                add_tweets_to_table(table, tweets)
                console.print(table)
                update_queries("queries.json", query_str, queries, timestamp, tweets)
            else:
                print("Old search for", query_str)
                tweets = q["tweets"]
                add_tweets_to_table(table, tweets)
                console.print(table)
        else:
            print("New search for", query_str)
            response = client.get(url, headers=headers)
            response_json = response.json()
            data = response_json.get("data", None)
            if not data:
                print(response_json)
                sys.exit(-1)
            tweets = [(tweet["id"], tweet["text"]) for tweet in data]
            add_tweets_to_table(table, tweets)
            console.print(table)
            update_queries("queries.json", query_str, queries, timestamp, tweets)


if __name__ == "__main__":
    main()
