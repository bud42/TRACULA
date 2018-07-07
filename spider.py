from dax import AutoSpider

name = 'TRACULA'

exe_lang = 'python'

inputs = [
    ("proj_label", "STRING", "Project"),
    ("sess_label", "STRING", "Session"),
    ("fs_path", "PATH", "Path to FreeSurfer install"),
    ("fsl_path", "PATH", "Path to FSL install"),
    ("fs_data", "DIR", "FreeSurfer subject data"),
    ("fs_label", "STRING", "Unique label of FreeSurfer assessor"),
    ("fs_subj", "STRING", "Unique label of FreeSurfer subject-sess label"),
    ("dti_nifti", "FILE", "Diffusion NIFTI file"),
    ("bval_txt", "FILE", "BVAL text file"),
    ("bvec_txt", "FILE", "BVEC text file"),
    ("cpts_txt", "FILE", "Control points text file", "F"),
    ("src_path", "PATH", "Path to spider helper source code")]

outputs = [
    ("TRACULA/*/dlabel.zip", "FILE", "DATA"),
    ("TRACULA/*/dmri.bedpostX.zip", "FILE", "DATA"),
    ("TRACULA/*/dmri_*.txt", "FILE", "DATA"),
    ("TRACULA/*/dmri.zip", "FILE", "DATA"),
    ("TRACULA/*/dpath.zip", "FILE", "DATA"),
    ("TRACULA/*/scripts.zip", "FILE", "DATA"),
    ("trac_*.sh", "FILE", "SCRIPT"),
    ("*_stats.txt", "FILE", "STATS"),
    ("TRACULA*report.pdf", "FILE", "PDF")
]

code = r"""#PYTHON

import sys
sys.path.append('${src_path}')
from traculaqa import TRACULAQA

trac = TRACULAQA(
    '${fs_path}',
    '${fsl_path}'
    )

trac.makeqa(
    '${fs_data}',
    '${fs_label}',
    '${fs_subj}',
    '${dti_nifti}',
    '${bval_txt}',
    '${bvec_txt}',
    '${temp_dir}',
    cpts_txt='${cpts_txt}',
    proj='${proj_label}',
    sess='${sess_label}'
    )
"""

if __name__ == '__main__':
    spider = AutoSpider(
        name,
        inputs,
        outputs,
        code,
        exe_lang=exe_lang
    )

    spider.go()
