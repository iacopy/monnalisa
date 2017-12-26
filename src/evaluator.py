import numpy as np
from PIL import Image


def resized(image, max_size):
    w, h = image.size
    div = max(w, h) / max_size
    resize = image.size
    if div > 1:
        resize = int(w / div), int(h / div)
        print('Resizing/{} -> {}'.format(div, max_size))
    return image.resize(resize)


class ImageEvaluator:
    def __init__(self, target_image, target_image_mode='RGB', resize=128):
        im = Image.open(target_image).convert(target_image_mode)
        im = resized(im, resize)
        im.save(target_image)
        # TODO: make a copy of the original
        self.target_filepath = target_image
        self.target_image = im
        self.target_image_mode = target_image_mode
        self.target_size = im.size
        self.target_arr = np.asarray(im.getdata())
        self.n_data = len(self.target_arr)
        # Create here, one time, the numpy array, whose the creation is the bottleneck
        self.candidate_arr = np.zeros(self.target_arr.shape, np.uint8)

    def evaluate(self, image):
        """Mean Squared Error
        """
        self.candidate_arr[:] = image.getdata()
        return ((self.target_arr - self.candidate_arr) ** 2).sum()


def func_evaluate(shapes_encoder, evaluator, genome):
    """Utility function."""
    phenotype = shapes_encoder.draw(genome)
    evaluation = evaluator.evaluate(phenotype)
    return dict(genome=genome, phenotype=phenotype, evaluation=evaluation)
