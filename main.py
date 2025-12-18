from flask import Flask, render_template, redirect, request, abort, send_file, url_for
from google.cloud import storage
from google.auth.exceptions import DefaultCredentialsError
import numpy as np
from scipy.optimize import minimize, NonlinearConstraint, nnls, linprog
from itertools import combinations
from stl import mesh
import os
import json
import io

# export GOOGLE_APPLICATION_CREDENTIALS="food-ai-455507-e2a9c115814e.json"     
json_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "food-ai-455507-e2a9c115814e.json"))
if os.path.exists(json_path):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = json_path
 
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = "./static/uploads"
bucket_name = "food-ai"

def upload_to_gcs(bucket_name, source_file_name, destination_blob_name):
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(source_file_name)
        return True
    except DefaultCredentialsError:
        return False
    except Exception:
        return False

    # print(f"File {source_file_name} uploaded to {destination_blob_name}.")

@app.route('/')
def main():
    # return render_template("test.html")
    return redirect("/data_collection")
    # return redirect("/upload_image")

@app.route('/upload_image', methods=["GET", "POST"])
def upload_image():
    if request.method == 'POST' and 'upload-image' in request.files:
        file = request.files['upload-image']
        path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(path)
        # print(path[1:])
        return redirect(url_for("nutrition_calculation", path=path[1:]))
    return render_template("upload-image.html")

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
TOLERANCE = 100

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

    vertices = np.array([\
        [0, 0, 0],
        [x, 0, 0],
        [x, y, 0],
        [0, y, 0],
        [0, 0, z],
        [x, 0, z],
        [x, y, z],
        [0, y, z]])
    
    faces = np.array([\
        [0,3,1],
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

    cube = mesh.Mesh(np.zeros(faces.shape[0], dtype=mesh.Mesh.dtype))
    for i, f in enumerate(faces):
        for j in range(3):
            cube.vectors[i][j] = vertices[f[j],:]

    import tempfile
    temp_dir = tempfile.gettempdir()
    tmp_path = os.path.join(temp_dir, name)
    blob_path = os.path.join("/meshes", name)
    cube.save(tmp_path)
    upload_to_gcs(bucket_name, tmp_path, blob_path)
    os.remove(tmp_path)

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

            # print("selected_nutrition shape:", selected_nutrition.shape)
            # print("positive_y shape:",        positive_y.shape)

            # print(selected_nutrition.T[mask, :].shape)
            # print(y[mask].shape)

            # amounts, residual = solve_pair(selected_nutrition, positive_y)
            # res = linprog(c=np.ones(2),
            #       A_eq=selected_nutrition.T[mask, :], b_eq=y[mask],
            #       bounds=(0, None),
            #       method='highs')
            fun = lambda x: np.linalg.norm(selected_nutrition.T[mask, :] @ x - y[mask])
            # for x in range(len(indices)): print((0., MAX_VOLUME / density[indices[x]]))
            res = minimize(fun, np.zeros(len(indices)), method='L-BFGS-B', bounds=[(0., MAX_VOLUME / density[indices[x]]) for x in range(len(indices))])


            print(f"Testing combination {indices}: amounts={res.x}, error={res.fun}")
            # Accept solution if both amounts are positive and error is reasonable
            if res.x[0] > 0 and res.x[1] > 0 and res.fun < TOLERANCE:
                solutions.append((indices, res.x, res.fun))
                print(f"  -> ACCEPTED")
            else:
                print(f"  -> REJECTED (tolerance={TOLERANCE})")


            # initial_guess = np.zeros(2)
            # bounds = [(0, None), (0, None)]

            # print(selected_nutrition, positive_y)

            # # sol = minimize(fun, initial_guess, args=(selected_nutrition, positive_y), method='SLSQP', bounds=bounds, constraints=[nonlinear_constraint])
            # sol = minimize(fun, initial_guess, args=(selected_nutrition, positive_y), method='SLSQP', bounds=bounds, constraints=[])

            # if sol.success:
            #     solutions.append((indices, sol.x, sol.fun))  # Store (indices, amounts, norm)

        solutions.sort(key=lambda x: x[2])
        print(f"\n=== Found {len(solutions)} valid solutions ===")
    
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
            x, y, z = mesh_generation(mesh_name, amounts[i], density[indices[i]])
            if x and y and z:
                material_mesh_list.append({'name': name[indices[i]], 'mesh': mesh_name, 'gram': amounts[i], 'x': round(x, 2), 'y': round(y, 2), 'z': round(z, 2)})
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
    info_dict = info_dict.split(",")
    # print(info_dict)
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
 
# main driver function
if __name__ == '__main__':
    app.run(host="127.0.0.1", port=8080, debug=True)