import streamlit as st
from rembg import remove
from PIL import Image, ImageEnhance
import io
import numpy as np
from streamlit_drawable_canvas import st_canvas

HIGH_RES_WIDTH = 1200
DISPLAY_WIDTH = 600

def resize_image(image, target_width):
    w, h = image.size
    if w > target_width:
        ratio = target_width / w
        new_h = int(h * ratio)
        return image.resize((target_width, new_h), Image.LANCZOS)
    return image

@st.cache_data
def remove_background(input_data_bytes):
    output_image_data = remove(input_data_bytes)
    output_image = Image.open(io.BytesIO(output_image_data)).convert("RGBA")
    return output_image

def apply_adjustments(image, contrast_factor, brightness_factor):
    adjusted_image = image.copy().convert("RGBA")
    contraster = ImageEnhance.Contrast(adjusted_image)
    adjusted_image = contraster.enhance(contrast_factor)
    brighter = ImageEnhance.Brightness(adjusted_image)
    final_img = brighter.enhance(brightness_factor)
    return final_img

def apply_mask_corrections(high_res_original, high_res_cutout, drawing_data, mode):
    small_mask_array = np.array(drawing_data.image_data)
    
    if small_mask_array.size == 0 or np.all(small_mask_array[:, :, 3] == 0):
        return high_res_cutout

    small_mask_alpha = Image.fromarray(small_mask_array[:, :, 3])
    high_res_mask = small_mask_alpha.resize(high_res_cutout.size, resample=Image.NEAREST)
    high_res_mask_array = np.array(high_res_mask)

    cutout_array = np.array(high_res_cutout.convert("RGBA"))
    original_array = np.array(high_res_original.convert("RGBA"))

    drawing_zone = high_res_mask_array > 0
    
    if mode == "Erase":
        cutout_array[drawing_zone, 3] = 0
    elif mode == "Restore":
        cutout_array[drawing_zone] = original_array[drawing_zone]

    return Image.fromarray(cutout_array, 'RGBA')

st.set_page_config(
    page_title="Background Remover & Editor",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("✂️ Background Remover")

uploaded_file = st.file_uploader(
    "Încarcă o imagine (JPG sau PNG):", 
    type=["jpg", "jpeg", "png"]
)

if uploaded_file is not None:
    file_bytes = uploaded_file.getvalue()
    
    raw_img = Image.open(io.BytesIO(file_bytes))
    high_res_image = resize_image(raw_img, HIGH_RES_WIDTH)
    
    buf_high = io.BytesIO()
    high_res_image.save(buf_high, format="PNG")
    high_res_bytes = buf_high.getvalue()
    high_res_cutout = remove_background(high_res_bytes)

    display_image = resize_image(high_res_image, DISPLAY_WIDTH)
    display_cutout = resize_image(high_res_cutout, DISPLAY_WIDTH)

    with st.sidebar:
        st.header("⚙️ Tool-uri")
        st.subheader("1. Ajustări")
        contrast_val = st.slider("Contrast", 0.5, 2.0, 1.0, 0.05)
        brightness_val = st.slider("Luminozitate", 0.5, 2.0, 1.0, 0.05)
        
        st.subheader("2. Magic Brush Manual")
        mode = st.radio("Mod Pensulă:", ["Erase", "Restore"])
        brush_size = st.slider("Dimensiune Pensulă", 5, 50, 20, 1)
        stroke_color = "rgba(0, 255, 0, 0.3)" if mode == "Restore" else "rgba(255, 0, 0, 0.3)"
        
    col_original, col_edited = st.columns(2)
    
    with col_original:
        st.header("Imagine Originală")
        st.image(display_image, use_column_width=False, width=DISPLAY_WIDTH)
        
    with col_edited:
        st.header("Imagine Editată")
        
        canvas_result = st_canvas(
            fill_color="rgba(0, 0, 0, 0)",  
            stroke_width=brush_size,
            stroke_color=stroke_color,
            background_image=display_cutout,
            update_streamlit=True,
            height=display_cutout.height,
            width=display_cutout.width,
            drawing_mode="freedraw",
            key="canvas_editor",
        )

        final_high_res = high_res_cutout.copy()
        
        if canvas_result.image_data is not None:
            final_high_res = apply_mask_corrections(
                high_res_image,
                high_res_cutout,
                canvas_result,
                mode
            )
            
        final_high_res = apply_adjustments(final_high_res, contrast_val, brightness_val)
        
        st.image(final_high_res, caption="Rezultat Final (Preview)", use_column_width=True)

        buf = io.BytesIO()
        final_high_res.save(buf, format="PNG")
        byte_im = buf.getvalue()

        st.download_button(
            label="Descărcare Imagine PNG",
            data=byte_im,
            file_name="imagine_editata_finala.png",
            mime="image/png"
        )
else:
    st.info("Vă rugăm să încărcați o imagine pentru a începe editarea.")
