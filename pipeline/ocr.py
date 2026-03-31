from __future__ import annotations

from typing import Iterable, List

import torch
from PIL import Image
from transformers import TrOCRProcessor, VisionEncoderDecoderModel


class CodeOCR:
    """OCR wrapper for transcribing text regions using TrOCR."""

    def __init__(self, model_name: str = "microsoft/trocr-base-handwritten") -> None:
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.processor = TrOCRProcessor.from_pretrained(model_name)
        self.model = VisionEncoderDecoderModel.from_pretrained(model_name).to(
            self.device
        )
        self.model.eval()

    @torch.no_grad()
    def transcribe_regions(self, image, regions: Iterable) -> List[str]:
        """Transcribe a list of cropped regions from a source image."""
        results: List[str] = []

        for region in regions:
            crop = region.crop(image)
            crop_pil = Image.fromarray(crop).convert("RGB")

            # Skip tiny crops that are unlikely to contain readable text
            if crop_pil.width < 10 or crop_pil.height < 5:
                results.append("")
                continue

            pixel_values = self.processor(
                images=crop_pil, return_tensors="pt"
            ).pixel_values.to(self.device)

            generated_ids = self.model.generate(
                pixel_values,
                num_beams=4,
                max_new_tokens=128,
                early_stopping=True,
            )
            text = self.processor.batch_decode(generated_ids, skip_special_tokens=True)[
                0
            ]

            results.append(text.strip())

        return results
