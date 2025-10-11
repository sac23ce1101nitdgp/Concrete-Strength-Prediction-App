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

models = {}
for name, path in model_paths.items():
    if os.path.exists(path):
        models[name] = load(path)
    else:
        st.error(f"Model file not found: {path}")
        st.stop()

# ---------------- App Title ----------------
st.title("🧠 FRBC Strength Prediction Web App")
st.markdown("""
Enter the input features below to predict:
- **Compressive Strength (MPa)**
- **Flexural Strength (MPa)**
- **Breaking Stress (MPa)**
""")

# ---------------- Input Feature Limits ----------------
feature_limits = {
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

# ---------------- Input UI (Two Columns) ----------------
st.header("Input Parameters")
cols = st.columns(2)
user_input = {}

for i, (feature, (low, high)) in enumerate(feature_limits.items()):
    with cols[i % 2]:
        val = st.number_input(feature, value=0.0, step=0.1, key=feature)
        if val < low or val > high:
            st.warning(f"⚠️ Value out of valid range ({low}–{high})")
        user_input[feature] = val

# ---------------- Auto-Calculations ----------------
cement = user_input["Cement Content (gm)"]
flyash = user_input["FlyAsh (gm)"]
ggbs = user_input["GGBS (gm)"]
fineagg = user_input["Fine Aggregate (gm)"]
water = user_input["Water (gm)"]
pf = user_input["Polypropylene Fiber (gm)"]
sf = user_input["Steel Fiber (gm)"]

# Total Binder
total_binder = cement + flyash + ggbs
user_input["Total Binder (gm)"] = total_binder

# Water/Binder ratio
user_input["Water:Binder"] = (water / total_binder) if total_binder > 0 else 0

# Fine Aggregate/Binder ratio
user_input["Fine Aggregate : Binder"] = (fineagg / total_binder) if total_binder > 0 else 0

# Steel Fiber/Polypropylene Fiber ratio
user_input["Steel Fiber: Polypropylene Fiber"] = (sf / pf) if pf > 0 else 0

# Zero-out NaOH and Na2SiO3 if both FlyAsh and GGBS are zero
if flyash == 0 and ggbs == 0:
    user_input["NaOH pallets (gm)"] = 0
    user_input["Na2SiO3 (gm)"] = 0

# ---------------- Validation Before Prediction ----------------
critical_fields = ["Cement Content (gm)", "Fine Aggregate (gm)", "Water (gm)", "Density (kg/m3)"]
invalid_inputs = any(user_input[f] == 0 for f in critical_fields)

# ---------------- Predict Button ----------------
if st.button("🔮 Predict"):
    if invalid_inputs:
        st.error("❌ Invalid input detected: Please ensure key parameters (Cement, Water, Fine Aggregate, and Density) are non-zero.")
    elif total_binder == 0:
        st.error("❌ Total Binder cannot be zero. Please enter valid binder quantities.")
    else:
        input_df = pd.DataFrame([user_input])
        try:
            predictions = {name: model.predict(input_df)[0] for name, model in models.items()}

            # ---------------- Display Predictions ----------------
            st.subheader("✅ Predicted Outputs")
            for k, v in predictions.items():
                st.write(f"**{k}:** {v:.3f} MPa")

            # ---------------- Visualization ----------------
            st.subheader("📊 Predicted Strengths Visualization")
            fig, ax = plt.subplots(figsize=(8, 5))
            bars = ax.bar(predictions.keys(), predictions.values(), color=['skyblue', 'lightgreen', 'salmon'])
            ax.set_ylabel("Strength (MPa)")
            ax.set_ylim(0, max(predictions.values()) * 1.2)
            for i, v in enumerate(predictions.values()):
                ax.text(i, v + max(predictions.values()) * 0.02, f"{v:.2f}", ha='center', fontsize=9)
            st.pyplot(fig)

            # ---------------- Export to Excel ----------------
            st.subheader("💾 Export Prediction")
            result_df = pd.DataFrame([{**user_input, **predictions}])
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                result_df.to_excel(writer, index=False)
            buffer.seek(0)

            st.download_button(
                label="Download Prediction as Excel",
                data=buffer,
                file_name="Concrete_Prediction.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except Exception as e:
            st.error(f"⚠️ Error during prediction: {e}")
