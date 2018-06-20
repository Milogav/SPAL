#####IMPORTS
import slicer
import os
import nibabel as nib
import numpy as np
import time

########### FUNCTION TO EXTRACT INPUT ARGUMENTS ###############
def getArguments():
    moduleDir = os.path.dirname(os.path.realpath(__file__))
    f = open(moduleDir+'/arguments.txt','r')
    arguments = f.read().split()
    f.close()
    os.remove(moduleDir+'/arguments.txt')
    return arguments

########### FUNCTION TO END THE PROGRAM EXECUTION ###############
def stopExecution(message = ''):
    print(message)
    quit()
################################

def load_nii(imgPath):
    imgNii = nib.load(imgPath)
    array = imgNii.get_data()
    return imgNii,array

def save_nii(array,nii_data,out_path):
    if not '.gz' in out_path:
        out_path += '.gz'
    img = nib.Nifti1Image(array, nii_data.affine, nii_data.header)
    nib.save(img,out_path)

def createVolume(name,n_row,n_col,n_slice):
        imageSize = [n_row, n_col, n_slice]
        imageSpacing = [1.0, 1.0, 1.0]
        voxelType = vtk.VTK_FLOAT
        
        # Create an empty image volume
        imageData = vtk.vtkImageData()
        imageData.SetDimensions(imageSize)
        imageData.AllocateScalars(voxelType, 1)
        thresholder = vtk.vtkImageThreshold()
        thresholder.SetInputData(imageData)
        thresholder.SetInValue(0)
        thresholder.SetOutValue(0)
        
        # Create volume node
        volumeNode = slicer.vtkMRMLScalarVolumeNode()
        volumeNode.SetSpacing(imageSpacing)
        volumeNode.SetImageDataConnection(thresholder.GetOutputPort())
        
        # Add volume to scene
        slicer.mrmlScene.AddNode(volumeNode)
        displayNode = slicer.vtkMRMLScalarVolumeDisplayNode()
        slicer.mrmlScene.AddNode(displayNode)
        colorNode = slicer.util.getNode('Grey')
        displayNode.SetAndObserveColorNodeID(colorNode.GetID())
        volumeNode.SetAndObserveDisplayNodeID(displayNode.GetID())
        volumeNode.CreateDefaultStorageNode()
        volumeNode.SetName(name)
        
        return volumeNode

####argument extraction
args = getArguments()

boldPath = args[0]
maskPath = args[1]
outPath = args[2]
outName = args[3]
startVol = int(args[4])
endVol = int(args[5])+1
gridResolution = args[6]
numIterations = args[7]
shrinkFactor = args[8]
#########

###define some parameters for n4itk bias correction module
n4parameters = {}
n4parameters["initialMeshResolution"] = gridResolution
n4parameters["numberOfIterations"] = numIterations
n4parameters["shrinkFactor"] = shrinkFactor

##load bold and mask arrays
boldFileName = os.path.basename(boldPath)
boldNii,bold = load_nii(boldPath)
maskNii,mask = load_nii(maskPath)

mask = mask.astype(bool)

r,c,p,t = bold.shape

if endVol > t:
  endVol = t

if startVol > endVol:
    stopExecution('\n\nError: The start volume selected for the averaging frame must be lower than the end volume selected')
    
numFrames = endVol-startVol
MSE = np.zeros(numFrames)
numVoxelsWithinMask = np.sum(mask)

logDir = outPath+os.sep+'Logs'
if not os.path.isdir(logDir):
    os.makedirs(logDir)
f=open(logDir+os.sep+'log_step1.txt','wb')
begin=time.time()

f.write('Extracting average volume without outliers inside volume range: '+str(startVol)+'/'+str(endVol-1)+'\nVolumes inside range: '+str(numFrames)+'\n');f.flush()

### get the MSE of each volume in the averaging frame with respect the other volumes
cont = 0
timer=time.time()
for i in range(startVol,endVol):
        f.write('Computing MSE of volume: '+str(i)+'/'+str(endVol-1)+'\n')
        f.flush()
        vol1 = bold[:,:,:,i]
        vol1 = vol1[mask]
        for j in range(startVol,endVol):
            vol2 = bold[:,:,:,j]
            vol2 = vol2[mask]
            MSE[cont] = MSE[cont] + np.sum( (vol1 - vol2) **2 )
        MSE[cont] = MSE[cont] / (numFrames * numVoxelsWithinMask)
        cont+=1

f.write('Took: '+str(time.time()-timer)+' s\n');f.flush()


boldResting = bold[:,:,:,startVol:endVol] ###extract the resting frame (averaging frame)
maxError = MSE.max()
minError = MSE.min()
thr = ( maxError + minError ) / 2 

##select only the volumes within the frame that have an MSE error below or equal to the mean MSE error
validVolumes = MSE<=thr

##calculate the average bold volume within the selected volumes
meanBold = np.mean(boldResting[:,:,:,validVolumes], axis=3, dtype=bold.dtype)

##save the average volume
averageBoldPath = outPath+os.sep+'averageWithoutOutliers.nii.gz'
save_nii(meanBold, boldNii, averageBoldPath)

###create new empty volumes as I/O of n4itk bias correction module
outBiasCorrectionNode = createVolume('outBiasCorrection',r,c,p)
biasFieldNode = createVolume('biasField',r,c,p)

###load average volume and mask volume into slicer
[_,avgBoldNode] = slicer.util.loadVolume(averageBoldPath, { 'center': True , 'discardOrientation' : True }, returnNode=True)
[_,maskNode] = slicer.util.loadVolume(maskPath, { 'center': True , 'discardOrientation' : True }, returnNode=True)

####set the remaining parameters of the n4itk bias correction
n4parameters["inputImageName"] = avgBoldNode.GetID()
n4parameters["maskImageName"] = maskNode.GetID()
n4parameters["outputImageName"] = outBiasCorrectionNode.GetID()
n4parameters["outputBiasFieldName"] = biasFieldNode.GetID()

f.write('\nComputing average bias field...\n');f.flush()
f.write('\nN4ITK parameters:'+str(n4parameters)+'\n');f.flush()

timer=time.time()
#run the bias correction module with the specified parameters
slicer.cli.run(slicer.modules.n4itkbiasfieldcorrection, None, n4parameters, wait_for_completion=True)
f.write('Took: '+str(time.time()-timer)+' s\n');f.flush()

##save resulting bias field node as a .nii file
slicer.util.saveNode(biasFieldNode, outPath+os.sep+'biasField_'+outName+'.nii.gz')

##load bias field nii file as a numpy array
biasNii,biasField = load_nii(outPath+os.sep+'biasField_'+outName+'.nii.gz')

##apply bias field correction to each volume of the initial BOLD fMRI series
f.write('\nApplying bias field correction...\n')
timer=time.time()
for i in range(0,t): 
     f.write('Correcting volume: '+str(i+1)+'/'+str(t)+'\n');f.flush()
     bold[:,:,:,i] = bold[:,:,:,i] / biasField

f.write('Took: '+str(time.time()-timer)+' s\n');f.flush()

bold = bold.astype(meanBold.dtype)

##save the bias corrected bold serie
save_nii(bold, boldNii, outPath+os.sep+outName+'.nii.gz')

##remove average bold volume
os.remove(averageBoldPath)

f.write('\DONE SUCCESSFULLY!   Total time: '+str(time.time()-begin)+'s')
f.close()
#####EXIT CODE
stopExecution('DONE SUCCESSFULLY!')
