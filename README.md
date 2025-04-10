# PersonalWellnessRecommender

Detailed Summary of the Personal Wellness Prediction System
This Python script implements an end-to-end system for generating synthetic wellness data, training machine learning models, and providing personalized health recommendations through a user interface. Here's a detailed breakdown:

##1. Data Generation
Synthetic Dataset Creation:

Generates 10,000 synthetic samples with realistic health metrics (age, BMI, sleep, activity, etc.) and correlations (e.g., higher BMI linked to lower activity).

Input Features: 20+ attributes including demographics, lifestyle, and biometrics.

Output Targets:

Regression: Recommended calories, macros, sleep duration, workout duration, daily steps.

Classification: Suggested workouts, meal timing, supplements, wellness score.

Realistic relationships (e.g., stress affects mood, activity influences steps).

Saved to personal_wellness_dataset_large.csv.

##2. Machine Learning Pipeline
Data Preprocessing:

Handles categorical (OneHotEncoder) and numerical features (StandardScaler).

Converts time strings (e.g., 06:30) to minutes for modeling.

Model Training:

Multi-Output Regression (Random Forest): Predicts continuous targets (calories, steps, etc.).

Classification (Random Forest per target): Predicts categorical recommendations (workout type, wellness score).

Evaluation:

Regression: RMSE and MAE (e.g., RMSE of 287.9 for calories).

Classification: Accuracy and F1-scores (e.g., 85% accuracy for wellness score).

##3. User Interaction & Visualization
Input Methods:

Default: Predefined sample data.

Custom: Manual entry with validation (e.g., BMI as number, wake-up time in HH:MM).

Random: Randomly sampled from the dataset.

Visualization:

Plots user input against training data distributions (histograms for numerical features, bar charts for categorical).

Helps users contextualize their inputs (e.g., "How does my BMI compare to others?").

Predictions:

Displays personalized recommendations (e.g., "Recommended Calories: 2500", "Wellness Score: Good").

##4. Technical Highlights
Handling Real-World Scenarios:

Imputes missing wake-up times with the training median.

Robust input validation (e.g., checks for valid time formats).

Model Optimization:

Random Forests with increased n_estimators (150 trees) and adjusted hyperparameters (e.g., max_depth=20) for balance between performance and overfitting.

Code Structure:

Modular functions for data generation, preprocessing, training, and prediction.

Uses Pipeline and ColumnTransformer for clean preprocessing integration.

##5. Example Output

=== Wellness Recommendations ===
                             Recommendation
Recommended Calories                  2500
Protein (g)                            145
Carbs (g)                              220
Fats (g)                                65
New Sleep Duration (hrs)               7.5
Recommended Workout Duration (hrs)     1.2
Target Daily Steps                    10000
Suggested Workout              Cardio + Strength
Meal Timing Advice         Regular Intervals
Recommended Meal Frequency      3 Meals a Day
Overall Wellness Score               Good

6. Potential Improvements

Hyperparameter Tuning: Use grid search for optimal model settings.

Feature Engineering: Derive new features (e.g., BMI categories).

Deployment: Wrap in a web app (e.g., Flask/Django) for broader access.

Real Data Integration: Replace synthetic data with real health records.

This system serves as a foundation for personalized wellness tools, demonstrating key concepts in synthetic data generation, multi-target ML, and user-centric design.
