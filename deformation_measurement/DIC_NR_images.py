from .C_First_Order import C_First_Order

from math import floor, ceil
import numpy as np
from PIL import Image
from scipy.interpolate import splrep, PPoly, RectBivariateSpline, BSpline, BPoly, bisplev, bisplrep, splder

class DIC_NR:

    def __init__(self,ref_img=None,def_img=None,subsetSize=None,ini_guess=None,*args,**kwargs):

        # Initialize variables
        self.subset_size = subsetSize
        self.spline_order = 6
        self.ini_guess = ini_guess

        # Make sure that the subset size specified is valid (not odd at this point)
        if (self.subset_size % 2 == 0):
            raise ValueError("Subset size must be odd")

        # Prepare for trouble (load images) (default directory is current working directory) https://stackoverflow.com/questions/12201577/how-can-i-convert-an-rgb-image-into-grayscale-in-python
        self.ref_image = np.array(Image.open(ref_img).convert('LA')) # numpy.array
        self.def_image = np.array(Image.open(def_img).convert('LA')) # numpy.array

        # Make it double
        self.ref_image = self.ref_image.astype('d') # convert to double
        self.def_image = self.def_image.astype('d') # convert to double

        # Obtain the size of the reference image
        self.X_size, self.Y_size, self._tmp= self.ref_image.shape

        # Termination condition for newton-raphson iteration
        self.Max_num_iter = 40 # maximum number of iterations
        self.TOL = [0,0]
        self.TOL[0] = 10**(-8) # change in correlation coeffiecient
        self.TOL[1] = 10**(-8)/2 # change in sum of all gradients.

        '''
        condition to check that point of interest is not close to edge. Point
        must away from edge greater than half of subset adding 15 to it to have
        range of initial guess accuracy.
        '''
        # +15 due to range of calc in initial_guess
        # -1 due to python indexing at 0, keep outside of rounding, using ceil as round will round down at 0.5
        self.Xmin = ceil((self.subset_size/2) + 15) -1
        self.Ymin = self.Xmin

        self.Xmax = ceil(self.X_size-((self.subset_size/2) + 15)) - 1
        self.Ymax = ceil(self.Y_size-((self.subset_size/2) + 15)) - 1
        self.Xp = self.Xmin
        self.Yp = self.Ymin

        if ( (self.Xp < self.Xmin) or (self.Yp < self.Ymin) or (self.Xp > self.Xmax) or  (self.Yp > self.Ymax) ):
            raise ValueError('Process terminated!!! First point of centre of subset is on the edge of the image. ')

        self.q_k = np.zeros(6)


    def initial_guess(self, ref_image, def_image, ini_guess, subset_size, Xp, Yp):

        # Automatic Initial Guess
        #q_0 = np.zeros_like([], shape=6)
        q_0 = np.zeros(6)
        q_0[0:2] = ini_guess

        # check all values of u & v within +/- 15 range of initial guess
        range_ = 15
        u_check = np.arange((round(q_0[0]) - range_), (round(q_0[0]) + range_)+1, 1, dtype=int)
        v_check = np.arange((round(q_0[1]) - range_), (round(q_0[1]) + range_)+1, 1, dtype=int)

        # Define the intensities of the first reference subset
        subref = ref_image[Yp-floor(subset_size/2):(Yp+floor(subset_size/2)), Xp-floor(subset_size/2):Xp+floor(subset_size/2),0]
        
        # Preallocate some matrix space
        sum_diff_sq = np.zeros((u_check.size, v_check.size))
        # Check every value of u and v and see where the best match occurs
        for iter1 in range(u_check.size):
            for iter2 in range(v_check.size):

                #Define intensities for deformed subset
                subdef = def_image[Yp-floor(subset_size/2)+v_check[iter2]:Yp+floor(subset_size/2)+v_check[iter2], Xp-floor(subset_size/2)+u_check[iter1]:Xp+floor(subset_size/2)+u_check[iter1],0]

                sum_diff_sq[iter1,iter2] = np.sum(np.square(subref-subdef))

        #These indexes locate the u & v value(in the initial range we are checking through) which returned the smallest sum of differences squared.
        u_value_index = np.argmin(np.min(sum_diff_sq, axis=1))
        v_value_index = np.argmin(np.min(sum_diff_sq, axis=0))

        q_0[0] = u_check[u_value_index]
        q_0[1] = v_check[v_value_index]

        self.q_k = q_0[0:6]


    def fit_spline(self, ref_img, def_img, spline_order):

        # Obtain the size of the reference image
        Y_size, X_size,tmp = ref_img.shape

        # Define the deformed image's coordinates
        X_defcoord = np.arange(0, X_size, dtype=int) # Maybe zero?
        Y_defcoord = np.arange(0, Y_size, dtype=int)

        #Fit spline
        self.def_interp = RectBivariateSpline(X_defcoord, Y_defcoord, def_img[:,:,0], kx=spline_order-1, ky=spline_order-1)
        #why subtract 1 from spline order?

        #Evaluate derivatives at coordinates
        self.def_interp_x = self.def_interp(X_defcoord, Y_defcoord, 0, 1)
        self.def_interp_y = self.def_interp(X_defcoord, Y_defcoord, 1, 0)


def DIC_NR_images(ref_img=None,def_img=None,subset_size=None,ini_guess=None,*args,**kwargs):

    # Make sure that the subset size specified is valid (not odd at this point)
    if (subset_size % 2 == 0):
        raise ValueError("Subset size must be odd")

    # Prepare for trouble (load images) (default directory is current working directory) https://stackoverflow.com/questions/12201577/how-can-i-convert-an-rgb-image-into-grayscale-in-python
    ref_image = np.array(Image.open(ref_img).convert('LA')) # numpy.array
    def_image = np.array(Image.open(def_img).convert('LA')) # numpy.array

    # Make it double
    ref_image = ref_image.astype('d') # convert to double
    def_image = def_image.astype('d') # convert to double

    # Obtain the size of the reference image
    X_size, Y_size, _tmp = ref_image.shape

    # Initialize variables
    spline_order = 6

    # Termination condition for newton-raphson iteration
    Max_num_iter = 40 # maximum number of iterations
    TOL = [0,0]
    TOL[0] = 10**(-8) # change in correlation coeffiecient
    TOL[1] = 10**(-8)/2 # change in sum of all gradients.

    '''
    condition to check that point of interest is not close to edge. Point
    must away from edge greater than half of subset adding 15 to it to have
    range of initial guess accuracy.
    '''
    # +15 due to range of calc in initial_guess
    # -1 due to python indexing at 0, keep outside of rounding
    Xmin = round((subset_size/2) + 15) -1
    Ymin = Xmin

    Xmax = round(X_size-((subset_size/2) + 15)) - 1
    Ymax = round(Y_size-((subset_size/2) + 15)) - 1
    Xp = Xmin
    Yp = Ymin

    if ((Xp < Xmin) or (Yp < Ymin) or (Xp > Xmax) or (Yp > Ymax)):
        raise ValueError('Process terminated!!! First point of centre of subset is on the edge of the image. ')
    
    #_____________Automatic Initial Guess_____________

    #Calculate quick guess for u&v through sum of differences squared?
    # Set the initial guess to be the "last iteration's" solution.
    q_k = initial_guess(ref_image, def_image, ini_guess, subset_size, Xp, Yp)

    # Preallocate the matrix that holds the deformation parameter results
    DEFORMATION_PARAMETERS = np.zeros_like([], shape=(Y_size,X_size,12))


    #_______________COMPUTATIONS________________

    # Start the timer: Track the time it takes to perform the heaviest computations
    #tic????

    #__________FIT SPLINE ONTO DEFORMED SUBSET________________________

    def_interp, def_interp_x, def_interp_y = fit_spline(ref_image, def_image, spline_order)

    #_________________________________________________________________________ 
    #t_interp = toc;    # Save the amount of time it took to interpolate

    # MAIN CORRELATION LOOP -- CORRELATE THE POINTS REQUESTED

    # for i=1:length(pts(:,1))
    for yy in range(Ymin, Ymax + 1):
        if yy > Ymin:
            q_k[0:6] = DEFORMATION_PARAMETERS[yy - 1, Xmin, 0:6]

        for xx in range(Xmin, Xmax + 1):
            #Points for correlation and initializaing the q matrix
            Xp = xx + 1
            Yp = yy + 1
            #t_tmp = toc

            _G = {
                "subset_size": subset_size,
                "ref_image": ref_image,
                "def_image": def_image,
                "def_interp": def_interp,
                "def_interp_x": def_interp_x,
                "def_interp_y": def_interp_y,
                "Xp": Xp,
                "Yp": Yp
            }

            # __________OPTIMIZATION ROUTINE: FIND BEST FIT____________________________
            # if (itr_skip == 0)
            # Initialize some values
            n = 0
            C_last, GRAD_last, HESS = C_First_Order(q_k, _G) # q_k was the result from last point or the user's guess
            optim_completed = False

            if np.isnan(abs(np.mean(np.mean(HESS)))):
                optim_completed = True

            while not optim_completed:
                # Compute the next guess and update the values
                delta_q = np.linalg.lstsq(HESS,(-GRAD_last), rcond=None) # Find the difference between q_k+1 and q_k
                q_k = q_k + delta_q[0]                             #q_k+1 = q_k + delta_q[0]
                C, GRAD, HESS = C_First_Order(q_k, _G) # Compute new values
                
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
            DEFORMATION_PARAMETERS[yy,xx,6] = 1 - C # correlation co-efficient final value

            # store points which are correlated in reference image i.e. center of subset
            DEFORMATION_PARAMETERS[yy,xx,7] = Xp
            DEFORMATION_PARAMETERS[yy,xx,8] = Yp

            DEFORMATION_PARAMETERS[yy,xx,9] = n # number of iterations
            DEFORMATION_PARAMETERS[yy,xx,10] = 0 #t_tmp # time of spline process
            DEFORMATION_PARAMETERS[yy,xx,11] = 0 #t_optim # time of optimization process

        print(yy)
        print(xx)


    '''
    filename = f"DEFORMATION_PARAMETERS({ref_img}, {def_img}, {Globs.subset_size})".replace('/', '')
    xxx,yyy,zzz = DEFORMATION_PARAMETERS.shape
    sav = np.swapaxes(DEFORMATION_PARAMETERS,2,1).reshape((xxx,yyy*zzz), order='A')
    savetxt_compact(filename, sav)
    savetxt_compact_matlab(filename, sav)
    '''

    return []

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

#DIC_NR_images("ref50.bmp", "def50.bmp", 7, [0, 0])
