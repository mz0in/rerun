"""Create and log an image."""

import numpy as np
import rerun as rr

# Create an image with numpy
image = np.zeros((8, 12, 3), dtype=np.uint8)
image[:, :, 0] = 255
image[0:4, 0:6] = (0, 255, 0)

rr.init("rerun_example_image_simple", spawn=True)

rr.log("image", rr.Image(image))
