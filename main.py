from flask import Flask, render_template, redirect, request, abort, send_file, url_for, jsonify
from google.cloud import storage
from google.auth.exceptions import DefaultCredentialsError
import numpy as np
from scipy.optimize import minimize, NonlinearConstraint, nnls, linprog
from itertools import combinations
import os
import json
import io
import requests
import re
from datagov_api import get_datagov_client

# export GOOGLE_APPLICATION_CREDENTIALS="food-ai-455507-e2a9c115814e.json"     
json_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "food-ai-455507-e2a9c115814e.json"))
if os.path.exists(json_path):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = json_path

# Diagnostics toggle (optional): set env DIAG_MODE=1 to include server-side errors in API responses
DIAG_MODE = os.getenv("DIAG_MODE", "0") not in ["0", "false", "False", ""]

# Mesh generation mode and solution limits for memory/time-constrained environments (e.g., Render)
# MESH_MODE: 'all' (default) | 'first' (only first solution) | 'none' (disable STL generation)
MESH_MODE = os.getenv("MESH_MODE", "all").strip().lower()
# MAX_SOLUTIONS: cap how many solution options we compute/return
try:
    MAX_SOLUTIONS = max(1, int(os.getenv("MAX_SOLUTIONS", "2")))
except Exception:
    MAX_SOLUTIONS = 2

# Mesh storage backend: 'gcs' (default) to upload to Google Cloud Storage, or 'local' to keep files in /tmp and serve directly
MESH_STORAGE = os.getenv("MESH_STORAGE", "gcs").strip().lower()

def _manifest_path():
    import tempfile
    return os.path.join(tempfile.gettempdir(), "meshes_manifest.json")

def _load_manifest():
    try:
        path = _manifest_path()
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"[WARN] Failed to load mesh manifest: {e}")
    return {}

def _save_manifest(manifest):
    try:
        path = _manifest_path()
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f)
    except Exception as e:
        print(f"[WARN] Failed to save mesh manifest: {e}")
 
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = "./static/uploads"
bucket_name = "food-ai"

def upload_to_gcs(bucket_name, source_file_name, destination_blob_name):
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(source_file_name)
        # Make the blob publicly readable
        blob.make_public()
        return True
    except DefaultCredentialsError:
        return False
    except Exception as e:
        print(f"Error uploading to GCS: {e}")
        return False

    # print(f"File {source_file_name} uploaded to {destination_blob_name}.")

# USDA FoodData Central API functions using data.gov API client
# API key is now securely stored in environment variable: DATA_GOV_API_KEY
# Get your API key from: https://api.data.gov/
data_gov_client = get_datagov_client()  # Uses X-Api-Key header authentication
USDA_API_URL = "https://api.nal.usda.gov/fdc/v1"

# Simple cache to reduce API calls and avoid rate limits
_search_cache = {}
_nutrition_cache = {}

WORD_NUMBER_MAP = {
    'a': 1,
    'an': 1,
    'one': 1,
    'two': 2,
    'three': 3,
    'four': 4,
    'five': 5,
    'six': 6,
    'seven': 7,
    'eight': 8,
    'nine': 9,
    'ten': 10,
    'half': 0.5,
    'dozen': 12,
}

def parse_food_input(food_input):
    """
    Parse user input like "100g chicken breast", "1 medium apple", or "two eggs".
    Returns: (food_name, quantity, unit)
    """
    cleaned = food_input.strip()

    # Pattern: number + optional unit + food name (e.g., "100g chicken breast")
    match = re.match(r'^(\d+(?:\.\d+)?)\s*([a-zA-Z]+)?\s+(.+)$', cleaned)
    if match:
        quantity = float(match.group(1))
        raw_unit = (match.group(2) or '').lower()
        food_name = match.group(3).strip()

        # If no explicit unit, decide between grams vs counted items
        if raw_unit:
            unit = raw_unit
        else:
            countable_keywords = ['egg', 'eggs', 'apple', 'apples', 'banana', 'bananas', 'orange', 'oranges']
            unit = 'unit' if any(k in food_name.lower() for k in countable_keywords) else 'g'

        return food_name, quantity, unit

    # Pattern: word-number + food name (e.g., "two eggs", "a banana")
    word_match = re.match(r'^(?P<num_word>[a-zA-Z]+)\s+(?P<food>.+)$', cleaned.lower())
    if word_match:
        num_word = word_match.group('num_word')
        food_name = word_match.group('food').strip()
        if num_word in WORD_NUMBER_MAP:
            return food_name, float(WORD_NUMBER_MAP[num_word]), 'unit'

    # Fallback: treat as a single unit
    return cleaned, 1.0, 'unit'

def search_usda_food(food_name):
    """
    Search for food in USDA FoodData Central using data.gov API client.
    Uses X-Api-Key header authentication (recommended by data.gov).
    Implements caching to reduce API calls and avoid rate limits.
    """
    # Check cache first
    cache_key = food_name.lower().strip()
    if cache_key in _search_cache:
        print(f"[CACHE HIT] Using cached results for '{food_name}'")
        return _search_cache[cache_key]
    
    # Make API request if not cached
    response = data_gov_client.make_request(
        endpoint=f"{USDA_API_URL}/foods/search",
        params={
            'query': food_name,
            'pageSize': 10
        }
    )
    
    # Store in cache
    if response:
        _search_cache[cache_key] = response
        print(f"[CACHED] Stored results for '{food_name}'")
    
    return response

def get_food_nutrition(fdc_id, quantity, unit):
    """
    Get detailed nutrition info for a food item using data.gov API client.
    Implements caching to reduce API calls and avoid rate limits.
    fdc_id: FDC ID from search results
    quantity: amount user consumed
    unit: unit of measurement (g, cup, etc.)
    """
    # Check cache first (only cache by FDC ID, calculate quantity later)
    if fdc_id in _nutrition_cache:
        print(f"[CACHE HIT] Using cached nutrition for FDC ID {fdc_id}")
        food_data = _nutrition_cache[fdc_id]
    else:
        # Make API request if not cached
        food_data = data_gov_client.make_request(
            endpoint=f"{USDA_API_URL}/food/{fdc_id}"
        )
        if food_data:
            _nutrition_cache[fdc_id] = food_data
            print(f"[CACHED] Stored nutrition data for FDC ID {fdc_id}")
    
    if food_data:
        
        print(f"\n=== USDA API Response for FDC ID {fdc_id} ===")
        print(f"Food Description: {food_data.get('description', 'N/A')}")
        print(f"Food Category: {food_data.get('foodCategory', {}).get('description', 'N/A')}")
        print(f"Data Type: {food_data.get('dataType', 'N/A')}")
        
        # Extract nutrition facts - more flexible matching
        nutrition_facts = {'carbs': 0, 'protein': 0, 'fat': 0}
        
        if 'foodNutrients' in food_data:
            print(f"\nFound {len(food_data['foodNutrients'])} nutrients")
            for nutrient in food_data['foodNutrients']:
                # Get nutrient info with different possible structures
                nutrient_info = nutrient.get('nutrient', {})
                nutrient_name = nutrient_info.get('name', '').lower()
                
                # Try different value fields based on data type
                value = nutrient.get('amount') or nutrient.get('value', 0)
                
                print(f"  - {nutrient_name}: {value}")
                
                # Match carbohydrates (more flexible)
                if 'carbohydrate' in nutrient_name:
                    if 'by difference' in nutrient_name or 'total' in nutrient_name:
                        if nutrition_facts['carbs'] == 0:  # Only take first match
                            nutrition_facts['carbs'] = value
                            print(f"    ✓ MATCHED as carbs")
                
                # Match protein
                elif 'protein' in nutrient_name:
                    if nutrition_facts['protein'] == 0:
                        nutrition_facts['protein'] = value
                        print(f"    ✓ MATCHED as protein")
                
                # Match fat (try multiple variations)
                elif 'fat' in nutrient_name or 'lipid' in nutrient_name:
                    if 'total' in nutrient_name or nutrient_name == 'total lipid (fat)':
                        if nutrition_facts['fat'] == 0:
                            nutrition_facts['fat'] = value
                            print(f"    ✓ MATCHED as fat")
        
        print(f"\nExtracted nutrition: {nutrition_facts}")
        
        # Get serving size - check multiple fields
        serving_size = 100  # default assumption
        if 'servingSizeUnit' in food_data and 'servingSize' in food_data:
            try:
                if food_data.get('servingSizeUnit', 'g').lower() == 'g':
                    serving_size = float(food_data['servingSize'])
                else:
                    serving_size = 100
            except:
                serving_size = 100
        
        print(f"Serving size: {serving_size}g")
        
        # Convert quantity to grams if needed
        quantity_in_grams = quantity
        unit_lower = unit.lower()
        food_desc = food_data.get('description', '').lower()

        # Descriptive sizes with USDA-style defaults
        if unit_lower in ['small', 'sm']:
            if 'egg' in food_desc:
                quantity_in_grams = quantity * 50
            elif 'apple' in food_desc:
                quantity_in_grams = quantity * 149
            elif 'banana' in food_desc:
                quantity_in_grams = quantity * 101
            else:
                quantity_in_grams = quantity * 100

        elif unit_lower in ['medium', 'med', 'md']:
            if 'egg' in food_desc:
                quantity_in_grams = quantity * 60
            elif 'apple' in food_desc:
                quantity_in_grams = quantity * 182
            elif 'banana' in food_desc:
                quantity_in_grams = quantity * 118
            elif 'orange' in food_desc:
                quantity_in_grams = quantity * 131
            else:
                quantity_in_grams = quantity * 150

        elif unit_lower in ['large', 'lg', 'big']:
            if 'egg' in food_desc:
                quantity_in_grams = quantity * 70
            elif 'apple' in food_desc:
                quantity_in_grams = quantity * 223
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

        # Liquid volume
        elif unit_lower in ['ml', 'milliliter', 'milliliters']:
            quantity_in_grams = quantity

        # Countable items default
        elif unit_lower in ['piece', 'pieces', 'item', 'items', 'unit', 'units', 'egg', 'eggs']:
            # Use food-specific defaults when counting items
            default_piece_weight = 150
            if 'egg' in food_desc:
                default_piece_weight = 60
            elif 'banana' in food_desc:
                default_piece_weight = 118
            elif 'apple' in food_desc:
                default_piece_weight = 182
            elif 'orange' in food_desc:
                default_piece_weight = 131
            quantity_in_grams = quantity * default_piece_weight

        else:
            # Unknown unit - assume grams
            print(f"[WARNING] Unknown unit '{unit}' - treating quantity as grams")
            quantity_in_grams = quantity
        
        print(f"Input: {quantity}{unit} = {quantity_in_grams}g")
        
        # Scale nutrition values
        scale_factor = quantity_in_grams / serving_size
        scaled_nutrition = {}
        for key, val in nutrition_facts.items():
            scaled_nutrition[key] = round(val * scale_factor, 2)
        
        print(f"Scale factor: {scale_factor}")
        print(f"Final scaled nutrition: {scaled_nutrition}")
        print("=" * 50 + "\n")
        
        return {
            'food_name': food_data.get('description', ''),
            'carbs': scaled_nutrition.get('carbs', 0),
            'protein': scaled_nutrition.get('protein', 0),
            'fat': scaled_nutrition.get('fat', 0),
            'quantity': quantity,
            'unit': unit,
            'serving_size': serving_size
        }
    print(f"Error: Could not retrieve food nutrition data for FDC ID {fdc_id}")
    return None

@app.route('/')
def main():
    # Redirect base URL to chatbot page
    return redirect('/chatbot')

@app.route('/nutrition_calculation', methods=["GET", "POST"])
def nutrition_calculation():
    path = request.args.get('path')
    name = path.split("/")[3].split('.')[0]
    with open('./static/foodseg/' + name + '/' + name + "_nutrition.json") as f: nutrition_data = json.load(f)
    results = {
        'image_origin': path,
        'image_seglab': './static/foodseg/' + name + '/' + name + "_labeled_seg.png",
        'image_report': nutrition_data
    }

    # nutrition = {
    #     'carbohydrate': round(nutrition_data['carbs'], 2),
    #     'protein': round(nutrition_data['protein'], 2),
    #     'fat': round(nutrition_data['fat'], 2)
    # }

    if request.method == "POST":
        next = request.form["next"]
        if next: return redirect(url_for("data_collection", carbs=round(nutrition_data['carbs'], 2), protein=round(nutrition_data['protein'], 2), fat=round(nutrition_data['fat'], 2)))

    return render_template("nutrition-calculation.html", results=results)

def calculate_rmr(weight, height, age, sex):
    if sex == 0:
        rmr = (9.99 * weight) + (6.25 * height) - (4.92 * age) + 5 
    else:
        rmr = (9.99 * weight) + (6.25 * height) - (4.92 * age) - 161
    return rmr

def calculate_daily_calories(rmr, activity_level):
    if activity_level == 0:
        calories = rmr * 1.2
    elif activity_level == 1:
        calories = rmr * 1.375
    elif activity_level == 2:
        calories = rmr * 1.55
    else:
        calories = rmr * 1.725
    return calories

def constraint_func(x): 
    return x[0] + x[1]

# x, y [5, 10], z in [1, 3]
def calculate_cube_dimension(volume):
    x = y = 10
    z = 3

    for i in np.arange(5.0, 10.0, 1.0):
        if volume / (i * i) <= 3 and volume / (i * i) >= 1:
            z = volume / (i * i)
            x = y = i

    return x * 10.0, y * 10.0, z * 10.0

min_size = np.array([8.0, 8.0, 0.15])  # Minimum dimensions in cm
max_size = np.array([15.0, 13.0, 2.2])  # Maximum dimensions in cm
MAX_VOLUME = max_size[0] * max_size[1] * max_size[2] # Dimention is cm
TOLERANCE = 400  # allow feasible solutions even with moderate error

def calculate_cube_dimension(volume):
    # Define size limits in cm

    # Calculate minimum and maximum volume based on maximum dimensions
    min_volume = min_size[0] * min_size[1] * min_size[2]
    max_volume = max_size[0] * max_size[1] * max_size[2]

    # Check if the volume is valid
    if volume < min_volume: return min_size[0] * 10.0, min_size[1] * 10.0,  min_size[2] * 10.0
    if volume > max_volume: return max_size[0] * 10.0, max_size[1] * 10.0,  max_size[2] * 10.0  # Return zero if volume is invalid

    # Iterate through possible dimensions
    for x in np.arange(min_size[0], max_size[0] + 0.1, 0.1):  # Increment by 0.5 cm
        for y in np.arange(min_size[1], max_size[1] + 0.1, 0.1):  # Increment by 0.5 cm
            z = volume / (x * y)  # Calculate height based on volume
            # Check if height is within limits
            if min_size[2] <= z <= max_size[2]:
                return x * 10.0, y * 10.0, z * 10.0  # Return dimensions in mm

    return 0, 0, 0 # Return zero if no valid dimensions are found

def mesh_generation(name, weight, density): #g/cm3
    x, y, z = calculate_cube_dimension(weight / density) # in mm
    # print(name, weight, density, weight / density, x, y, z)
    if (x == 0 or y == 0 or z == 0): return 0, 0, 0
    # print(x, y, z)
    # If mesh generation is disabled, just return dimensions without creating STL
    if MESH_MODE == 'none':
        return x, y, z

    # Lazy import to avoid loading numpy-stl unless needed
    try:
        from stl import mesh as stl_mesh
    except Exception as e:
        print(f"[WARN] Failed to import numpy-stl: {e}. Skipping STL generation.")
        return x, y, z

    vertices = np.array([[
        0, 0, 0],
        [x, 0, 0],
        [x, y, 0],
        [0, y, 0],
        [0, 0, z],
        [x, 0, z],
        [x, y, z],
        [0, y, z]])

    faces = np.array([[
        0,3,1],
        [1,3,2],
        [0,4,7],
        [0,7,3],
        [4,5,6],
        [4,6,7],
        [5,1,2],
        [5,2,6],
        [2,3,6],
        [3,7,6],
        [0,1,5],
        [0,5,4]])

    try:
        cube = stl_mesh.Mesh(np.zeros(faces.shape[0], dtype=stl_mesh.Mesh.dtype))
        for i, f in enumerate(faces):
            for j in range(3):
                cube.vectors[i][j] = vertices[f[j],:]

        import tempfile
        temp_dir = tempfile.gettempdir()
        tmp_path = os.path.join(temp_dir, name)
        blob_path = f"meshes/{name}"
        cube.save(tmp_path)

        if MESH_STORAGE == 'gcs':
            upload_to_gcs(bucket_name, tmp_path, blob_path)
            # Remove local temp file after upload
            try:
                os.remove(tmp_path)
            except Exception:
                pass
        else:
            # Keep local file for direct download via /download-stl
            print(f"[INFO] Stored STL locally at {tmp_path}")
            # Record manifest to allow on-demand regeneration
            manifest = _load_manifest()
            manifest[name] = { 'amount': float(weight), 'density': float(density) }
            _save_manifest(manifest)
    except Exception as e:
        print(f"[WARN] STL generation/upload failed for {name}: {e}")

    return x, y, z

def recommend(gender, age, height, weight, carbohydrate, protein, fat, activity, diet, preference):
    rmr = calculate_rmr(weight, height, age, gender)
    calories = calculate_daily_calories(rmr, activity)
    diet_scale = [(0.50 / 4.1, 0.20 / 4.1, 0.30 / 8.8), # balanced
              (0.60 / 4.1, 0.20 / 4.1, 0.20 / 8.8), # low fat
              (0.20 / 4.1, 0.30 / 4.1, 0.50 / 8.8), # low carbs,
              (0.28 / 4.1, 0.39 / 4.1, 0.33 / 8.8)] # high protein

    carbohydrate_intake, protein_intake, fat_intake = (calories * i for i in diet_scale[diet])

    carbohydrate_needed = carbohydrate_intake - carbohydrate
    protein_needed = protein_intake - protein
    fat_needed = fat_intake - fat

    # Each row is [carbohydrates, proteins, fats]
    W_per_hundred = np.array([
        [17, 1.56, 0.05],  # PSP
        [11.2, 6.6, 0.61],   # Red Lentils
        [1.4, 1.38, 12.1],  # Avocado
        [0.06, 19.8, 1.15]   # Chicken Breast
    ])

    W = W_per_hundred * 0.01

    name = ['Purple Sweet Potato', 'Red Lentils', 'Avocado', 'Chicken Breast']
    density = [0.81, 1.182, 0.63, 0.82]
    
    if preference: blocked = 3
    else: blocked = 1

    y = np.array([carbohydrate_needed, protein_needed, fat_needed]) # [carbohydrates, proteins, fats]

    # positive_indices = np.where(y > 0)[0]
    # positive_y = y[positive_indices]
    # positive_y = y
    # positive_y[positive_y <= 0] = 0
    
    nonlinear_constraint = NonlinearConstraint(constraint_func, 0.01, np.inf)

    solutions = []
    best_candidate = None  # fallback if nothing meets tolerance

    # def fun(amounts, nutritional_matrix, target):
    #     amounts = amounts.reshape(-1, 1)
    #     total_nutrition = np.dot(nutritional_matrix.T, amounts)
    #     return np.linalg.norm(total_nutrition - target)

    upper_bound = 10           # set None for “no limit”
    tolerance   = 1e-6

    def solve_pair(selected_nutrition, positive_y):
        # A = np.array([[nutrients[name1][c], nutrients[name2][c]] for c in cols], dtype=float) #selected_nutrition
        # Least-squares solution (satisfies A @ x ≈ b in L2 sense)
        # x, residuals, _, _ = np.linalg.lstsq(selected_nutrition.T, positive_y, rcond=None)
        x, res_norm = nnls(selected_nutrition.T, positive_y)
        residual = np.linalg.norm(selected_nutrition.T @ x - positive_y, ord=1)     # total absolute error
        return x, residual

    if np.any(y > 0):
        mask = y > 0  
        for indices in combinations(range(4), 2):
            if (blocked in indices): continue
            selected_nutrition = W[list(indices)]

            fun = lambda x: np.linalg.norm(selected_nutrition.T[mask, :] @ x - y[mask])
            res = minimize(fun, np.zeros(len(indices)), method='L-BFGS-B', bounds=[(0., MAX_VOLUME / density[indices[x]]) for x in range(len(indices))])

            print(f"Testing combination {indices}: amounts={res.x}, error={res.fun}")
            # Track best candidate even if above tolerance
            if res.x[0] > 0 and res.x[1] > 0:
                if best_candidate is None or res.fun < best_candidate[2]:
                    best_candidate = (indices, res.x, res.fun)

            # Accept solution if both amounts are positive and error is reasonable
            if res.x[0] > 0 and res.x[1] > 0 and res.fun < TOLERANCE:
                solutions.append((indices, res.x, res.fun))
                print(f"  -> ACCEPTED")
            else:
                print(f"  -> REJECTED (tolerance={TOLERANCE})")

        # If none accepted, use best candidate so we always produce meshes
        if not solutions and best_candidate:
            solutions.append(best_candidate)
            print(f"\nNo solutions under tolerance. Using best available combination with error={best_candidate[2]:.2f}")

        solutions.sort(key=lambda x: x[2])
        print(f"\n=== Found {len(solutions)} valid solutions ===")
    
    # Limit number of solutions to avoid long runtimes / memory use
    solutions = solutions[:MAX_SOLUTIONS]
    results = []

    for index in range(len(solutions)):
        indices, amounts, norm = solutions[index]
        material_mesh_list = []
        carbohydrate_supplement = protein_supplement = fat_supplement = 0
        # print(amounts)
        for i in range(len(amounts)):             
            amounts[i] = round(amounts[i], 2)
            if amounts[i] == 0: continue
            mesh_name = str(index) + "_" + name[indices[i]] + ".stl"
            carbohydrate_supplement += amounts[i] * W[indices[i]][0]
            protein_supplement += amounts[i] * W[indices[i]][1]
            fat_supplement += amounts[i] * W[indices[i]][2]
            # Decide whether to generate STL based on MESH_MODE
            generate_mesh = (MESH_MODE == 'all') or (MESH_MODE == 'first' and index == 0)
            x, y, z = mesh_generation(mesh_name, amounts[i], density[indices[i]]) if generate_mesh else calculate_cube_dimension(amounts[i] / density[indices[i]])
            mesh_field = mesh_name if generate_mesh and x and y and z and MESH_MODE != 'none' else ''
            if x and y and z:
                material_mesh_list.append({'name': name[indices[i]], 'mesh': mesh_field, 'gram': amounts[i], 'x': round(x, 2), 'y': round(y, 2), 'z': round(z, 2)})
        results.append((material_mesh_list, round(carbohydrate_supplement, 2), round(protein_supplement, 2), round(fat_supplement, 2)))            

    # print(results)

    recommend_dict = {'calories': round(calories, 2), 
                      'carbohydrate_intake': round(carbohydrate_intake, 2),
                      'protein_intake': round(protein_intake, 2),
                      'fat_intake': round(fat_intake, 2),
                      'carbohydrate_needed': round(carbohydrate_needed, 2),
                      'protein_needed': round(protein_needed, 2),
                      'fat_needed': round(fat_needed, 2),
                    #   'carbohydrate_supplement': round(carbohydrate_needed, 2),
                    #   'protein_supplement': round(protein_needed, 2),
                    #   'fat_supplement': round(fat_needed, 2),
                      'results': results
                    }
    
    return recommend_dict
 
@app.route('/data_collection', methods=["GET", "POST"])
def data_collection():
    # carbs = float(request.args.get('carbs'))
    # protein = float(request.args.get('protein'))
    # fat = float(request.args.get('fat'))
    if request.method == "POST":
        # print(request.form)
        submit = request.form["submit"]
        info_dict = {
            'gender': int(request.form["gender"]),
            'age': int(request.form["age"]),
            'height': float(request.form["height"]), 
            'weight': float(request.form["weight"]), 
            'carbs': float(request.form["carbohydrate"]),
            'protein': float(request.form["protein"]),
            'fat': float(request.form["fat"]),
            'activity': int(request.form["activity"]),
            'diet': int(request.form["diet"]),
            'preference': int(request.form["preference"]),
        }
        
        if submit: return redirect(url_for("nutrition_recommendation_display", info_dict=info_dict))
    # return render_template("data-collection.html", carbs=carbs, protein=protein, fat=fat)
    return render_template("data-collection.html")

def list2dict(info_dict):
    new_dict = {}
    for d in info_dict:
        index, value = d.split(':')

        if '{' in index: index = index[2:-1]
        else: index = index[2:-1]

        if '}' in value: value = value[:-1]
        else: value = value

        new_dict[index] = float(value)
    
    return new_dict

@app.route('/download/<path:filename>', methods=['GET', 'POST'])
def download(filename):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    
    blob_path = os.path.join("/meshes", filename)
    blob = bucket.blob(blob_path)

    file_stream = io.BytesIO()
    blob.download_to_file(file_stream)
    file_stream.seek(0)

    return send_file(file_stream, as_attachment=True, download_name=filename)

@app.route('/nutrition_recommendation_display', methods=["GET", "POST"])
def nutrition_recommendation_display():
    info_dict = request.args.get('info_dict')
    
    # If no info_dict provided, use default values for demo
    if info_dict is None:
        # Use default values as a dict directly
        info_dict = {
            'gender': 0,
            'age': 25,
            'height': 170.0,
            'weight': 70.0,
            'carbs': 0.0,
            'protein': 0.0,
            'fat': 0.0,
            'activity': 2,
            'diet': 0,
            'preference': 0
        }
    else:
        info_dict = info_dict.split(",")
        info_dict = list2dict(info_dict)
    
    # print(info_dict)
    recommend_dict = recommend(int(info_dict['gender']), int(info_dict['age']), info_dict['height'], info_dict['weight'], info_dict['carbs'], \
                               info_dict['protein'], info_dict['fat'], int(info_dict['activity']), int(info_dict['diet']), int(info_dict['preference']))

    # print(recommend_dict)
    
    if request.method == "POST":
        # print(request.form)
        refresh = request.form["refresh"]
        # if refresh: return redirect("/upload_image")
        if refresh: return redirect("/data_collection")
    return render_template("nutrition-recommendation.html", recommend_dict=recommend_dict)

# Chatbot routes
@app.route('/chatbot', methods=["GET", "POST"])
def chatbot():
    """Serve the chatbot interface"""
    return render_template("chatbot.html")

@app.route('/api/search-food', methods=['POST'])
def api_search_food():
    """Search for food in USDA database and return parsed nutrition"""
    try:
        data = request.json
        food_input = data.get('food_input', '').strip()
        
        if not food_input:
            return jsonify({'error': 'No food input provided'}), 400
        
        # Parse user input
        food_name, quantity, unit = parse_food_input(food_input)
        
        # Search USDA API
        search_results = search_usda_food(food_name)

        # Handle upstream errors (rate limit / connectivity)
        if search_results is None:
            return jsonify({
                'error': 'Upstream nutrition API unavailable (possible rate limit or connectivity issue). Please wait a bit and try again.',
                'suggestion': 'If this keeps happening, request a higher API limit or try later.'
            }), 503
        
        if 'foods' not in search_results or len(search_results['foods']) == 0:
            return jsonify({
                'error': f'No foods found for "{food_name}"',
                'suggestion': 'Try searching for a more specific food name'
            }), 404
        
        # Get the first result's detailed nutrition
        top_food = search_results['foods'][0]
        fdc_id = top_food.get('fdcId')
        
        nutrition = get_food_nutrition(fdc_id, quantity, unit)
        
        if not nutrition:
            return jsonify({
                'error': 'Could not retrieve nutrition information (upstream API may be rate limited).',
                'suggestion': 'Wait a few minutes and try again, or reduce rapid repeated searches.'
            }), 503
        
        return jsonify({
            'success': True,
            'nutrition': nutrition,
            'original_input': food_input
        }), 200
    
    except Exception as e:
        print(f"Error in api_search_food: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/calculate-recommendation', methods=['POST'])
def api_calculate_recommendation():
    """Calculate nutrition recommendation based on user info and daily intake"""
    try:
        data = request.json or {}
        user_info = data.get('user_info', {})
        daily_nutrition = data.get('daily_nutrition', {})

        if not data:
            return jsonify({'error': 'Request body missing. Send JSON with user_info and daily_nutrition.'}), 400

        def to_int(val, default=0):
            try:
                # Treat "" or None as missing -> default
                if val is None or val == '':
                    return default
                return int(val)
            except Exception:
                return default

        def to_float(val, default=0.0):
            try:
                if val is None or val == '':
                    return default
                return float(val)
            except Exception:
                return default

        # Extract values with safe coercion
        gender = to_int(user_info.get('gender'), 0)
        age = to_int(user_info.get('age'), 0)
        height = to_float(user_info.get('height'), 0)
        weight = to_float(user_info.get('weight'), 0)
        carbs = to_float(daily_nutrition.get('carbs'), 0)
        protein = to_float(daily_nutrition.get('protein'), 0)
        fat = to_float(daily_nutrition.get('fat'), 0)
        activity = to_int(user_info.get('activity'), 0)
        diet = to_int(user_info.get('diet'), 0)
        preference = to_int(user_info.get('preference'), 0)

        # Minimal validation with soft defaults
        missing = []
        if gender not in [0, 1]: missing.append('gender')
        if age <= 0: missing.append('age')
        if height <= 0: missing.append('height')
        if weight <= 0: missing.append('weight')
        if activity not in [0, 1, 2, 3]: missing.append('activity')
        if diet not in [0, 1, 2, 3]: missing.append('diet')
        if preference not in [0, 1]: missing.append('preference')

        # If missing, apply sensible defaults to keep API responsive
        if missing:
            defaults = {
                'gender': 0,
                'age': 25,
                'height': 170.0,
                'weight': 70.0,
                'activity': 2,
                'diet': 0,
                'preference': 0,
            }
            gender = gender if gender in [0,1] else defaults['gender']
            age = age if age > 0 else defaults['age']
            height = height if height > 0 else defaults['height']
            weight = weight if weight > 0 else defaults['weight']
            activity = activity if activity in [0,1,2,3] else defaults['activity']
            diet = diet if diet in [0,1,2,3] else defaults['diet']
            preference = preference if preference in [0,1] else defaults['preference']
            note = f"Applied defaults for: {', '.join(missing)}"
        else:
            note = None
        
        # Call existing recommendation function with a robust fallback
        try:
            recommend_dict = recommend(gender, age, height, weight, carbs, protein, fat, activity, diet, preference)
        except Exception as rec_err:
            # Fallback: compute targets and needs without optimization/meshes
            try:
                rmr = calculate_rmr(weight, height, age, gender)
                calories = calculate_daily_calories(rmr, activity)
                diet_scale = [
                    (0.50 / 4.1, 0.20 / 4.1, 0.30 / 8.8),  # balanced
                    (0.60 / 4.1, 0.20 / 4.1, 0.20 / 8.8),  # low fat
                    (0.20 / 4.1, 0.30 / 4.1, 0.50 / 8.8),  # low carbs
                    (0.28 / 4.1, 0.39 / 4.1, 0.33 / 8.8),  # high protein
                ]
                carbohydrate_intake, protein_intake, fat_intake = (calories * i for i in diet_scale[diet])
                recommend_dict = {
                    'calories': round(calories, 2),
                    'carbohydrate_intake': round(carbohydrate_intake, 2),
                    'protein_intake': round(protein_intake, 2),
                    'fat_intake': round(fat_intake, 2),
                    'carbohydrate_needed': round(carbohydrate_intake - carbs, 2),
                    'protein_needed': round(protein_intake - protein, 2),
                    'fat_needed': round(fat_intake - fat, 2),
                    'results': []
                }
                note = 'Generated minimal recommendation (optimization failed)'
                if DIAG_MODE:
                    recommend_dict.update({'error': str(rec_err)})
            except Exception as fb_err:
                print(f"Fallback generation failed: {fb_err}")
                if DIAG_MODE:
                    return jsonify({'error': f'Fallback failed: {fb_err}'}), 500
                raise rec_err

        if note:
            recommend_dict['note'] = note
        
        return jsonify({
            'success': True,
            'recommendation': recommend_dict
        }), 200
    
    except Exception as e:
        print(f"Error in api_calculate_recommendation: {e}")
        if DIAG_MODE:
            return jsonify({'error': str(e)}), 500
        return jsonify({'error': 'Recommendation failed. Please try again later.'}), 500

@app.route('/download-stl/<path:filename>', methods=['GET'])
def download_stl(filename):
    """Download STL file from Google Cloud Storage"""
    try:
        print(f"[DEBUG] Attempting to download STL file: {filename}")
        if MESH_STORAGE == 'local':
            import tempfile
            temp_dir = tempfile.gettempdir()
            local_path = os.path.join(temp_dir, filename)
            if not os.path.exists(local_path):
                print(f"[DEBUG] Local STL not found at {local_path}, attempting regeneration from manifest")
                # Try on-demand regeneration if manifest has info
                manifest = _load_manifest()
                meta = manifest.get(filename)
                if meta and 'amount' in meta and 'density' in meta:
                    try:
                        # Regenerate STL file
                        mesh_generation(filename, float(meta['amount']), float(meta['density']))
                    except Exception as regen_err:
                        print(f"[WARN] Regeneration failed: {regen_err}")
                else:
                    print("[DEBUG] No manifest entry for this file; cannot regenerate")
                # Re-check existence after regeneration attempt
                if not os.path.exists(local_path):
                    return jsonify({'error': f'File not found (local): {filename}'}), 404
            with open(local_path, 'rb') as f:
                file_data = io.BytesIO(f.read())
            file_data.seek(0)
            print(f"[DEBUG] Serving local STL {filename}, size: {file_data.getbuffer().nbytes} bytes")
            return send_file(
                file_data,
                mimetype='application/octet-stream',
                as_attachment=True,
                download_name=filename
            )
        else:
            storage_client = storage.Client()
            bucket = storage_client.bucket(bucket_name)
            blob_path = f"meshes/{filename}"
            print(f"[DEBUG] GCS blob path: {blob_path}")
            blob = bucket.blob(blob_path)
            
            # Check if blob exists
            if not blob.exists():
                print(f"[DEBUG] Blob does not exist at path: {blob_path}")
                return jsonify({'error': f'File not found in storage: {filename}'}), 404
            
            # Download to memory
            file_data = io.BytesIO()
            blob.download_to_file(file_data)
            file_data.seek(0)
            print(f"[DEBUG] Successfully downloaded {filename}, size: {file_data.getbuffer().nbytes} bytes")
            
            return send_file(
                file_data,
                mimetype='application/octet-stream',
                as_attachment=True,
                download_name=filename
            )
    except Exception as e:
        print(f"[ERROR] Error downloading STL: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'File not found or download failed: {str(e)}'}), 404

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'}), 200
 
# main driver function
if __name__ == '__main__':
    # Run on 0.0.0.0 to allow external access (Cloudflare tunnel, network access, etc.)
    app.run(host="0.0.0.0", port=5000, debug=True)