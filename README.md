# 🍲 ManjeAI: Smart Cooking Assistant for Food-Insecure Regions

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

ManjeAI is an AI-powered web app designed to help users in food-insecure regions (like Haiti) create nutritious, low-cost recipes using only the ingredients they have on hand. It leverages Google Gemini and LogMeal APIs to suggest recipes, estimate nutrition, and recommend affordable, local foods to balance meals.

---

## 🚀 Features

- 📝 **Recipe Generation**: Enter ingredients (or upload a food image) to get a full Markdown recipe with step-by-step instructions and emojis.
- 📸 **Image Ingredient Detection**: Upload a photo of your food, and ManjeAI will detect ingredients using LogMeal.
- 🥗 **Nutrition Estimation**: Get calories, protein, fiber, and vitamin A estimates for each recipe.
- 💡 **Smart Suggestions**: Receive context-aware suggestions for missing nutrients using local, affordable foods.
- 🌍 **Multilingual**: Supports English and Haitian Creole.
- 🕑 **History**: View and revisit your previously generated recipes.

---

## 🛠️ Installation

1. **Clone the repo:**
   ```bash
   git clone https://github.com/ZephyrusBlaze/ManjeAI.git
   cd ManjeAI
   ```
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Set up environment variables:**
   - Create a `.env` file with your API keys:
     ```env
     GEMINI_API_KEY=your_gemini_api_key
     LOGMEAL_API_KEY=your_logmeal_api_key
     ```
4. **Initialize the database:**
   ```bash
   python app.py  # The app will auto-create the DB if missing
   ```
5. **Run the app:**
   ```bash
   python app.py
   ```
   Visit [http://localhost:5000](http://localhost:5000) in your browser.

---

## 📂 Project Structure

```
ManjeAI/
├── app.py            # Main Flask app
├── history.db        # SQLite database
├── schema.sql        # DB schema
├── templates/        # HTML templates
├── .env              # API keys (not committed)
├── LICENSE
└── README.md
```

---

## 🔑 API Keys
- **Google Gemini**: [Get your API key](https://ai.google.dev/)
- **LogMeal**: [Get your API key](https://logmeal.com/)

---

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

---

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgements
- [Google Gemini](https://ai.google.dev/)
- [LogMeal](https://logmeal.com/)
- [Flask](https://flask.palletsprojects.com/)

---

## 🌱 Made with ❤️ for food security and community resilience.
