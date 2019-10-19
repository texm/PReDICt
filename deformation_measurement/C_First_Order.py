from math import floor
import numpy as np

class C_First_Order(object):
	def __init__(self, subset_size, ref_image, def_interp, def_interp_x, def_interp_y):
		self.subset_size  = subset_size
		self.ref_image    = ref_image
		self.def_interp   = def_interp
		self.def_interp_x = def_interp_x
		self.def_interp_y = def_interp_y
		
	def ev_concatenate(self, xd, yd):
		t = self.def_interp.ev(self.X, self.Y,dx=xd, dy=yd)
		g = np.zeros_like(t)
		tmp = 0

		for first_index in range(1, self.subset_size+1):
			for second_index in range(1, self.subset_size+1):
				g[0,tmp] = t[0,((second_index - 1)*7+first_index)-1]
				tmp+=1

		return g

	def define_deformed_subset(self, q, Xp, Yp):
		half_subset = floor(self.subset_size / 2)

		i = np.arange(-half_subset, half_subset + 1, dtype=int)
		j = np.arange(-half_subset, half_subset + 1, dtype=int)

		self.I_matrix, self.J_matrix = np.meshgrid(i, j)

		self.N = self.subset_size * self.subset_size
		
		self.I = np.reshape(self.I_matrix, (1, self.N), 'F')
		self.J = np.reshape(self.J_matrix, (1, self.N), 'F')

		u           = q[0]
		v           = q[1]
		du_dx       = q[2]
		dv_dy       = q[3]
		du_dy       = q[4]
		dv_dx       = q[5]

		#check this multuply
		self.X = Xp + u + self.I + np.multiply(self.I, du_dx) + np.multiply(self.J, du_dy)
		self.Y = Yp + v + self.J + np.multiply(self.J, dv_dy) + np.multiply(self.I, dv_dx)

		#print("X,Y coords to check on spline")
		#print(self.X)
		#print(self.Y)

		#Check reason for this
		#self.X = np.subtract(self.X,1)
		#self.Y = np.subtract(self.Y,1)

	def calculate(self, q, Xp, Yp, nargout=3):
		C = 0.0
		GRAD = 0.0
		HESS = 0.0

		half_subset = floor(self.subset_size / 2)

		self.define_deformed_subset(q, Xp, Yp)

		#print(self.def_interp.ev(15,16))

		g = self.def_interp.ev(self.Y, self.X)
		g = np.reshape(g, (self.subset_size, self.subset_size))
		print("deformed subset from g:")
		#print(g)
		g = np.transpose(g)
		#print("g transpose:")
		print(g)
		g = g.flatten()

		y0 = Yp - half_subset
		y1 = Yp + half_subset+1

		x0 = Xp - half_subset
		x1 = Xp + half_subset+1

		reference_subset = self.ref_image[y0:y1, x0:x1, 0]
		print("reference_subset")
		print(reference_subset)
		f = reference_subset.flatten()
		#f = np.reshape(self.ref_image[(Yp + self.J_matrix - 1), (Xp + self.I_matrix - 1), 0], (1, self.N), 'F')

		'''
		g = np.zeros_like(t)
		tmp = 0
		for first_index in range(1, self.subset_size+1):
			for second_index in range(1, self.subset_size+1):
				g[0,tmp] = t[0,((second_index - 1)*7+first_index)-1]
				tmp+=1

		temp = (f-g)
		'''
		SS_f_g = np.sum(np.sum(np.square((f-g))))
		SS_f_sq = np.sum(np.sum(np.square(f)))

		C = np.divide(SS_f_g, SS_f_sq)

		if nargout > 1:
			a = self.def_interp.ev(self.Y, self.X, 0, 1)
			a = np.reshape(a, (self.subset_size, self.subset_size))
			a = np.transpose(a)
			print("dg_dx:(check if needs transpose")
			print(a)
			dg_dX = a.flatten()

			b = self.def_interp.ev(self.Y, self.X, 1, 0)
			b = np.reshape(b, (self.subset_size, self.subset_size))
			b = np.transpose(b)
			print("dg_dy:(check if needs transpose")
			print(np.transpose(b))
			#print(b[0][0])
			dg_dY = b.flatten()

			#dg_dX = self.ev_concatenate(0, 1)
			#dg_dY = self.ev_concatenate(1, 0)

			dX_du = 1
			dX_dv = 0
			dX_dudx = np.transpose(np.reshape(self.I,(self.subset_size,self.subset_size))).flatten()
			print(dX_dudx)
			dX_dvdy = 0
			dX_dudy = np.transpose(np.reshape(self.J,(self.subset_size,self.subset_size))).flatten()
			dX_dvdx = 0

			dY_du = 0
			dY_dv = 1
			dY_dudx = 0
			dY_dvdy = np.transpose(np.reshape(self.J,(self.subset_size,self.subset_size))).flatten()
			dY_dudy = 0
			dY_dvdx = np.transpose(np.reshape(self.I,(self.subset_size,self.subset_size))).flatten()

			dg_du = np.multiply(dg_dX, dX_du) + np.multiply(dg_dY, dY_du)
			print("dg_du:")
			print(dg_du) #good
			dg_dv = np.multiply(dg_dX, dX_dv) + np.multiply(dg_dY, dY_dv)
			print("dg_dv:")
			print(dg_dv)#good
			#print("delta x du/dx")
			#print(np.reshape(dX_dudx,(11,11)))
			dg_dudx = np.multiply(dg_dX, dX_dudx) + np.multiply(dg_dY, dY_dudx)
			print("dg_dudx")
			print(dg_dudx)
			dg_dvdy = np.multiply(dg_dX, dX_dvdy) + np.multiply(dg_dY, dY_dvdy)
			print("dg_dvdy")
			print(dg_dvdy)
			dg_dudy = np.multiply(dg_dX, dX_dudy) + np.multiply(dg_dY, dY_dudy)
			print("dg_dudy")
			print(dg_dudy)
			dg_dvdx = np.multiply(dg_dX, dX_dvdx) + np.multiply(dg_dY, dY_dvdx)
			print("dg_dvdx")
			print(dg_dvdx)

			dC_du = np.sum(np.sum(np.multiply((g-f), dg_du)))
			dC_dv = np.sum(np.sum(np.multiply(g-f, dg_dv)))
			dC_dudx = np.sum(np.sum(np.multiply(g-f, dg_dudx)))
			dC_dvdy = np.sum(np.sum(np.multiply(g-f, dg_dvdy)))
			dC_dudy = np.sum(np.sum(np.multiply(g-f, dg_dudy)))
			dC_dvdx = np.sum(np.sum(np.multiply(g-f, dg_dvdx)))

			GRAD = np.multiply(2/SS_f_sq, np.array([ dC_du, dC_dv, dC_dudx, dC_dvdy, dC_dudy, dC_dvdx ]))
			print(GRAD)

		if nargout > 2:
			d2C_du2 = np.sum(np.sum(np.multiply(dg_du, dg_du)))
			d2C_dv2 = np.sum(np.sum(np.multiply(dg_dv, dg_dv)))
			d2C_dudx2 = np.sum(np.sum(np.multiply(dg_dudx, dg_dudx)))
			d2C_dvdy2 = np.sum(np.sum(np.multiply(dg_dvdy, dg_dvdy)))
			d2C_dudy2 = np.sum(np.sum(np.multiply(dg_dudy, dg_dudy)))
			d2C_dvdx2 = np.sum(np.sum(np.multiply(dg_dvdx, dg_dvdx)))

			d2C_dudv = np.sum(np.sum(np.multiply(dg_du, dg_dv)))
			d2C_dududx = np.sum(np.sum(np.multiply(dg_du, dg_dudx)))
			d2C_dudvdy = np.sum(np.sum(np.multiply(dg_du, dg_dvdy)))
			d2C_dududy = np.sum(np.sum(np.multiply(dg_du, dg_dudy)))
			d2C_dudvdx = np.sum(np.sum(np.multiply(dg_du, dg_dvdx)))

			d2C_dvdudx = np.sum(np.sum(np.multiply(dg_dv, dg_dudx)))
			d2C_dvdvdy = np.sum(np.sum(np.multiply(dg_dv, dg_dvdy)))
			d2C_dvdudy = np.sum(np.sum(np.multiply(dg_dv, dg_dudy)))
			d2C_dvdvdx = np.sum(np.sum(np.multiply(dg_dv, dg_dvdx)))

			d2C_dudxdvdy = np.sum(np.sum(np.multiply(dg_dudx, dg_dvdy)))
			d2C_dudxdudy = np.sum(np.sum(np.multiply(dg_dudx, dg_dudy)))
			d2C_dudxdvdx = np.sum(np.sum(np.multiply(dg_dudx, dg_dvdx)))

			d2C_dvdydudy = np.sum(np.sum(np.multiply(dg_dvdy, dg_dudy)))
			d2C_dvdydvdx = np.sum(np.sum(np.multiply(dg_dvdy, dg_dvdx)))

			d2C_dudydvdx = np.sum(np.sum(np.multiply(dg_dudy, dg_dvdx)))

			marr = np.array([
					[d2C_du2, d2C_dudv, d2C_dududx, d2C_dudvdy, d2C_dududy, d2C_dudvdx],
					[d2C_dudv, d2C_dv2, d2C_dvdudx, d2C_dvdvdy, d2C_dvdudy, d2C_dvdvdx],
					[d2C_dududx, d2C_dvdudx, d2C_dudx2,    d2C_dudxdvdy, d2C_dudxdudy, d2C_dudxdvdx],
					[d2C_dudvdy, d2C_dvdvdy, d2C_dudxdvdy, d2C_dvdy2,    d2C_dvdydudy, d2C_dvdydvdx],
					[d2C_dududy, d2C_dvdudy, d2C_dudxdudy, d2C_dvdydudy, d2C_dudy2,    d2C_dudydvdx],
					[d2C_dudvdx, d2C_dvdvdx, d2C_dudxdvdx, d2C_dvdydvdx, d2C_dudydvdx, d2C_dvdx2]
				])
			HESS = np.multiply((2/SS_f_sq), marr)

		return C, GRAD, HESS