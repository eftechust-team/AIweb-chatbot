# ELEVATEFOODS AI Recipe Chatbot - Chatbot Implementation Guide

## 🎯 New Features

The website has been transformed from a form-based data intake system to an **intelligent chatbot interface** for tracking food and nutrition!

### What's New:

1. **Conversational Chatbot UI** - A modern chat interface instead of traditional form blanks
2. **USDA FoodData Central Integration** - Real-time nutritional data for thousands of foods
3. **Real-time Nutrition Tracking** - See your daily carbs, protein, and fat totals update instantly
4. **Personalized Recommendations** - Get customized nutrition plans based on your profile
5. **Session Persistence** - Your data is saved locally in the browser

---

## 🚀 Getting Started

### 1. Access the Chatbot

Once the Flask server is running, navigate to:
```
http://localhost:8080/chatbot
```

### 2. Set Up Your Profile

In the right sidebar, fill in your personal information:
- **Gender**: Male or Female
- **Age**: Your age in years
- **Height**: In centimeters (cm)
- **Weight**: In kilograms (kg)
- **Activity Level**: How active you are (Sedentary, Low Active, Active, Very Active)
- **Diet Plan**: Your dietary preference (Balanced, Low Fat, Low Carb, High Protein)
- **Food Preference**: Your preferred supplement (Chicken or Lentils)

### 3. Track Your Food Intake

In the main chat area, type what you've eaten in natural language:

**Examples:**
- "100g chicken breast"
- "1 medium apple"
- "2 cups rice"
- "200g salmon fillet"
- "1 banana"

The chatbot will:
1. Parse your input
2. Search the USDA FoodData Central database
3. Return nutritional information
4. Update your daily totals

### 4. Get Recommendations

Once you've filled in your profile and logged some food intake, click the **"Get Recommendations"** button. The system will:
1. Calculate your daily calorie needs based on your profile
2. Determine how much carbs, protein, and fat you should consume
3. Compare with what you've eaten so far
4. Suggest foods to help you reach your goals

---

## 🔑 USDA API Key Setup (Important!)

The chatbot uses the **USDA FoodData Central API** to fetch real nutritional data. Currently, it's set to use the `DEMO_KEY`, which has limited requests.

### To Get Your Own API Key:

1. Visit: https://fdc.nal.usda.gov/api-key
2. Sign up for a free account
3. Copy your API key
4. In `main.py`, find this line (around line 43):
   ```python
   USDA_API_KEY = "DEMO_KEY"  # Replace with actual API key
   ```
5. Replace `"DEMO_KEY"` with your actual key:
   ```python
   USDA_API_KEY = "your_actual_api_key_here"
   ```

### API Key Benefits:
- **DEMO_KEY**: Very limited requests (for testing only)
- **Your Personal Key**: Unlimited requests, perfect for production use

---

## 📝 How It Works

### Food Input Parsing

The chatbot parses your food input to extract:
- **Quantity** (number)
- **Unit** (g, cup, oz, lb, ml, etc.)
- **Food Name**

Supported units:
- `g` or `grams`
- `cup`, `cups`
- `oz`, `ounce`, `ounces`
- `lb`, `lbs`, `pound`, `pounds`
- `ml`, `milliliter`

### Nutritional Data Retrieval

1. Your input is sent to the USDA API
2. The API searches for matching foods
3. Detailed nutrition facts are retrieved
4. Values are scaled to your portion size
5. Your daily totals are updated automatically

### Data Storage

- **Daily Intake**: Saved in your browser's local storage
- **User Profile**: Saved in your browser's local storage
- **Recommendations**: Stored in session storage

This means:
- ✅ Your data persists across browser sessions (same computer)
- ✅ No server-side storage of personal health data
- ⚠️ Data is local to your browser; clearing browser data will reset it

---

## 🗂️ Project Structure

### New Files Created:
- `templates/chatbot.html` - Main chatbot interface
- `static/chatbot.css` - Styling for the chatbot
- `static/chatbot.js` - Frontend logic and UI interactions

### Modified Files:
- `main.py` - Added USDA API functions and new routes

### New API Endpoints:
- `POST /api/search-food` - Search food and get nutrition
- `POST /api/calculate-recommendation` - Get personalized nutrition recommendations
- `GET/POST /chatbot` - Serve the chatbot interface

---

## 💡 Usage Examples

### Example Conversation:

```
You: 100g chicken breast
Bot: ✅ Chicken breast, raw
     Carbs: 0g
     Protein: 31.3g
     Fat: 3.6g

You: 1 medium apple
Bot: ✅ Apple, raw, with skin
     Carbs: 21.8g
     Protein: 0.26g
     Fat: 0.17g

You: [Click "Get Recommendations"]
Bot: 📊 Your Nutrition Recommendation
     Daily Calorie Target: 2500 kcal
     Carbs Target: 312.5g (Have: 21.8g, Need: 290.7g)
     Protein Target: 156.25g (Have: 31.56g, Need: 124.69g)
     Fat Target: 83.3g (Have: 3.77g, Need: 79.53g)
     
     Suggested Foods:
     - Purple Sweet Potato: 450g
     - Red Lentils: 280g
```

---

## 🎨 UI Features

### Sidebar
- **Today's Intake Section**: Shows real-time totals for carbs, protein, and fat
- **User Info Form**: Compact form to enter and save your personal data

### Main Chat Area
- **Chat Header**: Instructions and context
- **Messages Container**: Scrollable conversation history
- **Input Area**: Enter food items with hints

### Responsive Design
- ✅ Works on desktop, tablet, and mobile
- ✅ Sidebar collapses on smaller screens
- ✅ Touch-friendly input on mobile

---

## 🔧 Customization

### Colors and Styling

The chatbot uses CSS variables from `base.css`:
```css
--accent: #ff7a3d        /* Main orange color */
--accent-2: #ffc861      /* Secondary yellow color */
--text: #1f2937          /* Text color */
--muted: #4b5563         /* Muted text */
--border: rgba(...)      /* Border color */
```

Edit `static/chatbot.css` to customize colors and appearance.

### Nutrient Parsing

The USDA API returns over 100 different nutrients. Currently, we extract:
- Carbohydrates
- Protein
- Total Fat

To add more nutrients, edit the `get_food_nutrition()` function in `main.py`.

---

## ⚠️ Known Limitations

1. **DEMO_KEY Limits**: The default DEMO_KEY has very limited API requests
   - Solution: Get your own API key from the USDA website

2. **Unit Conversions**: Some foods use different units (volume vs. weight)
   - We use approximate conversions (1 cup ≈ 240ml)
   - For precision, use weight in grams

3. **Portion Size**: USDA data defaults to 100g
   - The system scales values based on your input
   - May not be 100% accurate for all foods

4. **Food Names**: Search works best with common food names
   - "Chicken breast" ✅ works
   - "Poultry muscle" ❌ may not work

---

## 🐛 Troubleshooting

### "No foods found" error
- Check your USDA API key is correct
- Try a different, more specific food name
- Make sure you're using the DEMO_KEY or a valid API key

### Daily totals not updating
- Check browser console for errors (F12 → Console)
- Make sure JavaScript is enabled
- Try refreshing the page

### Can't get recommendations
- Fill in all required fields in the User Info form
- Make sure gender, activity level, and diet plan are selected
- Log at least one food item

### Slow API responses
- The USDA API may be busy
- Try again in a moment
- Consider upgrading to a paid API plan if using high volume

---

## 🚀 Future Enhancements

Potential improvements for future versions:
1. Database storage for multi-device sync
2. User accounts and cloud backup
3. Barcode scanning for quick food entry
4. Food photos with AI recognition
5. Weekly/monthly nutrition reports
6. Integration with fitness apps
7. Recipes and meal planning
8. Export nutrition data as PDF

---

## 📱 Running the Server

```bash
# From the project root directory
python main.py
```

Then visit: `http://localhost:8080/`

---

## 📚 References

- **USDA FoodData Central**: https://fdc.nal.usda.gov/
- **USDA API Documentation**: https://fdc.nal.usda.gov/api-docs
- **Food Database**: Over 1 million foods available

---

## 💬 Questions?

For more information about the USDA FoodData Central API, visit their documentation at https://fdc.nal.usda.gov/api-docs

Enjoy tracking your nutrition with ELEVATEFOODS! 🥗
