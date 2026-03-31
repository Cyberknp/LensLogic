from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

import cv2
import numpy as np


@dataclass
class TextRegion:
    x: int
    y: int
    width: int
    height: int
    confidence: float

    def crop(self, image: np.ndarray) -> np.ndarray:
        return image[self.y : self.y + self.height, self.x : self.x + self.width]


class TextDetector:
    """EAST-based text detector with decode + NMS helpers."""

    def __init__(
        self,
        confidence_threshold: float = 0.5,
        nms_threshold: float = 0.4,
        model_path: str | Path = "models/frozen_east_text_detection.pb",
    ) -> None:
        self.confidence_threshold = confidence_threshold
        self.nms_threshold = nms_threshold

        model_path = Path(model_path)
        if not model_path.exists():
            raise FileNotFoundError(f"EAST model not found at: {model_path}")

        self.net = cv2.dnn.readNet(str(model_path))
        self.output_layers = [
            "feature_fusion/Conv_7/Sigmoid",
            "feature_fusion/concat_3",
        ]

    def detect(self, image: np.ndarray) -> List[TextRegion]:
        orig_h, orig_w = image.shape[:2]
        new_w = max(32, (orig_w // 32) * 32)
        new_h = max(32, (orig_h // 32) * 32)
        ratio_w, ratio_h = orig_w / new_w, orig_h / new_h

        blob = cv2.dnn.blobFromImage(
            image,
            1.0,
            (new_w, new_h),
            (123.68, 116.78, 103.94),
            swapRB=True,
            crop=False,
        )
        self.net.setInput(blob)
        scores, geometry = self.net.forward(self.output_layers)

        regions = self._decode_predictions(scores, geometry, ratio_w, ratio_h)
        regions = self._nms(regions)
        return sorted(regions, key=lambda r: (r.y // 20, r.x))

    def _decode_predictions(
        self,
        scores: np.ndarray,
        geometry: np.ndarray,
        ratio_w: float,
        ratio_h: float,
    ) -> List[TextRegion]:
        num_rows, num_cols = scores.shape[2:4]
        regions: List[TextRegion] = []

        for y in range(num_rows):
            scores_data = scores[0, 0, y]
            x_data0 = geometry[0, 0, y]
            x_data1 = geometry[0, 1, y]
            x_data2 = geometry[0, 2, y]
            x_data3 = geometry[0, 3, y]
            angles_data = geometry[0, 4, y]

            for x in range(num_cols):
                score = float(scores_data[x])
                if score < self.confidence_threshold:
                    continue

                offset_x = x * 4.0
                offset_y = y * 4.0
                angle = angles_data[x]
                cos = np.cos(angle)
                sin = np.sin(angle)

                h = x_data0[x] + x_data2[x]
                w = x_data1[x] + x_data3[x]

                end_x = offset_x + (cos * x_data1[x]) + (sin * x_data2[x])
                end_y = offset_y - (sin * x_data1[x]) + (cos * x_data2[x])
                start_x = end_x - w
                start_y = end_y - h

                # Scale back to original image size
                start_x = int(start_x * ratio_w)
                start_y = int(start_y * ratio_h)
                end_x = int(end_x * ratio_w)
                end_y = int(end_y * ratio_h)

                regions.append(
                    TextRegion(
                        x=start_x,
                        y=start_y,
                        width=max(0, end_x - start_x),
                        height=max(0, end_y - start_y),
                        confidence=score,
                    )
                )

        return regions

    def _nms(self, regions: List[TextRegion]) -> List[TextRegion]:
        if not regions:
            return []

        boxes = [[r.x, r.y, r.width, r.height] for r in regions]
        confidences = [float(r.confidence) for r in regions]

        indices = cv2.dnn.NMSBoxes(
            boxes=boxes,
            scores=confidences,
            score_threshold=self.confidence_threshold,
            nms_threshold=self.nms_threshold,
        )

        if len(indices) == 0:
            return []

        # indices can be [[i], [j], ...] or a flat list depending on OpenCV
        kept = []
        for idx in indices.flatten():
            kept.append(regions[int(idx)])

        return kept
