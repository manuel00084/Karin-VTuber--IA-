import cv2
import numpy as np

class ImagePreprocessor:
    def __init__(self):
        self.zoom = 1.0
        self.threshold = 0
        self.erode = False
        self.rgb_filter = None
        self.hsv_filter = None

    def set_rgb_filter(self, r_min=0, r_max=255, g_min=0, g_max=255, b_min=0, b_max=255):
        self.rgb_filter = (r_min, r_max, g_min, g_max, b_min, b_max)

    def set_hsv_filter(self, h_min=0, h_max=179, s_min=0, s_max=255, v_min=0, v_max=255):
        self.hsv_filter = (h_min, h_max, s_min, s_max, v_min, v_max)

    def clear_filters(self):
        self.rgb_filter = None
        self.hsv_filter = None

    def process(self, img):
        if img is None:
            return None
        result = img.copy()

        if self.zoom != 1.0:
            h, w = result.shape[:2]
            nh, nw = int(h * self.zoom), int(w * self.zoom)
            result = cv2.resize(result, (nw, nh), interpolation=cv2.INTER_CUBIC)

        if self.rgb_filter:
            r_min, r_max, g_min, g_max, b_min, b_max = self.rgb_filter
            mask = cv2.inRange(result, np.array([b_min, g_min, r_min]), np.array([b_max, g_max, r_max]))
            result = cv2.bitwise_and(result, result, mask=mask)

        if self.hsv_filter:
            hsv = cv2.cvtColor(result, cv2.COLOR_BGR2HSV)
            h_min, h_max, s_min, s_max, v_min, v_max = self.hsv_filter
            mask = cv2.inRange(hsv, np.array([h_min, s_min, v_min]), np.array([h_max, s_max, v_max]))
            result = cv2.bitwise_and(result, result, mask=mask)

        if self.threshold > 0:
            gray = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
            _, result = cv2.threshold(gray, self.threshold, 255, cv2.THRESH_BINARY)
            result = cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)

        if self.erode:
            kernel = np.ones((2, 2), np.uint8)
            result = cv2.erode(result, kernel, iterations=1)

        return result

    def process_for_ocr(self, img):
        h, w = img.shape[:2]
        up = cv2.resize(img, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)
        gray = cv2.cvtColor(up, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (0, 0), 15)
        norm = cv2.divide(gray, blur, scale=255)
        lab = cv2.cvtColor(cv2.cvtColor(norm, cv2.COLOR_GRAY2BGR), cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        contrast = cv2.merge([l, a, b])
        contrast = cv2.cvtColor(contrast, cv2.COLOR_LAB2BGR)
        gray2 = cv2.cvtColor(contrast, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray2, (0, 0), 1.0)
        sharpened = cv2.addWeighted(gray2, 1.8, blurred, -0.8, 0)
        return cv2.cvtColor(sharpened, cv2.COLOR_GRAY2BGR)
