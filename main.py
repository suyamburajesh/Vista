
import streamlit as st
import json
import time
import csv


def load_database(json_file):
    try:
        with open(json_file, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        st.error("❌ Database file not found!")
        return {}
    except json.JSONDecodeError:
        st.error("❌ Error loading JSON data!")
        return {}

# Show available departments
def show_options(database):
    if "department" not in database:
        return ["SELECT"]
    return ["SELECT"] + list(database["department"].keys())

# Find nearest cutoff match
def find_nearest_cutoff(available_cutoffs, user_cutoff):
    if not available_cutoffs:
        return None
    return min(available_cutoffs, key=lambda x: abs(x - user_cutoff))

# Recommend Colleges
def recommend_colleges(database, department, community, cutoff):
    if department == "SELECT" or community == "SELECT":
        return ["❌ Please select valid options."]

    if "department" in database:
        database = database["department"]

    dept_key = next((key for key in database.keys() if department.lower() in key.lower()), None)
    if not dept_key:
        return [f"❌ Invalid Department! Available: {', '.join(database.keys())}"]

    comm_key = next((key for key in database[dept_key].keys() if community.lower() in key.lower()), None)
    if not comm_key:
        return [f"❌ Invalid Community! Available for {dept_key}: {', '.join(database[dept_key].keys())}"]

    available_cutoffs = sorted(map(float, database[dept_key][comm_key].keys()))

    min_cutoff = cutoff - 1
    max_cutoff = cutoff + 1
    recommended_colleges = []

    for cutoff_value in available_cutoffs:
        if min_cutoff <= cutoff_value <= max_cutoff:
            recommended_colleges.extend(database[dept_key][comm_key][str(cutoff_value)])
        
        if len(recommended_colleges) >= 5:
            return recommended_colleges[:5]

    while len(recommended_colleges) < 5:
        nearest_cutoff = find_nearest_cutoff(available_cutoffs, cutoff)
        if nearest_cutoff is None:
            break

        additional_colleges = database[dept_key][comm_key][str(nearest_cutoff)]
        for college in additional_colleges:
            if len(recommended_colleges) < 5:
                recommended_colleges.append(college)
            else:
                break

        available_cutoffs.remove(nearest_cutoff)

    return recommended_colleges if recommended_colleges else ["❌ No colleges found."]

# Load JSON data
json_file = "combined.json"
database = load_database(json_file)

# Custom Styling
st.markdown("""
    <style>
        h1 { text-align: center; font-size: 40px; font-weight: bold; color: #2c3e50; animation: fadeIn 2s; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
        .fadeIn { animation: fadeIn 1.5s; }
        .stButton>button {
            background: linear-gradient(to right, #6a11cb, #2575fc);
            color: white; border: none; font-size: 16px;
            padding: 8px 12px; border-radius: 5px;
            transition: all 0.3s ease-in-out;
        }
        .stButton>button:hover { transform: scale(1.05); background: linear-gradient(to right, #2575fc, #6a11cb); }
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="fadeIn">🎓VISTA Virtual Intelligent System For TNEA Admissions</h1>', unsafe_allow_html=True)
st.write("🚀 Find the best colleges based on your cutoff!")

# Input Fields
col1, col2 = st.columns(2)

with col1:
    application_no = st.text_input("📄 Application Number", value="")  
    name = st.text_input("👤 Full Name", value="")  
    email = st.text_input("📧 Email Address", value="")  
    district = st.text_input("🏙️ District", value="")  

with col2:
    phone = st.text_input("📞 Phone Number", value="")  
    rank_no = st.number_input("🏅 Rank Number", min_value=1, step=1, value=1)  
    cutoff_marks = st.number_input("📊 Enter Your Cutoff Mark", min_value=0.0, max_value=200.0, step=0.1, value=0.0)  

# Department & Community Selection
departments = show_options(database)
selected_department = st.selectbox("🏛️ Select Department", departments, index=0)

if selected_department and selected_department != "SELECT":
    communities = ["SELECT"] + list(database["department"][selected_department].keys())
    selected_community = st.selectbox("🌍 Select Community", communities, index=0)
else:
    selected_community = "SELECT"

# Submit and Reset Buttons
col1, col2 = st.columns(2)
with col1:
    submit = st.button("✅ Submit")
with col2:
    reset = st.button("🔄 Reset")

# Reset Functionality
if reset:
    st.experimental_rerun()

# Submit Button Logic
if submit:
    with st.spinner("🔄 LLM Processing..."):
        time.sleep(2)  

    errors = []
    
    if not name.strip():
        errors.append("❌ Full Name is required.")
    if not email.strip() or "@" not in email:
        errors.append("❌ Valid Email Address is required.")
    if not phone.strip() or len(phone) != 10 or not phone.isdigit():
        errors.append("❌ Valid 10-digit Phone Number is required.")
    if selected_department == "SELECT":
        errors.append("❌ Please select a Department.")
    if selected_community == "SELECT":
        errors.append("❌ Please select a Community.")

    if errors:
        for error in errors:
            st.error(error)
    else:
        # Save data to CSV
        application_data = {
            "application_no": application_no,
            "name": name,
            "email": email,
            "district": district,
            "phone": phone,
            "rank_no": rank_no,
            "cutoff_marks": cutoff_marks,
            "department": selected_department,
            "community": selected_community
        }

        # Define the CSV file path
        csv_file = 'applications_data.csv'

        # Check if the CSV file exists, if not, create it with headers
        file_exists = False
        try:
            with open(csv_file, mode='r'):
                file_exists = True
        except FileNotFoundError:
            file_exists = False

        # Append data to CSV or create file with headers if it doesn't exist
        with open(csv_file, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=application_data.keys())

            # If the file doesn't exist, write headers
            if not file_exists:
                writer.writeheader()

            # Write the application data
            writer.writerow(application_data)

        # 🎈🎊 Success Animation
        #st.balloons()  
        time.sleep(1)
        st.markdown('<h2 class="fadeIn">🎯 Recommended Colleges:</h2>', unsafe_allow_html=True)

        colleges = recommend_colleges(database, selected_department, selected_community, cutoff_marks)
        for college in colleges:
            st.success(f"🏫 {college}")

        # Add a download button for the CSV file
        with open(csv_file, "rb") as f:
            st.download_button(
                label="Download CSV",
                data=f,
                file_name=csv_file,
                mime="text/csv"
            )
