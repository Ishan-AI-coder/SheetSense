import streamlit as st
from main import summarize_agent,plotting_agent,qa_agent
import matplotlib.pyplot as plt
import plotly.express as px
import pandas as pd
import asyncio



st.set_page_config(page_title="SheetSense", layout="wide")

# ----------------------- File Upload -----------------------
st.subheader("Upload your dataset")
uploaded_file = st.file_uploader("Upload a CSV or Excel file", type=["csv", "xlsx"])

df = None

if uploaded_file is not None:
    try:
        # Read file depending on extension
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith(".xlsx"):
            df = pd.read_excel(uploaded_file)
        else:
            st.error("Unsupported file format. Please upload CSV or Excel.")

        # Only display/preview if df is not None
        if df is not None:
            st.success(f"✅ Dataset loaded successfully with {df.shape[0]} rows and {df.shape[1]} columns")
            with st.expander("📄 Preview Dataset", expanded=False):
                st.dataframe(df.head(101))  # preview top 10 rows safely
            #Summarization Agent

            st.markdown('<div class="title"> 📝 SheetSense Summarizer</div>', unsafe_allow_html=True)
            # Create a rich, context-aware prompt
            user_prompt = f"""
            You are analyzing a dataset with {df.shape[0]} rows and {df.shape[1]} columns.
            The dataset has the following columns:
            {', '.join(df.columns.tolist())}.
            Provide a detailed summary including:
            - Overall dataset structure
            - Missing values (if any)
            - Key statistics and patterns
            - Actionable insights or observations

            Do not ask for the dataset again. Use the data provided via deps.
            """

            # Pass both the structured data and the context prompt
            with st.spinner("🧠 Analyzing dataset..."):
                summary = summarize_agent.run_sync(user_prompt, deps={"df": df})
    
            # Display the result
            st.markdown("### 📄 Summary")
            st.markdown(summary.output)
        
            

            #-------------------Plotting Agent------------------#
            # Custom CSS for styling
            st.markdown("""
            <style>
                .title {
                    font-size: 38px;
                    font-weight: bold;
                    color: #1f77b4;
                    text-align: center;
                    margin-bottom: 20px;
                }
                .subtitle {
                    font-size: 20px;
                    color: #333333;
                    margin-bottom: 10px;
                }
                .stButton>button {
                    background-color: #1f77b4;
                    color: white;
                    font-size: 18px;
                    padding: 10px;
                    border-radius: 8px;
                }
                .stSelectbox>div>div>select {
                    padding: 8px;
                    border-radius: 5px;
                    border: 1px solid #1f77b4;
                }
            </style>
            """, unsafe_allow_html=True)

            st.markdown('<div class="title">📊 SheetSense Plotter</div>', unsafe_allow_html=True)
            st.markdown('<div class="subtitle">Select the parameters and plot type to visualize your dataset</div>', unsafe_allow_html=True)
            

            # ----------------------- Helper: Sanitize Agent Code -----------------------
            def clean_plot_code(code: str) -> str:
                """
                Removes markdown code block syntax and plt.show() to prevent syntax errors.
                """
                return (
                    code.replace("```python", "")
                        .replace("```", "")
                        .replace("plt.show()", "")
                        .replace("plt.show()", "")
                        .strip()
                )

            # ----------------------- User Inputs -----------------------
            st.subheader("Plot Configuration")

            plot_types = ["Auto", "Histogram", "Bar Chart", "Pie Chart", "Line Chart", "Scatter Plot"]
            selected_plot = st.selectbox("Choose Plot Type (or Auto for agent decision)", plot_types)

            # Parameter selection
            all_columns = df.columns.tolist()
            if selected_plot in ["Histogram", "Line Chart"]:
                param1 = st.selectbox("Select 1 numerical column", [c for c in all_columns if df[c].dtype != 'object'])
                params = [param1]
            elif selected_plot == "Bar Chart":
                cat_col = st.selectbox("Select Categorical column", [c for c in all_columns if df[c].dtype == 'object'])
                num_col = st.selectbox("Select Numerical column", [c for c in all_columns if df[c].dtype != 'object'])
                params = [cat_col, num_col]
            elif selected_plot == "Pie Chart":
                cat_cols = st.multiselect("Select 1 or more categorical columns", [c for c in all_columns if df[c].dtype == 'object'])
                params = cat_cols
            elif selected_plot == "Scatter Plot":
                num1 = st.selectbox("Select first numerical column", [c for c in all_columns if df[c].dtype != 'object'])
                num2 = st.selectbox("Select second numerical column", [c for c in all_columns if df[c].dtype != 'object'])
                params = [num1, num2]
            else:
                # Auto
                param_auto = st.multiselect("Select columns (Agent decides plot type)", all_columns)
                params = param_auto

            # ----------------------- Run Agent -----------------------
            if st.button("Generate Plot"):
                if not params:
                    st.warning("Please select at least one column!")
                else:
                    user_input = f"Generate a {selected_plot} for columns: {', '.join(params)}"
                    with st.spinner("Generating plot..."):
                        result = plotting_agent.run_sync(user_input, deps=df)
                        plot_code = result.output

                        st.markdown("### 🧠 Generated Plot Code")

                        try:
                            cleaned_code = clean_plot_code(plot_code)
                            # Local namespace for safe execution
                            local_vars = {"df": df, "px": px}
                            exec(cleaned_code, globals(), local_vars)

                            # Display matplotlib plots
                            if plt.get_fignums():
                                st.pyplot(plt.gcf())
                                plt.close('all')

                            # Display Plotly plots
                            if "fig" in local_vars:
                                st.plotly_chart(local_vars["fig"], use_container_width=True)

                        except Exception as e:
                            st.error(f"❌ Failed to generate plot: {e}")
                            st.code(plot_code, language="python")
               


            # ----------------------- Q&A Agent-----------------------
            st.markdown("""
            <style>
            .title {
                font-size: 40px;
                font-weight: bold;
                color: #1f77b4;
                text-align: center;
                margin-bottom: 10px;
            }
            .subtitle {
                font-size: 18px;
                text-align: center;
                color: #444;
                margin-bottom: 30px;
            }
            .stButton>button {
                background-color: #1f77b4;
                color: white;
                font-size: 18px;
                font-weight: 500;
                border-radius: 10px;
                padding: 10px 24px;
                transition: all 0.3s ease;
            }
            .stButton>button:hover {
                background-color: #155a8a;
            }
            .stTextInput>div>div>input {
                border: 1px solid #1f77b4;
                border-radius: 8px;
                padding: 10px;
            }
            .result-box {
                background-color: #e9f2fb;  /* soft blue for contrast */
                border: 1px solid #bcd3ea;
                border-radius: 10px;
                padding: 20px;
                margin-top: 15px;
                color: #0d2b45;  /* dark blue text for readability */
                font-size: 17px;
                line-height: 1.6;
                box-shadow: 0 4px 12px rgba(0,0,0,0.08);
                animation: fadeIn 0.5s ease-in-out;
            }
            @keyframes fadeIn {
                from {opacity: 0; transform: translateY(5px);}
                to {opacity: 1; transform: translateY(0);}
            }
            footer {visibility: hidden;}
            </style>
            """, unsafe_allow_html=True)

            # ----------------------- Header -----------------------
            st.markdown('<div class="title">💬 SheetSense Q&A Agent</div>', unsafe_allow_html=True)
            st.markdown('<div class="subtitle">Ask questions about your dataset or get data-driven suggestions</div>', unsafe_allow_html=True)
            # ----------------------- User Input -----------------------
            st.subheader("Ask a Question")
            user_query = st.text_input("Type your question about the dataset (e.g., 'Which product sold the most?' or 'What is the average age?')")

            # ----------------------- Agent Response -----------------------
            if st.button("Get Answer"):
                if not user_query.strip():
                    st.warning("Please enter a valid question.")
                else:
                    with st.spinner("Analyzing dataset and generating response... 🤖"):
                        try:
                            async def ask_agent():
                                return await qa_agent.run(user_query, deps=df)

                            try:
                                response = qa_agent.run_sync(user_query, deps={"df": df})

                                if response:
                                    st.markdown("### 🤖 Agent Response")
                                    st.markdown(f"<div class='agent-response'>{response.output}</div>", unsafe_allow_html=True)

                                    # ---------------- Display Response ----------------
                                    st.markdown("### 🧠 Agent Response")
                                    st.markdown(f'<div class="result-box">{response}</div>', unsafe_allow_html=True)
                            except Exception as e:
                                st.error(f"⚠️ Failed to get response: {e}")
                        except Exception as e:
                            st.error(f"⚠️ Failed to get response: {e}")          

    except Exception as e:
        st.error(f"⚠️ Failed to load dataset: {e}")


#-------------------Plotting Agent------------------#
# # Custom CSS for styling
# st.markdown("""
# <style>
#     .title {
#         font-size: 38px;
#         font-weight: bold;
#         color: #1f77b4;
#         text-align: center;
#         margin-bottom: 20px;
#     }
#     .subtitle {
#         font-size: 20px;
#         color: #333333;
#         margin-bottom: 10px;
#     }
#     .stButton>button {
#         background-color: #1f77b4;
#         color: white;
#         font-size: 18px;
#         padding: 10px;
#         border-radius: 8px;
#     }
#     .stSelectbox>div>div>select {
#         padding: 8px;
#         border-radius: 5px;
#         border: 1px solid #1f77b4;
#     }
# </style>
# """, unsafe_allow_html=True)

# st.markdown('<div class="title">📊 SheetSense Plotter</div>', unsafe_allow_html=True)
# st.markdown('<div class="subtitle">Select the parameters and plot type to visualize your dataset</div>', unsafe_allow_html=True)

# # ----------------------- Dataset Preview -----------------------
# st.subheader("Dataset Preview")
# st.dataframe(df.head(10))

# # ----------------------- Helper: Sanitize Agent Code -----------------------
# def clean_plot_code(code: str) -> str:
#     """
#     Removes markdown code block syntax and plt.show() to prevent syntax errors.
#     """
#     return (
#         code.replace("```python", "")
#             .replace("```", "")
#             .replace("plt.show()", "")
#             .replace("plt.show()", "")
#             .strip()
#     )

# # ----------------------- User Inputs -----------------------
# st.subheader("Plot Configuration")

# plot_types = ["Auto", "Histogram", "Bar Chart", "Pie Chart", "Line Chart", "Scatter Plot"]
# selected_plot = st.selectbox("Choose Plot Type (or Auto for agent decision)", plot_types)

# # Parameter selection
# all_columns = df.columns.tolist()
# if selected_plot in ["Histogram", "Line Chart"]:
#     param1 = st.selectbox("Select 1 numerical column", [c for c in all_columns if df[c].dtype != 'object'])
#     params = [param1]
# elif selected_plot == "Bar Chart":
#     cat_col = st.selectbox("Select Categorical column", [c for c in all_columns if df[c].dtype == 'object'])
#     num_col = st.selectbox("Select Numerical column", [c for c in all_columns if df[c].dtype != 'object'])
#     params = [cat_col, num_col]
# elif selected_plot == "Pie Chart":
#     cat_cols = st.multiselect("Select 1 or more categorical columns", [c for c in all_columns if df[c].dtype == 'object'])
#     params = cat_cols
# elif selected_plot == "Scatter Plot":
#     num1 = st.selectbox("Select first numerical column", [c for c in all_columns if df[c].dtype != 'object'])
#     num2 = st.selectbox("Select second numerical column", [c for c in all_columns if df[c].dtype != 'object'])
#     params = [num1, num2]
# else:
#     # Auto
#     param_auto = st.multiselect("Select columns (Agent decides plot type)", all_columns)
#     params = param_auto

# # ----------------------- Run Agent -----------------------
# if st.button("Generate Plot"):
#     if not params:
#         st.warning("Please select at least one column!")
#     else:
#         user_input = f"Generate a {selected_plot} for columns: {', '.join(params)}"
#         with st.spinner("Generating plot..."):
#             result = plotting_agent.run_sync(user_input, deps=df)
#             plot_code = result.output

#             st.markdown("### 🧠 Generated Plot Code")
            
#             try:
#                 cleaned_code = clean_plot_code(plot_code)
#                 local_vars = {"df": df, "plt": plt, "px": px}
#                 exec(cleaned_code, {}, local_vars)

#                 # Display matplotlib plots
#                 if plt.get_fignums():
#                     st.pyplot(plt.gcf())
#                     plt.close('all')

#                 # Display Plotly plots
#                 if "fig" in local_vars:
#                     st.plotly_chart(local_vars["fig"], use_container_width=True)

#             except Exception as e:
#                 st.error(f"❌ Failed to generate plot: {e}")
#                 st.code(plot_code, language="python")
               


# # ----------------------- Q&A Agent-----------------------
# st.markdown("""
# <style>
# .title {
#     font-size: 40px;
#     font-weight: bold;
#     color: #1f77b4;
#     text-align: center;
#     margin-bottom: 10px;
# }
# .subtitle {
#     font-size: 18px;
#     text-align: center;
#     color: #444;
#     margin-bottom: 30px;
# }
# .stButton>button {
#     background-color: #1f77b4;
#     color: white;
#     font-size: 18px;
#     font-weight: 500;
#     border-radius: 10px;
#     padding: 10px 24px;
#     transition: all 0.3s ease;
# }
# .stButton>button:hover {
#     background-color: #155a8a;
# }
# .stTextInput>div>div>input {
#     border: 1px solid #1f77b4;
#     border-radius: 8px;
#     padding: 10px;
# }
# .result-box {
#     background-color: #e9f2fb;  /* soft blue for contrast */
#     border: 1px solid #bcd3ea;
#     border-radius: 10px;
#     padding: 20px;
#     margin-top: 15px;
#     color: #0d2b45;  /* dark blue text for readability */
#     font-size: 17px;
#     line-height: 1.6;
#     box-shadow: 0 4px 12px rgba(0,0,0,0.08);
#     animation: fadeIn 0.5s ease-in-out;
# }
# @keyframes fadeIn {
#     from {opacity: 0; transform: translateY(5px);}
#     to {opacity: 1; transform: translateY(0);}
# }
# footer {visibility: hidden;}
# </style>
# """, unsafe_allow_html=True)

# # ----------------------- Header -----------------------
# st.markdown('<div class="title">💬 SheetSense Q&A Agent</div>', unsafe_allow_html=True)
# st.markdown('<div class="subtitle">Ask questions about your dataset or get data-driven suggestions</div>', unsafe_allow_html=True)

# # ----------------------- Dataset Preview -----------------------
# with st.expander("📄 Preview Dataset", expanded=False):
#     st.dataframe(df.head(101))

# # ----------------------- User Input -----------------------
# st.subheader("Ask a Question")
# user_query = st.text_input("Type your question about the dataset (e.g., 'Which product sold the most?' or 'What is the average age?')")

# # ----------------------- Agent Response -----------------------
# if st.button("Get Answer"):
#     if not user_query.strip():
#         st.warning("Please enter a valid question.")
#     else:
#         with st.spinner("Analyzing dataset and generating response... 🤖"):
#             try:
#                 result = qa_agent.run_sync(user_query, deps={"df": df})
#                 response = result.output

#                 # ---------------- Display Response ----------------
#                 st.markdown("### 🧠 Agent Response")
#                 st.markdown(f'<div class="result-box">{response}</div>', unsafe_allow_html=True)

#             except Exception as e:
#                 st.error(f"⚠️ Failed to get response: {e}")