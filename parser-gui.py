import requests
from lxml import html
import matplotlib.pyplot as plt
import unicodedata

import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime
import os
from PIL import Image, ImageTk


class MainWindow(tk.Frame):
    def __init__(self, root):
        super().__init__(root)
        self.root = root
        root.title('Hurtowe ceny paliwa') #Wholesale fuel prices
        self.create_widgets()
        current_year = datetime.now().year
        self.content = self.my_parser(current_year)
        last_price = self.content['prices'][-1]
        last_price_date = self.content['dates'][-1]
        self.message.set(
            f'Najnowsza cena: {last_price} z dnia: {last_price_date}') #last price
        self.create_chart(self.content)

    def create_widgets(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label='Zakończ', command=self._exit) 
        menubar.add_cascade(label="Plik", menu=file_menu) # File menu

        self.chart_canvas = tk.Frame(master=self.root)
        self.chart_canvas.grid(row=1, column=0, columnspan=2)

        self.search_variable = tk.StringVar()
        self.search_entry = tk.Entry(
            self.root, textvariable=self.search_variable)
        self.search_entry.bind('<FocusIn>', self.on_entry_in)
        self.search_entry.bind('<Return>', self.on_entry_return)
        self.search_entry.bind('<KP_Enter>', self.on_entry_return)
        self.search_entry.config(fg='grey')
        self.search_variable.set("Podaj rok")
        self.search_entry.grid(row=0, column=0, sticky='E')

        self.button = tk.Button(
            master=self.root, text="Wyświetl", command=self._search)
        self.button.grid(row=0, column=1, pady=10, sticky='W')

        self.message = tk.StringVar()
        self.label = tk.Label(master=self.root, textvariable=self.message)
        self.label.grid(row=3, column=0, columnspan=2, sticky='W')

        self.copyright = tk.Label(
            master=self.root, text='(C) S.Kwiatkowski 2020')
        self.copyright.grid(row=0, column=1, sticky='E')

    def _exit(self):
        self.root.quit()     # stops mainloop
        self.root.destroy()  # this is necessary on Windows

    def on_entry_in(self, event):
        self.search_entry.config(fg='black')
        self.search_variable.set('')

    def on_entry_return(self, event):
        self._search()

    def create_chart(self, content):
        if content is not None:
            year = content.get('year')
            dates = content.get('dates')
            prices = content.get('prices')

            fig, ax = plt.subplots()
            ax.set_title(f'Cena dla paliwa {self.fuel} - {year} rok') #title: price for fuel and year
            ax.set_xlabel('Data') #Date label
            ax.set_ylabel('Cena') #Price label
            fig.autofmt_xdate()
            ax.grid(True)
            ax.xaxis.set_major_locator(plt.MaxNLocator(10)) #fewer dates
            ax.plot(dates, prices, c='#CA3F62')
            if not os.path.exists('data'):
                os.makedirs('data')
            fig.savefig(f'data/{self.fuel}-{year}.png')
            canvas = FigureCanvasTkAgg(fig, master=self.chart_canvas)
            canvas.draw()
            canvas.get_tk_widget().grid(row=0, column=0)

    def my_parser(self, year):
        try:
            page = requests.get(
                f'https://www.orlen.pl/PL/DlaBiznesu/HurtoweCenyPaliw/Strony/archiwum-cen.aspx?Fuel=ONEkodiesel&Year={year}')
        except Exception:
            page = False
        if page and page.ok:
            self.message.set('Ok')
            text = unicodedata.normalize("NFKC", page.text)
            tree = html.fromstring(text)
            table_content = tree.xpath('//tr/td/span/text()')
            if table_content:
                table_content = table_content[::-1]
                table_content = [x for x in table_content if x != 'zł/m']
                # print(table_content)
                content = {}
                content['year'] = year
                self.fuel = table_content.pop()
                content['dates'] = table_content[1::2]
                prices = table_content[::2]
                prices = [price.replace(' ', '') for price in prices]
                prices = list(map(int, prices))
                content['prices'] = prices
                self.content = content
                return self.content
            else:
                self.message.set('Brak danych dla podanego roku')
                for child in self.chart_canvas.winfo_children():
                    child.destroy()

    def _search(self):
        year = self.search_variable.get()
        if year.isdigit():
            if os.path.exists(f'data/{self.fuel}-{year}.png'):
                image = Image.open(f'data/{self.fuel}-{year}.png')
                self.imagetk = ImageTk.PhotoImage(image)
                self.img = tk.Label(image=self.imagetk,
                                    master=self.chart_canvas)
                self.img.grid(row=0, column=0, sticky='NSWE')
                self.message.set('Ok')
            else:
                self.create_chart(self.my_parser(year))
        self.search_entry.config(fg='black')
        self.search_variable.set("")


def main():
    root = tk.Tk()
    app = MainWindow(root)
    app.mainloop()


if __name__ == "__main__":
    main()
