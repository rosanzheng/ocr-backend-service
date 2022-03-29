import cv2
import numpy as np
import imutils

### PREPROCESSING WITH EDGE DETECTION ####


def preprocessing(img_path):
    ########################################################################
    img = cv2.imread(img_path)
    heightImg, widthImg, _ = img.shape
    img = imutils.resize(img, height=500)
    ########################################################################

    # CONVERT TO GRAY SCALE, ADD BLUR, ADD CANNY
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blur, 75, 200)

    # FIND ALL CONTOURS
    edgedCopy = edged.copy()
    cnts, _ = cv2.findContours(
        edgedCopy, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # FIND BIGGEST BOUNDING RECTANGLE
    maxRect = 0
    (xMax, yMax, wMax, hMax) = (0, 0, 0, 0)
    for c in cnts:
        (x, y, w, h) = cv2.boundingRect(c)
        rectArea = w*h
        if(rectArea > maxRect):
            maxRect = rectArea
            (xMax, yMax, wMax, hMax) = (x, y, w, h)

    # CALCULATE RATIO OF FOUND TRIANGLE
    # -> IF RATIO DOES NOT FIT THEN THE CARD WAS NOT FOUND CORRECTLY
    ratioEGK = 53.98 / 85.6  # Height / Width of health card = 0.6306
    ratioREC = hMax / wMax  # Height / Width of discovered rectangle

    # CHOOSING VARIANZ BETWEEN 0.05
    if ratioREC <= (ratioEGK + 0.05) and ratioREC >= (ratioEGK - 0.05):
        ### Only the bottom third of the image contains relevant information ###
        hMaxCropped = int(hMax / 3)
        newY = (2 * hMaxCropped)
        newW = 4 * int(wMax / 5)
        crop_img = img[yMax:yMax+hMax, xMax:xMax+wMax].copy()
        crop_img = cv2.cvtColor(crop_img, cv2.COLOR_BGR2GRAY)

        return crop_img, True
    else:
        print("Karte nicht erkannt")
        return img, False


def preprocessing_front(image):
    img = image
    height, width = img.shape
    # CROP IMAGE TO NECESSARY PART
    hMaxCropped = int(height / 3)
    newY = (2 * hMaxCropped)
    newW = 4 * int(width / 5)
    crop_img = img[newY:height, 0:newW]
    return crop_img


def preprocessing_threshadjust(image):
    ### ADD SHARPENING FILTER IF NOT ENOUGH IS RECOGNIZED ###
    # SHARPENING FILTER FOR BETTER OCR
    sharpening_filter = np.array([[-1, -1, -1],
                                  [-1, 9, -1],
                                  [-1, -1, -1]])
    crop_img = cv2.filter2D(image, -1, sharpening_filter)

    return image

def preprocessing_back(image, cardDetected):
    # READ AND CROP IMAGE FOR IF CARD SHAPE WAS DETECTED
    # OTHERWISE JUST USE THE WHOLE IMAGE AND TRY TO FIND THE DATA
    crop_img = []
    if cardDetected:
        img = image.copy()
        height, width = img.shape
        hMaxCropped = int(height / 2)
        crop_img = img[hMaxCropped:height, 0:width]
    else:
        crop_img = image.copy()

    blur = cv2.GaussianBlur(crop_img, (5, 5), 0)
    edged = cv2.Canny(blur, 75, 200)

    
    # FIND EDGES TO DETECT THE LINES WHERE DATA IS PROVIDED
    edgedCopy = edged.copy()
    cnts, _ = cv2.findContours(
        edgedCopy, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # FIND ALL BOUNDING RECTANGLES AND DETERMINE MAX WIDTH
    allRectangles = []
    maxWidth = 0
    # RATIO: 79,6/4 = BREITE / HÖHE
    ratioRectangle = 19.9 # RATIO BETWEEN WIDTH AND HEIGHT OF THE RECTANGLE
    for c in cnts:
        (x, y, w, h) = cv2.boundingRect(c)
        allRectangles.append((x, y, w, h))
        ratio = w / h
        if w > maxWidth and ratio >= (15) and ratio <= 25:
            maxWidth = w

    # NOW WE FIND THE  RECTANGLES WITH THE HIGHEST WIDTH
    recData = []
    for r in allRectangles:
        (x,y,w,h) = r
        if r[2] <= maxWidth and r[2] >= (maxWidth - 10):
            #cv2.rectangle(crop_img, (x, y), (x+w, y+h), (255,0,0), 2 )
            recData.append(r)

    # RETURN ARRAY OF RECS AND THE CROPPED IMAGE FOR PROCESSING
    if (len(recData) == 4):
        print("Alle Daten gefunden")
        
        # SORT RECTANGLES BY HEIGHT-POSITION (TOP REC COMES FIRST)
        n = len(recData)
        for i in range(n):
            already_sorted = True
            for j in range(n - i - 1):
                if recData[j][1] > recData[j + 1][1]:
                    recData[j], recData[j+1] = recData[j+1], recData[j]
                    already_sorted = False
            if already_sorted:
                break

        return crop_img, recData
    elif (len(recData) > 4):
        print("Zu viel bzw. zu wenig erkannt")
        return crop_img, []
    else:
        print("zu wenig erkannt")
        return crop_img, []
    