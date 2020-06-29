
export BASE="/projects/jenkins/images"
export GAS_FRACTION="${BASE}/${ES_INDEX}/${dir}/gafraction_${BRANCH}_${COMMIT_HASH}_${RUN_DATE}"

export ANIMATE=paraview_anmiation.py
export OUTFILE=hcs.avi

pvpython paraview_animation.py \
      --outfile="hcs.avi" \
      --plot-file-prefix="/home/aaron/projects/mfix_work/vis/hcs_5k/np_0027/adapt" \
      --low-index=0 \
      --high-index=925 \
      --index-step=25 \
      --camera-focal-point 0.0095 0.0095 0.0095 \
      --camera-position 0.0095 0.0095 0.0795

pvpython paraview_animation.py \
      --outfile="flubed.avi" \
      --plot-file-prefix="/home/aaron/projects/mfix_work/vis/fluid_bed/adapt" \
      --low-index=0 \
      --high-index=925 \
      --index-step=25 \
      --camera-focal-point 0.08 0.02 0 \
      --camera-position 0.08 0.02 0.4

# LoadAmrexParticleFiles(
#             outfile=args.outfile,
#             file_prefix=args.plot_file_prefix,
#             low_index=args.low_index,
#             high_index=args.high_index,
#             index_step=args.index_step,
#             camera_focal_point=args.camera_focal_point,
#             camera_position=args.camera_position,
#             )
#
#
# ## Good defaults for plots
# # LoadAmrexParticleFiles(
# #             outfile="hcs.avi",
# #             file_prefix="/home/aaron/projects/mfix_work/vis/hcs_5k/np_0027/adapt",
# #             low_index=0,
# #             high_index=925,
# #             index_step=25,
# #             camera_focal_point=[0.0095, 0.0095, 0.0095],
# #             camera_position=[0.08, 0.02, 0.4]
# #             )
# # Need to rotate axis so x is "up"
# LoadAmrexParticleFiles(
#             outfile="flubed.avi",
#             file_prefix="/home/aaron/projects/mfix_work/vis/fluid_bed/adapt",
#             low_index=0,
#             high_index=10000,
#             index_step=500,
#             # camera_focal_point=[0,0,0]
#             camera_focal_point=[0.08, 0.02, 0],
#             camera_position=[0.08, 0.02, 0.4]
#             )
