import pandas as pd
import io
import cloudinary
import cloudinary.uploader

# Configure your Cloudinary credentials
cloudinary.config(
    cloud_name="dge8sniaa",
    api_key="428333455231115",
    api_secret="huSTYFbBLUjU7EgxezYxohSjCRM"
)

def upload_dataframe_to_cloudinary(df, folder_name="Trend generator", file_name="dataframe.xlsx"):
    # Save the DataFrame as an Excel file in memory
    cloudinary.config(
    cloud_name="dge8sniaa",
    api_key="428333455231115",
    api_secret="huSTYFbBLUjU7EgxezYxohSjCRM"
)
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False)

    # Reset buffer position to start
    excel_buffer.seek(0)

    # Upload the Excel file to Cloudinary in the specified folder
    response = cloudinary.uploader.upload(
        excel_buffer,
        resource_type="raw",    # Set as 'raw' to handle non-image files
        folder=folder_name,
        public_id=file_name,  # Filename without extension
        overwrite=True
    )

    # Return the secure URL of the uploaded file
    print(response["secure_url"])
    return response["secure_url"]

