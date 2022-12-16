
#!/usr/bin/python

"""
LSM scanning code

# Adam Glaser 07/19
# Edited by Kevin Bishop 5/22
# Edited by Rob Serafin 9/22
# Edited by Lindsey Erion Barner 12/22

"""
import h5py
import numpy as np
import skimage.transform

def h5init(dest, camera, scan, experiment):

    f = h5py.File(dest, 'a')

    res_list = [1, 2, 4, 8]

    res_np = np.zeros((len(res_list), 3), dtype='float64')

    res_np[:, 0] = res_list
    res_np[:, 1] = res_list
    res_np[:, 2] = res_list

    subdiv_np = np.zeros((len(res_list), 3), dtype='uint32')

    subdiv_np[:, 0] = scan.chunkSize1
    subdiv_np[:, 1] = scan.chunkSize2
    subdiv_np[:, 2] = scan.chunkSize3

    tgroup = f.create_group('/t00000')

    tile = 0

    for j in range(scan.zTiles):

        for k in range(scan.yTiles):

            for ch in range(scan.nWavelengths):

                idx = tile + scan.zTiles*scan.yTiles*ch

                sgroup = f.create_group('/s' + str(idx).zfill(2))
                resolutions = f.require_dataset('/s' + str(idx).zfill(2) + '/resolutions',
                                                chunks=(res_np.shape),
                                                dtype='float64',
                                                shape=(res_np.shape),
                                                data=res_np)

                subdivisions = f.require_dataset('/s' + str(idx).zfill(2) + '/subdivisions',
                                                 chunks=(res_np.shape),
                                                 dtype='uint32',
                                                 shape=(subdiv_np.shape),
                                                 data=subdiv_np)

                for z in range(len(res_list)-1, -1, -1):

                    res = res_list[z]

                    resgroup = f.create_group('/t00000/s' + str(idx).zfill(2) + '/' + str(z))

                    if camera.quantSigma[list(experiment.wavelengths)[ch]] == 0:

                        data = f.require_dataset('/t00000/s' + str(idx).zfill(2) + '/' + str(z) + '/cells', 
                                                 chunks=(scan.chunkSize1,
                                                         scan.chunkSize2,
                                                         scan.chunkSize3),
                                                 dtype='int16',
                                                 shape=np.ceil(np.divide([scan.nFrames,
                                                                          camera.Y,
                                                                          camera.X],
                                                                          res)
                                                                          )
                                                                          )
                    else:
                        if ((camera.B3Denv != '') and
                            (camera.B3Denv != os.environ['CONDA_DEFAULT_ENV'])
                            ):
                            print('Warning: B3D is active but the ' +
                                  'current conda environment is: ' +
                                  os.environ['CONDA_DEFAULT_ENV'])
                            print('Press CTRL + C to exit and run \'conda' +
                                  ' activate ' + camera.B3Denv + '\' before ' +
                                  'running lsm-python-main.py')
                            input('Press Enter to override this warning' +
                                  ' and continue anyways')

                        data = f.require_dataset('/t00000/s' + str(idx).zfill(2) + '/' + str(z) + '/cells',
                                chunks=(scan.chunkSize1,
                                        scan.chunkSize2,
                                        scan.chunkSize3),
                                dtype='int16',
                                shape=np.ceil(np.divide([scan.nFrames,
                                                        camera.Y,
                                                        camera.X],
                                                        res)),
                                compression=32016,
                                compression_opts=(round(camera.quantSigma[list(experiment.wavelengths)[ch]]*1000),
                                                    camera.compressionMode,
                                                    round(2.1845*1000),
                                                    0, 
                                                    round(1.5*1000))
                                                 )

            tile += 1

    f.close()


def h5write(dest, img_3d, idx, ind1, ind2):

    f = h5py.File(dest, 'a')

    res_list = [1, 2, 4, 8]

    for z in range(len(res_list)):
        res = res_list[z]
        if res > 1:
            img_3d = skimage.transform.downscale_local_mean(img_3d,
                                                            (2, 2, 2)
                                                            ).astype('uint16')

        if ind1 == 0:
            ind1_r = ind1
        else:
            ind1_r = np.ceil((ind1 + 1)/res - 1)

        data = f['/t00000/s' + str(idx).zfill(2) + '/' + str(z) + '/cells']
        data[int(ind1_r):int(ind1_r+img_3d.shape[0])] = img_3d.astype('int16')

    f.close()


def write_xml(experiment, camera, scan):

    print("Writing BigDataViewer XML file...")

    c = scan.nWavelengths  # number of channels
    tx = scan.yTiles  # number of lateral x tiles
    ty = scan.zTiles  # number of vertical y tiles
    t = tx*ty  # total tiles

    ox = experiment.yWidth*1000  # offset along x in um
    oy = experiment.zWidth*1000  # offset along y in um

    sx = camera.sampling  # effective pixel size in x direction

    # effective pixel size in y direction
    sy = camera.sampling*np.cos(experiment.theta*np.pi/180.0)

    # effective pixel size in z direction (scan direction)
    sz = experiment.xWidth

    scale_x = sx/sy  # normalized scaling in x
    scale_y = sy/sy  # normalized scaling in y
    scale_z = sz/sy  # normalized scaning in z

    # shearing based on theta and y/z pixel sizes
    shear = -np.tan(experiment.theta*np.pi/180.0)*sy/sz

    f = open(experiment.drive + ':\\' + experiment.fname + '\\data.xml', 'w')
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    f.write('<SpimData version="0.2">\n')
    f.write('\t<BasePath type="relative">.</BasePath>\n')
    f.write('\t<SequenceDescription>\n')
    f.write('\t\t<ImageLoader format="bdv.hdf5">\n')
    f.write('\t\t\t<hdf5 type="relative">data.h5</hdf5>\n')
    f.write('\t\t</ImageLoader>\n')
    f.write('\t\t<ViewSetups>\n')

    for i in range(0, c):
        for j in range(0, t):
            ind = j+i*t
            if ind <= scan.yTiles*scan.zTiles*scan.nWavelengths:
                f.write('\t\t\t<ViewSetup>\n')
                f.write('\t\t\t\t<id>' + str(t*i+j) + '</id>\n')
                f.write('\t\t\t\t<name>' + str(t*i+j) + '</name>\n')
                f.write('\t\t\t\t<size>' + str(camera.X) + ' ' + str(camera.Y)
                        + ' ' + str(scan.nFrames) + '</size>\n')
                f.write('\t\t\t\t<voxelSize>\n')
                f.write('\t\t\t\t\t<unit>um</unit>\n')
                f.write('\t\t\t\t\t<size>' + str(sx) + ' ' + str(sy) + ' '
                        + str(sz) + '</size>\n')
                f.write('\t\t\t\t</voxelSize>\n')
                f.write('\t\t\t\t<attributes>\n')
                f.write('\t\t\t\t\t<illumination>0</illumination>\n')
                f.write('\t\t\t\t\t<channel>' + str(i) + '</channel>\n')
                f.write('\t\t\t\t\t<tile>' + str(j) + '</tile>\n')
                f.write('\t\t\t\t\t<angle>0</angle>\n')
                f.write('\t\t\t\t</attributes>\n')
                f.write('\t\t\t</ViewSetup>\n')

    f.write('\t\t\t<Attributes name="illumination">\n')
    f.write('\t\t\t\t<Illumination>\n')
    f.write('\t\t\t\t\t<id>0</id>\n')
    f.write('\t\t\t\t\t<name>0</name>\n')
    f.write('\t\t\t\t</Illumination>\n')
    f.write('\t\t\t</Attributes>\n')
    f.write('\t\t\t<Attributes name="channel">\n')

    for i in range(0, c):
        ind = i
        if ind <= scan.nWavelengths:
            f.write('\t\t\t\t<Channel>\n')
            f.write('\t\t\t\t\t<id>' + str(i) + '</id>\n')
            f.write('\t\t\t\t\t<name>' + str(i) + '</name>\n')
            f.write('\t\t\t\t</Channel>\n')

    f.write('\t\t\t</Attributes>\n')
    f.write('\t\t\t<Attributes name="tile">\n')

    for i in range(0, t):
        ind = i
        if ind <= scan.yTiles*scan.zTiles:
            f.write('\t\t\t\t<Tile>\n')
            f.write('\t\t\t\t\t<id>' + str(i) + '</id>\n')
            f.write('\t\t\t\t\t<name>' + str(i) + '</name>\n')
            f.write('\t\t\t\t</Tile>\n')

    f.write('\t\t\t</Attributes>\n')
    f.write('\t\t\t<Attributes name="angle">\n')
    f.write('\t\t\t\t<Illumination>\n')
    f.write('\t\t\t\t\t<id>0</id>\n')
    f.write('\t\t\t\t\t<name>0</name>\n')
    f.write('\t\t\t\t</Illumination>\n')
    f.write('\t\t\t</Attributes>\n')
    f.write('\t\t</ViewSetups>\n')
    f.write('\t\t<Timepoints type="pattern">\n')
    f.write('\t\t\t<integerpattern>0</integerpattern>')
    f.write('\t\t</Timepoints>\n')
    f.write('\t\t<MissingViews />\n')
    f.write('\t</SequenceDescription>\n')

    f.write('\t<ViewRegistrations>\n')

    for i in range(0, c):
        for j in range(0, ty):
            for k in range(0, tx):

                ind = i*ty*tx + j*tx + k

                if ind <= scan.yTiles*scan.zTiles*scan.nWavelengths:

                    shiftx = scale_x*(ox/sx)*k  # shift tile in x, unit pixels
                    shifty = -scale_y*(oy/sy)*j  # shift tile in y, unit pixels

                    f.write('\t\t<ViewRegistration timepoint="0" setup="'
                            + str(ind) + '">\n')

                    # affine matrix for translation of
                    # tiles into correct positions
                    f.write('\t\t\t<ViewTransform type="affine">\n')
                    f.write('\t\t\t\t<Name>Overlap</Name>\n')
                    f.write('\t\t\t\t<affine>1.0 0.0 0.0 ' + str(shiftx)
                            + ' 0.0 1.0 0.0 ' + str(shifty)
                            + ' 0.0 0.0 1.0 0.0</affine>\n')
                    f.write('\t\t\t</ViewTransform>\n')

                    # affine matrix for scaling of tiles in orthogonal
                    # XYZ directions, accounting for theta and
                    # inter-frame spacing
                    f.write('\t\t\t<ViewTransform type="affine">\n')
                    f.write('\t\t\t\t<Name>Scale</Name>\n')
                    f.write('\t\t\t\t<affine>' + str(scale_x)
                            + ' 0.0 0.0 0.0 0.0 ' + str(scale_y)
                            + ' 0.0 0.0 0.0 0.0 ' + str(scale_z)
                            + ' 0.0</affine>\n')
                    f.write('\t\t\t</ViewTransform>\n')

                    # affine matrix for shearing of data within each tile
                    f.write('\t\t\t<ViewTransform type="affine">\n')
                    f.write('\t\t\t\t<Name>Deskew</Name>\n')
                    f.write('\t\t\t\t<affine>1.0 0.0 0.0 0.0 0.0 1.0 '
                            + str(0.0) + ' 0.0 0.0 ' + str(shear)
                            + ' 1.0 0.0</affine>\n')
                    f.write('\t\t\t</ViewTransform>\n')

                    f.write('\t\t</ViewRegistration>\n')

    f.write('\t</ViewRegistrations>\n')
    f.write('\t<ViewInterestPoints />\n')
    f.write('\t<BoundingBoxes />\n')
    f.write('\t<PointSpreadFunctions />\n')
    f.write('\t<StitchingResults />\n')
    f.write('\t<IntensityAdjustments />\n')
    f.write('</SpimData>')
    f.close()