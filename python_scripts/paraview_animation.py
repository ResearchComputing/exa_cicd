

from paraview.simple import *

#https://kitware.github.io/paraview-docs/latest/python/paraview.simple.AMReXBoxLibParticlesReader.html#paraview.simple.AMReXBoxLibParticlesReader
#https://www.paraview.org/Wiki/ParaView_and_Python#Control_the_camera
#https://www.paraview.org/Wiki/ParaView/Python_Scripting

def LoadAmrexParticleFiles(
            outfile,
            file_prefix,
            low_index,
            high_index,
            index_step,
            camera_focal_point):
    filenames = [file_prefix + str(index).zfill(5) for index in range(low_index, high_index, index_step)]
    # for i in range(low_index, high_index, index_step):
    #     filenames.append

    reader = AMReXBoxLibParticlesReader(FileNames=filenames, ParticleType="particles")
    Show(reader)

    #print(dp.Representation, dp.GetProperty("Representation").Available)
    dp = GetDisplayProperties()
    dp.Representation = 'Point Gaussian'
    for item in vars(dp)['_Proxy__Properties'].items():
        print(item)
    # print(vars(dp))

    Render()
    camera = GetActiveCamera()
    camera.SetFocalPoint(camera_focal_point[0],camera_focal_point[1],camera_focal_point[2])
    # Animate over all time steps. Note that we are not passing the optional
    # 3rd argument here. If you pass a filename as the 3rd argument,
    # AnimateReader will create a movie.
    AnimateReader(reader)
    # Save the animation to an avi file
    SaveAnimation(filename=outfile)



LoadAmrexParticleFiles(
            outfile="flubed.avi",
            file_prefix="/home/aaron/projects/mfix_work/vis/hcs_5k/np_0027/adapt",
            low_index=0,
            high_index=925,
            index_step=25,
            camera_focal_point=[0.0095, 0.0095, 0.0095]
            )