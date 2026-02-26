import io
import pickle
import joblib
from pathlib import Path

import numpy as np
import PIL.Image
import PIL.ImageOps
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

# Load the trained model when the app starts
# Using model.zlib (compressed with joblib) for deployment
model = joblib.load("model.zlib")

# Create the FastAPI app
app = FastAPI(redirect_slashes=False)

# Add CORS middleware to allow cross-origin requests from GitHub Pages
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=dict)
async def health_check():
    return {"status": "ok"}


@app.head("/health", include_in_schema=False)
async def health_check_head():
    return {"status": "ok"}


# Home page - serves our HTML interface
@app.get("/", response_class=HTMLResponse)
async def read_root():
    return Path("index.html").read_text()


# Prediction endpoint
@app.post("/predict-image/", name="predict_image_slash")
@app.post("/predict-image", name="predict_image_no_slash")
async def predict_image(file: UploadFile = File(...)):
    # Read the uploaded file
    contents = await file.read()

    # Validate file size (max 5MB)
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 5MB.")

    # Validate file type
    allowed_types = {"image/jpeg", "image/png", "image/gif", "image/webp"}
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid file type.")

    try:
        # Open and preprocess the image
        image = PIL.Image.open(io.BytesIO(contents)).convert("L")  # Convert to grayscale
        image = PIL.ImageOps.invert(image)  # Invert colors (MNIST has white digits on black)
        image = image.resize((28, 28))  # Resize to 28x28
        image_array = np.array(image).reshape(1, -1) / 255.0  # Flatten and normalize

        # Make prediction
        prediction = model.predict(image_array)

        # Get prediction probabilities
        probabilities = model.predict_proba(image_array)[0]

        # Get top 5 predictions
        top_k = 5
        top_indices = np.argsort(probabilities)[-top_k:][::-1]
        top_predictions = [
            {"digit": int(i), "confidence": round(float(probabilities[i]) * 100, 2)}
            for i in top_indices
        ]

        # Return results
        return {
            "prediction": int(prediction[0]),
            "confidence": round(float(probabilities[prediction[0]]) * 100, 2),
            "top_predictions": top_predictions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process image: {str(e)}")
