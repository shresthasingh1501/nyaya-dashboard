import streamlit as st
import google.generativeai as genai
import google.ai.generativelanguage as glm
import time
import csv
from PIL import Image

API_KEY = 'AIzaSyAv7RXj23iVkQ6ZMjbTLLu5v1-_J1v09vY'
genai.configure(api_key=API_KEY)

# Dropdown options for project status
options = {
    0: "0% empty plot of land with no signs of construction.",
    5: "5% visible foundations or footings.",
    10: "10% raised foundations to the plinth level.",
    20: "20% completed lintel or beam structure.",
    40: "40% roof structure in place.",
    70: "70% visible flooring and plastering inside the structure.",
    90: "90% all external finishes and electrical installations.",
    100: "100% Completed building ready for handover"
}

def validate_lat_lng(lat, lng):
    try:
        lat = float(lat)
        lng = float(lng)
        if -90 <= lat <= 90 and -180 <= lng <= 180:
            return True, lat, lng
        else:
            return False, "Invalid latitude or longitude values.", None
    except ValueError:
        return False, "Latitude and longitude must be numbers.", None

def analyze_project(image, project_name, project_description, project_status):
    bytes_data = image.getvalue()

    prompt1 = f"""
    You are a construction image validation system by the Government of India whose work is to validate the Statements 1. Project Description and 2. Project Completion 
    with the picture provided of the construction
this is your rulebook for status verification
    0: "0% empty plot of land with no signs of construction.",
    5: "5% visible foundations or footings.",
    10: "10% raised foundations to the plinth level.",
    20: "20% completed lintel or beam structure.",
    40: "40% roof structure in place.",
    70: "70% visible flooring and plastering inside the structure.",
    90: "90% all external finishes and electrical installations.",
    100: "100% Completed building ready for handover"

    if the status provided by user doesnt match the picture (irrelevant pictures or under initial construction but claimed as completed by user) - return with 0 which means their statement is wrong 

    But if the project status matches the photo then you can return with 1 which means their statement is true

    so for this project in the picture has been reported to be at {project_status}% what is your verification status (only one single digit is allowed as your output no text description at any cost) 
    """

    model = genai.GenerativeModel('gemini-1.5-flash')
    response1 = model.generate_content(
        glm.Content(
            parts=[
                glm.Part(text=prompt1),
                glm.Part(
                    inline_data=glm.Blob(
                        mime_type='image/jpeg',
                        data=bytes_data
                    )
                ),
            ],
        ),
    )
    response1.resolve()
    answer1 = response1.text

    time.sleep(20)  # Wait for 20 seconds to avoid rate limiting

    prompt2 = f"""
    You are a reasoning system for construction image validation system by the Government of India whose work is to validate the verification done by the validation system using 20 words only and with the picture provided of the construction 
this is your rulebook for status verification
    0: "0% empty plot of land with no signs of construction.",
    5: "5% visible foundations or footings.",
    10: "10% raised foundations to the plinth level.",
    20: "20% completed lintel or beam structure.",
    40: "40% roof structure in place.",
    70: "70% visible flooring and plastering inside the structure.",
    90: "90% all external finishes and electrical installations.",
    100: "100% Completed building ready for handover"

    if the status provided by user doesnt match the picture (irrelevant pictures or under initial construction but claimed as completed by user) - validation system returns with 0 which means their statement is wrong 

    But if the project status matches the photo then validation system returns with 1 which means their statement is true
    with the picture provided of the construction, be very lenient and you can assume thing 
    so for this project name - {project_name}, with description - {project_description} has been reported to be at {project_status}% and
    for this picture of the project validation system had answered with {answer1} (1 means verified , 0 means not verified) to the overall verification, give reasoning in plain text 
    """

    response2 = model.generate_content(
        glm.Content(
            parts=[
                glm.Part(text=prompt2),
                glm.Part(
                    inline_data=glm.Blob(
                        mime_type='image/jpeg',
                        data=bytes_data
                    )
                ),
            ],
        ),
    )
    response2.resolve()

    return {"Check": answer1, "Reasoning": response2.text}

# Streamlit App
st.title("Construction Image Validation System")

project_name = st.text_input("Project Name")
project_description = st.text_area("Project Description")
lat = st.text_input("Latitude")
lng = st.text_input("Longitude")
project_status = st.selectbox("Project Status", options.keys(), format_func=lambda x: options[x])

uploaded_file = st.file_uploader("Choose an Image file", accept_multiple_files=False, type=['jpg', 'png'])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption='Uploaded Image', use_column_width=True)

generate = st.button("Review Project")

if generate:
    valid, lat, lng = validate_lat_lng(lat, lng)
    if not valid:
        st.error(lat)
    else:
        analysis = analyze_project(uploaded_file, project_name, project_description, project_status)
        if 'Error' in analysis:
            st.error(analysis['Error'])
        else:
            st.write(f"AI Review: {analysis['Check']}")
            st.write(f"AI Reasoning: {analysis['Reasoning']}")

            # Save data to CSV
            data = {
                "project_name": project_name,
                "project_status": project_status,
                "project_description": project_description,
                "ai_review": analysis['Check'],
                "ai_reason": analysis['Reasoning'],
                "latitude": lat,
                "longitude": lng,
                "image_path": uploaded_file.name
            }

            with open('map.csv', mode='a', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=data.keys())
                writer.writerow(data)

            st.success("Data saved to CSV file.")

