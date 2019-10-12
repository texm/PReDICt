
from C_First_Order import C_First_Order
import Globs
from vis_script_DIC import output_folder, vis_plotter

from math import floor
import numpy as np
from PIL import Image
from scipy.interpolate import splrep, PPoly, RectBivariateSpline, BSpline, BPoly, bisplev, bisplrep, splder

def check_subset(subsetSize):
    # Make sure that the subset size specified is valid (not odd at this point)
    if (subsetSize % 2 == 0):
        raise ValueError("Subset size must be odd")

    subsetSize = Globs.subset_size
    return subsetSize

def load_images(ref_img, def_img):
    # Prepare for trouble (load images) (default directory is current working directory) https://stackoverflow.com/questions/12201577/how-can-i-convert-an-rgb-image-into-grayscale-in-python
    Globs.ref_image = np.array(Image.open(ref_img).convert('LA')) # numpy.array
    Globs.def_image = np.array(Image.open(def_img).convert('LA')) # numpy.array

    # Make it double
    Globs.ref_image = Globs.ref_image.astype('d') # convert to double
    Globs.def_image = Globs.def_image.astype('d') # convert to double
    ##### Add error checking

def get_im_shape():
    # Obtain the size of the reference image
    X_size, Y_size, _tmp= Globs.ref_image.shape
    return X_size, Y_size, _tmp

def edge_check(X_size, Y_size, subset_size):

    '''
    condition to check that point of interest is not close to edge. Point
    must away from edge greater than half of subset adding 15 to it to have
    range of initial guess accuracy.
    '''
    Xmin = round((subset_size/2) + 15) # Might need to make it 14 cuz of arrays starting at 0
    Ymin = Xmin

    Xmax = round(X_size-((subset_size/2) + 15))
    Ymax = round(Y_size-((subset_size/2) + 15))
    Globs.Xp = Xmin
    Globs.Yp = Ymin

    if ( (Globs.Xp < Xmin) or (Globs.Yp < Ymin) or (Globs.Xp > Xmax) or  (Globs.Yp > Ymax) ):
        raise ValueError('Process terminated!!! First point of centre of subset is on the edge of the image. ')
    return Xmin, Xmax, Ymin, Ymax
    ### More error checking?

def DIC_NR_images(ref_img=None,def_img=None,subsetSize=None,ini_guess=None,*args,**kwargs):

    subset_size = check_subset(subsetSize)

    load_images(ref_img, def_img)

    X_size, Y_size, _tmp = get_im_shape()

    # Initialize variables
    spline_order = 6

    # Termination condition for newton-raphson iteration
    Max_num_iter = 40 # maximum number of iterations
    TOL = [0,0]
    TOL[0] = 10**(-8) # change in correlation coeffiecient
    TOL[1] = 10**(-8)/2 # change in sum of all gradients.

    Xmin, Xmax, Ymin, Ymax = edge_check(X_size, Y_size, subset_size)

    #_____________Automatic Initial Guess_____________

    # Automatic Initial Guess
    q_0 = np.zeros_like([], shape=(6))
    q_0[0:2] = ini_guess

    range_ = 15 # Minus 1 for array starting at zero?
    u_check = np.arange((round(q_0[0]) - range_), (round(q_0[1]) + range_) + 1, dtype=int)
    v_check = np.arange((round(q_0[0]) - range_), (round(q_0[1]) + range_) + 1, dtype=int)

    # Define the intensities of the first reference subset
    subref = Globs.ref_image[Globs.Yp-floor(subset_size/2):(Globs.Yp+floor(subset_size/2))+1, Globs.Xp-floor(subset_size/2):Globs.Xp+floor(subset_size/2)+1,0]

    # Preallocate some matrix space
    sum_diff_sq = np.zeros((u_check.size, v_check.size))
    # Check every value of u and v and see where the best match occurs
    for iter1 in range(u_check.size):
        for iter2 in range(v_check.size):
            subdef = Globs.def_image[(Globs.Yp-floor(subset_size/2)+v_check[iter2]):(Globs.Yp+floor(subset_size/2)+v_check[iter2])+1, (Globs.Xp-floor(subset_size/2)+u_check[iter1]):(Globs.Xp+floor(subset_size/2)+u_check[iter1])+1,0]

            sum_diff_sq[iter2,iter1] = np.sum(np.sum(np.square(subref-subdef)))

    OFFSET1 = np.argmin(np.min(sum_diff_sq, axis=1)) # These offsets are +1 in MATLAB
    OFFSET2 = np.argmin(np.min(sum_diff_sq, axis=0))

    q_0[0] = u_check[OFFSET2]
    q_0[1] = v_check[OFFSET1]

    del u_check
    del v_check
    del iter1
    del iter2
    del subref
    del subdef
    del sum_diff_sq
    del OFFSET1
    del OFFSET2

    # Preallocate the matrix that holds the deformation parameter results
    DEFORMATION_PARAMETERS = np.zeros_like([], shape=(Y_size,X_size,12))

    # Set the initial guess to be the "last iteration's" solution.
    q_k = q_0[0:6]

    #_______________COMPUTATIONS________________

    # Start the timer: Track the time it takes to perform the heaviest computations
    #tic????

    #__________FIT SPLINE ONTO DEFORMED SUBSET________________________
    # Obtain the size of the reference image
    Y_size, X_size,tmp = Globs.ref_image.shape

    # Define the deformed image's coordinates
    X_defcoord = np.arange(0, X_size, dtype=int) # Maybe zero?
    Y_defcoord = np.arange(0, Y_size, dtype=int)



    #spline = splrep(X_defcoord, Y_defcoord)
    #Globs.def_interp = PPoly.from_spline(spline)
    Globs.def_interp = RectBivariateSpline(X_defcoord, Y_defcoord, Globs.def_image[:,:,0], kx=3, ky=3)


    #Globs.def_interp_x = Globs.def_interp.ev(0,1)
    #Globs.def_interp_y = Globs.def_interp.ev(1,0)
    '''
    Globs.def_interp_x = Globs.def_interp(X_defcoord, Y_defcoord, 0, 1)
    Globs.def_interp_x = BPoly.from_derivatives(xi=X_defcoord,yi=Globs.def_interp_x)

    Globs.def_interp_y = Globs.def_interp(X_defcoord, Y_defcoord, 1, 0)
    Globs.def_interp_y = BPoly.from_derivatives(xi=Y_defcoord,yi=Globs.def_interp_y)
    #Globs.def_interp_y = BSpline.derivative(Globs.def_interp,[1,0])
    '''
    '''
    test = splder(Globs.def_interp.tcl,1)
    Globs.def_interp_x = bisplev(X_defcoord, Y_defcoord, Globs.def_interp.tck+(5,)+(5,), 0, 1)
    Globs.def_interp_y = bisplev(X_defcoord, Y_defcoord, Globs.def_interp.tck+(5,)+(5,), 1, 0)
    '''
    '''
    Globs.def_interp_x = RectBivariateSpline(X_defcoord, Y_defcoord, Globs.def_image[:,:,0], kx=5, ky=4)
    Globs.def_interp_y = RectBivariateSpline(X_defcoord, Y_defcoord, Globs.def_image[:,:,0], kx=4, ky=5)
    '''

    Globs.def_interp_x = Globs.def_interp(X_defcoord, Y_defcoord, 0, 1)
    Globs.def_interp_y = Globs.def_interp(X_defcoord, Y_defcoord, 1, 0)
    #_________________________________________________________________________
    #t_interp = toc;    # Save the amount of time it took to interpolate


    # MAIN CORRELATION LOOP -- CORRELATE THE POINTS REQUESTED

    # for i=1:length(pts(:,1))
    for yy in range(Ymin, Ymax + 1):
        if yy > Ymin:
            q_k[0:6] = DEFORMATION_PARAMETERS[yy - 1, Xmin, 0:6]

        for xx in range(Xmin, Xmax + 1):
            #Points for correlation and initializaing the q matrix
            Globs.Xp = xx + 1
            Globs.Yp = yy + 1
            #t_tmp = toc

            # __________OPTIMIZATION ROUTINE: FIND BEST FIT____________________________
            # if (itr_skip == 0)
            # Initialize some values
            n = 0
            C_last, GRAD_last, HESS = C_First_Order(q_k) # q_k was the result from last point or the user's guess
            optim_completed = False

            if np.isnan(abs(np.mean(np.mean(HESS)))):
                print(yy)
                print(xx)
                optim_completed = True
            while not optim_completed:
                # Compute the next guess and update the values
                delta_q = np.linalg.lstsq(HESS,(-GRAD_last), rcond=None) # Find the difference between q_k+1 and q_k
                q_k = q_k + delta_q[0]                             #q_k+1 = q_k + delta_q[0]
                C, GRAD, HESS = C_First_Order(q_k) # Compute new values

                # Add one to the iteration counter
                n = n + 1 # Keep track of the number of iterations

                # Check to see if the values have converged according to the stopping criteria
                if n > Max_num_iter or (abs(C-C_last) < TOL[0] and all(abs(delta_q[0]) < TOL[1])): #needs to be tested...
                    optim_completed = True

                C_last = C #Save the C value for comparison in the next iteration
                GRAD_last = GRAD # Save the GRAD value for comparison in the next iteration
            #_________________________________________________________________________
            #t_optim = toc - t_tmp

            #_______STORE RESULTS AND PREPARE INDICES OF NEXT SUBSET__________________
            # Store the current displacements
            DEFORMATION_PARAMETERS[yy,xx,0] = q_k[0] # displacement x
            DEFORMATION_PARAMETERS[yy,xx,1] = q_k[1] # displacement y
            DEFORMATION_PARAMETERS[yy,xx,2] = q_k[2]
            DEFORMATION_PARAMETERS[yy,xx,3] = q_k[3]
            DEFORMATION_PARAMETERS[yy,xx,4] = q_k[4]
            DEFORMATION_PARAMETERS[yy,xx,5] = q_k[5]
            DEFORMATION_PARAMETERS[yy,xx,6] = 1-C # correlation co-efficient final value
            # store points which are correlated in reference image i.e. center of subset
            DEFORMATION_PARAMETERS[yy,xx,7] = Globs.Xp
            DEFORMATION_PARAMETERS[yy,xx,8] = Globs.Yp

            DEFORMATION_PARAMETERS[yy,xx,9] = n # number of iterations
            DEFORMATION_PARAMETERS[yy,xx,10] = 0 #t_tmp # time of spline process
            DEFORMATION_PARAMETERS[yy,xx,11] = 0 #t_optim # time of optimization process

    x = DEFORMATION_PARAMETERS[:,:,0]
    y = DEFORMATION_PARAMETERS[:,:,0]
    output_folder('Def_vis')

    residual = (x**2 + y**2 )**0.5
    vis_plotter(x, 'X','x_vis.png')
    vis_plotter(y, 'Y','y_vis.png')
    vis_plotter(residual,'Residual' ,'total_vis.png')

    return DEFORMATION_PARAMETERS

def savetxt_compact(fname, x, fmt="%.6g", delimiter=','):
    with open(f"compact_{fname}.csv", 'w+') as fh:
        for row in x:
            line = delimiter.join("0" if value == 0 else fmt % value for value in row)
            fh.write(line + '\n')

def savetxt_compact_matlab(fname, x, fmt="%.6g", delimiter=','):
    with open(f"matlab_{fname}.csv", 'w+') as fh:
        for row in x:
            line = delimiter.join("0" if value == 0 else fmt % value for value in row)
            fh.write(line + '\n')

DIC_NR_images("ref50.bmp", "def50.bmp", 7, [0, 0])