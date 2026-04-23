import json
from pathlib import Path

import flask

from utils import TEMPLATE_FOLDER, FLASK_PORT, FLASK_ADDRESS, load_config, reset_config, save_config, get_wifi, set_wifi


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

        set_wifi(ssid, password)

        return {"status": "success"}, 200

    @app.route("/reset", methods=["POST"])
    def reset():
        reset_config()
        set_wifi("","", start=False)
        return {"status": "success"}, 200

    print('starting')
    app.run(host=FLASK_ADDRESS, port=FLASK_PORT, use_reloader=False)


if __name__ == "__main__":
    main()
