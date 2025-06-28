import cv2
from pyzbar.pyzbar import decode

def read_qr(image_path):
    img = cv2.imread(image_path)
    detected_barcodes = decode(img)

    if not detected_barcodes:
        print("QR Code wasn't found")
        return False
        
    else:
        for barcode in detected_barcodes:
            data = barcode.data.decode('utf-8')
            print("QR Code data:", data)
            return data

