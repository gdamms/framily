import flask
from urllib.parse import urlparse

from frame_core.config import ConfigStore, FrameState
from frame_core.logging import get_logger
from frame_core.network import CommandError, start_hotspot_connection
from utils import FLASK_ADDRESS, FLASK_PORT, TEMPLATE_FOLDER, get_wifi, set_wifi


logger = get_logger(__name__)
store = ConfigStore()


def _is_valid_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _validate_setup_payload(ssid: str, password: str, url: str) -> str | None:
    if not ssid:
        return "Wi-Fi SSID cannot be empty."
    if not password:
        return "Wi-Fi password cannot be empty."
    if len(password) < 8:
        return "Wi-Fi password must be at least 8 characters."
    if not _is_valid_url(url):
        return "Server URL must be a valid http(s) URL."
    return None


def main():
    app = flask.Flask(__name__, template_folder=TEMPLATE_FOLDER)

    @app.route("/")
    def index():
        config = store.load()
        try:
            ssid, password = get_wifi()
        except CommandError:
            ssid, password = "", ""

        message = config.get("message", "")
        last_error = config.get("last_error", "")
        last_error_at = int(config.get("last_error_at") or 0)
        state = config.get("state", FrameState.UNCONFIGURED.value)

        return flask.render_template(
            "index.html",
            ssid=ssid,
            password=password,
            message=message,
            last_error=last_error,
            last_error_at=last_error_at,
            state=state,
            url=config.get("server_url", ""),
        )

    @app.route("/setup", methods=["POST"])
    def setup():
        data = flask.request.form
        ssid = data.get("ssid", "").strip()
        password = data.get("password", "").strip()
        url = data.get("url", "").strip()

        validation_error = _validate_setup_payload(ssid, password, url)
        if validation_error:
            store.save_message(validation_error)
            return {"status": "error", "message": validation_error}, 400

        try:
            set_wifi(ssid, password, start=True)
        except CommandError as error:
            logger.error("Failed to set Wi-Fi credentials: %s", error)
            store.save_message("Failed to apply Wi-Fi credentials. Please verify and retry.")
            return {"status": "error", "message": "Wi-Fi configuration failed"}, 500

        store.update(
            server_url=url,
            message="",
            state=FrameState.CONNECTING_WIFI.value,
        )

        return {"status": "success"}, 200

    @app.route("/reset", methods=["POST"])
    def reset():
        store.reset()
        store.save_message("Configuration reset. Please configure the frame again.")

        try:
            start_hotspot_connection()
        except CommandError as error:
            logger.error("Failed to start hotspot after reset: %s", error)

        return {"status": "success"}, 200

    @app.route("/health", methods=["GET"])
    def health():
        config = store.load()
        return {
            "status": "ok",
            "state": config.get("state", FrameState.UNCONFIGURED.value),
            "last_success_at": config.get("last_success_at", 0),
            "last_error": config.get("last_error", ""),
            "consecutive_failures": config.get("consecutive_failures", 0),
        }, 200

    logger.info("Starting frame setup Flask service on %s:%s", FLASK_ADDRESS, FLASK_PORT)
    app.run(host=FLASK_ADDRESS, port=FLASK_PORT, use_reloader=False)


if __name__ == "__main__":
    main()
