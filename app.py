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

# ---------------- Input Features ----------------
input_features = [
    "Polypropylene Fiber (gm)", "Steel Fiber (gm)", "Length of PF (mm)", "Diameter of PF (mm)",
    "Length of SF (mm)", "Diameter of SF (mm)", "Cement Content (gm)", "FlyAsh (gm)", "GGBS (gm)",
    "Fine Aggregate (gm)", "NaOH pallets (gm)", "Water (gm)", "Na2SiO3 (gm)", "Water:Binder",
    "Density (kg/m3)", "AGE", "Steel Fiber: Polypropylene Fiber", "Total Binder (gm)",
    "Fine Aggregate : Binder"
]

# ---------------- Valid Ranges ----------------
valid_ranges = {
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
    "Fine Aggregate : Binder": (0.2, 3.0)
}

# ---------------- User Input ----------------
st.header("🧾 Input Parameters")
user_input = {}
out_of_range_flags = {}

col1, col2 = st.columns(2)

for i, feature in enumerate(input_features):
    target_col = col1 if i % 2 == 0 else col2
    with target_col:
        # Skip auto-calculated
        if feature in ["Water:Binder", "Total Binder (gm)", "Fine Aggregate : Binder", "Steel Fiber: Polypropylene Fiber"]:
            user_input[feature] = 0.0
        else:
            user_input[feature] = st.number_input(feature, value=0.0, min_value=0.0, key=feature)

            # Validation only after user changes from default
            low, high = valid_ranges.get(feature, (None, None))
            val = user_input[feature]
            if val != 0.0 and low is not None and high is not None:
                if not (low <= val <= high):
                    out_of_range_flags[feature] = f"⚠️ Value out of valid range ({low} - {high})."
                    st.markdown(
                        f"<p style='color:#E67E22;font-size:13px;margin-top:-8px;'>{out_of_range_flags[feature]}</p>",
                        unsafe_allow_html=True
                    )

# ---------------- Auto-Calculations ----------------
cement = user_input["Cement Content (gm)"]
flyash = user_input["FlyAsh (gm)"]
ggbs = user_input["GGBS (gm)"]
fine_agg = user_input["Fine Aggregate (gm)"]
water = user_input["Water (gm)"]
pf = user_input["Polypropylene Fiber (gm)"]
sf = user_input["Steel Fiber (gm)"]
naoh = user_input["NaOH pallets (gm)"]
na2sio3 = user_input["Na2SiO3 (gm)"]

# Derived features
total_binder = cement + flyash + ggbs
water_binder = water / total_binder if total_binder > 0 else 0
fineagg_binder = fine_agg / total_binder if total_binder > 0 else 0
sf_pf_ratio = sf / pf if pf > 0 else 0

user_input["Total Binder (gm)"] = total_binder
user_input["Water:Binder"] = water_binder
user_input["Fine Aggregate : Binder"] = fineagg_binder
user_input["Steel Fiber: Polypropylene Fiber"] = sf_pf_ratio

# ---------------- Rule for NaOH & Na2SiO3 ----------------
if (flyash > 0 or ggbs > 0) and (naoh == 0 or na2sio3 == 0):
    st.markdown(
        "<p style='color:#E74C3C;font-size:13px;'>⚠️ NaOH pallets and Na₂SiO₃ cannot be zero when FlyAsh or GGBS are present.</p>",
        unsafe_allow_html=True
    )
    out_of_range_flags["NaOH pallets (gm)"] = "invalid"
    out_of_range_flags["Na2SiO3 (gm)"] = "invalid"

# ---------------- Display Auto-Calculated ----------------
st.markdown("### 🔄 Auto-Calculated Fields")
st.write(f"**Total Binder (gm):** {total_binder:.2f}")
st.write(f"**Water:Binder:** {water_binder:.3f}")
st.write(f"**Fine Aggregate : Binder:** {fineagg_binder:.3f}")
st.write(f"**Steel Fiber : Polypropylene Fiber:** {sf_pf_ratio:.3f}")

# ---------------- Predict Button ----------------
if st.button("🔮 Predict"):
    if out_of_range_flags:
        st.error("❌ Please correct the highlighted input values before prediction.")
    else:
        input_df = pd.DataFrame([user_input])
        input_df = input_df[input_features]

        # Clip extreme unseen values
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
