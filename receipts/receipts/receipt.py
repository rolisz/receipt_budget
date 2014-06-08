from itertools import izip_longest
import re
import string
from joblib import Parallel, delayed
from line import Line
import numpy as np
import cv2
import matplotlib.pyplot as plt
from utils import resize, rotate

__author__ = 'Roland'

count = lambda l1, l2: len(list(filter(lambda c: c in l2, l1)))
days = ['luni', 'marti', 'miercuri', 'joi', 'vineri', 'sambata', 'duminica']


class Receipt:

    def __init__(self, img):
        if isinstance(img, basestring):
            img = cv2.imread(img)
            
        cv2.imwrite("tmp//original.jpg", img)
        self.img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        cv2.imwrite("tmp//gray.jpg", self.img)

        #self.img = cv2.adaptiveThreshold(self.img,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,\
        #    cv2.THRESH_BINARY_INV,11,2)
        ret_val, self.img = cv2.threshold(self.img, -1, float(255), cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
        #cv2.imwrite("tmp//binarized.jpg", self.img)
        self.dimg = self.img.copy()
        self.nimg = np.zeros(img.shape)
        self.straighten()
        self.cleanEdges()
        self.findLines()
        self.readBlobs()

    def straighten(self, stepsize=3, low_angle=-5, high_angle=5):
        # width is shape[1], height is shape[0]
        #cv2.imwrite("tmp//before.jpg", self.img)
        origWidth = self.img.shape[1]
        if low_angle < -20 or high_angle > 20:
            raise Exception("Photo is too skewed. Please straighten photo before trying to process it")


        img = resize(self.img, width=600)         # for some reason, straightening works better at this width :-??

        # straighten out images
        # using histograms: rotate +-5 in .3 steps, get max of each histogram
        #                   and ideal rotation is argmax of those maxes

        simg = img
        hists = []
        rng = list(range(low_angle*stepsize, high_angle*stepsize))
        bincount = 600 if img.shape[0] > 600 else img.shape[0]
        for ang in rng:
            pimg = rotate(simg, ang/float(stepsize), fixed=True) # was true, but doesn't make sense and doens't work
            # pimg = rotate(simg, ang/float(stepsize))
            # cv2.imwrite("tmp//rotate %d.jpg" % ang, pimg)
            hist, _ = np.histogram(pimg.sum(axis=1), bincount)
            #plt.plot(hist)
            #plt.savefig('tmp//hist %d.png' % ang, bbox_inches='tight')
            #plt.close()
            hists.append(max(hist))
        rot = np.argmax(hists)

        # if the best rotation angle is the one on the edge of our threshold, try to rotate again with an extended
        # threshold in that direction
        if rot == 0:
            self.straighten(low_angle=low_angle-5, high_angle=high_angle-5)
        elif rot == len(rng) - 1:
            self.straighten(low_angle=low_angle+5, high_angle=high_angle+5)
        img = rotate(self.img, rng[rot]/float(stepsize), fixed=False)   # otsu's method removes
                                                                          # background noise better

        # self.img = img.resize(w=origWidth//2)        # so that all letters are small enough
        self.img = resize(img, width=600)              # maybe I should look at average size of a blob ?
        #cv2.imwrite("tmp//straight.jpg", self.img)

    def cleanEdges(self, low_thresh=300, line_range=100, consec_lines=10, line_thresh=500, padding=10):
        # remove horizontal edges (blank lines and eventual artifacts such as receipt edge)
        # beginning is considered from the point where there is more than 100 pixels on a line
        # and in the following 100 lines there are no 10 consecutive lines with less then 250 pixels in total
        # and add 10 px padding
        # or if more then 30% of pixels are all white
        # same for end
        self.gnmp = self.img.copy()
        verticalProj = self.gnmp.sum(axis=0)
        #plt.plot(verticalProj)
        #plt.savefig('tmp//edges.png', bbox_inches='tight')
        #plt.close()
        print verticalProj, verticalProj.shape
        begin = 0
        end = 0
        upper_thresh = self.img.shape[0] * 255 * 0.3 * 10
        for i, p in enumerate(verticalProj):
            if begin == 0 and p > low_thresh:
                found = False
                for j in range(10, line_range):
                    s = sum(verticalProj[i+j:i+j+consec_lines])
                    # print s, line_thresh, upper_thresh
                    if s < line_thresh or s > upper_thresh:
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
                    s = sum(verticalProj[i - j:i-j+consec_lines])
                    # print s, line_thresh, upper_thresh
                    if s < line_thresh or s > upper_thresh:
                        found = True
                        break
                if not found:
                    end = i + padding
            if end != 0:
                break

        if self.gnmp.sum(axis=0).mean() > 15000:
            begin = max(20, begin)
            end = min(self.img.shape[1] - 20, end)
        else:
            begin = max(0, begin)
            end = min(self.img.shape[1], end)
        begin = 0 if begin < 0 else begin
        end = self.img.shape[1] if end > self.img.shape[1] else end
        print 'aaaa',begin, end, 0, self.img.shape
        self.img = self.img[:, begin:end]
        #cv2.imwrite("tmp//cleaned.jpg", self.img)
        self.gnmp = self.img.copy()
        self.dimg = self.img.copy()

    def findLines(self, line_beg=0, line_end=0, thresh=2000, padding=2):
        # find lines
        print self.gnmp.shape
        horizProj = self.gnmp.sum(axis=1)

        #plt.plot(horizProj)
        #plt.savefig('tmp//lines.png', bbox_inches='tight')
        #plt.close()
        mean = np.mean(horizProj)
        if mean > thresh * 5:
            thresh = np.mean(horizProj[200:-200])
        self.lines = []
        print horizProj
        for i, p in enumerate(horizProj):
            if p > thresh and line_beg == 0:
                line_beg = i - padding
            if line_beg != 0 and p < thresh:
                line_end = i + padding
                if line_end - line_beg > 15:
                    #cv2.imwrite("tmp\\line %d.jpg" % i, self.dimg[line_beg:line_end, 0:self.img.shape[1]])
                    self.lines.append(Line(line_beg, line_end,
                                      self.dimg[line_beg:line_end, 0:self.img.shape[1]]))
                line_beg = 0
        print self.lines
        # for line in self.lines:
        #     if line.endY - line.beginY > 15:
        #         self.img.drawRectangle(1, line.beginY, self.img.width - 2, line.endY - line.beginY)

    def readBlobs(self):
        """
        Analyze each line
        """
        nr = 6
        a = Parallel(n_jobs=nr)(delayed(parallel)(lines)
                                for lines in chunks(self.lines, len(self.lines)/nr))
        self.lines = []
        for l in a:
            print(l[0].getLine())
            self.lines.extend(l)

    def analyze_text(self):
        """
        Determine the properties of each line: shop, address, cui, items, date or total
        """
        lines = [x.getLine() for x in self.lines]
        labels = self._classify_lines(lines)
        props = {'shop': '', 'address': '', 'cui': '', 'items': [], 'data': '', 'total': ''}
        items = []
        for line, label in zip(lines, labels):
            if label in ['shop', 'total']:
                props[label] = line
            elif label == 'data':
                print(line)
                reg = re.search('((\d{2,4})[./\\-](\d{2,4})[./\\-](\d{2,4}))', line)
                props['data'] = "-".join(reg.groups()[1:])
            elif label == 'cui':
                reg = re.search('(\d{4,})', line)
                props['cui'] = "RO"+str(reg.groups()[0])
            elif label == 'address':
                props[label] += line
            elif label in ['price', 'name']:
                items.append((line, label))
        it = iter(items)
        groups = []
        for pr, na in izip_longest(it, it, fillvalue=('', '')):
            if pr[1] == 'name' and na[1] == 'price':
                pr, na = na, pr
            regex = re.search(r'([0-9,.]+?) *?x *?([0-9,.]+)', pr[0])
            if regex:
                grs = regex.groups()
                if len(grs) == 2:
                    quantity = grs[0].replace(',','.')
                    price = grs[1].replace(',','.')
                    tprice = round(float(quantity)*float(price), 2)
                elif len(grs) == 1:
                    tprice = round(float(grs[0].replace(',','.')), 2)
                tprst = str(tprice).replace('.', ',')
                if tprst in na[0]:
                    groups.append((na[0][:na[0].index(tprst)], tprice))
                else:
                    groups.append((na[0], tprice))
            else:
                same_line = re.search(r'(.+?) +([0-9][0-9,.]*)', pr[0])
                if same_line:
                    grs = same_line.groups()
                    groups.append((grs[0], float(grs[1].replace(',','.'))))
                same_line = re.search(r'(.+?) +([0-9,.]+)', na[0])
                if same_line:
                    grs = same_line.groups()
                    groups.append((grs[0], float(grs[1].replace(',','.'))))

        props['items'] = groups
        self.props = props

    def _classify_lines(self, receipt):
        """
        Classify each line with what it contains using a naive, rule based classifier
        """
        labels = []
        for i, line in enumerate(receipt):
                line = str(line)
                a_chars = count(line, string.ascii_letters)
                num_chars = count(line, string.digits)
                punct_chars = count(line, string.punctuation)

                if 'bon fiscal' in line.lower():
                    labels.append('unknown')
                #if 'subtotal' in line.lower():
                #    labels.append('unknown')

                elif (re.search('S\.?C\.?(.+?)(S.?R.?L.?)|(S[:.,]?A[:.,]?)', line, re.IGNORECASE) or\
                    any(x in line.lower() for x in ['kaufland'])) and i < 5 and 'shop' not in labels:
                    labels.append('shop')
                elif (re.search('(C[^\w]?U[^\w]?I[^\w]?)|(C[^\w]?F[^\w]?)|(C[^\w]?I[^\w]?F[^\w]?)|(COD FISCAL).+? (\d){4,}', line) or\
                      re.search('\d{8}', line)) and i < 6:
                    labels.append('cui')
                elif (re.search('(STR)|(CALEA)|(B-DUL).(.+?)', line, re.IGNORECASE) and i < 7) or\
                    (re.search('(NR).(\d+)', line, re.IGNORECASE) and i < 3):
                    labels.append('address')


                elif 'TVA' in line:
                    labels.append('tva')
                elif 'TOTAL' in line and 'SUBTOTAL' not in line:
                    labels.append('total')
                elif re.search('DATA?.+?\d{2,4}[.\\-]\d{2,4}[.\\-]\d{2,4}', line, re.IGNORECASE) or\
                     re.search('\d{2}[./\\-]\d{2}[./\\-]\d{2,4}', line, re.IGNORECASE):
                    labels.append('data')
                elif a_chars > 0 and num_chars/a_chars > 1 and 2 < i < len(receipt) - 7 and \
                     all(x not in line.lower() for x in ['tel', 'fax']) and 'total' not in labels:
                    labels.append('price')
                elif 3 < i < len(receipt) - 8 and a_chars+punct_chars > 5 and 'total' not in labels and ((\
                     all(not re.search('(\W|^)'+x, line.lower()) for x in ['tel', 'fax', 'subtotal', 'numerar', 'brut', 'net'] +
                     days)\
                    and not re.search('\d{5}', line)) or labels[-1] == 'price'):

                    labels.append('name')
                else:
                    labels.append('unknown')
        return labels


def chunks(l, n):
    """ Yield successive n-sized chunks from l.
    """
    for i in xrange(0, len(l), n):
        yield l[i:i+n]


def parallel(lines):
    """
    Helper for using multiproccesing for parallel execution
    """
    for line in lines:
        line.analyze()
        line.readLetters()
    return lines

if __name__ == "__main__":
    import os
    if os.name == 'posix':
        img = Receipt("../../bons/bon1.jpg")
    else:
        img = Receipt("D:\\AI\\Bonuri\\bonuri\\bon1.jpg")
        img.analyze_text()
        with open("tmp.txt", "wb") as f:
            f.writelines([x.getLine()+"\n" for x in img.lines])

