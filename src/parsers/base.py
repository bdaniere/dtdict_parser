from models.pages import ImagePage, PDFPage, XMLPage


class ParserFactory:
    def __init__(self, page: XMLPage | PDFPage | ImagePage):
        """
        Initialize the parser with the page it has to read.

        Args:
            page: a single page, already read from the file by DocumentReader.
        """

        self.page = page
