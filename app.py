import os
import threading
import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from binance.client import Client
from dotenv import load_dotenv, set_key
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
from PIL import Image, ImageTk
import io

# --- Environment Variable Handling ---
def load_env_variables():
    """Loads API keys from .env file."""
    load_dotenv()
    return os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET')

# --- API Client ---
API_KEY, API_SECRET = load_env_variables()
client = Client(API_KEY, API_SECRET)

# --- CSV Folder ---
csv_folder = os.path.join(os.getcwd(), 'data')
if not os.path.exists(csv_folder):
    os.makedirs(csv_folder)

# --- Settings Window ---
class SettingsWindow(ttk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Manage API Key")
        self.parent = parent
        self.geometry("400x200")
        self.transient(parent)

        frame = ttk.Frame(self, padding=20)
        frame.pack(fill=BOTH, expand=True)

        ttk.Label(frame, text="API Key:").grid(row=0, column=0, sticky=W, pady=5)
        self.api_key_entry = ttk.Entry(frame, width=40)
        self.api_key_entry.grid(row=0, column=1, pady=5)

        ttk.Label(frame, text="API Secret:").grid(row=1, column=0, sticky=W, pady=5)
        self.api_secret_entry = ttk.Entry(frame, width=40, show="*")
        self.api_secret_entry.grid(row=1, column=1, pady=5)

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=20)
        
        save_button = ttk.Button(button_frame, text="Save", command=self.save_keys, bootstyle=SUCCESS)
        save_button.pack(side=LEFT, padx=10)
        
        cancel_button = ttk.Button(button_frame, text="Cancel", command=self.destroy, bootstyle=SECONDARY)
        cancel_button.pack(side=LEFT, padx=10)

        self.load_keys()

    def load_keys(self):
        api_key, api_secret = load_env_variables()
        if api_key:
            self.api_key_entry.insert(0, api_key)
        if api_secret:
            self.api_secret_entry.insert(0, api_secret)

    def save_keys(self):
        key = self.api_key_entry.get()
        secret = self.api_secret_entry.get()

        if not key or not secret:
            messagebox.showerror("Error", "Both API Key and Secret are required.", parent=self)
            return

        dotenv_path = os.path.join(os.getcwd(), '.env')
        set_key(dotenv_path, 'BINANCE_API_KEY', key)
        set_key(dotenv_path, 'BINANCE_API_SECRET', secret)
        
        self.parent.update_client(key, secret)
        
        messagebox.showinfo("Success", "API Key has been saved.", parent=self)
        self.destroy()

# --- Main Application Class ---
class BinanceApp(ttk.Window):
    def __init__(self):
        super().__init__(themename="darkly")
        self.title("Binance Historical Data Extractor")
        self.state('zoomed')
        
        self.selected_pair = None
        self.df = None
        self.chart_image = None

        self.create_menu()
        self.create_widgets()
        
        self.after(100, self.check_api_key_on_startup)
        self.update_trading_pairs()

    def create_menu(self):
        menu_bar = ttk.Menu(self)
        self.config(menu=menu_bar)
        settings_menu = ttk.Menu(menu_bar, tearoff=False)
        menu_bar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Manage API Key", command=self.open_settings)

    def open_settings(self):
        SettingsWindow(self)

    def check_api_key_on_startup(self):
        api_key, api_secret = load_env_variables()
        if not api_key or not api_secret:
            instructions = (
                "Your Binance API Key is missing.\n\n"
                "To obtain your credentials:\n"
                "1. Log in to your Binance account.\n"
                "2. Go to 'API Management' in your account settings.\n"
                "3. Create a new API key.\n"
                "4. Ensure the key has permissions for 'Enable Reading'.\n"
                "5. Copy the API Key and Secret Key into the settings.\n\n"
                "Please enter your key in the Settings menu."
            )
            messagebox.showwarning("API Key Missing", instructions)
            self.open_settings()

    def update_client(self, key, secret):
        global client
        client = Client(key, secret)
        self.update_trading_pairs()

    def create_widgets(self):
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=BOTH, expand=True)

        controls_frame = ttk.Frame(main_frame)
        controls_frame.pack(side=LEFT, fill=Y, padx=(0, 20))

        search_frame = ttk.Labelframe(controls_frame, text="Search Trading Pair", padding=10)
        search_frame.pack(fill=X, pady=5)
        self.search_entry = ttk.Entry(search_frame)
        self.search_entry.pack(fill=X)
        self.search_entry.bind('<KeyRelease>', self.filter_trading_pairs)

        listbox_frame = ttk.Labelframe(controls_frame, text="Trading Pairs", padding=10)
        listbox_frame.pack(fill=BOTH, expand=True, pady=5)
        self.trading_pairs_listbox = tk.Listbox(listbox_frame, height=15, bg="#303030", fg="white", selectbackground="#007bff", selectforeground="white", borderwidth=0, highlightthickness=0)
        self.trading_pairs_listbox.pack(fill=BOTH, expand=True)
        self.trading_pairs_listbox.bind('<<ListboxSelect>>', self.on_pair_select)

        params_frame = ttk.Labelframe(controls_frame, text="Parameters", padding=10)
        params_frame.pack(fill=X, pady=5)

        ttk.Label(params_frame, text="Interval:").grid(row=0, column=0, sticky=W, pady=2)
        self.interval_var = tk.StringVar(value='1d')
        self.interval_dropdown = ttk.Combobox(params_frame, textvariable=self.interval_var, values=['1m', '5m', '15m', '1h', '4h', '1d'])
        self.interval_dropdown.grid(row=0, column=1, sticky=EW, pady=2)

        ttk.Label(params_frame, text="Start Date:").grid(row=1, column=0, sticky=W, pady=2)
        default_start = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        self.start_date_entry = ttk.Entry(params_frame)
        self.start_date_entry.insert(0, default_start)
        self.start_date_entry.grid(row=1, column=1, sticky=EW, pady=2)

        ttk.Label(params_frame, text="End Date:").grid(row=2, column=0, sticky=W, pady=2)
        default_end = datetime.now().strftime('%Y-%m-%d')
        self.end_date_entry = ttk.Entry(params_frame)
        self.end_date_entry.insert(0, default_end)
        self.end_date_entry.grid(row=2, column=1, sticky=EW, pady=2)
        params_frame.columnconfigure(1, weight=1)

        actions_frame = ttk.Frame(controls_frame)
        actions_frame.pack(fill=X, pady=10)
        self.retrieve_button = ttk.Button(actions_frame, text="Retrieve Data", command=self.retrieve_data, bootstyle=SUCCESS)
        self.retrieve_button.pack(side=LEFT, expand=True, fill=X, padx=(0, 5))
        self.csv_button = ttk.Button(actions_frame, text="Download CSV", command=self.download_csv, bootstyle=INFO, state="disabled")
        self.csv_button.pack(side=LEFT, expand=True, fill=X, padx=(5, 0))

        self.progress = ttk.Progressbar(controls_frame, orient="horizontal", mode="indeterminate")
        self.progress.pack(fill=X, pady=5)

        self.chart_frame = ttk.Labelframe(main_frame, text="Price Chart", padding=10)
        self.chart_frame.pack(side=LEFT, fill=BOTH, expand=True)
        self.chart_label = ttk.Label(self.chart_frame, text="No data to display.", anchor=CENTER)
        self.chart_label.pack(fill=BOTH, expand=True)

    def update_trading_pairs(self):
        try:
            self.trading_pairs = self.get_trading_pairs()
            self.filtered_pairs = self.trading_pairs.copy()
            self.update_listbox()
        except Exception:
            self.trading_pairs = []
            self.filtered_pairs = []
            self.update_listbox()

    def get_trading_pairs(self):
        exchange_info = client.get_exchange_info()
        symbols = [s['symbol'] for s in exchange_info['symbols'] if s['status'] == 'TRADING']
        return sorted(symbols)

    def filter_trading_pairs(self, event=None):
        query = self.search_entry.get().lower()
        self.filtered_pairs = [p for p in self.trading_pairs if query in p.lower()]
        self.update_listbox()

    def update_listbox(self):
        self.trading_pairs_listbox.delete(0, tk.END)
        for pair in self.filtered_pairs:
            self.trading_pairs_listbox.insert(tk.END, pair)
        if self.selected_pair in self.filtered_pairs:
            idx = self.filtered_pairs.index(self.selected_pair)
            self.trading_pairs_listbox.selection_set(idx)

    def on_pair_select(self, event):
        if self.trading_pairs_listbox.curselection():
            self.selected_pair = self.trading_pairs_listbox.get(self.trading_pairs_listbox.curselection())

    def retrieve_data(self):
        if not self.trading_pairs_listbox.curselection():
            messagebox.showerror("Error", "Please select a trading pair.")
            return
        self.selected_pair = self.trading_pairs_listbox.get(self.trading_pairs_listbox.curselection())
        
        self.retrieve_button.config(state="disabled")
        self.csv_button.config(state="disabled")
        self.chart_label.config(text="Retrieving data...")
        self.progress.start()
        
        threading.Thread(target=self.fetch_data, daemon=True).start()

    def fetch_data(self):
        try:
            pair = self.selected_pair
            interval = self.interval_var.get()
            start = self.start_date_entry.get()
            end = self.end_date_entry.get()
            
            klines = client.get_historical_klines(pair, interval, start, end)
            self.df = pd.DataFrame(klines, columns=['Open Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close Time', 'Quote Asset Volume', 'Number of Trades', 'Taker Buy Base Asset Volume', 'Taker Buy Quote Asset Volume', 'Ignore'])
            self.df['Open Time'] = pd.to_datetime(self.df['Open Time'], unit='ms')
            self.df.dropna(subset=['Open Time'], inplace=True)
            for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
                self.df[col] = pd.to_numeric(self.df[col])
            
            self.after(0, self.plot_data)
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", f"Failed to retrieve data: {e}"))
        finally:
            self.after(0, self.enable_buttons)

    def plot_data(self):
        if self.df is None or self.df.empty:
            self.chart_label.config(text="No data to display.")
            return

        df_plot = self.df.copy()
        df_plot['Open Time Str'] = df_plot['Open Time'].dt.strftime('%Y-%m-%d %H:%M')

        fig = go.Figure(data=[go.Candlestick(x=df_plot['Open Time Str'],
                                               open=df_plot['Open'],
                                               high=df_plot['High'],
                                               low=df_plot['Low'],
                                               close=df_plot['Close'])])

        fig.update_layout(
            title=f'{self.selected_pair} Price Chart ({self.interval_var.get()})',
            yaxis_title='Price (USD)',
            xaxis_rangeslider_visible=False,
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white')
        )
        
        img_bytes = fig.to_image(format="png", width=self.chart_frame.winfo_width(), height=self.chart_frame.winfo_height(), scale=2)
        
        threading.Thread(target=self.update_chart_image, args=(img_bytes,), daemon=True).start()

    def update_chart_image(self, img_bytes):
        try:
            original_image = Image.open(io.BytesIO(img_bytes))
            self.after(0, self._display_image, original_image)
        except Exception as e:
            print(f"Error updating chart image: {e}")

    def _display_image(self, image_obj):
        w, h = self.chart_frame.winfo_width(), self.chart_frame.winfo_height()
        if w > 1 and h > 1:
            resized_image = image_obj.resize((w, h), Image.LANCZOS)
            self.chart_image = ImageTk.PhotoImage(resized_image)
            self.chart_label.config(image=self.chart_image, text="")
        else:
            self.after(100, self._display_image, image_obj)

    def enable_buttons(self):
        self.progress.stop()
        self.retrieve_button.config(state="normal")
        if self.df is not None and not self.df.empty:
            self.csv_button.config(state="normal")

    def download_csv(self):
        if self.df is not None:
            filename = f"{self.selected_pair}_{self.interval_var.get()}_{self.start_date_entry.get()}_to_{self.end_date_entry.get()}.csv"
            file_path = os.path.join(csv_folder, filename)
            self.df.to_csv(file_path, index=False)
            messagebox.showinfo("Success", f"Data saved to {file_path}")

# --- Main Function ---
if __name__ == "__main__":
    app = BinanceApp()
    app.mainloop()