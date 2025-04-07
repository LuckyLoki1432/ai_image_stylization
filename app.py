from flask import Flask, render_template, request, send_file, url_for
import numpy as np
import cv2
from PIL import Image, ImageEnhance, ImageFilter, ImageDraw, ImageFont
from io import BytesIO
from pyngrok import ngrok
import threading
import time
import base64
import os



app = Flask(__name__)


# Create sample logo if it doesn't exist
if not os.path.exists('static/rompit.png'):
    img = Image.new('RGB', (200, 100), color=(73, 109, 137))
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 30)
    except:
        font = ImageFont.load_default()
    d.text((10,10), "ROMPIT", fill=(255,255,0), font=font)
    img.save('static/rompit.png')


# ========== STYLE DEFINITIONS ==========
STYLES = {
    "Van Gogh - Starry Night": "🌌",
    "Picasso - Cubist": "🧊",
    "Monet - Water Lilies": "🌸",
    "Hokusai - Great Wave": "🌊",
    "Warhol - Pop Art": "🟡",
    "Pencil Sketch": "✏",
    "Oil Painting": "🖌",
    "Ghibli - Animated Fantasy": "🐉"
}

# ========== FLASK ROUTES ==========
@app.route("/", methods=["GET", "POST"])
def home():
    # Default values
    selected_style = "Van Gogh - Starry Night"
    intensity = 0.7
    original_img = None
    edited_img = None

    if request.method == "POST":
        action = request.form.get("action", "preview")

        # Handle preset buttons
        if "preset" in request.form:
            preset = request.form["preset"]
            if preset == "vivid":
                intensity = 0.9
            elif preset == "subtle":
                intensity = 0.4

        # Get form values
        selected_style = request.form.get("style", selected_style)
        intensity = float(request.form.get("intensity", intensity))

        # Handle file upload
        if "file" in request.files and request.files["file"].filename != "":
            file = request.files["file"]
            img_bytes = file.read()

            # Convert original image to base64 for display
            original_img = base64.b64encode(img_bytes).decode('utf-8')

            # Apply selected style
            edited_img_data = apply_style(selected_style, intensity, BytesIO(img_bytes))

            # Handle download
            if action == "download":
                return send_file(
                    BytesIO(base64.b64decode(edited_img_data)),
                    mimetype="image/jpeg",
                    as_attachment=True,
                    download_name=f"styled_{selected_style.lower().replace(' ', '_')}.jpg"
                )

            edited_img = edited_img_data

    return render_template(
        "predefined.html" ,
        styles=list(STYLES.keys()),
        style_emojis=STYLES,
        selected_style=selected_style,
        intensity=intensity,
        original_img=original_img,
        edited_img=edited_img
    )

def apply_style(style_name, intensity, image_stream):
    """Apply the selected style to the image"""
    img = Image.open(image_stream)

    # Convert to RGB if needed
    if img.mode != 'RGB':
        img = img.convert('RGB')

    # Basic style simulation

    # Normalize intensity to reasonable ranges
    intensity = max(0, min(1, float(intensity)))

    if "Ghibli" in style_name.lower():
        # Convert to float32 for processing
        img_array = img_array.astype(np.float32) / 255.0

        blur_sigma = 1 + intensity * 3
        saturation_boost = 1 + intensity * 0.5
        glow_strength = intensity * 0.15

        soft_img = cv2.GaussianBlur(img_array, (0, 0), sigmaX=blur_sigma, sigmaY=blur_sigma)

        hsv = cv2.cvtColor(soft_img, cv2.COLOR_RGB2HSV)
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * saturation_boost, 0, 1)
        enhanced = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)

        painterly = cv2.bilateralFilter(enhanced, d=9,
                                     sigmaColor=0.2 + intensity*0.3,
                                     sigmaSpace=0.2 + intensity*0.3)

        glow = cv2.GaussianBlur(painterly, (0, 0), sigmaX=5, sigmaY=5)
        final_img = cv2.addWeighted(painterly, 1 - glow_strength,
                                   glow, glow_strength, 0)

        final_img = np.clip(final_img * (1 + intensity*0.15) - (intensity*0.05), 0, 1)
        img_array = (final_img * 255).astype(np.uint8)

    elif "Van Gogh" in style_name:
        img_array = np.array(img)
        for _ in range(int(intensity * 3)):
            img_array = cv2.GaussianBlur(img_array, (0,0), intensity*3)
            img_array = cv2.detailEnhance(img_array, sigma_s=10, sigma_r=0.15)
        img = Image.fromarray(img_array)

    elif "Picasso" in style_name:
        img_array = np.array(img)
        edges = cv2.Canny(img_array, 100, 200)
        img_array[edges > 0] = [0, 0, 0]
        img = Image.fromarray(img_array)

    elif "Pop Art" in style_name:
        img = img.quantize(colors=6).convert("RGB")

    elif "Pencil Sketch" in style_name:
        img_array = np.array(img)
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        inv_gray = 255 - gray
        blur = cv2.GaussianBlur(inv_gray, (21, 21), 0)
        sketch = cv2.divide(gray, 255-blur, scale=256)
        img = Image.fromarray(sketch)

    elif "Monet Water Lilies" in style_name:
        try:
            # apply watercolor effect
            if cv2.stylization:  # Check if function exists
                styled = cv2.stylization(img_array, sigma_s=150, sigma_r=0.6)
            else:
                styled = img_array.copy()

            # Add impressionistic blur
            blurred = cv2.GaussianBlur(styled, (0, 0), sigmaX=3*intensity, sigmaY=3*intensity)

            # Blend with original for texture
            blended = cv2.addWeighted(blurred, 0.7, styled, 0.3, 0)

            # Color adjustment -
            hsv = cv2.cvtColor(blended, cv2.COLOR_RGB2HSV)
            hsv[:,:,0] = np.where(hsv[:,:,0] < 30, hsv[:,:,0]-10, hsv[:,:,0])  # Shift greens
            hsv[:,:,0] = np.where(hsv[:,:,0] > 150, hsv[:,:,0]+10, hsv[:,:,0])  # Shift blues
            hsv[:,:,1] = np.clip(hsv[:,:,1]*1.3, 0, 255)  # Boost saturation
            hsv[:,:,2] = np.clip(hsv[:,:,2]*1.1, 0, 255)  # Slight brightness boost

            final = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
            img = Image.fromarray(final)

        except Exception as e:
            print(f"Error applying Monet style: {str(e)}")
            # Fallback to original image if error occurs
            img = Image.fromarray(img_array)

    elif "Oil Painting" in style_name:
        img_array = np.array(img)

        img_array = cv2.xphoto.oilPainting(
            img_array,
            size=int(7*intensity),
            dynRatio=int(1+(intensity*2)))

        img_array = cv2.detailEnhance(img_array, sigma_s=10, sigma_r=0.15)
        img = Image.fromarray(img_array)

    # Convert to JPEG for smaller size
    buffered = BytesIO()
    img.save(buffered, format="JPEG", quality=90)
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

# ========== RUN THE APP ==========
if __name__ == "__main__":
    # Start Flask server on a different port if 5000 is in use
    port = 5000
    print("running....")
    while True:
        try:
            threading.Thread(target=app.run, kwargs={'host': '0.0.0.0', 'port': port}, daemon=True).start()
            break
        except OSError:
            port += 1

    # Set up ngrok tunnel
    ngrok.set_auth_token("2v7LfZICv9D7Lfca21ptCR6Tyvv_6Xf7yXdvDkvkHr5XcFg5U")  # Free demo token
    public_url = ngrok.connect(port, proto="http")
    print(f"\n✨ Your Style Transfer Editor is ready at: {public_url.public_url}\n")

    # Keep the app running
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        print("App stopped")