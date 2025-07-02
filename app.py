import pandas as pd
import requests
import os
import streamlit as st

st.set_page_config(page_title="Personalized Variant Annotator", layout="wide")
st.title("🧬 Personalized Medicine: VCF Annotation App")

def annotate_variant(chrom, pos, ref, alt):
    query = f"{chrom}-{pos}-{ref}-{alt}"
    url = f"https://api.variantvalidator.org/variantvalidator/variant/GRCh38/{query}/annotation"
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            result = {
                "chr": chrom,
                "pos": pos,
                "ref": ref,
                "alt": alt,
                "gene": data.get('transcript_consequences', [{}])[0].get('gene_symbol', 'NA') if 'transcript_consequences' in data else 'NA',
                "clinical_significance": data.get('clinical_significance', 'NA'),
                "condition": data.get('conditions', [{}])[0].get('name', 'NA') if 'conditions' in data else 'NA',
                "link": data.get('external_link', 'https://www.ncbi.nlm.nih.gov/clinvar/') if data else 'https://www.ncbi.nlm.nih.gov/clinvar/',
                "source": "ClinVar"
            }
        else:
            result = {"chr": chrom, "pos": pos, "ref": ref, "alt": alt, "error": "Not Found"}
    except Exception as e:
        result = {"chr": chrom, "pos": pos, "ref": ref, "alt": alt, "error": str(e)}
    return result

def parse_and_annotate_vcf(file):
    annotations = []
    for line in file:
        if line.startswith('#'):
            continue
        parts = line.strip().split('\t')
        if len(parts) < 5:
            continue
        chrom = parts[0]
        pos = int(parts[1])
        ref = parts[3]
        alt_list = parts[4].split(',')
        for alt in alt_list:
            ann = annotate_variant(chrom, pos, ref, alt)
            annotations.append(ann)
    return pd.DataFrame(annotations)

uploaded_file = st.file_uploader("Upload your VCF file", type=["vcf"])

if uploaded_file is not None:
    with st.spinner("Annotating variants, please wait..."):
        lines = uploaded_file.read().decode('utf-8').splitlines()
        df = parse_and_annotate_vcf(lines)
        st.success("Annotation complete!")

        st.dataframe(df)

        st.download_button(
            label="📥 Download CSV",
            data=df.to_csv(index=False).encode('utf-8'),
            file_name="annotated_variants.csv",
            mime="text/csv"
        )

        if 'link' in df.columns:
            st.markdown("### 🔗 External Links")
            for idx, row in df.iterrows():
                if 'link' in row and row['link'] != "":
                    st.markdown(f"[{row['gene']} ({row['condition']}) - {row['clinical_significance']}]({row['link']})")
