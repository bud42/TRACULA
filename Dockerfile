FROM bids/base_fsl
FROM continuumio/miniconda3:latest

RUN apt-get update && apt-get -y install \
    gcc libsm6 libxt6 mayavi2 xvfb zip unzip wget curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
    && chmod 777 /opt && chmod a+s /opt

# Install prereqs
#RUN apt-get update -qq && apt-get install -yq --no-install-recommends \
#    apt-utils bzip2 ca-certificates curl zip unzip xorg wget xvfb \
#    && apt-get clean \
#    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
#    && chmod 777 /opt && chmod a+s /opt

# Install packages required by dax
#RUN apt-get update && apt-get install -yq \
#    libfreetype6-dev pkg-config  \
#    zlib1g-dev libxslt1-dev libxml2-dev \
#    && apt-get clean \
#    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
#    && chmod 777 /opt && chmod a+s /opt

# Install dax
#RUN pip install numpy pandas pyxnat
RUN pip install dax==0.8.0
RUN pip install mayavi

# Install packages needed to make PDF
RUN apt-get update && apt-get install -y \
    ghostscript libgs-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# # Install FreeSurfer v6.0.1
RUN apt-get update -qq && apt-get install -yq --no-install-recommends \
     bc libgomp1 libxmu6 libxt6 tcsh perl tar perl-modules \
     && apt-get clean \
     && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
RUN echo "Downloading FreeSurfer ..." \
     && curl -sSL --retry 5 \
     https://surfer.nmr.mgh.harvard.edu/pub/dist/freesurfer/6.0.1/freesurfer-Linux-centos6_x86_64-stable-pub-v6.0.1.tar.gz \
     | tar xzv -C /opt \
      --exclude='freesurfer/average' \
     --exclude='freesurfer/diffusion' \
     --exclude='freesurfer/docs' \
     --exclude='freesurfer/fsfast' \
     --exclude='freesurfer/fsafd' \
     --exclude='freesurfer/subjects' \
     --exclude='freesurfer/matlab' \
     --exclude='freesurfer/mni' \
     --exclude='freesurfer/data' \
     --exclude='freesurfer/bin/gcam*' \
     --exclude='freesurfer/bin/kvl*' \
     --exclude='freesurfer/lib/cuda' \
     --exclude='freesurfer/lib/tcl' \
     --exclude='freesurfer/lib/vtk' \
     --exclude='freesurfer/lib/KWWidgets' \
     --exclude='freesurfer/lib/images' \
     --exclude='freesurfer/lib/petsc' \
     --exclude='freesurfer/lib/qt'

# Configure environment
ENV FREESURFER_HOME=/opt/freesurfer
ENV FSLOUTPUTTYPE=NIFTI_GZ
ENV FSLMULTIFILEQUIT=TRUE
ENV FSLOUTPUTTYPE=NIFTI_GZ
ENV OS Linux
ENV FS_OVERRIDE 0
ENV FIX_VERTEX_AREA=
ENV SUBJECTS_DIR /opt/freesurfer/subjects
ENV FSF_OUTPUT_FORMAT nii.gz
ENV PERL5LIB /opt/freesurfer/mni/lib/perl5/5.8.5
ENV MNI_PERL5LIB /opt/freesurfer/mni/lib/perl5/5.8.5
ENV PATH=$PATH:/opt/freesurfer/bin:/usr/local/bin:/usr/bin:/bin
ENV PYTHONPATH=""
ENV FS_LICENSE=/opt/license.txt
RUN touch /opt/license.txt

RUN pip install xvfbwrapper
RUN pip install http://github.com/bud42/pyxnat/archive/py3.zip --upgrade

# Make sure other stuff is in path
COPY src /opt/src/

# Set bash as default shell
RUN ln -sf /bin/bash /bin/sh

# Make directories for I/O to bind
RUN mkdir /INPUTS /OUTPUTS

# Get the spider code
COPY spider.py /opt/spider.py
#COPY run.sh /opt/run.sh
#RUN chmod +x /opt/run.sh
ENTRYPOINT ["python", "/opt/spider.py"]
#ENTRYPOINT /opt/src/run.sh
