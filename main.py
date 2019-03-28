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


@app.route('/createaccount', methods=['GET', 'POST'])
def create_account():
    if 'username' in session and session['username'] in data['users']:
        return redirect('/')

    if request.method == 'POST':
        if request.form['username'] in data['users']:
            return render_template('create_account.html', error="Username already in use")
        elif request.form['password'] != request.form['password2']:
            return render_template('create_account.html', error="Passwords do not match")
        else:
            new_user = {'password': request.form['password'], 'last_login': datetime.now().ctime(),
                        'current_login': datetime.now().ctime(), 'favorites': []}
            data['users'][request.form['username']] = new_user
            save_data()
            session['username'] = request.form['username']
            return redirect('/')
    return render_template('create_account.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session and session['username'] in data['users']:
        return redirect('/')

    if request.method == 'POST':
        if request.form['username'] in data['users'] and request.form['password'] == \
                data['users'][request.form['username']]['password']:
            session['username'] = request.form['username']
            data['users'][session['username']]['last_login'] = data['users'][session['username']]['current_login']
            data['users'][session['username']]['current_login'] = datetime.now().ctime()
            save_data()
            return redirect('/')
        else:
            return render_template('login.html', error="Incorrect username or password")
    return render_template('login.html')


@app.route('/logout', methods=['GET'])
def logout():
    session.clear()
    return redirect('/login')


@app.route('/', methods=['GET', 'POST'])
def index():
    if 'username' not in session or session['username'] not in data['users']:
        return redirect('/login')
    if request.method == 'POST':
        toggle_favorite(request.form['guid'])
    items = merge_feeds([get_items_from_rss(get_espn_feed("NHL")), get_items_from_rss(get_espn_feed("NFL")),
                         get_items_from_rss(get_espn_feed("NBA"))])
    return render_template('index.html', items=items, last_login=data['users'][session['username']]['last_login'],
                           title='Home')


@app.route('/feed/<sport>', methods=['GET', 'POST'])
def specific_page(sport):
    if 'username' not in session or session['username'] not in data['users']:
        return redirect('/login')
    if request.method == 'POST':
        toggle_favorite(request.form['guid'])

    if sport != 'favorites':
        items = get_items_from_rss(get_espn_feed(sport))
    else:
        all_items = merge_feeds([get_items_from_rss(get_espn_feed("NHL")), get_items_from_rss(get_espn_feed("NFL")),
                                 get_items_from_rss(get_espn_feed("NBA"))])
        items = []
        for item in all_items:
            if item['favorite']:
                items.append(item)

    return render_template('index.html', items=items, last_login=data['users'][session['username']]['last_login'],
                           title=sport)


def toggle_favorite(guid):
    if guid in data['users'][session['username']]['favorites']:
        remove_favorite(guid)
    else:
        add_favorite(guid)
    save_data()


def add_favorite(guid):
    if guid not in data['users'][session['username']]['favorites']:
        data['users'][session['username']]['favorites'].append(guid)


def remove_favorite(guid):
    if guid in data['users'][session['username']]['favorites']:
        data['users'][session['username']]['favorites'].remove(guid)


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
        item_dict['favorite'] = item.guid.text in data['users'][session['username']]['favorites']
        items.append(item_dict)
    items.sort(key=itemgetter('dt'), reverse=True)
    return items


def get_espn_feed(sport):
    return objectify.fromstring(requests.get("http://www.espn.com/espn/rss/" + sport + "/news").content)


if __name__ == '__main__':
    load_data()
    app.run('0.0.0.0', port=31042)
