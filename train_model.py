import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

# =========================
# GENERATE SYNTHETIC HEALTH DATA
# =========================

np.random.seed(42)

rows = 1200

systolic_bp = np.random.randint(100, 180, rows)
diastolic_bp = np.random.randint(60, 110, rows)
glucose = np.random.randint(70, 300, rows)
cholesterol = np.random.randint(150, 320, rows)
triglycerides = np.random.randint(100, 350, rows)

labels = []

for i in range(rows):

    if glucose[i] > 150 and systolic_bp[i] > 150:
        labels.append("Kidney Disease")

    elif glucose[i] > 150:
        labels.append("Hyperglycemia")

    elif glucose[i] < 70:
        labels.append("Hypoglycemia")

    elif systolic_bp[i] > 150:
        labels.append("Hypertension")

    elif systolic_bp[i] < 90:
        labels.append("Hypotension")

    elif cholesterol[i] > 200:
        labels.append("Heart Disease")

    elif triglycerides[i]>250:
        labels.append("Heart Disease")

    else:
        labels.append("Healthy")

data = pd.DataFrame({
    "systolic_bp": systolic_bp,
    "diastolic_bp": diastolic_bp,
    "glucose": glucose,
    "cholesterol": cholesterol,
    "triglycerides": triglycerides,
    "label": labels
})

X = data.drop("label", axis=1)
y = data["label"]

# =========================
# TRAIN TEST SPLIT
# =========================

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# =========================
# RANDOM FOREST MODEL
# =========================

model = RandomForestClassifier(
    n_estimators=300,
    max_depth=8,
    random_state=42
)

model.fit(X_train, y_train)

# =========================
# EVALUATION
# =========================

predictions = model.predict(X_test)

print("Accuracy:", accuracy_score(y_test, predictions))
print("\nClassification Report:\n")
print(classification_report(y_test, predictions))

# =========================
# SAVE MODEL
# =========================

joblib.dump(model, "health_model.pkl")

print("\nModel saved successfully as health_model.pkl")