from pathlib import Path

from paddleocr import PaddleOCR

from extraction_with_ocr import PaddlePlanExtractor
from parsers.base import ParserFactory


class ImageParser(ParserFactory):
    TARGET_EPSG = "EPSG:2154"

    def __init__(self, file_path: Path):
        super().__init__(file_path)

    def read_content(self) -> list[str]:
        """
        Returns:
            list[str]: the texts recognized by the OCR in the image.
        """

        extractor = PaddlePlanExtractor(
            self.file_path,
            PaddleOCR(
                lang="fr",
                use_textline_orientation=True,
                # oneDNN crashes with Paddle 3.3 (ConvertPirAttribute2RuntimeAttribute)
                enable_mkldnn=False,
            ),
        )

        return [
            text for page_result in extractor.run() for text in page_result["rec_texts"]
        ]
