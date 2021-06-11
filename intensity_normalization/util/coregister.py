# -*- coding: utf-8 -*-
"""
intensity-normalization.util.coregister

Author: Jacob Reinhold (jcreinhold@gmail.com)
Created on: Jun 03, 2021
"""

__all__ = [
    "register",
    "Registrator",
]

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, Namespace
import logging
from typing import List, Optional

from intensity_normalization.parse import CLI, file_path, save_nifti_path
from intensity_normalization.type import (
    allowed_interpolators,
    allowed_transforms,
    NiftiImage,
    PathLike,
)


try:
    import ants
except (ModuleNotFoundError, ImportError):
    logging.warning("ANTsPy not installed. Install antspyx to use co-registration.")
    raise


def register(
    image: NiftiImage,
    template: Optional[NiftiImage] = None,
    type_of_transform: str = "Affine",
    interpolator: str = "bSpline",
    initial_rigid: bool = True,
) -> NiftiImage:
    if template is None:
        standard_mni = ants.get_ants_data("mni")
        template = ants.image_read(standard_mni)
    else:
        template = ants.from_nibabel(template)
    image = ants.from_nibabel(image)
    if initial_rigid:
        transforms = ants.registration(
            fixed=template, moving=image, type_of_transform="Rigid",
        )
        rigid_transform = transforms["fwdtransforms"][0]
    else:
        rigid_transform = None
    transform = ants.registration(
        fixed=template,
        moving=image,
        initial_transform=rigid_transform,
        type_of_transform=type_of_transform,
    )["fwdtransforms"]
    registered = ants.apply_transforms(
        template, image, transform, interpolator=interpolator,
    )
    return registered.to_nibabel()


class Registrator(CLI):
    def __init__(
        self,
        template: Optional[NiftiImage] = None,
        type_of_transform: str = "Affine",
        interpolator: str = "bSpline",
        initial_rigid: bool = True,
    ):
        if template is None:
            standard_mni = ants.get_ants_data("mni")
            self.template = ants.image_read(standard_mni)
        else:
            self.template = ants.from_nibabel(template)
        self.type_of_transform = type_of_transform
        self.interpolator = interpolator
        self.initial_rigid = initial_rigid

    def __call__(self, image: NiftiImage, *args, **kwargs) -> NiftiImage:
        return register(
            image,
            self.template,
            self.type_of_transform,
            self.interpolator,
            self.initial_rigid,
        )

    def register_images(self, images: List[NiftiImage]) -> List[NiftiImage]:
        return [self(image) for image in images]

    def register_images_to_templates(
        self, images: List[NiftiImage], templates: List[NiftiImage],
    ) -> List[NiftiImage]:
        assert len(images) == len(templates)
        registered = []
        original_template = self.template
        for image, template in zip(images, templates):
            self.template = template
            registered.append(self(image))
        self.template = original_template
        return registered

    @staticmethod
    def name() -> str:
        return "registered"

    @staticmethod
    def description() -> str:
        return "Co-register an image to MNI or another image."

    @staticmethod
    def get_parent_parser(desc: str) -> ArgumentParser:
        parser = ArgumentParser(
            description=desc, formatter_class=ArgumentDefaultsHelpFormatter,
        )
        parser.add_argument(
            "image", type=file_path(), help="Path of image to normalize.",
        )
        parser.add_argument(
            "-t",
            "--template",
            type=file_path(),
            default=None,
            help="Path of target for registration.",
        )
        parser.add_argument(
            "-o",
            "--output",
            type=save_nifti_path(),
            default=None,
            help="Path to save registered image.",
        )
        parser.add_argument(
            "-tot",
            "--type-of-transform",
            type=str,
            default="Affine",
            choices=allowed_transforms,
            help="Type of registration transform to perform.",
        )
        parser.add_argument(
            "-i",
            "--interpolator",
            type=str,
            default="bSpline",
            choices=allowed_interpolators,
            help="Type of interpolator to use.",
        )
        parser.add_argument(
            "-ir",
            "--initial-rigid",
            action="store_true",
            help=(
                "Do a rigid registration before doing "
                "the `type_of_transform` registration."
            ),
        )
        parser.add_argument(
            "-v",
            "--verbosity",
            action="count",
            default=0,
            help="Increase output verbosity (e.g., -vv is more than -v).",
        )
        return parser

    @classmethod
    def from_argparse_args(cls, args: Namespace):
        if args.template is not None:
            args.template = ants.image_read(args.template)
        return cls(
            args.template,
            args.type_of_transform,
            args.interpolator,
            args.initial_rigid,
        )

    @staticmethod
    def load_image(image_path: PathLike) -> ants.ANTsImage:
        return ants.image_read(image_path)
