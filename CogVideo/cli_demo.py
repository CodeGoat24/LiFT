"""
This script demonstrates how to generate a video using the CogVideoX model with the Hugging Face `diffusers` pipeline.

Running the Script:

CogVideoX-2b-LiFT
``bash
$ python cli_demo.py --prompt "A girl in a flowing white dress stands in a vast field of lavender at sunset. The golden light bathes the flowers, creating a soft, dreamy glow. A gentle breeze catches her hair, and the camera slowly pans around her, capturing the endless sea of purple." --model_path Fudan-FUXI/CogVideoX-2B-LiFT
```

"""

import argparse
from typing import Literal

import torch
from diffusers import (
    CogVideoXPipeline,
    CogVideoXDDIMScheduler,
    CogVideoXDPMScheduler,
)
from diffusers.utils import export_to_video, load_image, load_video

def generate_video(
    prompt: str,
    model_path: str,
    lora_path: str = None,
    lora_rank: int = 128,
    output_path: str = "./output.mp4",
    image_or_video_path: str = "",
    num_inference_steps: int = 50,
    guidance_scale: float = 6.0,
    num_videos_per_prompt: int = 1,
    dtype: torch.dtype = torch.bfloat16,
    generate_type: str = Literal["t2v", "i2v", "v2v"], 
    seed: int = 42,
):

    pipe = CogVideoXPipeline.from_pretrained(model_path, torch_dtype=dtype)

    if lora_path:
        pipe.load_lora_weights(lora_path, weight_name="pytorch_lora_weights.safetensors", adapter_name="test")
        pipe.fuse_lora(lora_scale=1 / lora_rank, components=['transformer'])

    pipe.scheduler = CogVideoXDPMScheduler.from_config(pipe.scheduler.config, timestep_spacing="trailing")

    pipe.to("cuda")

    # pipe.enable_sequential_cpu_offload()
    # pipe.vae.enable_slicing()
    # pipe.vae.enable_tiling()

    video_generate = pipe(
        prompt=prompt,
        num_videos_per_prompt=num_videos_per_prompt,
        num_inference_steps=num_inference_steps,
        num_frames=49,
        use_dynamic_cfg=True,
        guidance_scale=guidance_scale,
        generator=torch.Generator().manual_seed(seed),
    ).frames[0]

    export_to_video(video_generate, output_path, fps=8)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a video from a text prompt using CogVideoX")
    parser.add_argument(
        "--model_path", type=str, default='Fudan-FUXI/CogVideoX-2B-LiFT', help="The path of the pre-trained model to be used"
    )
    parser.add_argument(
        "--prompt", type=str, default="A girl riding a bike.", help="The description of the video to be generated"
    )
    parser.add_argument(
        "--output_path", type=str, default="./output.mp4", help="The path where the generated video will be saved"
    )
    parser.add_argument(
        "--num_inference_steps", type=int, default=50, help="Number of steps for the inference process"
    )
    parser.add_argument(
        "--dtype", type=str, default="float16", help="The data type for computation (e.g., 'float16' or 'bfloat16')"
    )
    parser.add_argument("--seed", type=int, default=42, help="The seed for reproducibility")
    
    args = parser.parse_args()
    dtype = torch.float16 if args.dtype == "float16" else torch.bfloat16
    generate_video(
        prompt=args.prompt,
        model_path=args.model_path,
        output_path=args.output_path,
        num_inference_steps=args.num_inference_steps,
        dtype=dtype,
        generate_type='t2v',
        seed=args.seed,
    )
