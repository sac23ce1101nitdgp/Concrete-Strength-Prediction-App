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
st.title("🧠 Fiber-Reinforced Binder Composite (FRBC) Strength Prediction App")
st.markdown("""
Enter the input parameters to predict:
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
    "Density (kg/m3)": (1900, 2500),
    "AGE": (1, 56)
}

# ---------------- Input UI (Two Columns) ----------------
st.header("Input Parameters")
cols = st.columns(2)
user_input = {}

for i, (feature, _) in enumerate(feature_limits.items()):
    with cols[i % 2]:
        val = st.number_input(feature, value=0.0, step=0.1, key=feature)
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
water_binder = (water / total_binder) if total_binder > 0 else 0
fineagg_binder = (fineagg / total_binder) if total_binder > 0 else 0
sf_pf_ratio = (sf / pf) if pf > 0 else 0

# Zero-out NaOH and Na2SiO3 if both FlyAsh and GGBS are zero
if flyash == 0 and ggbs == 0:
    user_input["NaOH pallets (gm)"] = 0
    user_input["Na2SiO3 (gm)"] = 0

# Add derived values
user_input.update({
    "Water:Binder": water_binder,
    "Total Binder (gm)": total_binder,
    "Fine Aggregate : Binder": fineagg_binder,
    "Steel Fiber: Polypropylene Fiber": sf_pf_ratio
})

# ---------------- Show Auto-Calculated Fields ----------------
st.subheader("🔧 Auto-Calculated Fields")
auto_cols = st.columns(2)
auto_cols[0].metric("Total Binder (gm)", f"{total_binder:.2f}")
auto_cols[0].metric("Water:Binder", f"{water_binder:.3f}")
auto_cols[1].metric("Fine Aggregate : Binder", f"{fineagg_binder:.3f}")
auto_cols[1].metric("Steel Fiber : Polypropylene Fiber", f"{sf_pf_ratio:.3f}")

# ---------------- Predict Button ----------------
if st.button("🔮 Predict"):
    # Validation 1: Critical fields non-zero (Cement can be zero)
    critical_fields = ["Fine Aggregate (gm)", "Water (gm)", "Density (kg/m3)"]
    invalid_zeros = [f for f in critical_fields if user_input[f] == 0]
    if invalid_zeros:
        st.error(f"❌ Invalid input: {', '.join(invalid_zeros)} cannot be zero.")
        st.stop()

    # Validation 2: Range checking (only display if invalid)
    invalid_ranges = []
    for feature, (low, high) in feature_limits.items():
        val = user_input[feature]
        if val < low or val > high:
            invalid_ranges.append(f"{feature} ({val} not in {low}-{high})")

    if invalid_ranges:
        st.error("⚠️ Out-of-range values detected:\n" + "\n".join(invalid_ranges))
        st.stop()

    # Validation 3: Binder check
    if total_binder == 0:
        st.error("❌ Total Binder cannot be zero. Please enter valid Cement, FlyAsh, or GGBS values.")
        st.stop()

    # ---------------- Prediction ----------------
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
