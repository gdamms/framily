import hashlib

from PIL import Image, ImageOps
from pathlib import Path
import json
from epd import epd7in3e
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from logging_setup import get_logger
from utils import EPD_IMAGE_PATH, EPD_INFO_PATH

logger = get_logger("epd")


def render_image(epd: epd7in3e.EPD, image_path: Path):
    if not image_path.exists():
        logger.warning(f"Image file '{image_path}' not found. Cannot display.")
        return
    img = Image.open(image_path)
    resampling = Image.Resampling.LANCZOS
    img = ImageOps.fit(img, (epd.width, epd.height), method=resampling, centering=(0.5, 0.5))
    epd.display(epd.getbuffer(img))


def write_epd_info(epd: epd7in3e.EPD):
    width, height = epd.width, epd.height
    info = {
        "width": width,
        "height": height,
    }
    with open(EPD_INFO_PATH, 'w') as f:
        json.dump(info, f)


def file_hash(path, algo="sha256", chunk_size=8192):
    h = hashlib.new(algo)
    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            h.update(chunk)
    return h.hexdigest()


class EPDImageHandler(FileSystemEventHandler):
    """Watches EPD_IMAGE_PATH's parent directory rather than the file itself:
    watchdog's handling of a watch scheduled directly on a single file is not
    reliable across all backends, and a watch on a file that doesn't exist
    yet at schedule time can misbehave. Watching the directory and filtering
    by filename works whether or not the file exists yet.

    Handles on_moved as well as on_modified/on_created: an atomic replace
    (write to a temp file, then rename it over the destination - what rsync,
    many editors, and atomic-write helpers do) fires a moved event with the
    final path as dest_path, not a modified/created event on that path at
    all. Missing this means those tools silently never trigger a redraw."""

    def __init__(self, epd: epd7in3e.EPD):
        self.epd = epd
        self.hash = None

    def _maybe_render(self, path: str):
        if path != str(EPD_IMAGE_PATH):
            return
        new_hash = file_hash(EPD_IMAGE_PATH)
        if new_hash != self.hash:
            self.hash = new_hash
            try:
                render_image(self.epd, EPD_IMAGE_PATH)
                logger.info(f"Redrew display from '{EPD_IMAGE_PATH}' (hash {new_hash[:12]}).")
            except Exception as e:
                logger.exception(f"Error occurred while rendering image: {e}")

    def on_modified(self, event):
        if not event.is_directory:
            self._maybe_render(event.src_path)

    def on_created(self, event):
        if not event.is_directory:
            self._maybe_render(event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            self._maybe_render(event.dest_path)


def main():
    epd = epd7in3e.EPD()
    event_handler = EPDImageHandler(epd)

    try:
        epd.init()

        # Save display info for other processes to read.
        write_epd_info(epd)

        # Draw once at startup when the image is already present, and seed
        # the handler's hash from it so the first file-system event after
        # startup doesn't trigger a redundant redraw of unchanged content.
        if EPD_IMAGE_PATH.exists():
            render_image(epd, EPD_IMAGE_PATH)
            event_handler.hash = file_hash(EPD_IMAGE_PATH)
            logger.info(f"Rendered '{EPD_IMAGE_PATH}' at startup (hash {event_handler.hash[:12]}).")
        else:
            logger.info(f"Image file '{EPD_IMAGE_PATH}' not found. Waiting for it to appear...")
    except epd7in3e.EPDBusyTimeoutError as e:
        logger.error(f"EPD startup failed: {e}")
        raise SystemExit(1) from e

    # Watch the parent directory for changes to the image file and update
    # the display accordingly.
    observer = Observer()
    observer.schedule(event_handler, path=str(EPD_IMAGE_PATH.parent), recursive=False)
    observer.start()
    observer.join()


if __name__ == '__main__':
    main()
