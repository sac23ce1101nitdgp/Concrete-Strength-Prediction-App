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

# ---------------- Feature Names and Ranges ----------------
input_features = [
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

# ---------------- Zero-Allowed and Non-Zero Sets ----------------
zero_allowed = {
    "Polypropylene Fiber (gm)", "Steel Fiber (gm)", "Length of PF (mm)", "Diameter of PF (mm)",
    "Length of SF (mm)", "Diameter of SF (mm)", "Cement Content (gm)", "FlyAsh (gm)", "GGBS (gm)"
}
zero_not_allowed = set(input_features) - zero_allowed

# ---------------- Input UI (Two Columns, Fine Step Sliders) ----------------
st.header("🧾 Input Parameters")
cols = st.columns(2)
user_input = {}

for i, feature in enumerate(input_features):
    low, high = feature_ranges[feature]
    with cols[i % 2]:
        val = st.number_input(
            feature,
            min_value=low,
            max_value=high,
            value=low,
            step=0.0002,
            format="%.6f"
        )
        user_input[feature] = val

# ---------------- Validation Functions ----------------
def check_zero_inputs(inputs_dict):
    invalid_fields = [f for f in zero_not_allowed if inputs_dict[f] == 0]
    return invalid_fields

def check_ranges(inputs_dict):
    out_of_range = []
    for f, (low, high) in feature_ranges.items():
        val = inputs_dict[f]
        if val < low or val > high:
            out_of_range.append(f"{f} (Allowed: {low}-{high}, Entered: {val})")
    return out_of_range

# ---------------- Predict Button ----------------
if st.button("🔮 Predict"):
    # Zero check
    zero_errors = check_zero_inputs(user_input)
    if zero_errors:
        st.error(f"❌ The following fields cannot be zero:\n• " + "\n• ".join(zero_errors))
    else:
        # Range check
        range_errors = check_ranges(user_input)
        if range_errors:
            st.error("⚠️ Inputs outside realistic range:\n• " + "\n• ".join(range_errors))
        else:
            # Prepare DataFrame in correct order
            input_df = pd.DataFrame([{f: user_input[f] for f in input_features}])

            # Prediction
            try:
                predictions = {name: float(model.predict(input_df)[0]) for name, model in models.items()}

                # ---------------- Display Predictions ----------------
                st.subheader("✅ Predicted Outputs")
                for k, v in predictions.items():
                    st.write(f"**{k}:** {v:.3f} MPa")

                # ---------------- Visualization ----------------
                st.subheader("📊 Predicted Strengths")
                fig, ax = plt.subplots(figsize=(8,5))
                bars = ax.bar(predictions.keys(), predictions.values(), color=['skyblue','lightgreen','salmon'])
                ax.set_ylabel("Strength (MPa)")
                ax.set_ylim(0, max(predictions.values())*1.2)
                for i, v in enumerate(predictions.values()):
                    ax.text(i, v + max(predictions.values())*0.02, f"{v:.2f}", ha='center', fontsize=9)
                st.pyplot(fig)

                # ---------------- Export to Excel ----------------
                st.subheader("💾 Export Prediction")
                result_df = pd.DataFrame([{**user_input, **predictions}])
                buffer = BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    result_df.to_excel(writer, index=False)
                buffer.seek(0)

                st.download_button(
                    label="⬇️ Download as Excel",
                    data=buffer,
                    file_name="Concrete_Prediction.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            except Exception as e:
                st.error(f"⚠️ Prediction Error: {e}")
