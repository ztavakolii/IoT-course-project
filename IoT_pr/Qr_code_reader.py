import cv2
from pyzbar.pyzbar import decode

def read_qr(image_path):
    try:
        img = cv2.imread(image_path)
        if img is None:
            print(f"Failed to load image: {image_path}")
            return None
        barcodes = decode(img)
        if not barcodes:
            print(f"No QR code detected in image: {image_path}")
            return None
        # Return the first QR code's data
        data = barcodes[0].data.decode('utf-8')
        print(f"Detected QR code: {data}")
        return data
    except Exception as e:
        print(f"Error reading QR code from {image_path}: {str(e)}")
        return None