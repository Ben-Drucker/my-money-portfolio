from curses import meta
import flask_cors
import plaid
from locale import currency
from threading import local
from flask import Flask, json, render_template, request, jsonify
import sqlite3, requests

username = "guest-web"


app = Flask(__name__)

client = plaid.Client(client_id='60a8883ef567db0011653ef1',
                      secret='78848d300c58f198b62864cb0bdbde',
                      environment='sandbox')

access_token = None

localhostport = 8080
flask_cors.CORS(app)

#app.config['SERVER_NAME'] = 'mymoneyportfol.io' + ":" + str(localhostport)
public_token = None


@app.route("/", subdomain="test")
def about_page():
    return render_template("about.html")


@app.route("/howitworks", subdomain="about")
def how_it_works():
    return render_template("howitworks.html")


@app.route("/")
def log_in_page():
    return render_template("login.html")


@app.route("/main")
def main_page():
    return render_template("main.html")


@app.route("/main/plaidinit", methods=['POST'])
def plaid_init():
    # Create a link_token for the given user
    # response = client.LinkToken.create(
    #     {
    #     'user': {
    #         'client_user_id': "01",
    #     },
    #     'products': ["auth"],
    #     'client_name': 'The Portfolio analyzer',
    #     'country_codes': ['US'],
    #     'language': 'en',
    #     }
    # )

    response = client.Sandbox.public_token.create(
        'ins_109511', ['auth']
    )

    # Send the data to the client — in this case, just return some text for now.
    return jsonify(response)


@app.route("/main/plaid_parser", methods=['GET'])
def plaidParser():
    try:
        accounts_response = client.Accounts.get(access_token)
    except plaid.errors.PlaidError as e:
        return jsonify({'error': {'display_message': e.display_message, 'error_code': e.code, 'error_type': e.type}})

    account_dict = dict(accounts_response)

    user_results = {'accounts': []}

    global id_dict
    id_dict = {}

    for account in account_dict['accounts']:
        account_info = {}
      
        name = str(account['official_name'])
        if name == "None":
            name = str(account['name'])
        id_name = name.replace(" ", "")

        bal = account['balances']['current']
        currency = account['balances']['iso_currency_code']
        subtype = account['subtype']
        type = account['type']

        account_info['bal'] = bal
        account_info['display_name'] = name
        account_info['subtype'] = subtype
        account_info['type'] = type
        account_info['currency'] = currency
        account_info['id_name'] = id_name
        account_info['user_selected'] = 0
        id_dict[id_name] = name
        account_info['username'] = username

        user_results['accounts'].append(account_info)

    metadata = {'institution_id': account_dict['item']['institution_id'],
                'item_id': account_dict['item']['item_id'],
                'request_id': account_dict['request_id']
                }

    connection = sqlite3.connect("private/account_data.sqlite")
    cursor = connection.cursor()

    for user_result in user_results['accounts']:
        cmd_data = "insert into user_account_data ({}) values ('{}')".format(", ".join([str(k) for k in user_result.keys()]), "', '".join([str(v) for v in user_result.values()]))
        try:
            cursor.execute(cmd_data)
        except sqlite3.IntegrityError as sqliteIntegError:
            print("Skipping insertion due to integrity error (probably preventing insertion of duplicate value.")

    try:
        cmd_metadata = "insert into user_account_metadata ({}) values ('{}')".format(", ".join([str(k) for k in metadata.keys()]), "', '".join([str(v) for v in metadata.values()]))
    except sqlite3.IntegrityError as sqliteIntegError:
            print("Skipping insertion due to integrity error (probably preventing insertion of duplicate value.")
    
    cursor.execute(cmd_metadata)
    
    connection.commit()
    cursor.close()

    return jsonify(user_results)


@app.route("/main/plaid_public_token", methods=['POST'])
def exchange_public_token():
    global access_token
    public_token = request.form['public_token']
    exchange_response = client.Item.public_token.exchange(public_token)
    access_token = exchange_response['access_token']
    item_id = exchange_response['item_id']
    return jsonify(exchange_response)


@app.route("/main/select_bank_accounts", methods=['POST'])
def select_bank_accounts():

    connection = sqlite3.connect("private/account_data.sqlite")
    cursor = connection.cursor()

    accounts_dict = request.form.to_dict()
    message = "<p class = medium_heading>You Selected:</p>\
            <ul class = ulplain>"

    look_for_names_cmd = "select display_name, id_name from user_account_data where username='{}'".format(username)
    cursor.execute(look_for_names_cmd)
    res = list(cursor)
    displays = [x[0] for x in res]
    ids = [x[1] for x in res]
    i = 0
    for id in ids:
        if id in accounts_dict:
            bit = 1
            message += ("<li class = liplain>" + displays[i] + "</li>")
        else:
            bit = 0
        cursor.execute("UPDATE user_account_data SET user_selected={} WHERE username='{}' and display_name='{}'".format(bit, username, displays[i]))
        connection.commit()
        i += 1

    message += "</ul>"

    connection.commit()
    cursor.close()

    pie = update_pie()

    return jsonify(message=message, net_worth=getNetWorth(username), pie_labels=pie['categories'], pie_vals=pie['values'], pie_labels_debt=pie['categories_debt'], pie_vals_debt=pie['values_debt'])

def update_pie():
    
    connection = sqlite3.connect("private/account_data.sqlite")
    cursor = connection.cursor()
    cmd = "select subtype, bal, type from user_account_data where username='{}' and user_selected = 1".format(username)
    cursor.execute(cmd)
    res = list(cursor)
    categories = []
    values = []
    categories_debt = []
    values_debt = []
    for x in res:
        if x[2] == "loan":
            values_debt.append(x[1])
            categories_debt.append(x[0])
        else:
            values.append(x[1])
            categories.append(x[0])
    return {'categories': categories, 'values': values, 'categories_debt': categories_debt, 'values_debt': values_debt}


def getNetWorth(username):
    total = 0
    connection = sqlite3.connect("private/account_data.sqlite")
    cursor = connection.cursor()
    cursor.execute(
        "select bal, display_name, type from user_account_data where username=? and user_selected=?", (username,1))
    res = list(cursor)
    for line in res:
        if line[2] != "loan":
            total += float(line[0])
        else:
            total -= float(line[0])

    return "%.2f" %(total)

@app.route("/main/process_stocks", methods=['POST'])
def process_stocks():
    dicts = []
    data = request.form.to_dict()
    current_pack = {}
    for ticker in data:
        if data[ticker] != "":
            if "ss" in ticker:
                current_pack['symbol'] = data[ticker].upper()
            elif "pd" in ticker:
                date_list = data[ticker].split("-")
                current_pack['date'] = "-".join([date_list[2], date_list[0], date_list[1]])
            elif "pp" in ticker:
                current_pack['price'] = data[ticker].replace("$", "")
                dicts.append(current_pack)
                current_pack = {}

    for d in dicts:
        #historical data

        url = 'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol=%s&outputsize=full&apikey=TH9WK3EYIB6D3SPF' %(d['symbol'])
        r = requests.get(url)
        data = r.json()
        if "Error Message" in data:
            print("The symbol \"%s\" is invalid." %(d['symbol']))
        else:
            print(data['Time Series (Daily)'][d['date']]['5. adjusted close'])
            pass

        #current data

        url = 'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=IBM&apikey=TH9WK3EYIB6D3SPF'
        r = requests.get(url)
        data = r.json()
        if "Error Message" in data:
            print("The symbol \"%s\" is invalid." %(d['symbol']))
        else:
            print(data['Global Quote']['05. price'])
            pass


    print(dicts)
    return "success"

# format {'ss1': 'ibm', 'pd1': '03-20-2020', 'pp1': '$100.10', 'ss2': '', 'pd2': '', 'pp2': '', 'ss3': '', 'pd3': '', 'pp3': ''}


if __name__ == "__main__":
    app.run(port=localhostport, debug=True)
