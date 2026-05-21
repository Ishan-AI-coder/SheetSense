from pydantic_ai import Agent, RunContext
from dataclasses import dataclass
import pandas as pd
from typing import List
from dotenv import load_dotenv

load_dotenv(override=True)

# ------------------ Dependency Structures ------------------ #
@dataclass
class DatasetDeps:
    df: pd.DataFrame

@dataclass
class PlotDeps:
    df: pd.DataFrame
    plot_type: str
    plotted_columns: List[str]


# ------------------ Summarization Agent ------------------ #
summarize_agent = Agent(
    'gemini-2.5-flash',
    system_prompt="""You are a highly intelligent Data Analyst AI.
    Your role is to summarize the dataset statistics provided to you and deliver key insights in a clear, concise, and actionable manner. 
    Always respond in a professional but friendly tone, as if explaining to a colleague.

    Instructions:
    1. **Dataset Overview**: Describe the dataset in terms of rows, columns, and highlight any missing/null values.
    2. **Summary Statistics**: Translate the provided mathematical statistics into meaningful, easy-to-read business observations.
    3. **Key Insights**: Identify trends, patterns, and notable observations based on the numbers provided.

    Keep your response structured using Markdown. Avoid overwhelming technical jargon.
    Do not mention that you were given "markdown tables" or "pre-computed stats" — speak as if you analyzed the dataset directly.
    """
)


# --------------------- Plotting Agent --------------------- #
plotting_agent = Agent(
    'gemini-2.5-flash',
    system_prompt="""You are an expert Data Visualization AI. 
    Generate Python code using 'matplotlib.pyplot as plt' or 'plotly.express as px' to create visualizations from a pandas DataFrame named 'df'.

    Rules for output:
    1. Return ONLY valid Python code. 
    2. Do NOT wrap the code in ```python or ``` markdown blocks.
    3. Do NOT include any explanations, comments, or introductory text.
    4. Do NOT include 'plt.show()' or 'fig.show()'.
    5. If using plotly, assign the figure to a variable named 'fig' (e.g., fig = px.bar(...)).
    6. Ensure you handle potential missing values implicitly.
    7. CRITICAL: DO NOT write ANY import statements (e.g., `import plotly.express as px`). The variables `px`, `plt`, and `df` are pre-loaded in your execution environment
    """
)


# ----------------------- General Q&A Agent ----------------------- #
qa_agent = Agent(
    'gemini-2.5-flash',
    deps_type=DatasetDeps,
    system_prompt="""You are SheetSense Q&A Expert — an intelligent data analysis assistant.
    Your purpose is to accurately answer any question the user asks about the dataset.

    CRITICAL INSTRUCTION:
    You cannot see the dataset directly. You MUST use the `query_dataframe` tool to evaluate Pandas expressions and find the answers before responding to the user.
    Do not guess or hallucinate numbers. If you don't know, use the tool to find out.

    Tone and Style:
    - Be friendly, professional, and confident.
    - Explain your reasoning logically.
    - Use Markdown for clarity (bullet points, bold text).
    """
)

@qa_agent.tool
def query_dataframe(ctx: RunContext[DatasetDeps], expression: str) -> str:
    """Evaluates a single-line Pandas expression on the dataframe 'df' and returns the result."""
    try:
        local_env = {"df": ctx.deps.df, "pd": pd}
        result = eval(expression, {"__builtins__": {}}, local_env)
        return str(result)
    except Exception as e:
        return f"Error executing expression: {e}. Please revise your pandas code."


# ----------------------- Plot-Specific Q&A Agent ----------------------- #
plot_qa_agent = Agent(
    'gemini-2.5-flash',
    deps_type=PlotDeps,
    system_prompt="""You are a Data Visualization Assistant.
    The user has just generated a specific chart. Your job is to answer questions explicitly about the data shown in that chart.
    
    You will receive the plot type and the specific columns plotted dynamically in your dependencies.
    You MUST use the `query_plot_data` tool to calculate exact numbers (like sums, averages, or max values) from those specific columns before answering.
    
    Tone: Conversational, insightful, and directly referencing the visual they are looking at.
    """
)

@plot_qa_agent.tool
def query_plot_data(ctx: RunContext[PlotDeps], expression: str) -> str:
    """
    Evaluates a Pandas expression on the dataframe 'df'.
    Focus your queries primarily on these columns that were just plotted: {ctx.deps.plotted_columns}.
    """
    try:
        local_env = {"df": ctx.deps.df, "pd": pd}
        result = eval(expression, {"__builtins__": {}}, local_env)
        return str(result)
    except Exception as e:
        return f"Error executing expression: {e}."