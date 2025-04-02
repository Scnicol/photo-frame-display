import requests
import io
import threading
import time
import logging
import pi3d

# Configuration
PHOTO_SERVER_URL = "http://localhost:5001/api/photos/random-photo"
DISPLAY_TIME = 3  # Seconds to show each photo
FPS = 10

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class PhotoFrameDisplay:
    def __init__(self):
        logging.info("Initializing display...")
        self.display = pi3d.Display.create(fullscreen=True, background=(0, 1, 0, 1), frames_per_second=FPS)
        self.shader = pi3d.Shader("uv_flat")

        self.sprite = pi3d.Sprite(camera=pi3d.Camera(is_3d=False), w=self.display.width, h=self.display.height)
        self.sprite.set_shader(self.shader)

        self.next_image_data = None

        logging.info("Starting background image fetch thread.")
        self.fetch_thread = threading.Thread(target=self.fetch_next_photo, daemon=True)
        self.fetch_thread.start()

    def load_photo_from_memory(self, image_data):
        """Load a texture directly from in-memory image data."""
        logging.info("Loading new image into texture.")
        texture = pi3d.Texture(io.BytesIO(image_data), mipmap=True)
        self.sprite.set_textures([texture])

    def fetch_next_photo(self):
        """Request the next photo from the server in the background."""
        while True:
            start_time = time.time()
            try:
                response = requests.get(PHOTO_SERVER_URL, timeout=5)
                elapsed_time = time.time() - start_time
                logging.info(f"Image request completed in {elapsed_time:.2f} seconds.")

                if response.status_code != 200:
                    raise requests.HTTPError(f"HTTP Error {response.status_code}")

                if response.content:
                    self.next_image_data = response.content
                else:
                    logging.warning("Received empty image data, keeping current display.")

            except requests.RequestException as e:
                logging.error(f"Error fetching photo: {e}")

            time.sleep(DISPLAY_TIME)

    def run(self):
        """Main display loop with FPS control."""
        logging.info("Entering main display loop.")
        while self.display.loop_running():
            if self.next_image_data:
                image_data = self.next_image_data  # Copy to local variable
                self.next_image_data = None  # Immediately reset shared variable
                self.load_photo_from_memory(image_data)

            self.sprite.draw()

if __name__ == "__main__":
    display = PhotoFrameDisplay()
    display.run()
