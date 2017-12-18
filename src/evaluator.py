import os

import numpy as np
from PIL import Image


class ImageEvaluator:
    def __init__(self, target_image, target_image_mode='RGB'):
        im = Image.open(target_image).convert(target_image_mode)
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


def evaluate(polygons_encoder, evaluator, genome):
    """Utility function."""
    phenotype = polygons_encoder.draw(genome)
    evaluation = evaluator.evaluate(phenotype)
    return dict(genome=genome, phenotype=phenotype, evaluation=evaluation)
