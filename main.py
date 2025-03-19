import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import re

from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory
from google_play_scraper import reviews, Sort
# Initialize Sastrawi stopword remover
factory = StopWordRemoverFactory()
stopwords_id = set(factory.get_stop_words())

# English stopwords
stopwords_en = {"and", "or", "but", "the", "this", "that", "a", "an", "to", "in", "of", "on", "for", "with", "at", "by", "from", "as", "is", "are", "was", "were", "be", "been", "have", "has", "had", "do", "does", "did", "not", "no", "yes", "it", "you", "we", "they", "he", "she", "i", "me", "my", "your", "our", "their", "his", "her", "its", "ours", "theirs"}

# Combine all stopwords
all_stopwords = stopwords_id.union(stopwords_en)

# Function to fetch Google Play reviews
def fetch_reviews(app_id, lang, num_reviews, sort):
    try:
        result, _ = reviews(
            app_id,
            lang=lang,          # 'id' for Indonesian, 'en' for English
            country='id',       # Country: 'id' for Indonesia
            count=num_reviews,  # Number of reviews
            sort=sort          # 0 = Most Relevant, 1 = Newest
        )

        # Create DataFrame
        df = pd.DataFrame(result, columns=['userName', 'score', 'content', 'at'])
        return df
    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame()

# Function to visualize score distribution
def plot_score_distribution(df):
    fig, ax = plt.subplots()
    sns.countplot(x='score', data=df, palette='Set2', ax=ax, order=sorted(df['score'].unique()))
    ax.set_title("Distribusi Rating Ulasan")
    st.pyplot(fig)

# Function to extract meaningful words from low-score reviews
def extract_top_words(df, min_score=1, max_score=3, top_n=20):
    low_score_reviews = df[(df['score'] >= min_score) & (df['score'] <= max_score)]['content'].str.lower()
    all_text = " ".join(low_score_reviews)

    # Clean text: remove punctuation and numbers
    words = re.findall(r'\b[a-zA-Z]{3,}\b', all_text)

    # Filter out stopwords
    meaningful_words = [word for word in words if word not in all_stopwords]

    # Count word frequency
    word_counts = Counter(meaningful_words)
    return word_counts.most_common(top_n)

# Function to plot common problems from low-score reviews
def plot_common_problems(word_counts):
    if not word_counts:
        st.warning("No significant issues found in low-score reviews.")
        return

    words, counts = zip(*word_counts)
    fig, ax = plt.subplots()
    sns.barplot(x=counts, y=words, palette='Reds_r', ax=ax)
    ax.set_title("Kata Ulasan Rating Rendah")
    st.pyplot(fig)

def main():
    st.title("📊 Google Play App Review (Ulasan) Sentiment Analyzer")

    # App options
    app_choices = {
        "Telkomsel MyTelkomsel": "com.telkomsel.telkomselcm",
        "TelkomselKu": "com.tsel.telkomselku",
        "DigiposAja": "com.telkomsel.digiposaja",
        "IndiHome SMART": "com.telkomsel.yinni",
        "Maxstream": "com.maxstream",
        "Digi Korlantas(SIM)": "id.qoin.korlantas.",
        "Super App Polri(SKCK)":"idsuperapps.polri.presisi",
        "Signal Polri(STNK)":"app.signal.id",
        "My Pertamina":"com.dafturn.mypertamina",


    }

    # App selector
    app_name = st.selectbox("Pilih App:", list(app_choices.keys()))
    app_id = app_choices[app_name]

    # Language selector
    #lang = st.radio("Choose Language:", ["Indonesian", "English"], index=0)
   # lang_code = 'id' if lang == "Indonesian" else 'en'
    lang = "Indonesian"
    lang_code = 'id'
    # Number of reviews
    num_reviews = st.number_input("Jumlah Ulasan yang Akan Diambil:", min_value=1, max_value=5000, value=100)

    # Sort options
    sort_option = st.radio("Sort Reviews By:", ["Most Relevant", "Newest"], index=1)
    sort_code = Sort.MOST_RELEVANT if sort_option == "Most Relevant" else Sort.NEWEST

    # Scrape button
    if st.button("Mengambil Ulasan"):
        st.info(f"Mengunduh Ulasan for {app_name} in {lang}...")
        df = fetch_reviews(app_id, lang_code, num_reviews, sort_code)

        if not df.empty:
            st.success(f"Terunduh {len(df)} Ulasan!")
            st.dataframe(df)

            # Visualize score distribution
            plot_score_distribution(df)

            # Extract and visualize common problems (low-score reviews)
            st.subheader("🛠️ Masalah Umum Pengguna (Rating ≤ 3)")
            common_issues = extract_top_words(df, max_score=3)
            plot_common_problems(common_issues)

            # Download CSV
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download CSV", data=csv, file_name=f"{app_name}_reviews.csv", mime="text/csv")

if __name__ == '__main__':
    main()
