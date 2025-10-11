# ===============================================================
# FRBC Strength Prediction Web App with Sliders
# ===============================================================

import streamlit as st
import pandas as pd
from joblib import load
import matplotlib.pyplot as plt
import numpy as np
import os

# ---------------- Load Pretrained Models ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
model_paths = {
    "Compressive Strength (MPa)": os.path.join(BASE_DIR, "Compressive_Strength_MPa_Model.joblib"),
    "Flexural Strength (MPa)": os.path.join(BASE_DIR, "Flexural_Strength_MPa_Model.joblib"),
    "Breaking Stress (MPa)": os.path.join(BASE_DIR, "Breaking_Stress_MPa_Model.joblib")
}

models = {}
for name, path in model_paths.items():
    if os.path.exists(path):
        models[name] = load(path)
    else:
        st.error(f"❌ Model not found: {path}")
        st.stop()

# ---------------- Feature Names and Ranges ----------------
all_features_order = [
    "Polypropylene Fiber (gm)", "Steel Fiber (gm)", "Length of PF (mm)", "Diameter of PF (mm)",
    "Length of SF (mm)", "Diameter of SF (mm)", "Cement Content (gm)", "FlyAsh (gm)", "GGBS (gm)",
    "Fine Aggregate (gm)", "NaOH pallets (gm)", "Water (gm)", "Na2SiO3 (gm)",
    "Water:Binder", "Density (kg/m3)", "AGE", "Steel Fiber: Polypropylene Fiber",
    "Total Binder (gm)", "Fine Aggregate : Binder"
]

feature_ranges = {
    "Polypropylene Fiber (gm)": (0, 5),
    "Steel Fiber (gm)": (0, 5),
    "Length of PF (mm)": (0, 15),
    "Diameter of PF (mm)": (0, 0.5),
    "Length of SF (mm)": (0, 65),
    "Diameter of SF (mm)": (0, 1.5),
    "Cement Content (gm)": (0, 600),
    "FlyAsh (gm)": (0, 300),
    "GGBS (gm)": (0, 300),
    "Fine Aggregate (gm)": (10, 900),
    "NaOH pallets (gm)": (0, 50),
    "Water (gm)": (1, 250),
    "Na2SiO3 (gm)": (0, 75),
    "Water:Binder": (0.2, 0.8),
    "Density (kg/m3)": (1900, 2500),
    "AGE": (1, 56),
    "Steel Fiber: Polypropylene Fiber": (0, 5),
    "Total Binder (gm)": (1, 700),
    "Fine Aggregate : Binder": (0.2, 10)
}

zero_allowed = {
    "Polypropylene Fiber (gm)", "Steel Fiber (gm)", "Length of PF (mm)", "Diameter of PF (mm)",
    "Length of SF (mm)", "Diameter of SF (mm)", "Cement Content (gm)", "FlyAsh (gm)", "GGBS (gm)"
}

# ---------------- App Title ----------------
st.title("🧠 FRBC Strength Prediction Web App")
st.markdown("Use sliders to enter mix design parameters. Leave optional fields as 0 to auto-calculate.")

# ---------------- User Inputs via Sliders ----------------
user_input = {}
cols = st.columns(2)
for i, feature in enumerate(all_features_order):
    min_val, max_val = feature_ranges[feature]
    with cols[i % 2]:
        user_input[feature] = st.slider(
            feature,
            min_value=float(min_val),
            max_value=float(max_val),
            value=float(min_val),
            step=(max_val - min_val)/100
        )

# ---------------- Derived Features (Optional) ----------------
total_binder = user_input["Cement Content (gm)"] + user_input["FlyAsh (gm)"] + user_input["GGBS (gm)"]

if user_input["Water:Binder"] == 0:
    user_input["Water:Binder"] = (user_input["Water (gm)"] / total_binder) if total_binder > 0 else 0

if user_input["Steel Fiber: Polypropylene Fiber"] == 0:
    pf = user_input["Polypropylene Fiber (gm)"]
    sf = user_input["Steel Fiber (gm)"]
    user_input["Steel Fiber: Polypropylene Fiber"] = (sf / pf) if pf > 0 else 0

user_input["Total Binder (gm)"] = total_binder
user_input["Fine Aggregate : Binder"] = (user_input["Fine Aggregate (gm)"] / total_binder) if total_binder > 0 else 0

# ---------------- Predict Button ----------------
if st.button("🔮 Predict"):
    try:
        # Prepare DataFrame in exact feature order
        input_df = pd.DataFrame([{feature: user_input[feature] for feature in all_features_order}])
        
        # Predict
        predictions = {name: float(model.predict(input_df)[0]) for name, model in models.items()}
        
        # Display predictions
        st.subheader("✅ Predicted Strengths")
        for k, v in predictions.items():
            st.write(f"**{k}:** {v:.3f} MPa")
        
        # Visualization
        fig, ax = plt.subplots()
        ax.bar(predictions.keys(), predictions.values(), color=['skyblue', 'lightgreen', 'salmon'])
        ax.set_ylabel("Strength (MPa)")
        for i, v in enumerate(predictions.values()):
            ax.text(i, v + max(predictions.values())*0.02, f"{v:.2f}", ha='center')
        st.pyplot(fig)
        
        # Export
        st.subheader("💾 Export Prediction")
        result_df = pd.DataFrame([{**user_input, **predictions}])
        buffer = result_df.to_excel(index=False, engine='openpyxl')
        st.download_button(
            label="⬇️ Download as Excel",
            data=buffer,
            file_name="Concrete_Prediction.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    except Exception as e:
        st.error(f"⚠️ Prediction Error: {e}")
