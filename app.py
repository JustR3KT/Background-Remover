import streamlit as st
from rembg import remove
from PIL import Image, ImageEnhance
import io
import numpy as np
from streamlit_drawable_canvas import st_canvas

@st.cache_data
def remove_background(input_data):
    output_image_data = remove(input_data.read())
    output_image = Image.open(io.BytesIO(output_image_data)).convert("RGBA")
    return output_image

def apply_adjustments(image, contrast_factor, brightness_factor):
    adjusted_image = image.copy().convert("RGBA") 
    
    contraster = ImageEnhance.Contrast(adjusted_image)
    adjusted_image = contraster.enhance(contrast_factor)
    
    brighter = ImageEnhance.Brightness(adjusted_image)
    final_img = brighter.enhance(brightness_factor)
    
    return final_img

def apply_mask_corrections(original_cutout, drawing_data, mode):
    
    correction_mask_array = np.array(drawing_data.image_data)

    if correction_mask_array.size == 0 or np.all(correction_mask_array[:, :, 3] == 0):
        return original_cutout

    cutout_array = np.array(original_cutout.copy())
    cutout_rgb = cutout_array[:, :, :3]
    cutout_alpha = cutout_array[:, :, 3]
    drawing_mask = correction_mask_array[:, :, 3] > 0
    
    if mode == "Erase":
        cutout_alpha[drawing_mask] = 0
        
    elif mode == "Restore":
        cutout_alpha[drawing_mask] = 255
    corrected_array = np.dstack((cutout_rgb, cutout_alpha))
    corrected_image = Image.fromarray(corrected_array, 'RGBA')
    
    return corrected_image

st.set_page_config(
    page_title="Background Remover & Editor)",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("✂️ Background Remover")

uploaded_file = st.file_uploader(
    "Încarcă o imagine (JPG sau PNG):", 
    type=["jpg", "jpeg", "png"]
)

if uploaded_file is not None:
    

    uploaded_file.seek(0)
    original_image = Image.open(uploaded_file)
    uploaded_file.seek(0) 
    cutout_image_original = remove_background(uploaded_file)

    with st.sidebar:
        st.header("⚙️ Tool-uri")

        st.subheader("1. Ajustări")
        contrast_val = st.slider("Contrast", 0.5, 2.0, 1.0, 0.05)
        brightness_val = st.slider("Luminozitate", 0.5, 2.0, 1.0, 0.05)
        st.subheader("2. Magic Brush Manual")
        
        mode = st.radio("Mod Pensulă:", ["Erase", "Restore"])
        
        brush_size = st.slider("Dimensiune Pensulă", 5, 50, 20, 1)
        stroke_color = "#000000"
        
        st.info(f"Desenați pe imaginea decupată de alături. Modul curent: **{mode}**.")
    col_original, col_edited = st.columns(2)
    with col_original:
        st.header("Imagine Originală")
        st.image(original_image, use_column_width=True)
    with col_edited:
        st.header("Imagine Editată")

        canvas_result = st_canvas(
            fill_color="rgba(0, 0, 0, 0)",  
            stroke_width=brush_size,
            stroke_color=stroke_color,
            background_image=cutout_image_original,
            update_streamlit=True,
            height=cutout_image_original.height,
            width=cutout_image_original.width,
            drawing_mode="freedraw",
            key="canvas",
        )

        final_edited_image = cutout_image_original.copy()
        if canvas_result.image_data is not None:

            final_edited_image = apply_mask_corrections(
                cutout_image_original, 
                canvas_result, 
                mode
            )
        final_edited_image = apply_adjustments(final_edited_image, contrast_val, brightness_val)
        
        st.image(final_edited_image, caption="Rezultat Final", use_column_width=True)

        buf = io.BytesIO()
        final_edited_image.save(buf, format="PNG")
        byte_im = buf.getvalue()

        st.download_button(
            label="Descărcare Imagine PNG",
            data=byte_im,
            file_name="imagine_editata_finala.png",
            mime="image/png"
        )
else:
    st.info("Vă rugăm să încărcați o imagine pentru a începe editarea.")
