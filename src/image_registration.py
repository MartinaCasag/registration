from matplotlib import pyplot as plt
import SimpleITK as sitk

def multires_registration(fixed_image, moving_image, initial_transform):
    registration_method = sitk.ImageRegistrationMethod()
    # Similarity metric settings:
    registration_method.SetMetricAsJointHistogramMutualInformation()
    registration_method.SetMetricSamplingStrategy(registration_method.RANDOM) #random voxels chosen to evaluate the metric
    registration_method.SetMetricSamplingPercentage(0.01) #percentage of voxels used for sampling
    registration_method.SetInterpolator(sitk.sitkLinear)

    # Optimizer settings:
    registration_method.SetOptimizerAsGradientDescent(learningRate=1.0, numberOfIterations=100,
                                                      estimateLearningRate=registration_method.Once)

    registration_method.SetOptimizerScalesFromPhysicalShift()

    registration_method.SetInitialTransform(initial_transform, inPlace=False)

    # Setup for the multi-resolution framework:
    registration_method.SetShrinkFactorsPerLevel(shrinkFactors=[4, 2, 1])
    registration_method.SetSmoothingSigmasPerLevel(smoothingSigmas=[2, 1, 0])
    registration_method.SmoothingSigmasAreSpecifiedInPhysicalUnitsOn()

    #execution and printing of results:
    final_transform = registration_method.Execute(fixed_image, moving_image)
    print('Final metric value: {0}'.format(registration_method.GetMetricValue()))
    print('Optimizer\'s stopping condition, {0}'.format(registration_method.GetOptimizerStopConditionDescription()))
    return final_transform, registration_method.GetMetricValue()


img1 = sitk.ReadImage("assets/ct/training_001_ct.mhd", sitk.sitkFloat32) #fixed image
img2 = sitk.ReadImage("assets/mr_T2/training_001_mr_T2.mhd", sitk.sitkFloat32) #moving image

#set initial transform
initial_transform = sitk.CenteredTransformInitializer(img1, img2, sitk.Euler3DTransform())

#resample the moving image to fit in the space of the fixed image and apply the initial transform
moving_resampled = sitk.Resample(img2, img1, initial_transform, sitk.sitkLinear, 0.0, img2.GetPixelID())

#get the final transform usign the registration function
final_transform, metr = multires_registration(img1, moving_resampled, initial_transform)

#resample the moving image to fit in the space of the fixed image and apply the final transform
moving_resampled2 = sitk.Resample(moving_resampled, img1, final_transform, sitk.sitkLinear, 0.0, img2.GetPixelID())

simg1 = sitk.Cast(sitk.RescaleIntensity(img1), sitk.sitkUInt8)
simg2 = sitk.Cast(sitk.RescaleIntensity(moving_resampled2), sitk.sitkUInt8)

# IMAGE FUSION:
#combine the scalar images into a multicomponent image
cimg_col1 = sitk.Compose(simg1, simg1 // 2. + simg2 // 2., simg2) #orange - blue
cimg_col2 = sitk.Compose(simg1, simg2, simg1) #magenta - green

zeros = sitk.Image(simg1.GetSize(), simg1.GetPixelID()) #create new image with same size and pixel type
zeros.CopyInformation(simg1) #copy the origin, spacing and direction from previous image
cimg_col3 = sitk.Compose(simg1, simg2, zeros) #red - green


#plot original images and result
im1 = sitk.GetArrayFromImage(img1)
im2 = sitk.GetArrayFromImage(img2)
out = sitk.GetArrayFromImage(cimg_col2)

a = []
a.append(im1)
a.append(im2)
a.append(out)

for j in range(0, len(a)):
    plt.ion()
    plt.show()
    for i in range(0, a[j].shape[0]):
        plt.clf()
        plt.title(i)
        if j == 0 or j ==1:
            plt.imshow(a[j][i, :, :], cmap='gray')
        else:
            plt.imshow(a[j][i, :, :])
        plt.axis('off')
        plt.draw()
        plt.pause(0.2)
    plt.close()
