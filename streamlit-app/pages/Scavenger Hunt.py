import streamlit as st
import pandas as pd
import os
import random
from PIL import Image

# Constants
UPLOAD_DIR = "SH_uploads"
LEADERBOARD_FILE = "leaderboard.csv"

# Create necessary directories
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Movember Bingo Tasks
tasks = [
    "Photo with a sausage roll",
    "Strava/ some proof of a 5k walk",
    "Photo with a coffee shop",
    "Photo where you can see a pond",
    "Log 10,000+ steps in any one day",
    "Photo with either sunrise or sunset",
    "Log a walk or other form of exercise with a colleague",
    "Take part in Movember / donate to a colleague who is",
    "Hot chocolate/hot drink with a film",
    "Photo of a book you're reading",
    "Photo by the beach",
    "Photo in local park/ green space",
    "Photo of activity with family/friends",
    "Do a good deed and write what it is",
    "Photo in comfies e.g. blanket/ oodie",
    "Photo of a local landmark"
]

# Assign points to each task in increments of 5
task_points = {task: (i + 1) * 5 for i, task in enumerate(tasks)}

# Page config
st.set_page_config(page_title="Move it Movember Scavenger Challenge", layout="wide")

import streamlit as st

# Add cohort verification checkbox
st.markdown("### This scavenger hunt is only for the Newcastle 2025 DXC Academic cohort.")
is_cohort_member = st.checkbox("Please tick this box if you are part of this cohort")

# If not checked, show redirect button
if not is_cohort_member:
    if st.button("I'm not part of this cohort"):
        st.markdown('<meta http-equiv="refresh" content="0;URL=/?page=home">', unsafe_allow_html=True)
    st.stop()

# If checked, continue with the rest of the app
# (The rest of the original app code should follow here)
# Main content
st.title("🕵️ Move it Movember Scavenger Challenge")

# Name input and normalization
full_name = st.text_input("Enter your full name to track your progress:")
normalized_name = full_name.strip().lower().replace(" ", "_") if full_name else "anonymous"

# Evidence uploader
st.subheader("📤 Submit Your Evidence")
selected_task = st.selectbox("Choose a challenge to submit evidence for:", tasks)
uploaded_file = st.file_uploader("Upload your photo evidence", type=["jpg", "jpeg", "png"])

# Load or initialize leaderboard
try:
    if os.path.exists(LEADERBOARD_FILE):
        leaderboard_df = pd.read_csv(LEADERBOARD_FILE)
        if "name" not in leaderboard_df.columns or "points" not in leaderboard_df.columns:
            leaderboard_df = pd.DataFrame(columns=["name", "points"])
    else:
        leaderboard_df = pd.DataFrame(columns=["name", "points"])
except Exception as e:
    st.error(f"Error loading leaderboard: {e}")
    leaderboard_df = pd.DataFrame(columns=["name", "points"])

# Handle submission
if uploaded_file and selected_task and full_name:
    task_index = tasks.index(selected_task) + 1
    file_extension = uploaded_file.name.split('.')[-1]
    filename = f"{normalized_name}_task_{task_index}.{file_extension}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    # Save file
    with open(filepath, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Update leaderboard
    completed_tasks = leaderboard_df[leaderboard_df["name"] == normalized_name]
    existing_points = int(completed_tasks["points"].values[0]) if not completed_tasks.empty else 0
    new_points = existing_points + task_points[selected_task]

    leaderboard_df = leaderboard_df[leaderboard_df["name"] != normalized_name]
    leaderboard_df = pd.concat([leaderboard_df, pd.DataFrame([[normalized_name, new_points]], columns=["name", "points"])], ignore_index=True)

    try:
        leaderboard_df.to_csv(LEADERBOARD_FILE, index=False)
    except PermissionError:
        st.error("Permission denied: Unable to write to leaderboard.csv. Please check file permissions.")

    st.success("🎉 Evidence uploaded! Task marked as complete.")
    st.toast(random.choice([
        "🥴 That moustache is working overtime!",
        "💪 You're crushing it like a Movember legend!",
        "📸 That photo deserves a gallery spot in the Louvre!",
        "🔥 You're hotter than a hot chocolate in November!"
    ]))

# Leaderboard display
if not leaderboard_df.empty and "name" in leaderboard_df.columns and "points" in leaderboard_df.columns:
    st.subheader("🏆 Leaderboard")
    sorted_df = leaderboard_df.sort_values(by="points", ascending=False)
    st.dataframe(sorted_df)

# Calculate progress
user_submissions = [f for f in os.listdir(UPLOAD_DIR) if f.startswith(normalized_name + "_task_")]
tasks_completed = len(user_submissions)
total_tasks = len(tasks)
progress = tasks_completed / total_tasks

# Show progress bar
st.subheader("📊 Your Progress")
st.progress(progress)
st.write(f"You've completed {tasks_completed} out of {total_tasks} tasks.")


# Gallery of all submissions
st.subheader("🖼️ Scavenger Gallery")
all_images = [f for f in os.listdir(UPLOAD_DIR) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
if all_images:
    grouped = {}
    for img in all_images:
        prefix = img.split("_task_")[0]
        grouped.setdefault(prefix, []).append(img)

    for user, images in grouped.items():
        st.markdown(f"### {user.replace('_', ' ').title()}")
        for i in range(0, len(images), 4):
            cols = st.columns(4)
            for j in range(4):
                if i + j < len(images):
                    img_path = os.path.join(UPLOAD_DIR, images[i + j])
                    with cols[j]:
                        st.image(Image.open(img_path), caption=images[i + j], use_container_width=True)
else:
    st.info("No submissions yet! Be the first to moustache your way to victory!")