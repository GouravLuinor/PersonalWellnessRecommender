"""Shared definitions: input options, feature lists and target lists."""

SEXES = ["Female", "Male"]
OBJECTIVES = ["Weight Loss", "Maintenance", "Weight Gain"]
TIMELINES = ["1 Month", "3 Months", "6 Months"]
DIETS = ["Balanced", "Vegetarian", "Vegan", "High Protein", "Keto"]
WORKOUT_TYPES = ["None", "Cardio", "Strength", "Yoga", "HIIT", "Mixed"]
ACTIVITY_LEVELS = ["Sedentary", "Lightly Active", "Active", "Very Active"]
SLEEP_QUALITIES = ["Poor", "Average", "Good", "Excellent"]
STRESS_LEVELS = ["Low", "Moderate", "High"]
MOODS = ["Happy", "Energetic", "Neutral", "Tired", "Sad"]
FOCUS_LEVELS = ["Low", "Medium", "High"]

CATEGORICAL_FEATURES = [
    "Sex",
    "Objective",
    "Timeline",
    "Diet Type",
    "Workout Type",
    "Activity Level",
    "Sleep Quality",
    "Stress Level",
    "Mood",
    "Mental Focus",
]

NUMERICAL_FEATURES = [
    "Age",
    "Height (cm)",
    "Weight (kg)",
    "BMI",
    "Sleep Duration (hrs)",
    "Wake Up Time (min)",
    "Exercise (min/day)",
    "Water Intake (L)",
    "Daily Steps",
    "Resting Heart Rate",
    "Systolic BP",
    "Diastolic BP",
]

FEATURES = NUMERICAL_FEATURES + CATEGORICAL_FEATURES

REGRESSION_TARGETS = [
    "Calories",
    "Protein (g)",
    "Carbs (g)",
    "Fats (g)",
    "Water Target (L)",
    "Sleep Target (hrs)",
    "Exercise Target (min/day)",
    "Steps Target",
    "Wellness Score",
]

CLASSIFICATION_TARGETS = ["Workout Plan", "Meal Pattern", "Mindfulness Practice"]

TARGETS = REGRESSION_TARGETS + CLASSIFICATION_TARGETS

WORKOUT_PLANS = [
    "Strength Training",
    "Cardio + Strength",
    "Low-Impact Cardio",
    "Yoga & Mobility",
    "HIIT + Recovery",
]
MEAL_PATTERNS = [
    "3 Balanced Meals",
    "5-6 Smaller Meals",
    "Time-Restricted Eating",
    "Regular Meals, Early Dinner",
]
MINDFULNESS_PRACTICES = [
    "Box Breathing",
    "Body-Scan Meditation",
    "Nature Walk",
    "Focused-Attention Meditation",
    "Gratitude Journaling",
]

# Bump when the generator or rules change so cached data/models are rebuilt.
DATA_VERSION = 2
