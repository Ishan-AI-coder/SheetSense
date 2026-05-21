import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
from main1 import summarize_agent, plotting_agent, qa_agent, DatasetDeps

st.set_page_config(page_title="SheetSense", layout="wide")

# ----------------------- Caching & Data Loading -----------------------
# Streamlit will cache this so it doesn't re-read the file on every interaction
@st.cache_data
def load_data(file):
    if file.name.endswith(".csv"):
        return pd.read_csv(file)
    elif file.name.endswith(".xlsx"):
        return pd.read_excel(file)
    return None

# ----------------------- Helper: Sanitize Code -----------------------
def clean_plot_code(code: str) -> str:
    """Removes markdown formatting and display calls to prevent syntax errors."""
    return (
        code.replace("```python", "")
        .replace(" ```", "")       
        .replace("plt.show()", "")
        .replace("fig.show()", "")
        .strip()
    )

# ----------------------- Main UI -----------------------
st.subheader("Upload your dataset")
uploaded_file = st.file_uploader("Upload a CSV or Excel file", type=["csv", "xlsx"])

if uploaded_file is not None:
    try:
        df = load_data(uploaded_file)
        
        if df is not None:
            st.success(f"✅ Dataset loaded successfully with {df.shape[0]} rows and {df.shape[1]} columns")
            
            with st.expander("📄 Preview Dataset", expanded=False):
                st.dataframe(df.head(100))

            # ------------------- Summarization Agent -------------------
            st.markdown("---")
            st.markdown("## 📝 SheetSense Summarizer")
            
            # Use a unique session state key based on filename so it regenerates only on a new file
            summary_key = f"summary_{uploaded_file.name}"
            
            if summary_key not in st.session_state:
                with st.spinner("🧠 Analyzing dataset structure and statistics..."):
                    # Pre-compute stats locally to save LLM tokens and prevent hallucination
                    summary_stats = df.describe(include='all').to_markdown()
                    missing_data = df.isnull().sum().to_markdown()
                    
                    user_prompt = f"""
                    The dataset has {df.shape[0]} rows and {df.shape[1]} columns.
                    Columns: {', '.join(df.columns.tolist())}.
                    
                    Missing Values per column:
                    {missing_data}
                    
                    Statistical Summary:
                    {summary_stats}
                    
                    Provide a detailed, readable summary of this data.
                    """
                    
                    # Run agent (no deps needed because data is in the text prompt)
                    result = summarize_agent.run_sync(user_prompt)
                    st.session_state[summary_key] = result.output

            st.markdown(st.session_state[summary_key])

            # ------------------- Plotting Agent -------------------
            st.markdown("---")
            st.markdown("## 📊 SheetSense Plotter")
            st.markdown("Select parameters to visualize your dataset.")

            plot_types = ["Auto", "Histogram", "Bar Chart", "Pie Chart", "Line Chart", "Scatter Plot"]
            selected_plot = st.selectbox("Choose Plot Type", plot_types)

            all_columns = df.columns.tolist()
            num_cols = [c for c in all_columns if pd.api.types.is_numeric_dtype(df[c])]
            cat_cols = [c for c in all_columns if not pd.api.types.is_numeric_dtype(df[c])]
            
            params = []
            if selected_plot in ["Histogram", "Line Chart"]:
                param1 = st.selectbox("Select 1 numerical column", num_cols)
                params = [param1] if param1 else []
            elif selected_plot == "Bar Chart":
                cat_col = st.selectbox("Select Categorical column", cat_cols)
                num_col = st.selectbox("Select Numerical column", num_cols)
                params = [cat_col, num_col] if cat_col and num_col else []
            elif selected_plot == "Pie Chart":
                params = st.multiselect("Select categorical columns", cat_cols)
            elif selected_plot == "Scatter Plot":
                num1 = st.selectbox("Select first numerical (X)", num_cols, key='x')
                num2 = st.selectbox("Select second numerical (Y)", num_cols, key='y')
                params = [num1, num2] if num1 and num2 else []
            else:
                params = st.multiselect("Select columns (Agent decides plot type)", all_columns)

            if st.button("Generate Plot"):
                if not params:
                    st.warning("Please select at least one column!")
                else:
                    user_input = f"Generate a {selected_plot} for columns: {', '.join(params)}"
                    with st.spinner("Writing plot code..."):
                        result = plotting_agent.run_sync(user_input)
                        cleaned_code = clean_plot_code(result.output)
                        
                        st.markdown("### 🧠 Generated Code")
                        st.code(cleaned_code, language="python")

                        try:
                            # SAFE EXECUTION: Restrict globals, pass only required locals
                            local_vars = {"df": df, "px": px, "plt": plt, "fig": None}
                            safe_globals = {"__builtins__": {}}
                            
                            exec(cleaned_code, safe_globals, local_vars)

                            # Render the plot dynamically based on what the agent used
                            if "fig" in local_vars and local_vars["fig"] is not None:
                                st.plotly_chart(local_vars["fig"], use_container_width=True)
                            elif plt.get_fignums():
                                st.pyplot(plt.gcf())
                                plt.close('all')
                            else:
                                st.warning("The code executed successfully, but no plot was rendered.")

                        except Exception as e:
                            st.error(f"❌ Failed to generate plot: {e}")

            # ----------------------- Q&A Agent -----------------------
            st.markdown("---")
            st.markdown("## 💬 SheetSense Q&A")
            st.markdown("Ask questions about your dataset. The AI will query the data directly.")

            user_query = st.text_input("Type your question")

            if st.button("Get Answer"):
                if not user_query.strip():
                    st.warning("Please enter a valid question.")
                else:
                    with st.spinner("Analyzing data to find your answer... 🤖"):
                        try:
                            # Pass the dataframe using our DatasetDeps dataclass
                            result = qa_agent.run_sync(
                                user_query, 
                                deps=DatasetDeps(df=df)
                            )
                            st.info(result.output)
                        except Exception as e:
                            st.error(f"⚠️ Failed to get response: {e}")

    except Exception as e:
        st.error(f"⚠️ Failed to load dataset: {e}")