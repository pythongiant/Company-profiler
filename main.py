import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
from openai import OpenAI
import traceback 
# import pdfkit
# import base64
# from weasyprint import HTML
# import tiktoken
# Function to scrape the website

import requests
from bs4 import BeautifulSoup
import re
import traceback

def scrape_website(site):
    linkedin = []
    token_limit = 16385
    sites = []
    text_content = ""
    metadata = {}  # Dictionary to store metadata
    print("finding for site ",site )
    try:
        hdr = {'User-Agent': 'Mozilla/5.0'}
        req = requests.get(site, headers=hdr)
        soup = BeautifulSoup(req.content, 'html.parser')
        
        # Extract metadata
        title = soup.title.string if soup.title else ""
        meta_tags = soup.find_all('meta')
        description = ""
        keywords = ""
        for tag in meta_tags:
            if tag.get('name') == 'description':
                description = tag.get('content')
            elif tag.get('name') == 'keywords':
                keywords = tag.get('content')

        # Store metadata in dictionary
        text_content += f"title :{title} \n description : {description} \n keywords: {keywords}"
        links = soup.body.find_all('a')
        text_content += soup.get_text()
        urls = [link.get('href') for link in links if link.get('href') is not None]
        done = 0    

        for link in urls:
            if "linkedin" in link:
                linkedin.append(link)
        
            if link.startswith('/'):
                link = site.replace('/','') + link
            if site in link and link not in sites:
                print("Going through ", link , " Now")  
                done += 1
                print("Done with ",done*100/len(urls),'%')
                try:
                    sites.append(link)
                    req = requests.get(link, headers=hdr)
                    soup = BeautifulSoup(req.content, 'html.parser')
                    links = soup.body.find_all('a') 
                    if len(text_content)/4 > token_limit:
                        print("Token Limit exceeds, breaking loop now")
                        break
                    links = [link.get("href") for link in soup.find_all('a') if link.get("href")]  # Extract all href attributes from <a> tags
                    links_text = ' '.join(links)  # Concatenate all links into a single string

                    text_content += re.sub(r'\s+', ' ', soup.get_text() + links_text)

                except Exception as e:
                    traceback.print_exc() 
                    st.error(f"Error while processing the website: {e}")
                
    except Exception as e:
        print(e)
        st.error(f"Error while processing the website: {e}")
    return linkedin, text_content[:token_limit*4]


# Streamlit UI
st.set_page_config(
    page_title="HUBX",
    page_icon="./logo.ico  ",
)
st.markdown(
    f'<img src="https://evalian.co.uk/wp-content/uploads/2022/06/logo.png" style="max-width:25%; background-color:white; height:auto;">', 
    unsafe_allow_html=True
)
st.title("Company Profile Analyser")

site = st.text_input("Enter the website URL", "https://ragnarcapital.com/")
from openai import OpenAI
client = OpenAI(api_key=st.secrets['api_key'])

if st.button("Analyze"):
    linkedin, text_content = scrape_website(site)
    print("Linkedin is ",linkedin)
    print("text_content found was ",text_content)
    if linkedin or text_content:
        if linkedin and text_content:
            st.success("Website processed successfully.")
        st.write("LinkedIn URLs: ", linkedin)

        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            temperature=0.5,
            presence_penalty=-1,
            messages=[{"role": "system", "content": """
           You are helping Investor to produce an executive summary with due diligence / company analysis report exportable in PDF. Return only the executive summary and nothing else. Get these details out of the company from their website's transcript which will be provided.
                        
- Summary of business. Do not add gibberish and if a data is not available skip that field completely. Mention only what is said in the transcript and do not infer any details outside of that. 
- Typical business model - Understanding revenue generation and operations. Mention only what is said in the transcript about the deal types and do not infer any details outside of that. 
- Risks of business (pros and cons) - Identifying potential challenges and opportunities. Do a very quick SWAT analysis.  Mention only what is said in the transcript and do not infer any details outside of that. 
- Unique Selling points - Highlighting competitive advantages. Mention only what is said in the transcript and do not infer any details outside of that. 
- Contact names within the business -  Facilitating direct communication with key stakeholders. Give Links, Address or direct names given in the document. If the details or links are not present then leave it


            """},{"role":"user","content":text_content}],

        )
        index = completion.choices[0].message.content
        st.markdown(index)
    else:
        
        st.error("No data found or an error occurred.")

