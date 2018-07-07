FROM ubuntu:xenial

# Install FSL5 core
RUN apt-get update && apt-get install -yq --no-install-recommends \
    wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
RUN wget -O- http://neuro.debian.net/lists/xenial.us-tn.full | tee /etc/apt/sources.list.d/neurodebian.sources.list
RUN apt-key adv --recv-keys --keyserver hkp://pool.sks-keyservers.net:80 0xA5D32F012649A5A9
RUN apt-get update && apt-get install -y fsl-5.0-core

# Configure FSL environment
ENV FSLDIR=/usr/share/fsl/5.0
ENV PATH=$PATH:$FSLDIR/bin
ENV LD_LIBRARY_PATH=/usr/lib/fsl/5.0:/usr/share/fsl/5.0/bin
ENV FSLMULTIFILEQUIT=TRUE
ENV FSLOUTPUTTYPE=NIFTI_GZ
ENV FSLTCLSH=/usr/bin/tclsh
ENV FSLWISH=/usr/bin/wish

# Install FreeSurfer v6.0.1
RUN apt-get update -qq && apt-get install -yq --no-install-recommends \
    bc libglu1 libgomp1 libxmu6 libxt6 tcsh perl tar perl-modules curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
    && chmod 777 /opt && chmod a+s /opt
RUN curl -sSL --retry 5 \
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

# Configure FreeSurfer environment
ENV FREESURFER_HOME=/opt/freesurfer
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

# Install packages for python
RUN apt-get update && apt-get install -yq --no-install-recommends \
    python-dev python-pip python-setuptools python-tk \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Install packages needed to make PDF
RUN apt-get update && apt-get install -yq --no-install-recommends \
    g++ gcc libsm6 libxt6 mayavi2 xvfb zip unzip wget curl \
    ghostscript libgs-dev libpng-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
RUN pip install xvfbwrapper
RUN pip install mayavi

# Install dax
RUN pip install dax==0.8.0

# Make sure other stuff is in path
COPY src /opt/src/

# Set bash as default shell
RUN ln -sf /bin/bash /bin/sh

# Make directories for I/O to bind
RUN mkdir /INPUTS /OUTPUTS

# Get the spider code
COPY spider.py /opt/spider.py
ENTRYPOINT ["python", "/opt/spider.py"]
