# Manual Update Instructions for main.py

## Problem
When user says "1 medium apple", the system doesn't know how to convert "medium" to grams,
so it treats it as 1 gram, giving incorrect nutrition values.

## Solution
Replace the unit conversion section in the `get_food_nutrition` function with improved logic
that handles descriptive sizes (small, medium, large).

## Location
File: main.py
Lines: approximately 171-180

## FIND THIS CODE:
```python
        # Convert quantity to grams if needed
        quantity_in_grams = quantity
        if unit.lower() in ['cup', 'cups']:
            quantity_in_grams = quantity * 240
        elif unit.lower() in ['oz', 'ounce', 'ounces']:
            quantity_in_grams = quantity * 28.35
        elif unit.lower() in ['lb', 'lbs', 'pound', 'pounds']:
            quantity_in_grams = quantity * 453.59
        elif unit.lower() in ['ml', 'milliliter']:
            quantity_in_grams = quantity
```

## REPLACE WITH THIS CODE:
```python
        # Convert quantity to grams if needed
        quantity_in_grams = quantity
        unit_lower = unit.lower()
        food_desc = food_data.get('description', '').lower()
        
        # Handle descriptive size units with USDA standard weights
        if unit_lower in ['small', 'sm']:
            if 'egg' in food_desc:
                quantity_in_grams = quantity * 50
            elif 'apple' in food_desc:
                quantity_in_grams = quantity * 149  # Small apple per USDA
            elif 'banana' in food_desc:
                quantity_in_grams = quantity * 101
            else:
                quantity_in_grams = quantity * 100
        
        elif unit_lower in ['medium', 'med', 'md']:
            if 'egg' in food_desc:
                quantity_in_grams = quantity * 60
            elif 'apple' in food_desc:
                quantity_in_grams = quantity * 182  # Medium apple per USDA
            elif 'banana' in food_desc:
                quantity_in_grams = quantity * 118  # Medium banana per USDA
            elif 'orange' in food_desc:
                quantity_in_grams = quantity * 131
            else:
                quantity_in_grams = quantity * 150
        
        elif unit_lower in ['large', 'lg', 'big']:
            if 'egg' in food_desc:
                quantity_in_grams = quantity * 70
            elif 'apple' in food_desc:
                quantity_in_grams = quantity * 223  # Large apple per USDA
            elif 'banana' in food_desc:
                quantity_in_grams = quantity * 136
            else:
                quantity_in_grams = quantity * 200
        
        # Volume units
        elif unit_lower in ['cup', 'cups']:
            quantity_in_grams = quantity * 240
        elif unit_lower in ['tbsp', 'tablespoon', 'tablespoons']:
            quantity_in_grams = quantity * 15
        elif unit_lower in ['tsp', 'teaspoon', 'teaspoons']:
            quantity_in_grams = quantity * 5
        
        # Weight units
        elif unit_lower in ['oz', 'ounce', 'ounces']:
            quantity_in_grams = quantity * 28.35
        elif unit_lower in ['lb', 'lbs', 'pound', 'pounds']:
            quantity_in_grams = quantity * 453.59
        elif unit_lower in ['g', 'gram', 'grams']:
            quantity_in_grams = quantity
        
        # Volume (liquid)
        elif unit_lower in ['ml', 'milliliter', 'milliliters']:
            quantity_in_grams = quantity
        
        # Countable items
        elif unit_lower in ['piece', 'pieces', 'item', 'items', 'unit', 'units']:
            quantity_in_grams = quantity * 150
        
        else:
            # Unknown unit - assume grams
            print(f"[WARNING] Unknown unit '{unit}' - treating quantity as grams")
            quantity_in_grams = quantity
```

## Standard Food Weights (USDA):
- Small apple: 149g
- Medium apple: 182g  ← This fixes "1 medium apple"
- Large apple: 223g
- Medium banana: 118g
- Medium orange: 131g
- Medium egg: 60g

## After Making Changes:
1. Save the file
2. The Flask app should auto-reload (debug mode is on)
3. Test with "1 medium apple" - should now give ~182g worth of nutrition

## Verification:
Input: "1 medium apple"
Should see in logs:
```
Input: 1medium = 182.0g  ← Correctly converted!
```
