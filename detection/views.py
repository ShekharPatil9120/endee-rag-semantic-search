from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from .models import UploadedImage
from PIL import Image, ImageOps
import numpy as np
import tensorflow as tf
import requests
from io import BytesIO
from .forms import ImageUploadForm, ImageURLForm
import pandas as pd
import os

# -------------------------------------------------------------
# PATHS
# -------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

CSV_PATH = os.path.join(BASE_DIR, "disease_solutions_v2.csv")
solutions_df = pd.read_csv(CSV_PATH)

# ------------------ MODEL PATHS ------------------------------
CORN_MODEL = os.path.join(ASSETS_DIR, "CORNs_model.tflite")
CORN_LABELS = os.path.join(ASSETS_DIR, "CORNs_labels.txt")

APPLE_MODEL = os.path.join(ASSETS_DIR, "model1.tflite")
APPLE_LABELS = os.path.join(ASSETS_DIR, "labels1.txt")



PLANT_MODEL = os.path.join(ASSETS_DIR, "plant_disease_model.tflite")
PLANT_LABELS = os.path.join(ASSETS_DIR, "plant_labels.txt")

INPUT_SIZE = 224

# -------------------------------------------------------------
# LOAD MODELS
# -------------------------------------------------------------
def load_model(path):
    interpreter = tf.lite.Interpreter(model_path=path)
    interpreter.allocate_tensors()
    return interpreter

# Lazy model initialization: avoid loading TFLite interpreters at import-time
apple_interpreter = None
corn_interpreter = None
plant_interpreter = None

apple_in = apple_out = corn_in = corn_out = plant_in = plant_out = None

APPLE_LABEL = CORN_LABEL = PLANT_LABEL = None

# If any error occurs while loading models, store message here
MODEL_LOAD_ERROR = None

def load_labels(path):
    with open(path, "r") as f:
        return [l.strip() for l in f.readlines()]


def init_interpreters():
    """Initialize TFLite interpreters on first use. Sets MODEL_LOAD_ERROR on failure."""
    global apple_interpreter, corn_interpreter, plant_interpreter
    global apple_in, apple_out, corn_in, corn_out, plant_in, plant_out
    global APPLE_LABEL, CORN_LABEL, PLANT_LABEL, MODEL_LOAD_ERROR

    if apple_interpreter is not None and corn_interpreter is not None and plant_interpreter is not None:
        return

    try:
        apple_interpreter = load_model(APPLE_MODEL)
        corn_interpreter = load_model(CORN_MODEL)
        plant_interpreter = load_model(PLANT_MODEL)

        # Input/Output details
        apple_in = apple_interpreter.get_input_details()[0]
        apple_out = apple_interpreter.get_output_details()[0]

        corn_in = corn_interpreter.get_input_details()[0]
        corn_out = corn_interpreter.get_output_details()[0]

        plant_in = plant_interpreter.get_input_details()[0]
        plant_out = plant_interpreter.get_output_details()[0]

        # Load labels
        APPLE_LABEL = load_labels(APPLE_LABELS)
        CORN_LABEL = load_labels(CORN_LABELS)
        PLANT_LABEL = load_labels(PLANT_LABELS)

    except Exception as e:
        # Keep a readable message for debugging and user feedback
        MODEL_LOAD_ERROR = str(e)
        # Nullify interpreters to indicate they are unavailable
        apple_interpreter = corn_interpreter = plant_interpreter = None
        apple_in = apple_out = corn_in = corn_out = plant_in = plant_out = None
        APPLE_LABEL = CORN_LABEL = PLANT_LABEL = None


# -------------------------------------------------------------
# PREPROCESS IMAGE
# -------------------------------------------------------------
def preprocess(pil_img):
    img = ImageOps.fit(pil_img, (INPUT_SIZE, INPUT_SIZE), Image.Resampling.LANCZOS)
    arr = np.asarray(img).astype("float32") / 255.0
    arr = np.expand_dims(arr, 0)
    return arr


# -------------------------------------------------------------
# GREEN PIXEL CHECK
# -------------------------------------------------------------
def green_ratio_check(pil_img, threshold=0.18):
    arr = np.array(pil_img.resize((224,224))).astype(np.int16)
    r, g, b = arr[:,:,0], arr[:,:,1], arr[:,:,2]

    green_mask = (g > r + 15) & (g > b + 15) & (g > 60)
    ratio = green_mask.mean()

    return ratio, ratio >= threshold


# -------------------------------------------------------------
# GENERIC MULTICLASS PREDICTION
# -------------------------------------------------------------
def predict(interpreter, input_details, output_details, img_array, label_list):
    interpreter.set_tensor(input_details["index"], img_array)
    interpreter.invoke()
    preds = interpreter.get_tensor(output_details["index"])[0]

    idx = int(np.argmax(preds))
    conf = float(preds[idx]) * 100
    return label_list[idx], conf


# -------------------------------------------------------------
# MAIN PREDICTION LOGIC
# -------------------------------------------------------------
def classify_image(pil_img):
    # Ensure interpreters are initialized (lazy-load)
    init_interpreters()
    if MODEL_LOAD_ERROR:
        return {
            "status": "model_error",
            "label": "Model Load Error",
            "confidence": 0.0,
            "message": MODEL_LOAD_ERROR
        }

    # 1) GREEN CHECK
    ratio, is_green = green_ratio_check(pil_img)

    if not is_green:
        return {
            "status": "invalid",
            "label": "Not a Plant (Low Green Pixels)",
            "confidence": round(ratio * 100, 2)
        }

    img_arr = preprocess(pil_img)

    # 2) RUN CORN MODEL FIRST
    corn_label, corn_conf = predict(
        corn_interpreter, corn_in, corn_out, img_arr, CORN_LABEL
    )

    # Only accept corn if confidence >= 90%
    is_corn_label = "corn" in corn_label.lower()

    if corn_conf >= 90 and is_corn_label:
        return {
            "status": "corn",
            "label": corn_label,
            "confidence": corn_conf
        }

    # 3) RUN APPLE MODEL
    apple_label, apple_conf = predict(
        apple_interpreter, apple_in, apple_out, img_arr, APPLE_LABEL
    )

    # Only accept apple if confidence >= 95%
    is_apple_label = "apple" in apple_label.lower()

    if apple_conf >= 95 and is_apple_label:
        return {
            "status": "apple",
            "label": apple_label,
            "confidence": apple_conf
        }

    # 4) RUN GENERAL PLANT MODEL (fallback)
    plant_label, plant_conf = predict(
        plant_interpreter, plant_in, plant_out, img_arr, PLANT_LABEL
    )

    return {
        "status": "general",
        "label": plant_label,
        "confidence": plant_conf
    }


# -------------------------------------------------------------
# VIEWS
# -------------------------------------------------------------
def detection_home(request):
    return render(request, "detection/upload.html")


def upload_image(request):
    if request.method == "POST":
        form = ImageUploadForm(request.POST, request.FILES)

        if form.is_valid():
            img_obj = form.save()
            pil_img = Image.open(img_obj.image).convert("RGB")

            result = classify_image(pil_img)
            # Handle model load error
            if result.get("status") == "model_error":
                return render(request, "detection/invalid.html", {
                    "error": "Model failed to load",
                    "confidence": 0,
                    "details": result.get("message")
                })

            if result["status"] == "invalid":
                return render(request, "detection/invalid.html", {
                    "error": result["label"],
                    "confidence": result["confidence"]
                })

            label = result["label"]
            conf = result["confidence"]

            # CSV lookup
            match = solutions_df[
                solutions_df["Crop & Disease Name"].str.lower() == label.lower()
            ]

            if not match.empty:
                temp = match["Temporary Solution (Organic & Cultural)"].values[0]
                perm = match["Permanent Solution (Chemical/Spray & Cultural)"].values[0]
            else:
                temp = "No solution found."
                perm = "Please update CSV."

            return render(request, "detection/result.html", {
                "class_name": label,
                "confidence": conf,
                "image_url": img_obj.image.url,
                "temp_solution": temp,
                "perm_solution": perm,
            })

    return render(request, "detection/upload_image.html", {
        "upload_form": ImageUploadForm()
    })


def enter_url(request):
    if request.method == "POST":
        form = ImageURLForm(request.POST)

        if form.is_valid():
            url = form.cleaned_data["image_url"]

            try:
                resp = requests.get(url, timeout=10)
                pil_img = Image.open(BytesIO(resp.content)).convert("RGB")
            except:
                return render(request, "detection/enter_url.html", {
                    "url_form": form,
                    "error": "Invalid image URL"
                })

            result = classify_image(pil_img)
            # Handle model load error
            if result.get("status") == "model_error":
                return render(request, "detection/invalid.html", {
                    "error": "Model failed to load",
                    "confidence": 0,
                    "details": result.get("message")
                })

            if result["status"] == "invalid":
                return render(request, "detection/invalid.html", {
                    "error": result["label"],
                    "confidence": result["confidence"]
                })

            label = result["label"]
            conf = result["confidence"]

            match = solutions_df[
                solutions_df["Crop & Disease Name"].str.lower() == label.lower()
            ]

            if not match.empty:
                temp = match["Temporary Solution (Organic & Cultural)"].values[0]
                perm = match["Permanent Solution (Chemical/Spray & Cultural)"].values[0]
            else:
                temp = "No solution found."
                perm = "Please update CSV."

            return render(request, "detection/result.html", {
                "class_name": label,
                "confidence": conf,
                "image_url": url,
                "temp_solution": temp,
                "perm_solution": perm,
            })

    return render(request, "detection/enter_url.html", {"url_form": ImageURLForm()})
