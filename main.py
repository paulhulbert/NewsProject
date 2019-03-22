from flask import Flask, render_template, request, session, redirect
import requests
from lxml import objectify
from datetime import datetime
from operator import itemgetter
import json


app = Flask(__name__)
app.secret_key = b'PaulIsAwesome'

data = dict()


def load_data():
    fil = open('data.json', 'r')
    global data
    data = json.loads(fil.read())
    fil.close()


def save_data():
    fil = open('data.json', 'w')
    data_string = json.dumps(data)
    fil.write(data_string)
    fil.close()


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session and session['username'] in data['users']:
        return redirect('/')

    if request.method == 'POST':
        if request.form['username'] in data['users'] and request.form['password'] == data['users'][request.form['username']]['password']:
            session['username'] = request.form['username']
            return redirect('/')
        else:
            return render_template('login.html', error="Incorrect username or password")
    return render_template('login.html')


@app.route('/logout', methods=['GET'])
def logout():
    session.clear()
    return redirect('/login')


@app.route('/')
def index():
    items = merge_feeds([get_items_from_rss(get_espn_feed("NHL")), get_items_from_rss(get_espn_feed("NFL")), get_items_from_rss(get_espn_feed("NBA"))])
    return render_template('index.html', items=items)


@app.route('/feed/<sport>')
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
    load_data()
    app.run('0.0.0.0')
