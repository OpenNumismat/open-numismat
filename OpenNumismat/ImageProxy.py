class ImageProxy():

    def __init__(self):
        self._current = None
        self._images = []

    def images(self):
        return self._images

    def setImages(self, images):
        self._images = images

    def append(self, image):
        self._images.append(image)

    def currentImage(self):
        for image in self._images:
            if image.field == self._current:
                return image

    def setCurrent(self, field):
        self._current = field

    def imageSaved(self, image):
        self.currentImage().imageSaved(image)
