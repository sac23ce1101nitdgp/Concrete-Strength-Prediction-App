# ==================== Concrete Strength Prediction Web App (Auto-Calculated Inputs) ====================
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
        st.error(f"❌ Model file not found: {path}")
        st.stop()

# ---------------- Page Title ----------------
st.title("🧠 FRBC Strength Prediction Web App (Smart Auto-Inputs)")
st.markdown("""
Enter the main material inputs below — derived parameters such as **Total Binder**, **Water:Binder**, 
**Fine Aggregate:Binder**, and **Steel Fiber:Polypropylene Fiber** are **calculated automatically**.
""")

# ---------------- Input Features ----------------
base_features = [
    "Polypropylene Fiber (gm)", "Steel Fiber (gm)", "Length of PF (mm)", "Diameter of PF (mm)",
    "Length of SF (mm)", "Diameter of SF (mm)", "Cement Content (gm)", "FlyAsh (gm)", "GGBS (gm)",
    "Fine Aggregate (gm)", "NaOH pallets (gm)", "Water (gm)", "Na2SiO3 (gm)",
    "Density (kg/m3)", "AGE"
]

# ---------------- Derived Features ----------------
derived_features = [
    "Steel Fiber: Polypropylene Fiber", "Total Binder (gm)", 
    "Water:Binder", "Fine Aggregate : Binder"
]

all_features = base_features + derived_features

# ---------------- Allowed Zeros ----------------
zero_allowed = {
    "Polypropylene Fiber (gm)", "Steel Fiber (gm)", "Length of PF (mm)", "Diameter of PF (mm)",
    "Length of SF (mm)", "Diameter of SF (mm)", "Cement Content (gm)", "FlyAsh (gm)", "GGBS (gm)"
}
zero_not_allowed = set(all_features) - zero_allowed

# ---------------- Feature Ranges (example – replace with real ones) ----------------
feature_ranges = {
    "Polypropylene Fiber (gm)": (0, 15),
    "Steel Fiber (gm)": (0, 15),
    "Length of PF (mm)": (0, 30),
    "Diameter of PF (mm)": (0, 2),
    "Length of SF (mm)": (0, 60),
    "Diameter of SF (mm)": (0, 2),
    "Cement Content (gm)": (0, 600),
    "FlyAsh (gm)": (0, 300),
    "GGBS (gm)": (0, 300),
    "Fine Aggregate (gm)": (150, 900),
    "NaOH pallets (gm)": (0, 250),
    "Water (gm)": (10, 250),
    "Na2SiO3 (gm)": (0, 350),
    "Water:Binder": (0.2, 0.8),
    "Density (kg/m3)": (1900, 2500),
    "AGE": (1, 90),
    "Steel Fiber: Polypropylene Fiber": (0, 5),
    "Total Binder (gm)": (50, 700),
    "Fine Aggregate : Binder": (0.5, 10.0)
}

# ---------------- Input Section ----------------
st.header("🔧 Input Parameters")
user_input = {}
cols = st.columns(2)
for i, feature in enumerate(base_features):
    with cols[i % 2]:
        user_input[feature] = st.number_input(feature, value=0.0, step=0.1)

# ---------------- Auto-Calculate Derived Parameters ----------------
try:
    cement = user_input["Cement Content (gm)"]
    flyash = user_input["FlyAsh (gm)"]
    ggbs = user_input["GGBS (gm)"]
    fine_agg = user_input["Fine Aggregate (gm)"]
    water = user_input["Water (gm)"]
    steel = user_input["Steel Fiber (gm)"]
    pp = user_input["Polypropylene Fiber (gm)"]

    # Total Binder
    total_binder = cement + flyash + ggbs
    # Water:Binder (avoid divide-by-zero)
    water_binder = water / total_binder if total_binder > 0 else 0
    # Fine Aggregate : Binder
    fineagg_binder = fine_agg / total_binder if total_binder > 0 else 0
    # Steel Fiber : Polypropylene Fiber
    sf_pf_ratio = steel / pp if pp > 0 else 0

    # Add to user_input
    user_input["Total Binder (gm)"] = round(total_binder, 3)
    user_input["Water:Binder"] = round(water_binder, 3)
    user_input["Fine Aggregate : Binder"] = round(fineagg_binder, 3)
    user_input["Steel Fiber: Polypropylene Fiber"] = round(sf_pf_ratio, 3)

    st.info(f"🧮 **Auto-calculated fields:**\n"
            f"- Total Binder (gm): {total_binder:.3f}\n"
            f"- Water:Binder: {water_binder:.3f}\n"
            f"- Fine Aggregate:Binder: {fineagg_binder:.3f}\n"
            f"- Steel Fiber:Polypropylene Fiber: {sf_pf_ratio:.3f}")

except Exception as e:
    st.warning(f"⚠️ Error calculating derived parameters: {e}")

# ---------------- Validation Functions ----------------
def validate_zero_inputs(data):
    invalid = [f for f in zero_not_allowed if data.get(f, 0) == 0]
    if invalid:
        st.warning("⚠️ The following parameters **cannot be zero**:\n" + "\n".join([f"• {x}" for x in invalid]))
        return False
    return True

def validate_range_inputs(data):
    out_of_range = []
    for f, (fmin, fmax) in feature_ranges.items():
        val = data.get(f, 0)
        if val < fmin or val > fmax:
            out_of_range.append(f"{f} (Allowed: {fmin}–{fmax}, Entered: {val})")
    if out_of_range:
        st.warning("⚠️ The following inputs are **outside the trained data range**:\n" + "\n".join([f"• {x}" for x in out_of_range]))
        return False
    return True

# ---------------- Predict Button ----------------
if st.button("🔮 Predict"):
    input_df = pd.DataFrame([user_input])

    # ---- Validation ----
    if not validate_zero_inputs(user_input):
        st.stop()
    if not validate_range_inputs(user_input):
        st.stop()

    # ---- Run Predictions ----
    predictions = {name: model.predict(input_df)[0] for name, model in models.items()}

    # ---- Display Predictions ----
    st.subheader("✅ Predicted Outputs")
    for k, v in predictions.items():
        st.write(f"**{k}:** {v:.3f} MPa")

    # ---- Visualization ----
    st.subheader("📊 Predicted Strengths Visualization")
    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(predictions.keys(), predictions.values(),
                  color=['skyblue', 'lightgreen', 'salmon'])
    ax.set_ylabel("Strength (MPa)", fontsize=10)
    ax.set_ylim(0, max(predictions.values()) * 1.2)
    ax.tick_params(axis='x', labelsize=9)
    ax.tick_params(axis='y', labelsize=9)
    for i, v in enumerate(predictions.values()):
        ax.text(i, v + max(predictions.values()) * 0.02, f"{v:.2f}", ha='center', fontsize=9)
    st.pyplot(fig)

    # ---- Download as Excel ----
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

# ---------------- Footer ----------------
st.markdown("---")
st.caption("Developed by Sharwar Ahmed Chowdhury | FRBC Strength Prediction Tool v3.0")
