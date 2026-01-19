# eSett Price Data Viewer

Interactive Streamlit application for visualizing price data from the eSett OpenData API.

## Features

- 📊 Interactive price charts using Plotly
- 🌍 Support for multiple Market Balance Areas (Sweden, Finland, Norway, Denmark)
- 📈 Multiple price types: Imbalance Sales/Purchase, Up/Down Regulation
- 📅 Customizable date ranges
- 💾 CSV export functionality

## Live Demo

[View on Streamlit Cloud](your-app-url-here)

## Local Development

1. Clone the repository:
```bash
git clone https://github.com/yourusername/esett-viewer.git
cd esett-viewer
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the app:
```bash
streamlit run app.py
```

## Data Source

Data is fetched from the [eSett OpenData API](https://api.opendata.esett.com).

## License

MIT
