from cv2 import cv2
import pytesseract
import numpy as np
import glob
from pathlib import Path
from preprocessing import preprocessing
from preprocessing import preprocessing_front
from preprocessing import preprocessing_threshadjust


def readData(processed, config):
    boxes = pytesseract.image_to_data(processed, lang='deu', config='config')
    allData = []
    for x, b in enumerate(boxes.splitlines()):
        if x != 0:
            b = b.split()
            if len(b) == 12:
                allData.append(b[11])
                (x, y, w, h) = int(b[6]), int(b[7]), int(b[8]), int(b[9])
                cv2.rectangle(processed, (x, y), (w+x, h+y), (0, 0, 255), 3)
    return allData

def hasDigit(string):
    return any(48 <= ord(char) <= 57 for char in string)

def front(img):
    # Pytesseract
    pytesseract.pytesseract.tesseract_cmd = '/usr/local/bin/tesseract'
    imgUrl = img
    img = cv2.imread(imgUrl)
    config = '--psm 6 --oem 3 -c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyzüöäABCDEFGHIJKLMNOPQRSTUVWXYZÜÖÄ tessedit_char_blacklist=1234567890'

    # PREPROCESSING: DOCUMENT SCANNER
    processed, success = preprocessing(imgUrl)

    # Gebe die Bounding Boxen zurück mit den einzelnen Zeilen
    if success:
        processed = preprocessing_front(processed)
        # DETECTING WORDS AND DATA
        allData = readData(processed, config)

        ### TRY TO REREAD IMAGE AND FINE TUNE IMAGE 3 TIMES
        i = 0
        while len(allData) <= 0 and i < 3:
            processed = preprocessing_threshadjust(processed)
            allData = readData(processed,config)
            i += 1

        ### IF NOT ENOUGH IS DETECTED ###
        if len(allData) <= 0:
            print("Image could not be processed")
            return []
        else:
            ### Find all in first line with similar Y Coordinatess
            couldBeInsurance = []
            for d in allData:
                if hasDigit(d) == False:
                    if d != 'Versichertennummer' and d != 'Versicherung' and len(d) > 2:
                        couldBeInsurance.append(d)
            if len(couldBeInsurance) > 0:
                return couldBeInsurance
            else:
                return []
    ### Everything that is in the lower half of the picture has to be seen separately
    else:
        print("Noch mal probieren, Lesen fehlgeschlagen")
        return []

