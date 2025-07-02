{
 "cells": [
  {
   "cell_type": "code",
   "execution_count": 1,
   "id": "68ef746f-64c0-46b5-87f8-12001c8c1f99",
   "metadata": {},
   "outputs": [
    {
     "name": "stderr",
     "output_type": "stream",
     "text": [
      "2025-07-02 09:43:27.566 \n",
      "  \u001b[33m\u001b[1mWarning:\u001b[0m to view this Streamlit app on a browser, run it with the following\n",
      "  command:\n",
      "\n",
      "    streamlit run C:\\Users\\Edrich\\anaconda3\\Lib\\site-packages\\ipykernel_launcher.py [ARGUMENTS]\n"
     ]
    }
   ],
   "source": [
    "import pandas as pd\n",
    "import requests\n",
    "import os\n",
    "import streamlit as st\n",
    "\n",
    "st.set_page_config(page_title=\"Personalized Variant Annotator\", layout=\"wide\")\n",
    "st.title(\"🧬 Personalized Medicine: VCF Annotation App\")\n",
    "\n",
    "def annotate_variant(chrom, pos, ref, alt):\n",
    "    query = f\"{chrom}-{pos}-{ref}-{alt}\"\n",
    "    url = f\"https://api.variantvalidator.org/variantvalidator/variant/GRCh38/{query}/annotation\"\n",
    "    headers = {\"Content-Type\": \"application/json\"}\n",
    "    try:\n",
    "        response = requests.get(url, headers=headers, timeout=10)\n",
    "        if response.status_code == 200:\n",
    "            data = response.json()\n",
    "            result = {\n",
    "                \"chr\": chrom,\n",
    "                \"pos\": pos,\n",
    "                \"ref\": ref,\n",
    "                \"alt\": alt,\n",
    "                \"gene\": data.get('transcript_consequences', [{}])[0].get('gene_symbol', 'NA') if 'transcript_consequences' in data else 'NA',\n",
    "                \"clinical_significance\": data.get('clinical_significance', 'NA'),\n",
    "                \"condition\": data.get('conditions', [{}])[0].get('name', 'NA') if 'conditions' in data else 'NA',\n",
    "                \"link\": data.get('external_link', 'https://www.ncbi.nlm.nih.gov/clinvar/') if data else 'https://www.ncbi.nlm.nih.gov/clinvar/',\n",
    "                \"source\": \"ClinVar\"\n",
    "            }\n",
    "        else:\n",
    "            result = {\"chr\": chrom, \"pos\": pos, \"ref\": ref, \"alt\": alt, \"error\": \"Not Found\"}\n",
    "    except Exception as e:\n",
    "        result = {\"chr\": chrom, \"pos\": pos, \"ref\": ref, \"alt\": alt, \"error\": str(e)}\n",
    "    return result\n",
    "\n",
    "def parse_and_annotate_vcf(file):\n",
    "    annotations = []\n",
    "    for line in file:\n",
    "        if line.startswith('#'):\n",
    "            continue\n",
    "        parts = line.strip().split('\\t')\n",
    "        if len(parts) < 5:\n",
    "            continue\n",
    "        chrom = parts[0]\n",
    "        pos = int(parts[1])\n",
    "        ref = parts[3]\n",
    "        alt_list = parts[4].split(',')\n",
    "        for alt in alt_list:\n",
    "            ann = annotate_variant(chrom, pos, ref, alt)\n",
    "            annotations.append(ann)\n",
    "    return pd.DataFrame(annotations)\n",
    "\n",
    "uploaded_file = st.file_uploader(\"Upload your VCF file\", type=[\"vcf\"])\n",
    "\n",
    "if uploaded_file is not None:\n",
    "    with st.spinner(\"Annotating variants, please wait...\"):\n",
    "        lines = uploaded_file.read().decode('utf-8').splitlines()\n",
    "        df = parse_and_annotate_vcf(lines)\n",
    "        st.success(\"Annotation complete!\")\n",
    "\n",
    "        st.dataframe(df)\n",
    "\n",
    "        st.download_button(\n",
    "            label=\"📥 Download CSV\",\n",
    "            data=df.to_csv(index=False).encode('utf-8'),\n",
    "            file_name=\"annotated_variants.csv\",\n",
    "            mime=\"text/csv\"\n",
    "        )\n",
    "\n",
    "        if 'link' in df.columns:\n",
    "            st.markdown(\"### 🔗 External Links\")\n",
    "            for idx, row in df.iterrows():\n",
    "                if 'link' in row and row['link'] != \"\":\n",
    "                    st.markdown(f\"[{row['gene']} ({row['condition']}) - {row['clinical_significance']}]({row['link']})\")\n"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3 (ipykernel)",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.11.7"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 5
}
