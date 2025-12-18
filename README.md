# Food AI - ELEVATEFOODS

A Flask-based web application that leverages AI and computer vision to analyze food images, calculate nutritional information, and provide personalized dietary recommendations.

## Overview

Food AI is an intelligent nutrition analysis platform that helps users make informed dietary decisions. Upload a photo of your food, and the system will:

1. **Analyze** the food items using segmentation
2. **Calculate** detailed nutritional information (carbs, proteins, fats, calories)
3. **Generate** personalized dietary recommendations based on your health profile and dietary goals

## Features

### 🔍 Image Analysis
- Food image recognition and segmentation using FoodSAM
- Support for JPG and PNG formats
- Optimized for top-down, high-contrast, well-lit food photos

### 📊 Nutrition Calculation
- Automatic nutritional analysis from uploaded food images
- Detailed macro nutrient breakdown (carbohydrates, proteins, fats)
- Calorie estimation
- Food volume and weight estimation via 3D mesh generation

### 🎯 Personalized Recommendations
- Data collection for user profiles (age, height, weight, gender, activity level)
- Activity level-based calorie calculation (RMR & TDEE)
- Multiple diet preference options:
  - Balanced (50% carbs, 20% protein, 30% fat)
  - Low Fat (60% carbs, 20% protein, 20% fat)
  - Low Carb (20% carbs, 30% protein, 50% fat)
  - High Protein (28% carbs, 39% protein, 33% fat)
- Personalized dietary supplement recommendations

### 📐 Advanced Features
- 3D mesh generation for food volume estimation
- Dimension constraints for accurate volume-to-weight conversion
- Google Cloud Storage integration for mesh file storage
- Responsive web interface with intuitive user flow

## Project Structure

```
.
├── main.py                          # Flask application entry point
├── food-ai-455507-e2a9c115814e.json # Google Cloud credentials
├── FoodSAM/                         # Food segmentation model
├── static/
│   ├── base.css                     # Base styling
│   ├── upload-image.css            # Upload page styling
│   ├── nutrition-calculation.css    # Calculation page styling
│   ├── nutrition-recommendation.css # Recommendation page styling
│   ├── data-collection.css          # Data collection styling
│   ├── uploads/                     # User-uploaded food images
│   └── foodseg/                     # Segmentation results
│       ├── C-4/                     # Sample segmentation data
│       └── C-6/                     # Sample segmentation data
└── templates/
    ├── data-collection.html         # User profile form
    ├── upload-image.html            # Image upload page
    ├── nutrition-calculation.html   # Nutrition results display
    └── nutrition-recommendation.html # Recommendation results
```

## User Flow

1. **Data Collection** → User enters personal health information
2. **Image Upload** → User uploads a food photo
3. **Nutrition Calculation** → System analyzes image and shows nutritional breakdown
4. **Recommendations** → Personalized dietary plan generated based on user profile and food consumption

## Technology Stack

- **Backend**: Flask (Python web framework)
- **Computer Vision**: FoodSAM (Food Segmentation model)
- **Cloud Storage**: Google Cloud Storage
- **Numerical Computation**: NumPy, SciPy
- **3D Modeling**: numpy-stl (STL mesh generation)
- **Frontend**: HTML, CSS

## Installation

### Prerequisites
- Python 3.7+
- Google Cloud Account with credentials
- pip (Python package manager)

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Food_AI-master
   ```

2. **Install dependencies**
   ```bash
   pip install flask google-cloud-storage numpy scipy numpy-stl
   ```

3. **Configure Google Cloud credentials**
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="food-ai-455507-e2a9c115814e.json"
   ```

4. **Run the application**
   ```bash
   python main.py
   ```

5. **Access the application**
   Open your browser and navigate to `http://localhost:5000`

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Redirects to data collection |
| GET/POST | `/data_collection` | User profile data entry |
| GET/POST | `/upload_image` | Food image upload |
| GET/POST | `/nutrition_calculation` | Nutrition analysis results |
| GET/POST | `/nutrition_recommendation` | Dietary recommendations |

## Key Functions

### Nutrition Calculation
- `calculate_rmr(weight, height, age, sex)` - Calculates Resting Metabolic Rate using Mifflin-St Jeor equation
- `calculate_daily_calories(rmr, activity_level)` - Calculates total daily energy expenditure (TDEE)
- `calculate_cube_dimension(volume)` - Estimates food dimensions from volume

### Food Recommendations
- `recommend(gender, age, height, weight, carbohydrate, protein, fat, activity, diet, preference)` - Generates personalized dietary recommendations using optimization algorithms

### 3D Mesh Generation
- `mesh_generation(name, weight, density)` - Creates 3D STL models for food visualization and uploads to Google Cloud Storage

## Data Format

Segmentation results are stored in JSON format:
```
static/foodseg/{name}/{name}_nutrition.json
```

Contains:
- Calorie count
- Carbohydrate content
- Protein content
- Fat content
- Volume estimation

## Configuration

### Dimension Constraints
- **Min dimensions**: 8.0cm × 8.0cm × 0.15cm
- **Max dimensions**: 15.0cm × 13.0cm × 2.2cm
- **Max volume**: 429 cm³

### Activity Level Multipliers
- Sedentary: 1.2 × RMR
- Lightly active: 1.375 × RMR
- Moderately active: 1.55 × RMR
- Very active: 1.725 × RMR

## Future Enhancements

- Real-time food recognition from camera feed
- Multi-language support
- Recipe suggestions based on nutritional needs
- Meal planning and grocery list generation
- Integration with fitness tracking apps
- Machine learning model improvements for accuracy

## License

[Add your license information here]

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues or questions, please open an issue on the repository.

---

**Note**: This is a beta version of ELEVATEFOODS. For best results, use high-contrast, well-lit, top-down photographs of food items.
