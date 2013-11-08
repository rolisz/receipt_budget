import cPickle
from itertools import tee, izip
import os
from joblib import load
from django.conf import settings
import numpy as np

__author__ = 'Roland'

size = 10

model = load(os.path.join(settings.PICKLE_ROOT, "joblib_seg.jb"))

logistic_model = load(os.path.join(settings.PICKLE_ROOT, "joblib_letter.jb"))

f = open(os.path.join(settings.PICKLE_ROOT, "label_encoder.pkl"), "rb")
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
        self.img = img.resize(h=Line.line_height)
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
                               self.img.resize(w=self.img.width, h=20).getGrayNumpyCv2(),
                               np.zeros((20, size))), axis=1)
        all_black = True
        while i < self.img.width:
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
            self.segments.append((prev, self.img.width - 1))
        self.img = self.img.applyLayers()

    def readLetters(self):
        """
        Character recognition
        """
        self.letters = []
        i = 0
        letters = []
        for begin, end in self.segments:
            lett = self.img.crop(begin - 1, 1, end - begin + 2, self.line_height - 2)   # add a bit of padding to help with
                                                                                # recognition
            self.img.drawRectangle(begin-1, 1, end - begin+2, 28)
            if lett.height > lett.width:
                lett = lett.resize(h=30)
            else:
                lett = lett.resize(w=30)
            if lett.width and lett.height:
                lett = lett.embiggen((30, 30))
                letters.append(lett.getGrayNumpy().transpose().reshape(-1))

        try:
            characters = labels.inverse_transform(logistic_model.predict(letters))
            for charac, segment in zip(characters, self.segments):
                self.letters.append((charac, segment[0], segment[1]))
        except ValueError:
            print(map(lambda x: x.shape, letters))
        self.img = self.img.applyLayers()

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
