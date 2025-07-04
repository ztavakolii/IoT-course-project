import cv2
from pyzbar.pyzbar import decode
from PIL import Image

def read_qr(image_path):
    try:
        img = cv2.imread(image_path)
        if img is None:
            print(f"Failed to load image: {image_path}")
            return None
        barcodes = decode(img)
        if not barcodes:
            print(f"No QR code detected in image: {image_path}")
            return read_qr_pillow(image_path)
        # Return the first QR code's data
        data = barcodes[0].data.decode('utf-8')
        print(f"Detected QR code: {data}")
        return data
    except Exception as e:
        print(f"Error reading QR code from {image_path}: {str(e)}")
        return None
    
def read_qr_opencv(image_path):
    img = cv2.imread(image_path)
    if img is None:
        return None
    detector = cv2.QRCodeDetector()
    data, points, _ = detector.detectAndDecode(img)
    if points is not None and data:
        print(f"Detected QR code: {data}")
        return data
    print("OpenCV QR detector failed.")
    return None


def read_qr_pillow(image_path):
    try:
        image = Image.open(image_path).convert('RGB')
        barcodes = decode(image)
        if barcodes:
            data = barcodes[0].data.decode('utf-8')
            print(f"[pillow] Detected: {data}")
            return data
        else:
            print("[pillow] No QR detected.")
    except Exception as e:
        print(f"[pillow] Error: {e}")
    return None
