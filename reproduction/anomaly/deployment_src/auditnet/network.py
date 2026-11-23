"""EfficientAD-S PDN (384/768 channels) and feature autoencoder.

Layer declarations adapted from nelson1425/EfficientAD common.py (Apache-2.0),
revision fcab5146f84ae17597044ad5ddf1656ccf805401. Not an authors' official release.
Changes: static rectangular-size extension, normalization buffers, strict loading.
At 256x256 these layer definitions match upstream_reference.py exactly.
"""
import torch
from torch import nn
import torch.nn.functional as F
from .upstream_reference import get_pdn_small, get_autoencoder


class FeatureAutoencoder(nn.Module):
    def __init__(self, image_size=(256, 256)):
        super().__init__()
        self.image_size = tuple(image_size)
        self.net = get_autoencoder(384)
        # Canonical encoder always sees 256x256, retaining its 64x1x1 bottleneck.
        # Noncanonical resolutions are explicitly documented deployment extensions.
        if self.image_size != (256, 256):
            h, w = self.image_size
            # Final PDN feature grid for unpadded convolutions: H/4 - 8.
            self.net[35] = nn.Upsample(size=(h // 4 - 8, w // 4 - 8), mode="bilinear", align_corners=False)

    def forward(self, x):
        if self.image_size != (256, 256):
            x = F.interpolate(x, (256, 256), mode="bilinear", align_corners=False)
        return self.net(x)


class EfficientAD(nn.Module):
    def __init__(self, image_size=(256, 256), teacher_weights=None):
        super().__init__()
        self.teacher = get_pdn_small(384)
        self.student = get_pdn_small(768)
        self.autoencoder = FeatureAutoencoder(image_size)
        self.register_buffer("teacher_mean", torch.zeros(1, 384, 1, 1))
        self.register_buffer("teacher_std", torch.ones(1, 384, 1, 1))
        if teacher_weights:
            self.load_teacher(teacher_weights)
        self.teacher.requires_grad_(False)
        self.teacher.eval()

    def load_teacher(self, path):
        state = torch.load(path, map_location="cpu", weights_only=True)
        # Anomalib release uses named conv1..conv4; its PDN convs match upstream.
        if "conv1.weight" in state:
            mapping = {"conv1": "0", "conv2": "3", "conv3": "6", "conv4": "8"}
            state = {mapping[k.split('.')[0]] + '.' + k.split('.', 1)[1]: v for k, v in state.items()}
        self.teacher.load_state_dict(state, strict=True)

    def train(self, mode=True):
        super().train(mode)
        self.teacher.eval()
        return self

    def normalized_teacher(self, x):
        with torch.no_grad():
            return (self.teacher(x).float() - self.teacher_mean) / self.teacher_std

    def forward(self, x):
        return self.normalized_teacher(x), self.student(x), self.autoencoder(x)


def raw_maps(outputs):
    teacher, student, ae = outputs
    return torch.cat(((teacher.float() - student[:, :384].float()).square().mean(1, keepdim=True),
                      (ae.float() - student[:, 384:].float()).square().mean(1, keepdim=True)), 1)
