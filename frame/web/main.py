import json
import threading
import time
from pathlib import Path

import flask

from utils import TEMPLATE_FOLDER, WEB_PORT, WEB_ADDRESS, load_config, reset_config, save_config, get_wifi, set_wifi

# Give the HTTP response time to reach the browser over the hotspot link
# before nmcli brings up the Wi-Fi connection and tears the hotspot down.
WIFI_CONNECT_DELAY_SECONDS = 2


def main():
    app = flask.Flask(__name__, template_folder=TEMPLATE_FOLDER)

    @app.route("/")
    def index():
        config = load_config()
        ssid, password = get_wifi()
        message = config.get("message", "")

        return flask.render_template(
            "index.html",
            ssid=ssid,
            password=password,
            message=message,
            url=config['server_url'],
        )

    @app.route("/setup", methods=["POST"])
    def setup():
        data = flask.request.form
        ssid = data.get("ssid", "")
        password = data.get("password", "")
        url = data.get("url", "")

        config = load_config()
        config["server_url"] = url
        save_config(config)

        def connect_later():
            time.sleep(WIFI_CONNECT_DELAY_SECONDS)
            set_wifi(ssid, password)

        threading.Thread(target=connect_later, daemon=True).start()

        message = (
            "Credentials saved! Trying to connect to Wi-Fi and to the server. "
            "You can close this page and follow the instructions on the frame."
        )
        return {"status": "success", "message": message}, 200

    @app.route("/reset", methods=["POST"])
    def reset():
        reset_config()
        set_wifi("","", start=False)
        return {"status": "success"}, 200

    print('starting')
    app.run(host=WEB_ADDRESS, port=WEB_PORT, use_reloader=False)


if __name__ == "__main__":
    main()
