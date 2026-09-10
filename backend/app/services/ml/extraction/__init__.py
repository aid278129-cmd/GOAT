"""ML Extraction Subpackage."""

from backend.app.services.ml.extraction.product_attributes import (
    product_attribute_extractor,
    ProductAttributeExtractor,
)

__all__ = ["product_attribute_extractor", "ProductAttributeExtractor"]
