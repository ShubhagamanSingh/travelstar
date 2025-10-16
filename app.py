import streamlit as st # type: ignore
from huggingface_hub import InferenceClient # type: ignore
from pymongo import MongoClient # type: ignore
import hashlib
from datetime import datetime, timedelta
import json
import requests # type: ignore

# --- Configuration ---
st.set_page_config(
    page_title="Travelstar - AI Travel Planner",
    page_icon="✈️",
    layout="wide"
)

# --- Custom CSS for Modern Travel UI ---
st.markdown("""
<style>
    .main {
        background-color: black;
    }
    
    .header-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 3rem 2rem;
        border-radius: 0 0 25px 25px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    
    .custom-card {
        background: white;
        padding: 2rem;
        border-radius: 20px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        margin-bottom: 1.5rem;
        transition: all 0.3s ease;
    }
    
    .custom-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 30px rgba(0,0,0,0.12);
    }
    
    .feature-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        margin: 0.5rem;
    }
    
    .budget-card {
        background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
    }
    
    .day-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 15px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
    }
    
    .stButton button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        width: 100%;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
    }
    
    .stTextInput input, .stTextArea textarea, .stNumberInput input, .stSelectbox select {
        border-radius: 15px;
        border: 2px solid #e0e0e0;
        padding: 0.75rem;
        font-size: 1rem;
    }
    
    .stTextInput input:focus, .stTextArea textarea:focus, .stNumberInput input:focus, .stSelectbox select:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    .success-message {
        background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        margin-top: -5rem;
        margin-bottom: 2rem;
    }
    
    .info-message {
        background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        margin: 1rem 0;
    }
    
    .activity-item {
        background: rgb(14, 17, 23);
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 3px solid #667eea;
    }

</style>
""", unsafe_allow_html=True)


# --- User Authentication and Data Management ---
@st.cache_resource
def get_mongo_client():
    """Establishes a connection to MongoDB and returns the collection object."""
    try:
        MONGO_URI = st.secrets["MONGO_URI"]
        DB_NAME = st.secrets["DB_NAME"]
        COLLECTION_NAME = st.secrets["COLLECTION_NAME"]
        client = MongoClient(MONGO_URI)
        return client[DB_NAME][COLLECTION_NAME]
    except Exception as e:
        st.error(f"Failed to connect to MongoDB: {e}")
        st.stop()

users_collection = get_mongo_client()

def hash_password(password):
    """Hashes a password for storing."""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_password, provided_password):
    """Verifies a provided password against a stored hash."""
    return stored_password == hash_password(provided_password)

def add_to_history(username, destination, itinerary_data):
    """Adds a generated itinerary to the user's history."""
    history_entry = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "destination": destination,
        "itinerary": itinerary_data
    }
    users_collection.update_one(
        {"_id": username},
        {"$push": {"travel_history": {"$each": [history_entry], "$position": 0}}}
    )

# Hugging Face token
try:
    HF_TOKEN = st.secrets["HF_TOKEN"]
except FileNotFoundError:
    st.error("Streamlit secrets file not found. Please create a .streamlit/secrets.toml file with your HF_TOKEN.")
    st.stop()

client = InferenceClient("meta-llama/Meta-Llama-3-8B-Instruct", token=HF_TOKEN)

# --- Travel Planning System Prompts ---
TRAVEL_PROMPTS = {
    "itinerary_planner": """You are Travelstar, an expert AI travel planner specializing in creating personalized, budget-friendly itineraries for students and young travelers.

**CRITICAL FORMATTING REQUIREMENTS:**
You MUST format your response as valid JSON with this exact structure:

{{
  "itinerary_title": "Creative title for the itinerary",
  "total_budget": "Total estimated cost",
  "budget_breakdown": {{
    "accommodation": "cost",
    "food": "cost",
    "activities_and_shopping": "cost",
    "transportation": "cost",
    "miscellaneous": "cost"
  }},
  "travel_tips": ["tip1", "tip2", "tip3", "tip4", "tip5"],
  "daily_itinerary": {{
    "Day 1": {{
      "theme": "Day theme",
      "morning": {{"activity": "description", "cost": "amount", "duration": "time"}},
      "afternoon": {{"activity": "description", "cost": "amount", "duration": "time"}},
      "evening": {{"activity": "description", "cost": "amount", "duration": "time"}}
    }},
    "Day 2": {{
      "theme": "Day theme",
      "morning": {{"activity": "description", "cost": "amount", "duration": "time"}},
      "afternoon": {{"activity": "description", "cost": "amount", "duration": "time"}},
      "evening": {{"activity": "description", "cost": "amount", "duration": "time"}}
    }}
  }}
}}

**User Travel Preferences:**
Destination: {destination}
Duration: {duration} days
Budget: {budget}
Travel Style: {travel_style}
Interests: {interests}
Season: {season}
Group Size: {group_size}

Create a realistic, budget-friendly itinerary that maximizes experiences while minimizing costs. Focus on student-friendly accommodations, local food, and free/cheap activities.""",

    "budget_optimizer": """You are a travel budget optimization expert. Given a travel itinerary, suggest specific ways to reduce costs while maintaining quality.

Provide 5-7 concrete money-saving tips specific to this destination and itinerary.""",

    "packing_list": """Create a smart packing list for this trip considering:
- Destination: {destination}
- Duration: {duration} days  
- Season: {season}
- Activities: {interests}

Focus on essentials and multi-purpose items for budget travelers."""
}

# --- AI Helper Functions ---
@st.cache_data(show_spinner=False)
def generate_travel_response(system_prompt, user_prompt):
    """Generate AI response for travel planning"""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    response_text = ""
    try:
        for chunk in client.chat_completion(messages, max_tokens=2048, temperature=0.7, stream=True):
            if chunk.choices and chunk.choices[0].delta.content:
                response_text += chunk.choices[0].delta.content
    except Exception as e:
        st.error(f"An error occurred while communicating with the AI model: {e}")
        return None
        
    return response_text.strip()

def generate_itinerary(user_data):
    """Generate a complete travel itinerary"""
    prompt = TRAVEL_PROMPTS["itinerary_planner"].format(**user_data)
    
    response = generate_travel_response(
        "You are an expert travel planner. Always respond with valid JSON format.",
        prompt
    )
    
    try:
        # Extract JSON from response (in case there's extra text)
        start_idx = response.find('{')
        end_idx = response.rfind('}') + 1
        json_str = response[start_idx:end_idx]
        return json.loads(json_str)
    except:
        # If JSON parsing fails, return a structured error
        return {"error": "Failed to generate itinerary. Please try again."}

def get_weather_info(destination):
    """Get basic weather information (simulated)"""
    # In a real app, you'd integrate with a weather API
    seasons = {
        "summer": "☀️ Warm and sunny, perfect for outdoor activities",
        "winter": "❄️ Cooler temperatures, great for indoor attractions",
        "spring": "🌷 Mild weather with blooming flowers",
        "fall": "🍂 Comfortable temperatures with beautiful foliage"
    }
    return seasons.get("spring", "Pleasant travel weather")

# --- UI Components ---
def display_modern_header():
    """Display modern header with gradient"""
    st.markdown("""
    <div class="header-container">
        <h1 style="margin:0; font-size: 3rem; font-weight: 700;">✈️ Travelstar</h1>
        <p style="margin:0; font-size: 1.3rem; opacity: 0.9; margin-top: 0.5rem;">
        AI-Powered Travel Planning for Smart Explorers
        </p>
    </div>
    """, unsafe_allow_html=True)

def display_features():
    """Display feature cards"""
    st.markdown("### 🌟 Why Choose Travelstar?")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h3>💰 Budget-Friendly</h3>
            <p>Maximize experiences, minimize costs</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h3>🎯 Personalized</h3>
            <p>Tailored to your interests & style</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <h3>⏱️ Time-Saving</h3>
            <p>Instant AI-powered itineraries</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="feature-card">
            <h3>🌍 Local Insights</h3>
            <p>Discover hidden gems & local favorites</p>
        </div>
        """, unsafe_allow_html=True)

def display_travel_form():
    """Display the travel planning form"""
    st.markdown("""
    <div class="custom-card">
        <h2 style="color: #333; margin-bottom: 1.5rem; text-align: center;">🗺️ Plan Your Perfect Trip</h2>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        destination = st.text_input(
            "**Destination in India** 🇮🇳",
            placeholder="e.g., Goa, Manali, Kerala...",
            help="Where do you want to go?"
        )
        
        duration = st.slider(
            "**Trip Duration (Days)** 📅",
            min_value=1,
            max_value=30,
            value=5,
            help="How many days will you be traveling?"
        )
        
        budget = st.selectbox(
            "**Budget Range (INR)** 💰",
            ["Budget (₹10k - ₹25k)", "Moderate (₹25k - ₹75k)", "Luxury (₹75k+)"],
            help="Select your total trip budget range"
        )
    
    with col2:
        travel_style = st.selectbox(
            "**Travel Style** 🎭",
            ["Backpacker", "Cultural Explorer", "Foodie", "Adventure Seeker", "Relaxation", "City Breaker"],
            help="How do you like to travel?"
        )
        
        interests = st.multiselect(
            "**Interests** 🎯",
            ["History & Culture", "Food & Dining", "Nature & Hiking", "Art & Museums", 
             "Shopping", "Nightlife", "Beaches", "Photography", "Local Markets"],
            default=["History & Culture", "Food & Dining"],
            help="What activities interest you most?"
        )
        
        season = st.selectbox(
            "**Travel Season** 🌸",
            ["Spring", "Summer", "Fall", "Winter"],
            help="When are you planning to travel?"
        )
    
    group_size = st.selectbox(
        "**Travel Group** 👥",
        ["Solo Travel", "Couple", "Friends (3-5)", "Family", "Group (6+)"],
        help="Who are you traveling with?"
    )
    
    additional_notes = st.text_area(
        "**Additional Preferences** 📝",
        placeholder="Any specific requirements? (dietary restrictions, mobility issues, special interests...)",
        height=80
    )
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    return {
        "destination": destination,
        "duration": duration,
        "budget": budget,
        "travel_style": travel_style,
        "interests": ", ".join(interests),
        "season": season,
        "group_size": group_size,
        "additional_notes": additional_notes
    }

def display_itinerary_results(itinerary, user_data):
    """Display the generated itinerary in a beautiful format"""
    if "error" in itinerary:
        st.error("❌ Failed to generate itinerary. Please try again with different parameters.")
        return
    
    st.markdown(f"""
    <div class="success-message">
        <h2 style="margin:0; color: white;">🎉 Your {user_data['destination']} Itinerary is Ready!</h2>
        <p style="margin:0.5rem 0 0 0; opacity: 0.9;">{itinerary.get('itinerary_title', 'Your Personalized Travel Plan')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Budget Overview
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="budget-card">
            <h3 style="margin:0; font-size: 1.5rem;">💰 Total Budget</h3>
            <p style="margin:0; font-size: 2rem; font-weight: bold;">{itinerary.get('total_budget', 'N/A')}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="custom-card">
            <h4 style="margin:0; color: #333;">📅 Duration</h4>
            <p style="margin:0; font-size: 1.5rem; font-weight: bold; color: #667eea;">{user_data['duration']} days</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="custom-card">
            <h4 style="margin:0; color: #333;">🎯 Travel Style</h4>
            <p style="margin:0; font-size: 1.2rem; color: #667eea;">{user_data['travel_style']}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Budget Breakdown
    st.markdown("### 💵 Budget Breakdown")
    budget_data = itinerary.get('budget_breakdown', {})
    
    if budget_data:
        cols = st.columns(len(budget_data))
        for i, (category, amount) in enumerate(budget_data.items()): # type: ignore
            with cols[i]:
                st.metric(category.title(), amount)
    
    # Daily Itinerary
    st.markdown("### 🗓️ Daily Itinerary")
    daily_itinerary = itinerary.get('daily_itinerary', {})
    
    for day, activities in daily_itinerary.items():
        with st.expander(f"{day}: {activities.get('theme', 'Daily Activities')}", expanded=True):
            col1, col2, col3 = st.columns(3)
            
            time_slots = {
                "Morning": activities.get('morning', {}),
                "Afternoon": activities.get('afternoon', {}),
                "Evening": activities.get('evening', {})
            }
            
            for time_slot, (title, details) in zip(["🌅 Morning", "☀️ Afternoon", "🌙 Evening"], time_slots.items()):
                with [col1, col2, col3][list(time_slots.keys()).index(title)]:
                    st.markdown(f"**{time_slot}**")
                    if details:
                        st.markdown(f"""
                        <div class="activity-item">
                            <strong>{details.get('activity', 'Activity')}</strong><br>
                            ⏱️ {details.get('duration', '2-3 hours')}<br>
                            💰 {details.get('cost', 'Free')}
                        </div>
                        """, unsafe_allow_html=True)
    
    # Travel Tips
    st.markdown("### 💡 Travel Tips")
    tips = itinerary.get('travel_tips', [])
    
    for i, tip in enumerate(tips, 1):
        st.info(f"{i}. {tip}")
    
    # Packing List
    st.markdown("### 🎒 Smart Packing Suggestions")
    with st.spinner("Generating packing list..."):
        packing_prompt = TRAVEL_PROMPTS["packing_list"].format(**user_data)
        packing_list = generate_travel_response(
            "You are a travel packing expert. Provide concise, practical packing advice.",
            packing_prompt
        )
        
        if packing_list:
            st.markdown(packing_list)

def display_modern_auth():
    """Display modern authentication in sidebar"""
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem;">
            <h2 style="color: #667eea; margin: 0;">Travelstar</h2>
            <p style="color: #666; margin: 0;">AI Travel Planner</p>
        </div>
        """, unsafe_allow_html=True)
        
        if not st.session_state.get('logged_in', False):
            tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])
            
            with tab1:
                username = st.text_input("Username", key="login_user")
                password = st.text_input("Password", type="password", key="login_pass")
                
                if st.button("Login", use_container_width=True):
                    if username and password:
                        user_data = users_collection.find_one({"_id": username})
                        if user_data and verify_password(user_data["password"], password):
                            st.session_state.logged_in = True
                            st.session_state.username = username
                            st.rerun()
                        else:
                            st.error("Invalid username or password")
                    else:
                        st.warning("Please enter username and password")
            
            with tab2:
                username = st.text_input("Username", key="reg_user")
                password = st.text_input("Password", type="password", key="reg_pass")
                confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm")
                
                if st.button("Register", use_container_width=True):
                    if username and password:
                        if password == confirm_password:
                            if users_collection.find_one({"_id": username}):
                                st.error("Username already exists")
                            else:
                                users_collection.insert_one({
                                    "_id": username,
                                    "password": hash_password(password),
                                    "travel_history": []
                                })
                                st.success("Registration successful! Please login.")
                        else:
                            st.error("Passwords do not match")
                    else:
                        st.warning("Please fill all fields")
        else:
            st.markdown(f"""
            <div class="custom-card">
                <h4 style="color: #667eea; margin: 0;">Welcome back!</h4>
                <p style="margin: 0.5rem 0; color: #666;">{st.session_state.username}</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Logout", use_container_width=True):
                st.session_state.logged_in = False
                st.session_state.username = ""
                st.rerun()

def display_travel_history():
    """Display user's travel history"""
    st.markdown("""
    <div class="custom-card">
        <h2 style="color: #333; text-align: center; margin-bottom: 2rem;">📚 Your Travel History</h2>
    """, unsafe_allow_html=True)
    
    user_data = users_collection.find_one({"_id": st.session_state.username})
    travel_history = user_data.get("travel_history", []) if user_data else []

    if not travel_history:
        st.markdown("""
        <div style="text-align: center; padding: 3rem;">
            <h3 style="color: #666;">No travel plans yet</h3>
            <p>Your amazing travel itineraries will appear here!</p>
            <div style="font-size: 4rem;">✈️</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for i, entry in enumerate(travel_history):
            with st.expander(f"🚞 {entry['destination']} - {entry['date']}", expanded=(i==0)):
                if 'itinerary' in entry:
                    itinerary = entry['itinerary']
                    st.markdown(f"### {itinerary.get('itinerary_title', 'Your Travel Plan')}")

                    # Budget Overview
                    st.metric("💰 Total Budget", itinerary.get('total_budget', 'N/A'))

                    # Budget Breakdown
                    st.markdown("<h5>💵 Budget Breakdown</h5>", unsafe_allow_html=True)
                    budget_data = itinerary.get('budget_breakdown', {})
                    if budget_data:
                        cols = st.columns(len(budget_data))
                        for j, (category, amount) in enumerate(budget_data.items()):
                            with cols[j]:
                                st.metric(category.title(), amount)

                    # Daily Itinerary
                    st.markdown("<h5>🗓️ Daily Itinerary</h5>", unsafe_allow_html=True)
                    daily_itinerary = itinerary.get('daily_itinerary', {})
                    for day, activities in daily_itinerary.items():
                        st.markdown(f"**{day}: {activities.get('theme', 'Daily Activities')}**")
                        time_slots = {
                            "Morning": activities.get('morning', {}),
                            "Afternoon": activities.get('afternoon', {}),
                            "Evening": activities.get('evening', {})
                        }
                        for time_slot, details in time_slots.items():
                            if details:
                                st.markdown(f"- **{time_slot}:** {details.get('activity', 'Activity')} ({details.get('cost', 'Free')})")

                    # Travel Tips
                    st.markdown("<h5>💡 Travel Tips</h5>", unsafe_allow_html=True)
                    tips = itinerary.get('travel_tips', [])
                    for tip in tips:
                        st.markdown(f"- {tip}")
    
    st.markdown("</div>", unsafe_allow_html=True)

# --- Main App Interface ---
display_modern_header()

# --- Authentication ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

display_modern_auth()

if not st.session_state.logged_in:
    # Welcome screen for non-logged in users
    st.markdown("""
    <div class="custom-card">
        <h2 style="text-align: center; color: #333; margin-bottom: 2rem;">Welcome to Travelstar! 🌍</h2>
        <p style="text-align: center; font-size: 1.2rem; color: #666; line-height: 1.6;">
        Say goodbye to stressful trip planning! Our AI-powered travel planner creates personalized, 
        budget-friendly itineraries tailored to your interests and travel style.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    display_features()
    
    st.markdown("""
    <div class="info-message">
        <p style="margin: 0; font-size: 1.1rem;">
        👈 <strong>Start Planning:</strong> Please login or register in the sidebar to create your first itinerary!
        </p>
    </div>
    """, unsafe_allow_html=True)

# --- Main Application ---
if st.session_state.logged_in:
    # --- Main Application Tabs ---
    tab1, tab2, tab3 = st.tabs(["🗺️ Plan Trip", "📚 My Trips", "💡 Travel Tips"])

    with tab1:
        display_features()
        user_data = display_travel_form()
        
        if st.button("🚀 Generate My Travel Plan", use_container_width=True):
            if not user_data['destination']:
                st.error("📍 Please enter a destination to continue")
            else:
                with st.spinner("🧠 AI is crafting your perfect itinerary... This may take a moment."):
                    # Get weather info
                    weather_info = get_weather_info(user_data['destination'])
                    
                    # Generate itinerary
                    itinerary = generate_itinerary(user_data)
                    
                    if itinerary and "error" not in itinerary:
                        # Display results
                        display_itinerary_results(itinerary, user_data)
                        
                        # Save to history
                        add_to_history(
                            st.session_state.username,
                            user_data['destination'],
                            itinerary
                        )
                        
                        # Weather information
                        st.markdown("### 🌤️ Travel Weather")
                        st.info(f"**{user_data['season']} in {user_data['destination']}:** {weather_info}")

    with tab2:
        display_travel_history()

    with tab3:
        st.markdown("""
        <div class="custom-card">
            <h2 style="color: #333; text-align: center; margin-bottom: 2rem;">💡 Smart Travel Tips</h2>
        """, unsafe_allow_html=True)
        
        tips_col1, tips_col2 = st.columns(2)
        
        with tips_col1:
            st.markdown("### 💰 Budget Travel Tips")
            st.info("""**1. Travel by Train**
- Indian Railways is extensive and budget-friendly for long distances.
- Book tickets in advance on IRCTC, especially for popular routes.
            
**2. Stay in Hostels**
- Use hostel chains like Zostel, The Hosteller, or goStops for affordable and social stays.
- Great for solo travelers and small groups.
            
**3. Eat Local & Street Food**
- Avoid expensive tourist restaurants.
- Explore local dhabas and street food stalls for authentic and cheap meals.
            """)
            
            st.markdown("### 🎒 Packing Smart")
            st.info("""**1. Pack for the Climate**
- India has diverse climates. Pack light cottons for the south and layers for the north.
- Always carry a scarf or stole for covering up at religious sites.
            
**2. Essentials Kit**
- Include hand sanitizer, wet wipes, basic medicines, and a reusable water bottle.
- A power bank is a must-have.
            
**3. Comfortable Footwear**
- You'll be doing a lot of walking.
- Pack sturdy sandals or walking shoes.
            """)
        
        with tips_col2:
            st.markdown("### 🌍 Cultural Tips")
            st.info("""**1. Dress Modestly**
- Especially when visiting temples, mosques, or rural areas.
- Covering shoulders and knees is a good practice.
            
**2. Bargain Respectfully**
- Bargaining is common at local markets, but do it with a smile.
- Have a price in mind and be prepared to walk away.
            
**3. Ask Before Photographing People**
- It's polite to ask for permission before taking close-up photos of people.
- Be respectful of their privacy.
            """)
            
            st.markdown("### 📱 Tech Tips")
            st.info("""**1. Get a Local SIM Card**
- Airtel, Jio, and Vi offer cheap data plans for tourists.
- You'll need your passport and visa for registration.
            
**2. Use UPI for Payments**
- Digital payments via UPI (Paytm, Google Pay, PhonePe) are widely accepted.
- Link your bank account for easy, cashless transactions.
            
**3. Use Ride-Hailing Apps**
- Uber and Ola are available in most major cities.
- Auto-rickshaws can also be booked through these apps for fair prices.
            """)
        
        st.markdown("</div>", unsafe_allow_html=True)