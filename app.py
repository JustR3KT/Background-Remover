import streamlit as st
from rembg import remove
from PIL import Image, ImageEnhance
import io
import numpy as np
from streamlit_drawable_canvas import st_canvas

# Funcții de bază

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
    
    # Imaginea desenată (masca de corecție) este un array RGBA
    correction_mask_array = np.array(drawing_data.image_data)

    if correction_mask_array.size == 0 or np.all(correction_mask_array[:, :, 3] == 0):
        # Nicio corecție aplicată
        return original_cutout

    cutout_array = np.array(original_cutout.copy())
    
    # Canalele de culori RGB
    cutout_rgb = cutout_array[:, :, :3]
    # Canalul Alpha (transparența)
    cutout_alpha = cutout_array[:, :, 3]

    # Determinăm masca de corecție din desen (unde opacitatea e > 0)
    # Aici presupunem că desenul a fost făcut peste tot cu o culoare opacă (e.g., negru)
    drawing_mask = correction_mask_array[:, :, 3] > 0
    
    if mode == "Erase":
        # Pentru ștergere (Erase), setăm canalul Alpha la 0 (transparent) în zonele desenate
        cutout_alpha[drawing_mask] = 0
        
    elif mode == "Restore":
        # Pentru restaurare (Restore), setăm canalul Alpha la 255 (opac) în zonele desenate
        # Atenție: Restaurarea nu poate aduce înapoi datele RGB originale, ci doar opacitatea
        # Va dezvălui fundalul original (care e zero în imaginea decupată, deci negru/maro),
        # de aceea este mai util să refolosim masca originală de la rembg și să o corectăm.
        # Pentru simplitate, setăm opacitatea la 255 (complet vizibil)
        cutout_alpha[drawing_mask] = 255
        
        # O metodă mai complexă ar presupune reluarea procesului de decupare inițial și
        # modificarea măștii *înainte* de aplicare. Pentru scopul nostru, lăsăm opacitatea 255.


    # Reconstruim imaginea finală
    corrected_array = np.dstack((cutout_rgb, cutout_alpha))
    corrected_image = Image.fromarray(corrected_array, 'RGBA')
    
    return corrected_image


# =================================================================
# Interfața Streamlit
# =================================================================

st.set_page_config(
    page_title="Background Remover & Editor (Python)",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("✂️ Aplicație Background Remover și Editare Avansată")

uploaded_file = st.file_uploader(
    "Încarcă o imagine (JPG sau PNG):", 
    type=["jpg", "jpeg", "png"]
)

if uploaded_file is not None:
    
    # Citim și decupăm imaginea o singură dată
    uploaded_file.seek(0)
    original_image = Image.open(uploaded_file)
    uploaded_file.seek(0) 
    cutout_image_original = remove_background(uploaded_file)
    
    # --- Coloana 1: Tool-uri ---
    with st.sidebar:
        st.header("⚙️ Tool-uri")
        
        # 1. Ajustări (Adjust)
        st.subheader("1. Ajustări")
        contrast_val = st.slider("Contrast", 0.5, 2.0, 1.0, 0.05)
        brightness_val = st.slider("Luminozitate", 0.5, 2.0, 1.0, 0.05)
        
        # 2. Magic Brush (Erase/Restore)
        st.subheader("2. Magic Brush Manual")
        
        mode = st.radio("Mod Pensulă:", ["Erase", "Restore"])
        
        brush_size = st.slider("Dimensiune Pensulă", 5, 50, 20, 1)

        # Setăm culoarea pensulei la negru pentru a genera o mască consistentă
        # Modul "Erase" sau "Restore" va fi aplicat bazat pe switch-ul de mai sus
        stroke_color = "#000000"
        
        st.info(f"Desenați pe imaginea decupată de alături. Modul curent: **{mode}**.")


    # --- Coloana 2: Imagini ---
    
    col_original, col_edited = st.columns(2)
    
    # Imaginea Originală
    with col_original:
        st.header("Imagine Originală")
        st.image(original_image, use_column_width=True)

    # Imaginea Editabilă (Cutout + Brush + Adjust)
    with col_edited:
        st.header("Imagine Editată (Brush & Adjust)")
        
        # 3. Canvas pentru desenare (Magic Brush)
        
        canvas_result = st_canvas(
            fill_color="rgba(0, 0, 0, 0)",  
            stroke_width=brush_size,
            stroke_color=stroke_color,
            background_image=cutout_image_original, # Afișăm imaginea decupată ca fundal
            update_streamlit=True,
            height=cutout_image_original.height,
            width=cutout_image_original.width,
            drawing_mode="freedraw",
            key="canvas",
        )

        final_edited_image = cutout_image_original.copy()
        
        # Aplicați corecțiile doar dacă s-a desenat ceva
        if canvas_result.image_data is not None:
            
            # Aplicăm corecțiile (Erase/Restore)
            final_edited_image = apply_mask_corrections(
                cutout_image_original, 
                canvas_result, 
                mode
            )

        # Aplicați ajustările (Contrast/Brightness)
        final_edited_image = apply_adjustments(final_edited_image, contrast_val, brightness_val)
        
        st.image(final_edited_image, caption="Rezultat Final (Transparent)", use_column_width=True)
        
        # Opțiune de descărcare
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