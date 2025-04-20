import pandas as pd

# Function to process a single file into long format
def process_file_to_long_format(file_path):
    # Read the CSV file
    df = pd.read_csv(file_path)
    
    # Melt the dataframe to create a long format
    melted_df = pd.melt(
        df,
        id_vars=['Episode'],
        value_vars=[col for col in df.columns if col.startswith('Reference_')],
        var_name='Reference_Number',
        value_name='Reference'
    )
    
    # Clean up the data
    melted_df = melted_df.dropna(subset=['Reference'])
    melted_df = melted_df.drop('Reference_Number', axis=1)
    melted_df = melted_df[melted_df['Reference'].str.strip() != '']
    
    return melted_df

# Process both files
print("Processing references2.csv...")
df2 = process_file_to_long_format('references2.csv')
print(f"Shape of references2.csv after processing: {df2.shape}")

print("\nProcessing references3.csv...")
df3 = process_file_to_long_format('references3.csv')
print(f"Shape of references3.csv after processing: {df3.shape}")

# Combine the dataframes
combined_df = pd.concat([df2, df3], ignore_index=True)

# Remove any duplicates
combined_df = combined_df.drop_duplicates()

# Sort by episode URL
combined_df = combined_df.sort_values('Episode')

# Display information
print("\nFinal combined dataset:")
print("Shape:", combined_df.shape)
print("\nFirst few rows:")
display(combined_df.head(10))

# Save to a new CSV file
combined_df.to_csv('combined_references_long_format.csv', index=False)
print("\nSaved to combined_references_long_format.csv")

# Display some statistics
print("\nNumber of references per episode:")
print(combined_df.groupby('Episode').size().describe())