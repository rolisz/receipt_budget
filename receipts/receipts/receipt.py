import re
from SimpleCV import Image, FeatureSet
from get_receipt_info import process_receipt
from line import Line
import numpy as np

__author__ = 'Roland'

class Receipt:

    def __init__(self, img):
        print(img)
        print(isinstance(img, basestring))
        if isinstance(img, basestring):
            img = Image(str(img))
        print(img.size())
        self.img = img
        self.dimg = img.copy()
        self.nimg = Image(img.size())
        self.straighten()
        self.cleanEdges()
        self.findLines()
        self.readBlobs()

    def straighten(self, stepsize=3, low_angle=-5, high_angle=5):
        origWidth = self.img.width
        img = self.img.resize(w=600)         # for some reason, straightening works better at this width :-??

        # straighten out images
        # using histograms: rotate +-5 in .3 steps, get max of each histogram
        #                   and ideal rotation is argmax of those maxes

        simg = img.binarize(210)    # for some reason, straightening works better with this binarization
                                    # rather than otsu's method
        hists = []
        rng = list(range(low_angle*stepsize, high_angle*stepsize))
        bincount = 600 if img.height > 600 else img.height
        for ang in rng:
            pimg = simg.rotate(ang/float(stepsize), fixed=True)
            hist = pimg.horizontalHistogram(bincount)
            hists.append(max(hist))
        rot = np.argmax(hists)

        # if the best rotation angle is the one on the edge of our threshold, try to rotate again with an extended
        # threshold in that direction
        # @todo dry this up
        # @todo comparison if new best is better, maybe can be handled by edge
        if rot == 0:
            self.straighten(low_angle=low_angle-5, high_angle=high_angle-5)
        elif rot == len(rng) - 1:
            self.straighten(low_angle=low_angle+5, high_angle=high_angle+5)
        img = self.img.binarize().rotate(rng[rot]/float(stepsize), fixed=True)   # otsu's method removes
                                                                            # background noise better

        # self.img = img.resize(w=origWidth//2)        # so that all letters are small enough
        self.img = img.resize(w=600)                                             # maybe I should look at average size of a blob ?

    def cleanEdges(self, low_thresh=300, line_range=100, consec_lines=10, line_thresh=500, padding=10):
        # remove horizontal edges (blank lines and eventual artifacts such as receipt edge)
        # beginning is considered from the point where there is more than 100 pixels on a line
        # and in the following 100 lines there are no 10 consecutive lines with less then 250 pixels in total
        # and add 10 px padding
        # same for end
        self.gnmp = self.img.getGrayNumpy()
        verticalProj = self.gnmp.sum(axis=1)
        begin = 0
        end = 0
        for i, p in enumerate(verticalProj):
            if begin == 0 and p > low_thresh:
                found = False
                for j in range(10, line_range):
                    if sum(verticalProj[i+j:i+j+consec_lines]) < line_thresh:
                        found = True
                        break
                if not found:
                    begin = i - padding
            if begin != 0:
                break

        for i in range(len(verticalProj) - 1, 0, -1):
            p = verticalProj[i]
            if end == 0 and p > low_thresh:
                found = False
                for j in range(10, line_range):
                    if sum(verticalProj[i - j:i-j+consec_lines]) < line_thresh:
                        found = True
                        break
                if not found:
                    end = i + padding
            if end != 0:
                break
        print(self.img.size())
        print(begin)
        print(end)
        self.img = self.img.crop(begin, 0, end - begin, self.img.height)
        self.dimg = self.img.copy()

    def findLines(self, line_beg=0, line_end=0, thresh=2000, padding=2):
        # find lines
        horizProj = self.gnmp.sum(axis=0)

        self.lines = []
        for i, p in enumerate(horizProj):
            if p > thresh and line_beg == 0:
                line_beg = i - padding
            if line_beg != 0 and p < thresh:
                line_end = i + padding
                if line_end - line_beg > 15:
                    self.lines.append(Line(line_beg, line_end, self.dimg.crop(0, line_beg, self.img.width,
                                                                              line_end - line_beg)))
                line_beg = 0

        for line in self.lines:
            if line.endY - line.beginY > 15:
                self.img.drawRectangle(1, line.beginY, self.img.width - 2, line.endY - line.beginY)

    def readBlobs(self):
        for line in self.lines:
            line.analyze()
            line.readLetters()
            self.nimg.drawText(" ".join(map(lambda x:x[0],line.letters)), 10, line.beginY)
        self.img = self.img.applyLayers()
        self.nimg = self.nimg.applyLayers().getNumpy().transpose([1, 0, 2])

    def analyze_text(self):
        #print([x.getLine() for x in self.lines])
        self.props = process_receipt([x.getLine() for x in self.lines])
        #print(self.props)




def train(i):
    print(i)
    img_letters = []
    try:
        img = Receipt("D:/AI/Bonuri/bonuri/bon%d.jpg" % i)
        for line in img.lines:
            img_letters.append(line.letters)
            print(line.letters)
    except Exception:
        pass
    return i, img_letters


if __name__ == '__main__':
    img = Receipt("D:/AI/Bonuri/bonuri/bon%d.jpg" % 3)
    img.analyze_text()
    #letters = []
    #from sklearn.externals.joblib import Parallel, delayed
    #
    #
    #r = Parallel(n_jobs=4, verbose=15)(delayed(train)(i) for i in range(1, 40))
    #
    #for i, img_letters in r:
    #    letters.append(img_letters)
    #
    #import cPickle
    #f = open("read_letters.pkl", "wb")
    #cPickle.dump(letters, f)
    #f.close()