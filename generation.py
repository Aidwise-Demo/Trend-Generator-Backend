import pandas as pd
from io import StringIO
import re
import time
from openpyxl import load_workbook
import os

def get_category(model, Trends, filename):
    response = model.generate_content("Provide the names of category which follow " + Trends + " trends which are related to deparatment of health Abu dhabi, Do not ignore Mater Prompt, Here is the master prompt: Follow the example i have shown always answer in comma separated, do not use numbering, like csv do not use any other format other than csv format to answer, for example you should answer like Category1, Category2 , Category3 ")
    df_category = pd.read_csv(StringIO(response.text), header=None)

    # Transpose the DataFrame to switch rows and columns
    df_category = df_category.transpose()
    time.sleep(10)
    get_subtrends_of_Category(model, df_category, filename)
    
    # return df_category

def get_subtrends_of_Category(model, df_category, filename):
    len = df_category.shape[0]
    for i in range(len):
        value = str(df_category.iloc[i, 0])
        subtrends = model.generate_content("Give me sub-trends for " + value + "  which are related to deparatment of health Abu dhabi, Do not ignore Mater Prompt, Here is the master prompt: Firstly Do not include Cateogry in the answer just answer the subtrends as example i have shown always answer in comma separated, do not use numbering, like csv do not use any other format other than csv format to answer, for example you should answer like subtrend1, subtrend2 , subtrend2")
        df_subtrends = pd.read_csv(StringIO(subtrends.text), header=None)
        # print(subtrends.text)
        df_subtrends = df_subtrends.transpose()
        time.sleep(10)
        get_subtrends1_of_subtrends(model, df_subtrends, filename)

    # return df_subtrends

def get_subtrends1_of_subtrends(model, df_subtrends, filename):
    len = df_subtrends.shape[0]
    for i in range(len):
        value = str(df_subtrends.iloc[i, 0])
        subtrends1 = model.generate_content("Give me sub-trends for " + value + " which are related to deparatment of health Abu dhabi, Do not ignore Mater Prompt, Here is the master prompt: Firstly Do not include Cateogry in the answer just answer the subtrends as example i have shown always answer in comma separated, do not use numbering, like csv do not use any other format other than csv format to answer, for example you should answer like subtrend1, subtrend2 , subtrend2 ")
        print(subtrends1.text)
        df_subtrends1 = pd.read_csv(StringIO(subtrends1.text), header=None)
        df_subtrends1 = df_subtrends1.transpose()
        time.sleep(10)
        final_output(model, df_subtrends1, filename)

    # return df_subtrends1

def final_output(model, df_subtrends2, filename):
    len = df_subtrends2.shape[0]
    for i in range(len):
        value = str(df_subtrends2.iloc[i, 0])
        prompt = f"""Generate a tabular dataset with 6 columns, AKWAYS 6 COLUMNS NOT 7 separated by '~' and each row delineated by '//'. Omit column names and represent missing values with NAN without spaces.

    For this Subcategory: {value}, include the following information below (do not include anything else):
    ~ Subcategory: [the name of the subcategory]
    ~ Trend: [AI-generated insight on the specific trend in the Department of health abu dhabi]
    ~ Detail: [AI-generated insight on the details and statistics related to the trend]
    ~ Threat: [AI-generated insight on potential threats associated with the trend in the Department of health abu dhabi]
    ~ Opportunity: [AI-generated insight on opportunities arising from the trend in the Department of health abu dhabi]
    ~ Impact Score: [AI-generated insight on the impact score of the trend] (Score: High Medium Low)

    Ensure that each response does not exceed one line for clarity and brevity. Generate at least 30 rows, and for each category, you can generate as many rows as subcategories.

    For each sub-category, do not write anything else; just provide the data. Thank you!
    DO NOT include the row numbering. Only answers like this:?

    Digital Workforce ~ Automation is rapidly transforming the UAE workforce, leading to increased efficiency and productivity. ~ By 2025, robots and AI are predicted to replace 15% of jobs, requiring workers to upskill and adapt to new technologies. ~ Job displacement and economic inequality may arise due to the automation of tasks, particularly affecting low-skilled workers. ~ New job opportunities and industries, such as AI and robotics engineering, are emerging, creating a demand for skilled professionals. ~ High //
    Digital Urbanization ~ The UAE is undergoing significant digital transformation, driven by smart city initiatives and AI-powered infrastructure. ~ Dubai's "Smart City 2021" strategy aims to integrate technology for better public services, traffic management, and resource optimization. ~ Cybersecurity risks and privacy concerns may increase with the expansion of digital infrastructure and data collection. ~ Digitalization can promote economic diversification, enhance citizen engagement, and improve overall quality of life. ~ High //

    DO NOT ANSWER LIKE THE BELOW:
    ~ Virtual consultations ~ AI-powered virtual consultations are gaining traction in the UAE's healthcare sector, providing patients with convenient and remote healthcare access. ~ AI-enabled virtual consultations can streamline patient care, reduce costs, and expand healthcare services to underserved areas. ~ Potential data security vulnerabilities and privacy concerns need to be addressed to ensure patient confidentiality. ~ This trend presents opportunities for expanding telemedicine, promoting preventive care, and minimizing the burden on healthcare facilities. ~ High//
    ~ AI in education ~ AI is revolutionizing the UAE's education landscape by personalizing learning experiences and improving teaching outcomes. ~ AI-powered adaptive learning platforms tailor educational content to individual students' needs, enhancing knowledge retention and engagement. ~ Lack of proper teacher training and potential biases in algorithms pose challenges to AI integration in education. ~ AI can democratize education, provide real-time feedback, and facilitate lifelong learning opportunities. ~ High //
    ~ Robotic process automation ~ The UAE is embracing robotic process automation (RPA) to enhance efficiency and productivity across various industries. ~ RPA streamlines repetitive and mundane tasks, allowing human workers to focus on higher-value activities. ~ Overreliance on RPA may result in job losses, exacerbating unemployment issues. ~ Automation can lead to cost savings, improved accuracy, and increased compliance, driving economic growth. ~ High //
    """
        final_output = model.generate_content(prompt)

        print(final_output.text)
        try:
            data_df = pd.read_csv(StringIO(final_output.text.replace('//', '')), sep='~', header=None, engine='python')

            # data_df.to_excel('output.xlsx', index=False, engine='openpyxl')

            file_path = f'{filename}.xlsx'

            if not os.path.exists(file_path):
                    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                            pd.DataFrame().to_excel(writer, index=False, sheet_name='Sheet1')

            # Load the existing Excel file
            existing_data = pd.read_excel(file_path, sheet_name='Sheet1')

            # Concatenate the existing data with the new data
            combined_data = pd.concat([existing_data, data_df], ignore_index=True)

            # Use ExcelWriter to overwrite the existing file with the updated data
            with pd.ExcelWriter(file_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                    # Write the combined data to the Excel file
                    combined_data.to_excel(writer, index=False, sheet_name='Sheet1')

            print("Data Appended successfully")
            time.sleep(20)

        except Exception as e:
            final_output = model.generate_content(prompt)

            print(final_output.text)
            try:
                data_df = pd.read_csv(StringIO(final_output.text.replace('//', '')), sep='~', header=None, engine='python')

                # data_df.to_excel('output.xlsx', index=False, engine='openpyxl')

                file_path = 'output.xlsx'

                if not os.path.exists(file_path):
                        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                                pd.DataFrame().to_excel(writer, index=False, sheet_name='Sheet1')

                # Load the existing Excel file
                existing_data = pd.read_excel(file_path, sheet_name='Sheet1')

                # Concatenate the existing data with the new data
                combined_data = pd.concat([existing_data, data_df], ignore_index=True)

                # Use ExcelWriter to overwrite the existing file with the updated data
                with pd.ExcelWriter(file_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                        # Write the combined data to the Excel file
                        combined_data.to_excel(writer, index=False, sheet_name='Sheet1')

                print("Data Appended successfully")
                time.sleep(20)

            except Exception as e:
                print(f"An error occurred: {str(e)}")
                
                