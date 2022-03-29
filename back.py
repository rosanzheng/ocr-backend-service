from cv2 import cv2
import pytesseract
import numpy as np
import glob
from pathlib import Path
from preprocessing import preprocessing
from preprocessing import preprocessing_back
from preprocessing import preprocessing_threshadjust

def readData(processed, configTess, array):
    boxes = pytesseract.image_to_data(processed, config=configTess)
    insuranceArray = []
    for x, b in enumerate(boxes.splitlines()):
        if x != 0:
            b = b.split()
            if len(b) == 12:
                (x, y, w, h) = int(b[6]), int(b[7]), int(b[8]), int(b[9])
                if array:
                    insuranceArray.append(b[11])
                else:
                    return b[11]
    if array:
        return insuranceArray
    else:
        return ""

def hasDigit(string):
    return any(48 <= ord(char) <= 57 for char in string)

def back(img):
    # Pytesseract
    pytesseract.pytesseract.tesseract_cmd = '/usr/local/bin/tesseract'
    imgUrl = img
    img = cv2.imread(imgUrl)

    # PREPROCESSING: DOCUMENT SCANNER
    processed, success = preprocessing(imgUrl)
    # Gebe die Bounding Boxen zurück mit den einzelnen Zeilen
    crop_img, rectangles = preprocessing_back(processed, success)
    if len(rectangles) > 0:
        # Split image into 4 rectangles:
        name = crop_img[rectangles[0][1]:(rectangles[0][1] - 5)+rectangles[0][3]+10, rectangles[0][0]:rectangles[0][0]+int (rectangles[0][2] / 2)].copy()
        surname = crop_img[rectangles[1][1]:rectangles[1][1]+rectangles[1][3], rectangles[1][0]:rectangles[1][0]+ int (rectangles[1][2] / 2)].copy()
        birthDate = crop_img[rectangles[1][1]:rectangles[1][1]+rectangles[1][3], rectangles[1][0] + int (rectangles[1][2] / 2): rectangles[1][0]+int (rectangles[1][2])].copy()
        personalId = crop_img[rectangles[2][1]:rectangles[2][1]+rectangles[2][3], rectangles[2][0]:rectangles[2][0]+int (rectangles[2][2] / 2)].copy()
        carrierId = crop_img[rectangles[2][1]:rectangles[2][1]+rectangles[2][3], rectangles[2][0] + int (rectangles[2][2] / 2): rectangles[2][0]+int (rectangles[2][2])].copy()
        cardId = crop_img[rectangles[3][1]:rectangles[3][1]+rectangles[3][3], rectangles[3][0]:rectangles[3][0]+int (rectangles[3][2] / 2)].copy()
        expirationDate = crop_img[rectangles[3][1]:rectangles[3][1]+rectangles[3][3], rectangles[3][0] + int (rectangles[3][2] / 2): rectangles[3][0]+int (rectangles[3][2])].copy()
        
        # Add Sharpen Filter on each image:
        name = preprocessing_threshadjust(name)
        surname = preprocessing_threshadjust(surname)
        birthDate = preprocessing_threshadjust(birthDate)
        personalId = preprocessing_threshadjust(personalId)
        carrierId = preprocessing_threshadjust(carrierId)
        cardId = preprocessing_threshadjust(cardId)
        expirationDate = preprocessing_threshadjust(expirationDate)

        # READ DATA
        config = '--psm 7 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZÄÜÖ'
        name = readData(name, config, False)

        config = '--psm 7 --oem 3 -c tessedit_char_blacklist=1234567890'
        surname = readData(surname, config, False)

        config = '--psm 7 --oem 3 -c tessedit_char_whitelist=1234567890/'
        birthDate = readData(birthDate, config, False)

        config = '--psm 7 --oem 3 -c tessedit_char_whitelist=1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        personalId = readData(personalId, config, False)

        config = '--psm 7 --oem 3 -c tessedit_char_whitelist=1234567890'
        carrierIdString = readData(carrierId, config, False)

        config = '--psm 7 --oem 3'
        insurance = readData(carrierId, config, True)
        insuranceString = ""
        for i in insurance:
            if not('-' in i) and not(hasDigit(i)):
                insuranceString += i + " "

        cardId = readData(cardId, config, False)

        config = '--psm 7 --oem 3 -c tessedit_char_whitelist=1234567890/'
        expirationDate = readData(expirationDate, config, False)
        return [name, surname, birthDate, personalId, carrierIdString, insuranceString, cardId, expirationDate]
    else:
        print("Rückseite konnte nicht gelesen werden, keine Karte erkannt")
        return []