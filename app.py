import pandas as pd
import requests
import os
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Personalized Variant Annotator", layout="wide")
st.title("🧬 Personalized Medicine: VCF Annotation App")

# Annotation function using MyVariant.info
def annotate_variant(chrom, pos, ref, alt):
    hgvs = f"chr{chrom}:g.{pos}{ref}>{alt}"
    url = f"https://myvariant.info/v1/variant/{hgvs}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        gene = data.get('gene', {}).get('symbol', 'NA')
        clinical = data.get('clinvar', {})
        result = {
            "chr": chrom,
            "pos": pos,
            "ref": ref,
            "alt": alt,
            "gene": gene,
            "clinical_significance": clinical.get('clinical_significance', 'NA'),
            "condition": clinical.get('trait', ['NA'])[0] if isinstance(clinical.get('trait', []), list) else 'NA',
            "link": f"https://www.ncbi.nlm.nih.gov/clinvar/variation/{clinical.get('rcv', [{}])[0].get('accession', '')}" if 'rcv' in clinical else '',
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

# Load and annotate VCF

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

# Fetch clinical trial data
def fetch_clinical_trials(condition):
    query = condition.replace(' ', '+')
    url = f"https://clinicaltrials.gov/api/query/study_fields?expr={query}&fields=BriefTitle,Phase,OverallStatus,InterventionName,LocationCity,NCTId&min_rnk=1&max_rnk=3&fmt=json"
    try:
        res = requests.get(url, timeout=10)
        data = res.json()['StudyFieldsResponse']['StudyFields']
        return pd.DataFrame(data)
    except:
        return pd.DataFrame()

uploaded_file = st.file_uploader("Upload your VCF file", type=["vcf"])

if uploaded_file is not None:
    with st.spinner("Annotating variants, please wait..."):
        lines = uploaded_file.read().decode('utf-8').splitlines()
        df = parse_and_annotate_vcf(lines)
        st.success("Annotation complete!")

        # Visualization of chromosome variant positions
        df_numeric = df.copy()
        df_numeric['pos'] = pd.to_numeric(df_numeric['pos'], errors='coerce')
        df_numeric = df_numeric[df_numeric['pos'].notna()]

        fig = px.scatter(
            df_numeric,
            x="pos",
            y=[0]*len(df_numeric),
            hover_data=["gene", "condition", "clinical_significance"],
            title="🧬 Variant Positions on Chromosome",
            labels={"pos": "Genomic Position"},
        )
        fig.update_traces(marker=dict(size=10, color="#636EFA"))
        fig.update_layout(yaxis=dict(showticklabels=False), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

        # Show detailed results and trial info
        st.subheader("📋 Variant Annotation Table")
        st.dataframe(df)

        selected_idx = st.selectbox("Select a variant to view more info:", options=df.index, format_func=lambda x: f"{df.at[x, 'gene']} - {df.at[x, 'condition']}")

        selected = df.loc[selected_idx]
        st.markdown(f"### 🦠 **Disease:** {selected['condition']}")
        st.markdown(f"**Gene:** {selected['gene']}")
        st.markdown(f"**Clinical Significance:** {selected['clinical_significance']}")
        if selected['link']:
            st.markdown(f"🔗 [ClinVar Link]({selected['link']})")

        with st.expander("🧪 Clinical Trials Related to This Condition"):
            trial_df = fetch_clinical_trials(selected['condition'])
            if not trial_df.empty:
                st.dataframe(trial_df)
            else:
                st.info("No trials found or API request failed.")

        st.download_button(
            label="📥 Download Annotated CSV",
            data=df.to_csv(index=False).encode('utf-8'),
            file_name="annotated_variants.csv",
            mime="text/csv"
        )
