# ==================== Concrete Strength Prediction Web App ====================
import streamlit as st
import pandas as pd
from joblib import load
import matplotlib.pyplot as plt
from io import BytesIO
import os
import numpy as np

# ---------------- BASE DIRECTORY ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------------- Load Pre-trained Models ----------------
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
        st.error(f"❌ Model file not found: {path}")
        st.stop()

# ---------------- App Title ----------------
st.title("🧠 Fiber Reinforced Binder Composite (FRBC) Strength Prediction")
st.markdown("""
Enter the mix design parameters below to predict:
- **Compressive Strength (MPa)**
- **Flexural Strength (MPa)**
- **Breaking Stress (MPa)**
""")

# ---------------- Input Fields ----------------
input_features = [
    "Polypropylene Fiber (gm)", "Steel Fiber (gm)", "Length of PF (mm)", "Diameter of PF (mm)",
    "Length of SF (mm)", "Diameter of SF (mm)", "Cement Content (gm)", "FlyAsh (gm)", "GGBS (gm)",
    "Fine Aggregate (gm)", "NaOH pallets (gm)", "Water (gm)", "Na2SiO3 (gm)", "Water:Binder",
    "Density (kg/m3)", "AGE", "Steel Fiber: Polypropylene Fiber", "Total Binder (gm)",
    "Fine Aggregate : Binder"
]

# ---------------- User Input ----------------
st.header("🧾 Input Parameters")
user_input = {}

for feature in input_features:
    if feature in ["Water:Binder", "Total Binder (gm)", "Fine Aggregate : Binder", "Steel Fiber: Polypropylene Fiber"]:
        user_input[feature] = 0.0  # Will be auto-calculated
    else:
        user_input[feature] = st.number_input(feature, value=0.0, min_value=0.0)

# ---------------- Auto-Calculations ----------------
cement = user_input["Cement Content (gm)"]
flyash = user_input["FlyAsh (gm)"]
ggbs = user_input["GGBS (gm)"]
fine_agg = user_input["Fine Aggregate (gm)"]
water = user_input["Water (gm)"]
pf = user_input["Polypropylene Fiber (gm)"]
sf = user_input["Steel Fiber (gm)"]

# Calculate derived features safely
total_binder = cement + flyash + ggbs
water_binder = water / total_binder if total_binder > 0 else 0
fineagg_binder = fine_agg / total_binder if total_binder > 0 else 0
sf_pf_ratio = sf / pf if pf > 0 else 0

user_input["Total Binder (gm)"] = total_binder
user_input["Water:Binder"] = water_binder
user_input["Fine Aggregate : Binder"] = fineagg_binder
user_input["Steel Fiber: Polypropylene Fiber"] = sf_pf_ratio

# Display auto-calculated fields
st.markdown("### 🔄 Auto-Calculated Fields")
st.write(f"**Total Binder (gm):** {total_binder:.2f}")
st.write(f"**Water:Binder:** {water_binder:.3f}")
st.write(f"**Fine Aggregate : Binder:** {fineagg_binder:.3f}")
st.write(f"**Steel Fiber : Polypropylene Fiber:** {sf_pf_ratio:.3f}")

# ---------------- Input Validation ----------------
invalid_inputs = []

# Allow these to be zero
allowed_zero = {
    "Polypropylene Fiber (gm)", "Steel Fiber (gm)", "Length of PF (mm)", "Diameter of PF (mm)",
    "Length of SF (mm)", "Diameter of SF (mm)", "Cement Content (gm)", "FlyAsh (gm)", "GGBS (gm)"
}

# These must be non-zero
non_zero = {
    "Fine Aggregate (gm)", "NaOH pallets (gm)", "Water (gm)", "Na2SiO3 (gm)",
    "Water:Binder", "Density (kg/m3)", "AGE", "Steel Fiber: Polypropylene Fiber",
    "Total Binder (gm)", "Fine Aggregate : Binder"
}

for key in non_zero:
    if key in user_input and user_input[key] == 0:
        invalid_inputs.append(key)

if invalid_inputs:
    st.warning(f"⚠️ The following inputs must be **non-zero**: {', '.join(invalid_inputs)}")

# ---------------- Predict Button ----------------
if st.button("🔮 Predict"):
    if invalid_inputs:
        st.error("❌ Please correct the invalid inputs before prediction.")
    else:
        input_df = pd.DataFrame([user_input])
        input_df = input_df[input_features]  # ensure correct order

        # Clip extreme unseen values (avoid model extrapolation errors)
        input_df = input_df.clip(lower=0, upper=np.percentile(input_df, 99, axis=0))

        # Run predictions
        predictions = {}
        for name, model in models.items():
            try:
                predictions[name] = float(model.predict(input_df)[0])
            except Exception as e:
                st.error(f"Prediction error for {name}: {e}")
                predictions[name] = np.nan

        # ---------------- Display Predictions ----------------
        st.subheader("✅ Predicted Outputs")
        for k, v in predictions.items():
            if not np.isnan(v):
                st.write(f"**{k}:** {v:.3f} MPa")
            else:
                st.write(f"**{k}:** Prediction unavailable")

        # ---------------- Visualization ----------------
        st.subheader("📊 Predicted Strengths Visualization")
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.bar(predictions.keys(), predictions.values(), color=['skyblue', 'lightgreen', 'salmon'])
        ax.set_ylabel("Strength (MPa)", fontsize=10)
        ax.tick_params(axis='x', labelsize=9)
        ax.tick_params(axis='y', labelsize=9)
        for i, v in enumerate(predictions.values()):
            ax.text(i, v + 1, f"{v:.2f}", ha='center', fontsize=9)
        st.pyplot(fig)

        # ---------------- Export as Excel ----------------
        st.subheader("💾 Export Prediction")
        result_df = pd.DataFrame([{**user_input, **predictions}])
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            result_df.to_excel(writer, index=False)
        buffer.seek(0)

        st.download_button(
            label="⬇️ Download Prediction as Excel",
            data=buffer,
            file_name="Concrete_Prediction.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
