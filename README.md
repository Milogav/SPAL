# SPAL

## Description

This repository contains a 3DSlicer extension written in python than performs spatiotemporal alignment of in utero BOLD MRI sequences acquired during maternal hyperoxia, as described in the research paper: 

        Spatiotemporal Alignment of In Utero BOLD-MRI Series
        (Esra Abaci Turk, PhD,1,2 Jie Luo, PhD,1,2 Borjan Gagoski, PhD,3 Javier Pascau, PhD,2,4,5 Carolina Bibbo, MD,6 Julian N. Robinson, MD,6 P. Ellen Grant, MD, 1 Elfar Adalsteinsson, PhD,2,7,8 Polina Golland, PhD,7,9 and Norberto Malpica, PhD2,10*)
        http://dx.doi.org/10.1002/jmri.25585

## Dependencies
- 3DSlicer http://download.slicer.org/

- Elastix http://elastix.isi.uu.nl/

- The following python packages: 
        nibabel
        scipy
        numpy 

 - dcm2nii (required for dicom to nii conversion module)
 	- Ubuntu installation: sudo apt-get install mricron
	- MacOS installation : download MRIcron .dmg file (https://www.nitrc.org/frs/download.php/9330/MRIcron_macOS.dmg) and move the MRIcron folder inside the .dmg file to '/Applications' folder

## Installation

1) Add each module folder to 3DSlicer module paths (Edit -> Application settings -> Modules -> Paths -> Add). This folders are:

	- .../AverageTimeSerieMRI
	- .../BiasCorrection
	- .../Dicom2NiiConverter
	- .../FirstOutlierRejection
	- .../InterMC_NonRigidUterus
	- .../InterMC_RigidBrain
	- .../InterMC_RigidUterus
	- .../INTRAvolumeMovementCorrection
	- .../SecondOutlierRejection
	- .../TimeActivityCurvesGeneration

2) Allow the python executable scripts (the files without extension at each module folder) to be executed as a program (this step is not required in MacOS)

3) Change the path in the '.../_config/elastixPath.txt' file with the path to elastix in your computer (e.g. /home/user/elastix)
	- (Mac users) Also change the path in the '.../_config/dcm2niiPath.txt' file with the path to dcm2nii executable in your computer (e.g. /Applications/MRIcron/dcm2nii -> default)

4) Through 3DSlicer python interactor, install nibabel and scipy packages via pip:

        import pip
        pip.main(['install','scipy'])
        pip.main(['install','nibabel'])

KNOWN BUGS AND POSSIBLE SOLUTIONS:

1) There is a bug when installing nibabel through pip on the slicer python interactor. If pip command does not work, open a terminal in your computer and install nibabel through pip (e.g. sudo pip install nibabel). Then copy the folder where nibabel was installed (should be inside the dist-packages folder in the python directory e.g. /usr/local/lib/python2.7/dist-packages/nibabel (Ubuntu) || /Library/Python/2.7/dist-packages/nibabel (Mac) ) to the slicer python directory (e.g. /home/user/Slicer-4.8.1-linux-amd64/lib/Python/lib/python2.7 (Ubuntu) || /Applications/Slicer.app/Contents/lib/Python/lib/python2.7 (Mac) ). Then, nibabel package should be importable in the slicer's python interactor.

2) The shebang line ( #!/usr/bin/env python-real ) in the python executable files seems to load the Slicer python interpreter (python-real) wrongly in MacOS, which makes some of the import statements (e.g for numpy and nibabel) to fail. This has been taken into consideration, by setting a default python-real path in each executable in the MacOS version of the extension. (#!/Applications/Slicer.app/Contents/bin/python-real ). Please note that this default path will work if 3DSlicer was installed under that default folder. Otherwise, the shebang line in each python executable (the files without extension at each module folder) should be changed accordingly to point to the the python-real executable file of your Slicer application path. 

NOTE: this extension has been tested in Slicer version 4.8 for Ubuntu 16.04 and MacOS Sierra. 
