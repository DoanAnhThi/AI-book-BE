import os
import io
from typing import List, Optional

from pypdf import PdfWriter, PdfReader


async def merge_pdf_books(pdf_bytes_list: List[bytes], output_filename: Optional[str] = None) -> bytes:
    """
    Merge multiple PDF byte streams into a single PDF.

    Args:
        pdf_bytes_list: List of PDF data in bytes.
        output_filename: Optional output filename when saving to disk. If provided,
            the merged PDF will be saved to the same directory as this module.

    Returns:
        bytes: The merged PDF content.
    """

    if not pdf_bytes_list:
        raise ValueError("pdf_bytes_list must contain at least one PDF stream")

    writer = PdfWriter()

    try:
        for index, pdf_bytes in enumerate(pdf_bytes_list, start=1):
            if not pdf_bytes:
                print(f"Skipping empty PDF at position {index}")
                continue

            reader = PdfReader(io.BytesIO(pdf_bytes))
            for page in reader.pages:
                writer.add_page(page)

        output_stream = io.BytesIO()
        writer.write(output_stream)
        output_stream.seek(0)
        merged_bytes = output_stream.getvalue()

        if output_filename:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            output_path = os.path.join(base_dir, output_filename)
            with open(output_path, "wb") as file:
                file.write(merged_bytes)
            print(f"Merged PDF saved to {output_path}")

        return merged_bytes

    finally:
        # PdfWriter doesn't need explicit closing in newer versions
        pass

