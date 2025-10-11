# ✈️ Travelstar - AI Travel Planner

This Streamlit application is **Travelstar**, an AI-powered travel planner designed to help students and young travelers create personalized, budget-friendly itineraries. Say goodbye to stressful planning and hello to smart, seamless adventures.

## ✨ Features

- **AI Itinerary Generation**: Creates detailed, day-by-day travel plans based on your destination, duration, budget, and interests.
- **Budget Planning**: Provides an estimated total budget and a breakdown for accommodation, food, activities, and more.
- **Smart Travel Tips**: Get AI-generated tips specific to your destination to save money and travel smarter.
- **Packing List Generator**: Automatically creates a packing list tailored to your trip's season, duration, and activities.
- **User Authentication**: Secure login and registration system for a personalized experience.
- **Personalized Trip History**: Keeps a log of all your generated itineraries, allowing you to review past travel plans.
- **AI-Powered**: Utilizes a powerful language model (Llama 3) from Hugging Face to provide intelligent and helpful responses.
- **Secure & Private**: Uses Streamlit's secrets management for API tokens and database credentials, and stores user data securely in MongoDB.

## 🚀 Setup and Installation Guide

Follow these steps to get the application running on your local machine.

### Step 1: Get Your API Keys and Credentials

You will need three things:
1.  **Hugging Face API Token**: To access the AI model.
2.  **MongoDB Connection URI**: To store user data and history.
3.  **Database and Collection Names**: To specify where to store the data in MongoDB.

*   **Hugging Face API Token**:
    1.  Go to the Hugging Face website: huggingface.co
    2.  Navigate to **Settings** -> **Access Tokens** and create a new token with `read` permissions.
    3.  Copy the generated token (`hf_...`).

*   **MongoDB URI**:
    1.  Create a free cluster on MongoDB Atlas.
    2.  Once your cluster is set up, go to **Database** -> **Connect** -> **Drivers**.
    3.  Select Python and copy the connection string (URI). Remember to replace `<password>` with your database user's password.
    4.  You will also need to name your database and collection (e.g., `travelstar_db`, `users`).

### Step 2: Create the Secrets File

Streamlit uses a `.streamlit/secrets.toml` file to store sensitive information like API keys.

1.  In your project's root directory (`travelstar/`), create a new folder named `.streamlit`.
2.  Inside the `.streamlit` folder, create a new file named `secrets.toml`.
3.  Add your credentials to this file as shown below:

    ```toml
    # .streamlit/secrets.toml
    HF_TOKEN = "hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    MONGO_URI = "mongodb+srv://<username>:<password>@your_cluster_url/?retryWrites=true&w=majority"
    DB_NAME = "your_database_name"
    COLLECTION_NAME = "your_collection_name"
    ```
    *Replace the placeholder values with your actual credentials.*

### Step 3: Install Required Packages

Open your terminal or command prompt, navigate to the project's root directory (`travelstar/`), and run the following command to install the required Python packages from `requirements.txt`:

```bash
pip install -r requirements.txt
```

### Step 4: Run the Streamlit App

Once the installation is complete, run the following command in your terminal:

```bash
streamlit run app.py
```

Your web browser should automatically open with the application running!

## 📁 Project Structure
study_buddy/
├── .streamlit/
│   └── secrets.toml
├── app.py
├── requirements.txt
└── README.md
