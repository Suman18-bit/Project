import os
# --- CRITICAL FIX: MUST BE AT THE VERY TOP ---
# This forces TensorFlow 2.16+ to use the Keras 2 engine 
# so it can understand 'batch_shape' and 'optional' in your .h5 file
os.environ['TF_USE_LEGACY_KERAS'] = '1'

import streamlit as st
import numpy as np
import pickle
from PIL import Image
import tensorflow as tf
from tensorflow.keras.models import load_model, Model
from tensorflow.keras.applications.vgg16 import VGG16, preprocess_input
from tensorflow.keras.preprocessing.image import img_to_array
from tensorflow.keras.preprocessing.sequence import pad_sequences

# ---------------------------------------------------------
# Configuration Constants
# ---------------------------------------------------------
# Adjust MAX_LENGTH to match the value used during your model training
MAX_LENGTH = 35 
MODEL_PATH = "models/model.h5"
TOKENIZER_PATH = "models/tokenizer.pkl"

# ---------------------------------------------------------
# Resource Loading & Caching
# ---------------------------------------------------------
@st.cache_resource
def load_assets():
    """Loads VGG16, your trained model, and the tokenizer once and caches them."""
    # 1. Load and configure VGG16 for feature extraction
    vgg_base = VGG16()
    vgg_model = Model(inputs=vgg_base.inputs, outputs=vgg_base.layers[-2].output)
    
    # 2. Load your custom captioning model
    if not os.path.exists(MODEL_PATH):
        st.error(f"Model file not found at {MODEL_PATH}. Please ensure it is placed in the 'models' folder.")
        st.stop()
    
    # Because of the legacy switch at the top, this will now load successfully
    caption_model = load_model(MODEL_PATH)
    
    # 3. Load the tokenizer
    if not os.path.exists(TOKENIZER_PATH):
        st.error(f"Tokenizer file not found at {TOKENIZER_PATH}.")
        st.stop()
    with open(TOKENIZER_PATH, "rb") as f:
        tokenizer = pickle.load(f)
        
    return vgg_model, caption_model, tokenizer

# Initialize models and tokenizer
try:
    vgg_model, caption_model, tokenizer = load_assets()
except Exception as e:
    st.error(f"Error loading models or tokenizer: {e}")
    st.stop()

# ---------------------------------------------------------
# Helper Functions for Inference
# ---------------------------------------------------------
def extract_features(uploaded_file, model):
    """Preprocesses the image and extracts features using VGG16."""
    img = Image.open(uploaded_file)
    # Convert grayscale/RGBA to RGB just in case
    if img.mode != 'RGB':
        img = img.convert('RGB')
        
    img = img.resize((224, 224))
    img = img_to_array(img)
    img = np.expand_dims(img, axis=0)
    img = preprocess_input(img)
    features = model.predict(img, verbose=0)
    return features

def get_word_from_index(index, tokenizer):
    """Maps an index integer back to its corresponding word."""
    for word, idx in tokenizer.word_index.items():
        if idx == index:
            return word
    return None

def generate_caption(model, tokenizer, features, max_len):
    """Generates a caption sequence word-by-word."""
    in_text = "startseq"
    
    for _ in range(max_len):
        # Convert current text sequence to integers
        sequence = tokenizer.texts_to_sequences([in_text])[0]
        sequence = pad_sequences([sequence], maxlen=max_len)
        
        # Predict the next token probability distribution
        y_hat = model.predict([features, sequence], verbose=0)
        y_hat = np.argmax(y_hat)
        
        # Map index to word
        word = get_word_from_index(y_hat, tokenizer)
        
        if word is None:
            break
            
        in_text += " " + word
        
        if word == "endseq":
            break
            
    # Clean the output string
    cleaned_caption = in_text.replace("startseq", "").replace("endseq", "").strip()
    return cleaned_caption.capitalize()

# ---------------------------------------------------------
# Streamlit Interface Layout
# ---------------------------------------------------------
st.set_page_config(page_title="Smart Caption Generator", page_icon="📸")

st.title("📸 Smart Caption Generator")
st.write("Upload an image below, and the VGG16 + LSTM deep learning model will generate a descriptive caption.")

# File uploader widget
uploaded_image = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

if uploaded_image is not None:
    # Display the uploaded image
    image = Image.open(uploaded_image)
    st.image(image, caption="Uploaded Image", use_container_width=True)
    
    # Process and Predict Button
    if st.button("Generate Caption", type="primary"):
        with st.spinner("Analyzing image and generating caption..."):
            try:
                # Step 1: Feature Extraction
                features = extract_features(uploaded_image, vgg_model)
                
                # Step 2: Sequence Prediction
                caption = generate_caption(caption_model, tokenizer, features, MAX_LENGTH)
                
                # Step 3: Present Result
                st.success("Caption Generated Successfully!")
                st.markdown(f"### **{caption}**")
                
            except Exception as e:
                st.error(f"An error occurred during inference: {e}")
