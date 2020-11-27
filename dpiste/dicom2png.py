from pydicom import dcmread
from matplotlib import pyplot

def dicom2png(infile, outfile):
  ds = dcmread(infile)
  pixels = ds.pixel_array
  pyplot.imsave(outfile, pixels, cmap=pyplot.cm.bone)
  print(f"file {outfile} written")


dicom2png("/tmp/pynetdicom/1.3.6.1.4.1.9590.100.1.2.12392078612698738504735382232322772600", "/tmp/pynetdicom/1.3.6.1.4.1.9590.100.1.2.12392078612698738504735382232322772600.png")
