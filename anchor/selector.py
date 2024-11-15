import json
import numpy as np
import torch
import clip
from PIL import Image

def load_images_and_extract_features(json_data, model, preprocess):
    image_features = []
    for frame in json_data['frames']:
        image_path = frame['file_path']
        image = preprocess(Image.open(image_path)).unsqueeze(0).to(device)
        image_features.append(model.encode_image(image))
    return torch.cat(image_features)

def find_nearest_image(image_features, text_features):
    # Normalize features to compute cosine similarity
    image_features = image_features / image_features.norm(dim=-1, keepdim=True)
    text_features = text_features / text_features.norm(dim=-1, keepdim=True)
    # Compute similarity scores
    similarity = (text_features @ image_features.T).squeeze()
    # Find the index of the highest similarity score
    nearest_image_idx = similarity.argmax().item()
    return nearest_image_idx

def main(json_input, text_prompt):
    # Load the model and preprocessing tools
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, preprocess = clip.load("ViT-B/32", device=device)
    
    # Load JSON data
    with open(json_input, 'r') as f:
        data = json.load(f)
    
    # Extract features from images
    image_features = load_images_and_extract_features(data, model, preprocess)
    
    # Encode text to get its features
    text = clip.tokenize([text_prompt]).to(device)
    text_features = model.encode_text(text)
    
    # Find the nearest image
    nearest_image_idx = find_nearest_image(image_features, text_features)
    nearest_image_path = data['frames'][nearest_image_idx]['file_path']
    
    print(f"The nearest image to the text prompt is at index {nearest_image_idx}: {nearest_image_path}")

if __name__ == "__main__":
    json_input = 'path_to_your_json_file.json'  # Replace with the JSON file path
    text_prompt = "There is a cup on the table."  
    main(json_input, text_prompt)
