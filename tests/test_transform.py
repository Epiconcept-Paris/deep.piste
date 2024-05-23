import os
import unittest

from dpiste import __main__
from dpiste import utils
from tests.file_operations import FileOperations


class TransformCliTest(unittest.TestCase):
    """Tests for CLI subcommand 'transform'"""

    @classmethod
    def setUpClass(cls):
        """this method is called once before running all tests"""
        super(TransformCliTest, cls).setUpClass()
        FileOperations.init_test_dirs()
        os.environ['DP_HOME'] = FileOperations.dp_home()

    def tearDown(self):
        """this method is called after each test"""
        utils.cleandir(FileOperations.input_dir())
        utils.cleandir(TestFileOperations.output_dir())

    def test_dicom_deid(self):
        """
        nominal scenario for deidentifying a folder of mammograms to 
        png files and meta.csv
        """
        org_root = '150859203650428010901'
        __main__.main(
            [
                'transform',
                'dicom-deid',
                '-i', FileOperations.sample_mammograms(),
                '-o', FileOperations.output_dir(),
                '-r', org_root
            ]
        )

        output_files = os.listdir(FileOperations.output_dir())
        self.assertEqual(len(output_files), 2)
        self.assertTrue('meta.csv' in output_files)
        remaining_files = [f for f in output_files if f != 'meta.csv']
        if len(remaining_files) > 1:
            self.fail("Too many files in output directory")
        img_file = remaining_files[0]
        self.assertTrue(img_file.startswith(org_root))
        self.assertTrue(img_file.endswith('.png'))
