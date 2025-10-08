# ==================== Concrete Strength Prediction Web App ====================
import streamlit as st
import pandas as pd
from joblib import load
import matplotlib.pyplot as plt
from io import BytesIO
import os

# ---------------- BASE DIRECTORY ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------------- Load Pre-trained Models ----------------
model_paths = {
    "Compressive Strength (MPa)": os.path.join(BASE_DIR, "Compressive_Strength_MPa_Model.joblib"),
    "Flexural Strength (MPa)": os.path.join(BASE_DIR, "Flexural_Strength_MPa_Model.joblib"),
    "Breaking Stress (MPa)": os.path.join(BASE_DIR, "Breaking_Stress_MPa_Model.joblib")
}

# Load models safely
models = {}
for name, path in model_paths.items():
    if os.path.exists(path):
        models[name] = load(path)
    else:
        st.error(f"Model file not found: {path}")
        st.stop()  # Stop the app if a model is missing

# ---------------- App Title ----------------
st.title("🧠 FRBC Strength Prediction Web App")
st.markdown("""
Enter the 19 input features below to predict:
- Compressive Strength (MPa)
- Flexural Strength (MPa)
- Breaking Stress (MPa)
""")

# ---------------- Input Fields ----------------
input_features = [
    "Polypropylene Fiber (gm)", "Steel Fiber (gm)", "Length of PF (mm)", "Diameter of PF (mm)",
    "Length of SF (mm)", "Diameter of SF (mm)", "Cement Content (gm)", "FlyAsh (gm)", "GGBS (gm)",
    "Fine Aggregate (gm)", "NaOH pallets (gm)", "Water (gm)", "Na2SiO3 (gm)", "Water:Binder",
    "Density (kg/m3)", "AGE", "Steel Fiber: Polypropylene Fiber", "Total Binder (gm)",
    "Fine Aggregate : Binder"
]

user_input = {}
st.header("Input Parameters")
for feature in input_features:
    user_input[feature] = st.number_input(feature, value=0.0)

# ---------------- Predict Button ----------------
if st.button("🔮 Predict"):
    input_df = pd.DataFrame([user_input])
    
    # Run predictions
    predictions = {name: model.predict(input_df)[0] for name, model in models.items()}
    
    # ---------------- Display Predictions ----------------
    st.subheader("✅ Predicted Outputs")
    for k, v in predictions.items():
        st.write(f"**{k}:** {v:.3f} MPa")
    
 # ---------------- Bar Chart ----------------
st.subheader("📊 Predicted Strengths Visualization")
fig, ax = plt.subplots(figsize=(8,5))  # Optional: adjust figure size
bars = ax.bar(predictions.keys(), predictions.values(), color=['skyblue','lightgreen','salmon'])

ax.set_ylabel("Strength (MPa)", fontsize=10)  # smaller y-axis label
ax.set_ylim(0, max(predictions.values())*1.2)
ax.tick_params(axis='x', labelsize=9)  # smaller x-axis labels
ax.tick_params(axis='y', labelsize=9)  # smaller y-axis labels

# Display value on top of each bar
for i, v in enumerate(predictions.values()):
    ax.text(i, v + max(predictions.values())*0.02, f"{v:.2f}", ha='center', fontsize=9)  # smaller text

st.pyplot(fig)

    
    # ---------------- Download Prediction as Excel ----------------
    st.subheader("💾 Export Prediction")
    result_df = pd.DataFrame([{**user_input, **predictions}])
    buffer = BytesIO()
    
    # Use ExcelWriter with openpyxl engine for Streamlit Cloud compatibility
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        result_df.to_excel(writer, index=False)
    
    buffer.seek(0)
    
    st.download_button(
        label="Download Prediction as Excel",
        data=buffer,
        file_name="Concrete_Prediction.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
