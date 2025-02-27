import json
import re

scores = {  
        'Good': 0.9,
        'Normal': 0.2,
        'Bad': 0.05        
        }

def get_score(reward):
    if 'Normal' in reward:
        return scores['Normal']
    elif 'Bad' in reward:
        return scores['Bad']
    else:
        return scores['Good']
    

with open(f'/path/to/json_file.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

data_list = []
import tqdm
for i in tqdm.trange(len(data)):
    item = data_list[i]

    item['score'] = (get_score(item["semantic consistency"]) + get_score(item["fidelity issues"]) + get_score(item["motion issues"])) / 3
    item['score'] = round(item['score'], 2)

    data_list.append(item)


with open(f'/path/to/save_path.json', 'w', encoding='utf-8') as json_file:
    json.dump(data_list, json_file, ensure_ascii=False, indent=4)


