# Binance Historical Data Extractor

A user-friendly desktop application for retrieving, visualizing and saving historical cryptocurrency data from Binance.

![App Screenshot](screenshot.png)  <!-- You can add a screenshot later -->

## Features

-   Modern, dark-themed interface.
-   Search for any trading pair available on Binance.
-   Select different time intervals (from minutes to days).
-   Specify a date range for the historical data.
-   Visualize the data as a candlestick chart.
-   Download the retrieved data as a CSV file.
-   Securely manage your Binance API keys.

## Setup and Installation

Follow these steps to get the application running on your local machine.

### 1. Prerequisites

-   Python 3.x
-   Git

### 2. Clone the Repository

Clone this repository to your local machine:

```bash
git clone <repository-url>
cd Binance-Historical-Data-Extractor
```

### 3. Set Up a Virtual Environment

It's highly recommended to use a virtual environment to manage project dependencies.

```bash
# Create the virtual environment
python -m venv venv

# Activate the environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 4. Install Dependencies

Install the required Python packages using pip:

```bash
pip install -r requirements.txt
```

### 5. Configure API Keys

The application requires a Binance API key and secret to fetch data.

1.  **Create a `.env` file** in the root of the project directory. You can do this by copying the example file:
    ```bash
    # On Windows:
    copy .env.example .env
    # On macOS/Linux:
    cp .env.example .env
    ```

2.  **Obtain your API credentials:**
    -   Log in to your Binance account.
    -   Navigate to **API Management** in your account settings.
    -   Create a new API key.
    -   Ensure the key has permissions for **Enable Reading**.
    -   Copy the **API Key** and **Secret Key**.

3.  **Add your credentials to the `.env` file:**
    Open the `.env` file and paste your keys into the corresponding fields:
    ```
    BINANCE_API_KEY="YOUR_API_KEY_HERE"
    BINANCE_API_SECRET="YOUR_SECRET_KEY_HERE"
    ```

## How to Run

With your virtual environment activated and your `.env` file configured, run the application with the following command:

```bash
python app.py
```

The application window will open, and you can start retrieving data. If your API keys are missing, a settings window will pop up to guide you.
