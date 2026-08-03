import hashlib

from PIL import Image, ImageOps
from pathlib import Path
import json
from epd import epd7in3e
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from utils import EPD_IMAGE_PATH, EPD_INFO_PATH


def render_image(epd: epd7in3e.EPD, image_path: Path):
    if not image_path.exists():
        print(f"Image file '{image_path}' not found. Cannot display.")
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
    def __init__(self, epd: epd7in3e.EPD):
        self.epd = epd
        self.hash = None

    def on_modified(self, event):
        new_hash = file_hash(EPD_IMAGE_PATH)
        if event.src_path == str(EPD_IMAGE_PATH) and new_hash != self.hash:
            self.hash = new_hash
            try:
                render_image(self.epd, EPD_IMAGE_PATH)
            except Exception as e:
                print(f"Error occurred while rendering image: {e}")


def main():
    epd = epd7in3e.EPD()
    epd.init()

    # Save display info for other processes to read.
    write_epd_info(epd)

    # Draw once at startup when the image is already present.
    if EPD_IMAGE_PATH.exists():
        render_image(epd, EPD_IMAGE_PATH)
    else:
        print(f"Image file '{EPD_IMAGE_PATH}' not found. Waiting for it to appear...")

    # Watch for changes to the image file and update the display accordingly.
    observer = Observer()
    event_handler = EPDImageHandler(epd)
    observer.schedule(event_handler, path=str(EPD_IMAGE_PATH))
    observer.start()
    observer.join()


if __name__ == '__main__':
    main()
