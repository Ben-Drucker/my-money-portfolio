from threading import local
from flask import Flask, render_template, request, jsonify
import sqlite3

username = "guest-web"

import plaid

import flask_cors

app = Flask(__name__)

client = plaid.Client(client_id='60a8883ef567db0011653ef1',
                      secret='78848d300c58f198b62864cb0bdbde',
                      environment='sandbox')

access_token = None

localhostport = 8080
flask_cors.CORS(app)

app.config['SERVER_NAME'] = 'mymoneyportfol.io'+ ":" + str(localhostport)
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
    response = client.LinkToken.create({
        'user': {
            'client_user_id': "01",
        },
        'products': ["auth"],
        'client_name': 'The Portfolio analyzer',
        'country_codes': ['US'],
        'language': 'en',
    })
    # Send the data to the client — in this case, just return some text for now.
    return jsonify(response)


@app.route("/main/plaid_parser", methods=['GET'])
def plaidParser():
    try:
        accounts_response = client.Accounts.get(access_token)
    except plaid.errors.PlaidError as e:
        return jsonify({'error': {'display_message': e.display_message, 'error_code': e.code, 'error_type': e.type}})

    res = ""

    account_dict = dict(accounts_response)

    user_results = {'accounts': []}
    global id_dict
    id_dict = {}

    res += "Accounts found:<br>"
    for account in account_dict['accounts']:
        account_info = {'display_name':"", 'bal': 0}

        name = str(account['official_name'])
        if name == "None":
            name = str(account['name'])
        res += name
        account_info['display_name'] = name
        id_name = name.replace(" ", "")
        account_info['id_name'] = id_name
        id_dict[id_name] = name
        res += " | Balance = "
        bal = account['balances']['current']
        account_info['bal'] = bal;
        res += str(bal)
        res += "<br>"
        user_results['accounts'].append(account_info)

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

    accounts_dict = request.form.to_dict()
    message = "<p>You Selected:</p>\
            <ul>"
    for name_id in accounts_dict:
        message += ("<li>" + id_dict[name_id] + "</li>")

    message += "</ul>"

    connection = sqlite3.connect("private/users.db")
    cursor = connection.cursor()

    username = "guest-web"
    acct_name = "acct-web"
    acct_bal = 421.27
    message = "message-web"

    SQLrequest = "insert into account_data (username, acct_name, acct_bal, message) values (?, ?, ?, ?)"
    actual_vals = (username, acct_name, acct_bal, message)
    cursor.execute(SQLrequest, actual_vals)
    connection.commit()
    cursor.close()
    return "/"

@app.route("/main/select_bank_accounts_feedback", methods=['GET'])
def select_bank_accounts_feedback():

    connection = sqlite3.connect("private/users.db")
    cursor = connection.cursor()
    SQLrequest = "select message from account_data where username=?"
    actual_vals = (username, )
    cursor.execute(SQLrequest, actual_vals)
    res = cursor.fetchall()
    connection.commit()
    cursor.close()
    
    try:
        return str(res[0])
    except IndexError:
        pass
    return "e r r o r"


if __name__ == "__main__":
    app.run(port=localhostport)