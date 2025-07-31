# sales-dashboard

# 📊 Sales Analytics Dashboard

This Streamlit-based dashboard provides a comprehensive analysis of sales data for a clothing store, allowing users to explore key performance indicators (KPIs), visualize trends, and gain insights into customer behavior, product performance, and manager efficiency.

---

## 🧩 Features

- **Interactive Filters**: Filter data by year, country, product category, and manager.
- **11 Analytical Tabs**: Each tab addresses a specific business question from the provided TЗ (job interview task).
- **Data Visualization**: Includes bar charts, scatter plots, line graphs, and more using Plotly.
- **Cached Data Loading**: For faster performance on repeated runs.
- **Error Handling**: Gracefully handles missing files or incorrect data formats.

---

## 📁 Project Structure

```
dashboard/
│
├── Визуализация/               # Folder containing Excel data files
│   ├── Календарь.xlsx
│   ├── Контрагенты.xlsx
│   ├── План по категориям.xlsx
│   ├── Сотрудники.xlsx
│   ├── Товары.xlsx
│   └── Факт продаж.xlsx
│
└── dashboard.py                # Main Python script with Streamlit app
```

---

## 🛠️ Requirements

Make sure you have the following packages installed:

```bash
pip install streamlit pandas numpy plotly openpyxl
```

> ✅ `openpyxl` is required to read `.xlsx` files.

---

## ▶️ How to Run

1. Clone the repository:
```bash
git clone https://github.com/your-username/sales-analytics-dashboard.git
cd sales-analytics-dashboard
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the app:
```bash
streamlit run dashboard.py
```

4. Open your browser and go to:  
**http://localhost:8501**

---

## 📈 Key Questions Answered

| Tab | Business Question |
|-----|-------------------|
| 1 | Who are the most profitable customers in "Women's Shoes" in Germany? |
| 2 | Which 20% of customers bring 80% of profit in Brazil? |
| 3 | Which countries are the most promising? |
| 4 | Which manager brings the highest sales volume? |
| 5 | Are there managers who achieve high sales only through large discounts? |
| 6 | Which days of the week are most productive for selling "Baby Clothes"? |
| 7 | What products did Matvey Krylov sell, at what price, and with what discount? |
| 8 | Which products in the "Swimwear" category are the best-selling and most profitable? |
| 9 | How has the profit for the "Running Suit" changed over time? Should it be removed from the catalog? |
| 10 | What is the ROI and how does it change from year to year? |
| 11 | Is the sales plan being met? |

https://catalogcompetitivenessanalysisdashboard-8r4n8tagb2nrpdbkkhnz6r.streamlit.app/



<img width="3840" height="1818" alt="Untitled diagram _ Mermaid Chart-2025-07-31-142802" src="https://github.com/user-attachments/assets/3decce97-18ed-448f-90a8-c08b9ab3bafd" />
