import streamlit as st
from google_play_scraper import search, reviews, Sort
import pandas as pd

# Cached function to fetch app search results
@st.cache_data
def fetch_app_options(app_name, max_results=100):
    results = search(app_name, lang="en", country="us", n_hits=max_results)
    return [{"name": app['title'], "app_id": app['appId']} for app in results]

# Function to fetch app reviews
def fetch_reviews(app_id, country='US', num_reviews=100):
    try:
        progress = st.progress(0)
        reviews_data, _ = reviews(
            app_id,
            lang='en',
            country=country,
            count=num_reviews,
            sort=Sort.NEWEST
        )
        progress.progress(100)  # Update progress to 100% when done
        return reviews_data
    except Exception as e:
        st.error(f"Error fetching reviews: {e}")
        return []

# Function to save reviews to a CSV file
def save_reviews_to_csv(reviews_data):
    reviews_list = []
    for review in reviews_data:
        reviews_list.append({
            'Date': review['at'].strftime("%d/%m/%y"),
            'Review': review['content'],
            'Rating': review['score'],
            'Response_date': review['repliedAt'].strftime("%d/%m/%y") if review['repliedAt'] else None,
            'Response': review['replyContent'] if review['replyContent'] else None
        })

    df = pd.DataFrame(reviews_list)
    return df.to_csv(index=False)

# Streamlit app layout
st.title("Google Play Store App Review Fetcher")

# Step 1: User enters the app name
app_name = st.text_input("Enter the app name from Google Play Store:")

# Add country selection
country = st.selectbox("Select a country:", ["US", "IN", "GB", "CA", "AU"])

# Add dynamic review count selection
num_reviews = st.slider("Number of reviews to fetch:", min_value=10, max_value=200, step=10)

# Search and display options for app selection
if app_name:
    st.write("Searching for apps...")
    apps = fetch_app_options(app_name)
    if apps:
        selected_app = st.selectbox("Select an app:", [f"{app['name']} (ID: {app['app_id']})" for app in apps])

        if selected_app:
            # Extract the selected app's ID
            selected_app_id = selected_app.split("(ID: ")[-1][:-1]  # Parse app ID from choice

            # Step 2: Fetch and display reviews on button click
            if st.button("Fetch Reviews"):
                st.write(f"Fetching reviews for {selected_app}...")

                # Fetch reviews with progress
                reviews_data = fetch_reviews(selected_app_id, country=country, num_reviews=num_reviews)

                if reviews_data:
                    # Step 3: Display the reviews in a DataFrame
                    st.write("Sample Reviews:")
                    df = pd.DataFrame([
                        {
                            'Date': review['at'].strftime("%d/%m/%y"),
                            'Review': review['content'],
                            'Rating': review['score'],
                            'Response': review['replyContent'] if review['replyContent'] else None
                        }
                        for review in reviews_data
                    ])
                    st.write(df.head())

                    # Save to CSV and provide download link
                    csv_data = save_reviews_to_csv(reviews_data)
                    st.download_button(
                        label="Download reviews as CSV",
                        data=csv_data,
                        file_name=f"{selected_app_id}_reviews.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("No reviews found.")
    else:
        st.warning("No matching apps found. Please refine your search.")
