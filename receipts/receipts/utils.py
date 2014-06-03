import cv2
import numpy as np

def resize(img, width=None, height=None, method=cv2.INTER_AREA):
    if width is None and height is None:
        raise Exception("It doesn't make sense to resize without giving any dims")
    orig_h, orig_w = img.shape
    if width is None:
        width = height*orig_w/orig_h
    elif height is None:
        height = width*orig_h/orig_w
    print img.shape, height, width
    return cv2.resize(img, (width, height), interpolation=method)

def rotate(img, angle, fixed=True, point=[-1, -1], scale = 1.0):
        """
        Inspired from SimpleCV

        **PARAMETERS**

        * *angle* - angle in degrees positive is clockwise, negative is counter clockwise
        * *point* - the point about which we want to rotate, if none is defined we use the center.
        * *scale* - and optional floating point scale parameter.

        """
        if( point[0] == -1 or point[1] == -1 ):
            point[0] = (img.shape[1]-1)/2
            point[1] = (img.shape[0]-1)/2

        # first we create what we thing the rotation matrix should be
        rotMat = cv2.getRotationMatrix2D((float(point[0]), float(point[1])), float(angle), float(scale))
        if fixed:
            return cv2.warpAffine(img, M=rotMat, dsize=img.shape)

        A = np.array([0, 0, 1])
        B = np.array([img.shape[1], 0, 1])
        C = np.array([img.shape[1], img.shape[0], 1])
        D = np.array([0, img.shape[0], 1])
        #So we have defined our image ABC in homogenous coordinates
        #and apply the rotation so we can figure out the image size
        a = np.dot(rotMat, A)
        b = np.dot(rotMat, B)
        c = np.dot(rotMat, C)
        d = np.dot(rotMat, D)
        #I am not sure about this but I think the a/b/c/d are transposed
        #now we calculate the extents of the rotated components.
        minY = min(a[1], b[1], c[1], d[1])
        minX = min(a[0], b[0], c[0], d[0])
        maxY = max(a[1], b[1], c[1], d[1])
        maxX = max(a[0], b[0], c[0], d[0])
        #from the extents we calculate the new size
        newWidth = np.ceil(maxX-minX)
        newHeight = np.ceil(maxY-minY)
        #now we calculate a new translation
        tX = 0
        tY = 0
        #calculate the translation that will get us centered in the new image
        if( minX < 0 ):
            tX = -1.0*minX
        elif(maxX > newWidth-1 ):
            tX = -1.0*(maxX-newWidth)

        if( minY < 0 ):
            tY = -1.0*minY
        elif(maxY > newHeight-1 ):
            tY = -1.0*(maxY-newHeight)

        #now we construct an affine map that will the rotation and scaling we want with the
        #the corners all lined up nicely with the output image.
        src = np.float32([(A[0], A[1]), (B[0], B[1]), (C[0], C[1])])
        dst = np.float32([(a[0]+tX, a[1]+tY), (b[0]+tX, b[1]+tY), (c[0]+tX, c[1]+tY)])

        rotMat = cv2.getAffineTransform(src, dst)

        #calculate the translation of the corners to center the image
        #use these new corner positions as the input to cvGetAffineTransform
        retVal = cv2.warpAffine(img, rotMat, (img.shape[1], img.shape[0]))
        return retVal

def embiggen(img, size=None, pos=None):
        """ Inspired from SimpleCV"""
        
        if( size == None or size[0] < img.shape[1] or size[1] < img.shape[0] ):
            logger.warning("image.embiggenCanvas: the size provided is invalid")
            return None

        newCanvas = np.zeros(size)
        if pos is None:
            x1, y1 = ((size[0]-img.shape[1])/2), ((size[1]-img.shape[0])/2)
        
        x2, y2 = x1 + img.shape[1], y1 + img.shape[0]
        print x1, x2, y1, y2
        newCanvas[y1:y2, x1:x2] = img
        return newCanvas