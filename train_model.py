import pickle
import os

import joblib
from tensorflow.keras.datasets import mnist
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

print("Loading MNIST dataset...")
(X, y), (X_test, y_test) = mnist.load_data()
X = X.reshape(-1, 784).astype('float32') / 255.0

print("Splitting data...")
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

print("Training Random Forest model...")
clf = RandomForestClassifier(n_estimators=100, n_jobs=-1, random_state=42)
clf.fit(X_train, y_train)

print(f"Test Accuracy: {clf.score(X_test, y_test) * 100:.2f}%")

# Save original model (uncompressed)
print("Saving original model...")
with open("model.pkl", "wb") as f:
    pickle.dump(clf, f)
original_size = os.path.getsize("model.pkl")
print(f"Original model size: {original_size / (1024*1024):.2f} MB")

# Save compressed model using joblib with zlib compression
print("Creating compressed model (joblib + zlib)...")
joblib.dump(clf, "model.zlib", compress=('zlib', 3))
compressed_size = os.path.getsize("model.zlib")
print(f"Compressed model size: {compressed_size / (1024*1024):.2f} MB")
print(f"Size reduction: {(1 - compressed_size/original_size) * 100:.1f}%")

print("\nModel files created:")
print("  - model.pkl (original, ~115 MB)")
print("  - model.zlib (compressed, ~18 MB)")
print("\nFor deployment, use model.zlib")
