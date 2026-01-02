import pandas as pd
from langchain_core.tools import tool
from typing import Optional

# Global DataFrame storage (set by API)
_dataframe: Optional[pd.DataFrame] = None


def set_dataframe(df: pd.DataFrame):
    global _dataframe
    _dataframe = df


def get_dataframe() -> Optional[pd.DataFrame]:
    return _dataframe


@tool
def get_data_info() -> str:
    """Get information about the uploaded data including columns, types, and sample rows."""
    if _dataframe is None:
        return "No data uploaded yet."

    info = []
    info.append(f"Shape: {_dataframe.shape[0]} rows, {_dataframe.shape[1]} columns")
    info.append(f"\nColumns and types:")
    for col in _dataframe.columns:
        info.append(f"  - {col}: {_dataframe[col].dtype}")
    info.append(f"\nFirst 3 rows:\n{_dataframe.head(3).to_string()}")
    return "\n".join(info)


@tool
def run_analysis(code: str) -> str:
    """Execute pandas code on the uploaded DataFrame.
    The DataFrame is available as 'df'.
    Use print() to output results.
    Example: print(df.groupby('category')['amount'].sum())
    """
    if _dataframe is None:
        return "No data uploaded yet."

    import io
    import sys

    output = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = output

    try:
        local_vars = {"df": _dataframe, "pd": pd}
        exec(code, {"__builtins__": __builtins__}, local_vars)
        result = output.getvalue()
        if not result.strip():
            # If nothing was printed, try to get the last expression value
            result = "Code executed successfully (no output)"
    except Exception as e:
        result = f"Error: {str(e)}"
    finally:
        sys.stdout = old_stdout

    return result


@tool
def get_column_stats(column: str) -> str:
    """Get statistics for a specific column (sum, mean, min, max, etc.)."""
    if _dataframe is None:
        return "No data uploaded yet."

    if column not in _dataframe.columns:
        return f"Column '{column}' not found. Available: {list(_dataframe.columns)}"

    col = _dataframe[column]

    if pd.api.types.is_numeric_dtype(col):
        stats = {
            "count": col.count(),
            "sum": col.sum(),
            "mean": col.mean(),
            "min": col.min(),
            "max": col.max(),
            "std": col.std(),
        }
        return f"Statistics for '{column}':\n" + "\n".join(
            f"  {k}: {v}" for k, v in stats.items()
        )
    else:
        return f"Value counts for '{column}':\n{col.value_counts().to_string()}"


def get_pandas_tools():
    return [get_data_info, run_analysis, get_column_stats]
