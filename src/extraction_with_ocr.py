import logging
import os

import cv2
import numpy as np

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s -- %(levelname)s -- %(message)s"
)

# Disable the PaddleX connectivity check (avoids an unnecessary network call at
# every PaddleOCR instantiation) and silence verbose model-loading INFO logs.
os.environ.setdefault("DISABLE_MODEL_SOURCE_CHECK", "True")
for _noisy_logger in ("paddlex", "paddle"):
    logging.getLogger(_noisy_logger).setLevel(logging.WARNING)


logger = logging.getLogger(__name__)


# ██████╗  █████╗ ██████╗ ██████╗ ██╗     ███████╗
# ██╔══██╗██╔══██╗██╔══██╗██╔══██╗██║     ██╔════╝
# ██████╔╝███████║██║  ██║██║  ██║██║     █████╗
# ██╔═══╝ ██╔══██║██║  ██║██║  ██║██║     ██╔══╝
# ██║     ██║  ██║██████╔╝██████╔╝███████╗███████╗
# ╚═╝     ╚═╝  ╚═╝╚═════╝ ╚═════╝ ╚══════╝╚══════╝


class PaddlePlanExtractor:
    def __init__(self, image_path, ocr):
        """
        OCR de plans techniques avec PaddleOCR

        :param image_path: (str) path to the image file
        :param ocr: (paddleocr._pipelines.ocr.PaddleOCR) OCR used for the process
        """

        self.image = self._load_image(image_path)
        # OCR is memory intensive on very large plans.
        # Limit the input resolution to avoid native crashes locally.
        self.max_ocr_pixels = int(os.getenv("ZCW_OCR_MAX_PIXELS", "16000000"))
        # Keep the largest side below PaddleOCR default hard limit to avoid hidden resizes.
        self.max_ocr_side = int(os.getenv("ZCW_OCR_MAX_SIDE", "3900"))
        self._ocr_scale_x = 1.0
        self._ocr_scale_y = 1.0
        self._ocr_offset_x = 0.0
        self._ocr_offset_y = 0.0
        self.crop_ocr_content = os.getenv("ZCW_OCR_CONTENT_CROP", "1") == "1"
        self.ocr_white_threshold = int(os.getenv("ZCW_OCR_WHITE_THRESHOLD", "245"))
        self.ocr_crop_padding = int(os.getenv("ZCW_OCR_CROP_PADDING", "20"))
        self.ocr = ocr

    def _load_image(self, image_path):
        """Load the image using OpenCV"""

        if not os.path.exists(image_path):
            raise FileNotFoundError(f"The file {image_path} does not exist.")

        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError(f"Unable to load the image {image_path}")

        return image

    def _prepare_ocr_image(self):
        """Return an image potentially downscaled for OCR and store inverse scales."""

        self._ocr_offset_x = 0.0
        self._ocr_offset_y = 0.0

        ocr_image = self.image
        if self.crop_ocr_content:
            gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
            content_mask = gray < self.ocr_white_threshold
            if np.any(content_mask):
                ys, xs = np.where(content_mask)
                min_x = max(0, int(xs.min()) - self.ocr_crop_padding)
                max_x = min(
                    self.image.shape[1] - 1, int(xs.max()) + self.ocr_crop_padding
                )
                min_y = max(0, int(ys.min()) - self.ocr_crop_padding)
                max_y = min(
                    self.image.shape[0] - 1, int(ys.max()) + self.ocr_crop_padding
                )

                ocr_image = self.image[min_y : max_y + 1, min_x : max_x + 1]
                self._ocr_offset_x = float(min_x)
                self._ocr_offset_y = float(min_y)

        height, width = ocr_image.shape[:2]
        num_pixels = height * width

        self._ocr_scale_x = 1.0
        self._ocr_scale_y = 1.0

        pixel_ratio = 1.0
        if self.max_ocr_pixels > 0 and num_pixels > self.max_ocr_pixels:
            pixel_ratio = (self.max_ocr_pixels / float(num_pixels)) ** 0.5

        side_ratio = 1.0
        max_side = max(width, height)
        if self.max_ocr_side > 0 and max_side > self.max_ocr_side:
            side_ratio = self.max_ocr_side / float(max_side)

        resize_ratio = min(pixel_ratio, side_ratio)
        if resize_ratio >= 1.0:
            return ocr_image

        new_width = max(1, int(width * resize_ratio))
        new_height = max(1, int(height * resize_ratio))
        if self.max_ocr_side > 0:
            new_width = min(new_width, self.max_ocr_side)
            new_height = min(new_height, self.max_ocr_side)

        resized = cv2.resize(
            ocr_image, (new_width, new_height), interpolation=cv2.INTER_AREA
        )
        self._ocr_scale_x = width / float(new_width)
        self._ocr_scale_y = height / float(new_height)

        logger.warning(
            "Image trop grande pour OCR (%sx%s -> %sx%s). "
            "Downscale temporaire applique via ZCW_OCR_MAX_PIXELS=%s, ZCW_OCR_MAX_SIDE=%s",
            width,
            height,
            new_width,
            new_height,
            self.max_ocr_pixels,
            self.max_ocr_side,
        )

        return resized

    def run(self):
        """Start detecting and recognizing text in the image"""

        ocr_image = self._prepare_ocr_image()
        self.paddle_result = self.ocr.predict(ocr_image, use_doc_unwarping=False)

        if not self.paddle_result:
            logger.warning("Aucun texte n'a été détecté sur l'impage")

        return self.paddle_result

    # def draw_output_image(self):
    #     """ """

    #     self.paddle_result[0].save_to_img(
    #         self.image_plan_instance.get_output_path("_ocr_paddle")
    #     )
