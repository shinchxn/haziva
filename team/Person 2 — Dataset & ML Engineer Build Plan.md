# PERSON 2 — DATASET & ML ENGINEER

## Main Goal

Build the **training dataset, ML training pipeline, prediction pipeline, model evaluation, and explainability output** for the SIH 26191 prototype.

The output of your work must be a working model that can take habitation-level hazard, exposure, vulnerability, and forecast-related features and produce:

**Current Risk → 24h Risk → 72h Risk → Confidence → Risk Drivers**

Person 3 will connect these outputs to the backend.

---

# 1. Tech Stack

Use:

- **Python**
- **Pandas**
- **NumPy**
- **Scikit-learn**
- **XGBoost or LightGBM** if justified by the available dataset
- **GeoPandas** for geographic dataset processing where required
- **Joblib** or equivalent for saving the trained model

Keep the model interpretable and suitable for the available data.

---

# 2. Build the Training Dataset

Create the model-ready dataset by combining the available project data.

The dataset should connect information at the **habitation/location level**.

Include the available:

### Hazard Features

- Landslide susceptibility
- Slope
- Elevation/terrain
- Historical hazard evidence
- Recent rainfall
- Accumulated rainfall
- Forecast rainfall

### Exposure Features

- Population
- Households
- Population density
- Critical infrastructure exposure

### Vulnerability Features

- Housing/service vulnerability indicators
- Accessibility
- Essential-service distance
- Other supported vulnerability indicators

Only use features that are actually available and documented.

---

# 3. Feature Engineering

Build the feature-engineering pipeline required by the model.

Create useful derived features from the available data, such as:

- Recent rainfall accumulation
- Multi-period rainfall accumulation
- Forecast rainfall accumulation
- Rainfall change/trend
- Hazard × rainfall interaction
- Population exposure indicators
- Accessibility indicators

The feature-engineering process must be reproducible.

The same feature pipeline must be usable for both training and future prediction.

---

# 4. Prepare Model Input

Create one consistent model input structure.

Example:

```text
Habitation
      ↓
Terrain Features
      ↓
Hazard Features
      ↓
Rainfall Features
      ↓
Exposure Features
      ↓
Vulnerability Features
      ↓
Model Features
```

The training dataset and prediction dataset must use the same feature definitions.

---

# 5. Build the Risk Model

Build an interpretable baseline risk model first.

Evaluate suitable models such as:

- Logistic Regression
- Random Forest
- Gradient Boosting
- XGBoost/LightGBM where justified

Select the model based on actual validation performance and suitability for the available data.

Do not use deep learning unless the dataset genuinely supports it.

---

# 6. Risk Prediction

The model must produce habitation-level risk.

The prediction pipeline should support:

```text
Current Conditions
        ↓
Current Risk

Forecast Conditions
        ↓
24h Risk

Forecast Conditions
        ↓
72h Risk
```

The output should be a risk value/probability that can be consumed by the backend.

---

# 7. Prediction Output

Create a standard prediction output.

Example:

```json
{
  "habitation_id": "hab_001",
  "current_risk": 0.68,
  "risk_24h": 0.81,
  "risk_72h": 0.76,
  "confidence": 0.74
}
```

These are only output-format examples.

The actual values must come from the trained model.

---

# 8. Risk Trajectory

Generate the risk trajectory from the actual prediction results.

Compare:

```text
Current Risk
     ↓
24h Risk
     ↓
72h Risk
```

Classify the trajectory as:

- Stable
- Increasing
- Rapidly Increasing
- Decreasing
- Critical

The classification logic must be consistent and documented.

---

# 9. Explainability

Build model explainability so the system can answer:

> **Why is this habitation receiving this risk level?**

Return actual contributing features.

Possible examples:

```text
High landslide susceptibility
High recent rainfall
High forecast rainfall
High slope
High population exposure
Limited accessibility
```

These explanations must come from the actual model/features.

Do not generate generic explanations unrelated to the prediction.

---

# 10. Prediction Confidence

Produce a confidence/uncertainty measure appropriate to the selected model and validation approach.

Keep it separate from risk.

Example:

```text
Risk: 0.81
Confidence: 0.74
```

Do not present confidence as a guarantee that the disaster will or will not happen.

---

# 11. Model Evaluation

Evaluate the trained model using appropriate metrics for the available target/data.

Depending on the model/task, evaluate relevant measures such as:

- Accuracy
- Precision
- Recall
- F1
- ROC-AUC
- Calibration
- Confusion matrix

Choose metrics that actually match the prediction problem.

The evaluation results should be saved/documented so Person 3 and the final dashboard can report model status appropriately.

---

# 12. Model Sanity Checks

Check that the model behaves logically with changing inputs.

For example:

```text
Higher relevant rainfall
        ↓
Risk should respond appropriately
```

Also check:

- Missing values
- Invalid values
- Extreme values
- Feature consistency
- Prediction range
- Unexpected model behavior

The purpose is to ensure the model output is technically usable before integration.

---

# 13. Saved Model

Save the trained model so the backend can load/use it.

Also save the required:

- Feature definitions
- Preprocessing
- Encoders/scalers if used
- Model configuration
- Model version
- Training metadata

Person 3 must be able to integrate the model without rebuilding the training process.

---

# 14. Prediction Interface

Create a clean prediction interface for backend integration.

Conceptually:

```text
Input Features
      ↓
Feature Preprocessing
      ↓
Trained Model
      ↓
Risk Prediction
      ↓
Confidence
      ↓
Risk Drivers
```

The interface should accept habitation-level feature data and return the standardized prediction output.

---

# 15. Multiple Prediction Horizons

Make the prediction pipeline support:

```text
NOW
24 HOURS
72 HOURS
```

The horizon-specific inputs must use the corresponding current/forecast conditions.

Do not simply copy the current risk into the future fields.

---

# 16. Output for Person 3

Person 3 needs a clean model output containing:

```text
Habitation ID
Current Risk
24h Risk
72h Risk
Confidence
Risk Drivers
Model Version
Prediction Timestamp
```

This becomes the intelligence input for the backend.

---

# 17. Output for Person 4

Person 4 needs the model information through Person 3's API.

The model must therefore provide enough information for the frontend to display:

```text
Current Risk
24h Risk
72h Risk
Trajectory
Confidence
Why Risk Is High
```

---

# 18. Output for Person 5

The model must provide habitation-level risk information that can be associated with geographic coordinates.

The map will then visualize:

```text
Habitation Location
        +
Risk
        +
Priority
```

---

# 19. Output for Person 6

The model must provide the risk/priority information required to trigger relocation analysis.

The flow becomes:

```text
ML Prediction
      ↓
Risk
      ↓
Trajectory
      ↓
Priority
      ↓
Relocation Logic
```

Person 6 handles the relocation logic.

---

# 20. Final Working Flow

Person 2's complete module must work like this:

```text
RAW PROJECT DATA
       ↓
DATA CLEANING
       ↓
FEATURE ENGINEERING
       ↓
TRAINING DATASET
       ↓
MODEL TRAINING
       ↓
MODEL EVALUATION
       ↓
SAVED MODEL
       ↓
CURRENT + FORECAST FEATURES
       ↓
PREDICTION
       ↓
CURRENT / 24H / 72H RISK
       ↓
CONFIDENCE
       ↓
RISK DRIVERS
       ↓
PERSON 3 BACKEND
```

---

# Final Build Result

Person 2 must deliver a **working, reusable ML pipeline** that takes the project's available hazard, rainfall, terrain, exposure, and vulnerability features and produces reliable, explainable habitation-level future-risk outputs for:

**Current → 24h → 72h**

These outputs become the core intelligence consumed by the backend, dashboard, map, and relocation system.