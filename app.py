import pandas as pd
import requests
import os
import streamlit as st

st.set_page_config(page_title="Personalized Variant Annotator", layout="wide")
st.title("🧬 Personalized Medicine: VCF Annotation App")

def annotate_variant(chrom, pos, ref, alt):
    # Format for MyVariant.info: chr{chrom}:g.{pos}{ref}>{alt}
    hgvs = f"chr{chrom}:g.{pos}{ref}>{alt}"
    url = f"https://myvariant.info/v1/variant/{hgvs}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        result = {
            "chr": chrom,
            "pos": pos,
            "ref": ref,
            "alt": alt,
            "gene": data.get('gene', {}).get('symbol', 'NA'),
            "clinical_significance": data.get('clinvar', {}).get('clinical_significance', 'NA'),
            "condition": data.get('clinvar', {}).get('trait', ['NA'])[0] if isinstance(data.get('clinvar', {}).get('trait', []), list) else 'NA',
            "link": f"https://www.ncbi.nlm.nih.gov/clinvar/variation/{data.get('clinvar', {}).get('rcv', [{}])[0].get('accession', '')}" if 'clinvar' in data else '',
            "source": "MyVariant.info"
        }
    except Exception as e:
        result = {
            "chr": chrom,
            "pos": pos,
            "ref": ref,
            "alt": alt,
            "gene": "NA",
            "clinical_significance": "Error",
            "condition": str(e),
            "link": "",
            "source": "MyVariant.info (fail)"
        }
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
                if row.get('link'):
                    st.markdown(f"[{row['gene']} ({row['condition']}) - {row['clinical_significance']}]({row['link']})")
