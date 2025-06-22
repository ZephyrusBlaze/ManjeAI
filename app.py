from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
import os
from google import genai
from dotenv import load_dotenv
import requests

load_dotenv(".env")

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"
if not os.path.exists(app.config["UPLOAD_FOLDER"]):
    os.makedirs(app.config["UPLOAD_FOLDER"])

DB_PATH = "history.db"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LOGMEAL_API_KEY = os.getenv("LOGMEAL_API_KEY")


# --- DB ---
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with open("schema.sql", encoding="utf-8") as f:
        schema = f.read()
    conn = get_db()
    conn.executescript(schema)
    conn.commit()
    conn.close()


# --- Routes ---
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        ingredients = request.form.get("ingredients", "")
        language = request.form.get("language", "English")
        image = request.files.get("image")
        detected_ingredients = []
        if image and image.filename:
            img_path = os.path.join(app.config["UPLOAD_FOLDER"], image.filename)
            image.save(img_path)
            api_user_token = LOGMEAL_API_KEY
            headers = {"Authorization": "Bearer " + api_user_token}
            api_url = "https://api.logmeal.com/v2"
            try:
                with open(img_path, "rb") as img_file:
                    resp = requests.post(
                        api_url + "/image/segmentation/complete",
                        files={"image": img_file},
                        headers=headers,
                        timeout=20,
                    )
                if resp.status_code == 200:
                    image_id = resp.json().get("imageId")
                    if image_id:
                        resp_ing = requests.post(
                            api_url + "/nutrition/recipe/ingredients",
                            json={"imageId": image_id},
                            headers=headers,
                            timeout=20,
                        )
                        if resp_ing.status_code == 200:
                            recipe = resp_ing.json().get("recipe", [])
                            detected_ingredients = [
                                item["name"] for item in recipe if "name" in item
                            ]
            except Exception:
                detected_ingredients = []
        all_ingredients = list(
            set(
                [i.strip() for i in ingredients.split(",") if i.strip()]
                + detected_ingredients
            )
        )
        return redirect(
            url_for("result", ingredients=",".join(all_ingredients), language=language)
        )
    return render_template("index.html")


@app.route("/result")
def result():
    ingredients = request.args.get("ingredients", "")
    language = request.args.get("language", "English")
    if not ingredients:
        return redirect(url_for("index"))
    markdown, nutrition, suggestion, chart_data, error = get_gemini_recipe(
        ingredients, language
    )
    return render_template(
        "result.html",
        ingredients=ingredients,
        markdown=markdown,
        nutrition=nutrition,
        suggestion=suggestion,
        chart_data=chart_data,
        language=language,
        error=error,
    )


@app.route("/save", methods=["POST"])
def save():
    data = request.json
    ingredients = data.get("ingredients", "")
    markdown = data.get("markdown", "")
    nutrition = data.get("nutrition", "")
    conn = get_db()
    conn.execute(
        "INSERT INTO history (ingredients, markdown, nutrition) VALUES (?, ?, ?)",
        (ingredients, markdown, nutrition),
    )
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})


@app.route("/history")
def history():
    conn = get_db()
    cur = conn.execute("SELECT * FROM history ORDER BY date_created DESC")
    rows = cur.fetchall()
    conn.close()
    return render_template("history.html", rows=rows)


@app.route("/view/<int:recipe_id>")
def view_recipe(recipe_id):
    conn = get_db()
    cur = conn.execute("SELECT * FROM history WHERE id = ?", (recipe_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return redirect(url_for("history"))

    import re

    nutrition = row["nutrition"] or ""
    cal = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*kcal", nutrition, re.I)
    protein = re.search(
        r"([0-9]+(?:\.[0-9]+)?)\s*g\s*protein|protein:\s*([0-9]+(?:\.[0-9]+)?)\s*g",
        nutrition,
        re.I,
    )
    fiber = re.search(
        r"([0-9]+(?:\.[0-9]+)?)\s*g\s*fiber|fiber:\s*([0-9]+(?:\.[0-9]+)?)\s*g",
        nutrition,
        re.I,
    )
    vitA = re.search(
        r"([0-9]+(?:\.[0-9]+)?)\s*mg\s*vitamin\s*A|vitamin\s*A:\s*([0-9]+(?:\.[0-9]+)?)\s*mg",
        nutrition,
        re.I,
    )
    chart_data = [
        float(cal.group(1)) if cal else 0,
        float(protein.group(1) or protein.group(2)) if protein else 0,
        float(fiber.group(1) or fiber.group(2)) if fiber else 0,
        float(vitA.group(1) or vitA.group(2)) if vitA else 0,
    ]

    markdown = row["markdown"]
    if markdown and markdown.startswith('"') and markdown.endswith('"'):
        markdown = markdown[1:-1]
    nutrition = row["nutrition"]
    if nutrition and nutrition.startswith('"') and nutrition.endswith('"'):
        nutrition = nutrition[1:-1]

    import re

    markdown = re.sub(
        r"^(#+)([ \t]+)(.*)$",
        lambda m: f"{m.group(1)}{m.group(2)}**{m.group(3).strip()}**",
        markdown,
        flags=re.MULTILINE,
    )
    markdown = markdown.strip()
    return render_template(
        "result.html",
        ingredients=row["ingredients"],
        markdown=markdown,
        nutrition=nutrition,
        suggestion="",
        chart_data=chart_data,
        language="English",
        error=None,
    )


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/detect", methods=["POST"])
def detect():
    image = request.files.get("image")
    if not image or not image.filename:
        return jsonify({"ingredients": []})
    img_path = os.path.join(app.config["UPLOAD_FOLDER"], image.filename)
    image.save(img_path)
    api_user_token = LOGMEAL_API_KEY
    headers = {"Authorization": "Bearer " + api_user_token}
    api_url = "https://api.logmeal.com/v2"
    try:
        with open(img_path, "rb") as img_file:
            resp = requests.post(
                api_url + "/image/segmentation/complete",
                files={"image": img_file},
                headers=headers,
                timeout=20,
            )
        if resp.status_code != 200:
            return jsonify({"ingredients": []})
        image_id = resp.json().get("imageId")
        if not image_id:
            return jsonify({"ingredients": []})
        resp_ing = requests.post(
            api_url + "/nutrition/recipe/ingredients",
            json={"imageId": image_id},
            headers=headers,
            timeout=20,
        )
        if resp_ing.status_code != 200:
            return jsonify({"ingredients": []})
        recipe = resp_ing.json().get("recipe", [])
        detected_ingredients = [item["name"] for item in recipe if "name" in item]
        return jsonify({"ingredients": detected_ingredients})
    except Exception:
        return jsonify({"ingredients": []})


# --- Gemini Recipe Logic ---
def get_gemini_recipe(ingredients, language):
    prompt = f"""
You are a smart cooking assistant for food-insecure regions like Haiti.
The user has the following ingredients: {ingredients}

Please:
1. Suggest one low-cost, fuel-saving recipe using **only** these ingredients. Write the recipe in Markdown format, starting with a title, then a list of ingredients, then step-by-step instructions with icons/emojis. Do not just write a summary or intro, always include a full recipe.
2. Provide a nutrition estimate in this exact format (on a single line): Nutrition: Calories: X kcal, Protein: Y g, Fiber: Z g, Vitamin A: W mg
3. Identify missing nutrients and suggest cheap, local foods to balance it. Your suggestions must be context-aware: for sweet dishes, suggest only appropriate sweet or neutral add-ons (e.g., nuts, fruits, honey, coconut, etc.), and for savory dishes, suggest only appropriate savory add-ons (e.g., beans, greens, eggs, etc.). Write this as: Suggestion: [Markdown-formatted suggestions, use lists and bold for foods]
4. Keep the language friendly, clear, and if selected, use **Haitian Creole**.

Respond in: {language}

Format your answer as:
---
[Markdown recipe: include a title, ingredients list, and step-by-step instructions. Do not write only a summary.]
---
Nutrition: Calories: X kcal, Protein: Y g, Fiber: Z g, Vitamin A: W mg
---
Suggestion: [Markdown-formatted suggestions]
---
"""
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model="gemini-2.5-flash", contents=prompt
        )
        text = response.text

        parts = [p.strip() for p in text.split("---") if p.strip()]
        markdown = parts[0] if len(parts) > 0 else ""
        nutrition = ""
        suggestion = ""
        chart_data = [0, 0, 0, 0]
        if len(parts) > 1:
            for part in parts[1:]:
                if part.lower().startswith("nutrition:"):
                    nutrition = part.replace("Nutrition:", "").strip()
                elif part.lower().startswith("suggestion:"):
                    suggestion = part.replace("Suggestion:", "").strip()
        import re

        cal = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*kcal", nutrition, re.I)
        protein = re.search(
            r"([0-9]+(?:\.[0-9]+)?)\s*g\s*protein|protein:\s*([0-9]+(?:\.[0-9]+)?)\s*g",
            nutrition,
            re.I,
        )
        fiber = re.search(
            r"([0-9]+(?:\.[0-9]+)?)\s*g\s*fiber|fiber:\s*([0-9]+(?:\.[0-9]+)?)\s*g",
            nutrition,
            re.I,
        )
        vitA = re.search(
            r"([0-9]+(?:\.[0-9]+)?)\s*mg\s*vitamin\s*A|vitamin\s*A:\s*([0-9]+(?:\.[0-9]+)?)\s*mg",
            nutrition,
            re.I,
        )
        chart_data = [
            float(cal.group(1)) if cal else 0,
            float(protein.group(1) or protein.group(2)) if protein else 0,
            float(fiber.group(1) or fiber.group(2)) if fiber else 0,
            float(vitA.group(1) or vitA.group(2)) if vitA else 0,
        ]
        return markdown, nutrition, suggestion, chart_data, None
    except Exception as e:
        return "", "", "", [0, 0, 0, 0], str(e)


if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        init_db()
    app.run(debug=True)
