import copy
import niftiutils.helper_fxns as hf
import niftiutils.transforms as tr
import niftiutils.registration as regs
import itertools
import nibabel as nib
import numpy as np
import os
import shutil
import time

###########################
### File I/O
###########################

def check_dcm_paths(patient_id, patient_df):
	blmri_path = "Z:\\Isa\\blmri\\"+str(patient_df.loc[patient_id, "BL-MRI"])
	fumri_path = "Z:\\Isa\\fumri\\"+str(patient_df.loc[patient_id, "FU1/2-MRI"])
	if not os.path.exists(blmri_path+"\\T1_AP"):
		print(blmri_path+"\\T1_AP")
	if not os.path.exists(blmri_path+"\\T1_BL"):
		print(blmri_path+"\\T1_AP")
	if not os.path.exists(fumri_path+"\\T1_AP"):
		print(fumri_path+"\\T1_AP")
	if not os.path.exists(fumri_path+"\\T1_BL"):
		print(fumri_path+"\\T1_AP")

def is_segmented(patient_id):
	if os.path.exists(base_dir + "BL-segs"):
		print(patient_id)

def set_paths(patient_id, patient_df, dcm_paths, nii_paths, mask_paths):
	img_base_dir = "Z:\\Isa\\spect\\"

	if not os.path.exists("Z:\\Isa\\"+str(patient_id)):
		os.makedirs("Z:\\Isa\\"+str(patient_id))
		
	base_dir = "Z:\\Isa\\"+str(patient_id)+"\\"

	dcm_paths[patient_id] = {"ct": img_base_dir+str(patient_df.loc[patient_id, "SPECT"])+"\\CT",
			"fused": img_base_dir+str(patient_df.loc[patient_id, "SPECT"])+"\\Fused",
			"spect": img_base_dir+str(patient_df.loc[patient_id, "SPECT"])+"\\SPECT",
			"fumri-art": "Z:\\Isa\\fumri\\"+str(patient_df.loc[patient_id, "FU1/2-MRI"])+"\\T1_AP",
			"fumri-pre": "Z:\\Isa\\fumri\\"+str(patient_df.loc[patient_id, "FU1/2-MRI"])+"\\T1_BL",
			"blmri-art": "Z:\\Isa\\blmri\\"+str(patient_df.loc[patient_id, "BL-MRI"])+"\\T1_AP",
			"blmri-pre": "Z:\\Isa\\blmri\\"+str(patient_df.loc[patient_id, "BL-MRI"])+"\\T1_BL"}

	nii_paths[patient_id] = {'base': base_dir}
	img_types = ['blmri-art', 'blmri-pre', 'fumri-art', 'fumri-pre', 'ct', 'spect', 'fused', 'fused-ch1', 'fused-ch2', 'fused-ch3']
	for img_type in img_types:
		nii_paths[patient_id][img_type] = base_dir + img_type + ".nii"
		nii_paths[patient_id][img_type+"-reg"] = base_dir + img_type + "-reg.nii"

	mask_paths[patient_id] = {"liver-bl": base_dir + "BL-segs\\BL-Liver.ids",
				"tumor-bl": base_dir + "BL-segs\\BL-Tumor.ids",
				"liver-fu": base_dir + "FU-segs\\FU-Liver.ids",
				"tumor-fu": base_dir + "FU-segs\\FU-Tumor.ids",
				"necrosis-bl": base_dir + "BL-segs\\necrosis.ids",
				"viable-tumor-bl": base_dir + "BL-segs\\viable_tumor.ids",
				"necrosis-fu": base_dir + "FU-segs\\necrosis.ids",
				"viable-tumor-fu": base_dir + "FU-segs\\viable_tumor.ids",
				"necrosis-fu-scaled": base_dir + "FU-segs\\necrosis-scaled.ids",
				"viable-tumor-fu-scaled": base_dir + "FU-segs\\viable_tumor-scaled.ids"}

	if not os.path.exists(dcm_paths[patient_id]["spect"]):
		spect_path = img_base_dir+str(patient_df.loc[patient_id, "SPECT"])
		for fn in os.listdir(spect_path):
			if 'recon - ac' in fn:
				dcm_paths[patient_id]['spect'] = spect_path + "\\" + fn
				break
				
	if not os.path.exists(dcm_paths[patient_id]["ct"]):
		spect_path = img_base_dir+str(patient_df.loc[patient_id, "SPECT"])
		for fn in os.listdir(spect_path):
			if 'y90 sirs' in fn and 'ac' not in fn:
				dcm_paths[patient_id]['ct'] = spect_path + "\\" + fn
				break
				
	if not os.path.exists(dcm_paths[patient_id]["fused"]):
		spect_path = img_base_dir+str(patient_df.loc[patient_id, "SPECT"])
		for fn in os.listdir(spect_path):
			if 'fused tran' in fn:
				dcm_paths[patient_id]['fused'] = spect_path + "\\" + fn
				break

def save_all_niis(patient_id, dcm_paths, nii_paths, overwrite=True):
	if (not overwrite) and os.path.exists(nii_p['spect']):
		return

	nii_p = nii_paths[patient_id]

	spect_img = hf.get_spect_series(dcm_paths[patient_id]['spect'])
	hf.save_nii(spect_img, nii_p['spect'])

	fused_img = hf.get_spect_series(dcm_paths[patient_id]['fused'])
	hf.save_nii(fused_img[:,:,:,0], nii_p['fused-ch1'])
	hf.save_nii(fused_img[:,:,:,1], nii_p['fused-ch2'])
	hf.save_nii(fused_img[:,:,:,2], nii_p['fused-ch3'])
	hf.save_nii((fused_img[:,:,:,0] + fused_img[:,:,:,1] + fused_img[:,:,:,2])/3, nii_p['fused'])

	ct_img, dims = hf.dcm_load(dcm_paths[patient_id]['ct'])
	hf.save_nii(ct_img, nii_p['ct'], dims)

	blmri_art, dims = hf.dcm_load(dcm_paths[patient_id]['blmri-art'])
	hf.save_nii(blmri_art, nii_p['blmri-art'], dims)

	blmri_pre, dims = hf.dcm_load(dcm_paths[patient_id]['blmri-pre'])
	hf.save_nii(blmri_pre, nii_p['blmri-pre'], dims)

	fumri_art, dims = hf.dcm_load(dcm_paths[patient_id]['fumri-art'])
	hf.save_nii(fumri_art, nii_p['fumri-art'], dims)

	fumri_pre, dims = hf.dcm_load(dcm_paths[patient_id]['fumri-pre'])
	hf.save_nii(fumri_pre, nii_p['fumri-pre'], dims)


###########################
### Registration
###########################

def reg_all_niis(patient_id, nii_paths, verbose=True):
	""""""
	t = time.time()

	if verbose:
		print("\n"+str(patient_id))
	pat_nii_paths = nii_paths[patient_id]
	base_dir = pat_nii_paths['base']
	temp_file = "Z:\\temp.nii"
	
	blmri_art, _ = hf.ni_load(pat_nii_paths["blmri-art"])
	
	if verbose:
		print("Registering BL MRI (pre) to BL MRI (arterial)")
	reg_nii("blmri-art", "blmri-pre", pat_nii_paths, fixed_img=blmri_art)
	
	if verbose:
		print("Registering FU MRI to BL MRI (arterial)")
	_, blfu_transform_path = reg_nii("blmri-art", "fumri-art", pat_nii_paths, fixed_img=blmri_art)
	
	if verbose:
		print("Registering FU MRI (pre) to FU MRI (arterial)")
	if not reg_nii("fumri-art", "fumri-pre", pat_nii_paths, out_img_path=temp_file, overwrite=True) is None:
		if verbose:
			print("Transforming FU MRI (pre) to BL MRI coords")
		transform_nii(temp_file, [blfu_transform_path], pat_nii_paths, out_img_path=base_dir+"fumri-pre-reg.nii")
			
	if verbose:
		print("Registering CT to BL MRI")
	_, blct_transform_path = reg_nii("blmri-art", "ct", pat_nii_paths, fixed_img=blmri_art)

	if verbose:
		print("Registering Fused to CT")
	_, ctfused_transform_path = reg_nii("ct", "fused-ch1", pat_nii_paths, out_img_path=temp_file, overwrite=True)
	if verbose:
		print("Transforming Fused to BL MRI coords")
	transform_nii(temp_file, [blct_transform_path], pat_nii_paths, out_img_path=base_dir+"fused-reg.nii")

	if verbose:
		print("Registering SPECT to Fused")
	reg_nii("fused-ch1", "spect", pat_nii_paths, out_img_path=temp_file, overwrite=True)
	if verbose:
		print("Transforming SPECT to BL MRI coords")
	transform_nii(temp_file, [ctfused_transform_path], pat_nii_paths, out_img_path=temp_file, overwrite=True)
	transform_nii(temp_file, [blct_transform_path], pat_nii_paths, out_img_path=base_dir+"spect-reg.nii")

	os.remove(temp_file)
	print(time.time() - t)

def reg_nii(fixed_img_type, moving_img_type, pat_nii_paths, 
			 out_img_path="default", out_transform_path="default", overwrite=False):
	"""Registers images. 
	"""
	
	if out_transform_path == "default":
		out_transform_path = pat_nii_paths['base'] + moving_img_type+'_'+fixed_img_type+'_xform.txt'
	
	out_img_path, out_transform_path = regs.reg_bis(pat_nii_paths[fixed_img_type],
				pat_nii_paths[moving_img_type], out_transform_path, out_img_path, overwrite=overwrite)
	
	return out_img_path, out_transform_path

def reg_nii_sitk(fixed_img_type, moving_img_type, pat_nii_paths, 
			 moving_img=None, out_img_path=None, out_transform_path=None, overwrite=False, verbose=False, reg_type='demons'):
	"""Registers images. 
	"""
	import importlib
	importlib.reload(hf)

	if out_img_path is None:
		out_img_path = hf.add_to_filename(pat_nii_paths[moving_img_type], "-reg")
		
	if out_transform_path is None:
		out_transform_path = pat_nii_paths['base'] + moving_img_type+'_'+fixed_img_type+'_transform.hdf5'
		
	temp_path = hf.add_to_filename(pat_nii_paths[moving_img_type],"-scaled")
		
	if (not overwrite) and os.path.exists(out_img_path):
		print(out_img_path, "already exists. Skipping registration.")
		return None
	
	fixed_img, voxdims = hf.ni_load(pat_nii_paths[fixed_img_type])
	if moving_img is None:
		moving_img, _ = hf.ni_load(pat_nii_paths[moving_img_type])
		
	if moving_img.shape == fixed_img.shape:
		print(fixed_img_type, "and", moving_img_type, "have the same shape. Skipping registration.")
		return None
	
	moving_img_scaled, _ = tr.rescale(moving_img, fixed_img.shape)
	hf.save_nii(moving_img_scaled, temp_path, dims=voxdims)
	
	regs.reg_img(pat_nii_paths[fixed_img_type], temp_path, out_transform_path, out_img_path, verbose=verbose, reg_type=reg_type)
	
	os.remove(temp_path)
	
	return out_img_path, out_transform_path

def transform_nii(in_img_path, transform_paths, fixed_img_paths, out_img_path=None, overwrite=True):
	"""Transforms image based on previous transform and scaling to target_dims."""
	
	if out_img_path is None:
		out_img_path = hf.add_to_filename(in_img_path, "-reg")
	if (not overwrite) and os.path.exists(out_img_path):
		print(out_img_path, "already exists. Skipping transform.")
		return False
		
	temp_path = hf.add_to_filename(in_img_path, "-temp")
		
	shutil.copyfile(in_img_path, temp_path)
	
	for index, transform_path in enumerate(transform_paths):
		hf.transform(temp_path, transform_path, fixed_img_paths[index], temp_path)
	
	if temp_path != out_img_path:
		if os.path.exists(out_img_path):
			os.remove(out_img_path)
		os.rename(temp_path, out_img_path)
	
	return out_img_path

def transform_nii_sitk(in_img_path, transform_paths, pat_nii_paths, target_imgs=None, out_img_path=None, overwrite=True):
	"""Transforms image based on previous transform and scaling to target_dims."""
	
	if out_img_path is None:
		out_img_path = hf.add_to_filename(in_img_path, "-reg")
	if (not overwrite) and os.path.exists(out_img_path):
		print(out_img_path, "already exists. Skipping transform.")
		return False
		
	temp_path = hf.add_to_filename(in_img_path, "-temp")
		
	shutil.copyfile(in_img_path, temp_path)
	
	for index, transform_path in enumerate(transform_paths):
		if target_imgs is None:
			target_img_type = transform_path[transform_path.find('_')+1:transform_path.rfind('_')]
			target_img, _ = hf.ni_load(pat_nii_paths[target_img_type])
		else:
			target_img = target_imgs[index]

		hf.transform(temp_path, transform_path)
		
		hf.save_nii(hf.rescale(hf.ni_load(temp_path)[0], target_img.shape)[0], temp_path)
	
	if temp_path != out_img_path:
		if os.path.exists(out_img_path):
			os.remove(out_img_path)
		os.rename(temp_path, out_img_path)
	
	return True