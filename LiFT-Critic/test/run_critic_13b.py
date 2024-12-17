# This file is modified from https://github.com/haotian-liu/LLaVA/

import argparse
import os
import os.path as osp
import re
from io import BytesIO

import requests
import torch
from PIL import Image

from llava.constants import (
    DEFAULT_IM_END_TOKEN,
    DEFAULT_IM_START_TOKEN,
    DEFAULT_IMAGE_TOKEN,
    IMAGE_PLACEHOLDER,
    IMAGE_TOKEN_INDEX,
)
from llava.conversation import SeparatorStyle, conv_templates
from llava.mm_utils import KeywordsStoppingCriteria, get_model_name_from_path, process_images, tokenizer_image_token
from llava.model.builder import load_pretrained_model
from llava.utils import disable_torch_init
import warnings; 

warnings.filterwarnings("ignore")


def image_parser(args):
    out = args.image_file.split(args.sep)
    return out


def load_image(image_file):
    if image_file.startswith("http") or image_file.startswith("https"):
        print("downloading image from url", args.video_file)
        response = requests.get(image_file)
        image = Image.open(BytesIO(response.content)).convert("RGB")
    else:
        image = Image.open(image_file).convert("RGB")
    return image


def load_images(image_files):
    out = []
    for image_file in image_files:
        image = load_image(image_file)
        out.append(image)
    return out


def eval_model(args):
    # Model
    disable_torch_init()
    

    model_name = get_model_name_from_path(args.model_path)
    tokenizer, model, image_processor, context_len = load_pretrained_model(args.model_path, model_name, args.model_base)
    import json
    with open(args.data_root, 'r', encoding='utf-8') as f:
        data = json.load(f)

    question_type = ['semantic consistency', 'fidelity issues', 'motion issues']
    question_list = [
            " Please identify the semantic consistency issues in this video, focusing on the alignment between the text and the visual content. Specifically, point out any discrepancies regarding the subject (e.g., person or animal), quantity, color, scene description, style, and other relevant aspects.",
            " Please identify the fidelity issues in this video, assessing the realism of the content, including people, animals, and other objects. Highlight any problems such as missing limbs, deformed hands or faces, or other unrealistic elements.",
            " Please identify the motion issues in this video, focusing on the continuity and smoothness of actions, as well as their coherence and adherence to the laws of physics."
        ]

    reward_item_list = []

    for item in data:
        reward_item = item.copy()
        output_list = []
        for i in range(len(question_type)):
    
            qs = item['caption'] + question_list[i]
            video_path = args.image_root + item['video']

            from llava.mm_utils import opencv_extract_frames
            
            images, num_frames = opencv_extract_frames(video_path, args.num_video_frames)

            image_token_se = DEFAULT_IM_START_TOKEN + DEFAULT_IMAGE_TOKEN + DEFAULT_IM_END_TOKEN
            if IMAGE_PLACEHOLDER in qs:
                if model.config.mm_use_im_start_end:
                    qs = re.sub(IMAGE_PLACEHOLDER, image_token_se, qs)
                else:
                    qs = re.sub(IMAGE_PLACEHOLDER, DEFAULT_IMAGE_TOKEN, qs)
            else:
                if DEFAULT_IMAGE_TOKEN not in qs:
                    # print("no <image> tag found in input. Automatically append one at the beginning of text.")
                    # do not repeatively append the prompt.
                    if model.config.mm_use_im_start_end:
                        qs = (image_token_se + "\n") * len(images) + qs
                    else:
                        qs = (DEFAULT_IMAGE_TOKEN + "\n") * len(images) + qs
            # print("input: ", qs)

            if "llama-2" in model_name.lower():
                conv_mode = "llava_llama_2"
            elif "v1" in model_name.lower():
                conv_mode = "llava_v1"
            elif "mpt" in model_name.lower():
                conv_mode = "mpt"
            else:
                conv_mode = "llava_v0"

            if args.conv_mode is not None and conv_mode != args.conv_mode:
                print(
                    "[WARNING] the auto inferred conversation mode is {}, while `--conv-mode` is {}, using {}".format(
                        conv_mode, args.conv_mode, args.conv_mode
                    )
                )
            else:
                args.conv_mode = conv_mode

            conv = conv_templates[args.conv_mode].copy()
            conv.append_message(conv.roles[0], qs)
            conv.append_message(conv.roles[1], None)
            prompt = conv.get_prompt()

            images_tensor = process_images(images, image_processor, model.config).to(model.device, dtype=torch.float16)
            input_ids = tokenizer_image_token(prompt, tokenizer, IMAGE_TOKEN_INDEX, return_tensors="pt").unsqueeze(0).cuda()

            stop_str = conv.sep if conv.sep_style != SeparatorStyle.TWO else conv.sep2
            keywords = [stop_str]
            stopping_criteria = KeywordsStoppingCriteria(keywords, tokenizer, input_ids)

            # print(images_tensor.shape)
            with torch.inference_mode():
                output_ids = model.generate(
                    input_ids,
                    images=[
                        images_tensor,
                    ],
                    do_sample=True if args.temperature > 0 else False,
                    temperature=args.temperature,
                    top_p=args.top_p,
                    num_beams=args.num_beams,
                    max_new_tokens=args.max_new_tokens,
                    use_cache=True,
                    stopping_criteria=[stopping_criteria],
                )

            outputs = tokenizer.batch_decode(output_ids, skip_special_tokens=True)[0]
            outputs = outputs.strip()
            if outputs.endswith(stop_str):
                outputs = outputs[: -len(stop_str)]
            outputs = outputs.strip()

            reward_item[question_type[i]] = outputs

        reward_item_list.append(reward_item)
    
    with open(args.save_file, 'w', encoding='utf-8') as f:
        json.dump(reward_item_list, f, ensure_ascii=False, indent=4)
            

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", type=str, default="./LiFT-Critic-13b-lora-v1.5")
    parser.add_argument("--model-base", type=str, default=f"Efficient-Large-Model/VILA1.5-13b")
    parser.add_argument("--num-video-frames", type=int, default=8)
    parser.add_argument("--image_root", type=str, default=f"./demo/videos/")
    parser.add_argument("--data_root", type=str, default=f"./demo/test.json")
    parser.add_argument("--save_file", type=str, default=f"./demo/critic_output_13b.json")
    parser.add_argument("--conv-mode", type=str, default=f"vicuna_v1")
    parser.add_argument("--sep", type=str, default=",")
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--top_p", type=float, default=None)
    parser.add_argument("--num_beams", type=int, default=1)
    parser.add_argument("--max_new_tokens", type=int, default=512)
    args = parser.parse_args()

    print('the result file will be save to: ' + args.save_file)

    eval_model(args)
