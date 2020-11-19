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

#def download_dicom()

#org.dcm4che3.tool.getscu.GetSCU.main(Array("-c", "DCM4CHEE@localhost:11112",  "-m", "StudyInstanceUID=1.3.6.1.4.1.9590.100.1.2.409914573611683067919391940392991059926", "--directory", "/tmp"))

from pydicom.dataset import Dataset
from pynetdicom import (
	AE, build_context, build_role, StoragePresentationContexts,
	PYNETDICOM_IMPLEMENTATION_UID,
	PYNETDICOM_IMPLEMENTATION_VERSION
)
from pynetdicom.pdu_primitives import SCP_SCU_RoleSelectionNegotiation
from pynetdicom.sop_class import (
	PatientRootQueryRetrieveInformationModelGet, PatientRootQueryRetrieveInformationModelMove,
	CTImageStorage, DigitalMammographyXRayImagePresentationStorage
)

ae = AE(ae_title='TITLE_SCU')

ae.add_requested_context(DigitalMammographyXRayImagePresentationStorage)
ae.add_requested_context(PatientRootQueryRetrieveInformationModelGet)
ext_neg = []

role = SCP_SCU_RoleSelectionNegotiation()
#role = build_role(DigitalMammographyXRayImagePresentationStorage, scp_role=True)   # I tried but same error occurred
role = build_role(CTImageStorage, scp_role=True)
role.sop_class_uid = DigitalMammographyXRayImagePresentationStorage
role.scu_role = False # original False
role.scp_role = True # original True

ae.add_supported_context(DigitalMammographyXRayImagePresentationStorage)
ext_neg.append(role)

def on_c_store(ds, context, info):
	print("ON_C_STORE")
	meta = Dataset()
	meta.MediaStorageSOPClassUID = ds.SOPClassUID
	meta.MediaStorageSOPInstanceUID = ds.SOPInstanceUID
	meta.ImplementationClassUID = PYNETDICOM_IMPLEMENTATION_UID
	meta.ImplementationVersionName = PYNETDICOM_IMPLEMENTATION_VERSION
	meta.TransferSyntaxUID = context.transfer_syntax
	ds.file_meta = meta
	ds.is_little_endian = context.transfer_syntax.is_little_endian
	ds.is_implicit_VR = context.transfer_syntax.is_implicit_VR
	ds.save_as(ds.SOPInstanceUID, write_like_original=False)
	return 0x0000


ae.on_c_store = on_c_store

ds = Dataset()
ds.QueryRetrieveLevel = 'SERIES'
ds.PatientID = "P_00246_RIGHT_MLO.dcm"
ds.StudyInstanceUID = "1.3.6.1.4.1.9590.100.1.2.378115250312337004138147429152188255726"
ds.SeriesInstanceUID = "1.3.6.1.4.1.9590.100.1.2.25530538411839768118282182472795553760"
assoc = ae.associate('localhost', 11112, ae_title=b'DCM4CHEE', ext_neg=ext_neg)

if assoc.is_established:
	responses = assoc.send_c_get(ds, query_model=PatientRootQueryRetrieveInformationModelGet)
	for (status, identifier) in responses:
		if status:
			print('C-GET query status: 0x{0:04x}'.format(status.Status))
			if status.Status in (0xFF00, 0xFF01):
				print(identifier)
		else:
			print('Connection timed out, was aborted or received invalid response')
	assoc.release()
else:
	print('Association rejected, aborted or never connected')
#for (f, ds) in read_dicom(infiles):
#  print(f"file {f} containes {len(str(ds))} lines")
