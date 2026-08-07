import flask

from logging_setup import LOG_PATH, get_logger
from utils import (
    AGENT_RECHECK_PATH,
    TEMPLATE_FOLDER,
    WEB_PORT,
    WEB_ADDRESS,
    load_config,
    save_config,
)

logger = get_logger("web")

LOG_TAIL_LINES = 500


def _tail_log(n: int) -> str:
    try:
        with open(LOG_PATH, "r", errors="replace") as f:
            lines = f.readlines()
    except OSError as e:
        return f"Could not read log file '{LOG_PATH}': {e}"
    return "".join(lines[-n:])


def main():
    app = flask.Flask(__name__, template_folder=TEMPLATE_FOLDER)

    @app.route("/")
    def index():
        config = load_config()
        message = config.get("message", "")

        return flask.render_template(
            "index.html",
            ssid=config.get("wifi_ssid", ""),
            password=config.get("wifi_password", ""),
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
        config["wifi_ssid"] = ssid
        config["wifi_password"] = password
        config["wifi_should_update"] = True
        save_config(config)
        AGENT_RECHECK_PATH.touch(exist_ok=True)
        logger.info(f"Setup submitted: server_url={url!r}, ssid={ssid!r}")

        message = (
            "Credentials saved! Trying to connect to Wi-Fi and to the server. "
            "You can close this page and follow the instructions on the frame."
        )
        return {"status": "success", "message": message}, 200

    @app.route("/reset", methods=["POST"])
    def reset():
        # Deletes the framily server-side, and only then forgets the
        # id/token locally so it registers a fresh framily, as if this were
        # the frame's first run. Wi-Fi credentials and the server URL are
        # left untouched - the user shouldn't have to re-enter them just
        # because the framily was deleted.
        logger.info("Framily reset requested; agent will delete it server-side.")
        config = load_config()
        config["pending_delete"] = True
        save_config(config)
        AGENT_RECHECK_PATH.touch(exist_ok=True)

        message = (
            "Framily reset requested! If a framily was previously registered, it is now being "
            "deleted from the server. You can then click on \"Setup Framily\" to register a new one."
        )
        return {"status": "success", "message": message}, 200

    @app.route("/logs")
    def logs():
        return flask.Response(_tail_log(LOG_TAIL_LINES), mimetype="text/plain")

    logger.info("Starting web UI.")
    app.run(host=WEB_ADDRESS, port=WEB_PORT, use_reloader=False, threaded=True)


if __name__ == "__main__":
    main()
