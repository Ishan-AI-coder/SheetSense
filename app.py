import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
from main import summarize_agent, plotting_agent, qa_agent, plot_qa_agent, DatasetDeps, PlotDeps
import re

st.set_page_config(page_title="SheetSense", layout="wide")

# ----------------------- Caching & Data Loading -----------------------
@st.cache_data
def load_data(file):
    if file.name.endswith(".csv"):
        return pd.read_csv(file)
    elif file.name.endswith(".xlsx"):
        return pd.read_excel(file)
    return None

def clean_plot_code(code: str) -> str:
    code = (
        code.replace("```python", "")
        .replace("```", "")
        .replace("plt.show()", "")
        .replace("fig.show()", "")
    )
    
    code = re.sub(r'^(?:from\s+[\w\.]+\s+import\s+.*|import\s+.*)$', '', code, flags=re.MULTILINE)
    
    return code.strip()

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
            
            summary_key = f"summary_{uploaded_file.name}"
            
            if summary_key not in st.session_state:
                with st.spinner("🧠 Analyzing dataset structure and statistics..."):
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
                        
                        # Store plot state and RESET plot Q&A history when a new plot is made
                        st.session_state.current_plot_code = cleaned_code
                        st.session_state.current_plot_type = selected_plot
                        st.session_state.current_plot_params = params
                        st.session_state.plot_qa_history = []  # Pydantic AI history
                        st.session_state.plot_ui_chat = []     # Streamlit UI history

            # Render the Plot and the Plot Q&A if a plot exists in session state
            if "current_plot_code" in st.session_state:
                try:
                    local_vars = {"df": df, "px": px, "plt": plt, "fig": None}
                    safe_globals = {"__builtins__": {}}
                    exec(st.session_state.current_plot_code, safe_globals, local_vars)

                    if "fig" in local_vars and local_vars["fig"] is not None:
                        st.plotly_chart(local_vars["fig"], use_container_width=True)
                    elif plt.get_fignums():
                        st.pyplot(plt.gcf())
                        plt.close('all')
                        
                    # --- PLOT-SPECIFIC Q&A ---
                    st.markdown("### 📈 Ask about this Plot")
                    
                    # Display chat history for the plot
                    for msg in st.session_state.plot_ui_chat:
                        with st.chat_message(msg["role"]):
                            st.markdown(msg["content"])
                            
                    # FIX: Use a form instead of chat_input to prevent layout skewing
                    with st.form(key="plot_qa_form", clear_on_submit=True):
                        col1, col2 = st.columns([5, 1])
                        with col1:
                            plot_query = st.text_input(
                                "Ask a question about the data in this chart...", 
                                label_visibility="collapsed",
                                placeholder="Ask a question about this specific chart..."
                            )
                        with col2:
                            submit_plot = st.form_submit_button("Ask 🤖", use_container_width=True)
                            
                    if submit_plot and plot_query:
                        # Display user message instantly
                        st.session_state.plot_ui_chat.append({"role": "user", "content": plot_query})
                        with st.chat_message("user"):
                            st.markdown(plot_query)
                            
                        # Run plot QA agent
                        with st.chat_message("assistant"):
                            with st.spinner("Analyzing plot data..."):
                                plot_deps = PlotDeps(
                                    df=df, 
                                    plot_type=st.session_state.current_plot_type, 
                                    plotted_columns=st.session_state.current_plot_params
                                )
                                plot_result = plot_qa_agent.run_sync(
                                    plot_query, 
                                    deps=plot_deps, 
                                    message_history=st.session_state.plot_qa_history
                                )
                                st.markdown(plot_result.output)
                                
                                # Save context
                                st.session_state.plot_qa_history.extend(plot_result.new_messages())
                                st.session_state.plot_ui_chat.append({"role": "assistant", "content": plot_result.output})

                except Exception as e:
                    st.error(f"❌ Failed to render plot: {e}")


            # ----------------------- General Q&A Agent -----------------------
            st.markdown("---")
            st.markdown("## 💬 General Dataset Q&A")
            st.markdown("Ask general questions about the entire dataset.")

            # Initialize history for General Q&A
            if "general_qa_history" not in st.session_state:
                st.session_state.general_qa_history = []  # For Pydantic AI Context
            if "general_ui_chat" not in st.session_state:
                st.session_state.general_ui_chat = []     # For Streamlit Rendering

            # Render existing chat
            for msg in st.session_state.general_ui_chat:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

            general_query = st.chat_input("Type your question (e.g., 'What is the average price?')")

            if general_query:
                # Add user message to UI
                st.session_state.general_ui_chat.append({"role": "user", "content": general_query})
                with st.chat_message("user"):
                    st.markdown(general_query)

                # Get Agent Response
                with st.chat_message("assistant"):
                    with st.spinner("Analyzing data to find your answer... 🤖"):
                        try:
                            qa_result = qa_agent.run_sync(
                                general_query, 
                                deps=DatasetDeps(df=df),
                                message_history=st.session_state.general_qa_history
                            )
                            st.markdown(qa_result.output)
                            
                            # Append history
                            st.session_state.general_qa_history.extend(qa_result.new_messages())
                            st.session_state.general_ui_chat.append({"role": "assistant", "content": qa_result.output})
                            
                        except Exception as e:
                            st.error(f"⚠️ Failed to get response: {e}")

    except Exception as e:
        st.error(f"⚠️ Failed to load dataset: {e}")