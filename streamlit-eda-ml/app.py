import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns
import neo4j
import os
from dotenv import load_dotenv
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error

load_dotenv()

URI = os.getenv('NEO4J_URI')
AUTH = (os.getenv('NEO4J_USERNAME'), os.getenv('NEO4J_PASSWORD'))
QUERY = """
        MATCH (m:Movie) 
        WHERE none(k in ['imdbRating','budget','runtime','year','revenue','imdbVotes','released'] WHERE m[k] IS NULL)

        RETURN m.movieId as id,m.title as title,m.budget as budget,m.countries[0] as country,
        m.imdbId as imdbId,m.imdbRating as rating,m.imdbVotes as votes,
        m.languages[0] as language,m.plot as plot,m.poster as poster,m.released as released,m.revenue as revenue,
        m.runtime as runtime,m.tmdbId as tmdbId,
        m.url as url,m.year as year,[(m)-[:IN_GENRE]->(g) | g.name][0] as genre
        LIMIT $rows
        """

    
@st.cache_data(ttl=300, max_entries=100)
def read_data(query, rows=1):
    with neo4j.GraphDatabase.driver(URI, auth=AUTH) as driver:
        records, summary, keys = driver.execute_query(query, {"rows":rows})
        return pd.DataFrame(records, columns=keys)

def predict(input):
    st.sidebar.header("Prediction")
    data = input
    predict_column = st.sidebar.selectbox("Select value to predict", data.columns, index=data.columns.get_loc("budget"))

    # Preprocess the 'genre' column using one-hot encoding
    encoder = OneHotEncoder()
    encoder.fit(data[["genre"]])

    genres_encoded = encoder.transform(data[["genre"]]).toarray()

    # Create a DataFrame from the one-hot encoded genres and set column names
    genres_encoded_df = pd.DataFrame(genres_encoded, columns=encoder.get_feature_names_out(["genre"]))

    # Merge the one-hot encoded genres back into the original DataFrame
    # keep rating, genres_encoded, year
    data = input[["rating","year",predict_column]]
    data = data.join(genres_encoded_df) # .drop(columns=["genre","title","country","id"], axis=1)

    st.write(data.head())

    # Define the features (X) and target (y)
    X = data.drop(predict_column, axis=1)
    y = data[predict_column]

    # Split the data into train and test sets (80% train, 20% test)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Initialize the RandomForestRegressor model
    model = RandomForestRegressor(n_estimators=100, random_state=42)

    # Train the model using the training data
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)

    # Calculate the mean squared error
    mse = mean_squared_error(y_test, y_pred)
    st.text("Mean squared error: {}".format(mse))

    # Make sample predictions
    sample_data = [
        {"rating": 7.5, "year": 2000, "genre": "Action"},
        {"rating": 8.2, "year": 1995, "genre": "Drama"},
    ]
    sample_df = pd.DataFrame(sample_data)
    st.write(sample_df)

    st.header("2000 Action Movies")
    st.write(input[(input["year"] == 2000) & (input["genre"] == "Action")].head())
    st.header("1995 Dramas")
    st.write(input[(input["year"] == 1995) & (input["genre"] == "Drama")].head())

    # Preprocess the sample data (one-hot encoding for genre)
    sample_genres_encoded = encoder.transform(sample_df[["genre"]]).toarray()
    sample_genres_encoded_df = pd.DataFrame(sample_genres_encoded, columns=encoder.get_feature_names_out(["genre"]))
    sample_df = sample_df.join(sample_genres_encoded_df).drop("genre", axis=1)

    sample_predictions = model.predict(sample_df)
    st.write("Sample predictions: {}".format(sample_predictions))

    
def eda(data):
    st.sidebar.header("Visualizations")

    st.header("Upload your CSV data file")
    data_file = "/Users/mh/Downloads/movieData/movies.csv"
    # st.file_uploader("Upload CSV", type=["csv"])
    if data is not None:
        # data = pd.DataFrame(records, columns=keys)
        st.write("Data overview:")
        st.write(data.head())

        plot_options = ["Bar plot", "Scatter plot", "Histogram", "Box plot"]
        selected_plot = st.sidebar.selectbox("Choose a plot type", plot_options)

        if selected_plot == "Bar plot":
            x_axis = st.sidebar.selectbox("Select x-axis", data.columns)
            y_axis = st.sidebar.selectbox("Select y-axis", data.columns)
            st.write("Bar plot:")
            fig, ax = plt.subplots()
            sns.barplot(x=data[x_axis], y=data[y_axis], ax=ax)
            ax.set_xticklabels(ax.get_xticklabels(), rotation=90, ha="right")
            ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True, nbins=10))
            st.pyplot(fig)

        elif selected_plot == "Scatter plot":
            x_axis = st.sidebar.selectbox("Select x-axis", data.columns)
            y_axis = st.sidebar.selectbox("Select y-axis", data.columns)
            st.write("Scatter plot:")
            fig, ax = plt.subplots()
            sns.scatterplot(x=data[x_axis], y=data[y_axis], ax=ax)
            ax.set_xticklabels(ax.get_xticklabels(), rotation=90, ha="right")
            ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True, nbins=10))
            st.pyplot(fig)

        elif selected_plot == "Histogram":
            column = st.sidebar.selectbox("Select a column", data.columns)
            bins = st.sidebar.slider("Number of bins", 5, 100, 20)
            st.write("Histogram:")
            fig, ax = plt.subplots()
            sns.histplot(data[column], bins=bins, ax=ax)
            ax.set_xticklabels(ax.get_xticklabels(), rotation=90, ha="right")
            ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True, nbins=10))
            st.pyplot(fig)

        elif selected_plot == "Box plot":
            column = st.sidebar.selectbox("Select a column", data.columns)
            st.write("Box plot:")
            fig, ax = plt.subplots()
            sns.boxplot(data[column], ax=ax)
            ax.set_xticklabels(ax.get_xticklabels(), rotation=90, ha="right")
            ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True, nbins=10))
            st.pyplot(fig)

pages = {"EDA":eda, "Predict":predict}

def main():
    st.title("Hello, World! EDA Streamlit App")
    selected_page = st.sidebar.selectbox("Choose a page", options=list(pages.keys()))

    rows = st.sidebar.number_input("Number of rows", min_value=1, max_value=5000, value=50, step=1)
    data = read_data(QUERY, rows)

    pages[selected_page](data)

if __name__ == "__main__":
    main()

