# ==================== FRBC Strength Prediction Web App ====================
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
Enter all mix design parameters below to predict:
- **Compressive Strength (MPa)**
- **Flexural Strength (MPa)**
- **Breaking Stress (MPa)**
""")

# ---------------- Input Feature Order & Ranges ----------------
feature_order = [
    "Polypropylene Fiber (gm)", "Steel Fiber (gm)", "Length of PF (mm)", "Diameter of PF (mm)",
    "Length of SF (mm)", "Diameter of SF (mm)", "Cement Content (gm)", "FlyAsh (gm)", "GGBS (gm)",
    "Fine Aggregate (gm)", "NaOH pallets (gm)", "Water (gm)", "Na2SiO3 (gm)",
    "Water:Binder", "Density (kg/m3)", "AGE", "Steel Fiber: Polypropylene Fiber",
    "Total Binder (gm)", "Fine Aggregate : Binder"
]

feature_ranges = {
    "Polypropylene Fiber (gm)": (0.0, 5.0),
    "Steel Fiber (gm)": (0.0, 5.0),
    "Length of PF (mm)": (0.0, 15.0),
    "Diameter of PF (mm)": (0.0, 0.5),
    "Length of SF (mm)": (0.0, 65.0),
    "Diameter of SF (mm)": (0.0, 1.5),
    "Cement Content (gm)": (0.0, 600.0),
    "FlyAsh (gm)": (0.0, 300.0),
    "GGBS (gm)": (0.0, 300.0),
    "Fine Aggregate (gm)": (10.0, 900.0),
    "NaOH pallets (gm)": (0.0, 50.0),
    "Water (gm)": (1.0, 250.0),
    "Na2SiO3 (gm)": (0.0, 75.0),
    "Water:Binder": (0.2, 0.8),
    "Density (kg/m3)": (1900.0, 2500.0),
    "AGE": (1.0, 56.0),
    "Steel Fiber: Polypropylene Fiber": (0.0, 5.0),
    "Total Binder (gm)": (1.0, 700.0),
    "Fine Aggregate : Binder": (0.2, 10.0)
}

# ---------------- Zero Allowed vs Non-Zero Required ----------------
zero_allowed = {
    "Polypropylene Fiber (gm)", "Steel Fiber (gm)", "Length of PF (mm)", "Diameter of PF (mm)",
    "Length of SF (mm)", "Diameter of SF (mm)", "Cement Content (gm)", "FlyAsh (gm)", "GGBS (gm)"
}
zero_not_allowed = set(feature_order) - zero_allowed

# ---------------- Input UI (Two Columns) ----------------
st.header("🧾 Input Parameters")
cols = st.columns(2)
user_input = {}

for i, feature in enumerate(feature_order):
    low, high = feature_ranges[feature]
    with cols[i % 2]:
        val = st.number_input(
            label=feature,
            min_value=float(low),
            max_value=float(high),
            value=float(low),
            step=0.0002,
            format="%.6f"
        )
        user_input[feature] = val

# ---------------- Validation Functions ----------------
def validate_zero_inputs(data):
    invalid = [f for f in zero_not_allowed if data[f] == 0.0]
    if invalid:
        return False, "⚠️ The following parameters cannot be zero:\n• " + "\n• ".join(invalid)
    return True, ""

def validate_range_inputs(data):
    out_of_range = []
    for f, (low, high) in feature_ranges.items():
        val = data[f]
        if val < low or val > high:
            out_of_range.append(f"{f} (Allowed: {low}–{high}, Entered: {val})")
    if out_of_range:
        return False, "⚠️ Inputs outside realistic range:\n• " + "\n• ".join(out_of_range)
    return True, ""

# ---------------- Predict Button ----------------
if st.button("🔮 Predict"):
    is_valid_zero, msg_zero = validate_zero_inputs(user_input)
    is_valid_range, msg_range = validate_range_inputs(user_input)

    if not is_valid_zero:
        st.error(msg_zero)
    elif not is_valid_range:
        st.error(msg_range)
    else:
        try:
            # Ensure DataFrame matches training feature order
            input_df = pd.DataFrame([{f: user_input[f] for f in feature_order}])

            # Predict
            predictions = {name: float(model.predict(input_df)[0]) for name, model in models.items()}

            # Display Predictions
            st.subheader("✅ Predicted Outputs")
            for k, v in predictions.items():
                st.write(f"**{k}:** {v:.3f} MPa")

            # Visualization
            st.subheader("📊 Predicted Strengths Visualization")
            fig, ax = plt.subplots(figsize=(8, 5))
            ax.bar(predictions.keys(), predictions.values(), color=['skyblue', 'lightgreen', 'salmon'])
            ax.set_ylabel("Strength (MPa)")
            ax.set_ylim(0, max(predictions.values()) * 1.2)
            for i, v in enumerate(predictions.values()):
                ax.text(i, v + max(predictions.values())*0.02, f"{v:.2f}", ha='center', fontsize=9)
            st.pyplot(fig)

            # Export to Excel
            st.subheader("💾 Export Prediction")
            result_df = pd.DataFrame([{**user_input, **predictions}])
            buffer = BytesIO()
            result_df.to_excel(buffer, index=False)
            buffer.seek(0)

            st.download_button(
                label="⬇️ Download Prediction as Excel",
                data=buffer,
                file_name="Concrete_Prediction.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        except Exception as e:
            st.error(f"⚠️ Prediction Error: {e}")
