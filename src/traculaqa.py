import os
import sys
import shutil
import os.path
import math
from stat import S_IXUSR, ST_MODE
from string import Template
import nibabel as nib
import numpy as np
from numpy.ma import masked_array
from mayavi import mlab
from scipy import ndimage
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

mlab.options.offscreen = True

CPTS_LIST = [
    'fmajor_PP_avg33_mni_bbr_cpts_7.txt',
    'fminor_PP_avg33_mni_bbr_cpts_5.txt',
    'lh.atr_PP_avg33_mni_bbr_cpts_5.txt',
    'lh.cab_PP_avg33_mni_bbr_cpts_4.txt',
    'lh.ccg_PP_avg33_mni_bbr_cpts_5.txt',
    'lh.cst_AS_avg33_mni_bbr_cpts_6.txt',
    'lh.ilf_AS_avg33_mni_bbr_cpts_5.txt',
    'lh.slfp_PP_avg33_mni_bbr_cpts_5.txt',
    'lh.slft_PP_avg33_mni_bbr_cpts_5.txt',
    'lh.unc_AS_avg33_mni_bbr_cpts_5.txt',
    'rh.atr_PP_avg33_mni_bbr_cpts_5.txt',
    'rh.cab_PP_avg33_mni_bbr_cpts_4.txt',
    'rh.ccg_PP_avg33_mni_bbr_cpts_5.txt',
    'rh.cst_AS_avg33_mni_bbr_cpts_6.txt',
    'rh.ilf_AS_avg33_mni_bbr_cpts_5.txt',
    'rh.slfp_PP_avg33_mni_bbr_cpts_5.txt',
    'rh.slft_PP_avg33_mni_bbr_cpts_5.txt',
    'rh.unc_AS_avg33_mni_bbr_cpts_5.txt']

DIR2TRACT = {
    'fmajor_PP_avg33_mni_bbr': 'fmajor',
    'fminor_PP_avg33_mni_bbr': 'fminor',
    'lh.atr_PP_avg33_mni_bbr': 'lh_atr',
    'lh.cab_PP_avg33_mni_bbr': 'lh_cab',
    'lh.ccg_PP_avg33_mni_bbr': 'lh_ccg',
    'lh.cst_AS_avg33_mni_bbr': 'lh_cst',
    'lh.ilf_AS_avg33_mni_bbr': 'lh_ilf',
    'lh.slfp_PP_avg33_mni_bbr': 'lh_slfp',
    'lh.slft_PP_avg33_mni_bbr': 'lh_slft',
    'lh.unc_AS_avg33_mni_bbr': 'lh_unc',
    'rh.atr_PP_avg33_mni_bbr': 'rh_atr',
    'rh.cab_PP_avg33_mni_bbr': 'rh_cab',
    'rh.ccg_PP_avg33_mni_bbr': 'rh_ccg',
    'rh.cst_AS_avg33_mni_bbr': 'rh_cst',
    'rh.ilf_AS_avg33_mni_bbr': 'rh_ilf',
    'rh.slfp_PP_avg33_mni_bbr': 'rh_slfp',
    'rh.slft_PP_avg33_mni_bbr': 'rh_slft',
    'rh.unc_AS_avg33_mni_bbr': 'rh_unc'}

DMRIRC_TEMPLATE = Template("""# TRACULA dmrirc created by Spider_TRACULA
setenv SUBJECTS_DIR ${fs_dir}
set dtroot = ${trac_dir}
set subjlist = (${fs_subj})
set dcmroot = ${dif_dir}
set dcmlist = (${dif_nii})
set bvecfile = ${dif_bvecs}
set bvalfile = ${dif_bvals}
set nb0 = 1
set dob0 = 0
set doeddy = 1
set dorotbvecs = 1
set thrbet = 0.2
set doregflt = 0
set doregbbr = 1
set doregmni = 1
set usemaskanat = 1
set pathlist = (lh.cst_AS rh.cst_AS lh.unc_AS rh.unc_AS lh.ilf_AS rh.ilf_AS \
fmajor_PP fminor_PP
lh.atr_PP rh.atr_PP lh.ccg_PP rh.ccg_PP lh.cab_PP rh.cab_PP \
lh.slfp_PP rh.slfp_PP lh.slft_PP rh.slft_PP)

set ncpts = (6 6 5 5 5 5 7 5 5 5 5 5 4 4 5 5 5 5)
set trainfile = $$FREESURFER_HOME/trctrain/trainlist.txt
set nstick = 2
set nburnin = 200
set nsample = 7500
set nkeep = 5
set reinit = 1
""")

TRACULA_TEMPLATE = Template("""#!/bin/bash
# TRACULA script created by Spider_TRACULA_v1
export FSL_DIR=${fsl_dir}
export FSLDIR=${fsl_dir}
source $$FSLDIR/etc/fslconf/fsl.sh
export PATH=$${FSLDIR}/bin:$${PATH}
export FREESURFER_HOME=${fs_home}
source $$FREESURFER_HOME/SetUpFreeSurfer.sh

# Run pre-processing
trac-all -prep -c ${dmrirc_path}

# Run bedpost
trac-all -bedp -c ${dmrirc_path}

# Add control points edits if any
cp ${edits_dir}/*cpts*.txt ${trac_path}/dlabel/diff/

# Make paths
trac-all -path -c ${dmrirc_path}
mri_convert ${merged_mgz} ${merged_niigz}
""")


TRACT_THRESHOLD = 0.1
T_ALPHA = 1.0
TRACT_CMAP = plt.get_cmap('autumn')
ISO_CMAP_NAME = 'autumn'
FA_CMAP = plt.get_cmap('gray')
SAVE_DPI = 300

TRACT_ARRAY = [
    ('fx', (0.8, 0.4, 0.4), 0, 'Corpus Callosum Forceps Major/Minor', 'fmajor', 'fminor'),
    ('xh.atr', (1.0, 1.0, 0.4), 0, 'Left/Right Anterior Thalamic Radiation', 'lh_atr', 'rh_atr'),
    ('xh.cab', (0.6, 0.8, 0.0), 2, 'Left/Right Cingulum - Angular Bundle', 'lh_cab', 'rh_cab'),
    ('xh.ccg', (0.0, 0.6, 0.6), 2, 'Left/Right Cingulum - Cingulate Gyrus', 'lh_ccg', 'rh_ccg'),
    ('xh.cst', (0.8, 0.6, 1.0), 1, 'Left/Right Corticospinal Tract', 'lh_cst', 'rh_cst'),
    ('xh.ilf', (1.0, 0.6, 0.2), 2, 'Left/Right Inferior Longitudinal Fasc.', 'lh_ilf', 'rh_ilf'),
    ('xh.slfp', (0.8, 0.8, 0.8), 2, 'Left/Right Sup Lngit. Fasc. - Parietal', 'lh_slfp', 'rh_slfp'),
    ('xh.slft', (0.6, 1.0, 1.0), 2, 'Left/Right Sup Lngit. Fasc. - Temporal', 'lh_slft', 'rh_slft'),
    ('xh.unc', (0.4, 0.6, 1.0), 2, 'Left/Right Uncinate Fasciculus', 'lh_unc', 'rh_unc')]

TRACT_DICT = {
    0 : ('fmajor', (0.8, 0.4, 0.4), 0, 'Corpus Callosum Forceps Major'),
    1 : ('fminor', (0.8, 0.4, 0.4), 0, 'Corpus Callosum Forceps Minor'),
    2 : ('lh.atr', (1.0, 1.0, 0.4), 0, 'Left Anterior Thalamic Radiation'),
    3 : ('lh.cab', (0.6, 0.8, 0.0), 2, 'Left Cingulum - Angular Bundle'),
    4 : ('lh.ccg', (0.0, 0.6, 0.6), 2, 'Left Cingulum - Cingulate Gyrus'),
    5 : ('lh.cst', (0.8, 0.6, 1.0), 1, 'Left Corticospinal Tract'),
    6 : ('lh.ilf', (1.0, 0.6, 0.2), 2, 'Left Inferior Longitudinal Fasciculus'),
    7 : ('lh.slfp', (0.8, 0.8, 0.8), 2, 'Left Superior Longitudinal Fasciculus - Parietal'),
    8 : ('lh.slft', (0.6, 1.0, 1.0), 2, 'Left Superior Longitudinal Fasciculus - Temporal'),
    9 : ('lh.unc', (0.4, 0.6, 1.0), 2, 'Left Uncinate Fasciculus'),
    10 : ('rh.atr', (1.0, 1.0, 0.4), 0, 'Right Anterior Thalamic Radiation'),
    11 : ('rh.cab', (0.6, 0.8, 0.0), 2, 'Right Cingulum - Angular Bundle'),
    12 : ('rh.ccg', (0.0, 0.6, 0.6), 2, 'Right Cingulum - Cingulate Gyrus'),
    13 : ('rh.cst', (0.8, 0.6, 1.0), 1, 'Right Corticospinal Tract'),
    14 : ('rh.ilf', (1.0, 0.6, 0.2), 2, 'Right Inferior Longitudinal Fasciculus'),
    15 : ('rh.slfp', (0.8, 0.8, 0.8), 2, 'Right Superior Longitudinal Fasciculus - Parietal'),
    16 : ('rh.slft', (0.6, 1.0, 1.0), 2, 'Right Superior Longitudinal Fasciculus - Temporal'),
    17 : ('rh.unc', (0.4, 0.6, 1.0), 2, 'Right Uncinate Fasciculus')}


def square_slice(slice_data):
    (xdim, ydim) = slice_data.shape

    if xdim < ydim:
        ddim = ydim - xdim
        top = np.zeros(
            (int(math.ceil(ddim / 2.0)), ydim), dtype=slice_data.dtype)
        bottom = np.zeros(
            (int(math.floor(ddim / 2.0)), ydim), dtype=slice_data.dtype)
        slice_data = np.concatenate((top, slice_data, bottom))
    elif xdim > ydim:
        ddim = xdim - ydim
        left = np.zeros(
            (xdim, int(math.ceil(ddim / 2.0))), dtype=slice_data.dtype)
        right = np.zeros(
            (xdim, int(math.floor(ddim / 2.0))), dtype=slice_data.dtype)
        slice_data = np.concatenate((left, slice_data, right))
    else:
        # Already squared
        pass

    return slice_data


def square_rgba(rgba_data):
    (xdim, ydim) = rgba_data.shape[0:2]

    if xdim < ydim:
        ddim = ydim - xdim
        top = np.zeros(
            (int(math.ceil(ddim / 2.0)), ydim, 4), dtype=rgba_data.dtype)
        bottom = np.zeros(
            (int(math.floor(ddim / 2.0)), ydim, 4), dtype=rgba_data.dtype)
        rgba_data = np.concatenate((top, rgba_data, bottom))
    elif xdim > ydim:
        ddim = xdim - ydim
        left = np.zeros(
            xdim, (int(math.ceil(ddim / 2.0)), 4), dtype=rgba_data.dtype)
        right = np.zeros(
            xdim, (int(math.floor(ddim / 2.0)), 4), dtype=rgba_data.dtype)
        rgba_data = np.concatenate((left, rgba_data, right))
    else:
        # Already squared
        pass

    return rgba_data


def square_rgb(rgb_data):
    (xdim, ydim) = rgb_data.shape[0:2]

    if xdim < ydim:
        ddim = ydim - xdim
        top = np.zeros(
            (int(math.ceil(ddim / 2.0)), ydim, 3), dtype=rgb_data.dtype)
        bottom = np.zeros(
            (int(math.floor(ddim / 2.0)), ydim, 3), dtype=rgb_data.dtype)
        rgb_data = np.concatenate((top, rgb_data, bottom))
    elif xdim > ydim:
        ddim = xdim - ydim
        left = np.zeros(xdim, (math.ceil(ddim / 2.0), 3), dtype=rgb_data.dtype)
        right = np.zeros(
            xdim, (math.floor(ddim / 2.0), 3), dtype=rgb_data.dtype)
        rgb_data = np.concatenate((left, rgb_data, right))
    else:
        # Already squared
        pass

    return rgb_data


class TRACULAQA:
    def __init__(self, fs_path, fsl_path):
        self.fs_path = fs_path
        self.fsl_path = fsl_path

    def makeqa(self,
               fs_data,
               fs_label,
               fs_subj,
               dti_nifti,
               bval_txt,
               bvec_txt,
               out_dir,
               cpts_txt='',
               proj='UNKNOWN', sess='UNKNOWN', version='UNKNOWN'):

        # Figure out the destination based on format of unzipped data
        if os.path.exists(os.path.join(fs_data, 'DATA', fs_label)):
            src = os.path.join(fs_data, 'DATA', fs_label)
        elif os.path.exists(os.path.join(fs_data, 'DATA', fs_subj)):
            src = os.path.exists(os.path.join(fs_data, 'DATA', fs_subj))
        elif os.path.exists(os.path.join(fs_data, 'DATA', 'mri')):
            src = os.path.join(fs_data, 'DATA')
        else:
            print('ERROR:failed to download FreeSurfer data.')
            # TODO: throw an error
            return

        # Move it so FS dir name is same as session
        dest = os.path.join(fs_data, fs_subj)
        print('Moving ' + src + ' to ' + dest)
        shutil.move(src, dest)

        trac_dir = os.path.join(out_dir, 'TRACULA')
        if not os.path.exists(trac_dir):
            os.mkdir(trac_dir)

        edits_dir = os.path.join(out_dir, 'EDITS')
        if not os.path.exists(edits_dir):
            os.mkdir(edits_dir)

        trac_path = os.path.join(trac_dir, fs_subj)
        stats_path = os.path.join(out_dir, 'TRACULA_' + fs_subj + '_stats.txt')
        pdf_path = os.path.join(out_dir, 'TRACULA_' + fs_subj + '_report.pdf')
        merged_mgz = os.path.join(
            trac_path, 'dpath', 'merged_avg33_mni_bbr.mgz')
        merged_niigz = merged_mgz[:-3] + 'nii.gz'
        dmrirc_path = os.path.join(
            out_dir, 'dmrirc_' + fs_subj + '.txt')
        trac_filepath = os.path.join(out_dir, 'trac_' + fs_subj + '.sh')
        mgh_bvals_path = os.path.join(out_dir, 'mgh_bvals.txt')
        mgh_bvecs_path = os.path.join(out_dir, 'mgh_bvecs.txt')
        fa_path = os.path.join(trac_path, 'dmri', 'dtifit_FA.nii.gz')
        motion_path = os.path.join(trac_path, 'dmri', 'dwi_motion.txt')

        # Handle any Edits

        # TODO:

        # Copy dti NIFTI
        shutil.copyfile(dti_nifti, os.path.join(out_dir, 'dti.nii.gz'))
        dti_nifti = os.path.join(out_dir, 'dti.nii.gz')

        # Write the transposed bvals and bvecs
        cmd = 'cols=`head -n 1 ' + bval_txt + ' | wc -w`;for (( i=1; i <= $cols; i++)); do awk \'{printf ("%s%s", tab, $\'$i\'); tab="  "} END {print ""}\' ' + bval_txt + ';done >> ' + mgh_bvals_path
        print(cmd)
        os.system(cmd)

        cmd = 'cols=`head -n 1 ' + bvec_txt + ' | wc -w`;for (( i=1; i <= $cols; i++)); do awk \'{printf ("%s%s", tab, $\'$i\'); tab="  "} END {print ""}\' ' + bvec_txt + ';done >> ' + mgh_bvecs_path
        print(cmd)
        os.system(cmd)

        # Remove extra volume from Philips DTI sequence
        cmd = 'tail -n 1 ' + mgh_bvecs_path + ' | grep \"0.000000  -0.000000  0.000000\"'
        cmd += ' && head -n -1 ' + mgh_bvecs_path + ' > ' + mgh_bvecs_path + '.tmp && mv ' + mgh_bvecs_path + '.tmp ' + mgh_bvecs_path
        cmd += ' && head -n -1 ' + mgh_bvals_path + ' > ' + mgh_bvals_path + '.tmp && mv ' + mgh_bvals_path + '.tmp ' + mgh_bvals_path
        cmd += ' && fslroi ' + dti_nifti + ' ' + dti_nifti + ' 0 33'
        print(cmd)
        os.system(cmd)

        # Write the TRACULA parameters file
        dmrirc_data = {
            'fs_dir': fs_data,
            'trac_dir': trac_dir,
            'fs_subj': fs_subj,
            'dif_dir': os.path.dirname(dti_nifti),
            'dif_nii': os.path.basename(dti_nifti),
            'dif_bvecs': mgh_bvecs_path,
            'dif_bvals': mgh_bvals_path
        }

        with open(dmrirc_path, 'w') as f:
            f.write(DMRIRC_TEMPLATE.substitute(dmrirc_data))

        # Write the TRACULA script
        trac_data = {
            'dmrirc_path': dmrirc_path,
            'fs_home': self.fs_path,
            'fsl_dir': self.fsl_path,
            'merged_mgz': merged_mgz,
            'merged_niigz': merged_niigz,
            'trac_path': trac_path,
            'edits_dir': edits_dir
        }

        with open(trac_filepath, 'w') as f:
            f.write(TRACULA_TEMPLATE.substitute(trac_data))

        # Run the TRACULA script
        os.chmod(trac_filepath, os.stat(trac_filepath)[ST_MODE] | S_IXUSR)
        os.system(trac_filepath)

        # stats
        trac_stats = self.parse_trac_stats(trac_dir, fs_subj)
        trac_stats.update(self.parse_dwi_motion(motion_path))
        self.write_stats(stats_path, trac_stats)

        # pdf
        self.make_pdf(fa_path, merged_niigz, pdf_path, trac_stats, proj, sess)

        # Zip each subdir
        os.chdir(os.path.join(trac_dir, fs_subj))
        for z in os.listdir('.'):
            if os.path.isdir(z):
                cmd = 'zip -qr ' + z + '.zip ' + z
                print(cmd)
                os.system(cmd)

    def show_tract_page0(self, ax, f_data, t_data, t_num):
        tract_data = t_data[:, :, :, t_num]
        index_of_max = np.unravel_index(
            np.argmax(tract_data), tract_data.shape)

        if TRACT_DICT[t_num][2] == 0:  # axial
            f_slice = np.flipud(np.transpose(f_data[:, :, index_of_max[2]]))
            t_slice = np.flipud(
                np.transpose(tract_data[:, :, index_of_max[2]]))
        elif TRACT_DICT[t_num][2] == 1:  # coronal
            f_slice = np.flipud(np.transpose(f_data[:, index_of_max[1], :]))
            t_slice = np.flipud(
                np.transpose(tract_data[:, index_of_max[1], :]))
        elif TRACT_DICT[t_num][2] == 2:  # sagittal
            f_slice = np.flipud(np.transpose(f_data[index_of_max[0], :, :]))
            t_slice = np.flipud(
                np.transpose(tract_data[index_of_max[0], :, :]))
        else:
            return None

        f_slice = square_slice(f_slice)
        t_slice = square_slice(t_slice)
        mt_slice = masked_array(t_slice, t_slice <= 0)

        ax.imshow(f_slice, cmap=FA_CMAP)
        ax.imshow(mt_slice, cmap=TRACT_CMAP, alpha=T_ALPHA)
        ax.set_title(TRACT_DICT[t_num][0], fontsize=10)
        ax.set_axis_off()

    def tracula_first_page(self, fig, f_data, t_data, s_data, proj, sess):
        mlab.figure(bgcolor=(0, 0, 0))
        t_count = t_data.shape[3]

        # Draw all the tracts on one figure, colored based on LUT
        for t_num in range(0, t_count):
            # Get this tract
            t_surf = np.flipud(t_data[:, :, :, t_num])

            # Calculate threshold
            t_min = t_surf.max() * TRACT_THRESHOLD

            # Apply threshold
            t_surf = masked_array(t_surf, t_surf <= t_min)

            # Smoothing Filter
            t_surf = ndimage.uniform_filter(t_surf, 2)

            # Draw it
            src = mlab.pipeline.scalar_field(t_surf)
            t_color = TRACT_DICT[t_num][1]
            mlab.pipeline.iso_surface(src, contours=[t_min, ], color=t_color)

        # from top
        mlab.view(0, 0)
        t_top = mlab.screenshot(mode='rgb')

        # from bottom
        mlab.view(0, -180)
        t_bottom = mlab.screenshot(mode='rgb')

        # from left
        mlab.view(0, -90)
        t_left = mlab.screenshot(mode='rgb')

        # from right
        mlab.view(0, 90)
        t_right = mlab.screenshot(mode='rgb')

        # from front
        mlab.view(90, 90)
        t_front = mlab.screenshot(mode='rgb')

        # from back
        mlab.view(-90, 90)
        t_back = mlab.screenshot(mode='rgb')

        mlab.close()

        # Now add the screenshots to our main figure
        ax = fig.add_subplot(4, 4, 1)
        ax.imshow(square_rgb(t_top))
        ax.set_title('Superior', fontsize=10)
        ax.set_axis_off()

        ax = fig.add_subplot(4, 4, 2)
        ax.imshow(square_rgb(t_bottom))
        ax.set_title('Inferior', fontsize=10)
        ax.set_axis_off()

        ax = fig.add_subplot(4, 4, 5)
        ax.imshow(square_rgb(t_left))
        ax.set_title('Left', fontsize=10)
        ax.set_axis_off()

        ax = fig.add_subplot(4, 4, 6)
        ax.imshow(square_rgb(t_right))
        ax.set_title('Right', fontsize=10)
        ax.set_axis_off()

        ax = fig.add_subplot(4, 4, 9)
        ax.imshow(square_rgb(t_front))
        ax.set_title('Anterior', fontsize=10)
        ax.set_axis_off()

        ax = fig.add_subplot(4, 4, 10)
        ax.imshow(square_rgb(t_back))
        ax.set_title('Posterior', fontsize=10)
        ax.set_axis_off()

        t_count = t_data.shape[3]
        nrows = 6
        ncols = 6
        ax = None
        for t_num in range(0, t_count):
            iplot = (int(t_num / 3) * 6) + (t_num % 3) + 4
            ax = fig.add_subplot(nrows, ncols, iplot)
            self.show_tract_page0(ax, f_data, t_data, t_num)

        motion_text = 'Motion: '
        motion_text += '   AvgTrans=' + str(s_data['tracula_motion_avgtrans'])
        motion_text += '   AvgRot=' + str(s_data['tracula_motion_avgrot'])
        motion_text += '   BadSlices=' + str(s_data['tracula_motion_pctbadslices']) + '%'
        motion_text += '   AvgDropScore=' + str(s_data['tracula_motion_avgdropscore'])
        ax.annotate(motion_text,
                    xy=(0, 0),
                    xytext=(40, 40),
                    textcoords='figure pixels', fontsize=10)

        self.show_footer()

        fig.suptitle(
            'TRACULA - Summary of Results\nProject: ' + proj + '  Session:' + sess, fontsize=16)

        columns = ('Tract Name', 'FA')
        colors = [row[1] for row in TRACT_ARRAY]
        rows = [row[0] for row in TRACT_ARRAY]
        cell_text = [[t[3], ''] for t in TRACT_ARRAY]

        # Get the FA values from s_data
        for i, t in enumerate(TRACT_ARRAY):
            tractL = t[4]
            tractR = t[5]
            faL = s_data['tracula_' + tractL + '_fa_avg_weight']
            faR = s_data['tracula_' + tractR + '_fa_avg_weight']
            faL = "{0:.2f}".format(float(faL))
            faR = "{0:.2f}".format(float(faR))
            cell_text[i][1] = faL + ' / ' + faR

        ax = fig.add_subplot(4, 2, 7, frame_on=False)
        ax.xaxis.set_visible(False)
        ax.yaxis.set_visible(False)
        the_table = ax.table(cellText=cell_text,
                             rowLabels=rows,
                             rowColours=colors,
                             colLabels=columns,
                             colWidths=[0.8, 0.2],
                             loc='center',
                             cellLoc='left')

        the_table.auto_set_font_size(False)
        the_table.set_fontsize(6)
        ax.text(0.5, -0.07, '*FA is weighted mean in Tract', horizontalalignment='center', fontsize=6)
        # the_table.scale(2, 2)
        # plt.tight_layout(pad=0.1, w_pad=0.1, h_pad=0.1)
        return

    def show_footer(self):
        plt.figtext(
            0.02, 0.02,
            'http://xnat.vanderbilt.edu, ' + os.path.basename(sys.argv[0]),
            horizontalalignment='left', fontsize=8)
        plt.figtext(
            0.98, 0.02,
            'brian.d.boyd@vanderbilt.edu, Vanderbilt University, 2015',
            horizontalalignment='right', fontsize=8)

    def show_tract(self, fig, f_data, t_data, t_num):
        # Peak index
        index_of_max = np.unravel_index(
            np.argmax(t_data[:, :, :, t_num]), t_data[:, :, :, t_num].shape)

        fa_axl_slice = np.flipud(np.transpose(f_data[:, :, index_of_max[2]]))
        fa_cor_slice = np.flipud(np.transpose(f_data[:, index_of_max[1], :]))
        fa_sag_slice = np.flipud(np.transpose(f_data[index_of_max[0], :, :]))

        t_axl_slice = np.flipud(
            np.transpose(t_data[:, :, index_of_max[2], t_num]))
        t_cor_slice = np.flipud(
            np.transpose(t_data[:, index_of_max[1], :, t_num]))
        t_sag_slice = np.flipud(
            np.transpose(t_data[index_of_max[0], :, :, t_num]))

        fa_axl_slice = square_slice(fa_axl_slice)
        fa_cor_slice = square_slice(fa_cor_slice)
        fa_sag_slice = square_slice(fa_sag_slice)
        t_axl_slice = square_slice(t_axl_slice)
        t_cor_slice = square_slice(t_cor_slice)
        t_sag_slice = square_slice(t_sag_slice)

        mt_axl_slice = masked_array(t_axl_slice, t_axl_slice <= 0)
        mt_cor_slice = masked_array(t_cor_slice, t_cor_slice <= 0)
        mt_sag_slice = masked_array(t_sag_slice, t_sag_slice <= 0)

        ax = fig.add_subplot(441)
        ax.text(0, 0.5, 'FA Image', va='center', ha='center')
        ax.set_axis_off()

        ax = fig.add_subplot(445)
        ax.text(0, 0.5, 'Tract Probability\nImage', va='center', ha='center')
        ax.set_axis_off()

        ax = fig.add_subplot(449)
        ax.text(
            0, 0.5, 'Tract IsoSurface\nImage\n10% Threshold',
            va='center', ha='center')
        ax.set_axis_off()

        ax = fig.add_subplot(442)
        ax.imshow(fa_axl_slice, cmap=FA_CMAP)
        ax.set_title('Axial')
        ax.set_axis_off()

        ax = fig.add_subplot(443)
        ax.imshow(fa_cor_slice, cmap=FA_CMAP)
        ax.set_title('Coronal')
        ax.set_axis_off()

        ax = fig.add_subplot(444)
        ax.imshow(fa_sag_slice, cmap=FA_CMAP)
        ax.set_title('Sagittal')
        ax.set_axis_off()

        ax = fig.add_subplot(446)
        ax.imshow(fa_axl_slice, cmap=FA_CMAP)
        ax.imshow(mt_axl_slice, cmap=TRACT_CMAP, alpha=T_ALPHA)
        ax.set_axis_off()

        ax = fig.add_subplot(447)
        ax.imshow(fa_cor_slice, cmap=FA_CMAP)
        ax.imshow(mt_cor_slice, cmap=TRACT_CMAP, alpha=T_ALPHA)
        ax.set_axis_off()

        ax = fig.add_subplot(448)
        ax.imshow(fa_sag_slice, cmap=FA_CMAP)
        ax.imshow(mt_sag_slice, cmap=TRACT_CMAP, alpha=T_ALPHA)
        ax.set_axis_off()

        # Prep the mlab data
        t_surf = t_data[:, :, :, t_num]
        t_min = t_surf.max() * TRACT_THRESHOLD
        t_surf = masked_array(t_surf, t_surf <= t_min)
        t_surf = ndimage.uniform_filter(t_surf, 2)

        # Create the screenshots
        mlab.figure(bgcolor=(0, 0, 0))
        src = mlab.pipeline.scalar_field(t_surf)
        mlab.pipeline.iso_surface(src, contours=[t_min, ], colormap='autumn')

        # Axial
        mlab.view(0, 0)
        t_axl_surf = mlab.screenshot(mode='rgb')

        # Coronal
        mlab.view(-90, 90)
        t_cor_surf = mlab.screenshot(mode='rgb')

        # Sagittal
        mlab.view(0, 90)
        t_sag_surf = mlab.screenshot(mode='rgb')

        mlab.close()

        # Axial
        if False:  # Make background transparent
            rgb_t_axl_surf = t_axl_surf[:, :, 0:3]
            indices = np.where(np.all(rgb_t_axl_surf == (0, 0, 0), axis=-1))
            alpha_axl_surf = t_axl_surf[:, :, 3]
            alpha_axl_surf[:, :] = 1
            alpha_axl_surf[indices[0], indices[1]] = 0
            t_axl_surf[:, :, 3] = alpha_axl_surf

        t_axl_surf = square_rgb(t_axl_surf)
        ax = fig.add_subplot(4, 4, 10)
        ax.imshow(t_axl_surf)
        ax.set_axis_off()

        # Coronal
        if False:  # Make background transparent
            rgb_t_cor_surf = t_cor_surf[:, :, 0:3]
            indices = np.where(np.all(rgb_t_cor_surf == (0, 0, 0), axis=-1))
            alpha_cor_surf = t_cor_surf[:, :, 3]
            alpha_cor_surf[:, :] = 1
            alpha_cor_surf[indices[0], indices[1]] = 0
            t_cor_surf[:, :, 3] = alpha_cor_surf

        t_cor_surf = square_rgb(t_cor_surf)
        ax = fig.add_subplot(4, 4, 11)
        ax.imshow(t_cor_surf)
        ax.set_axis_off()

        # Sagittal
        if False:  # Make background transparent
            rgb_t_sag_surf = t_sag_surf[:, :, 0:3]
            indices = np.where(np.all(rgb_t_sag_surf == (0, 0, 0), axis=-1))
            alpha_sag_surf = t_sag_surf[:, :, 3]
            alpha_sag_surf[:, :] = 1
            alpha_sag_surf[indices[0], indices[1]] = 0
            t_sag_surf[:, :, 3] = alpha_sag_surf

        t_sag_surf = square_rgb(t_sag_surf)
        ax = fig.add_subplot(4, 4, 12)
        ax.imshow(t_sag_surf)
        ax.set_axis_off()

        fig.suptitle(
            TRACT_DICT[t_num][3] + ' (' + TRACT_DICT[t_num][0] + ')', fontsize=16)
        self.show_footer()

    def make_pdf(self, fa_path, tracts_path, pdf_path, trac_stats, proj, sess):
        (pdf_dir, pdf_name) = os.path.split(pdf_path)

        # Load the FA data 3-D
        f_img = nib.load(fa_path)
        f_img_data = f_img.get_data()

        # Load the Tracts data 4-D
        t_img = nib.load(tracts_path)
        t_img_data = t_img.get_data()

        fig = plt.figure(0, figsize=(7.5, 9.5))

        # Make the first page
        self.tracula_first_page(
            fig, f_img_data, t_img_data, trac_stats, proj, sess)
        plt.subplots_adjust(wspace=0.01, hspace=0.01)
        plt.show()
        tmp_pdf = os.path.join(pdf_dir, '0_' + pdf_name)
        print('INFO:saving PDF:' + tmp_pdf)
        fig.savefig(
            tmp_pdf, transparent=True, orientation='portrait', dpi=SAVE_DPI)

        # Make the invidual tract pages
        t_count = t_img_data.shape[3]
        for t_num in range(0, t_count):
            fig.clf()
            self.show_tract(fig, f_img_data, t_img_data, t_num)
            plt.subplots_adjust(wspace=0.01, hspace=0.01)
            plt.show()
            tmp_pdf = os.path.join(
                pdf_dir, 
                str(t_num + 1) + '_TRACT_' + TRACT_DICT[t_num][0] + '_' + pdf_name)
            print('INFO:saving PDF:' + tmp_pdf)
            fig.savefig(
                tmp_pdf, transparent=False, orientation='portrait', dpi=SAVE_DPI)

        plt.close(fig)

        # Concatenate PDF
        cmd = 'gs -q -sPAPERSIZE=letter -dNOPAUSE -dBATCH -sDEVICE=pdfwrite -sOutputFile=' + pdf_path + ' ' + pdf_dir + '/[0-9]*.pdf'
        print('INFO:saving final PDF:' + cmd)
        os.system(cmd)

    def write_stats(self, file_path, stats):
        with open(file_path, 'w') as f:
            for key in sorted(stats):
                f.write(key + '=' + stats[key] + '\n')

    def parse_trac_stats(self, trac_dir, sess_label):
        stats = {}

        # Parse each file
        for f in DIR2TRACT:
            tract_file = trac_dir + '/' + sess_label + '/dpath/' + f + '/pathstats.overall.txt'
            tract = DIR2TRACT[f]

            # Load the file
            with open(tract_file) as f:
                line_data = list(map(lambda x: x.strip(), f.read().splitlines()))

            # Parse each line
            for line in line_data:
                if line.startswith('#'):
                    continue

                stringline = line.split(' ')
                if len(stringline) > 1:
                    k = 'tracula' + '_' + tract + '_' + stringline[0].lower()
                    stats[k] = stringline[1]

        return stats

    def parse_dwi_motion(self, motion_file):
        stats = {}

        with open(motion_file) as f:
            line_data = list(map(lambda x: x.strip(), f.read().splitlines()))

        if line_data[0] != 'AvgTranslation AvgRotation PercentBadSlices AvgDropoutScore':
            return None

        motion_data = line_data[1].split()

        if len(motion_data) != 4:
            return None

        stats['tracula_motion_avgtrans'] = motion_data[0]
        stats['tracula_motion_avgrot'] = motion_data[1]
        stats['tracula_motion_pctbadslices'] = motion_data[2]
        stats['tracula_motion_avgdropscore'] = motion_data[3]

        return stats
