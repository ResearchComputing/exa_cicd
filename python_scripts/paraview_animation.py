import argparse

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
            camera_focal_point,
            camera_position):
    filenames = [file_prefix + str(index).zfill(5) for index in range(low_index, high_index, index_step)]

    reader = AMReXBoxLibParticlesReader(FileNames=filenames, ParticleType="particles")
    Show(reader)

    #print(dp.Representation, dp.GetProperty("Representation").Available)
    dp = GetDisplayProperties()
    dp.Representation = 'Point Gaussian'

    Render()
    camera = GetActiveCamera()
    camera.SetFocalPoint(camera_focal_point[0],camera_focal_point[1],camera_focal_point[2])
    camera.SetPosition(camera_position[0], camera_position[1], camera_position[2])

    # Animate over all time steps.
    AnimateReader(reader)
    # Save the animation to an avi file
    SaveAnimation(filename=outfile)


parser = argparse.ArgumentParser(description='Animation options for MFIX-Exa plotfiles')
parser.add_argument('--plot-file-prefix', dest='plot_file_prefix', type=str, required=True, help='Plot file pattern prefix glob (ex: /home/user/plt)')
parser.add_argument('--outfile', dest='outfile', type=str, required=True, help='Path to save velocity plot file')
parser.add_argument('--low-index', dest='low_index', type=int, required=True, help='Starting plotfile index (int)')
parser.add_argument('--high-index', dest='high_index', type=int, required=True, help='Ending plotfile index (int)')
parser.add_argument('--index-step', dest='index_step', type=int, required=True, help='Step between plotfiles (int)')
parser.add_argument('--camera-focal-point', dest="camera_focal_point", type=float, nargs=3, required=True, help="3 floats: x y z")
parser.add_argument('--camera-position', dest="camera_position", type=float, nargs=3, required=True, help="3 floats x y z")
args = parser.parse_args()

LoadAmrexParticleFiles(
            outfile=args.outfile,
            file_prefix=args.plot_file_prefix,
            low_index=args.low_index,
            high_index=args.high_index,
            index_step=args.index_step,
            camera_focal_point=args.camera_focal_point,
            camera_position=args.camera_position,
            )
