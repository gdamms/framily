from PIL import Image, ImageOps
from pathlib import Path
from inotify.adapters import Inotify
import json
from frame_core.settings import EPD_IMAGE_PATH, EPD_INFO_PATH
from epd import epd7in3e


def render_image(epd: epd7in3e.EPD, image_path: Path):
    if not image_path.exists():
        print(f"Image file '{image_path}' not found. Cannot display.")
        return
    img = Image.open(image_path)
    img = img.rotate(90, expand=True)
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


def drain_events(watcher):
    while True:
        event = next(watcher.event_gen(yield_nones=False, timeout_s=0), None)
        if event is None:
            break


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

    watcher = Inotify()
    watcher.add_watch(str(EPD_IMAGE_PATH.parent))
    interested_events = {
        'IN_CLOSE_WRITE',
        'IN_CREATE',
        'IN_MOVED_TO',
        'IN_DELETE',
    }

    try:
        for event in watcher.event_gen(yield_nones=False):
            if event is None:
                continue

            _, type_names, _, file_name = event
            if file_name == EPD_IMAGE_PATH.name and interested_events.intersection(type_names):
                drain_events(watcher)
                render_image(epd, EPD_IMAGE_PATH)
    except KeyboardInterrupt:
        watcher.remove_watch(str(EPD_IMAGE_PATH.parent))


if __name__ == '__main__':
    main()
