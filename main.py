from flask import Flask, render_template
import requests
from lxml import objectify
from datetime import datetime
from operator import itemgetter


app = Flask(__name__)


@app.route('/')
def index():
    items = merge_feeds([get_items_from_rss(get_espn_feed("NHL")), get_items_from_rss(get_espn_feed("NFL")), get_items_from_rss(get_espn_feed("NBA"))])
    return render_template('index.html', items=items)


@app.route('/<sport>')
def specific_page(sport):
    items = get_items_from_rss(get_espn_feed(sport))
    return render_template('index.html', items=items)


def merge_feeds(feeds):
    main_feed = []
    while True:
        item = pop_earliest_item(feeds)
        if not item:
            break
        main_feed.append(item)
    return main_feed


def pop_earliest_item(feeds):
    min_feed = None
    min_dt = datetime.fromordinal(1)

    for feed in feeds:
        if not feed:
            continue
        if feed[0]['dt'] > min_dt:
            min_feed = feed
            min_dt = feed[0]['dt']

    if not min_feed:
        return None
    return min_feed.pop(0)



def get_items_from_rss(rss_dump):
    items = []
    for item in rss_dump.channel.iterchildren(tag='item'):
        item_dict = {}
        item_dict['title'] = item.title.text
        item_dict['description'] = item.description.text
        item_dict['image'] = item.image.text
        item_dict['link'] = item.link.text
        item_dict['pubDate'] = item.pubDate.text
        item_dict['guid'] = item.guid.text
        item_dict['dt'] = datetime.strptime(item.pubDate.text, '%a, %d %b %Y %H:%M:%S EST')
        items.append(item_dict)
    items.sort(key=itemgetter('dt'), reverse=True)
    return items


def get_espn_feed(sport):
    return objectify.fromstring(requests.get("http://www.espn.com/espn/rss/" + sport + "/news").content)


if __name__ == '__main__':
    app.run('0.0.0.0')
