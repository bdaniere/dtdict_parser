from pathlib import Path


class ParserFactory:
    def __init__(self, file_path: Path):
        """
        Initialize the ParserFactory with the given file path.

        Args:
            file_path (Path): The path to the file to be parsed.
        """

        self.file_path = file_path
