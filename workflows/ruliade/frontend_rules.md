# Frontend Development Rules (Streamlit + Plotly)

## Streamlit Application Architecture

### State Management
- **Use `st.session_state` for persistent data across reruns**
  ```python
  # Initialize state variables safely
  if 'counter' not in st.session_state:
      st.session_state.counter = 0
  
  # Update state through callbacks
  def increment():
      st.session_state.counter += 1
  
  st.button("Increment", on_click=increment)
  ```

- **Prefer `st.cache_data` for data caching**
  ```python
  @st.cache_data
  def load_data(file_path: str) -> pd.DataFrame:
      return pd.read_csv(file_path)
  ```

- **Use `st.cache_resource` for expensive resources**
  ```python
  @st.cache_resource
  def init_model():
      return load_ml_model()
  ```

### Layout and Structure
- **Use columns for responsive layouts**
  ```python
  col1, col2, col3 = st.columns([2, 1, 1])
  with col1:
      st.plotly_chart(main_chart, use_container_width=True)
  with col2:
      st.metric("Total", value)
  ```

- **Implement sidebar for controls**
  ```python
  with st.sidebar:
      filter_option = st.selectbox("Filter", options)
      date_range = st.date_input("Date Range", value=[start, end])
  ```

- **Use containers for logical grouping**
  ```python
  with st.container():
      st.header("Data Analysis")
      # Related widgets and displays
  ```

### Form Handling
- **Group related inputs in forms**
  ```python
  with st.form("data_input"):
      name = st.text_input("Name")
      age = st.number_input("Age", min_value=0)
      submitted = st.form_submit_button("Submit")
      
      if submitted:
          process_data(name, age)
  ```

## Plotly Integration

### Chart Creation Standards
- **Use `plotly.graph_objects` for complex charts**
  ```python
  import plotly.graph_objects as go
  
  fig = go.Figure()
  fig.add_trace(go.Scatter(x=x_data, y=y_data, name="Series"))
  fig.update_layout(
      title="Chart Title",
      xaxis_title="X Axis",
      yaxis_title="Y Axis"
  )
  ```

- **Use `plotly.express` for quick visualizations**
  ```python
  import plotly.express as px
  
  fig = px.scatter(df, x="column1", y="column2", color="category")
  ```

### Interactive Features
- **Enable hover information**
  ```python
  fig.update_traces(
      hovertemplate="<b>%{x}</b><br>Value: %{y}<extra></extra>"
  )
  ```

- **Add range selectors for time series**
  ```python
  fig.update_layout(
      xaxis=dict(
          rangeselector=dict(
              buttons=list([
                  dict(count=7, label="7d", step="day", stepmode="backward"),
                  dict(count=30, label="30d", step="day", stepmode="backward"),
                  dict(step="all")
              ])
          ),
          rangeslider=dict(visible=True),
          type="date"
      )
  )
  ```

### Chart Performance
- **Use `use_container_width=True` for responsive charts**
  ```python
  st.plotly_chart(fig, use_container_width=True)
  ```

- **Optimize large datasets with sampling**
  ```python
  if len(df) > 10000:
      df_sample = df.sample(n=5000)
  else:
      df_sample = df
  ```

## Data Visualization Patterns

### Dashboard Layout
- **Create metric tiles for KPIs**
  ```python
  col1, col2, col3, col4 = st.columns(4)
  col1.metric("Revenue", f"${revenue:,.0f}", delta=f"{revenue_change:.1%}")
  col2.metric("Orders", f"{orders:,}", delta=f"{order_change:+d}")
  ```

- **Use tabs for different views**
  ```python
  tab1, tab2, tab3 = st.tabs(["Overview", "Details", "Settings"])
  with tab1:
      # Overview content
  with tab2:
      # Detailed analysis
  ```

### Chart Types Guidelines
- **Line charts for time series**
  ```python
  fig = px.line(df, x="date", y="value", color="category")
  ```

- **Bar charts for categorical comparisons**
  ```python
  fig = px.bar(df, x="category", y="value", color="subcategory")
  ```

- **Scatter plots for correlations**
  ```python
  fig = px.scatter(df, x="feature1", y="feature2", size="size_col", color="color_col")
  ```

## Error Handling and User Experience

### Input Validation
- **Validate user inputs early**
  ```python
  if uploaded_file is not None:
      try:
          df = pd.read_csv(uploaded_file)
          if df.empty:
              st.error("Uploaded file is empty")
              st.stop()
      except Exception as e:
          st.error(f"Error reading file: {str(e)}")
          st.stop()
  ```

### Loading States
- **Show progress for long operations**
  ```python
  with st.spinner("Loading data..."):
      data = expensive_operation()
  
  # Or with progress bar
  progress_bar = st.progress(0)
  for i in range(100):
      # Update progress
      progress_bar.progress(i + 1)
  ```

### Error Messages
- **Provide clear, actionable error messages**
  ```python
  try:
      result = risky_operation()
  except ValueError as e:
      st.error(f"Invalid input: {str(e)}")
      st.info("Please check your data format and try again")
  except Exception as e:
      st.error("An unexpected error occurred")
      st.exception(e)  # Only in development
  ```

## Performance Best Practices

### Caching Strategy
- **Cache expensive computations**
  ```python
  @st.cache_data(ttl=3600)  # Cache for 1 hour
  def process_large_dataset(df):
      return df.groupby("category").agg({"value": "sum"})
  ```

- **Use hash functions for complex objects**
  ```python
  @st.cache_data
  def process_data(_df, config_dict):
      # Use _df to skip hashing of DataFrame
      return expensive_processing(_df, config_dict)
  ```

### Memory Management
- **Clear large objects when done**
  ```python
  # Process data
  large_df = load_large_dataset()
  result = process_data(large_df)
  
  # Clear from memory
  del large_df
  ```

## Testing Frontend Components

### Streamlit Testing
- **Test app logic separately from UI**
  ```python
  def test_data_processing():
      # Test the business logic
      result = process_user_input(test_data)
      assert result.shape[0] > 0
  ```

- **Use `AppTest` for integration testing**
  ```python
  from streamlit.testing.v1 import AppTest
  
  def test_app():
      at = AppTest.from_file("app.py")
      at.run()
      assert not at.exception
  ```

## Security Considerations

### Input Sanitization
- **Validate file uploads**
  ```python
  if uploaded_file.type not in ["text/csv", "application/json"]:
      st.error("Only CSV and JSON files are allowed")
      st.stop()
  ```

- **Sanitize user inputs for display**
  ```python
  import html
  safe_input = html.escape(user_input)
  ```

### Environment Variables
- **Use st.secrets for sensitive data**
  ```python
  api_key = st.secrets["api_key"]
  ```

## Code Organization

### File Structure
```
streamlit_app/
├── pages/
│   ├── 1_📊_Dashboard.py
│   ├── 2_📈_Analysis.py
│   └── 3_⚙️_Settings.py
├── utils/
│   ├── data_processing.py
│   ├── chart_helpers.py
│   └── config.py
├── components/
│   ├── sidebar.py
│   └── metrics.py
└── main.py
```

### Modular Components
- **Extract reusable chart functions**
  ```python
  def create_time_series_chart(df, x_col, y_col, title):
      fig = px.line(df, x=x_col, y=y_col, title=title)
      fig.update_layout(showlegend=False)
      return fig
  ```

- **Create custom components**
  ```python
  def metric_card(title, value, delta=None):
      col1, col2 = st.columns([3, 1])
      col1.metric(title, value, delta)
      return col1, col2
  ``` 