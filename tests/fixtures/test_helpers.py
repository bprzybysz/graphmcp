def create_mock_st_columns(num_columns: int):
    """
    A helper function to create a tuple of MagicMock objects for mocking
    streamlit.columns.
    
    This can be used in tests to avoid repetitive mocking code.
    """
    from unittest.mock import MagicMock
    return tuple(MagicMock() for _ in range(num_columns))
