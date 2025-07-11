# don_concrete/ui/config/theme.py

# It's more conventional to set the theme in the .streamlit/config.toml file.
# However, this file can serve as a central place to define theme colors
# if we need to use them in custom CSS or components.

THEME_SETTINGS = {
    "primaryColor": "#7792E3",
    "backgroundColor": "#0E1117",
    "secondaryBackgroundColor": "#262730",
    "textColor": "#FAFAFA",
    "font": "sans serif"
}

# To apply this theme, you would typically copy these settings into
# .streamlit/config.toml like this:
#
# [theme]
# primaryColor="#7792E3"
# backgroundColor="#0E1117"
# secondaryBackgroundColor="#262730"
# textColor="#FAFAFA"
# font="sans serif"
