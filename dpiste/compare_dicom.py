from pydicom import dcmread
from pydicom.data import get_testdata_file
from matplotlib import pyplot
from difflib import Differ

infile = get_testdata_file("MR_small.dcm")

infiles = [
    "/home/fod/datapub/cbis-ddsm/Calc-Test_P_00246_RIGHT_MLO_1/1.3.6.1.4.1.9590.100.1.2.12392078612698738504735382232322772600"
   ,"/home/fod/datapub/cbis-ddsm/CBIS-DDSM/Calc-Test_P_00246_RIGHT_MLO/08-29-2017-DDSM-55726/1.000000-full mammogram images-53760/1-1.dcm"
 ]


def write_dicom(infiles):
  i = 0
  for infile in infiles:
    outfile = f"/home/fod/deleteme/dicom_{i}.png"
    ds = dcmread(infile)
    pixels = ds.pixel_array
    pyplot.imsave(outfile, pixels, cmap=pyplot.cm.bone)
    print(f"file {outfile} written")
    i = i +1

def read_dicom(infiles):
  for infile in infiles:
    ds = dcmread(infile)
    yield((infile, ds) )

def compare_dicom(infiles):
  lines = list([str(df).splitlines(keepends = True) for (f, df) in read_dicom(infiles)])
  difs = Differ().compare(lines[0], lines[1])
  return filter(lambda l: l[0:2] != "  ", difs)


