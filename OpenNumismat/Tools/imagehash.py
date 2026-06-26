import imagehash
from PIL import Image


def image_hash(pil_image, method):
    # Squaring
    if method != 'crop_resistant_hash':
        w, h = pil_image.size
        if w > h:
            offset = (w - h) // 2
            pil_image = pil_image.crop((offset, 0, w - offset, h))
        else:
            offset = (h - w) // 2
            pil_image = pil_image.crop((0, offset, w, h - offset))

    # Resize
    # pil_image = pil_image.resize((256, 256), Image.Resampling.LANCZOS)

    # Filter
    if method == 'phash_orb':
        pil_image = _img2orientedBRIEF(pil_image)

    # Compute hash
    if method == 'ahash':
        return imagehash.average_hash(pil_image)
    elif method == 'phash' or method == 'phash_orb':
        return imagehash.phash(pil_image)
    elif method == 'dhash':
        return imagehash.dhash(pil_image)
    # elif method == 'whash':
    #     return imagehash.whash(pil_image)
    # elif method == 'colorhash':
    #     return imagehash.colorhash(pil_image)
    elif method == 'crop_resistant_hash':
        return imagehash.crop_resistant_hash(pil_image)


def int2hash(hash_int):
    # Convert the signed int64 to an unsigned 64-bit integer
    unsigned_uint64 = hash_int & 0xFFFFFFFFFFFFFFFF

    # Format as a 16-character, zero-padded hex string
    hex_str = f"{unsigned_uint64:016x}"

    # Convert hex string back to an ImageHash object
    return imagehash.hex_to_hash(hex_str)


def _img2orientedBRIEF(image, nfeatures=2000):
    import cv2
    import numpy as np

    if isinstance(image, Image.Image):  # convert PIL to cv2
        image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

    if len(image.shape) == 3:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # https://www.geeksforgeeks.org/feature-detection-and-matching-with-opencv-python/
    orb = cv2.ORB_create(nfeatures=nfeatures)
    kp = orb.detect(image)

    height, width = image.shape
    img = np.zeros([height, width, 1], dtype=np.uint8)
    img.fill(255)

    # Drawing the keypoints
    if width <= 512:
        for i in kp:
            x = int(i.pt[0])
            y = int(i.pt[1])
            cv2.circle(img, (x, y), 2, (0, 0, 255), -1)
    else:
        img = cv2.drawKeypoints(img, kp, 0, color=(0, 255, 0))

    image = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))  # convert cv2 to PIL
    return image
