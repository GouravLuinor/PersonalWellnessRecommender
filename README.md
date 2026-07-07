# Personal Wellness Recommender

A machine learning–powered wellness recommendation system that generates personalized suggestions across nutrition, exercise, sleep, mindfulness, and daily habits.

The project combines an exploratory machine learning workflow with an interactive Streamlit application, consolidating the original model-development and application repositories into a single reproducible codebase.

> **Note:** This project uses synthetically generated wellness data with modeled relationships. It is intended for educational and experimental purposes and is not a medical diagnostic system.

---

## Overview

Personal Wellness Recommender explores how machine learning can be used to generate individualized wellness suggestions from lifestyle and behavioral inputs.

Users provide information such as:

* age and BMI
* wellness objective and timeline
* diet preference
* sleep duration and quality
* workout habits
* activity level
* stress and mood
* hydration
* mental focus
* daily steps
* resting heart rate
* blood pressure

The application processes these features through machine learning pipelines trained at runtime on generated synthetic data and presents personalized recommendations through an interactive web interface.

---

## Key Features

### Personalized Wellness Profile

Collects lifestyle and behavioral inputs through a structured Streamlit form and presents the submitted profile in an accessible interface.

### Synthetic Dataset Generation

Generates a dataset of 10,000 simulated wellness profiles with modeled relationships between lifestyle variables.

Generated data is stored locally under:

```text
data/generated/
```

Runtime-generated datasets are excluded from version control.

### Machine Learning Pipelines

Uses scikit-learn pipelines for preprocessing and prediction, including:

* categorical feature encoding
* numerical feature scaling
* train/test splitting
* Random Forest regression
* Random Forest classification
* multi-output regression

### Personalized Recommendations

Produces recommendations across areas such as:

* nutrition
* meal timing
* meal frequency
* exercise
* daily step targets
* sleep
* mindfulness
* general wellness habits

### Interactive Streamlit Application

Provides a browser-based interface for:

* entering wellness information
* viewing the submitted profile
* comparing user characteristics with generated data
* generating personalized recommendations
* visualizing results

---

## Project Structure

```text
PersonalWellnessRecommender/
├── app/
│   └── streamlit_app.py
│
├── notebooks/
│   └── PersonalWellnessRecommender.ipynb
│
├── data/
│   └── generated/                  # Created at runtime; ignored by Git
│
├── docs/
│   ├── project-report.pdf
│   ├── synthetic-data-methodology.pdf
│   └── legacy/
│       ├── app-readme.md
│       └── model-readme.md
│
├── .devcontainer/
│   └── devcontainer.json
│
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Tech Stack

| Area                    | Technologies                               |
| ----------------------- | ------------------------------------------ |
| Language                | Python                                     |
| Web Application         | Streamlit                                  |
| Data Processing         | pandas, NumPy                              |
| Machine Learning        | scikit-learn                               |
| Visualization           | Matplotlib, Seaborn                        |
| Development Environment | VS Code Dev Containers / GitHub Codespaces |
| Experimentation         | Jupyter Notebook                           |

---

## Machine Learning Approach

The project uses a synthetic dataset generation pipeline to create simulated wellness profiles with modeled relationships among lifestyle variables.

The application then builds machine learning workflows using components such as:

* `ColumnTransformer`
* `StandardScaler`
* `OneHotEncoder`
* `Pipeline`
* `RandomForestRegressor`
* `RandomForestClassifier`
* `MultiOutputRegressor`

This structure allows numerical and categorical features to be processed consistently before model training and inference.

---

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/GouravLuinor/PersonalWellnessRecommender.git
cd PersonalWellnessRecommender
```

### 2. Create a Virtual Environment

```bash
python3 -m venv .venv
```

Activate it on Linux or macOS:

```bash
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Run the Application

```bash
streamlit run app/streamlit_app.py
```

Then open the local URL displayed by Streamlit, typically:

```text
http://localhost:8501
```

---

## Generated Data

The application generates synthetic wellness data on first use and stores it at:

```text
data/generated/personal_wellness_dataset_large.csv
```

The generated dataset is intentionally excluded from Git through `.gitignore`.

This keeps runtime artifacts separate from source code and allows the dataset to be recreated locally.

---

## Documentation

Additional project material is available under `docs/`:

* `project-report.pdf` — project presentation/report material
* `synthetic-data-methodology.pdf` — documentation of the synthetic data approach
* `legacy/` — archived documentation from the original repositories before consolidation

The exploratory notebook is available at:

```text
notebooks/PersonalWellnessRecommender.ipynb
```

---

## Important Limitations

This project has several important limitations:

* The dataset is synthetic rather than collected from real-world participants.
* Relationships within the generated data are modeled by the project logic.
* Model performance on synthetic data should not be interpreted as evidence of real-world clinical validity.
* Recommendations are generated for educational and experimental purposes.
* The application is not intended to diagnose, treat, prevent, or manage medical conditions.
* Outputs should not replace guidance from qualified healthcare professionals.

---

## Project Evolution

This repository consolidates two earlier development tracks:

* machine learning experimentation and synthetic-data research
* interactive Streamlit application development

Their Git histories have been preserved in the unified repository to retain the project's development record.

---

## Future Improvements

Potential next steps include:

* evaluation on appropriate real-world public datasets
* improved model validation and benchmarking
* model explainability using feature importance or SHAP
* automated testing
* persistent user profiles
* improved accessibility
* containerized deployment
* API-based inference architecture
* stronger separation between model training and application inference

---

## Disclaimer

This software is an educational machine learning project. It does not provide medical advice, diagnosis, or treatment. Always consult qualified healthcare professionals for decisions concerning health or medical conditions.
