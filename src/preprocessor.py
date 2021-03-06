import matplotlib.pyplot as plt
import numpy as np
from abc import ABC
from math import ceil
from typing import List, Tuple, Union
from sklearn.cluster import DBSCAN


class Preprocessor(ABC):
    def __call__(self, x: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        raise NotImplementedError

    def export_figure(self, x: np.ndarray, y: np.ndarray):
        new_x, new_y = self(x, y)
        plt.figure()
        plt.title(self.__class__.__name__)
        plt.scatter(x, y, s=10, c="gray", label="Original Samples")
        plt.scatter(new_x, new_y, s=5, c="red", label="Transformed Samples")
        plt.legend()
        plt.xlabel("x")
        plt.ylabel("y")
        plt.savefig(self.__class__.__name__)
        plt.close()


class NullPreprocessor(Preprocessor):
    def __call__(self, x: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        return x, y


class KernelPreprocessor(Preprocessor):
    def __init__(self, kernel_size: Union[float, Tuple[float, float]], strides: Union[float, Tuple[float, float]], threshold: float):
        # The kernel preprocessor is inspired by the kernels in neural networks (NN)
        # kernel_size and strides function in the exact same ways as they do in NN kernels
        # padding in NN kernels is always set to kernel_size in this kernel preprocessor
        # threshold is the minimum proportion of samples required in a kernel for it to generate a combined sample
        try:
            self.kernel_size: Tuple[float, float] = kernel_size[0:2]
        except TypeError:
            self.kernel_size: Tuple[float, float] = (kernel_size, kernel_size)
        try:
            self.strides: Tuple[float, float] = strides[0:2]
        except TypeError:
            self.strides: Tuple[float, float] = (strides, strides)
        self.threshold: float = threshold

    def combine(self, samples: List[Tuple[float, float]]) -> Union[Tuple[float, float], None]:
        raise NotImplementedError

    def __call__(self, x: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        kernels = dict()
        for xi, yi in zip(x, y):
            ix_low = ceil((xi - x.min()) / self.strides[0])
            ix_high = int((xi - (x.min() - self.kernel_size[0])) / self.strides[0])
            iy_low = ceil((yi - y.min()) / self.strides[1])
            iy_high = int((yi - (y.min() - self.kernel_size[1])) / self.strides[1])
            for ix in range(ix_low, ix_high + 1):
                for iy in range(iy_low, iy_high + 1):
                    try:
                        kernels[(ix, iy)].append((xi, yi))
                    except KeyError:
                        kernels[(ix, iy)] = [(xi, yi)]
        new_x = list()
        new_y = list()
        self.threshold_size = ceil(x.shape[0] * self.threshold)
        for key in kernels:
            try:
                _x, _y = self.combine(kernels[key])
            except TypeError:
                continue
            new_x.append(_x)
            new_y.append(_y)
        del self.threshold_size
        return np.array(new_x), np.array(new_y)


class MeanKernelPreprocessor(KernelPreprocessor):
    def combine(self, samples: List[Tuple[float, float]]) -> Union[Tuple[float, float], None]:
        if len(samples) < self.threshold_size:
            return None
        sum_x = 0
        sum_y = 0
        for x, y in samples:
            sum_x += x
            sum_y += y
        return sum_x / len(samples), sum_y / len(samples)


class ClusteringPreprocessor(Preprocessor):
    def __init__(self, mode, eps, min_samples):
        self.mode = mode
        self.eps = eps
        self.min_samples = min_samples

    def __call__(self, x: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        if self.mode == "DBSCAN":
            X = np.c_[x, y]
            clustering = DBSCAN(eps=self.eps, min_samples=self.min_samples).fit(X)
            index = np.where(clustering.labels_ != -1)
            new_x = np.delete(x, index)
            new_y = np.delete(y, index)
            return np.array(new_x), np.array(new_y)