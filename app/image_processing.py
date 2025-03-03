import cv2
import numpy as np
import base64

def image_to_base64(img, ext=".jpg"):
    success, buffer = cv2.imencode(ext, img)
    if not success:
        raise ValueError("Image encoding failed")
    img_as_text = base64.b64encode(buffer).decode('utf-8')
    mime = "image/png" if ext == ".png" else "image/jpeg"
    return f"data:{mime};base64,{img_as_text}"

def color_transfer(source, target):
    # Convert images to LAB color space
    source_lab = cv2.cvtColor(source, cv2.COLOR_BGR2LAB).astype("float32")
    target_lab = cv2.cvtColor(target, cv2.COLOR_BGR2LAB).astype("float32")
    
    (l_mean_src, a_mean_src, b_mean_src) = cv2.mean(source_lab)[:3]
    l_std_src = np.std(source_lab[:, :, 0])
    a_std_src = np.std(source_lab[:, :, 1])
    b_std_src = np.std(source_lab[:, :, 2])
    
    l_mean_tar = np.mean(target_lab[:, :, 0])
    a_mean_tar = np.mean(target_lab[:, :, 1])
    b_mean_tar = np.mean(target_lab[:, :, 2])
    
    l_std_tar = np.std(target_lab[:, :, 0])
    a_std_tar = np.std(target_lab[:, :, 1])
    b_std_tar = np.std(target_lab[:, :, 2])
    
    (l, a, b) = cv2.split(target_lab)
    l = ((l - l_mean_tar) * (l_std_src / (l_std_tar + 1e-8))) + l_mean_src
    a = ((a - a_mean_tar) * (a_std_src / (a_std_tar + 1e-8))) + a_mean_src
    b = ((b - b_mean_tar) * (b_std_src / (b_std_tar + 1e-8))) + b_mean_src
    
    transfer_lab = cv2.merge([l, a, b])
    transfer_lab = np.clip(transfer_lab, 0, 255).astype("uint8")
    transfer_bgr = cv2.cvtColor(transfer_lab, cv2.COLOR_LAB2BGR)
    return transfer_bgr

def simulate_color_blindness(image, deficiency):
    image_float = image.astype(np.float32) / 255.0
    image_rgb = cv2.cvtColor(image_float, cv2.COLOR_BGR2RGB)
    
    if deficiency == "protanopia":
        M = np.array([[0.56667, 0.43333, 0],
                      [0.55833, 0.44167, 0],
                      [0,       0.24167, 0.75833]])
    elif deficiency == "deuteranopia":
        M = np.array([[0.625, 0.375, 0],
                      [0.70,  0.30,  0],
                      [0,     0.30,  0.70]])
    elif deficiency == "tritanopia":
        M = np.array([[0.95,    0.05,   0],
                      [0,       0.43333, 0.56667],
                      [0,       0.475,   0.525]])
    else:
        return image
    simulated = np.dot(image_rgb, M.T)
    simulated = np.clip(simulated, 0, 1)
    simulated_uint8 = (simulated * 255).astype(np.uint8)
    simulated_bgr = cv2.cvtColor(simulated_uint8, cv2.COLOR_RGB2BGR)
    return simulated_bgr