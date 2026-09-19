import joblib

MODEL_DIR = "models/spatial_baseline"

model_a = joblib.load(
    f"{MODEL_DIR}/model_a_with_gsi.joblib"
)

model_b = joblib.load(
    f"{MODEL_DIR}/model_b_without_gsi.joblib"
)

rf_a = model_a["model"]
rf_b = model_b["model"]

print("=" * 60)
print("MODEL A — WITH GSI")
print("=" * 60)

print("Algorithm:", model_a["algorithm"])
print("Features:", model_a["features"])
print("Number of features:", len(model_a["features"]))
print("Estimator:", type(rf_a))
print("Number of trees:", rf_a.n_estimators)

print("\nTraining parameters:")
for key, value in model_a["training_parameters"].items():
    print(f"  {key}: {value}")

print("\n" + "=" * 60)
print("MODEL B — WITHOUT GSI")
print("=" * 60)

print("Algorithm:", model_b["algorithm"])
print("Features:", model_b["features"])
print("Number of features:", len(model_b["features"]))
print("Estimator:", type(rf_b))
print("Number of trees:", rf_b.n_estimators)

print("\nTraining parameters:")
for key, value in model_b["training_parameters"].items():
    print(f"  {key}: {value}")

print("\n" + "=" * 60)
print("MODEL LOAD TEST PASSED")
print("=" * 60)