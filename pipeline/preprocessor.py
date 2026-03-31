from __future__ import annotations

import cv2
import numpy as np


class ImagePreprocessor:
    """Preprocess images for downstream OCR / detection.

    Pipeline:
        1) Grayscale
        2) Denoise
        3) Deskew
        4) Adaptive binarization
    """

    def process(self, image: np.ndarray) -> np.ndarray:
        """Run the full preprocessing pipeline."""
        gray = self._to_grayscale(image)
        denoised = self._denoise(gray)
        deskewed = self._deskew(denoised)
        binary = self._binarize(deskewed)
        return binary

    def _to_grayscale(self, img: np.ndarray) -> np.ndarray:
        if len(img.shape) == 3:
            return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        return img

    def _denoise(self, img: np.ndarray) -> np.ndarray:
        return cv2.fastNlMeansDenoising(
            img, h=10, templateWindowSize=7, searchWindowSize=21
        )

    def _deskew(self, img: np.ndarray) -> np.ndarray:
        edges = cv2.Canny(img, 50, 150, apertureSize=3)
        lines = cv2.HoughLinesP(
            edges,
            1,
            np.pi / 180,
            100,
            minLineLength=100,
            maxLineGap=10,
        )
        if lines is None:
            return img

        angles = [
            np.degrees(np.arctan2(y2 - y1, x2 - x1))
            for x1, y1, x2, y2 in lines[:, 0]
            if abs(np.degrees(np.arctan2(y2 - y1, x2 - x1))) < 45
        ]
        if not angles:
            return img

        median_angle = np.median(angles)
        if abs(median_angle) < 0.5:
            return img

        h, w = img.shape[:2]
        M = cv2.getRotationMatrix2D((w // 2, h // 2), median_angle, 1.0)
        return cv2.warpAffine(
            img,
            M,
            (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE,
        )

    def _binarize(self, img: np.ndarray) -> np.ndarray:
        return cv2.adaptiveThreshold(
            img,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            blockSize=35,
            C=11,
        )
