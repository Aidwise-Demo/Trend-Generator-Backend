import json
import os
import shutil
import smtplib
import tempfile
import uuid
from email.message import EmailMessage
from pathlib import Path
from filetocloudinary import upload_dataframe_to_cloudinary
# pip install cloudinary
import cloudinary
import cloudinary.uploader
import google.generativeai as genai
import motor.motor_asyncio
import openpyxl
import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from pydantic import BaseModel
from starlette.background import BackgroundTask
from xlsxwriter import Workbook
import limited_generation as Limit_gen
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI_GRAVITY")
client1 = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
db = client1.HorizonScanner
collection1 = db.Input
collection2 = db.Ouput

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY_GRAVITY")
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS_GRAVITY")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD_GRAVITY")

genai.configure(api_key=GOOGLE_API_KEY)

safety_settings = [
    {
        "category": "HARM_CATEGORY_DANGEROUS",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_NONE",
    },
]

# model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest")
# model = genai.GenerativeModel(model_name="gemini-1.0-pro")
model = genai.GenerativeModel(model_name="gemini-1.5-flash-latest", safety_settings=safety_settings)

# model = GoogleGenerativeAI(model="gemini-1.5-flash-latest", google_api_key=GOOGLE_API_KEY)

Trend_list = ['Social','Technological','Economic','Environmental','Political','Legal','Ethical']
# sample
# Gmail SMTP configuration
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587

OUTPUT_FOLDER = "Output"
Path(OUTPUT_FOLDER).mkdir(parents=True, exist_ok=True)

app = FastAPI()

# Allow all origins for demonstration purposes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with your client's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Input(BaseModel):
    Trends: str
    filename: str
    no_of_gen: int
    email: str
    dept: str
    geography: str
    additional_details: str

def smart_capitalize(sentence):
    
    exclude_words = {
    "a", "an", "and", "as", "at", "but", "by", "for", "if", "in", "nor", "of", "on", "or", "so", "the", "to", "up", "with"
    }
    # Split the sentence into words
    words = sentence.split()
    
    # Capitalize the first word unconditionally
    capitalized_sentence = [words[0].capitalize()]
    
    # Capitalize each word based on the exclude list
    for word in words[1:]:
        if word.lower() in exclude_words:
            capitalized_sentence.append(word.lower())
        else:
            capitalized_sentence.append(word.capitalize())
    
    # Join the words back into a single string
    return " ".join(capitalized_sentence)

def send_email(email, download_link):
    # Create email message
    Usermsg = EmailMessage()

    # Read HTML content from file with UTF-8 encoding
    with open("email.html", "r", encoding="utf-8") as file:
        html_content = file.read()

    html_content = html_content.replace("{download_link}", download_link)

    Usermsg.set_content(html_content, subtype='html') 
    Usermsg['Subject'] = "Your file is ready to download 🎉"
    Usermsg['From'] = EMAIL_ADDRESS
    Usermsg['To'] = email

    # Send email via SMTP
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(Usermsg)
        server.quit()
        print('Your message has been sent!', 'success')
    except Exception as e:
        print('There was an error sending your message. Please try again later.', 'danger')

def update_status(folder_name):
    print("Updating Status")
    result = collection1.update_one({"Foldername": folder_name}, {"$set": {"Status": True}})
    print("Status Updated!")

def insert_data(output_data):
    print("Inserting Data")
    inserted_document = collection2.insert_one(output_data)
    print(f"Output Stored in DB")

def background_function(Trends, no_of_gen, filename, email, folder_name, dept , additional_details, geography):
    # Your asynchronous function implementation here
    Limit_gen.get_category_no_of_gen(model, Trends, no_of_gen , filename, dept, additional_details, geography)
    
    # Define column names
    column_names = ['Subcategory', 'Trend', 'Detail', 'Threat', 'Opportunity', 'Impact Score']

    # Read Excel file into DataFrame and set column names
    df = pd.read_excel(filename + '.xlsx', names=column_names)
    df = df.dropna()
    df = df.drop_duplicates()
    clodinary_filename=filename.split("\\")
    upload_dataframe_to_cloudinary(df,file_name=f"{clodinary_filename[-1]}.xlsx")
    download_link=upload_dataframe_to_cloudinary(df,file_name=f"{clodinary_filename[-1]}.xlsx")
    print("saved to cloudinary")
    
    if os.path.exists(filename+ '.xlsx'):
        os.remove(filename+ '.xlsx')
        
    json_data = df.to_json(orient='records', indent=4)
    
    output_data = {
        "Foldername": folder_name,
        "output_data": json.loads(json_data)
    }
    
    insert_data(output_data)
    
    deletepath = os.path.join('Output', folder_name)
    
    if os.path.exists(deletepath):
        try:
            shutil.rmtree(deletepath)
            print(f"Folder '{deletepath}' deleted successfully")
        except Exception as e:
            print(f"Error deleting folder '{deletepath}': {str(e)}")
            # Additional logging can be added here for debugging
    else:
        print(f"Folder '{deletepath}' not found")

    send_email(email=email, download_link=download_link)
    print(f"Email Sent to : {email}")
    
    update_status(folder_name)

@app.get("/", response_class=HTMLResponse)
def read_index():
    with open("index.html", "r") as file:
        html_content = file.read()
    return HTMLResponse(content=html_content)
    
@app.post("/limited_generate")
async def limited_generation(Input_get: Input, background_tasks: BackgroundTasks = BackgroundTasks()):

    print(Input_get.Trends, " - " , Input_get.filename, " - ", Input_get.no_of_gen)
    # Generate a random folder name
    folder_name = str(uuid.uuid4())
    display_name = str(f"{Input_get.Trends.capitalize()} Trend Report for {Input_get.geography.capitalize()}_{smart_capitalize(str(Input_get.dept))}")
    folder_path = os.path.join(OUTPUT_FOLDER, folder_name)

    os.makedirs(folder_path,exist_ok=True)

    file_path = os.path.join(folder_path, Input_get.filename)
    
    input_data = {
        "Foldername": folder_name,
        "display_name": display_name,
        "Status": False,
        "input_data": dict(Input_get)
    }
    
    inserted_document = await collection1.insert_one(input_data)
    # Function Call Here
    background_tasks.add_task(background_function, Input_get.Trends, Input_get.no_of_gen , file_path, Input_get.email, folder_name, Input_get.dept, Input_get.additional_details, Input_get.geography)

    return {"Foldername": folder_name}

@app.get("/status/{folder_name}")
async def get_status(folder_name: str):
    
    records = await collection1.find_one({"Foldername": folder_name})

    if records['Status']:
        return {"status": "completed"}
    else:
        return {"status": "processing"}          

@app.get("/inputlist")
async def get_input():
    print(f"MONGO_URI: {MONGO_URI}")
    records = await collection1.find().to_list(length=None)
    if not records:
        raise HTTPException(status_code=404, detail="No records found")
    for file in records:
        file["_id"] = str(file["_id"])
    return JSONResponse(content=records)

@app.get("/data/{folder_name}")
async def get_data(folder_name: str):
    
    records = await collection1.find_one({"Foldername": folder_name})

    if records['Status']:
        
        output = await collection2.find_one({"Foldername": folder_name})
        return JSONResponse(content=output['output_data'])
    else:
        return {"message": "Data not generated yet"}   

@app.get("/DownloadFile/{folder_name}")
async def download_file(folder_name: str):
    records = await collection1.find_one({"Foldername": folder_name})

    if not records:
        return JSONResponse(content={"error": "Folder not found"}, status_code=404)

    if records['Status']:
        output = await collection2.find_one({"Foldername": folder_name})
        
        if not output or 'output_data' not in output:
            return JSONResponse(content={"error": "Output data not found"}, status_code=404)
        
        # Create a temporary file with a secure random name
        fd, temp_path = tempfile.mkstemp(suffix='.xlsx')
        os.close(fd)

        try:
            # Create and save the workbook
            wb = openpyxl.Workbook()
            wb.save(temp_path)

            # Write the data to the temporary file
            pd.DataFrame(output['output_data']).to_excel(temp_path, index=False)

            # Ensure the file exists before sending it
            if os.path.isfile(temp_path):
                return FileResponse(
                    path=temp_path,
                    filename=f"{records['display_name']}.xlsx" if records['display_name'] else "output.xlsx",
                    media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    background=BackgroundTask(lambda: os.unlink(temp_path))
                )
            else:
                raise HTTPException(status_code=500, detail="File not created")
        except Exception as e:
            # If an error occurs, ensure the file is deleted
            if os.path.isfile(temp_path):
                os.unlink(temp_path)
            raise HTTPException(status_code=500, detail=f"Error creating file: {str(e)}")
    else:
        return JSONResponse(content={"error": "File not ready to download"}, status_code=404)