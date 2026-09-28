import tensorflow as tf

# مسیر درست: یک سطح بالاتر برو، بعد وارد backend/model شو
model = tf.keras.models.load_model("backend/model/acne.keras", compile=False)

print("مدل با موفقیت لود شد!")
print(model.summary())