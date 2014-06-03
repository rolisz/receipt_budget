import cPickle
from itertools import tee, izip
import os
from joblib import load
import cv2
# from django.conf import settings
import numpy as np
from utils import resize, rotate, embiggen 

__author__ = 'Roland'

size = 10

# model = load("./ml_models/joblib_seg.jb", "rb")
model = cPickle.load(open("./ml_models/test_seg_model.pkl", "rb"))

logistic_model = load("./ml_models/joblib_letter.jb")

f = open("./ml_models/label_encoder.pkl", "rb")
labels = cPickle.load(f)
f.close()


def pairwise(iterable):
    a, b = tee(iterable)
    next(b, None)
    return izip(a, b)


def getAverageDistance(line, filter_thresh):
    diffs = list(abs(b[1] - a[2]) for a, b in pairwise(line) if abs(b[1] - a[2]) < filter_thresh)
    return sum(diffs) / len(line)


class Line:

    line_height = 30

    def __init__(self, begin, end, img):
        self.img = resize(img, height=Line.line_height)
        self.beginY = begin
        self.endY = end

    def analyze(self):
        """
        Character segmentation
        """
        prev = 0
        i = size
        true_query = []
        nimg = np.concatenate((np.zeros((20, size)),
                               resize(self.img, width=self.img.shape[1], height=20),
                               np.zeros((20, size))), axis=1)
        all_black = True
        while i < self.img.shape[1]:
            mimg = nimg[:, i-size:i+size]
            
            mimg = mimg.reshape(-1).astype(float)
            # nimg = pipe.transform(nimg)
            probabilities = model.predict_proba(mimg)[0]
            # print(probabilities)
            if probabilities[0] > probabilities[1]:
                pred = 0
            else:
                pred = 1
            if all_black and nimg[:, i].sum() > 50:
                all_black = False
            cv2.imwrite("tmp\\seg %d %s.jpg" % (i, pred), mimg.reshape((20,20)))
            if pred == 1:
                true_query.append((i - size, probabilities[1], all_black))
                all_black = True
                if 5 < i - prev < 30:
                    prev = i
                    i += 5
                else:
                    prev = i
            i += 1

        self.segments = []
        prev = 0
        for i, prob, all_black in true_query:
            if not all_black and nimg[:, prev+size:i+size].sum() > 200:
                self.segments.append((prev, i))
            prev = i
        if nimg[:, prev+size:].sum() > 200:
            self.segments.append((prev, self.img.shape[1] - 1))
        #self.img = self.img.applyLayers()

    def readLetters(self):
        """
        Character recognition
        """
        self.letters = []
        i = 0
        letters = []
        for begin, end in self.segments:
            lett = self.img[1:self.line_height - 2, begin - 1:end + 2]   # add a bit of padding to help with
                                                                                # recognition
            
            if lett.shape[1] == 0:
                continue 
            # self.img.drawRectangle(begin-1, 1, end - begin+2, 28)
            if lett.shape[0] > lett.shape[1]:
                lett = resize(lett, height=30)
            else:
                lett = resize(lett, width=30)
            if lett.shape[0] > 0 and lett.shape[1] > 0 :
                lett = embiggen(lett, (30, 30))
                cv2.imwrite("tmp\\char %d %s.jpg" % (i, "r"), lett)
                letters.append(lett.reshape(-1))
            i += 1
        try:
            characters = labels.inverse_transform(logistic_model.predict(letters))
            print characters
            for charac, segment in zip(characters, self.segments):
                self.letters.append((charac, segment[0], segment[1]))
        except ValueError:
            print(map(lambda x: x.shape, letters))
        # self.img = self.img.applyLayers()

    def getWordsX(self):
        """Return words with x coordinates"""
        word = ''
        prev = 0
        prev_word_start = 0
        distances = list(abs(b[1] - a[2]) for a, b in pairwise(self.letters))
        avg = getAverageDistance(self.letters, 30)
        space_dist = avg * 1.5 if avg * 1.5 > 5 else 7
        for i, element in enumerate(self.letters):
            letter, x1, x2 = element

            if i > 0 and x1 - prev >= space_dist and word:
                yield (word, prev_word_start)
                word = ''
                prev_word_start = x1

            prev = x2
            word += letter
        yield (word, prev_word_start)

    def getLine(self):
        """Just return words with spaces between them"""
        words = list(self.getWordsX())
        line = ''
        prev = 0
        for word, start in words:
            line += ' '*((start-prev)/10)+ word
            prev = start
        return line

        
if __name__ == '__main__':
    img = cv2.imread("D:\\AI\\Bonuri\\imgs\\lines\\0.jpg", 0)
    l = Line(0, img.shape[1], img)
    l.analyze()
    l.readLetters()
    print l
    print l.getLine()