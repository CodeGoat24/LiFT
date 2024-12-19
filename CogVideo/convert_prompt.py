"""
The CogVideoX model is designed to generate high-quality videos based on detailed and highly descriptive prompts.
The model performs best when provided with refined, granular prompts, which enhance the quality of video generation.
This script is designed to assist with transforming simple user inputs into detailed prompts suitable for CogVideoX.
For text-to-video, simply provide the prompt.

### How to run:
Run the script for **text-to-video**:
    $ python convert_demo.py --prompt "A girl riding a bike." --type "t2v"
    
"""

import argparse
import base64
from mimetypes import guess_type
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import random
import json
import tqdm


sys_prompt_t2v = """You are part of a team of bots that creates videos. You work with an assistant bot that will draw anything you say in square brackets.

For example , outputting " a beautiful morning in the woods with the sun peaking through the trees " will trigger your partner bot to output an video of a forest morning , as described. You will be prompted by people looking to create detailed , amazing videos. The way to accomplish this is to take their short prompts and make them extremely detailed and descriptive.
There are a few rules to follow:

You will only ever output a single video description per user request.

When modifications are requested , you should not simply make the description longer . You should refactor the entire description to integrate the suggestions.
Other times the user will not want modifications , but instead want a new image . In this case , you should ignore your previous conversation with the user.

Video descriptions must have the same num of words as examples below. Extra words will be ignored.
"""

sys_prompt_i2v = """
**Objective**: **Give a highly descriptive video caption based on input image and user input. **. As an expert, delve deep into the image with a discerning eye, leveraging rich creativity, meticulous thought. When describing the details of an image, include appropriate dynamic information to ensure that the video caption contains reasonable actions and plots. If user input is not empty, then the caption should be expanded according to the user's input. 

**Note**: The input image is the first frame of the video, and the output video caption should describe the motion starting from the current image. User input is optional and can be empty. 

**Note**: Don't contain camera transitions!!! Don't contain screen switching!!! Don't contain perspective shifts !!!

**Answering Style**:
Answers should be comprehensive, conversational, and use complete sentences. The answer should be in English no matter what the user's input is. Provide context where necessary and maintain a certain tone.  Begin directly without introductory phrases like "The image/video showcases" "The photo captures" and more. For example, say "A woman is on a beach", instead of "A woman is depicted in the image".

**Output Format**: "[highly descriptive image caption here]"

user input:
"""

def convert_prompt(prompt: str, retry_times: int = 3, type: str = "t2v", image_path: str = None):
    """
    Convert a prompt to a format that can be used by the model for inference
    """
    model = AutoModelForCausalLM.from_pretrained(
        "Qwen/Qwen2.5-72B-Instruct",
        torch_dtype=torch.float16,
        device_map="auto"
    ).eval()
    tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-72B-Instruct")


    text = prompt.strip()

    messages=[
        {"role": "system", "content": f"{sys_prompt_t2v}"},
        {
            "role": "user",
            "content": 'Create an imaginative video descriptive caption or modify an earlier caption for the user input : " a girl is on the beach"',
        },
        {
            "role": "assistant",
            "content": "A radiant woman stands on a deserted beach, arms outstretched, wearing a beige trench coat, white blouse, light blue jeans, and chic boots, against a backdrop of soft sky and sea. Moments later, she is seen mid-twirl, arms exuberant, with the lighting suggesting dawn or dusk. Then, she runs along the beach, her attire complemented by an off-white scarf and black ankle boots, the tranquil sea behind her. Finally, she holds a paper airplane, her pose reflecting joy and freedom, with the ocean's gentle waves and the sky's soft pastel hues enhancing the serene ambiance.",
        },
        {
            "role": "user",
            "content": 'Create an imaginative video descriptive caption or modify an earlier caption for the user input : " A man jogging on a football field"',
        },
        {
            "role": "assistant",
            "content": "A determined man in athletic attire, including a blue long-sleeve shirt, black shorts, and blue socks, jogs around a snow-covered soccer field, showcasing his solitary exercise in a quiet, overcast setting. His long dreadlocks, focused expression, and the serene winter backdrop highlight his dedication to fitness. As he moves, his attire, consisting of a blue sports sweatshirt, black athletic pants, gloves, and sneakers, grips the snowy ground. He is seen running past a chain-link fence enclosing the playground area, with a basketball hoop and children's slide, suggesting a moment of solitary exercise amidst the empty field.",
        },
        {
            "role": "user",
            "content": 'Create an imaginative video descriptive caption or modify an earlier caption for the user input : " A woman is dancing, HD footage, close-up"',
        },
        {
            "role": "assistant",
            "content": "A young woman with her hair in an updo and wearing a teal hoodie stands against a light backdrop, initially looking over her shoulder with a contemplative expression. She then confidently makes a subtle dance move, suggesting rhythm and movement. Next, she appears poised and focused, looking directly at the camera. Her expression shifts to one of introspection as she gazes downward slightly. Finally, she dances with confidence, her left hand over her heart, symbolizing a poignant moment, all while dressed in the same teal hoodie against a plain, light-colored background.",
        },
        {
            "role": "user",
            "content": f'Create an imaginative video descriptive caption or modify an earlier caption in ENGLISH for the user input: " {text} "',
        },
    ]

    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )

    device = "cuda"
    model_inputs = tokenizer([text], return_tensors="pt").to(device)

    generated_ids = model.generate(
        model_inputs.input_ids,
        max_new_tokens=512
    )
    generated_ids = [
        output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
    ]

    response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]


    return response
        
    


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", type=str, default='A girl riding a bike.', help="Prompt to convert")
    parser.add_argument("--retry_times", type=int, default=3, help="Number of times to retry the conversion")
    parser.add_argument("--type", type=str, default="t2v", help="Type of conversion (t2v or i2v)")
    parser.add_argument("--image_path", type=str, default=None, help="Path to the image file")
    args = parser.parse_args()

    converted_prompt = convert_prompt(args.prompt, args.retry_times, args.type, args.image_path)

    print(converted_prompt)
