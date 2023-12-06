import requests
from flask import Flask, render_template, request
from datetime import datetime, timedelta

app = Flask(__name__)
app.static_folder = 'static'

# API details
# api_url = "Your API URL"
# basic_auth = (Your userid & password)

# Define conversation states
states = {
    "START": 0,
    "SELECT_COMPANY": 1,
    "SELECT_DATE_RANGE": 2,
    "SELECT_START_DATE": 3,
    "SELECT_END_DATE": 4,
    "DISPLAY_COLLECTION": 5,
    "LAST_CONVERSATION": 6  
}

current_state = states["START"]
selected_company = ""
start_date = ""
end_date = ""
collection_amount = ""

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/get")
def get_bot_response():
    global current_state, selected_company, start_date, end_date, collection_amount

    userText = request.args.get('msg')
    bot_response = ""

    if current_state == states["START"]:
        if userText == "1":
            bot_response = "Please reply with the company for collection by selecting one of the following options:<br>"
            # Fetch the list of companies from the API
            companies = fetch_companies()
            company_list = "<br>".join([f"{index+1}. {company}" for index, company in enumerate(companies)])
            bot_response += f"{company_list}"  #Your key reference from API
            current_state = states["SELECT_COMPANY"]
        elif userText == "2":
            bot_response = "You selected 'Outstanding'. This feature is currently not available."
        else:
            bot_response = "Invalid input. Please select one of the following options:<br>1. Collection<br>2. Outstanding"

    elif current_state == states["SELECT_COMPANY"]:
        # User selected a company by entering a number
        company_index = int(userText) - 1
        companies = fetch_companies()
        if company_index >= 0 and company_index < len(companies):
            selected_company = companies[company_index]
            bot_response = "Please reply with the date range for the selection:<br>"
            bot_response += "1. Today<br>"
            bot_response += "2. Current Month<br>"
            bot_response += "3. Current Quarter<br>"
            bot_response += "4. Last Quarter<br>"
            bot_response += "5. Current Year<br>"
            bot_response += "6. Other"
            current_state = states["SELECT_DATE_RANGE"]
        else:
            bot_response = "Invalid input. Please select a valid company.<br>"
            bot_response += "Please reply with the company for collection by selecting one of the following options:<br>"
            company_list = "<br>".join([f"{index+1}. {company}" for index, company in enumerate(companies)])
            bot_response += f"{company_list}"
            return bot_response

    elif current_state == states["SELECT_DATE_RANGE"]:
        if userText == "1":  # Today
            today = datetime.now()
            start_date = today.strftime("%d-%m-%Y")
            end_date = today.strftime("%d-%m-%Y")
        elif userText == "2":  # Current Month
            today = datetime.now()
            start_date = today.replace(day=1).strftime("%d-%m-%Y")
            end_date = today.strftime("%d-%m-%Y")
        elif userText == "3":  # Current Quarter
            today = datetime.now()
            quarter_start = (today.month - 1) // 3 * 3 + 1
            start_date = today.replace(month=quarter_start, day=1).strftime("%d-%m-%Y")
            end_date = today.strftime("%d-%m-%Y")
        elif userText == "4":  # Last Quarter
            today = datetime.now()
            quarter_start = (today.month - 1) // 3 * 3 - 3 + 1
            quarter_end = quarter_start + 2
            start_date = today.replace(month=quarter_start, day=1).strftime("%d-%m-%Y")
            end_date = today.replace(month=quarter_end, day=1).strftime("%d-%m-%Y")
        elif userText == "5":  # Current Year
            today = datetime.now()
            start_date = today.replace(month=1, day=1).strftime("%d-%m-%Y")
            end_date = today.strftime("%d-%m-%Y")
        elif userText == "6":  # Other
            bot_response = "Please enter the start date in the format (DD-MM-YYYY)."
            current_state = states["SELECT_START_DATE"]
            return bot_response
        else:
            bot_response = "Invalid input. Please select a valid date range option:<br>"
            bot_response += "1. Today<br>"
            bot_response += "2. Current Month<br>"
            bot_response += "3. Current Quarter<br>"
            bot_response += "4. Last Quarter<br>"
            bot_response += "5. Current Year<br>"
            bot_response += "6. Other"
            return bot_response


        # Convert the date format from DD-MM-YYYY to YYYY-MM-DD for API
        start_date_api = datetime.strptime(start_date, "%d-%m-%Y").strftime("%Y-%m-%d")
        end_date_api = datetime.strptime(end_date, "%d-%m-%Y").strftime("%Y-%m-%d")

        # Fetch collection data from the API based on the selected company and date range
        collection_amount = fetch_collection_amount(selected_company, start_date_api, end_date_api)
        bot_response = f"Your collection for company '{selected_company}' for the duration {start_date} to {end_date} is Rs. {collection_amount}<br><br>"
        bot_response += "To proceed further, reply with the following options:<br>1- Main Menu<br>2- Revise your date range<br>3- Indicate that you've completed your request."
        current_state = states["LAST_CONVERSATION"]  # Update state to the last conversation state

    elif current_state == states["SELECT_START_DATE"]:
        # User entered the start date for the "Other" option
        start_date = userText.strip()
        bot_response = "Please enter the end date in the format (DD-MM-YYYY)."
        current_state = states["SELECT_END_DATE"]

    elif current_state == states["SELECT_END_DATE"]:
        # User entered the end date for the "Other" option
        end_date = userText.strip()

        # Fetch collection data from the API based on the selected company and date range
        collection_amount = fetch_collection_amount(selected_company, start_date, end_date)
        bot_response = f"Your collection for company '{selected_company}' for the duration {start_date} to {end_date} is Rs. {collection_amount}<br><br>"
        bot_response += "To proceed further, reply with the following options:<br>1- Main Menu<br>2- Revise your date range<br>3- Indicate that you've completed your request."
        current_state = states["LAST_CONVERSATION"]  # Update state to the last conversation state

    elif current_state == states["LAST_CONVERSATION"]:
        if userText == "1":
            # Redirect to the initial stage
            current_state = states["START"]
            bot_response = "Please reply with the company for collection by selecting one of the following options:<br>"
            # Fetch the list of companies from the API
            companies = fetch_companies()
            company_list = "<br>".join([f"{index+1}. {company}" for index, company in enumerate(companies)])
            bot_response += f"{company_list}"
        elif userText == "2":
            # Redirect to the date range options
            current_state = states["SELECT_DATE_RANGE"]
            bot_response = "Please reply with the date range for the selection:<br>"
            bot_response += "1. Today<br>"
            bot_response += "2. Current Month<br>"
            bot_response += "3. Current Quarter<br>"
            bot_response += "4. Last Quarter<br>"
            bot_response += "5. Current Year<br>"
            bot_response += "6. Other"
        elif userText == "3":
            # Indicate completion of the request
            current_state = states["START"]
            bot_response = "Thank you for using EstateBot.<br>Have a nice day! 😊"
        else:
            bot_response = "Invalid input. Please select one of the following options:<br>1. Main Menu<br>2. Revise your date range<br>3. Indicate that you've completed your request."

    return bot_response


def fetch_companies():
    # Fetch the list of companies from the API
    # url = f"Your API URL"
    response = requests.get(url, auth=basic_auth)
    if response.status_code == 200:
        companies = response.json().get("d", {}).get("results", [])
        return [company[""] for company in companies]
    return []


def fetch_collection_amount(company, start_date, end_date):
    # Fetch the collection amount from the API
    # url = f"Your API URL"
    response = requests.get(url, auth=basic_auth)
    if response.status_code == 200:
        collection_data = response.json().get("d", {}).get("results", [])
        if collection_data:
            return collection_data[0][""]
    return "No data available"


if __name__ == '__main__':
    app.run(debug=True)



