from numpy import *
from utils import *
from scipy.signal import convolve2d
from scipy.special import erf

def qratio(boxes):
    return (sum(sum(boxes,-1),-1)/boxes[...,1,1]-1)/8

def qratio_sim(points, sigma): #Simulated Q-ratio
    #center and sigma are broadcast against each other.
    
    #Set the Q-ratio region: 3x3 pixels around 1x1 center.
    q_matrix = [[[2.,-1.]],[[1.,0.]]]
    
    #Add three new axes for the computation
    points_new = points[...,None,:,None]
    sigma_new = sigma[...,None,None,None]
    
    return (divide.reduce(prod(subtract.reduce(erf(divide(q_matrix-
        points_new,sigma_new*sqrt(2))),-1),-1),-1)-1)/8

class Image:
    def __init__(self, pixels, ka_guess=505.):
        self.pixels = pixels
        self.totals = totals(self.pixels, n=3)
        self.maxima = maxima(self.totals, n=3)
        self.k_alpha = k_alpha(self.totals, self.maxima, ka_guess)
        self.good = (abs(self.totals - self.k_alpha[0]) < self.k_alpha[1])
        self.boxes = boxes(self.good, self.pixels, n=3)
	self.good_box = self.boxes.reshape((-1,9)).argmax(axis=1) == 4
	self.boxes = self.boxes[self.good_box].copy()
        self.qratio = qratio(self.boxes)
	self.qratio_agg = qratio(average(self.boxes, 0))

