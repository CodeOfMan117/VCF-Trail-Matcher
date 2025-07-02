**Personalized VCF Annotation App**

A Streamlit web app that allows users to upload VCF files, annotate genetic variants using NCBI's Variant Validator API, and receive clinically relevant information, drug associations, and links to external databases.

## Features

- Upload `.vcf` files
- Get gene, clinical significance, and condition annotations
- Download annotated results as CSV
- Clickable external database links

## How to Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
