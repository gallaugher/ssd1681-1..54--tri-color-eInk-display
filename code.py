import time
import board
import busio
import displayio
import adafruit_ssd1681
import digitalio
import terminalio
from fourwire import FourWire
from adafruit_display_text import label
from adafruit_bitmap_font import bitmap_font
from adafruit_debouncer import Debouncer

displayio.release_displays()

# Display setup for Pico W using EYESPI
spi = busio.SPI(clock=board.GP18, MOSI=board.GP19)
epd_cs = board.GP17
epd_dc = board.GP21
epd_reset = board.GP15
epd_busy = board.GP2  # Use this if your display has a BUSY pin connected

display_bus = FourWire(
    spi,
    command=epd_dc,
    chip_select=epd_cs,
    reset=epd_reset,
    baudrate=1000000
)

time.sleep(1)

display = adafruit_ssd1681.SSD1681(
    display_bus,
    width=200,
    height=200,
    busy_pin=epd_busy,  # Use None if BUSY not connected
    highlight_color=0xFF0000,
    rotation=180,
)

# Setup LED on GP6 (assumes active HIGH LED: True = ON)
led = digitalio.DigitalInOut(board.GP6)
led.direction = digitalio.Direction.OUTPUT
led.value = False  # Start with LED off

# Button setup with Debouncer on GP20
pin = digitalio.DigitalInOut(board.GP20)
pin.direction = digitalio.Direction.INPUT
pin.pull = digitalio.Pull.UP
button = Debouncer(pin)

# Load fonts
try:
    font_large = bitmap_font.load_font("/fonts/helvB18.bdf")
    font_small = bitmap_font.load_font("/fonts/helvB12.bdf")
    print("Fonts loaded successfully")
except Exception as e:
    import traceback
    print("Font loading error:")
    traceback.print_exception(e)
    font_large = terminalio.FONT
    font_small = terminalio.FONT

# State tracking
showing_image = False
last_refresh_time = 0

def create_white_background():
    bg_bitmap = displayio.Bitmap(200, 200, 1)
    bg_palette = displayio.Palette(1)
    bg_palette[0] = 0xFFFFFF
    return displayio.TileGrid(bg_bitmap, pixel_shader=bg_palette)

def show_info_page():
    print("📄 Showing info page...")
    g = displayio.Group()
    g.append(create_white_background())

    title_label = label.Label(
        font_large,
        text="SSD1681 eInk",
        color=0x000000,
        x=10,
        y=20
    )
    g.append(title_label)

    specs = [
        ("200x200 pixels", 0x000000, 50),
        ("Tri-color display", 0xFF0000, 70),
        ("Black/White/Red", 0x000000, 90),
        ("Low power design", 0xFF0000, 110),
        ("Can redraw every 3 min.", 0xFF0000, 130),
        ("Zero power static", 0x000000, 150),
        ("Paper-like view", 0x000000, 170),
        ("Press button for image", 0x000000, 190)
    ]

    for text, color, y_pos in specs:
        spec_label = label.Label(font_small, text=text, color=color, x=10, y=y_pos)
        g.append(spec_label)

    display.root_group = g
    display.refresh()
    print("📄 Info page displayed")

def show_image_page():
    print("🖼 Showing image page...")
    try:
        with open("/bc-logo-for-tri-color.bmp", "rb") as f:
            pic = displayio.OnDiskBitmap(f)
            print(f"🖼 Image size: {pic.width}x{pic.height}")

            g = displayio.Group()
            t = displayio.TileGrid(
                pic,
                pixel_shader=getattr(pic, "pixel_shader", displayio.ColorConverter())
            )
            g.append(t)

            display.root_group = g
            display.refresh()
            print("🖼 Image displayed")

    except Exception as e:
        print(f"❌ Image error: {e}")

# Initial display
print("🚀 Starting with info page...")
show_info_page()
last_refresh_time = time.monotonic()

# Main loop
print("🔁 Entering main loop with debounced button")

while True:
    current_time = time.monotonic()

    if current_time - last_refresh_time < 180:
        led.value = False  # Not ready, keep LED off
    else:
        led.value = True   # Ready, turn LED on

    button.update()
    if button.fell:
        if led.value:
            showing_image = not showing_image
            print(f"🔘 Button Pressed - toggling screen - showing_image: {showing_image}")
            if showing_image:
                show_image_page()
            else:
                show_info_page()
            last_refresh_time = time.monotonic()
        else:
            elapsed = current_time - last_refresh_time
            print(f"⏱ Refresh skipped: only {elapsed:.1f}s since last. Need 180s.")

    time.sleep(0.01)
