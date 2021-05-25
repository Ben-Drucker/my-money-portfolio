from flask import Flask, render_template, request, jsonify

import plaid

app = Flask(__name__)

client = plaid.Client(client_id='60a8883ef567db0011653ef1',
                      secret='78848d300c58f198b62864cb0bdbde',
                      environment='sandbox')

access_token = None


public_token = None


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
    print("generated token")
    return jsonify(response)


@app.route("/main/plaid_parser", methods=['GET'])
def plaidParser():
    print("top of plaidParser")
    try:
        accounts_response = client.Accounts.get(access_token)
        print("section 1")
    except plaid.errors.PlaidError as e:
        print("section 2")
        return jsonify({'error': {'display_message': e.display_message, 'error_code': e.code, 'error_type': e.type}})
    print("section 3")

    res = ""

    account_dict = dict(accounts_response)

    user_results = {'accounts': []}

    res += "Accounts found:<br>"
    for account in account_dict['accounts']:
        account_info = {'display_name':"", 'bal': 0}

        name = str(account['official_name'])
        if name == "None":
            name = str(account['name'])
        res += name
        account_info['display_name'] = name
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
    print("set access token.")
    item_id = exchange_response['item_id']
    return jsonify(exchange_response)


if __name__ == "__main__":
    app.run(port=42100)
