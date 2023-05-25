import neo4j
import os
from dotenv import load_dotenv
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error

load_dotenv()

URI = os.getenv('NEO4J_URI')
AUTH = (os.getenv('NEO4J_USERNAME'), os.getenv('NEO4J_PASSWORD'))

with neo4j.GraphDatabase.driver(URI, auth=AUTH) as driver:
    result = driver.execute_query("""
                                                  MATCH (m:Movie) 
                                                  WHERE m.budget IS NOT NULL
                                                  RETURN m.movieId as id,m.title as title,m.budget as budget,
                                                         m.countries[0] as country,m.imdbRating as rating, m.year as year,
                                                    [(m)-[:IN_GENRE]->(g) | g.name][0] as genre
                                                  LIMIT 1000
                                                  """)
    records, summary, keys = result
    print("keys:", keys)
    for record in records:
        print("answer:", record)

    dicts = [r.data() for r in records]
    print(pd.DataFrame(dicts))
    print(pd.DataFrame(records, columns=keys))

    print(f"result available after {summary.result_available_after}ms")



# Assuming you have a dataset in a CSV file named 'movies_data.csv'
data = pd.DataFrame(records, columns=keys) # pd.read_csv("movies_data.csv")

# Preprocess the 'genre' column using one-hot encoding
encoder = OneHotEncoder()
encoder.fit(data[["genre"]])

genres_encoded = encoder.transform(data[["genre"]]).toarray()

# Create a DataFrame from the one-hot encoded genres and set column names
genres_encoded_df = pd.DataFrame(genres_encoded, columns=encoder.get_feature_names_out(["genre"]))

# Merge the one-hot encoded genres back into the original DataFrame
# keep rating, genres_encoded, year
data = data.join(genres_encoded_df).drop(columns=["genre","title","country","id"], axis=1)

# Define the features (X) and target (y)
X = data.drop("budget", axis=1)
y = data["budget"]

print(X.keys())

# Split the data into train and test sets (80% train, 20% test)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Initialize the RandomForestRegressor model
model = RandomForestRegressor(n_estimators=100, random_state=42)

# Train the model using the training data
model.fit(X_train, y_train)

# Predict the movie budgets for the test set
y_pred = model.predict(X_test)

# Calculate the mean squared error
mse = mean_squared_error(y_test, y_pred)
print("Mean squared error:", mse)

# Make sample predictions
sample_data = [
    {"rating": 7.5, "year": 2022, "genre": "Action"},
    {"rating": 8.2, "year": 1995, "genre": "Drama"},
]
sample_df = pd.DataFrame(sample_data)

# Preprocess the sample data (one-hot encoding for genre)
sample_genres_encoded = encoder.transform(sample_df[["genre"]]).toarray()
sample_genres_encoded_df = pd.DataFrame(sample_genres_encoded, columns=encoder.get_feature_names_out(["genre"]))
sample_df = sample_df.join(sample_genres_encoded_df).drop("genre", axis=1)

# Predict the movie budgets for the sample data
sample_predictions = model.predict(sample_df)
print("Sample predictions:", sample_predictions)
