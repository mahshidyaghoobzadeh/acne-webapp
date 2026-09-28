import os
os.environ["TF_USE_LEGACY_KERAS"] = "1"

from pathlib import Path
import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.preprocessing.image import ImageDataGenerator

print("TensorFlow version:", tf.__version__)

# -----------------------
# مسیرها مطابق پروژه شما
# acne-webapp/
#   backend/train_model.py  <-- این فایل
#   dataset/train , dataset/test
# -----------------------
BASE_DIR = Path(__file__).resolve().parent          # acne-webapp/backend
PROJECT_DIR = BASE_DIR.parent                      # acne-webapp
DATASET_DIR = PROJECT_DIR / "dataset"

train_dir = DATASET_DIR / "train"
val_dir   = DATASET_DIR / "test"

IMG_SIZE = (224, 224)
BATCH_SIZE = 16

# -----------------------
# Data loaders
# -----------------------
train_datagen = ImageDataGenerator(
    rescale=1.0 / 255.0,
    rotation_range=15,
    width_shift_range=0.08,
    height_shift_range=0.08,
    zoom_range=0.15,
    horizontal_flip=True,
)

val_datagen = ImageDataGenerator(rescale=1.0 / 255.0)

train_gen = train_datagen.flow_from_directory(
    str(train_dir),
    target_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    class_mode="binary",
)

val_gen = val_datagen.flow_from_directory(
    str(val_dir),
    target_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    class_mode="binary",
)

# -----------------------
# Model (Transfer Learning)
# -----------------------
base = tf.keras.applications.EfficientNetB0(
    include_top=False,
    weights="imagenet",
    input_shape=(IMG_SIZE[0], IMG_SIZE[1], 3),
)
base.trainable = False

inp = layers.Input(shape=(IMG_SIZE[0], IMG_SIZE[1], 3))
x = base(inp, training=False)
x = layers.GlobalAveragePooling2D()(x)
x = layers.Dropout(0.3)(x)
out = layers.Dense(1, activation="sigmoid")(x)

model = models.Model(inp, out)
model.compile(
    optimizer=tf.keras.optimizers.Adam(1e-3),
    loss="binary_crossentropy",
    metrics=["accuracy", tf.keras.metrics.AUC(name="auc")],
)

callbacks = [
    tf.keras.callbacks.EarlyStopping(patience=4, restore_best_weights=True),
    tf.keras.callbacks.ReduceLROnPlateau(patience=2, factor=0.5),
]

print("\n[Stage 1] Training head...")
model.fit(train_gen, epochs=15, validation_data=val_gen, callbacks=callbacks)

# -----------------------
# Fine-tune last layers
# -----------------------
print("\n[Stage 2] Fine-tuning...")
base.trainable = True
for layer in base.layers[:-30]:
    layer.trainable = False

model.compile(
    optimizer=tf.keras.optimizers.Adam(1e-4),
    loss="binary_crossentropy",
    metrics=["accuracy", tf.keras.metrics.AUC(name="auc")],
)

model.fit(train_gen, epochs=10, validation_data=val_gen, callbacks=callbacks)

# -----------------------
# Save to backend/model
# -----------------------
MODEL_DIR = BASE_DIR / "model"
MODEL_DIR.mkdir(exist_ok=True)

model.save(str(MODEL_DIR / "acne.h5"), save_format="h5")
print("✅ Saved:", MODEL_DIR / "acne.h5")

model.save(str(MODEL_DIR / "acne_savedmodel"), save_format="tf")
print("✅ SavedModel folder:", MODEL_DIR / "acne_savedmodel")
