import cv2
from pyzbar.pyzbar import decode

def read_qr(image_path):
    img = cv2.imread(image_path)
    if img is None:
        print("Could not load image")
        return False

    barcodes = decode(img)
    if not barcodes:
        print("No QR code detected")
        return False

    for barcode in barcodes:
        data = barcode.data.decode('utf-8')
        print("Detected QR:", data)
        return data
