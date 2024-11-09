# ustoz_shogird_avto_bot


# How to run the bot on your local machine or server:
If server is not configured to use async functions, you can you the sync version of the bot by running the following command:
```bash
git checkout dev
```
This will switch to the sync version of the bot.
## 1. Install the requirements:
```
pip install -r requirements.txt
```
## 2. Create a .env file in the root directory of the project and add the following variables:
```
API_ID=your_api_id
API_HASH=your_api_hash
BOT_TOKEN=your_bot_token
```
## 3. Run the bot:
```bash
python main.py
```

# How to setWebhook:

## 1. Import process_single_update from webhook.py
```python
from webhook import process_single_update
```

## 2. Create a view function that will handle the incoming webhook request
```python
@app.route('/webhook', methods=['POST'])
def webhook():
    if request.json:
        process_single_update(request.json)
    return 'ok'
```
## 3. Don't forget to set the webhook
```python
from webhook import set_webhook

set_webhook(url='your_webhook_url')
```

# To Send a message to a user daily:
You can run the following command to send a message to a user daily:
```bash
python main.py get_data
python main.py send_data
```
It will scrape the data from the channel and send it to the users.