"""
Improved food unit conversion with support for descriptive sizes
"""

# Update the unit conversion section in get_food_nutrition function

# REPLACE THIS CODE (around line 171-180):
"""
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
"""

# WITH THIS IMPROVED CODE:

def convert_quantity_to_grams(quantity, unit, food_description):
    """
    Convert various quantity units to grams with support for descriptive sizes.
    
    Supports:
    - Descriptive: small, medium, large
    - Volume: cup, ml, tbsp, tsp
    - Weight: oz, lb, g
    - Countable: piece, item, unit
    """
    unit_lower = unit.lower()
    
    # Handle descriptive size units (small, medium, large)
    # Typical weights for common foods
    if unit_lower in ['small', 'sm']:
        # Small fruit/vegetable ~100g, small egg ~50g
        if 'egg' in food_description.lower():
            return quantity * 50
        else:
            return quantity * 100
    
    elif unit_lower in ['medium', 'med', 'md']:
        # Medium fruit/vegetable ~150g, medium egg ~60g
        if 'egg' in food_description.lower():
            return quantity * 60
        elif 'apple' in food_description.lower():
            return quantity * 182  # USDA standard medium apple
        elif 'banana' in food_description.lower():
            return quantity * 118  # USDA standard medium banana
        elif 'orange' in food_description.lower():
            return quantity * 131  # USDA standard medium orange
        else:
            return quantity * 150  # Default medium size
    
    elif unit_lower in ['large', 'lg', 'big']:
        # Large fruit/vegetable ~200g, large egg ~70g
        if 'egg' in food_description.lower():
            return quantity * 70
        elif 'apple' in food_description.lower():
            return quantity * 223
        elif 'banana' in food_description.lower():
            return quantity * 136
        else:
            return quantity * 200
    
    # Volume units
    elif unit_lower in ['cup', 'cups']:
        return quantity * 240
    
    # Weight units
    elif unit_lower in ['oz', 'ounce', 'ounces']:
        return quantity * 28.35
    elif unit_lower in ['lb', 'lbs', 'pound', 'pounds']:
        return quantity * 453.59
    elif unit_lower in ['g', 'gram', 'grams']:
        return quantity
    
    # Liquid volume
    elif unit_lower in ['ml', 'milliliter', 'milliliters']:
        return quantity
    elif unit_lower in ['tbsp', 'tablespoon', 'tablespoons']:
        return quantity * 15
    elif unit_lower in ['tsp', 'teaspoon', 'teaspoons']:
        return quantity * 5
    
    # Countable items
    elif unit_lower in ['piece', 'pieces', 'item', 'items', 'unit', 'units']:
        # Default piece/item weight ~150g
        return quantity * 150
    
    else:
        # Unknown unit - assume it's already in grams or use quantity as multiplier
        print(f"[WARNING] Unknown unit '{unit}' - treating as grams")
        return quantity


# USAGE IN get_food_nutrition function:
# Replace the old conversion code with:
# quantity_in_grams = convert_quantity_to_grams(quantity, unit, food_data.get('description', ''))
