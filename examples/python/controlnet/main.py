#!/usr/bin/env python3
"""
Example running ControlNet conditioned on Canny edges.

Based on https://huggingface.co/docs/diffusers/using-diffusers/controlnet.

Run
```sh
examples/python/controlnet/main.py
```
"""
from __future__ import annotations

import argparse
import os

import cv2
import numpy as np
import PIL.Image
import requests
import rerun as rr
import torch
from diffusers import (
    AutoencoderKL,
    ControlNetModel,
    StableDiffusionXLControlNetPipeline,
)

RERUN_LOGO_URL = "https://storage.googleapis.com/rerun-example-datasets/controlnet/rerun-icon-1000.png"


def controlnet_callback(
    iteration: int, timestep: float, latents: torch.Tensor, pipeline: StableDiffusionXLControlNetPipeline
) -> None:
    rr.set_time_sequence("iteration", iteration)
    rr.set_time_seconds("timestep", timestep)

    image = pipeline.vae.decode(latents / pipeline.vae.config.scaling_factor, return_dict=False)[0]
    image = pipeline.image_processor.postprocess(image, output_type="np").squeeze()
    rr.log("output", rr.Image(image))
    rr.log("latent", rr.Tensor(latents.squeeze(), dim_names=["channel", "height", "width"]))


def run_canny_controlnet(image_path: str, prompt: str, negative_prompt: str) -> None:
    if not torch.cuda.is_available():
        print("This example requires a torch with CUDA, but no CUDA device found. Aborting.")
        return

    if image_path.startswith("http://") or image_path.startswith("https://"):
        pil_image = PIL.Image.open(requests.get(image_path, stream=True).raw)
    elif os.path.isfile(image_path):
        pil_image = PIL.Image.open(image_path)
    else:
        raise ValueError(f"Invalid image_path: {image_path}")

    image = np.array(pil_image)

    if image.shape[2] == 4:  # RGBA image
        rgb_image = image[..., :3]  # RGBA to RGB
        rgb_image[image[..., 3] < 200] = 0.0  # reduces artifacts for transparent parts
    else:
        rgb_image = image

    low_threshold = 100.0
    high_threshold = 200.0
    canny_image = cv2.Canny(rgb_image, low_threshold, high_threshold)
    canny_image = canny_image[:, :, None]
    # cv2.dilate(kjgk
    canny_image = np.concatenate([canny_image, canny_image, canny_image], axis=2)
    canny_image = PIL.Image.fromarray(canny_image)

    rr.log("input/raw", rr.Image(image), timeless=True)
    rr.log("input/canny", rr.Image(canny_image), timeless=True)

    controlnet = ControlNetModel.from_pretrained(
        "diffusers/controlnet-canny-sdxl-1.0",
        torch_dtype=torch.float16,
        use_safetensors=True,
    )
    vae = AutoencoderKL.from_pretrained(
        "madebyollin/sdxl-vae-fp16-fix", torch_dtype=torch.float16, use_safetensors=True
    )
    pipeline = StableDiffusionXLControlNetPipeline.from_pretrained(
        "stabilityai/stable-diffusion-xl-base-1.0",
        controlnet=controlnet,
        vae=vae,
        torch_dtype=torch.float16,
        use_safetensors=True,
    )

    pipeline.enable_model_cpu_offload()

    rr.log("positive_prompt", rr.TextDocument(prompt), timeless=True)
    rr.log("negative_prompt", rr.TextDocument(negative_prompt), timeless=True)

    images = pipeline(
        prompt,
        negative_prompt=negative_prompt,
        image=canny_image,  # add batch dimension
        controlnet_conditioning_scale=0.5,
        callback=lambda i, t, latents: controlnet_callback(i, t, latents, pipeline),
    ).images[0]

    rr.log("output", rr.Image(images))


def main() -> None:
    parser = argparse.ArgumentParser(description="Use Canny-conditioned ControlNet to generate image.")
    parser.add_argument(
        "--img_path",
        type=str,
        help="Path to image used as input for Canny edge detector.",
        default=RERUN_LOGO_URL,
    )
    parser.add_argument(
        "--prompt",
        type=str,
        help="Prompt used as input for ControlNet.",
        default="aerial view, a futuristic research complex in a bright foggy jungle, hard lighting",
    )
    parser.add_argument(
        "--negative_prompt",
        type=str,
        help="Negative prompt used as input for ControlNet.",
        default="low quality, bad quality, sketches",
    )
    rr.script_add_args(parser)
    args = parser.parse_args()

    rr.script_setup(args, "rerun_example_controlnet")
    run_canny_controlnet(args.img_path, args.prompt, args.negative_prompt)
    rr.script_teardown(args)


if __name__ == "__main__":
    main()
