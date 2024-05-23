"""
Module for handling file-related operations in a unit testing context.
"""
import os


class FileOperations:
    """
    A utility class for locating files and folders within the filesystem
    and generating test directories.

    This class provides methods to retrieve paths for translators' root folder and referential file.

    Example:
        import os

        FileOperations.test_root()

    """
    CURRENT_FILE_PATH = os.path.abspath(__file__)
    TEST_ROOT_PATH = os.path.dirname(CURRENT_FILE_PATH)

    @classmethod
    def test_root(cls) -> str:
        return cls.TEST_ROOT_PATH

    @classmethod
    def test_assets_dir(cls) -> str:
        return os.path.join(cls.test_root(), 'assets')

    @classmethod
    def dp_home(cls) -> str:
        return os.path.join(cls.test_assets_dir(), 'dp_home')

    @classmethod
    def input_dir(cls) -> str:
        return os.path.join(cls.dp_home(), 'data', 'input')

    @classmethod
    def output_dir(cls) -> str:
        return os.path.join(cls.dp_home(), 'data', 'output')

    @classmethod
    def sample_mammograms(cls) -> str:
        return os.path.join(cls.test_assets_dir(), 'sample_mammograms')

    @classmethod
    def init_test_dirs(cls) -> str:
        """Initialize test directories.

        Create directories that does not exist in the tree structure.
        """
        if not os.path.isdir(cls.test_assets_dir()):
            os.mkdir(cls.test_assets_dir())

        if not os.path.isdir(cls.dp_home()):
            os.mkdir(cls.dp_home())

        if not os.path.isdir(cls.input_dir()):
            os.makedirs(cls.input_dir())

        if not os.path.isdir(cls.output_dir()):
            os.makedirs(cls.output_dir())
