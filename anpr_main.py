import cv2, imutils, easyocr, os
from matplotlib import pyplot as plt
import numpy as np

DETECTED_FOLDER = 'static'
os.makedirs(DETECTED_FOLDER, exist_ok=True)

def anpr_processing(img):
    try:
        text, converted_img_path, message = None, None, None
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # kernal size and default sigma x
        gblur = cv2.GaussianBlur(gray, (5,5), 0)
        
        # threshold lower, upper
        edged = cv2.Canny(gblur, 30, 200)

        #shallow copy, tree form gives levels of contour, approximately how they look
        keypoints = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        contours = imutils.grab_contours(keypoints)
        
        #get first 10 by contour area
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]
        
        location = None
        for contour in contours:
            
            # approximate the polygon of our contours, 10 as the rough estimation (gets higher with the no.) of being a rectangle
            # 10 tells how fine and accurate our approximation be, if we have high dents it's gonna round off
            approx = cv2.approxPolyDP(contour, 10, True)
            
            # if our approximation has 4 keypoints - rectangle
            if len(approx) == 4:
                # coordinates
                location = approx
                break

        # masking        
        # 2D shape by gray image of empty mask and how to fill it in (blank zeros)
        mask = np.zeros(gray.shape, np.uint8)
        
        
        if location is not None:
            # on location 255 with bitwise and gives the same, others = 0 with bitwise and gives black, draw all contours = -1
            new_image = cv2.drawContours(mask, [location], 0, 255, -1)
            
            # overlay the mask and gets segment of the image
            new_image = cv2.bitwise_and(img, img, mask=mask)
            
            x, y = np.where(mask==255)
            x1, y1 = np.min(x), np.min(y)
            x2, y2 = np.max(x), np.max(y)
            cropped_img = gray[x1:x2 + 1, y1:y2 + 1]
            
            # pass the language
            reader = easyocr.Reader(['en'])
            result = reader.readtext(cropped_img)
            print(result)
            
            if result:
                text = result[0][-2]
                print('Number Plate: ', text)
                
                font = cv2.FONT_HERSHEY_SIMPLEX
                print(approx)
                res = cv2.putText(img, text=text, org=(approx[0][0][0], approx[1][0][1] + 40), fontFace=font, fontScale=0.8, color=(0, 255, 0), thickness=2, lineType=cv2.LINE_AA)
                
                # draw rectangle
                res = cv2.rectangle(img, tuple(approx[0][0]), tuple(approx[2][0]), (0, 255, 0), 2)
                converted_img_path = os.path.join(DETECTED_FOLDER, 'converted_img.jpg')
                cv2.imwrite(converted_img_path, cv2.cvtColor(res, cv2.COLOR_BGR2RGB))
            else:
                message = 'The number plate is not extractable'
        else:
            message = 'No number plates has been detected'
    
    except:
        message = "Error"

    return {'text': text, 'converted_img_path': converted_img_path, 'message': message}


def anpr_processing2(img):
    return {'result': 'IZA-6106', 'converted_img_path': '/static/images/logo2.png', 'message': None}
        

if __name__ == "__main__":
    img = cv2.imread('static\images\HPIM0809.JPG')
    anpr_processing(img)